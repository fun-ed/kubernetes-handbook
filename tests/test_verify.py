import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from scripts import verify


VALID_SCHEMA = {
    "type": "object",
    "required": ["apiVersion", "kind", "metadata"],
    "properties": {
        "apiVersion": {"type": "string"},
        "kind": {"type": "string"},
        "metadata": {"type": "object", "required": ["name"]},
        "spec": {"type": "object"},
    },
    "additionalProperties": False,
}


class VerifyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "examples").mkdir()
        (self.root / "manifests").mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def write(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def fake_schema_loader(self, keys):
        return {key: VALID_SCHEMA for key in keys}, {}

    def test_yaml_loader_rejects_duplicate_keys(self):
        self.write(
            "examples/duplicate.yaml",
            "apiVersion: v1\nkind: Pod\nkind: Service\nmetadata:\n  name: demo\n",
        )

        inventory = verify.collect_manifest_resources(self.root)

        self.assertEqual(inventory.resources, [])
        self.assertEqual(len(inventory.errors), 1)
        self.assertIn("duplicate key", inventory.errors[0]["message"])

    def test_historical_file_is_excluded_and_list_items_are_counted(self):
        self.write(
            "examples/old.yaml",
            "# HISTORICAL: archived example\napiVersion: v1\nkind: Pod\nmetadata:\n  name: old\n",
        )
        self.write(
            "manifests/resources.yml",
            "apiVersion: v1\nkind: List\nitems:\n"
            "  - apiVersion: v1\n    kind: Pod\n    metadata:\n      name: one\n"
            "  - apiVersion: v1\n    kind: Service\n    metadata:\n      name: two\n"
            "---\nnull\n",
        )

        inventory = verify.collect_manifest_resources(self.root)

        self.assertEqual(inventory.yaml_files, 2)
        self.assertEqual(inventory.historical_files, ["examples/old.yaml"])
        self.assertEqual(inventory.empty_documents, 1)
        self.assertEqual(len(inventory.resources), 2)
        self.assertEqual(
            [resource.document for resource in inventory.resources],
            ["1.items[0]", "1.items[1]"],
        )
        self.assertFalse(inventory.errors)


    def test_valid_builtin_resource_is_counted_as_validated(self):
        self.write(
            "examples/pod.yaml",
            "apiVersion: v1\nkind: Pod\nmetadata:\n  name: demo\n  creationTimestamp: 2024-01-01T00:00:00Z\n",
        )

        result = verify.validate_local(self.root, schema_loader=self.fake_schema_loader)

        self.assertEqual(result.builtin_validated, 1)
        self.assertIsInstance(result.inventory.resources[0].body["metadata"]["creationTimestamp"], str)
        self.assertFalse(result.errors)

    def test_invalid_json_schema_fails_closed(self):
        self.write(
            "examples/pod.yaml",
            "apiVersion: v1\nkind: Pod\nmetadata:\n  name: demo\n",
        )

        def malformed_schema_loader(keys):
            return {key: {"type": "not-a-json-schema-type"} for key in keys}, {}

        result = verify.validate_local(self.root, schema_loader=malformed_schema_loader)

        self.assertEqual(result.builtin_validated, 0)
        self.assertTrue(any("schema validation failed" in error["message"] for error in result.errors))

    def test_yaml_merge_override_is_accepted_but_explicit_duplicates_are_not(self):
        self.write(
            "examples/pod.yaml",
            "apiVersion: v1\nkind: Pod\nmetadata:\n"
            "  <<: &defaults\n    name: merged\n"
            "  name: explicit\n",
        )

        inventory = verify.collect_manifest_resources(self.root)

        self.assertFalse(inventory.errors)
        self.assertEqual(inventory.resources[0].body["metadata"]["name"], "explicit")

    def test_malformed_yaml_fails_without_skipping_schema_validation(self):
        self.write("examples/bad.yaml", "apiVersion: [unterminated\n")

        result = verify.validate_local(self.root, schema_loader=self.fake_schema_loader)

        self.assertEqual(result.builtin_validated, 0)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("YAML", result.errors[0]["document"])

    def test_invalid_api_version_is_an_error_not_an_unvalidated_custom_resource(self):
        self.write(
            "examples/bad-api.yaml",
            "apiVersion: gateway.networking.k8s.io/v1/extra\nkind: HTTPRoute\nmetadata:\n  name: route\n",
        )

        result = verify.validate_local(self.root, schema_loader=self.fake_schema_loader)

        self.assertEqual(result.custom_resources, [])
        self.assertTrue(any("invalid Kubernetes apiVersion syntax" in error["message"] for error in result.errors))

    def test_strict_builtin_schema_rejects_malformed_object(self):
        self.write(
            "examples/pod.yaml",
            "apiVersion: v1\nkind: Pod\nmetadata:\n  name: demo\nunknownField: true\n",
        )

        result = verify.validate_local(self.root, schema_loader=self.fake_schema_loader)

        self.assertEqual(result.builtin_validated, 0)
        self.assertTrue(any("not allowed by the strict schema" in error["message"] for error in result.errors))

    def test_custom_resource_is_not_claimed_as_locally_validated(self):
        self.write(
            "manifests/custom.yaml",
            "apiVersion: gateway.networking.k8s.io/v1\nkind: HTTPRoute\nmetadata:\n  name: route\n",
        )

        result = verify.validate_local(self.root, schema_loader=self.fake_schema_loader)
        report = verify.build_local_report(result)

        self.assertEqual(result.builtin_validated, 0)
        self.assertEqual(len(result.custom_resources), 1)
        self.assertEqual(report["counts"]["custom_resources_not_validated_locally"], 1)
        self.assertEqual(report["validated"]["builtin_resources_by_strict_schema"], 0)

    def test_deployment_selector_mismatch_is_reported(self):
        self.write(
            "examples/deployment.yaml",
            "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: demo\n"
            "spec:\n  selector:\n    matchLabels:\n      app: selected\n"
            "  template:\n    metadata:\n      labels:\n        app: different\n"
            "    spec: {}\n",
        )

        result = verify.validate_local(self.root, schema_loader=self.fake_schema_loader)

        self.assertTrue(any("do not match" in error["message"] for error in result.errors))
        self.assertEqual(result.builtin_validated, 0)

    def test_server_and_each_kubelet_must_match_exact_target_patch(self):
        correct_server = {"serverVersion": {"gitVersion": "v1.37.1"}}
        correct_nodes = {
            "items": [
                {"metadata": {"name": "control-plane"}, "status": {"nodeInfo": {"kubeletVersion": "v1.37.1"}}},
                {"metadata": {"name": "worker"}, "status": {"nodeInfo": {"kubeletVersion": "v1.37.1"}}},
            ]
        }
        verified = verify.assert_exact_versions(correct_server, correct_nodes)
        self.assertEqual(len(verified["kubelets"]), 2)

        wrong_server = {"serverVersion": {"gitVersion": "v1.37.0"}}
        with self.assertRaisesRegex(verify.VerificationError, "refusing API writes"):
            verify.assert_exact_versions(wrong_server, correct_nodes)

        wrong_kubelet = json.loads(json.dumps(correct_nodes))
        wrong_kubelet["items"][1]["status"]["nodeInfo"]["kubeletVersion"] = "v1.37.0"
        with self.assertRaisesRegex(verify.VerificationError, "node 'worker' kubelet"):
            verify.assert_exact_versions(correct_server, wrong_kubelet)

    def test_cluster_commands_are_bound_to_a_private_kubeconfig(self):
        command = verify.kubectl_command("kubectl", "/private/run/kubeconfig", ["get", "nodes"])
        self.assertEqual(command[:3], ["kubectl", "--kubeconfig", "/private/run/kubeconfig"])
        self.assertIn("get", command)

        args = verify.parse_arguments(["--cluster", "--image", "local/test-node:v1.37.1"])
        self.assertTrue(args.cluster)
        with self.assertRaises(SystemExit):
            verify.parse_arguments(
                ["--cluster", "--image", "local/test-node:v1.37.1", "--kubeconfig", "/tmp/user-config"]
            )

    def test_server_validation_uses_non_server_side_dry_run_apply(self):
        resource = verify.ManifestResource(
            "examples/pod.yaml",
            "1",
            {"apiVersion": "v1", "kind": "Pod", "metadata": {"name": "demo"}},
        )
        completed = verify.subprocess.CompletedProcess([], 0, "", "")

        with patch.object(verify.subprocess, "run", return_value=completed) as run:
            verify._server_dry_run(resource, "kubectl", Path("/private/run/kubeconfig"))

        command = run.call_args.args[0]
        self.assertIn("--dry-run=server", command)
        self.assertIn("--validate=strict", command)
        self.assertNotIn("--server-side", command)
        self.assertFalse(any(argument.startswith("--field-manager=") for argument in command))

    def test_calico_source_matches_only_projectcalico_v3_globalnetworkpolicy(self):
        source = verify.CALICO_GLOBAL_NETWORK_POLICY_CRD
        resource = verify.ManifestResource(
            "manifests/global-network-policy.yaml",
            "1",
            {"apiVersion": "projectcalico.org/v3", "kind": "GlobalNetworkPolicy"},
        )
        self.assertEqual(verify._required_crd_releases([resource]), [source])

        crd = """apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: globalnetworkpolicies.projectcalico.org
spec:
  group: projectcalico.org
  names:
    kind: GlobalNetworkPolicy
  versions:
    - name: v3
      served: true
      storage: true
"""
        names, crd_yaml, excluded = verify._crds_for_apply_from_release(source, crd)

        installed = verify.yaml.safe_load(crd_yaml)
        self.assertEqual(names, ["globalnetworkpolicies.projectcalico.org"])
        self.assertEqual(installed["spec"]["group"], "projectcalico.org")
        self.assertEqual(installed["spec"]["versions"][0]["name"], "v3")
        self.assertFalse(excluded)

        old_group_resource = verify.ManifestResource(
            "manifests/old-calico-api.yaml",
            "1",
            {"apiVersion": "crd.projectcalico.org/v1", "kind": "GlobalNetworkPolicy"},
        )
        self.assertEqual(verify._required_crd_releases([old_group_resource]), [])

        wrong_group = crd.replace("group: projectcalico.org", "group: crd.projectcalico.org")
        with self.assertRaisesRegex(verify.VerificationError, "expected projectcalico.org/v3 GlobalNetworkPolicy"):
            verify._crds_for_apply_from_release(source, wrong_group)
        wrong_version = crd.replace("name: v3", "name: v4")
        with self.assertRaisesRegex(verify.VerificationError, "expected projectcalico.org/v3 GlobalNetworkPolicy"):
            verify._crds_for_apply_from_release(source, wrong_version)

    def test_gateway_experimental_bundle_filters_only_expected_admission_policies(self):
        bundle = """apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: first.example.test
---
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicy
metadata:
  name: safe-upgrades.gateway.networking.k8s.io
---
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicyBinding
metadata:
  name: safe-upgrades.gateway.networking.k8s.io
---
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: second.example.test
"""

        names, crd_yaml, excluded = verify._crds_for_apply_from_release(
            verify.GATEWAY_EXPERIMENTAL_CRDS,
            bundle,
        )

        applied = list(verify.yaml.safe_load_all(crd_yaml))
        self.assertEqual(names, ["first.example.test", "second.example.test"])
        self.assertEqual(
            [document["kind"] for document in applied],
            ["CustomResourceDefinition", "CustomResourceDefinition"],
        )
        self.assertEqual(
            [(item["apiVersion"], item["kind"]) for item in excluded],
            [
                ("admissionregistration.k8s.io/v1", "ValidatingAdmissionPolicy"),
                ("admissionregistration.k8s.io/v1", "ValidatingAdmissionPolicyBinding"),
            ],
        )
        self.assertEqual([item["document"] for item in excluded], [2, 3])

        unknown_workload = bundle + """---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: unexpected
"""
        with self.assertRaisesRegex(verify.VerificationError, "unexpected apiVersion/kind"):
            verify._crds_for_apply_from_release(verify.GATEWAY_EXPERIMENTAL_CRDS, unknown_workload)

    def test_builtin_schema_mapping_uses_group_prefix(self):
        resource = verify.ManifestResource(
            "examples/net.yaml",
            "1",
            {"apiVersion": "networking.k8s.io/v1", "kind": "NetworkPolicy"},
        )

        self.assertEqual(verify.schema_key(resource), "networkpolicy-networking-v1.json")


if __name__ == "__main__":
    unittest.main()
