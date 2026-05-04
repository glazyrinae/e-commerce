(() => {
  const cartUtils = window.ECommerceCartUtils;
  if (!cartUtils) {
    console.error("basket_page_core.js requires cart_common.js");
    return;
  }

  const showRowMessage = (row, message) => {
    const msgEl = row.querySelector(".js-stock-msg");
    cartUtils.showTimedMessage(msgEl, message);
  };

  const setCartEmptyState = ({ summaryEl, actionsEl, emptyEl }, isEmpty) => {
    if (summaryEl) summaryEl.style.display = isEmpty ? "none" : "";
    if (actionsEl) actionsEl.style.display = isEmpty ? "none" : "";
    if (emptyEl) emptyEl.style.display = isEmpty ? "" : "none";
  };

  const updateTotals = ({ totalItemsEl, totalPriceEl, summaryEl, actionsEl, emptyEl }, totalItems, totalPrice) => {
    if (totalItemsEl) totalItemsEl.textContent = String(totalItems);
    if (totalPriceEl) totalPriceEl.textContent = String(totalPrice);
    cartUtils.setHeaderCartCount(totalItems);
    setCartEmptyState({ summaryEl, actionsEl, emptyEl }, Number(totalItems) === 0);
  };

  const syncRowButtons = (row) => {
    const qtyInput = row.querySelector(".js-qty-input");
    const stockInput = row.querySelector('input[name="stock_cnt"]');
    const minusBtn = row.querySelector('.js-qty-btn[data-type="minus"]');
    const plusBtn = row.querySelector('.js-qty-btn[data-type="plus"]');
    if (!qtyInput || !stockInput) return;

    const qty = Number.parseInt(qtyInput.value || "1", 10) || 1;
    const stock = Number.parseInt(stockInput.value || "0", 10) || 0;
    const minusDisabled = qty <= 1;
    const plusDisabled = stock <= 0 || qty >= stock;

    if (minusBtn) {
      minusBtn.classList.toggle("disabled", minusDisabled);
      minusBtn.disabled = minusDisabled;
      minusBtn.setAttribute("aria-disabled", minusDisabled ? "true" : "false");
    }
    if (plusBtn) {
      plusBtn.classList.toggle("disabled", plusDisabled);
      plusBtn.disabled = plusDisabled;
      plusBtn.setAttribute("aria-disabled", plusDisabled ? "true" : "false");
    }
  };

  const lockRow = (row, isLocked) => {
    row.dataset.loading = isLocked ? "1" : "0";
    const controls = row.querySelectorAll(".js-qty-btn, .js-remove-item");
    controls.forEach((control) => {
      control.classList.toggle("disabled", isLocked);
      if ("disabled" in control) {
        control.disabled = isLocked;
      }
      control.setAttribute("aria-disabled", isLocked ? "true" : "false");
    });
  };

  const updateBasketItemFactory = ({ basketUrl, totalsRefs }) => {
    return async (row, nextQuantity) => {
      if (row.dataset.loading === "1") return;

      const basketId = Number.parseInt(row.dataset.basketId || "0", 10) || 0;
      if (!basketId) return;

      lockRow(row, true);
      try {
        const response = await fetch(basketUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": cartUtils.getCsrfToken(),
            "X-Requested-With": "XMLHttpRequest",
          },
          body: JSON.stringify({
            basket_id: basketId,
            quantity: nextQuantity,
          }),
        });

        const data = await response.json().catch(() => ({}));
        if (!response.ok || !data.success) {
          showRowMessage(row, data.error || "Ошибка обновления корзины.");
          return;
        }

        if (data.removed) {
          row.remove();
        } else {
          const qtyInput = row.querySelector(".js-qty-input");
          const lineTotal = row.querySelector(".js-line-total");
          const stockInput = row.querySelector('input[name="stock_cnt"]');
          if (qtyInput) qtyInput.value = String(data.quantity);
          if (lineTotal) lineTotal.textContent = String(data.line_total);
          if (stockInput && Number.isFinite(Number.parseInt(String(data.stock_cnt), 10))) {
            stockInput.value = String(data.stock_cnt);
          }
          if (data.capped && data.message) {
            showRowMessage(row, data.message);
          }
          syncRowButtons(row);
        }

        updateTotals(
          totalsRefs,
          data.cart_total_items,
          data.cart_total_price_items,
        );
      } catch {
        showRowMessage(row, "Ошибка сети. Повторите попытку.");
      } finally {
        if (document.body.contains(row)) {
          lockRow(row, false);
          syncRowButtons(row);
        }
      }
    };
  };

  const initBasketPage = () => {
    const cartList = document.getElementById("js-cart-list");
    if (!cartList) return;
    if (cartList.dataset.basketInit === "1") return;
    cartList.dataset.basketInit = "1";

    const basketUrl = cartList.dataset.basketUrl || "";
    if (!basketUrl) return;

    const totalsRefs = {
      totalItemsEl: document.getElementById("js-cart-total-items"),
      totalPriceEl: document.getElementById("js-cart-total-price"),
      summaryEl: document.getElementById("js-cart-summary"),
      actionsEl: document.getElementById("js-cart-actions"),
      emptyEl: document.getElementById("js-empty-cart"),
    };

    const updateBasketItem = updateBasketItemFactory({ basketUrl, totalsRefs });

    cartList.querySelectorAll("[data-basket-row]").forEach(syncRowButtons);

    cartList.addEventListener("click", (event) => {
      const removeBtn = event.target.closest(".js-remove-item");
      if (removeBtn) {
        event.preventDefault();
        const row = removeBtn.closest("[data-basket-row]");
        if (!row || row.dataset.loading === "1") return;
        updateBasketItem(row, 0);
        return;
      }

      const qtyBtn = event.target.closest(".js-qty-btn");
      if (!qtyBtn) return;
      event.preventDefault();
      if (qtyBtn.disabled) return;

      const row = qtyBtn.closest("[data-basket-row]");
      if (!row || row.dataset.loading === "1") return;

      const qtyInput = row.querySelector(".js-qty-input");
      const stockInput = row.querySelector('input[name="stock_cnt"]');
      if (!qtyInput || !stockInput) return;

      const current = Number.parseInt(qtyInput.value || "1", 10) || 1;
      const stock = Number.parseInt(stockInput.value || "0", 10) || 0;

      if (qtyBtn.dataset.type === "plus") {
        if (stock <= 0) {
          showRowMessage(row, "Товара нет в наличии.");
          syncRowButtons(row);
          return;
        }
        if (current >= stock) {
          showRowMessage(row, `В наличии только ${stock} шт.`);
          syncRowButtons(row);
          return;
        }
        updateBasketItem(row, current + 1);
        return;
      }

      if (current <= 1) {
        showRowMessage(row, "Минимальное количество: 1 шт.");
        syncRowButtons(row);
        return;
      }
      updateBasketItem(row, current - 1);
    });
  };

  window.__initBasketPage = initBasketPage;
})();
