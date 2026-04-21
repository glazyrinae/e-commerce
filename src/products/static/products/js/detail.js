document.addEventListener("DOMContentLoaded", () => {
    const pluralizeReviews = (count) => {
        const n = Math.abs(count) % 100;
        const n1 = n % 10;
        if (n > 10 && n < 20) {
            return "отзывов";
        }
        if (n1 > 1 && n1 < 5) {
            return "отзыва";
        }
        if (n1 === 1) {
            return "отзыв";
        }
        return "отзывов";
    };

    const parseRatingSummary = (text) => {
        const normalized = String(text || "").replace(",", ".").trim();
        const strictMatch = normalized.match(
            /([0-5](?:\.\d+)?)\s*\(\s*(\d+)\s*отзыв\w*\s*\)/i,
        );
        if (strictMatch) {
            return {
                rating: Number.parseFloat(strictMatch[1]),
                count: Number.parseInt(strictMatch[2], 10),
            };
        }

        const numbers = normalized.match(/\d+(?:\.\d+)?/g) || [];
        if (numbers.length >= 2) {
            return {
                rating: Number.parseFloat(numbers[0]),
                count: Number.parseInt(numbers[1], 10),
            };
        }
        return null;
    };

    const renderRatingStars = (container, rating, textNode) => {
        container.querySelectorAll("i.bi").forEach((icon) => icon.remove());

        for (let i = 1; i <= 5; i += 1) {
            const delta = rating - (i - 1);
            let iconClass = "bi-star";
            if (delta >= 0.75) {
                iconClass = "bi-star-fill";
            } else if (delta >= 0.25) {
                iconClass = "bi-star-half";
            }

            const icon = document.createElement("i");
            icon.className = `bi ${iconClass} text-warning`;
            if (textNode) {
                container.insertBefore(icon, textNode);
            } else {
                container.appendChild(icon);
            }
        }
    };

    const normalizeDetailRatingSummary = () => {
        const allReviewsLink = document.querySelector('a[href="#reviews"]');
        const summaryRow = allReviewsLink
            ? allReviewsLink.closest(".mb-4")?.querySelector(".d-flex.align-items-center")
            : null;
        const summaryText = summaryRow?.querySelector("span");
        if (!summaryRow || !summaryText) {
            return;
        }

        const parsed = parseRatingSummary(summaryText.textContent);
        if (!parsed || Number.isNaN(parsed.rating) || Number.isNaN(parsed.count)) {
            return;
        }

        const safeRating = Math.max(0, Math.min(5, parsed.rating));
        const safeCount = Math.max(0, parsed.count);
        const ratingText = Number.isInteger(safeRating)
            ? String(safeRating)
            : safeRating.toFixed(1);

        renderRatingStars(summaryRow, safeRating, summaryText);
        summaryText.classList.add("ms-2");
        summaryText.textContent = `${ratingText} (${safeCount} ${pluralizeReviews(safeCount)})`;
    };

    normalizeDetailRatingSummary();

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
