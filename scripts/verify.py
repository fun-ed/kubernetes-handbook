#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["PyYAML==6.0.3", "jsonschema==4.25.1"]
# ///
"""Validate handbook manifests locally and, optionally, against an owned kind cluster."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

import yaml
from jsonschema import Draft7Validator
from jsonschema.exceptions import SchemaError

TARGET_VERSION = "1.37.1"
API_VERSION_PATTERN = re.compile(r"^v[0-9]+(?:(?:alpha|beta)[0-9]+)?$")
API_GROUP_PATTERN = re.compile(r"^[a-z0-9](?:[-a-z0-9]*[a-z0-9])?(?:\.[a-z0-9](?:[-a-z0-9]*[a-z0-9])?)*$")

SCHEMA_COMMIT = "8df8a883b68a24a104b4a9e43c1288090ae60b3b"
SCHEMA_BASE = (
    "https://raw.githubusercontent.com/yannh/kubernetes-json-schema/"
    f"{SCHEMA_COMMIT}/v{TARGET_VERSION}-standalone-strict"
)
SCHEMA_SOURCE = "yannh/kubernetes-json-schema strict standalone schemas"
FIELD_MANAGER = "handbook-version-verify"

BUILTIN_API_GROUPS = {
    "",
    "admissionregistration.k8s.io",
    "apiextensions.k8s.io",
    "apiregistration.k8s.io",
    "apps",
    "authentication.k8s.io",
    "authorization.k8s.io",
    "autoscaling",
    "batch",
    "certificates.k8s.io",
    "coordination.k8s.io",
    "discovery.k8s.io",
    "events.k8s.io",
    "extensions",
    "flowcontrol.apiserver.k8s.io",
    "networking.k8s.io",
    "node.k8s.io",
    "policy",
    "rbac.authorization.k8s.io",
    "resource.k8s.io",
    "scheduling.k8s.io",
    "storage.k8s.io",
    "storagemigration.k8s.io",
}

# Release bundles are filtered to CRDs only; the experimental Gateway bundle also has these
# explicitly checked admission-policy objects, which are recorded but not installed.
GATEWAY_STANDARD_CRDS = "https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.6.2/standard-install.yaml"
GATEWAY_EXPERIMENTAL_CRDS = "https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.6.2/experimental-install.yaml"
GATEWAY_EXCLUDED_POLICY_OBJECTS = {
    ("admissionregistration.k8s.io/v1", "ValidatingAdmissionPolicy"),
    ("admissionregistration.k8s.io/v1", "ValidatingAdmissionPolicyBinding"),
}
CALICO_GLOBAL_NETWORK_POLICY_CRD = "https://raw.githubusercontent.com/projectcalico/calico/v3.33.0/api/config/crd/projectcalico.org_globalnetworkpolicies.yaml"
CRD_RELEASES = {
    "https://github.com/cert-manager/cert-manager/releases/download/v1.21.2/cert-manager.crds.yaml": {
        "cert-manager.io",
        "acme.cert-manager.io",
    },
    CALICO_GLOBAL_NETWORK_POLICY_CRD: {
        "projectcalico.org",
    },
}
CRD_RELEASE_EXPECTATIONS = {
    CALICO_GLOBAL_NETWORK_POLICY_CRD: {
        "group": "projectcalico.org",
        "kind": "GlobalNetworkPolicy",
        "metadata_name": "globalnetworkpolicies.projectcalico.org",
        "served_version": "v3",
    },
}

SYSTEM_NAMESPACES = {"default", "kube-system", "kube-public", "kube-node-lease"}


class VerificationError(Exception):
    """A validation or isolated-cluster operation failed."""


class UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""

    def construct_mapping(self, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
        explicit_nodes = {
            id(key_node)
            for key_node, _ in node.value
            if key_node.tag != "tag:yaml.org,2002:merge"
        }
        self.flatten_mapping(node)
        result: dict[Any, Any] = {}
        seen_explicit: set[Any] = set()
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                explicit_duplicate = id(key_node) in explicit_nodes and key in seen_explicit
                if id(key_node) in explicit_nodes:
                    seen_explicit.add(key)
            except TypeError as exc:
                raise yaml.constructor.ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    "found an unhashable mapping key",
                    key_node.start_mark,
                ) from exc
            if explicit_duplicate:
                raise yaml.constructor.ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    f"found duplicate key {key!r}",
                    key_node.start_mark,
                )
            result[key] = self.construct_object(value_node, deep=deep)
        return result


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    UniqueKeyLoader.construct_mapping,
)
UniqueKeyLoader.yaml_implicit_resolvers = {
    first: [
        (tag, pattern)
        for tag, pattern in resolvers
        if tag != "tag:yaml.org,2002:timestamp"
    ]
    for first, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}



@dataclass
class ManifestResource:
    path: str
    document: str
    body: dict[str, Any]


@dataclass
class Inventory:
    root: pathlib.Path
    yaml_files: int = 0
    historical_files: list[str] = field(default_factory=list)
    empty_documents: int = 0
    resources: list[ManifestResource] = field(default_factory=list)
    errors: list[dict[str, str]] = field(default_factory=list)


@dataclass
class LocalResult:
    inventory: Inventory
    builtin_validated: int = 0
    custom_resources: list[ManifestResource] = field(default_factory=list)
    errors: list[dict[str, str]] = field(default_factory=list)


def _error(path: str, document: str, message: str) -> dict[str, str]:
    return {"source": path, "document": document, "message": message}


def _append_resource(
    inventory: Inventory,
    relative_path: str,
    document_ref: str,
    document: Any,
    depth: int = 0,
) -> None:
    if depth > 32:
        inventory.errors.append(_error(relative_path, document_ref, "nested List depth exceeds 32"))
        return
    if not isinstance(document, dict):
        inventory.errors.append(_error(relative_path, document_ref, "resource document must be a YAML mapping"))
        return
    api_version = document.get("apiVersion")
    kind = document.get("kind")
    if not isinstance(api_version, str) or not api_version or not isinstance(kind, str) or not kind:
        inventory.errors.append(_error(relative_path, document_ref, "resource must have string apiVersion and kind"))
        return
    try:
        api_group(api_version)
    except ValueError as exc:
        inventory.errors.append(_error(relative_path, document_ref, str(exc)))
        return

    if kind == "List":
        items = document.get("items")
        if not isinstance(items, list):
            inventory.errors.append(_error(relative_path, document_ref, "List.items must be an array"))
            return
        for index, item in enumerate(items):
            _append_resource(inventory, relative_path, f"{document_ref}.items[{index}]", item, depth + 1)
        return
    inventory.resources.append(ManifestResource(relative_path, document_ref, document))


def collect_manifest_resources(root: pathlib.Path | str) -> Inventory:
    """Read examples/ and manifests/, excluding files marked HISTORICAL from resources."""
    root_path = pathlib.Path(root).resolve()
    inventory = Inventory(root=root_path)
    paths: list[pathlib.Path] = []
    for directory in ("examples", "manifests"):
        base = root_path / directory
        if base.exists():
            paths.extend(path for path in base.rglob("*") if path.is_file() and path.suffix.lower() in {".yaml", ".yml"})
    paths.sort()
    inventory.yaml_files = len(paths)

    for path in paths:
        relative = path.relative_to(root_path).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            inventory.errors.append(_error(relative, "file", f"cannot read YAML file: {exc}"))
            continue
        historical = any(line.startswith("# HISTORICAL:") for line in text.splitlines()[:5])
        if historical:
            inventory.historical_files.append(relative)
        try:
            documents = list(yaml.load_all(text, Loader=UniqueKeyLoader))
        except (yaml.YAMLError, ValueError, TypeError) as exc:
            inventory.errors.append(_error(relative, "YAML", str(exc)))
            continue
        if historical:
            continue
        for index, document in enumerate(documents, start=1):
            if document is None:
                inventory.empty_documents += 1
                continue
            _append_resource(inventory, relative, str(index), document)
    return inventory


def api_group(api_version: str) -> str:
    """Validate and return the API group, or the empty group for a core version."""
    parts = api_version.split("/")
    if len(parts) == 1:
        group = ""
        version = parts[0]
    elif len(parts) == 2:
        group, version = parts
    else:
        raise ValueError("invalid Kubernetes apiVersion syntax")
    if not API_VERSION_PATTERN.fullmatch(version) or (group and not API_GROUP_PATTERN.fullmatch(group)):
        raise ValueError("invalid Kubernetes apiVersion syntax")
    return group


def is_builtin_resource(resource: ManifestResource) -> bool:
    try:
        return api_group(resource.body["apiVersion"]) in BUILTIN_API_GROUPS
    except (KeyError, ValueError):
        return False


def schema_key(resource: ManifestResource) -> str:
    api_version = resource.body["apiVersion"]
    group = api_group(api_version)
    version = api_version.split("/", 1)[-1]
    prefix = f"{group.split('.', 1)[0]}-" if group else ""
    return f"{resource.body['kind'].lower()}-{prefix}{version}.json"


def _fetch_schema(key: str) -> tuple[str, dict[str, Any] | None, str | None]:
    url = f"{SCHEMA_BASE}/{key}"
    request = urllib.request.Request(url, headers={"User-Agent": "kubernetes-handbook-verifier"})
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            schema = json.loads(response.read().decode("utf-8"))
        if not isinstance(schema, dict):
            raise ValueError("schema response is not a JSON object")
        Draft7Validator.check_schema(schema)
        return key, schema, None
    except (OSError, urllib.error.URLError, json.JSONDecodeError, UnicodeDecodeError, ValueError, SchemaError) as exc:
        return key, None, f"could not fetch or parse pinned schema {url}: {exc}"


def load_schemas(keys: Iterable[str]) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    """Fetch strict schemas from one immutable upstream commit; report every failure."""
    unique_keys = sorted(set(keys))
    if not unique_keys:
        return {}, {}
    schemas: dict[str, dict[str, Any]] = {}
    failures: dict[str, str] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        for key, schema, error in executor.map(_fetch_schema, unique_keys):
            if error:
                failures[key] = error
            elif schema is not None:
                schemas[key] = schema
    return schemas, failures


def _schema_problems(schema: dict[str, Any], body: dict[str, Any]) -> list[str]:
    validator = Draft7Validator(schema, format_checker=Draft7Validator.FORMAT_CHECKER)
    problems = sorted(
        validator.iter_errors(body),
        key=lambda problem: tuple(str(part) for part in problem.absolute_path),
    )
    messages = []
    for problem in problems:
        path = ".".join(str(part) for part in problem.absolute_path) or "<root>"
        keyword = str(problem.validator or "schema")
        descriptions = {
            "additionalProperties": "contains fields not allowed by the strict schema",
            "required": "is missing one or more required fields",
            "type": "has the wrong JSON type",
            "enum": "is not an allowed value",
            "const": "does not match the required constant",
            "format": "does not match the required format",
            "pattern": "does not match the required pattern",
        }
        detail = descriptions.get(keyword, f"violates the {keyword!r} schema constraint")
        messages.append(f"{path}: {detail}")
    return messages


def _semantic_problems(resource: ManifestResource) -> list[str]:
    body = resource.body
    kind = body.get("kind")
    problems: list[str] = []
    if kind in {"Deployment", "DaemonSet", "ReplicaSet", "StatefulSet"}:
        spec = body.get("spec") or {}
        selector = spec.get("selector") if isinstance(spec, dict) else None
        template = spec.get("template") if isinstance(spec, dict) else None
        metadata = template.get("metadata") if isinstance(template, dict) else None
        labels = metadata.get("labels") if isinstance(metadata, dict) else None
        labels = labels if isinstance(labels, dict) else {}
        if not isinstance(selector, dict) or not (selector.get("matchLabels") or selector.get("matchExpressions")):
            problems.append("workload selector must select at least one Pod")
        else:
            match_labels = selector.get("matchLabels") or {}
            if isinstance(match_labels, dict) and any(labels.get(key) != value for key, value in match_labels.items()):
                problems.append("selector matchLabels do not match Pod template labels")
    if kind == "PodDisruptionBudget":
        spec = body.get("spec") or {}
        selector = spec.get("selector") if isinstance(spec, dict) else None
        if not isinstance(selector, dict) or not (selector.get("matchLabels") or selector.get("matchExpressions")):
            problems.append("PodDisruptionBudget selector must be explicit and nonempty")
    serialized = yaml.safe_dump(body, sort_keys=True)
    if "seccomp.security.alpha.kubernetes.io" in serialized:
        problems.append("legacy seccomp annotation is not valid for this baseline")
    return problems


def validate_local(
    root: pathlib.Path | str,
    schema_loader: Callable[[Iterable[str]], tuple[dict[str, dict[str, Any]], dict[str, str]]] = load_schemas,
) -> LocalResult:
    """Validate local YAML, builtin strict schemas, and selected safety invariants."""
    inventory = collect_manifest_resources(root)
    result = LocalResult(inventory=inventory, errors=list(inventory.errors))
    builtin = [resource for resource in inventory.resources if is_builtin_resource(resource)]
    result.custom_resources = [resource for resource in inventory.resources if not is_builtin_resource(resource)]
    keys: dict[str, list[ManifestResource]] = {}
    for resource in builtin:
        try:
            key = schema_key(resource)
        except (KeyError, ValueError) as exc:
            result.errors.append(_error(resource.path, resource.document, str(exc)))
            continue
        keys.setdefault(key, []).append(resource)

    schemas, fetch_errors = schema_loader(keys)
    for key, resources in keys.items():
        if key in fetch_errors:
            for resource in resources:
                result.errors.append(_error(resource.path, resource.document, fetch_errors[key]))
            continue
        schema = schemas.get(key)
        if schema is None:
            detail = f"pinned strict schema {key} was not returned; validation cannot be skipped"
            for resource in resources:
                result.errors.append(_error(resource.path, resource.document, detail))
            continue
        for resource in resources:
            try:
                problems = _schema_problems(schema, resource.body)
            except Exception as exc:  # A malformed downloaded schema must fail closed.
                result.errors.append(_error(resource.path, resource.document, f"schema validation failed for {key}: {exc}"))
                continue
            semantic = _semantic_problems(resource)
            for problem in problems + semantic:
                result.errors.append(_error(resource.path, resource.document, problem))
            if not problems and not semantic:
                result.builtin_validated += 1
    return result


def resource_summary(resource: ManifestResource) -> dict[str, str]:
    body = resource.body
    metadata = body.get("metadata") if isinstance(body.get("metadata"), dict) else {}
    summary = {
        "source": resource.path,
        "document": resource.document,
        "apiVersion": str(body.get("apiVersion", "")),
        "kind": str(body.get("kind", "")),
    }
    if metadata.get("name") is not None:
        summary["name"] = str(metadata["name"])
    return summary


def build_local_report(result: LocalResult, mode: str = "local") -> dict[str, Any]:
    inventory = result.inventory
    builtin_count = sum(is_builtin_resource(resource) for resource in inventory.resources)
    return {
        "target_kubernetes": TARGET_VERSION,
        "mode": mode,
        "schema_validation": {
            "source": SCHEMA_SOURCE,
            "commit": SCHEMA_COMMIT,
            "version_directory": f"v{TARGET_VERSION}-standalone-strict",
            "note": "Third-party strict schemas supplement, but do not replace, an exact-version API server dry-run.",
        },
        "counts": {
            "yaml_files_seen": inventory.yaml_files,
            "historical_files_excluded": len(inventory.historical_files),
            "empty_yaml_documents_excluded": inventory.empty_documents,
            "active_resources_after_List_expansion": len(inventory.resources),
            "builtin_resources": builtin_count,
            "builtin_resources_validated_locally": result.builtin_validated,
            "custom_resources_not_validated_locally": len(result.custom_resources),
            "errors": len(result.errors),
        },
        "excluded": {
            "historical_files": inventory.historical_files,
            "empty_yaml_documents": inventory.empty_documents,
            "custom_resources_not_validated_locally": [resource_summary(item) for item in result.custom_resources],
        },
        "validated": {"builtin_resources_by_strict_schema": result.builtin_validated},
        "errors": result.errors,
    }


def exact_version(value: Any) -> bool:
    return isinstance(value, str) and value == f"v{TARGET_VERSION}"


def assert_exact_versions(version_report: Any, nodes_report: Any) -> dict[str, Any]:
    """Fail unless API server and every kubelet report the exact target patch version."""
    if not isinstance(version_report, dict):
        raise VerificationError("kubectl version output is not a JSON object")
    server_info = version_report.get("serverVersion")
    server_version = server_info.get("gitVersion") if isinstance(server_info, dict) else None
    if not exact_version(server_version):
        raise VerificationError(
            f"refusing API writes: API server version is {server_version!r}, expected v{TARGET_VERSION}"
        )
    if not isinstance(nodes_report, dict) or not isinstance(nodes_report.get("items"), list):
        raise VerificationError("kubectl get nodes output is not a JSON object with an items array")
    nodes = nodes_report["items"]
    if not nodes:
        raise VerificationError("refusing API writes: cluster reports no kubelet nodes")
    versions: list[dict[str, str]] = []
    for node in nodes:
        metadata = node.get("metadata") if isinstance(node, dict) else {}
        status = node.get("status") if isinstance(node, dict) else {}
        info = status.get("nodeInfo") if isinstance(status, dict) else {}
        name = metadata.get("name", "<unnamed>") if isinstance(metadata, dict) else "<unnamed>"
        kubelet_version = info.get("kubeletVersion") if isinstance(info, dict) else None
        versions.append({"name": str(name), "kubelet_version": str(kubelet_version or "")})
        if not exact_version(kubelet_version):
            raise VerificationError(
                f"refusing API writes: node {name!r} kubelet is {kubelet_version!r}, expected v{TARGET_VERSION}"
            )
    return {"api_server": server_version, "kubelets": versions}


def kubectl_command(binary: str, kubeconfig: pathlib.Path | str, arguments: Iterable[str]) -> list[str]:
    """Build a kubectl command that always names the verifier-owned kubeconfig."""
    return [binary, "--kubeconfig", str(kubeconfig), *arguments]


def _isolated_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment.pop("KUBECONFIG", None)
    return environment

def _kind_environment(docker: str) -> dict[str, str]:
    environment = _isolated_environment()
    environment["KIND_EXPERIMENTAL_PROVIDER"] = "docker"
    docker_path = pathlib.Path(docker)
    if docker_path.parent != pathlib.Path("."):
        environment["PATH"] = f"{docker_path.parent.resolve()}{os.pathsep}{environment.get('PATH', '')}"
    return environment


def _run_process(
    command: list[str],
    *,
    input_text: str | None = None,
    timeout: int = 120,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            command,
            input=input_text,
            text=True,
            capture_output=True,
            timeout=timeout,
            env=env if env is not None else _isolated_environment(),
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise VerificationError(f"command failed to run: {command[0]}: {exc}") from exc
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise VerificationError(
            f"command {command[0]!r} exited {result.returncode}: {detail or 'no diagnostic output'}"
        )
    return result


def _run_kubectl(
    kubectl: str,
    kubeconfig: pathlib.Path,
    arguments: Iterable[str],
    *,
    input_text: str | None = None,
    timeout: int = 120,
) -> subprocess.CompletedProcess[str]:
    return _run_process(
        kubectl_command(kubectl, kubeconfig, arguments),
        input_text=input_text,
        timeout=timeout,
    )


def _fetch_release_yaml(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "kubernetes-handbook-verifier"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.read().decode("utf-8")
    except (OSError, urllib.error.URLError, UnicodeDecodeError) as exc:
        raise VerificationError(f"cannot download required official CRD release file {url}: {exc}") from exc


def _required_crd_releases(resources: Iterable[ManifestResource]) -> list[str]:
    groups = set()
    for resource in resources:
        try:
            groups.add(api_group(resource.body["apiVersion"]))
        except (KeyError, ValueError):
            continue
    releases = []
    if "gateway.networking.x-k8s.io" in groups:
        releases.append(GATEWAY_EXPERIMENTAL_CRDS)
    elif "gateway.networking.k8s.io" in groups:
        releases.append(GATEWAY_STANDARD_CRDS)
    releases.extend(url for url, release_groups in CRD_RELEASES.items() if groups & release_groups)
    return releases


def _crds_for_apply_from_release(
    url: str,
    text: str,
) -> tuple[list[str], str, list[dict[str, Any]]]:
    try:
        names: list[str] = []
        crd_documents: list[dict[str, Any]] = []
        excluded: list[dict[str, Any]] = []
        excluded_identities: set[tuple[str, str]] = set()
        for index, document in enumerate(yaml.load_all(text, Loader=UniqueKeyLoader), start=1):
            if document is None:
                continue
            if not isinstance(document, dict):
                raise VerificationError(
                    f"official CRD source {url} document {index} is not an object"
                )

            api_version = document.get("apiVersion")
            kind = document.get("kind")
            if api_version == "apiextensions.k8s.io/v1" and kind == "CustomResourceDefinition":
                metadata = document.get("metadata")
                name = metadata.get("name") if isinstance(metadata, dict) else None
                if not isinstance(name, str) or not name:
                    raise VerificationError(f"official CRD source {url} document {index} has no metadata.name")
                expectation = CRD_RELEASE_EXPECTATIONS.get(url)
                if expectation is not None:
                    spec = document.get("spec")
                    crd_names = spec.get("names") if isinstance(spec, dict) else None
                    versions = spec.get("versions") if isinstance(spec, dict) else None
                    served_versions = {
                        version.get("name")
                        for version in versions or []
                        if isinstance(version, dict) and version.get("served") is True
                    }
                    if (
                        name != expectation["metadata_name"]
                        or not isinstance(spec, dict)
                        or spec.get("group") != expectation["group"]
                        or not isinstance(crd_names, dict)
                        or crd_names.get("kind") != expectation["kind"]
                        or expectation["served_version"] not in served_versions
                    ):
                        raise VerificationError(
                            f"official CRD source {url} document {index} is not the expected "
                            f"{expectation['group']}/{expectation['served_version']} {expectation['kind']} CRD"
                        )
                names.append(name)
                crd_documents.append(document)
                continue

            identity = (api_version, kind)
            if url == GATEWAY_EXPERIMENTAL_CRDS and identity in GATEWAY_EXCLUDED_POLICY_OBJECTS:
                if identity in excluded_identities:
                    raise VerificationError(
                        f"official Gateway policy source {url} repeats expected {kind}"
                    )
                metadata = document.get("metadata")
                name = metadata.get("name") if isinstance(metadata, dict) else None
                if not isinstance(name, str) or not name:
                    raise VerificationError(
                        f"official Gateway policy source {url} document {index} has no metadata.name"
                    )
                excluded.append(
                    {
                        "document": index,
                        "apiVersion": api_version,
                        "kind": kind,
                        "name": name,
                    }
                )
                excluded_identities.add(identity)
                continue

            raise VerificationError(
                f"official CRD source {url} document {index} has unexpected apiVersion/kind "
                f"{api_version!r}/{kind!r}; only CRDs and the two expected Gateway policy kinds are allowed"
            )

        if not names:
            raise VerificationError(f"official CRD source {url} contains no CRDs")
        if url == GATEWAY_EXPERIMENTAL_CRDS and excluded_identities != GATEWAY_EXCLUDED_POLICY_OBJECTS:
            missing = sorted(GATEWAY_EXCLUDED_POLICY_OBJECTS - excluded_identities)
            raise VerificationError(
                f"official Gateway policy source {url} is missing expected policy kinds: {missing}"
            )
        crd_yaml = yaml.safe_dump_all(crd_documents, sort_keys=False)
        return names, crd_yaml, excluded
    except (yaml.YAMLError, ValueError, TypeError) as exc:
        raise VerificationError(f"cannot parse official CRD source {url}: {exc}") from exc


def _namespace_names(resources: Iterable[ManifestResource]) -> list[str]:
    names: set[str] = set()
    for resource in resources:
        body = resource.body
        metadata = body.get("metadata") if isinstance(body.get("metadata"), dict) else {}
        if body.get("kind") == "Namespace":
            name = metadata.get("name")
            if isinstance(name, str) and name:
                names.add(name)
        else:
            namespace = metadata.get("namespace") or "default"
            if isinstance(namespace, str):
                names.add(namespace)
    return sorted(names - SYSTEM_NAMESPACES)


def _make_namespace(name: str) -> str:
    return yaml.safe_dump(
        {"apiVersion": "v1", "kind": "Namespace", "metadata": {"name": name}},
        sort_keys=False,
    )


def _retryable_crd_discovery(stderr: str) -> bool:
    return "failed to find resource referenced by paramkind" in stderr.lower()


def _server_dry_run(
    resource: ManifestResource,
    kubectl: str,
    kubeconfig: pathlib.Path,
    *,
    retries: int = 8,
) -> subprocess.CompletedProcess[str]:
    body = yaml.safe_dump(resource.body, sort_keys=False)
    command = [
        "apply",
        "--dry-run=server",
        "--validate=strict",
        "-f",
        "-",
    ]
    for attempt in range(retries + 1):
        try:
            result = subprocess.run(
                kubectl_command(kubectl, kubeconfig, command),
                input=body,
                text=True,
                capture_output=True,
                timeout=120,
                env=_isolated_environment(),
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise VerificationError(f"server dry-run command failed: {exc}") from exc
        if result.returncode == 0:
            return result
        if attempt == retries or not _retryable_crd_discovery(result.stderr):
            return result
        time.sleep(2)
    raise AssertionError("unreachable")


def _runtime_smoke(kubectl: str, kubeconfig: pathlib.Path) -> dict[str, Any]:
    namespace = "handbook-v137-smoke"
    workload_and_service = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: http-smoke
  namespace: handbook-v137-smoke
spec:
  replicas: 1
  selector:
    matchLabels:
      app: http-smoke
  template:
    metadata:
      labels:
        app: http-smoke
    spec:
      containers:
        - name: web
          image: busybox:1.37.0
          imagePullPolicy: IfNotPresent
          command: ["sh", "-c", "mkdir -p /www && echo handbook-v137-ok >/www/index.html && httpd -f -p 8080 -h /www"]
          ports:
            - containerPort: 8080
              name: http
---
apiVersion: v1
kind: Service
metadata:
  name: http-smoke
  namespace: handbook-v137-smoke
spec:
  selector:
    app: http-smoke
  ports:
    - name: http
      port: 8080
      targetPort: http
"""
    _run_kubectl(kubectl, kubeconfig, ["create", "namespace", namespace], timeout=60)
    _run_kubectl(
        kubectl,
        kubeconfig,
        ["apply", "--server-side", f"--field-manager={FIELD_MANAGER}", "-f", "-"],
        input_text=workload_and_service,
    )
    _run_kubectl(
        kubectl,
        kubeconfig,
        ["rollout", "status", "deployment/http-smoke", "-n", namespace, "--timeout=180s"],
        timeout=190,
    )
    client_yaml = yaml.safe_dump(
        {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {"name": "dns-client", "namespace": namespace},
            "spec": {
                "restartPolicy": "Never",
                "containers": [
                    {
                        "name": "client",
                        "image": "busybox:1.37.0",
                        "imagePullPolicy": "IfNotPresent",
                        "command": [
                            "sh",
                            "-c",
                            "nslookup http-smoke.handbook-v137-smoke.svc.cluster.local && wget -q -O- http://http-smoke.handbook-v137-smoke.svc.cluster.local:8080",
                        ],
                    }
                ],
            },
        },
        sort_keys=False,
    )
    _run_kubectl(
        kubectl,
        kubeconfig,
        ["apply", "--server-side", f"--field-manager={FIELD_MANAGER}", "-f", "-"],
        input_text=client_yaml,
    )
    _run_kubectl(
        kubectl,
        kubeconfig,
        ["wait", "--for=jsonpath={.status.phase}=Succeeded", "pod/dns-client", "-n", namespace, "--timeout=180s"],
        timeout=190,
    )
    logs = _run_kubectl(kubectl, kubeconfig, ["logs", "pod/dns-client", "-n", namespace]).stdout
    if "handbook-v137-ok" not in logs:
        raise VerificationError(f"DNS/service smoke pod did not receive the expected HTTP response: {logs.strip()!r}")
    return {
        "passed": True,
        "checks": ["Deployment became ready", "Service DNS resolved", "HTTP request through Service returned expected body"],
        "workload_image": "busybox:1.37.0",
        "informer_events": "not tested; this smoke test uses kubectl waits and does not claim client-go informer coverage",
    }


