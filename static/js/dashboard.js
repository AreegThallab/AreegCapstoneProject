
document.addEventListener("DOMContentLoaded", function () {

    // =========================================
    // 01. DASHBOARD MOBILE NAVIGATION
    // Same opening behavior as home.js
    // =========================================

    const menuButton = document.querySelector(".dashboard-menu-toggle");
    const navLinks = document.querySelector(".dashboard-mobile-panel");

    if (menuButton && navLinks) {

        const menuIcon = menuButton.querySelector("img");
        const openIcon = menuButton.dataset.menuIcon;
        const closeIcon = menuButton.dataset.closeIcon;

        // Close mobile menu
        function closeMenu() {
            navLinks.classList.remove("is-open");

            menuButton.setAttribute("aria-expanded", "false");
            menuButton.setAttribute("aria-label", "فتح القائمة");

            navLinks.setAttribute(
                "aria-hidden",
                String(window.innerWidth <= 780)
            );

            if (menuIcon && openIcon) {
                menuIcon.src = openIcon;
                menuIcon.alt = "أيقونة فتح القائمة";
            }
        }

        // Open or close mobile menu
        menuButton.addEventListener("click", function () {

            const isOpen = navLinks.classList.toggle("is-open");

            menuButton.setAttribute(
                "aria-expanded",
                String(isOpen)
            );

            menuButton.setAttribute(
                "aria-label",
                isOpen ? "إغلاق القائمة" : "فتح القائمة"
            );

            navLinks.setAttribute(
                "aria-hidden",
                String(!isOpen)
            );

            if (menuIcon) {
                const nextIcon = isOpen ? closeIcon : openIcon;

                if (nextIcon) {
                    menuIcon.src = nextIcon;

                    menuIcon.alt = isOpen
                        ? "أيقونة إغلاق القائمة"
                        : "أيقونة فتح القائمة";
                }
            }
        });

        // Close menu after clicking a navigation link
        navLinks.querySelectorAll("a").forEach(function (link) {
            link.addEventListener("click", closeMenu);
        });

        // Close menu when Escape is pressed
        document.addEventListener("keydown", function (event) {

            if (
                event.key === "Escape" &&
                navLinks.classList.contains("is-open")
            ) {
                closeMenu();
                menuButton.focus();
            }
        });

        // Reset menu on desktop
        window.addEventListener("resize", function () {

            if (window.innerWidth > 780) {
                closeMenu();
                navLinks.removeAttribute("aria-hidden");
            } else {
                navLinks.setAttribute(
                    "aria-hidden",
                    String(!navLinks.classList.contains("is-open"))
                );
            }
        });

        // Initial mobile state
        if (window.innerWidth <= 780) {
            closeMenu();
        }
    }

});
