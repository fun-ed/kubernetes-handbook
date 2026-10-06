#!/usr/bin/env python3
"""Compare reviewed component baselines with stable GitHub releases."""

from __future__ import annotations

import argparse
import http.client
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple
from urllib.parse import urlparse


SCHEMA_VERSION = 1
API_BASE = "https://api.github.com"
API_PAGE_SIZE = 100
MAX_API_PAGES = 10
MAX_RKE2_API_PAGES = 13
MAX_TOTAL_API_REQUESTS = 55
MAX_AUTHENTICATED_TOTAL_API_REQUESTS = 500
_api_requests_made = 0
API_TIMEOUT_SECONDS = 8
SUPPORT_STATUSES = {
    "confirmed-1.37",
    "known-issue",
    "matrix-excludes-target",
    "not-confirmed",
    "not-tested",
    "same-minor-guidance",
}
VERSION_RE = re.compile(
    r"^v?(?P<major>0|[1-9][0-9]{0,8})\.(?P<minor>0|[1-9][0-9]{0,8})\."
    r"(?P<patch>0|[1-9][0-9]{0,8})(?P<prerelease>-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+(?P<build>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)
DISTRO_REVISIONS = {"k0s": re.compile(r"^k0s\.(\d+)$"), "rke2": re.compile(r"^rke2r(\d+)$")}
DISTRO_PRERELEASE_BUILD = re.compile(
    r"^(?:k0s\.[0-9]+|rke2r[0-9]+)[.-](?:alpha|beta|rc|preview|dev)(?:[.-][0-9A-Za-z-]+)*$",
    re.IGNORECASE,
)
DISTRO_IDS = frozenset(DISTRO_REVISIONS)
REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
COMPONENT_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TAG_PREFIX_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

TAG_EXCLUDE_PREFIX_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")

class CheckError(ValueError):
    """An invalid watchlist or incomplete upstream release response."""


def _object_without_duplicate_keys(pairs: List[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CheckError("JSON contains a duplicate object key.")
        result[key] = value
    return result


def _load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file, object_pairs_hook=_object_without_duplicate_keys)
    except json.JSONDecodeError as error:
        raise CheckError("JSON input is malformed.") from error
    except OSError as error:
        raise CheckError("JSON input could not be read.") from error


def parse_stable_version(value: Any, label: str) -> Tuple[int, int, int]:
    if not isinstance(value, str):
        raise CheckError(f"{label} must be a stable three-part version string.")
    match = VERSION_RE.fullmatch(value)
    if not match or match.group("prerelease"):
        raise CheckError(f"{label} must be a stable three-part version string.")
    return int(match.group("major")), int(match.group("minor")), int(match.group("patch"))


def _distro_revision(value: str, component_id: str) -> int:
    match = VERSION_RE.fullmatch(value)
    build = match.group("build") if match else None
    if component_id == "k0s" and build is None:
        return 0
    revision_match = DISTRO_REVISIONS[component_id].fullmatch(build or "") if match else None
    if revision_match is None:
        raise CheckError(f"{component_id} release must use its recognized stable build revision suffix.")
    return int(revision_match.group(1))


def _valid_date(value: Any, label: str) -> date:
    if not isinstance(value, str):
        raise CheckError(f"{label} must be an ISO date.")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise CheckError(f"{label} must be an ISO date.") from error
    if parsed.isoformat() != value:
        raise CheckError(f"{label} must be an ISO date.")
    return parsed


def _valid_https_url(value: Any, label: str) -> None:
    if not isinstance(value, str):
        raise CheckError(f"{label} must be an HTTPS URL.")
    try:
        parsed = urlparse(value)
        valid = parsed.scheme == "https" and bool(parsed.hostname) and not parsed.username and not parsed.password
    except ValueError:
        valid = False
    if not valid:
        raise CheckError(f"{label} must be an HTTPS URL without credentials.")


def validate_watchlist(data: Any) -> Dict[str, Any]:
    required_root = {"schema_version", "target_kubernetes_version", "snapshot_date", "components"}
    if not isinstance(data, dict) or set(data) != required_root:
        raise CheckError("Watchlist must contain the documented top-level fields only.")
    if type(data["schema_version"]) is not int or data["schema_version"] != SCHEMA_VERSION:
        raise CheckError("Watchlist schema_version is unsupported.")

    parse_stable_version(data["target_kubernetes_version"], "target_kubernetes_version")
    snapshot_date = _valid_date(data["snapshot_date"], "snapshot_date")
    components = data["components"]
    if not isinstance(components, list) or not components:
        raise CheckError("Watchlist components must be a non-empty array.")

    required_component = {
        "id",
        "repository",
        "baseline_version",
        "release_url",
        "support_url",
        "support_reviewed_on",
        "support_status",
        "supported_kubernetes_range",
        "support_notes",
        "kubeadm_pin",
    }
    seen_ids = set()
    seen_repositories = set()
    for component in components:
        if not isinstance(component, dict):
            raise CheckError("Each component must be an object.")
        component_fields = set(component)
        optional_component_fields = {
            "tag_prefix",
            "tag_exclude_prefixes",
            "tag_exclude_tags",
            "tag_exclusion_notes",
        }
        if (
            not required_component.issubset(component_fields)
            or component_fields - required_component - optional_component_fields
        ):
            raise CheckError("Each component must contain the documented fields only.")

        component_id = component["id"]
        repository = component["repository"]
        if not isinstance(component_id, str) or not COMPONENT_ID_RE.fullmatch(component_id):
            raise CheckError("Component id must be lowercase words separated by hyphens.")
        if component_id in seen_ids:
            raise CheckError(f"Watchlist contains duplicate component id: {component_id}.")
        seen_ids.add(component_id)

        if not isinstance(repository, str) or not REPOSITORY_RE.fullmatch(repository):
            raise CheckError(f"Component {component_id} has an invalid GitHub repository.")
        if repository.lower() in seen_repositories:
            raise CheckError(f"Watchlist contains duplicate repository: {repository}.")
        seen_repositories.add(repository.lower())
        tag_prefix = component.get("tag_prefix")
        if tag_prefix is not None and (
            not isinstance(tag_prefix, str) or not TAG_PREFIX_RE.fullmatch(tag_prefix)
        ):
            raise CheckError(f"Component {component_id} has an invalid tag_prefix.")
        excluded_prefixes = component.get("tag_exclude_prefixes", [])
        if not isinstance(excluded_prefixes, list):
            raise CheckError(f"Component {component_id} tag_exclude_prefixes must be an array.")
        seen_excluded_prefixes = set()
        for excluded_prefix in excluded_prefixes:
            if (
                not isinstance(excluded_prefix, str)
                or not TAG_EXCLUDE_PREFIX_RE.fullmatch(excluded_prefix)
                or (tag_prefix is not None and not excluded_prefix.startswith(tag_prefix))
            ):
                raise CheckError(f"Component {component_id} has an invalid excluded tag prefix.")
            if excluded_prefix in seen_excluded_prefixes:
                raise CheckError(f"Component {component_id} has duplicate excluded tag prefixes.")
            seen_excluded_prefixes.add(excluded_prefix)
        excluded_tags = component.get("tag_exclude_tags", [])
        if not isinstance(excluded_tags, list):
            raise CheckError(f"Component {component_id} tag_exclude_tags must be an array.")
        seen_excluded_tags = set()
        for excluded_tag in excluded_tags:
            if (
                not isinstance(excluded_tag, str)
                or not TAG_PREFIX_RE.fullmatch(excluded_tag)
                or (tag_prefix is not None and not excluded_tag.startswith(tag_prefix))
            ):
                raise CheckError(f"Component {component_id} has an invalid excluded tag.")
            if excluded_tag in seen_excluded_tags:
                raise CheckError(f"Component {component_id} has duplicate excluded tags.")
            seen_excluded_tags.add(excluded_tag)
        exclusion_notes = component.get("tag_exclusion_notes")
        if (excluded_prefixes or excluded_tags) and (
            not isinstance(exclusion_notes, str) or not exclusion_notes.strip()
        ):
            raise CheckError(f"Component {component_id} tag exclusions need source notes.")

        parse_stable_version(component["baseline_version"], f"{component_id}.baseline_version")
        expected_release_url = f"https://github.com/{repository}/releases"
        if component["release_url"] != expected_release_url:
            raise CheckError(f"Component {component_id} release_url must link to its GitHub releases.")
        _valid_https_url(component["support_url"], f"{component_id}.support_url")

        reviewed_on = _valid_date(component["support_reviewed_on"], f"{component_id}.support_reviewed_on")
        if reviewed_on > snapshot_date:
            raise CheckError(f"Component {component_id} support review is later than the snapshot date.")
        support_status = component["support_status"]
        if not isinstance(support_status, str) or support_status not in SUPPORT_STATUSES:
            raise CheckError(f"Component {component_id} has an unknown support_status.")

        supported_range = component["supported_kubernetes_range"]
        if supported_range is not None and (not isinstance(supported_range, str) or not supported_range.strip()):
            raise CheckError(f"Component {component_id} supported_kubernetes_range must be text or null.")
        if not isinstance(component["support_notes"], str) or not component["support_notes"].strip():
            raise CheckError(f"Component {component_id} support_notes must be non-empty text.")

        pin = component["kubeadm_pin"]
        if pin is not None:
            if not isinstance(pin, dict) or set(pin) != {"version", "pin_type", "source_url"}:
                raise CheckError(f"Component {component_id} kubeadm_pin has invalid fields.")
            parse_stable_version(pin["version"], f"{component_id}.kubeadm_pin.version")
            if pin["pin_type"] != "kubeadm-default":
                raise CheckError(f"Component {component_id} pin_type must be kubeadm-default.")
            expected_source = (
                "https://github.com/kubernetes/kubernetes/blob/"
                f"{data['target_kubernetes_version']}/build/dependencies.yaml"
            )
            if pin["source_url"] != expected_source:
                raise CheckError(f"Component {component_id} kubeadm pin must cite the target Kubernetes source pin.")

    return data


def load_watchlist(path: Path) -> Dict[str, Any]:
    return validate_watchlist(_load_json(path))


def load_fixture(path: Path, repositories: Sequence[str]) -> Dict[str, List[Any]]:
    data = _load_json(path)
    if not isinstance(data, dict) or set(data) != {"schema_version", "releases"}:
        raise CheckError("Fixture must contain schema_version and releases fields only.")
    if type(data["schema_version"]) is not int or data["schema_version"] != SCHEMA_VERSION:
        raise CheckError("Fixture schema_version is unsupported.")
    releases = data["releases"]
    if not isinstance(releases, dict):
        raise CheckError("Fixture releases must be an object keyed by repository.")
    expected = set(repositories)
    actual = set(releases)
    if actual != expected:
        raise CheckError("Fixture repositories must exactly match the component watchlist.")
    for repository, rows in releases.items():
        if not isinstance(rows, list):
            raise CheckError(f"Fixture releases for {repository} must be an array.")
    return releases


def _fetch_api_json(url: str, opener: Callable[..., Any]) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "kubernetes-handbook-component-watch/1",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with opener(request, timeout=API_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        raise CheckError(f"GitHub release API returned HTTP {error.code}.") from error
    except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException) as error:
        raise CheckError("GitHub release API request failed.") from error
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CheckError("GitHub release API returned malformed JSON.") from error


def fetch_releases(
    repository: str,
    tag_prefix: Optional[str] = None,
    opener: Optional[Callable[..., Any]] = None,
) -> List[Any]:
    if opener is None:
        opener = urllib.request.urlopen

    # GitHub's /releases/latest follows publication order, not SemVer order.
    # Scan every public release page so an older-but-later-published branch
    # cannot hide the numerically greatest stable tag.
    releases: List[Any] = []
    global _api_requests_made
    token = os.environ.get("GITHUB_TOKEN")
    request_budget = (
        MAX_AUTHENTICATED_TOTAL_API_REQUESTS if token else MAX_TOTAL_API_REQUESTS
    )
    page_limit = MAX_RKE2_API_PAGES if repository.lower() == "rancher/rke2" else MAX_API_PAGES
    for page in range(1, page_limit + 1):
        if _api_requests_made >= request_budget:
            budget_kind = "authenticated" if token else "public"
            raise CheckError(f"GitHub {budget_kind} API request budget reached; rerun later.")
        _api_requests_made += 1
        url = f"{API_BASE}/repos/{repository}/releases?per_page={API_PAGE_SIZE}&page={page}"
        payload = _fetch_api_json(url, opener)
        if not isinstance(payload, list):
            raise CheckError("GitHub release API response must be an array.")
        releases.extend(payload)
        if len(payload) < API_PAGE_SIZE:
            return releases

    raise CheckError("GitHub release API pagination limit reached before the result was complete.")

def _published_at(value: Any) -> str:
    if not isinstance(value, str):
        raise CheckError("GitHub release API returned a stable release without published_at.")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise CheckError("GitHub release API returned an invalid published_at timestamp.") from error
    if parsed.tzinfo is None:
        raise CheckError("GitHub release API returned a published_at timestamp without a timezone.")
    return parsed.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def latest_stable_release(
    releases: Any,
    tag_prefix: Optional[str] = None,
    tag_exclude_prefixes: Sequence[str] = (),
    component_id: Optional[str] = None,
    tag_exclude_tags: Sequence[str] = (),
) -> Dict[str, Any]:
    if not isinstance(releases, list):
        raise CheckError("GitHub release API response must be an array.")
    stable = []
    for release in releases:
        if not isinstance(release, dict):
            raise CheckError("GitHub release API returned a non-object release.")
        tag = release.get("tag_name")
        if not isinstance(tag, str) or not tag:
            raise CheckError("GitHub release API returned a release without tag_name.")
        prerelease = release.get("prerelease")
        draft = release.get("draft")
        if type(prerelease) is not bool or type(draft) is not bool:
            raise CheckError("GitHub release API returned invalid prerelease or draft flags.")
        if draft or prerelease:
            continue
        if tag in tag_exclude_tags:
            continue
        if any(tag.startswith(prefix) for prefix in tag_exclude_prefixes):
            continue
        if tag_prefix is not None and not tag.startswith(tag_prefix):
            continue
        version_tag = tag[len(tag_prefix):] if tag_prefix else tag
        match = VERSION_RE.fullmatch(version_tag)
        if not match:
            raise CheckError("GitHub release API returned a matching stable tag that is not a version.")
        if match.group("prerelease"):
            continue
        build_metadata = match.group("build") or ""
        if component_id in DISTRO_IDS and DISTRO_PRERELEASE_BUILD.fullmatch(build_metadata):
            continue
        version = tuple(int(match.group(part)) for part in ("major", "minor", "patch"))
        revision = _distro_revision(version_tag, component_id) if component_id in DISTRO_IDS else 0
        stable.append(
            {
                "version": version,
                "revision": revision,
                "version_text": version_tag[1:] if version_tag.startswith("v") else version_tag,
                "tag": tag,
                "published_at": _published_at(release.get("published_at")),
            }
        )

    if not stable:
        raise CheckError("GitHub release API returned no matching stable semantic-version release.")
    return max(stable, key=lambda release: (release["version"], release["revision"], release["tag"]))


def check_watchlist(
    watchlist: Dict[str, Any],
    release_loader: Callable[[str, Optional[str]], List[Any]],
) -> Dict[str, Any]:
    global _api_requests_made
    _api_requests_made = 0
    validate_watchlist(watchlist)
    report_components = []
    errors = []

    for component in watchlist["components"]:
        try:
            tag_prefix = component.get("tag_prefix")
            releases = release_loader(component["repository"], tag_prefix)
            latest = latest_stable_release(
                releases,
                tag_prefix,
                component.get("tag_exclude_prefixes", []),
                component["id"],
                component.get("tag_exclude_tags", []),
            )
            baseline_version = parse_stable_version(
                component["baseline_version"], f"{component['id']}.baseline_version"
            )
            baseline_revision = (
                _distro_revision(component["baseline_version"], component["id"])
                if component["id"] in DISTRO_IDS
                else 0
            )
            latest_order = (latest["version"], latest["revision"])
            baseline_order = (baseline_version, baseline_revision)
            if latest_order < baseline_order:
                raise CheckError("GitHub's newest stable release is older than the recorded baseline.")
            newer = latest_order > baseline_order
            report_components.append(
                {
                    "id": component["id"],
                    "repository": component["repository"],
                    "baseline_version": component["baseline_version"],
                    "latest_stable_version": latest["version_text"],
                    "latest_stable_tag": latest["tag"],
                    "published_at": latest["published_at"],
                    "release_url": (
                        f"https://github.com/{component['repository']}/releases/tag/{latest['tag']}"
                    ),
                    "newer_release": newer,
                    "review_required": newer,
                    "baseline_support": {
                        "reviewed_version": component["baseline_version"],
                        "status": component["support_status"],
                        "reviewed_on": component["support_reviewed_on"],
                        "supported_kubernetes_range": component["supported_kubernetes_range"],
                        "support_url": component["support_url"],
                        "notes": component["support_notes"],
                    },
                    "kubeadm_pin": component["kubeadm_pin"],
                }
            )
        except CheckError as error:
            errors.append({"component": component["id"], "error": str(error)})

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "target_kubernetes_version": watchlist["target_kubernetes_version"],
        "snapshot_date": watchlist["snapshot_date"],
        "status": "error" if errors else "ok",
        "support_checks": "manual-only",
        "components": report_components,
        "errors": errors,
    }


def error_report(error: str, watchlist: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "target_kubernetes_version": watchlist.get("target_kubernetes_version") if watchlist else None,
        "snapshot_date": watchlist.get("snapshot_date") if watchlist else None,
        "status": "error",
        "support_checks": "manual-only",
        "components": [],
        "errors": [{"component": None, "error": error}],
    }


def print_summary(report: Dict[str, Any]) -> None:
    updated = [component for component in report["components"] if component["review_required"]]
    if report["status"] == "error":
        print(
            f"Component release check failed; {len(report['components'])} component(s) have usable results."
        )
    elif updated:
        print(f"{len(updated)} newer stable release(s) need manual review.")
    else:
        print("No newer stable releases than the recorded baselines were found.")

    for component in updated:
        print(
            f"{component['id']}: {component['baseline_version']} -> "
            f"{component['latest_stable_version']} (published {component['published_at']}); "
            "review Kubernetes compatibility before changing a pin."
        )
    for error in report["errors"]:
        label = error["component"] or "watchlist"
        print(f"ERROR [{label}]: {error['error']}", file=sys.stderr)
    print("Kubernetes compatibility checks remain manual.")


def _write_report(path: Path, report: Dict[str, Any]) -> None:
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: Optional[Sequence[str]] = None) -> int:
    default_watchlist = Path(__file__).resolve().parents[1] / "setup" / "component-watchlist.json"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--watchlist", type=Path, default=default_watchlist, help="component watchlist JSON file"
    )
    parser.add_argument("--fixture", type=Path, help="offline GitHub Releases API fixture JSON")
    parser.add_argument("--output", type=Path, help="write the machine-readable JSON report to this file")
    args = parser.parse_args(argv)

    watchlist = None
    try:
        watchlist = load_watchlist(args.watchlist)
        if args.fixture:
            fixture = load_fixture(
                args.fixture, [component["repository"] for component in watchlist["components"]]
            )
            release_loader = lambda repository, tag_prefix: fixture[repository]
        else:
            release_loader = fetch_releases
        report = check_watchlist(watchlist, release_loader)
    except CheckError as error:
        report = error_report(str(error), watchlist)

    if args.output:
        try:
            _write_report(args.output, report)
        except OSError:
            print("ERROR: Could not write the JSON report.", file=sys.stderr)
            return 2
        print_summary(report)
    else:
        print_summary(report)
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