def run_owned_cluster_validation(
    resources: list[ManifestResource],
    *,
    kind: str,
    kubectl: str,
    docker: str,
    image: str,
) -> dict[str, Any]:
    """Create a unique kind cluster and stop only its nodes, retaining its data."""
    output_dir = pathlib.Path(tempfile.mkdtemp(prefix="kubernetes-handbook-v137-verify-"))
    output_dir.chmod(0o700)
    kubeconfig = output_dir / "kubeconfig"
    cluster_name = f"handbook-v137-{os.urandom(16).hex()}"
    report: dict[str, Any] = {
        "mode": "owned-kind-cluster",
        "cluster": {
            "name": cluster_name,
            "image": image,
            "created": False,
            "deleted_by_verifier": False,
            "stopped_nodes": [],
        },
        "output_directory": str(output_dir),
        "output_file": str(output_dir / "report.json"),
        "counts": {"server_dry_run_passed": 0, "server_dry_run_failed": 0},
        "server_dry_run_errors": [],
        "official_bundle_objects_excluded": [],
        "validated": {"server_dry_run_resources": 0},
        "runtime_smoke": {"passed": False, "not_run": True},
        "errors": [],
    }
    cluster_created = False
    cluster_create_started = False
    kind_environment = _kind_environment(docker)
    try:
        listed = _run_process([kind, "get", "clusters"], timeout=60, env=kind_environment).stdout.splitlines()
        if cluster_name in {line.strip() for line in listed}:
            raise VerificationError(f"generated kind cluster name already exists; refusing reuse: {cluster_name}")
        cluster_create_started = True
        _run_process(
            [
                kind,
                "create",
                "cluster",
                "--name",
                cluster_name,
                "--image",
                image,
                "--kubeconfig",
                str(kubeconfig),
                "--wait",
                "180s",
            ],
            timeout=240,
            env=kind_environment,
        )
        cluster_created = True
        report["cluster"]["created"] = True
        if kubeconfig.exists():
            kubeconfig.chmod(0o600)

        version_result = _run_kubectl(kubectl, kubeconfig, ["version", "-o", "json"])
        nodes_result = _run_kubectl(kubectl, kubeconfig, ["get", "nodes", "-o", "json"])
        report["versions"] = assert_exact_versions(
            json.loads(version_result.stdout),
            json.loads(nodes_result.stdout),
        )

        for url in _required_crd_releases(resources):
            release_yaml = _fetch_release_yaml(url)
            names, crd_yaml, excluded = _crds_for_apply_from_release(url, release_yaml)
            report["official_bundle_objects_excluded"].extend(
                {"source": url, **item} for item in excluded
            )
            _run_kubectl(
                kubectl,
                kubeconfig,
                ["apply", "--server-side", f"--field-manager={FIELD_MANAGER}", "-f", "-"],
                input_text=crd_yaml,
                timeout=180,
            )
            _run_kubectl(
                kubectl,
                kubeconfig,
                ["wait", "--for=condition=Established", "--timeout=120s", *[f"crd/{name}" for name in names]],
                timeout=130,
            )
        report["crd_sources_installed"] = _required_crd_releases(resources)

        for namespace in _namespace_names(resources):
            _run_kubectl(
                kubectl,
                kubeconfig,
                ["apply", "--server-side", f"--field-manager={FIELD_MANAGER}", "-f", "-"],
                input_text=_make_namespace(namespace),
            )

        for resource in resources:
            result = _server_dry_run(resource, kubectl, kubeconfig)
            if result.returncode:
                report["counts"]["server_dry_run_failed"] += 1
                report["server_dry_run_errors"].append(
                    _error(resource.path, resource.document, (result.stderr or result.stdout).strip())
                )
            else:
                report["counts"]["server_dry_run_passed"] += 1
        report["validated"]["server_dry_run_resources"] = report["counts"]["server_dry_run_passed"]
        if report["counts"]["server_dry_run_failed"]:
            report["errors"].append("one or more active resources failed exact-version server-side dry-run")
        else:
            report["runtime_smoke"] = {"passed": False, "not_run": False}
            report["runtime_smoke"] = _runtime_smoke(kubectl, kubeconfig)
    except (VerificationError, json.JSONDecodeError, OSError, yaml.YAMLError) as exc:
        report["errors"].append(str(exc))
        if cluster_create_started and not cluster_created:
            report["cluster"]["partial_create_cleanup"] = (
                "not attempted because kind did not report a successful create; no existing nodes were stopped"
            )
    finally:
        if cluster_created:
            try:
                node_names = [
                    line.strip()
                    for line in _run_process(
                        [kind, "get", "nodes", "--name", cluster_name],
                        timeout=60,
                        env=kind_environment,
                    ).stdout.splitlines()
                    if line.strip()
                ]
                if any(not node.startswith(f"{cluster_name}-") for node in node_names):
                    raise VerificationError("kind returned a node outside this run's unique cluster name")
                if node_names:
                    _run_process([docker, "stop", "--time", "10", *node_names], timeout=120)
                report["cluster"]["stopped_nodes"] = node_names
            except VerificationError as exc:
                report["errors"].append(f"owned node stop failed: {exc}")
        try:
            if kubeconfig.exists():
                kubeconfig.chmod(0o600)
                report["cluster"]["private_kubeconfig_retained"] = True
        except OSError as exc:
            report["errors"].append(f"cannot secure temporary kubeconfig: {exc}")
    report["counts"]["errors"] = len(report["errors"]) + len(report["server_dry_run_errors"])
    return report


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cluster", action="store_true", help="create a unique kind cluster for server validation")

    parser.add_argument("--docker", default="docker", help="Docker executable used to stop created kind nodes (default: docker)")
    parser.add_argument("--kind", default="kind", help="kind executable (default: kind)")
    parser.add_argument("--kubectl", default="kubectl", help="kubectl executable (default: kubectl)")
    parser.add_argument("--image", help="exact Kubernetes node image to use with kind; required with --cluster")
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path(__file__).resolve().parents[1], help=argparse.SUPPRESS)
    arguments = parser.parse_args(argv)
    if arguments.cluster and not arguments.image:
        parser.error("--cluster requires --image with an exact Kubernetes node image")
    if not arguments.cluster and arguments.image:
        parser.error("--image can only be used with --cluster")
    return arguments


