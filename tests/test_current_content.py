"""Offline regression cases for the opt-in inline Markdown YAML scanner."""
from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check-current-content.py"
SPEC = importlib.util.spec_from_file_location("current_content", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load the current-content checker")
current_content = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(current_content)


class CurrentContentTests(unittest.TestCase):
    def scan(self, content: str, crd_validator=None, schema_loader=None):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "sample.md"
            path.write_text(content, encoding="utf-8")
            schema = {
                "type": "object",
                "properties": {
                    "apiVersion": {"type": "string"},
                    "kind": {"type": "string"},
                    "metadata": {
                        "type": "object",
                        "properties": {"name": {"type": "string"}},
                        "required": ["name"],
                        "additionalProperties": False,
                    },
                    "data": {"type": "object"},
                },
                "required": ["apiVersion", "kind", "metadata"],
                "additionalProperties": False,
            }
            loader = schema_loader or (lambda keys: ({key: schema for key in keys}, {}))
            return current_content.inventory_docs(
                root,
                [path],
                schema_loader=loader,
                crd_validator=crd_validator,
            )

    def test_duplicate_yaml_keys_fail_closed(self):
        report = self.scan("```yaml\napiVersion: v1\nkind: Pod\nmetadata:\n  name: one\n  name: two\n```\n")
        self.assertEqual(report["counts"]["errors"], 1)
        self.assertIn("duplicate key", report["errors_detail"][0]["message"])

    def test_malformed_yaml_is_reported_not_skipped(self):
        report = self.scan("```yaml\napiVersion: [\nkind: Pod\n```\n")
        self.assertEqual(report["inventory"][0]["classification"], "invalid_yaml")
        self.assertEqual(report["counts"]["errors"], 1)

    def test_custom_api_is_listed_without_claiming_schema_validation(self):
        report = self.scan("```yaml\napiVersion: demo.example.io/v1\nkind: Demo\nmetadata:\n  name: one\n```\n")
        self.assertEqual(report["counts"]["custom_api_objects_unvalidated"], 1)
        self.assertEqual(report["counts"]["strict_schema_validated"], 0)

    def test_native_kubeadm_configuration_is_not_classified_as_custom_resource(self):
        report = self.scan("```yaml\napiVersion: kubeadm.k8s.io/v1beta4\nkind: ClusterConfiguration\nclusterName: demo\n```\n")
        self.assertEqual(report["inventory"][0]["classification"], "native_configuration")
        self.assertEqual(report["counts"]["custom_api_objects_unvalidated"], 0)

    def test_native_audit_policy_is_classified_by_exact_group_and_kind(self):
        report = self.scan(
            "```yaml\napiVersion: audit.k8s.io/v1\nkind: Policy\nomitStages: [RequestReceived]\nrules: []\n```\n"
        )
        self.assertEqual(report["counts"]["native_config_fences"], 1)
        self.assertEqual(report["counts"]["custom_api_objects_unvalidated"], 0)

    def test_unknown_kind_in_native_group_is_not_exempted_as_configuration(self):
        report = self.scan(
            "```yaml\napiVersion: audit.k8s.io/v1\nkind: PolicyLike\nrules: []\n```\n"
        )
        self.assertEqual(report["counts"]["native_config_fences"], 0)
        self.assertEqual(report["counts"]["custom_api_objects_unvalidated"], 1)

    def test_template_is_explicitly_classified(self):
        report = self.scan("```yaml\napiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: {{ .Values.name }}\n```\n")
        self.assertEqual(report["inventory"][0]["classification"], "template")
        self.assertEqual(report["counts"]["template_fences"], 1)
    def test_historical_context_does_not_bypass_schema_validation(self):
        report = self.scan(
            "This is an older, removed example.\n"
            "```yaml\napiVersion: v1\nkind: Pod\nmetadata:\n  name: stale\nobsoleteField: true\n```\n"
        )
        self.assertTrue(report["inventory"][0]["historical_context"])
        self.assertEqual(report["counts"]["served_api_objects"], 1)
        self.assertEqual(report["counts"]["strict_schema_validated"], 0)
        self.assertEqual(report["counts"]["errors"], 1)
        self.assertIn("contains fields not allowed", report["errors_detail"][0]["message"])

    def test_literal_json_closing_braces_do_not_skip_schema_validation(self):
        report = self.scan(
            "```yaml\napiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: braces\n"
            "data:\n  payload: '{\"object\":{\"end\":\"}}\"}}'\nunexpected: true\n```\n"
        )
        self.assertEqual(report["counts"]["template_fences"], 0)
        self.assertEqual(report["counts"]["served_api_objects"], 1)
        self.assertEqual(report["counts"]["strict_schema_validated"], 0)
        self.assertEqual(report["counts"]["errors"], 1)
        self.assertIn("contains fields not allowed", report["errors_detail"][0]["message"])

    def test_bash_heredoc_resource_is_inventoried(self):
        report = self.scan(
            "```bash\ncat <<'EOF' | kubectl apply -f -\n"
            "apiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: inline\n"
            "data:\n  message: hello\nEOF\n```\n"
        )
        self.assertEqual(report["counts"]["strict_schema_validated"], 1)
        self.assertEqual(report["inventory"][0]["language"], "yaml heredoc")

    def test_unclosed_yaml_fence_fails_closed(self):
        report = self.scan("```yaml\napiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: open\n")
        self.assertEqual(report["inventory"][0]["classification"], "unclosed_fence")
        self.assertEqual(report["counts"]["errors"], 1)

    def test_missing_resource_identity_fails_closed(self):
        report = self.scan("```yaml\napiVersion: v1\nmetadata:\n  name: missing-kind\n```\n")
        self.assertEqual(report["counts"]["errors"], 1)

    def crd_fixture(self):
        return (
            "```yaml\n"
            "apiVersion: apiextensions.k8s.io/v1\n"
            "kind: CustomResourceDefinition\n"
            "metadata:\n"
            "  name: widgets.example.com\n"
            "spec:\n"
            "  group: example.com\n"
            "  scope: Namespaced\n"
            "  names:\n"
            "    plural: widgets\n"
            "    kind: Widget\n"
            "  versions:\n"
            "    - name: v1\n"
            "      served: true\n"
            "      storage: true\n"
            "      schema:\n"
            "        openAPIV3Schema:\n"
            "          type: object\n"
            "          properties:\n"
            "            spec:\n"
            "              type: object\n"
            "```\n"
        )

    def test_valid_crd_uses_primary_backend_and_separate_count(self):
        calls = []

        def validator(requests):
            calls.extend(requests)
            return {
                "module_version": "v0.37.1",
                "results": [{"id": "0", "errors": []}],
            }

        report = self.scan(self.crd_fixture(), crd_validator=validator)
        self.assertEqual(len(calls), 1)
        self.assertEqual(report["counts"]["primary_crd_validated"], 1)
        self.assertEqual(report["counts"]["strict_schema_validated"], 0)
        self.assertEqual(report["counts"]["errors"], 0)
        self.assertEqual(report["validated"][0]["backend"], "k8s.io/apiextensions-apiserver@v0.37.1")
        self.assertEqual(len(report["validated"][0]["body_sha256"]), 64)

    def test_invalid_crd_errors_from_primary_backend(self):
        report = self.scan(
            self.crd_fixture(),
            crd_validator=lambda requests: {
                "module_version": "v0.37.1",
                "results": [{
                    "id": "0",
                    "errors": [{
                        "field": "spec.versions[0].schema",
                        "type": "Invalid",
                        "detail": "must be a structural schema",
                    }],
                }],
            },
        )
        self.assertEqual(report["counts"]["primary_crd_validated"], 0)
        self.assertEqual(report["counts"]["errors"], 1)
        self.assertIn("structural schema", report["errors_detail"][0]["message"])

    def test_crd_helper_failures_and_wrong_versions_fail_closed(self):
        failures = [
            lambda requests: (_ for _ in ()).throw(FileNotFoundError("go missing")),
            lambda requests: {"module_version": "v0.37.0", "results": [{"id": "0", "errors": []}]},
            lambda requests: {"module_version": "v0.37.1", "results": []},
            lambda requests: {"module_version": "v0.37.1", "results": "malformed"},
        ]
        for runner in failures:
            with self.subTest(runner=runner):
                report = self.scan(self.crd_fixture(), crd_validator=runner)
                self.assertEqual(report["counts"]["primary_crd_validated"], 0)
                self.assertEqual(report["counts"]["errors"], 1)
                self.assertIn("official CRD validation unavailable", report["errors_detail"][0]["message"])

    def test_go_and_helper_failures_fail_closed_without_running_a_compiler(self):
        completed = lambda returncode, stdout="", stderr="": subprocess.CompletedProcess(
            args=["go", "run", "."],
            returncode=returncode,
            stdout=stdout,
            stderr=stderr,
        )
        failure_cases = [
            (FileNotFoundError("go is not installed"), None),
            (None, completed(1, stderr="build failed")),
            (None, completed(0, stdout="{")),
            (None, completed(0, stdout='{"module_version":"v0.37.0","results":[]}')),
        ]
        for side_effect, return_value in failure_cases:
            with self.subTest(side_effect=side_effect, return_value=return_value):
                with patch.object(
                    current_content.subprocess,
                    "run",
                    side_effect=side_effect,
                    return_value=return_value,
                ) as runner:
                    report = self.scan(self.crd_fixture())
                runner.assert_called_once()
                self.assertEqual(report["counts"]["primary_crd_validated"], 0)
                self.assertEqual(report["counts"]["errors"], 1)
                self.assertIn("official CRD validation unavailable", report["errors_detail"][0]["message"])

    def test_missing_non_crd_builtin_schema_still_fails_closed(self):
        report = self.scan(
            "```yaml\napiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: one\ndata: {}\n```\n",
            schema_loader=lambda keys: ({}, {key: "offline schema unavailable" for key in keys}),
        )
        self.assertEqual(report["counts"]["strict_schema_validated"], 0)
        self.assertEqual(report["counts"]["errors"], 1)
        self.assertIn("offline schema unavailable", report["errors_detail"][0]["message"])


if __name__ == "__main__":
    unittest.main()
