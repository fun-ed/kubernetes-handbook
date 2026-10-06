#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["PyYAML==6.0.3", "jsonschema==4.25.1"]
# ///
"""Inventory and validate YAML fences in current handbook Markdown."""

import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

import yaml

ROOT = Path(__file__).resolve().parents[1]
CRD_VALIDATOR_DIR = ROOT / "scripts" / "validate-crds"
CRD_VALIDATOR_VERSION = "v0.37.1"
VERIFY_PATH = ROOT / "scripts" / "verify.py"
_spec = importlib.util.spec_from_file_location("handbook_verify", VERIFY_PATH)
if _spec is None or _spec.loader is None:
    raise RuntimeError("Cannot load the manifest validator")
_verify = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _verify
_spec.loader.exec_module(_verify)

FENCE = re.compile(r"^( {0,12})(`{3,}|~{3,})\s*([^`]*)$")
HISTORICAL = re.compile(r"histor(?:ical|y)|deprecated|removed|退役|已移除|歷史|舊版", re.I)
TEMPLATE_TOKEN = re.compile(r"{{-?\s*(?:if\b|with\b|range\b|end\b|else\b|define\b|template\b|include\b|toYaml\b|nindent\b|quote\b|default\b|required\b|\.Values\b|\.Release\b|\.Chart\b|\.Capabilities\b|\$[A-Za-z_])")
NATIVE_KEYS = {"clusters", "users", "contexts", "current-context", "preferences", "apiServer", "clusterCIDR", "containerRuntimeEndpoint", "cgroupDriver", "runtimeRequestTimeout", "plugins", "criSocket", "podSubnet", "serviceSubnet"}
NATIVE_API_VERSIONS = {
    "audit.k8s.io": {"v1"},
    "kubeadm.k8s.io": {"v1beta4"},
    "kubelet.config.k8s.io": {"v1beta1"},
    "kubeproxy.config.k8s.io": {"v1alpha1"},
}
NATIVE_API_KINDS = {
    "audit.k8s.io": {"Policy"},
    "kubeadm.k8s.io": {"InitConfiguration", "ClusterConfiguration", "JoinConfiguration", "ResetConfiguration", "UpgradeConfiguration"},
    "kubelet.config.k8s.io": {"KubeletConfiguration"},
    "kubeproxy.config.k8s.io": {"KubeProxyConfiguration"},
}

