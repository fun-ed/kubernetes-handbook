(function () {
    const currentScript = document.currentScript;
    if (!currentScript) {
        return;
    }

    const bundleUrl = new URL("mermaid.min.js", currentScript.src).href;

    function renderDiagrams() {
        const nodes = Array.from(document.querySelectorAll(".mermaid"));
        if (nodes.length === 0) {
            return;
        }

        const script = document.createElement("script");
        script.src = bundleUrl;
        script.onload = function () {
            if (!window.mermaid) {
                console.error("The local Mermaid bundle did not expose its renderer.");
                return;
            }

            window.mermaid.initialize({
                startOnLoad: false,
                securityLevel: "strict"
            });
            window.mermaid.run({ nodes }).catch((error) => {
                console.error("Unable to render Mermaid diagrams.", error);
            });
        };
        script.onerror = function () {
            console.error("Unable to load the local Mermaid bundle.");
        };
        document.head.appendChild(script);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", renderDiagrams, { once: true });
    } else {
        renderDiagrams();
    }
})();
