document.addEventListener("DOMContentLoaded", () => {
    const header = document.querySelector("[data-site-header]");
    const navToggle = document.querySelector(".nav-toggle");
    const navList = document.querySelector("#primaryNav");
    const navLinks = Array.from(document.querySelectorAll(".nav-link"));
    const mapLinks = Array.from(document.querySelectorAll(".map-location"));
    const samePageHashLinks = (links) => links.filter((link) => {
        const href = link.getAttribute("href") || "";
        return href.startsWith("#") && href.length > 1;
    });
    const sectionLinks = [...samePageHashLinks(navLinks), ...samePageHashLinks(mapLinks)];
    const sections = Array.from(new Set(sectionLinks
        .map((link) => document.querySelector(link.getAttribute("href")))
        .filter(Boolean)));

    const closeMenu = () => {
        if (!navToggle || !navList) return;
        navList.classList.remove("is-open");
        navToggle.setAttribute("aria-expanded", "false");
    };

    if (navToggle && navList) {
        navToggle.addEventListener("click", () => {
            const isOpen = navList.classList.toggle("is-open");
            navToggle.setAttribute("aria-expanded", String(isOpen));
        });

        navLinks.forEach((link) => {
            link.addEventListener("click", closeMenu);
        });

        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape") {
                closeMenu();
            }
        });
    }

    const markScrolled = () => {
        if (!header) return;
        header.classList.toggle("is-scrolled", window.scrollY > 20);
    };

    markScrolled();
    window.addEventListener("scroll", markScrolled, { passive: true });

    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
        anchor.addEventListener("click", (event) => {
            const hash = anchor.getAttribute("href");
            const target = document.querySelector(hash);
            if (!target) return;
            event.preventDefault();
            closeMenu();

            const headerOffset = header ? header.getBoundingClientRect().height : 0;
            const targetTop = target.getBoundingClientRect().top + window.scrollY - headerOffset - 16;

            window.scrollTo({
                top: Math.max(targetTop, 0),
                behavior: prefersReducedMotion ? "auto" : "smooth"
            });

            history.replaceState(null, "", hash);
            target.setAttribute("tabindex", "-1");
            window.setTimeout(() => target.removeAttribute("tabindex"), 1200);
        });
    });

    if ("IntersectionObserver" in window && sections.length) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) return;
                const activeId = `#${entry.target.id}`;

                navLinks.forEach((link) => {
                    link.classList.toggle("is-active", link.getAttribute("href") === activeId);
                });

                mapLinks.forEach((link) => {
                    link.classList.toggle("is-active", link.getAttribute("href") === activeId);
                });
            });
        }, {
            rootMargin: "-35% 0px -55% 0px",
            threshold: 0
        });

        sections.forEach((section) => observer.observe(section));
    }

    const dashboard = document.querySelector(".swamp-dashboard");

    if (!prefersReducedMotion && dashboard) {
        window.addEventListener("scroll", () => {
            const offset = Math.min(window.scrollY * 0.035, 18);
            dashboard.style.transform = `translateY(${offset}px)`;
        }, { passive: true });
    }
});
