require(["gitbook"], function (gitbook) {
    "use strict";

    function addPageToc() {
        var section = document.querySelector(".markdown-section");
        if (!section) {
            return;
        }

        var previous = section.querySelector(".handbook-page-toc");
        if (previous) {
            previous.remove();
        }

        var headings = Array.prototype.slice.call(section.querySelectorAll("h1, h2, h3"))
            .filter(function (heading) { return heading.id; });
        if (headings.length < 2) {
            return;
        }

        var nav = document.createElement("nav");
        nav.className = "handbook-page-toc";
        nav.setAttribute("aria-label", "本页目录");

        var title = document.createElement("strong");
        title.textContent = "本页目录";
        nav.appendChild(title);

        var list = document.createElement("ul");
        headings.forEach(function (heading) {
            var item = document.createElement("li");
            item.className = "handbook-page-toc-level-" + heading.tagName.slice(1);

            var link = document.createElement("a");
            link.href = "#" + heading.id;
            link.textContent = heading.textContent.trim();
            item.appendChild(link);
            list.appendChild(item);
        });

        nav.appendChild(list);
        section.insertBefore(nav, headings[0]);
    }

    gitbook.events.bind("page.change", addPageToc);
    addPageToc();
});
