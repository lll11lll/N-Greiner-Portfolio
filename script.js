document.addEventListener("DOMContentLoaded", () => {
    const header = document.querySelector("[data-site-header]");
    const navToggle = document.querySelector(".nav-toggle");
    const navList = document.querySelector("#primaryNav");
    const navLinks = Array.from(document.querySelectorAll(".nav-link"));
    const sections = navLinks
        .map((link) => document.querySelector(link.getAttribute("href")))
        .filter(Boolean);

    if (navToggle && navList) {
        navToggle.addEventListener("click", () => {
            const isOpen = navList.classList.toggle("is-open");
            navToggle.setAttribute("aria-expanded", String(isOpen));
        });

        navLinks.forEach((link) => {
            link.addEventListener("click", () => {
                navList.classList.remove("is-open");
                navToggle.setAttribute("aria-expanded", "false");
            });
        });
    }

    const markScrolled = () => {
        if (!header) return;
        header.classList.toggle("is-scrolled", window.scrollY > 20);
    };

    markScrolled();
    window.addEventListener("scroll", markScrolled, { passive: true });

    document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
        anchor.addEventListener("click", (event) => {
            const target = document.querySelector(anchor.getAttribute("href"));
            if (!target) return;
            event.preventDefault();
            target.scrollIntoView({ behavior: "smooth", block: "start" });
            history.replaceState(null, "", anchor.getAttribute("href"));
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
            });
        }, {
            rootMargin: "-35% 0px -55% 0px",
            threshold: 0
        });

        sections.forEach((section) => observer.observe(section));
    }

    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const dashboard = document.querySelector(".swamp-dashboard");

    if (!prefersReducedMotion && dashboard) {
        window.addEventListener("scroll", () => {
            const offset = Math.min(window.scrollY * 0.035, 18);
            dashboard.style.transform = `translateY(${offset}px)`;
        }, { passive: true });
    }
});