def run_crd_validator(resources: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate CRD definitions through the pinned official Kubernetes library."""
    try:
        completed = subprocess.run(
            ["go", "run", "."],
            cwd=CRD_VALIDATOR_DIR,
            input=json.dumps(resources, ensure_ascii=False),
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        raise RuntimeError(f"official CRD validation requires Go and the pinned helper: {exc}") from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip() or f"helper exited with status {completed.returncode}"
        raise RuntimeError(f"official CRD validation helper failed: {detail}")
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("official CRD validation helper returned malformed JSON") from exc
    if not isinstance(result, dict) or result.get("module_version") != CRD_VALIDATOR_VERSION or not isinstance(result.get("results"), list):
        raise RuntimeError("official CRD validation helper returned an invalid result or wrong module version")
    return result


def is_crd_definition(resource: _verify.ManifestResource) -> bool:
    return (
        resource.body.get("apiVersion") == "apiextensions.k8s.io/v1"
        and resource.body.get("kind") == "CustomResourceDefinition"
    )


def _resource_evidence(resource: _verify.ManifestResource, backend: str) -> dict[str, Any]:
    serialized = json.dumps(resource.body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return {
        "source": resource.path,
        "line": resource.document,
        "apiVersion": resource.body["apiVersion"],
        "kind": resource.body["kind"],
        "backend": backend,
        "body_sha256": hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
    }
EXCLUDED_PARTS = {".git", ".agents", ".serena", ".github", ".gitbook", "_book", "archive", "node_modules", "generated"}


def active_markdown(root: Path) -> list[Path]:
    """Deterministic active-doc inventory; archived, generated and hidden docs excluded."""
    return sorted(
        path for path in root.rglob("*.md")
        if not (EXCLUDED_PARTS & set(path.relative_to(root).parts))
        and not any(part.startswith(".") for part in path.relative_to(root).parts)
        and "en" not in path.relative_to(root).parts
    )


def yaml_fences(text: str):
    """Yield YAML fences and YAML documents embedded in shell heredocs."""
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        opening = FENCE.match(lines[i])
        if not opening:
            i += 1
            continue
        marker, info = opening.group(2), opening.group(3).strip().lower()
        language = info.split(None, 1)[0] if info else ""
        close = re.compile(r"^ {0,12}" + re.escape(marker[0]) + "{" + str(len(marker)) + r",}\s*$")
        end = i + 1
        while end < len(lines) and not close.match(lines[end]):
            end += 1
        closed = end < len(lines)
        context = "\n".join(lines[max(0, i - 8):i])

        if language in {"yaml", "yml"}:
            yield i + 2, info, "\n".join(lines[i + 1:end]), context, closed
        elif language in {"bash", "sh", "shell"}:
            h = i + 1
            while h < end:
                heredoc = re.search(r"<<(?!<)-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1", lines[h])
                if not heredoc:
                    h += 1
                    continue
                delimiter = heredoc.group(2)
                body_end = h + 1
                while body_end < end and lines[body_end].strip().lstrip("\t") != delimiter:
                    body_end += 1
                heredoc_closed = body_end < end
                heredoc_context = "\n".join(lines[max(0, i - 8):h])
                yield h + 2, "yaml heredoc", "\n".join(lines[h + 1:body_end]), heredoc_context, closed and heredoc_closed
                h = body_end + 1
        i = min(end + 1, len(lines))


def native_config(document: Any, path: str, context: str) -> bool:
    if not isinstance(document, dict):
        return False
    if document.get("kind") == "Config" and {"clusters", "users", "contexts"} & set(document):
        return True
    api_version = document.get("apiVersion")
    if isinstance(api_version, str):
        group = api_version.split("/", 1)[0] if "/" in api_version else ""
        return document.get("kind") in NATIVE_API_KINDS.get(group, set())
    if "apiVersion" in document or "kind" in document:
        return False
    if path.startswith("setup/cluster/samples/rke2/") and "native rke2 configuration" in context.lower():
        return True
    return bool(set(document) & NATIVE_KEYS) or bool(set(document) & {"containerd", "version", "logging", "storage", "network", "kubelet", "systemd"})

def inventory_docs(
    root: Path,
    paths: list[Path] | None = None,
    schema_loader=None,
    crd_validator: Callable[[list[dict[str, Any]]], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    resources: list[_verify.ManifestResource] = []
    for path in paths if paths is not None else active_markdown(root):
        rel = path.relative_to(root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append({"source": rel, "message": f"cannot read Markdown: {exc}"})
            continue
        for number, info, source, context, closed in yaml_fences(text):
            row: dict[str, Any] = {"source": rel, "line": number, "language": info}
            if not closed:
                errors.append({"source": rel, "line": str(number), "message": "YAML fence is not closed"})
                row["classification"] = "unclosed_fence"
                rows.append(row)
                continue
            if TEMPLATE_TOKEN.search(source):
                row["classification"] = "template"
                rows.append(row)
                continue
            if HISTORICAL.search(context):
                row["historical_context"] = True
            try:
                docs = list(yaml.load_all(source, Loader=_verify.UniqueKeyLoader))
            except (yaml.YAMLError, ValueError, TypeError) as exc:
                errors.append({"source": rel, "line": str(number), "message": f"YAML fence parse failed: {exc}"})
                row["classification"] = "invalid_yaml"
                rows.append(row)
                continue
            row["document_count"] = len(docs)
            row["classification"] = "yaml_data"
            for index, body in enumerate(docs, 1):
                document_ref = f"line {number}, doc {index}"
                if body is None:
                    errors.append({"source": rel, "line": str(number), "message": f"empty YAML document #{index}"})
                    continue
                if not isinstance(body, dict):
                    row["classification"] = "yaml_data"
                    continue
                if native_config(body, rel, context):
                    row["classification"] = "native_configuration"
                    api_version = body.get("apiVersion")
                    if isinstance(api_version, str) and "/" in api_version:
                        group, version = api_version.split("/", 1)
                        if group in NATIVE_API_VERSIONS and version not in NATIVE_API_VERSIONS[group]:
                            row["native_api_version_status"] = "not in current v1.37.1 schema set"
                            errors.append({"source": rel, "line": str(number), "message": f"native configuration API {api_version} is not in the known current Kubernetes v1.37.1 schema set"})
                    continue
                if "apiVersion" in body or "kind" in body:
                    inventory = _verify.Inventory(root=root)
                    _verify._append_resource(inventory, rel, document_ref, body)
                    if inventory.errors:
                        errors.extend({"source": rel, "line": str(number), "message": issue["message"]} for issue in inventory.errors)
                        continue
                    for resource in inventory.resources:
                        row.setdefault("resources", []).append({"apiVersion": resource.body["apiVersion"], "kind": resource.body["kind"]})
                        resources.append(resource)
                        row["classification"] = "served_api_resource" if _verify.is_builtin_resource(resource) else "custom_api_resource"
            rows.append(row)

    builtin = [resource for resource in resources if _verify.is_builtin_resource(resource)]
    custom = [resource for resource in resources if not _verify.is_builtin_resource(resource)]
    crds = [resource for resource in builtin if is_crd_definition(resource)]
    strict_builtin = [resource for resource in builtin if not is_crd_definition(resource)]
    keys: dict[str, list[_verify.ManifestResource]] = {}
    for resource in strict_builtin:
        try:
            keys.setdefault(_verify.schema_key(resource), []).append(resource)
        except (KeyError, ValueError) as exc:
            errors.append({"source": resource.path, "line": resource.document, "message": str(exc)})
    schemas, fetch_errors = (schema_loader or _verify.load_schemas)(keys)
    strict_validated: list[dict[str, Any]] = []
    for key, grouped in keys.items():
        if key in fetch_errors or key not in schemas:
            message = fetch_errors.get(key, f"strict schema {key} unavailable; validation cannot be skipped")
            errors.extend({"source": r.path, "line": r.document, "message": message} for r in grouped)
            continue
        for resource in grouped:
            try:
                problems = _verify._schema_problems(schemas[key], resource.body) + _verify._semantic_problems(resource)
            except Exception as exc:
                problems = [f"strict schema validation failed: {exc}"]
            if problems:
                errors.extend({"source": resource.path, "line": resource.document, "message": problem} for problem in problems)
            else:
                strict_validated.append(_resource_evidence(resource, "yannh/kubernetes-json-schema"))

    crd_validated: list[dict[str, Any]] = []
    if crds:
        runner = crd_validator or run_crd_validator
        requests = [
            {"id": str(index), "source": resource.path, "document": resource.document, "body": resource.body}
            for index, resource in enumerate(crds)
        ]
        try:
            response = runner(requests)
            if (
                not isinstance(response, dict)
                or response.get("module_version") != CRD_VALIDATOR_VERSION
                or not isinstance(response.get("results"), list)
            ):
                raise RuntimeError("official CRD validation helper returned an invalid result or wrong module version")
            results = {str(item["id"]): item for item in response["results"] if isinstance(item, dict) and "id" in item}
            if len(results) != len(crds) or set(results) != {str(i) for i in range(len(crds))}:
                raise RuntimeError("official CRD validation helper returned incomplete or duplicate resource results")
            for index, resource in enumerate(crds):
                result = results[str(index)]
                issues = result.get("errors")
                if not isinstance(issues, list):
                    raise RuntimeError("official CRD validation helper returned malformed validation errors")
                for issue in issues:
                    if not isinstance(issue, dict) or not all(isinstance(issue.get(key), str) for key in ("field", "type", "detail")):
                        raise RuntimeError("official CRD validation helper returned malformed validation error details")
                    errors.append({
                        "source": resource.path,
                        "line": resource.document,
                        "message": f"official CRD validation {issue['type']} at {issue['field']}: {issue['detail']}",
                    })
                if not issues:
                    crd_validated.append(_resource_evidence(resource, f"k8s.io/apiextensions-apiserver@{CRD_VALIDATOR_VERSION}"))
        except Exception as exc:
            errors.extend({"source": resource.path, "line": resource.document, "message": f"official CRD validation unavailable: {exc}"} for resource in crds)
    return {
        "schema_version": 1,
        "scope": "active Markdown under the repository, excluding archive/, en/, generated/ and hidden/tooling directories; both zh-TW and canonical docs included",
        "counts": {
            "markdown_files": len(paths if paths is not None else active_markdown(root)),
            "yaml_fences": len(rows),
            "served_api_objects": len(resources) - len(custom),
            "strict_schema_validated": len(strict_validated),
            "primary_crd_validated": len(crd_validated),
            "custom_api_objects_unvalidated": len(custom),
            "native_config_fences": sum(r["classification"] == "native_configuration" for r in rows),
            "template_fences": sum(r["classification"] == "template" for r in rows),
            "yaml_data_fences": sum(r["classification"] == "yaml_data" for r in rows),
            "errors": len(errors),
        },
        "inventory": rows,
        "validated": strict_validated + crd_validated,
        "custom_api_objects": [_resource_evidence(r, "unvalidated_custom_api") for r in custom],
        "errors_detail": errors,
        "limitations": [
            "Templates are explicitly classified but not expanded/rendered.",
            "Custom APIs are inventoried, not validated against vendor CRDs.",
            "Native configuration and plain YAML data are classified, not schema-validated.",
            "Official apiextensions-apiserver CRD validation is library validation, not API-server dry-run/installation.",
            "Historical context is heuristic, based on nearby text; the inventory must be reviewed when context is ambiguous.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    parser.add_argument("--output", type=Path, help="write machine-readable report to this path")
    args = parser.parse_args()
    report = inventory_docs(args.root.resolve())
    serialized = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    return 1 if report["errors_detail"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
