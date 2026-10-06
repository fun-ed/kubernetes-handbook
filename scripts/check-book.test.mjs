import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtemp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { runInNewContext } from "node:vm";

import { checkRenderedBook } from "./check-book.mjs";
import handbookRendering from "../plugins/handbook-rendering/index.js";

async function restoreSiteNavigation(site) {
    return handbookRendering.hooks.finish.call({
        output: {
            name: "website",
            root: () => site.outputDirectory
        },
        readFileAsString: () => readFile(path.join(site.rootDirectory, "SUMMARY.md"), "utf8")
    });
}

test("converts Mermaid code blocks into escaped render targets", () => {
    const source = 'flowchart TD\nA["<script>alert(1)</script> & text"]';
    const block = { kwargs: { language: "mermaid" }, body: source };

    assert.equal(handbookRendering.blocks.code(block), block);
    assert.equal(
        block.body,
        '<div class="mermaid">flowchart TD\nA["&lt;script&gt;alert(1)&lt;/script&gt; &amp; text"]</div>'
    );

    const ordinaryBlock = { kwargs: { language: "text" }, body: "<not-html>" };
    assert.equal(handbookRendering.blocks.code(ordinaryBlock), ordinaryBlock);
    assert.equal(ordinaryBlock.body, "<not-html>");
});

test("binds HonKit preview listeners to IPv4 loopback", () => {
    const result = spawnSync(process.execPath, [
        "--require",
        path.join(import.meta.dirname, "serve-loopback.cjs"),
        "-e",
        'const http = require("node:http"); const server = http.createServer(); server.listen(0, () => { console.log(server.address().address); server.close(); });'
    ], { encoding: "utf8", timeout: 5000 });

    assert.equal(result.status, 0, result.stderr);
    assert.equal(result.stdout.trim(), "127.0.0.1");
});

test("activates the page TOC on first load and later page changes", async () => {
    const script = await readFile(path.join(import.meta.dirname, "../plugins/handbook-rendering/assets/page-toc.js"), "utf8");
    let reads = 0;
    let pageChange;
    runInNewContext(script, {
        require(dependencies, activate) {
            assert.deepEqual(Array.from(dependencies), ["gitbook"]);
            activate({ events: { bind(event, handler) {
                assert.equal(event, "page.change");
                pageChange = handler;
            } } });
        },
        document: { querySelector() {
            reads += 1;
            return null;
        } }
    });
    assert.equal(reads, 1);
    pageChange();
    assert.equal(reads, 2);
});

test("binds numeric-string CLI preview ports to IPv4 loopback", () => {
    const result = spawnSync(process.execPath, [
        "--require",
        path.join(import.meta.dirname, "serve-loopback.cjs"),
        "-e",
        'const server = require("node:http").createServer(); server.listen("0", () => { console.log(server.address().address); server.close(); });'
    ], { encoding: "utf8", timeout: 5000 });
    assert.equal(result.status, 0, result.stderr);
    assert.equal(result.stdout.trim(), "127.0.0.1");
});

async function makeSite(t) {
    const rootDirectory = await mkdtemp(path.join(os.tmpdir(), "handbook-smoke-"));
    const outputDirectory = path.join(rootDirectory, "_book");
    t.after(() => rm(rootDirectory, { recursive: true, force: true }));

    await mkdir(path.join(outputDirectory, "setup"), { recursive: true });
    await mkdir(path.join(outputDirectory, "introduction"), { recursive: true });
    await mkdir(path.join(outputDirectory, ".gitbook", "assets"), { recursive: true });
    await writeFile(path.join(rootDirectory, "SUMMARY.md"), '## Setup <a id="setup"></a>\n');
    await writeFile(path.join(outputDirectory, "index.html"), '<nav><a href="setup/">Setup</a><li class="header" id="setup">Setup</li></nav>');
    await writeFile(path.join(outputDirectory, "setup", "index.html"), '<table><tr><td>etcd</td></tr></table><a href="kubernetes-v1.37.html">v1.37</a>');
    await writeFile(path.join(outputDirectory, "setup", "kubernetes-v1.37.html"), '<pre><code>kubeadm config validate</code></pre>');
    await writeFile(path.join(outputDirectory, "introduction", "concepts.html"), '<img src="../.gitbook/assets/pod%20%285%29.png">');
    await writeFile(path.join(outputDirectory, ".gitbook", "assets", "pod (5).png"), "image fixture");
    await writeFile(path.join(outputDirectory, "search_plus_index.json"), JSON.stringify({ docs: [{ text: "Kubernetes" }] }));

    return { rootDirectory, outputDirectory };
}

