# Repository Guidelines

## Project overview

This is a Chinese-language Kubernetes reference handbook built with GitBook. Markdown chapters, diagrams, and Kubernetes examples are the primary source. It is not the Kubernetes source tree or a single deployable application.

The current baseline is Kubernetes **v1.37.1**, with a component snapshot dated **2026-10-05**. For version, API, image, or installation changes, read `setup/kubernetes-v1.37.md` and `setup/component-versions.md` first. Keep upstream latest versions separate from kubeadm-bundled pins and explicit compatibility statements.

## Architecture & data flow

`README.md` provides the preface, `SUMMARY.md` defines chapter navigation, and `book.json` configures GitBook rendering and plugins. GitBook consumes the chapters and assets to produce the static site in `_book/` or ebook exports. The root `Makefile` wraps these operations.

`examples/` and `manifests/` contain teaching and deployment artifacts, not shared application modules. Small applications such as `examples/client/informer/` have their own local tooling. There is no central `src/` tree or application entry point; `package.json`'s `main: index.js` is not an implemented entry point.

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

Run book commands from the repository root with GitBook available.

| Command | Purpose |
| --- | --- |
| `make` or `make build` | Build the site into `_book/`. |
| `make serve` | Preview the book, normally at `localhost:4000`. |
| `make epub`, `make pdf`, `make mobi` | Export `kubernetes-handbook` in the selected format. |
| `make install` | Install GitBook CLI globally through npm, then install book plugins. |
| `make spell` | Fetch misspell with `go get`, then check tracked files. This is not a general linter. |
| `make clean` | Delete `_book/`; ebook exports remain. |

There is no configured lint command. `npm test` deliberately exits with "no test specified" and does not validate changes. Installation and spelling targets change tooling state; use them only when needed.

## Code conventions & common patterns

- Keep chapters in their existing language, usually Chinese, and follow neighboring Markdown headings, tables, and fenced `bash`/`yaml` examples.
- Add chapters to the relevant topic directory and update `SUMMARY.md` plus any affected local index. Prefer descriptive lowercase, hyphenated names such as `resource-management.md`.
- Use relative internal links and image paths. Preserve encoded asset filenames where existing links require them.
- Follow the local YAML layout around `apiVersion`, `kind`, `metadata`, and `spec`. Examples span Kubernetes versions; preserve the chapter's version context rather than treating old APIs as current defaults.
- Preserve per-file `# HISTORICAL:` markers on archived manifests and keep them out of current installation commands. Current manifests need served APIs and matching selectors; changing only `apiVersion` or an image tag is not a complete migration.
- For Go samples, follow the sample's own module and formatting. The informer sample uses event callbacks, cache synchronization, stop-channel shutdown, and explicit error handling. These are local patterns, not repository-wide requirements.
- No shared dependency-injection or application-state framework exists. Keep examples self-contained instead of introducing handbook-wide application abstractions.

## Important files

`SUMMARY.md` and `book.json` control navigation and rendering. `Makefile` and `package.json` define maintenance tooling. `CONTRIBUTING.md` and `appendix/contributing.md` describe the PR workflow. `.github/workflows/codeql-analysis.yml` configures code scanning, not book publication or content tests. `.gitignore` excludes dependencies, `_book/`, and ebook/PDF outputs.

## Runtime/tooling preferences

Use the existing npm/GitBook toolchain. `book.json` requests GitBook `>=3.2.2`; `package.json` declares `gitbook-cli` `^2.3.2`. No Node runtime, package-manager version, or lockfile is pinned, and Bun is not configured. Do not assume `npm ci` or modern Node compatibility. Check both `book.json` and `package.json` when changing plugins because their plugin lists differ. Keep generated output out of source changes.

The legacy build is currently blocked: GitBook 3.2.3's bundled npm plugin installer fails, and the declared GitHub plugin 3.x requires GitBook 4 alpha. See the actual validation record in `setup/kubernetes-v1.37.md`. Do not claim a rendered build passed or recommend an unsupported old Node runtime as the production solution.

## Testing & QA

No repository-wide automated test framework, coverage requirement, or Markdown/YAML lint configuration is defined. For content edits, build/preview when the GitBook toolchain is available and inspect affected navigation, links, anchors, images, code fences, and plugin rendering. A successful build does not verify external links or tutorial commands.

`manifests/test/` contains examples, not a test suite. Validate changed examples against the Kubernetes version described by the chapter. Run cluster-dependent checks only in an explicitly intended disposable environment; tutorial scripts and manifests may create/delete resources or require cloud credentials. Do not execute chapter commands as routine repository checks. Report unavailable tooling and unperformed checks explicitly.

Public releases use `fun-ed/kubernetes-handbook` and `main`. This release is an explicitly approved clean snapshot: preserve the local original source history, but never publish it with `--all`, `--mirror`, or tags. Exclude `.serena/`, generated exports, kubeconfigs, keys, and private QA artifacts; retain original attribution and license notices.
