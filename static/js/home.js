
document.addEventListener("DOMContentLoaded", function () {

    // =========================================
    // 01. MOBILE NAVIGATION
    // =========================================

    const menuButton = document.querySelector(".menu-toggle");
    const navLinks = document.querySelector(".nav-links");

    if (menuButton && navLinks) {

        const menuIcon = menuButton.querySelector("img");

        const openIcon = menuButton.dataset.menuIcon;
        const closeIcon = menuButton.dataset.closeIcon;

        // Close mobile menu
        function closeMenu() {
            navLinks.classList.remove("is-open");

            menuButton.setAttribute("aria-expanded", "false");
            menuButton.setAttribute("aria-label", "فتح القائمة");

            if (menuIcon && openIcon) {
                menuIcon.src = openIcon;
            }
        }

        // Open or close mobile menu
        menuButton.addEventListener("click", function () {

            const isOpen = navLinks.classList.toggle("is-open");

            menuButton.setAttribute("aria-expanded", String(isOpen));

            menuButton.setAttribute(
                "aria-label",
                isOpen ? "إغلاق القائمة" : "فتح القائمة"
            );

            if (menuIcon) {
                const nextIcon = isOpen ? closeIcon : openIcon;

                if (nextIcon) {
                    menuIcon.src = nextIcon;
                }
            }
        });

        // Close menu after clicking a navigation link
        navLinks.querySelectorAll("a").forEach(function (link) {
            link.addEventListener("click", closeMenu);
        });

        // Close menu when Escape is pressed
        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape") {
                closeMenu();
            }
        });

        // Reset menu on desktop
        window.addEventListener("resize", function () {
            if (window.innerWidth > 780) {
                closeMenu();
            }
        });
    }


    // =========================================
    // 02. DAWRAH HUB - CONNECTING LINES
    // =========================================

    const hubNodes = document.querySelectorAll(".hub-node");
    const hubLines = document.querySelectorAll(".hub-line");

    // Highlight the line connected to a node
    function highlightHubLine(nodeName) {

        hubLines.forEach(function (line) {

            if (line.dataset.target === nodeName) {
                line.classList.add("is-active");
            } else {
                line.classList.remove("is-active");
            }

        });
    }

    // Remove all highlighted lines
    function resetHubLines() {

        hubLines.forEach(function (line) {
            line.classList.remove("is-active");
        });

    }

    hubNodes.forEach(function (node) {

        // Highlight on hover
        node.addEventListener("mouseenter", function () {
            highlightHubLine(node.dataset.node);
        });

        // Reset when mouse leaves
        node.addEventListener("mouseleave", resetHubLines);

    });

});
