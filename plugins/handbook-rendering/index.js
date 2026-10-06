const fs = require("node:fs/promises");
const path = require("node:path");

const REPOSITORY_URL = "https://github.com/fun-ed/kubernetes-handbook";
const BRANCH = "main";
const SOURCE_LINK = /(\]\()((?:\.\.\/|\.\/)*\.agents\/[^\s)]+\.md(?:#[^\s)]*)?)(\))/g;

function escapeDiagramSource(source) {
    return source.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function renderMermaidBlock(block) {
    if (block.kwargs?.language !== "mermaid") {
        return block;
    }

    block.body = `<div class="mermaid">${escapeDiagramSource(block.body)}</div>`;
    return block;
}

function resolveSourceUrl(href, pagePath) {
    const fragmentIndex = href.indexOf("#");
    const relativePath = fragmentIndex === -1 ? href : href.slice(0, fragmentIndex);
    const fragment = fragmentIndex === -1 ? "" : href.slice(fragmentIndex);
    const sourcePath = path.posix.normalize(path.posix.join(path.posix.dirname(pagePath), relativePath));

    if (!sourcePath.startsWith(".agents/")) {
        return null;
    }

    const encodedPath = sourcePath.split("/").map(encodeURIComponent).join("/");
    return `${REPOSITORY_URL}/blob/${BRANCH}/${encodedPath}${fragment}`;
}

function preserveSourceLinks(page) {
    if (!page || typeof page.path !== "string" || typeof page.content !== "string") {
        return page;
    }

    const content = page.content.replace(SOURCE_LINK, (match, prefix, href, suffix) => {
        const sourceUrl = resolveSourceUrl(href, page.path);
        return sourceUrl ? `${prefix}${sourceUrl}${suffix}` : match;
    });

    return content === page.content ? page : { ...page, content };
}

function decodeEntities(value) {
    return value
        .replace(/&amp;/gi, "&")
        .replace(/&lt;/gi, "<")
        .replace(/&gt;/gi, ">")
        .replace(/&quot;/gi, '"')
        .replace(/&#39;/gi, "'")
        .replace(/&#(\d+);/g, (_, number) => String.fromCodePoint(Number(number)))
        .replace(/&#x([\da-f]+);/gi, (_, number) => String.fromCodePoint(parseInt(number, 16)));
}

function normalizeText(value) {
    return decodeEntities(value.replace(/<[^>]*>/g, " ")).replace(/\s+/g, " ").trim();
}

function readSummaryAnchors(summary) {
    const anchors = [];
    for (const line of summary.split(/\r?\n/)) {
        const heading = line.match(/^\s*#{1,6}\s+(.+?)\s*$/);
        if (!heading) {
            continue;
        }
        const anchor = heading[1].match(/<a\b[^>]*\bid=["']([^"']+)["'][^>]*>\s*<\/a>/i);
        if (anchor) {
            anchors.push({
                id: anchor[1],
                title: normalizeText(heading[1].replace(anchor[0], "").replace(/[`*_~]/g, ""))
            });
        }
    }
    return anchors;
}

function escapeAttribute(value) {
    return value.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;");
}

function escapeRegExp(value) {
    return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function restoreHeaderIds(html, anchors) {
    const restored = new Set();
    const patched = html.replace(
        /(<li\b(?=[^>]*\bclass=["'][^"']*\bheader\b[^"']*["'])[^>]*>)([\s\S]*?)(<\/li>)/gi,
        (match, openingTag, body, closingTag) => {
            const title = normalizeText(body);
            const anchor = anchors.find((item) => item.title === title);
            if (!anchor) {
                return match;
            }

            const encodedId = escapeAttribute(anchor.id);
            const hasTargetId = new RegExp(`\\bid=["']${escapeRegExp(anchor.id)}["']`, "i");
            if (hasTargetId.test(`${openingTag}${body}`)) {
                restored.add(anchor.id);
                return match;
            }

            restored.add(anchor.id);
            if (/\bid=["'][^"']+["']/i.test(openingTag)) {
                return `${openingTag}<a id="${encodedId}"></a>${body}${closingTag}`;
            }
            return `${openingTag.slice(0, -1)} id="${encodedId}">${body}${closingTag}`;
        }
    );
    return { html: patched, restored };
}

async function collectHtmlFiles(directory) {
    const files = [];
    for (const entry of await fs.readdir(directory, { withFileTypes: true })) {
        const entryPath = path.join(directory, entry.name);
        if (entry.isDirectory()) {
            files.push(...await collectHtmlFiles(entryPath));
        } else if (entry.isFile() && entry.name.endsWith(".html")) {
            files.push(entryPath);
        }
    }
    return files;
}

async function restoreSummaryAnchors(outputRoot, summary) {
    const anchors = readSummaryAnchors(summary);
    if (anchors.length === 0) {
        throw new Error("SUMMARY.md contains no raw anchor IDs to restore");
    }

    const indexFile = path.join(outputRoot, "index.html");
    const htmlFiles = await collectHtmlFiles(outputRoot);
    if (!htmlFiles.includes(indexFile)) {
        throw new Error("HonKit output is missing index.html");
    }

    let indexRestored = new Set();
    for (const filePath of htmlFiles) {
        const original = await fs.readFile(filePath, "utf8");
        const result = restoreHeaderIds(original, anchors);
        if (result.html !== original) {
            await fs.writeFile(filePath, result.html);
        }
        if (filePath === indexFile) {
            indexRestored = result.restored;
        }
    }

    const missingIds = anchors.map((anchor) => anchor.id).filter((id) => !indexRestored.has(id));
    if (missingIds.length > 0) {
        throw new Error(`HonKit sidebar headers did not match SUMMARY.md anchors: ${missingIds.join(", ")}`);
    }
    return anchors.length;
}

async function finishWebsiteOutput() {
    if (this.output.name !== "website") {
        return;
    }
    const outputRoot = this.output.root();
    const summary = await this.readFileAsString("SUMMARY.md");
    await restoreSummaryAnchors(outputRoot, summary);

    const pluginAssets = path.join(outputRoot, "gitbook", "honkit-plugin-handbook-rendering");
    await fs.mkdir(pluginAssets, { recursive: true });
    await fs.copyFile(
        require.resolve("mermaid/dist/mermaid.min.js"),
        path.join(pluginAssets, "mermaid.min.js")
    );
}


module.exports = {
    book: {
        assets: "./assets",
        css: ["page-toc.css"],
        js: ["mermaid-loader.js", "page-toc.js"]
    },
    blocks: {
        code: renderMermaidBlock
    },
    hooks: {
        "page:before": preserveSourceLinks,
        finish: finishWebsiteOutput
    },
    resolveSourceUrl,
    preserveSourceLinks,
    renderMermaidBlock,
    restoreSummaryAnchors
};
