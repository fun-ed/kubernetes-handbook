"""Offline tests for the component release checker."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
import urllib.error
from copy import deepcopy
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check-component-updates.py"
SPEC = importlib.util.spec_from_file_location("component_updates", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load the component update checker.")
component_updates = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(component_updates)


def sample_watchlist():
    return {
        "schema_version": 1,
        "target_kubernetes_version": "v1.37.1",
        "snapshot_date": "2026-10-05",
        "components": [
            {
                "id": "example-component",
                "repository": "example/project",
                "baseline_version": "1.2.3",
                "release_url": "https://github.com/example/project/releases",
                "support_url": "https://example.org/support",
                "support_reviewed_on": "2026-10-05",
                "support_status": "not-confirmed",
                "supported_kubernetes_range": None,
                "support_notes": "Compatibility needs manual review.",
                "kubeadm_pin": None,
            }
        ],
    }


def release(tag, published_at="2026-10-04T12:00:00Z", prerelease=False, draft=False):
    return {
        "tag_name": tag,
        "published_at": published_at,
        "prerelease": prerelease,
        "draft": draft,
    }


class ComponentUpdateTests(unittest.TestCase):
    def setUp(self):
        component_updates._api_requests_made = 0

    def test_checked_in_watchlist_passes_schema_validation(self):
        watchlist = component_updates.load_watchlist(ROOT / "setup" / "component-watchlist.json")
        components = {component["id"]: component for component in watchlist["components"]}

        self.assertEqual(components["etcd"]["baseline_version"], "3.7.2")
        self.assertEqual(components["etcd"]["kubeadm_pin"]["version"], "3.7.0")
        self.assertEqual(components["coredns"]["baseline_version"], "1.14.7")
        self.assertEqual(components["coredns"]["kubeadm_pin"]["version"], "1.14.6")

    def test_fixture_reports_new_stable_release_and_utc_timestamp(self):
        watchlist = sample_watchlist()
        fixture_data = {
            "schema_version": 1,
            "releases": {
                "example/project": [
                    release("v1.2.4", "2026-10-04T15:15:00+03:00"),
                    release("v1.2.3"),
                ]
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            fixture_path = Path(directory) / "fixture.json"
            fixture_path.write_text(json.dumps(fixture_data), encoding="utf-8")
            fixture = component_updates.load_fixture(fixture_path, ["example/project"])

        report = component_updates.check_watchlist(
            watchlist, lambda repository, tag_prefix: fixture[repository]
        )
        self.assertEqual(report["status"], "ok")
        self.assertEqual(len(report["components"]), 1)
        component = report["components"][0]
        self.assertTrue(component["newer_release"])
        self.assertTrue(component["review_required"])
        self.assertEqual(component["baseline_version"], "1.2.3")
        self.assertEqual(component["latest_stable_version"], "1.2.4")
        self.assertEqual(component["published_at"], "2026-10-04T12:15:00Z")
        self.assertEqual(component["baseline_support"]["reviewed_version"], "1.2.3")
        self.assertEqual(report["support_checks"], "manual-only")

    def test_prereleases_and_drafts_do_not_replace_stable_baseline(self):
        watchlist = sample_watchlist()
        releases = [
            release("v9.0.0-rc.1"),
            release("v8.0.0", prerelease=True),
            release("v7.0.0", draft=True),
            release("v1.2.3"),
        ]

        report = component_updates.check_watchlist(watchlist, lambda repository, tag_prefix: releases)

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["components"][0]["latest_stable_version"], "1.2.3")
        self.assertFalse(report["components"][0]["newer_release"])
        self.assertFalse(report["components"][0]["review_required"])


    def test_k0s_same_patch_build_revision_requires_review(self):
        watchlist = sample_watchlist()
        watchlist["components"][0].update(
            {
                "id": "k0s",
                "repository": "k0sproject/k0s",
                "release_url": "https://github.com/k0sproject/k0s/releases",
                "baseline_version": "1.36.4+k0s.1",
                "tag_prefix": "v",
            }
        )
        releases = [
            release("v1.37.0+k0s.1-rc.1"),
            release("v1.36.4+k0s.2"),
            release("v1.36.4+k0s.1"),
            release("v0.13.1"),
        ]

        report = component_updates.check_watchlist(watchlist, lambda repository, tag_prefix: releases)

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["components"][0]["latest_stable_version"], "1.36.4+k0s.2")
        self.assertTrue(report["components"][0]["review_required"])

    def test_rke2_pagination_uses_larger_bounded_limit_than_other_repositories(self):
        calls = []

        def opener(request, timeout):
            page = int(request.full_url.rsplit("page=", 1)[1])
            calls.append(page)
            response = mock.MagicMock()
            response.__enter__.return_value = response
            payload = [{}] * 100 if page < component_updates.MAX_RKE2_API_PAGES else []
            response.read.return_value = json.dumps(payload).encode("utf-8")
            return response

        releases = component_updates.fetch_releases("rancher/rke2", "v", opener)
        self.assertEqual(len(releases), 100 * (component_updates.MAX_RKE2_API_PAGES - 1))
        self.assertEqual(calls, list(range(1, component_updates.MAX_RKE2_API_PAGES + 1)))

        with mock.patch.object(component_updates, "MAX_API_PAGES", 1):
            with self.assertRaises(component_updates.CheckError):
                component_updates.fetch_releases("example/project", "v", opener)

    def test_rke2_rebuild_revision_is_numeric_and_unknown_suffix_fails_closed(self):
        watchlist = sample_watchlist()
        watchlist["components"][0].update(
            {
                "id": "rke2",
                "repository": "rancher/rke2",
                "release_url": "https://github.com/rancher/rke2/releases",
                "baseline_version": "1.37.1+rke2r9",
                "tag_prefix": "v",
            }
        )
        releases = [release("v1.37.1+rke2r10"), release("v1.37.1+rke2r9")]

        report = component_updates.check_watchlist(watchlist, lambda repository, tag_prefix: releases)

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["components"][0]["latest_stable_version"], "1.37.1+rke2r10")
        self.assertTrue(report["components"][0]["review_required"])

        bad_release = [release("v1.37.1+unrecognized")]
        report = component_updates.check_watchlist(watchlist, lambda repository, tag_prefix: bad_release)
        self.assertEqual(report["status"], "error")

    def test_product_tag_prefixes_ignore_other_repository_releases(self):
        watchlist = sample_watchlist()
        cluster_autoscaler = watchlist["components"][0]
        cluster_autoscaler.update(
            {
                "id": "cluster-autoscaler",
                "repository": "kubernetes/autoscaler",
                "release_url": "https://github.com/kubernetes/autoscaler/releases",
                "baseline_version": "1.2.3",
                "tag_prefix": "cluster-autoscaler-",
                "tag_exclude_prefixes": ["cluster-autoscaler-chart-"],
                "tag_exclusion_notes": "The chart has its own release stream.",
            }
        )
        metrics_server = deepcopy(cluster_autoscaler)
        metrics_server.update(
            {
                "id": "metrics-server",
                "repository": "kubernetes-sigs/metrics-server",
                "release_url": "https://github.com/kubernetes-sigs/metrics-server/releases",
                "baseline_version": "0.9.0",
                "tag_prefix": "v",
                "tag_exclude_prefixes": [],
            }
        )
        watchlist["components"].append(metrics_server)
        releases = {
            "kubernetes/autoscaler": [
                release("vertical-pod-autoscaler-99.0.0"),
                release("cluster-autoscaler-chart-9.0.0"),
                release("cluster-autoscaler-1.2.4"),
                release("cluster-autoscaler-1.2.3"),
            ],
            "kubernetes-sigs/metrics-server": [
                release("metrics-server-helm-chart-9.0.0"),
                release("v0.9.0"),
            ],
        }

        report = component_updates.check_watchlist(
            watchlist, lambda repository, tag_prefix: releases[repository]
        )

        self.assertEqual(report["status"], "ok")
        components = {component["id"]: component for component in report["components"]}
        self.assertEqual(components["cluster-autoscaler"]["latest_stable_version"], "1.2.4")
        self.assertEqual(components["metrics-server"]["latest_stable_version"], "0.9.0")
        self.assertNotIn("support_status", components["metrics-server"])
        self.assertEqual(
            components["metrics-server"]["baseline_support"]["reviewed_version"], "0.9.0"
        )

    def test_malformed_prefixed_tag_fails_instead_of_being_ignored(self):
        watchlist = sample_watchlist()
        component = watchlist["components"][0]
        component["tag_prefix"] = "cluster-autoscaler-"
        releases = [release("cluster-autoscaler-not-a-version")]

        report = component_updates.check_watchlist(
            watchlist, lambda repository, tag_prefix: releases
        )

        self.assertEqual(report["status"], "error")
        self.assertIn("matching stable tag", report["errors"][0]["error"])

    def test_exact_legacy_tag_exclusions_do_not_hide_unrecognized_tags(self):
        watchlist = sample_watchlist()
        component = watchlist["components"][0]
        component["tag_prefix"] = "v"
        component["tag_exclude_tags"] = ["v001"]
        component["tag_exclusion_notes"] = "Legacy tag documented in upstream release history."
        releases = [release("v001"), release("v1.2.3")]

        report = component_updates.check_watchlist(
            watchlist, lambda repository, tag_prefix: releases
        )
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["components"][0]["latest_stable_version"], "1.2.3")

        unknown_legacy = [release("v002"), release("v1.2.3")]
        report = component_updates.check_watchlist(
            watchlist, lambda repository, tag_prefix: unknown_legacy
        )
        self.assertEqual(report["status"], "error")
        self.assertIn("matching stable tag", report["errors"][0]["error"])

    def test_product_exclusion_prefix_can_scope_unprefixed_api_tags(self):
        watchlist = sample_watchlist()
        component = watchlist["components"][0]
        component["tag_exclude_prefixes"] = ["api/"]
        component["tag_exclusion_notes"] = "API subtree is a separately versioned product."
        releases = [release("api/v99.0.0"), release("v1.2.3")]

        report = component_updates.check_watchlist(
            watchlist, lambda repository, tag_prefix: releases
        )
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["components"][0]["latest_stable_version"], "1.2.3")

    def test_authenticated_request_header_and_separate_budget_are_secret_safe(self):
        response = mock.MagicMock()
        response.__enter__.return_value = response
        response.read.return_value = json.dumps([release("v1.2.3")] * 100).encode("utf-8")
        opener = mock.Mock(return_value=response)

        with mock.patch.dict(component_updates.os.environ, {"GITHUB_TOKEN": "unit-test-token"}):
            with mock.patch.object(component_updates, "MAX_AUTHENTICATED_TOTAL_API_REQUESTS", 1):
                with mock.patch.object(component_updates, "MAX_API_PAGES", 2):
                    component_updates._api_requests_made = 0
                    with self.assertRaisesRegex(
                        component_updates.CheckError, "authenticated API request budget"
                    ) as raised:
                        component_updates.fetch_releases("example/project", opener=opener)
                    self.assertNotIn("unit-test-token", str(raised.exception))

        self.assertEqual(opener.call_count, 1)
        request = opener.call_args[0][0]
        self.assertEqual(request.get_header("Authorization"), "Bearer unit-test-token")

        with mock.patch.dict(component_updates.os.environ, {"GITHUB_TOKEN": ""}):
            with mock.patch.object(component_updates, "MAX_TOTAL_API_REQUESTS", 1):
                with mock.patch.object(component_updates, "MAX_API_PAGES", 2):
                    component_updates._api_requests_made = 0
                    with self.assertRaisesRegex(component_updates.CheckError, "public API request budget"):
                        component_updates.fetch_releases("example/project", opener=opener)

    def test_unprefixed_repository_uses_complete_paginated_release_list(self):
        response = mock.MagicMock()
        response.__enter__.return_value = response
        response.read.return_value = json.dumps([release("v1.2.3")]).encode("utf-8")
        opener = mock.Mock(return_value=response)

        releases = component_updates.fetch_releases("example/project", opener=opener)

        self.assertEqual(releases[0]["tag_name"], "v1.2.3")
        request = opener.call_args[0][0]
        self.assertTrue(request.full_url.endswith("/repos/example/project/releases?per_page=100&page=1"))
    def test_newer_semver_on_later_published_page_is_not_missed(self):
        newest_published_first = [release("v1.9.0")] * 100
        newest_published_later = [release("v1.10.0")]
        responses = []
        for payload in (newest_published_first, newest_published_later):
            response = mock.MagicMock()
            response.__enter__.return_value = response
            response.read.return_value = json.dumps(payload).encode("utf-8")
            responses.append(response)
        opener = mock.Mock(side_effect=responses)

        releases = component_updates.fetch_releases("example/project", opener=opener)
        newest = component_updates.latest_stable_release(releases)

        self.assertEqual(newest["version_text"], "1.10.0")
        self.assertEqual(opener.call_count, 2)

    def test_api_failure_is_an_error_not_a_no_update_result(self):
        watchlist = sample_watchlist()
        with mock.patch.object(
            component_updates.urllib.request,
            "urlopen",
            side_effect=urllib.error.URLError("private transport detail"),
        ):
            report = component_updates.check_watchlist(watchlist, component_updates.fetch_releases)

        self.assertEqual(report["status"], "error")
        self.assertEqual(report["components"], [])
        self.assertIn("request failed", report["errors"][0]["error"])
        self.assertNotIn("private transport detail", json.dumps(report))

    def test_cli_writes_error_report_and_nonzero_status_on_api_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            watchlist_path = Path(directory) / "watchlist.json"
            report_path = Path(directory) / "report.json"
            watchlist_path.write_text(json.dumps(sample_watchlist()), encoding="utf-8")

            with mock.patch.object(
                component_updates.urllib.request,
                "urlopen",
                side_effect=urllib.error.URLError("private transport detail"),
            ), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                exit_code = component_updates.main(
                    ["--watchlist", str(watchlist_path), "--output", str(report_path)]
                )

            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(exit_code, 1)
            self.assertEqual(report["status"], "error")
            self.assertIn("request failed", report["errors"][0]["error"])


    def test_malformed_stable_release_tag_fails_the_component_check(self):
        watchlist = sample_watchlist()
        releases = [release("release-current"), release("v1.2.3")]

        report = component_updates.check_watchlist(
            watchlist, lambda repository, tag_prefix: releases
        )

        self.assertEqual(report["status"], "error")
        self.assertEqual(report["components"], [])
        self.assertIn("not a version", report["errors"][0]["error"])

    def test_duplicate_component_id_is_rejected(self):
        watchlist = sample_watchlist()
        watchlist["components"].append(deepcopy(watchlist["components"][0]))

        with self.assertRaisesRegex(component_updates.CheckError, "duplicate component id"):
            component_updates.validate_watchlist(watchlist)

    def test_duplicate_repository_is_rejected(self):
        watchlist = sample_watchlist()
        duplicate = deepcopy(watchlist["components"][0])
        duplicate["id"] = "another-component"
        watchlist["components"].append(duplicate)

        with self.assertRaisesRegex(component_updates.CheckError, "duplicate repository"):
            component_updates.validate_watchlist(watchlist)

    def test_invalid_or_prerelease_baseline_is_rejected(self):
        watchlist = sample_watchlist()
        watchlist["components"][0]["baseline_version"] = "1.2.3-rc.1"

        with self.assertRaisesRegex(component_updates.CheckError, "stable three-part version"):
            component_updates.validate_watchlist(watchlist)

    def test_fixture_with_duplicate_json_keys_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture_path = Path(directory) / "fixture.json"
            fixture_path.write_text(
                '{"schema_version":1,"schema_version":1,"releases":{"example/project":[]}}',
                encoding="utf-8",
            )

            with self.assertRaisesRegex(component_updates.CheckError, "duplicate object key"):
                component_updates.load_fixture(fixture_path, ["example/project"])


def load_tests(loader, tests, pattern):
    if tests.countTestCases() < 17:
        raise RuntimeError("Component update test discovery is incomplete.")
    return tests