def main(argv: list[str] | None = None) -> int:
    args = parse_arguments(argv)
    local = validate_local(args.root)
    report = build_local_report(local, mode="owned-kind-cluster" if args.cluster else "local")
    if args.cluster and not local.errors:
        cluster = run_owned_cluster_validation(
            local.inventory.resources,
            kind=args.kind,
            kubectl=args.kubectl,
            docker=args.docker,
            image=args.image,
        )
        local_counts = report["counts"]
        local_validated = report["validated"]
        report.update(cluster)
        report["validated"] = {**local_validated, **cluster["validated"]}
        report["counts"] = {**local_counts, **cluster["counts"]}
        custom_count = len(local.custom_resources)
        if cluster["counts"]["server_dry_run_passed"] == len(local.inventory.resources):
            report["validated"]["custom_resources_by_server_dry_run"] = custom_count
        report["counts"]["custom_resources_not_validated_locally"] = custom_count
        report["excluded"]["custom_resources_not_validated_locally"] = [
            resource_summary(item) for item in local.custom_resources
        ]
        output_file = pathlib.Path(cluster["output_file"])
        try:
            output_file.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        except OSError as exc:
            report["errors"].append(f"cannot write JSON report to {output_file}: {exc}")
            report["counts"]["errors"] += 1
    elif args.cluster:
        report["errors"].append("cluster run skipped because local YAML or schema validation failed")
        report["counts"]["errors"] = len(report["errors"])

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report.get("errors") or report.get("server_dry_run_errors") else 0


if __name__ == "__main__":
    raise SystemExit(main())