test("accepts a rendered book with chapter content, links, search, image, and raw anchors", async (t) => {
    const site = await makeSite(t);
    assert.deepEqual(await checkRenderedBook(site), []);
});

test("restores raw SUMMARY anchors to HonKit default-theme sidebar headers", async (t) => {
    const site = await makeSite(t);
    await writeFile(path.join(site.outputDirectory, "index.html"), '<nav><li class="header">Setup</li><a href="setup/">Setup</a></nav>');

    await restoreSiteNavigation(site);
    const index = await readFile(path.join(site.outputDirectory, "index.html"), "utf8");
    assert(index.includes('<li class="header" id="setup">Setup</li>'));
});

test("rejects a canonical directory link if its rendered index is missing", async (t) => {
    const site = await makeSite(t);
    await rm(path.join(site.outputDirectory, "setup", "index.html"));

    const errors = await checkRenderedBook(site);
    assert(errors.includes("Missing rendered file: setup/index.html"));
});

test("fails if a SUMMARY anchor cannot match a rendered sidebar heading", async (t) => {
    const site = await makeSite(t);
    await writeFile(path.join(site.outputDirectory, "index.html"), '<nav><li class="header">Different title</li></nav>');

    await assert.rejects(
        restoreSiteNavigation(site),
        (error) => error.message.includes("sidebar headers did not match SUMMARY.md anchors: setup")
    );
});

test("rejects rendered navigation that loses its chapter link and raw anchor", async (t) => {
    const site = await makeSite(t);
    await writeFile(path.join(site.outputDirectory, "index.html"), "<nav></nav>");

    const errors = await checkRenderedBook(site);
    assert(errors.some((error) => error.includes("Rendered navigation does not link")));
    assert(errors.some((error) => error.includes("lost raw SUMMARY.md anchor: setup")));
});

test("rejects a malformed search artifact", async (t) => {
    const site = await makeSite(t);
    await writeFile(path.join(site.outputDirectory, "search_plus_index.json"), "not JSON");

    const errors = await checkRenderedBook(site);
    assert(errors.includes("Search index is not valid JSON: search_plus_index.json"));
});

test("rejects unsupported GitBook block syntax before rendering can hide it", async (t) => {
    const site = await makeSite(t);
    await writeFile(path.join(site.rootDirectory, "unsupported-block.md"), "{% tabs %}\ncontent\n{% endtabs %}\n");

    const errors = await checkRenderedBook(site);
    assert(errors.some((error) => error.includes("unsupported-block.md:1")));
});

test("rewrites source-only .agents links without changing nested page content", () => {
    const source = '<details><summary>Nested section</summary><p>Visible text</p></details>\n\n[Debug SOP](../.agents/skill-debug.md)';
    const page = { path: "setup/kubernetes-v1.37.md", content: source };
    const rendered = handbookRendering.hooks["page:before"](page);

    assert.match(rendered.content, /<details><summary>Nested section<\/summary><p>Visible text<\/p><\/details>/);
    assert.match(rendered.content, /https:\/\/github\.com\/fun-ed\/kubernetes-handbook\/blob\/main\/\.agents\/skill-debug\.md/);
});
