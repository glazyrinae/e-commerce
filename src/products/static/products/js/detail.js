document.addEventListener("DOMContentLoaded", () => {
    const cnt = document.querySelector(".cnt-good");
    const loadBtnMinus = document.querySelector(".btn-minus");
    const loadBtnPlus = document.querySelector(".btn-plus");

    if (cnt) {
        const minusGood = () => {
            const currentValue = Number.parseInt(cnt.value, 10) || 0;
            if (currentValue > 0) {
                cnt.value = String(currentValue - 1);
            }
        };

        const plusGood = () => {
            const currentValue = Number.parseInt(cnt.value, 10) || 0;
            cnt.value = String(currentValue + 1);
        };

        if (loadBtnMinus) {
            loadBtnMinus.addEventListener("click", minusGood);
        }

        if (loadBtnPlus) {
            loadBtnPlus.addEventListener("click", plusGood);
        }
    }

    const allReviewsLink = document.querySelector('a[href="#reviews"]');
    const reviewsTabBtn = document.getElementById("reviews-tab");
    const tabsContainer = document.getElementById("productTabs");
    const reviewsPane = document.getElementById("reviews");

    if (allReviewsLink && reviewsTabBtn) {
        allReviewsLink.addEventListener("click", (event) => {
            event.preventDefault();

            if (window.bootstrap?.Tab) {
                window.bootstrap.Tab.getOrCreateInstance(reviewsTabBtn).show();
            } else {
                const tabButtons = document.querySelectorAll(
                    '#productTabs [data-bs-toggle="tab"]',
                );
                tabButtons.forEach((btn) => {
                    btn.classList.remove("active");
                    btn.setAttribute("aria-selected", "false");
                });
                reviewsTabBtn.classList.add("active");
                reviewsTabBtn.setAttribute("aria-selected", "true");

                const tabPanes = document.querySelectorAll(
                    "#productTabsContent .tab-pane",
                );
                tabPanes.forEach((pane) => {
                    pane.classList.remove("show", "active");
                });
                if (reviewsPane) {
                    reviewsPane.classList.add("show", "active");
                }
            }

            const scrollTarget = tabsContainer || reviewsTabBtn;
            scrollTarget.scrollIntoView({ behavior: "smooth", block: "start" });
        });
    }
});
