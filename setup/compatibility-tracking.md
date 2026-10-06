# Kubernetes v1.37 component compatibility tracking

The [component watchlist](component-watchlist.json) records selected Kubernetes v1.37.1 support gaps and release baselines from [the component version table](component-versions.md). Its snapshot and manual support-review dates are 2026-10-05. It distinguishes a component's standalone baseline from a kubeadm default pin. For example, Kubernetes v1.37.1 pins etcd 3.7.0 and CoreDNS 1.14.6, while the standalone baselines are etcd 3.7.2 and CoreDNS 1.14.7. The k0s and RKE2 rows record distribution releases separately; their embedded Kubernetes versions and bundled components are not kubeadm pins.

The pause image pin is 3.10.2. The source table records no independent stable release baseline for it, so the checker does not query it and the pin remains under manual source review.

A newer upstream release does not establish Kubernetes v1.37 compatibility and does not change either baseline or pin. The checker reads GitHub's public Releases API, ignores drafts and prereleases, and compares stable semantic versions with the recorded baselines. For k0s (`+k0s.N`) and RKE2 (`+rke2rN`), those stable build suffixes are numeric distribution rebuild revisions, not prerelease markers; the checker compares their revision numbers within each distribution without changing SemVer build-metadata ordering for other projects. An unknown distro suffix fails the release check. It does not read compatibility pages, modify source files, select versions, certify support, or create issues. People must review the official support link and update compatibility status by hand.

## Run the release check

From the repository root, use Python 3 and the standard library. This portable command writes a JSON report to `/tmp` and prints a short summary:

```sh
python3 scripts/check-component-updates.py --output /tmp/kubernetes-component-updates.json
```

The JSON report contains the UTC check time, each component's baseline and newest stable release, and whether a newer release needs manual review. Manually reviewed compatibility fields appear under `baseline_support` with their `reviewed_version`; they apply to the recorded baseline, not to a newer release. A network or malformed API response produces an error report and a nonzero exit status. The checker never reports a clean no-update result if a watched repository could not be checked.

The checker paginates GitHub's public Releases API for every watched repository and compares the highest stable semantic version, rather than trusting the first stable release or GitHub's `/releases/latest` publication-order endpoint. `tag_prefix` and `tag_exclude_prefixes` scope repositories with multiple products (including containerd's `api/` releases, autoscaler charts, and kube-state-metrics chart releases); exact-tag exclusions are limited to reviewed legacy tags with source/date notes in the watchlist. Unknown stable tags matching the selected product scope still fail closed. Ordinary repositories are capped at 10 pages (1,000 releases); RKE2 uses 13 pages (1,300 releases), currently 12 pages. The current 29-repository watchlist exceeds the 55-request public-only cap, so an unauthenticated run cannot complete the scan and reports a budget error rather than a clean partial result. When `GITHUB_TOKEN` is present, the checker sends it only as an Authorization header for public GET requests and applies a separate local cap of 500 API requests; 500 is the checker cap, not GitHub's rate-limit quota. Per-repository pagination limits remain in effect. The scheduled workflow supplies its built-in token with `contents: read` permission.

The optional `--fixture FILE` argument reads deterministic, offline release data for tests. The file is JSON with `schema_version: 1` and a `releases` object keyed by each watched `owner/repository`; each value uses the GitHub Releases API list shape. The fixture must include every repository in the watchlist. No fixture is needed for a normal check.

## Review an update

For each report entry with `review_required: true`:

1. Open that component's official `support_url` in the watchlist and check a version-specific support matrix or release note for Kubernetes 1.37.
2. Check the upstream release and the separate kubeadm/source pin, if one is recorded. A kubeadm default is not a general compatibility guarantee.
3. Test any proposed combination in an isolated cluster before changing the manually maintained version table or support status.

The checker will not make those changes. The watchlist's `support_status`, `supported_kubernetes_range`, `support_notes`, and `support_reviewed_on` fields remain an explicit manual record. `null` means that this watchlist has not recorded a supported range, not that every Kubernetes version is supported.

## Weekly report

The `Component release watch` workflow runs weekly and on manual dispatch. It has only read-only `contents: read` repository permission and supplies its built-in token only to the checker step for public release GET requests. The checker does not display or persist the token. The workflow uploads the JSON report as a workflow artifact; a failed check keeps the workflow failed, even when it uploads an error report for diagnosis. It does not publish site content or edit issues.
