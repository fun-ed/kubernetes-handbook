# Repository Guidelines

## Project overview

This is a Chinese-language Kubernetes reference handbook with GitBook-format Markdown and navigation, rendered by HonKit. Chapters, diagrams, and Kubernetes examples are the primary source. It is not the Kubernetes source tree or a single deployable application.

The current baseline is Kubernetes **v1.37.1**, with a component snapshot dated **2026-10-05**. For version, API, image, or installation changes, read `setup/kubernetes-v1.37.md` and `setup/component-versions.md` first. Keep upstream latest versions separate from kubeadm-bundled pins and explicit compatibility statements.

## Architecture & data flow

`README.md` provides the preface, `SUMMARY.md` defines chapter navigation, and `book.json` configures rendering. HonKit consumes the chapters and assets to produce the static site in `_book/` or ebook exports. The root `Makefile` preserves the build/preview/export entrypoints.

`examples/` and `manifests/` contain teaching and deployment artifacts, not shared application modules. Small applications such as `examples/client/informer/` have their own local tooling. There is no central `src/` tree or application entry point.

## Key directories

- `introduction/`, `concepts/`: fundamentals, architecture, components, and resource objects.
- `setup/`, `deploy/`, `extension/`, `network/`: installation guides and integrations.
- `apps/`, `practice/`, `troubleshooting/`: application topics, operational guidance, and diagnosis.
- `examples/`: standalone manifests, scripts, and client samples. `manifests/` groups add-on/component configurations.
- `.gitbook/assets/` and topic-local image directories hold referenced illustrations.
- `en/` contains English material with its own `book.json`; it is not a complete mirrored navigation tree.
- `community/` documents upstream Kubernetes development. Its testing commands are not handbook tests.
- `.agents/skill-investigate.md`, `.agents/skill-debug.md`, and `.agents/skill-maintenance.md` record the upgrade's investigation, diagnosis, verification, rollback, and publication SOPs.

## Development commands

Run book commands from the repository root after selecting the Node version in `.nvmrc` and installing the locked dependencies with `npm ci`. Read `setup/site-build.md` before changing rendering or plugins.

| Command | Purpose |
| --- | --- |
| `make` or `make build` | Build the site into `_book/`. |
| `make serve` | Preview the book, normally at `localhost:4000`. |
| `make epub`, `make pdf`, `make mobi` | Export `kubernetes-handbook` in the selected format. |
| `make install` | Install the local dependencies from the npm lockfile. |
| `make spell` | Fetch misspell with `go get`, then check tracked files. This is not a general linter. |
| `make clean` | Delete `_book/`; ebook exports remain. |

`npm test` checks rendering adapters and output-checker failure cases; `npm run check:book` checks the built site. `make verify` runs local manifest regression; `make verify-cluster` explicitly enables isolated runtime checks. Read `setup/verification.md` for exact scope and prerequisites. These are separate checks, not one full-stack certification.

## Code conventions & common patterns

- Keep chapters in their existing language, usually Chinese, and follow neighboring Markdown headings, tables, and fenced `bash`/`yaml` examples.
- Add chapters to the relevant topic directory and update `SUMMARY.md` plus any affected local index. Prefer descriptive lowercase, hyphenated names such as `resource-management.md`.
- Use relative internal links and image paths. Preserve encoded asset filenames where existing links require them.
- Follow the local YAML layout around `apiVersion`, `kind`, `metadata`, and `spec`. Examples span Kubernetes versions; preserve the chapter's version context rather than treating old APIs as current defaults.
- Preserve per-file `# HISTORICAL:` markers on archived manifests and keep them out of current installation commands. Current manifests need served APIs and matching selectors; changing only `apiVersion` or an image tag is not a complete migration.
- For Go samples, follow the sample's own module and formatting. The informer sample uses event callbacks, cache synchronization, stop-channel shutdown, and explicit error handling. These are local patterns, not repository-wide requirements.
- No shared dependency-injection or application-state framework exists. Keep examples self-contained instead of introducing handbook-wide application abstractions.

## Important files

`SUMMARY.md` and `book.json` control navigation and rendering. `Makefile`, `package.json`, and the lockfile define maintenance tooling. `CONTRIBUTING.md` and `appendix/contributing.md` describe the PR workflow. `.github/workflows/docs.yml` checks the rendered site without deploying it; CodeQL remains a separate code scan. Keep dependencies, build outputs, reports, and private QA data ignored.

## Runtime/tooling preferences

Use local pinned HonKit/npm dependencies and Node LTS from `.nvmrc`; keep dependency updates separate from content changes. Preserve navigation, raw HTML anchors, code, images, and GitBook block content when changing the renderer. The legacy GitBook failure in `setup/kubernetes-v1.37.md` is dated evidence, not a reason to restore an unsupported Node runtime.

For component maintenance, read `setup/compatibility-tracking.md` and `setup/component-watchlist.json`. The checker reports stable releases requiring review; official support status is manually reviewed and dated. Keep the frozen `setup/component-versions.md` snapshot separate from newer observations.

## Testing & QA

For rendering changes, run the adapter tests, build, and rendered-output checks, then inspect affected navigation, images, code fences, search, and diagram rendering. A successful site build does not verify external links or tutorial commands.

`manifests/test/` contains examples, not a test suite. The regression harness distinguishes current standalone resources from historical files and third-party schemas from authoritative API checks. Cluster mode creates its own unique kind cluster and temporary kubeconfig; it never uses the user's current context. Tutorial scripts remain teaching artifacts and are not routine checks. Report unavailable tooling, exclusions, and unperformed checks explicitly.

Public releases use `fun-ed/kubernetes-handbook` and `main`. This release is an explicitly approved clean snapshot: preserve the local original source history, but never publish it with `--all`, `--mirror`, or tags. Exclude `.serena/`, generated exports, kubeconfigs, keys, and private QA artifacts; retain original attribution and license notices.
