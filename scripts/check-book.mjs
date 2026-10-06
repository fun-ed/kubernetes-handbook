import { readdir, readFile, stat } from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const DEFAULT_OUTPUT = "_book";
const SKIPPED_DIRECTORIES = new Set([".git", ".serena", "_book", "node_modules", "en"]);

async function readOutput(outputDirectory, relativePath, errors) {
    const filePath = path.join(outputDirectory, relativePath);
    try {
        return await readFile(filePath, "utf8");
    } catch {
        errors.push(`Missing rendered file: ${relativePath}`);
        return null;
    }
}

function findRawAnchorIds(summary) {
    return Array.from(summary.matchAll(/<a\s+id=["']([^"']+)["']\s*><\/a>/gi), (match) => match[1]);
}

function containsUnsupportedBlockSyntax(line) {
    const prose = line.replace(/(`+)(.*?)\1/g, "");
    return /\{%[^%]*%\}/.test(prose) || /<\/?(?:hint|tabs?|content-ref|file|embed)\b[^>]*>/i.test(prose);
}

async function findUnsupportedBlockSyntax(sourceDirectory) {
    const findings = [];

    async function walk(directory) {
        let entries;
        try {
            entries = await readdir(directory, { withFileTypes: true });
        } catch {
            return;
        }

        for (const entry of entries) {
            if (entry.isDirectory()) {
                if (!SKIPPED_DIRECTORIES.has(entry.name)) {
                    await walk(path.join(directory, entry.name));
                }
                continue;
            }
            if (!entry.isFile() || !entry.name.endsWith(".md")) {
                continue;
            }

            const filePath = path.join(directory, entry.name);
            const content = await readFile(filePath, "utf8");
            let fence = null;
            for (const [index, line] of content.split(/\r?\n/).entries()) {
                const fenceMatch = line.match(/^\s*(`{3,}|~{3,})/);
                if (fenceMatch) {
                    const marker = fenceMatch[1];
                    if (!fence) {
                        fence = { char: marker[0], length: marker.length };
                    } else if (marker[0] === fence.char && marker.length >= fence.length) {
                        fence = null;
                    }
                    continue;
                }
                if (!fence && containsUnsupportedBlockSyntax(line)) {
                    findings.push(`${path.relative(sourceDirectory, filePath)}:${index + 1}`);
                }
            }
        }
    }

    await walk(sourceDirectory);
    return findings;
}

function hasLinkTo(html, relativeTarget) {
    const escapedTarget = relativeTarget.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    return new RegExp(`href=["'][^"']*${escapedTarget}(?:#[^"']*)?["']`, "i").test(html);
}

async function imageExists(outputDirectory, htmlFile, html) {
    const imageTags = Array.from(html.matchAll(/<img\b[^>]*\bsrc=["']([^"']+)["'][^>]*>/gi));
    const image = imageTags.find((match) => /pod.*\.png/i.test(match[1]) && /\.gitbook\/assets/i.test(match[1]));
    if (!image) {
        return false;
    }

    const source = image[1].split(/[?#]/, 1)[0];
    if (/^(?:[a-z]+:)?\/\//i.test(source)) {
        return false;
    }

    let assetPath;
    try {
        assetPath = path.resolve(path.dirname(path.join(outputDirectory, htmlFile)), decodeURIComponent(source));
        await stat(assetPath);
        return true;
    } catch {
        return false;
    }
}

export async function checkRenderedBook({ rootDirectory = process.cwd(), outputDirectory = path.join(rootDirectory, DEFAULT_OUTPUT) } = {}) {
    const errors = [];
    const [index, setupIndex, currentChapter, concepts, summary] = await Promise.all([
        readOutput(outputDirectory, "index.html", errors),
        readOutput(outputDirectory, "setup/index.html", errors),
        readOutput(outputDirectory, "setup/kubernetes-v1.37.html", errors),
        readOutput(outputDirectory, "introduction/concepts.html", errors),
        readFile(path.join(rootDirectory, "SUMMARY.md"), "utf8").catch(() => {
            errors.push("Missing source navigation file: SUMMARY.md");
            return null;
        })
    ]);

    if (index && !hasLinkTo(index, "setup/index.html") && !hasLinkTo(index, "setup/")) {
        errors.push("Rendered navigation does not link to setup/index.html or canonical setup/");
    }
    if (setupIndex && !/<table\b/i.test(setupIndex)) {
        errors.push("Rendered setup/index.html is missing its version table");
    }
    if (setupIndex && !hasLinkTo(setupIndex, "kubernetes-v1.37.html")) {
        errors.push("Rendered setup/index.html is missing its link to the v1.37 chapter");
    }
    if (currentChapter && !/<pre\b[\s\S]*?<code\b[\s\S]*?kubeadm[\s\S]*?<\/code>/i.test(currentChapter)) {
        errors.push("Rendered v1.37 chapter is missing its kubeadm code example");
    }
    if (concepts && !(await imageExists(outputDirectory, "introduction/concepts.html", concepts))) {
        errors.push("Rendered introduction/concepts.html is missing its expected local pod image");
    }

    if (index && summary) {
        const rawAnchorIds = findRawAnchorIds(summary);
        if (rawAnchorIds.length === 0) {
            errors.push("SUMMARY.md has no raw HTML navigation anchors to verify");
        }
        for (const anchorId of rawAnchorIds) {
            const escapedId = anchorId.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
            if (!new RegExp(`\\bid=["']${escapedId}["']`, "i").test(index)) {
                errors.push(`Rendered navigation lost raw SUMMARY.md anchor: ${anchorId}`);
            }
        }
    }

    const searchPlusIndex = await readOutput(outputDirectory, "search_plus_index.json", errors);
    if (searchPlusIndex) {
        try {
            const parsed = JSON.parse(searchPlusIndex);
            if (!parsed || JSON.stringify(parsed).length < 3 || !JSON.stringify(parsed).includes("Kubernetes")) {
                errors.push("Search index is empty or does not contain handbook text");
            }
        } catch {
            errors.push("Search index is not valid JSON: search_plus_index.json");
        }
    }

    errors.push(...await checkSourceSyntax(rootDirectory));

    return errors;
}

export async function checkSourceSyntax(rootDirectory = process.cwd()) {
    const locations = await findUnsupportedBlockSyntax(rootDirectory);
    return locations.map((location) => `Unsupported GitBook block syntax at ${location}; migrate it or add a tested renderer adapter`);
}

async function main() {
    const sourceOnly = process.argv.includes("--source-only");
    const errors = sourceOnly ? await checkSourceSyntax() : await checkRenderedBook();
    if (errors.length > 0) {
        for (const error of errors) {
            console.error(`ERROR: ${error}`);
        }
        process.exitCode = 1;
        return;
    }
    if (sourceOnly) {
        console.log("No unsupported GitBook block syntax found in source Markdown.");
    } else {
        console.log("Rendered book smoke check passed: content, navigation, search, assets, and anchors are present.");
    }
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
    await main();
}
