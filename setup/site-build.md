# 网站构建与预览

本书使用本地 HonKit 6.2.2 构建静态网站。工具链固定为 Node.js 24.21.0 和提交到仓库的 `package-lock.json`。不需要全局安装 GitBook、HonKit 或插件，也不要运行旧版 `gitbook install`。

## 前置条件与安装

需要 Git、mise 或能提供 Node.js 24.21.0 的版本管理器，以及 npm 11.19.0。仓库根目录的 `.nvmrc` 固定 Node 版本。使用 mise 时：

```sh
mise install node@24.21.0
mise exec node@24.21.0 -- npm ci
```

`npm ci` 按 lockfile 安装 HonKit、插件与传递依赖。依赖版本不一致时，先检查 Node、npm 与 `package-lock.json`，不要改用全局安装来绕过问题。

## 常用命令

```sh
make build
make serve
npm test
npm run check:book
```

`make build` 生成 `_book/`；`make serve` 在本机 `127.0.0.1` 启动预览服务器，默认使用端口 4000，预览和实时重载监听都限制在回环接口。`npm test` 运行本地渲染适配器与输出检查器的单元测试。`npm run check:book` 检查已生成的网站文件、章节内容、导航、搜索索引、图片与锚点。先构建再运行输出检查。

HonKit 内建代码高亮继续处理代码围栏。Mermaid 图表由仓库本地适配器将围栏转换为图表节点，再调用固定版本的本地 `mermaid@12.1.0` 浏览器包渲染；只有含图表的页面才加载该包，不使用 CDN。适配器显式设置 `securityLevel: "strict"`。网站使用 HonKit 默认主题，不替换主题。

本书继续固定稳定版 `gitbook-plugin-search-plus` 1.0.3，以保留它支持的任意字符与代码内容搜索；`book.json` 关闭默认 `search`、`lunr` 插件。不要改用 `latest` 预发布版。`editlink` 保留逐页编辑链接；默认主题侧栏提供仓库链接。旧 `github` 插件不再加载。仓库适配器保留页内目录，把 README 与版本记录中未列入 `SUMMARY.md` 的 `.agents/` 源文件链接改为 GitHub 源码链接，并在 HonKit 完成网站输出时恢复 `SUMMARY.md` 的九个原始锚点。未启用的 `alerts`、`github-buttons` 和 `page-treeview` 依赖已移除。

旧 `page-toc` 插件只声明 GitBook 3 兼容范围。仓库适配器用默认主题资源提供简洁的页内目录；书籍主导航仍由 `SUMMARY.md` 和默认主题处理。

构建命令先检查模板块，再启动 HonKit。根目录当前 Markdown 没有 `{% ... %}` 形式的 GitBook 模板块。若发现不支持的 hint、tabs、content-ref、file 或 embed 块，构建会在渲染前失败并给出路径。新增这类内容前，先改成 HonKit 支持的 Markdown/HTML，或补上并测试明确的渲染适配器；保留标签但不显示内部内容不算兼容。

默认主题不做替换。HonKit 原生渲染图片、表格、代码围栏和普通 Markdown 链接；其默认目录模板会丢弃 `SUMMARY.md` 标题中的原始 `<a id>`。本地插件在每次网站生成完成后，把九个 ID 放回对应的侧栏标题，并处理 `honkit serve` 的重建。`check:book` 会验证生成的导航锚点。

## 安全限制

当前锁定依赖的 `npm audit` 仍报告 9 个 high-severity findings。HonKit 6.2.2 的传递依赖链中包括 `chokidar`、`nunjucks` 与 `braces`；审计没有为 HonKit、这些依赖提供可直接采用的兼容自动修复，因此此工具链不能称为 audit-clean。Mermaid 的旧插件依赖已移除；当前锁定的 Mermaid 将 DOMPurify 解析为 3.4.16，审计未报告 critical finding。升级依赖前应重新审查完整审计结果；只在受信任机器上预览，并保持 `make serve` 的回环绑定。


## EPUB、PDF 与 MOBI

```sh
make epub
make pdf
make mobi
```

EPUB 由 HonKit 本地生成。PDF 和 MOBI 转换需要外部 Calibre 提供 `ebook-convert`。Calibre 不由 npm 安装或锁定，CI 只构建网站，不生成这些格式。若转换失败，先确认 Calibre 已安装并可从 `PATH` 找到；不要把缺少 Calibre 当成 HonKit 网站构建失败。

## 回退

如需回退本次工具链，恢复 `Makefile`、`package.json`、`package-lock.json`、`book.json`、`.nvmrc`、`plugins/handbook-rendering/`、`scripts/serve-loopback.cjs` 与 `.github/workflows/docs.yml` 到迁移前版本，并恢复旧的 GitBook CLI 安装说明。旧 GitBook 3 构建在本仓库曾遇到插件安装错误和 `gitbook-plugin-github@3.0.0` 要求 GitBook 4 alpha 的版本冲突；回退只还原旧配置，不代表旧构建已修复或可用。

## 本次工具链验收（2026-10-05）

固定 Node 24.21.0 的 `npm ci`、12 个适配器／失败路径测试、完整 `make build` 和 `npm run check:book` 均通过。网站生成 186 页，输出检查覆盖代码、表格、导航、搜索索引、图片与九个原始目录锚点。

真实浏览器还验证了首屏页内目录、搜索结果和 GitHub 编辑目标；独立的临时 Markdown fixture 经 HonKit 构建后，由本地 Mermaid 12.1.0 渲染为 SVG，运行配置为 strict。fixture 未加入手册章节，也未保留在最终网站产物中。

实际启动预览后检查 TCP listeners，确认网站和实时重载均只监听 `127.0.0.1`。检查发现 CLI 传入数字字符串端口时，会绕过原先仅测试整数端口的限制；现已规范化数字端口，并添加对应测试。该限制只作用于预览命令，不修改全局 Node 配置。

本节不表示网站已部署、GitHub Actions 已在远端运行，或 EPUB／PDF／MOBI 已完成验收。依赖审计仍有上方列明的 9 个 high findings，不能称为安全审计全通过。
