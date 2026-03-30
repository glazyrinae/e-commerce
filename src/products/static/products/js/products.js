document.addEventListener("DOMContentLoaded", () => {
    const loadMoreBtn = document.getElementById("load-more-btn");
    const contentContainer = document.getElementById("content-container");
    const loadingIndicator = document.getElementById("loading-indicator");
    const modalLong = document.getElementById("modallong");

    const getCookie = (name) => {
        if (!document.cookie) return null;

        const cookies = document.cookie.split(";");
        for (const cookiePart of cookies) {
            const cookie = cookiePart.trim();
            if (cookie.startsWith(`${name}=`)) {
                return decodeURIComponent(cookie.slice(name.length + 1));
            }
        }

        return null;
    };

    const csrfToken = getCookie("csrftoken");

    if (loadMoreBtn) {
        loadMoreBtn.addEventListener("click", loadMoreContent);
    }

    document.addEventListener("click", (event) => {
        if (!event.target.closest("#modallong")) return;

        if (
            event.target.matches(".quantity-left-minus") ||
            event.target.closest(".quantity-left-minus")
        ) {
            const button = event.target.matches(".quantity-left-minus")
                ? event.target
                : event.target.closest(".quantity-left-minus");
            handleQuantityMinus(button);
        }

        if (
            event.target.matches(".quantity-right-plus") ||
            event.target.closest(".quantity-right-plus")
        ) {
            const button = event.target.matches(".quantity-right-plus")
                ? event.target
                : event.target.closest(".quantity-right-plus");
            handleQuantityPlus(button);
        }
    });

    function handleQuantityMinus(button) {
        const input = button.closest(".input-group")?.querySelector(".form-control");
        const cartCount = document.querySelector(".cart-count");
        if (!input) return;

        const currentCount = Number.parseInt(cartCount?.textContent || "0", 10) || 0;
        const currentValue = Number.parseInt(input.value || "0", 10) || 0;

        if (cartCount && currentCount >= 1) {
            cartCount.textContent = String(currentCount - 1);
        }

        if (currentValue >= 1) {
            input.value = String(currentValue - 1);
            updateQuantity(input);
        }
    }

    function handleQuantityPlus(button) {
        const input = button.closest(".input-group")?.querySelector(".form-control");
        const cartCount = document.querySelector(".cart-count");
        if (!input) return;

        const currentCount = Number.parseInt(cartCount?.textContent || "0", 10) || 0;
        const currentValue = Number.parseInt(input.value || "0", 10) || 0;

        input.value = String(currentValue + 1);
        if (cartCount) {
            cartCount.textContent = String(currentCount + 1);
        }

        updateQuantity(input);
    }

    function updateQuantity(input) {
        const prodId = input.getAttribute("data-prodId");
        if (!prodId) return;

        fetch(`/basket/cart/${prodId}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken || "",
                "X-Requested-With": "XMLHttpRequest",
            },
            body: JSON.stringify({ quantity: input.value }),
        })
            .then((response) => response.json())
            .then((data) => {
                console.log("Ответ от сервера:", data);
            })
            .catch((error) => {
                console.error("Ошибка:", error);
            });
    }

    // if (modalLong) {
    //     modalLong.addEventListener("show.bs.modal", (event) => {
    //         const button = event.relatedTarget;
    //         const productId = button?.getAttribute("data-product_id");
    //         if (!productId) return;

    //         fetch(`/basket/cart/${productId}`, {
    //             method: "POST",
    //             headers: {
    //                 "Content-Type": "application/json",
    //                 "X-CSRFToken": csrfToken || "",
    //                 "X-Requested-With": "XMLHttpRequest",
    //             },
    //         })
    //             .then((response) => response.json())
    //             .then((product) => {
    //                 document.getElementById("modalProductContent").innerHTML = `
    //                   <div class="mini-cart cart-list p-0 mt-3">
    //                     <div class="mini-cart-item d-flex pb-3">
    //                       <div class="col-lg-2 col-md-3 col-sm-2 me-4">
    //                           <a href="#" title="product-image">
    //                           <img src='${product.img}' class="img-fluid" alt="single-product-item">
    //                           </a>
    //                       </div>
    //                       <div class="col-lg-9 col-md-8 col-sm-8">
    //                           <div class="product-header d-flex justify-content-between align-items-center mb-3">
    //                           <h4 class="product-title fs-6 me-5">${product.name}</h4>
    //                           </div>
    //                           <div class="quantity-price d-flex justify-content-between align-items-center">
    //                           <div class="input-group product-qty">
    //                               <button type="button"
    //                               class="quantity-left-minus btn btn-light rounded-0 rounded-start btn-number"
    //                               data-type="minus">
    //                                   <svg width="16" height="16">
    //                                       <use xlink:href="#minus"></use>
    //                                   </svg>
    //                               </button>
    //                               <input type="text" name="quantity" class="form-control input-number quantity" data-prodId="${product.id}" value="${product.quantity}" />
    //                               <button type="button" class="quantity-right-plus btn btn-light rounded-0 rounded-end btn-number"
    //                               data-type="plus">
    //                               <svg width="16" height="16">
    //                                   <use xlink:href="#plus"></use>
    //                               </svg>
    //                               </button>
    //                           </div>
    //                           <div class="price-code">
    //                               <span class="product-price fs-6">${product.price}</span>
    //                           </div>
    //                           </div>
    //                       </div>
    //                     </div>
    //                   </div>
    //                 <div class="modal-footer my-4 justify-content-center">
    //                     <button type="button" class="btn btn-red hvr-sweep-to-right dark-sweep">Заказать</button>
    //                     <button type="button"
    //                     class="btn btn-outline-gray hvr-sweep-to-right dark-sweep">Перейти в корзину</button>
    //                 </div>
    //                 `;
    //             })
    //             .catch((error) => {
    //                 console.error("Ошибка загрузки товара:", error);
    //                 document.getElementById("modalProductContent").innerHTML = `
    //                     <div class="alert alert-danger">
    //                         Ошибка загрузки товара
    //                     </div>
    //                 `;
    //             });
    //     });
    // }

    function loadMoreContent() {
        if (!loadMoreBtn || !contentContainer || !loadingIndicator) return;

        const nextPage = loadMoreBtn.dataset.nextPage;
        const categorySlug = window.location.pathname.replace(/^\/|\/$/g, "");
        const url = `/load-more/${categorySlug}/?page=${nextPage}`;

        loadMoreBtn.style.display = "none";
        loadingIndicator.style.display = "block";

        fetch(url, {
            headers: {
                "X-Requested-With": "XMLHttpRequest",
            },
        })
            .then((response) => {
                if (!response.ok) {
                    throw new Error("Network response was not ok");
                }
                return response.json();
            })
            .then((data) => {
                contentContainer.insertAdjacentHTML("beforeend", data.html);

                if (data.has_next) {
                    loadMoreBtn.dataset.nextPage = String(Number.parseInt(nextPage, 10) + 1);
                    loadMoreBtn.style.display = "block";
                } else {
                    loadMoreBtn.remove();
                }
            })
            .catch((error) => {
                console.error("Error:", error);
                loadMoreBtn.textContent = "Ошибка загрузки";
            })
            .finally(() => {
                loadingIndicator.style.display = "none";
            });
    }
});
