(() => {
  if (window.__quickViewSubmitInit) return;
  window.__quickViewSubmitInit = true;

  const modalReturnFocus = new WeakMap();

  const isFocusable = (el) =>
    !!el && typeof el.focus === "function" && !el.hasAttribute("disabled");

  const tryFocus = (el) => {
    if (!isFocusable(el)) return false;
    el.focus();
    return true;
  };

  const getFallbackTrigger = (modal) => {
    if (!modal?.id) return null;
    try {
      return document.querySelector(
        `[data-bs-toggle="modal"][data-bs-target="#${CSS.escape(modal.id)}"]`,
      );
    } catch {
      return document.querySelector(
        `[data-bs-toggle="modal"][data-bs-target="#${modal.id}"]`,
      );
    }
  };

  document.addEventListener("show.bs.modal", (event) => {
    const modal = event.target;
    if (!(modal instanceof HTMLElement)) return;
    modalReturnFocus.set(modal, event.relatedTarget ?? document.activeElement);
  });

  document.addEventListener("hide.bs.modal", (event) => {
    const modal = event.target;
    if (!(modal instanceof HTMLElement)) return;
    const active = document.activeElement;
    if (active instanceof HTMLElement && modal.contains(active)) active.blur();
  });

  document.addEventListener("hidden.bs.modal", (event) => {
    const modal = event.target;
    if (!(modal instanceof HTMLElement)) return;
    const returnTo = modalReturnFocus.get(modal);
    if (tryFocus(returnTo)) return;
    tryFocus(getFallbackTrigger(modal));
  });

  const dedupeBtnChecks = (container) => {
    if (!container) return;
    const seen = new Set();
    const inputs = Array.from(container.querySelectorAll('input[type="radio"]'));
    inputs.forEach((input) => {
      const value = String(input.value || "").trim();
      const label = container.querySelector(`label[for="${CSS.escape(input.id)}"]`);
      if (!value) {
        input.remove();
        if (label) label.remove();
        return;
      }
      if (seen.has(value)) {
        input.remove();
        if (label) label.remove();
        return;
      }
      seen.add(value);
    });
  };

  const getPairsInStock = (variantsEl) => {
    const pairs = [];
    if (!variantsEl) return pairs;
    variantsEl.querySelectorAll("span[data-cnt]").forEach((el) => {
      const cnt = Number.parseInt(el.dataset.cnt || "0", 10);
      const inBasket = String(el.dataset.inBasket || "0") === "1";
      if (!(cnt > 0) && !inBasket) return;
      const color = (el.dataset.color || "").trim();
      const size = (el.dataset.size || "").trim();
      if (!color || !size) return;
      pairs.push({ color, size });
    });
    return pairs;
  };

  const buildSizesByColorMap = (pairs) => {
    const sizesByColor = new Map();
    pairs.forEach(({ color, size }) => {
      if (!sizesByColor.has(color)) sizesByColor.set(color, new Set());
      sizesByColor.get(color).add(size);
    });
    return sizesByColor;
  };

  const getVariantCnt = (variantsEl, color, size) => {
    if (!variantsEl || !color || !size) return 0;
    const match = Array.from(variantsEl.querySelectorAll("span[data-cnt]")).find((el) => {
      return String((el.dataset.color || "").trim()) === String(color).trim()
        && String((el.dataset.size || "").trim()) === String(size).trim();
    });
    return match ? (Number.parseInt(match.dataset.cnt || "0", 10) || 0) : 0;
  };

  const isVariantInBasket = (variantsEl, color, size) => {
    if (!variantsEl || !color || !size) return false;
    const match = Array.from(variantsEl.querySelectorAll("span[data-cnt]")).find((el) => {
      return String((el.dataset.color || "").trim()) === String(color).trim()
        && String((el.dataset.size || "").trim()) === String(size).trim();
    });
    return !!match && String(match.dataset.inBasket || "0") === "1";
  };

  const setFirstEnabledChecked = (inputs) => {
    const firstEnabled = inputs.find((i) => !i.disabled);
    if (firstEnabled) firstEnabled.checked = true;
  };

  const syncHidden = (form) => {
    const colorInput = form.querySelector('input[name="color"]');
    const sizeInput = form.querySelector('input[name="size"]');
    const qtyHidden = form.querySelector('input[name="quantity"]');
    const qtyVisible = form.querySelector("[data-qv-qty]");

    const colorChecked = form.querySelector('[data-qv-colors] input[type="radio"]:checked');
    const sizeChecked = form.querySelector('[data-qv-sizes] input[type="radio"]:checked');

    if (colorInput) colorInput.value = colorChecked ? colorChecked.value : "";
    if (sizeInput) sizeInput.value = sizeChecked ? sizeChecked.value : "";
    if (qtyHidden && qtyVisible) qtyHidden.value = String(qtyVisible.value || "1");
  };

  const setLabelDisabled = (form, input, withStrike = false) => {
    const label = form.querySelector(`label[for="${CSS.escape(input.id)}"]`);
    if (!label) return;
    label.classList.toggle("disabled", input.disabled);
    label.classList.toggle("qv-size-unavailable", withStrike && input.disabled);
    if (input.disabled) {
      label.setAttribute("aria-disabled", "true");
    } else {
      label.removeAttribute("aria-disabled");
    }
  };

  const applyAvailability = (form, sizesByColor) => {
    const colors = Array.from(form.querySelectorAll('[data-qv-colors] input[type="radio"]'));
    const sizes = Array.from(form.querySelectorAll('[data-qv-sizes] input[type="radio"]'));

    colors.forEach((input) => {
      input.disabled = !sizesByColor.has(String(input.value));
      setLabelDisabled(form, input, false);
    });

    const checkedColor0 = form.querySelector('[data-qv-colors] input[type="radio"]:checked');
    if (!checkedColor0 || checkedColor0.disabled) {
      if (checkedColor0) checkedColor0.checked = false;
      setFirstEnabledChecked(colors);
    }
    const checkedSize0 = form.querySelector('[data-qv-sizes] input[type="radio"]:checked');
    if (!checkedSize0 || checkedSize0.disabled) {
      if (checkedSize0) checkedSize0.checked = false;
    }

    const selectedColor = (form.querySelector('[data-qv-colors] input[type="radio"]:checked') || {}).value || "";
    const allowedSizes = selectedColor ? (sizesByColor.get(selectedColor) || new Set()) : new Set();
    sizes.forEach((input) => {
      input.disabled = !selectedColor || !allowedSizes.has(String(input.value));
      setLabelDisabled(form, input, true);
    });

    const checkedSize = form.querySelector('[data-qv-sizes] input[type="radio"]:checked');
    if (checkedSize && checkedSize.disabled) {
      checkedSize.checked = false;
    }

    if (!form.querySelector('[data-qv-sizes] input[type="radio"]:checked')) {
      setFirstEnabledChecked(sizes);
    }
  };

  const applyMaxQty = (form) => {
    const variantsEl = form.querySelector("[data-qv-variants]");
    const qtyInput = form.querySelector("[data-qv-qty]");
    const plusBtn = form.querySelector("[data-qv-qty-plus]");
    const submitBtn = form.querySelector("[data-qv-submit]");

    if (!qtyInput) return;

    const color = (form.querySelector('[data-qv-colors] input[type="radio"]:checked') || {}).value || "";
    const size = (form.querySelector('[data-qv-sizes] input[type="radio"]:checked') || {}).value || "";
    const maxQty = getVariantCnt(variantsEl, color, size);
    const inBasket = isVariantInBasket(variantsEl, color, size);

    if (maxQty > 0) {
      qtyInput.max = String(maxQty);
    } else {
      qtyInput.removeAttribute("max");
    }

    const current = Number.parseInt(qtyInput.value || "1", 10) || 1;
    const clamped = maxQty > 0 ? Math.min(Math.max(1, current), maxQty) : Math.max(1, current);
    if (String(clamped) !== String(qtyInput.value || "")) qtyInput.value = String(clamped);

    if (plusBtn) plusBtn.classList.toggle("disabled", maxQty > 0 && clamped >= maxQty);
    if (submitBtn) {
      if (!submitBtn.dataset.defaultText) {
        submitBtn.dataset.defaultText = (submitBtn.textContent || "").trim();
      }
      submitBtn.disabled = inBasket || !(color && size && maxQty > 0);
      submitBtn.textContent = inBasket
        ? "Товар уже в корзине"
        : (submitBtn.dataset.defaultText || "В корзину");
    }
  };

  const showStockMsg = (form, text) => {
    const el = form.querySelector("[data-qv-stock-msg]");
    if (!el) return;
    el.textContent = text;
    el.style.display = "";
    window.clearTimeout(el.__qvTimer);
    el.__qvTimer = window.setTimeout(() => {
      el.style.display = "none";
      el.textContent = "";
    }, 1800);
  };

  const getCsrfToken = (form) => {
    const el = form.querySelector('input[name="csrfmiddlewaretoken"]');
    return el ? el.value : "";
  };

  const setHeaderCartCount = (count) => {
    const badge = document.querySelector(".cart-count");
    if (!badge) return;
    const parsed = Number.parseInt(String(count), 10);
    if (!Number.isFinite(parsed) || parsed < 0) return;
    badge.textContent = String(parsed);
  };

  const initForm = (form) => {
    if (!form || form.dataset.qvInit === "1") return;
    form.dataset.qvInit = "1";

    const colorsContainer = form.querySelector("[data-qv-colors]");
    const sizesContainer = form.querySelector("[data-qv-sizes]");
    const variantsEl = form.querySelector("[data-qv-variants]");

    dedupeBtnChecks(colorsContainer);
    dedupeBtnChecks(sizesContainer);

    const pairs = getPairsInStock(variantsEl);
    const sizesByColor = buildSizesByColorMap(pairs);

    const colorInputs = Array.from(form.querySelectorAll('[data-qv-colors] input[type="radio"]'));
    const sizeInputs = Array.from(form.querySelectorAll('[data-qv-sizes] input[type="radio"]'));

    if (!form.querySelector('[data-qv-colors] input[type="radio"]:checked')) {
      setFirstEnabledChecked(colorInputs);
    }
    const checkedSizeOnInit = form.querySelector('[data-qv-sizes] input[type="radio"]:checked');
    if (checkedSizeOnInit) checkedSizeOnInit.checked = false;

    applyAvailability(form, sizesByColor);
    applyMaxQty(form);
    syncHidden(form);

    form.addEventListener("change", (event) => {
      if (event.target && event.target.matches('[data-qv-colors] input[type="radio"], [data-qv-sizes] input[type="radio"]')) {
        applyAvailability(form, sizesByColor);
        applyMaxQty(form);
        syncHidden(form);
      }
      if (event.target && event.target.matches("[data-qv-qty]")) {
        const qty = Math.max(1, Number.parseInt(event.target.value || "1", 10) || 1);
        event.target.value = String(qty);
        applyMaxQty(form);
        syncHidden(form);
      }
    });

    form.addEventListener("click", (event) => {
      const qtyInput = form.querySelector("[data-qv-qty]");
      if (!qtyInput) return;

      const plus = event.target.closest("[data-qv-qty-plus]");
      const minus = event.target.closest("[data-qv-qty-minus]");
      if (!plus && !minus) return;

      event.preventDefault();
      const current = Number.parseInt(qtyInput.value || "1", 10) || 1;
      const max = Number.parseInt(qtyInput.getAttribute("max") || "", 10);
      const hasMax = Number.isFinite(max) && max > 0;
      if (plus && hasMax && current >= max) {
        showStockMsg(form, `В наличии только ${max} шт. Вы выбрали ${current} шт.`);
        applyMaxQty(form);
        syncHidden(form);
        return;
      }
      const next = plus
        ? (hasMax ? Math.min(max, current + 1) : current + 1)
        : Math.max(1, current - 1);
      qtyInput.value = String(next);
      applyMaxQty(form);
      syncHidden(form);
    });

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      syncHidden(form);

      const productId = (form.querySelector('input[name="product_id"]') || {}).value || "";
      const color = (form.querySelector('input[name="color"]') || {}).value || "";
      const size = (form.querySelector('input[name="size"]') || {}).value || "";
      const quantity = Number.parseInt(((form.querySelector('input[name="quantity"]') || {}).value || "1"), 10) || 1;
      const variantsEl = form.querySelector("[data-qv-variants]");
      const maxQty = getVariantCnt(variantsEl, color, size);
      const inBasket = isVariantInBasket(variantsEl, color, size);

      if (!productId || !color || !size) {
        showStockMsg(form, "Выберите цвет и размер.");
        return;
      }
      if (!(maxQty > 0)) {
        showStockMsg(form, "Этого варианта нет в наличии.");
        return;
      }
      if (inBasket) {
        showStockMsg(form, "Товар уже в корзине.");
        return;
      }
      if (quantity > maxQty) {
        showStockMsg(form, `В наличии только ${maxQty} шт.`);
        return;
      }

      const csrf = getCsrfToken(form);
      const submitBtn = form.querySelector("[data-qv-submit]");
      if (submitBtn) submitBtn.disabled = true;

      try {
        const res = await fetch(`/basket/cart/${productId}`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrf,
            "X-Requested-With": "XMLHttpRequest",
          },
          body: JSON.stringify({ product_id: productId, color, size, quantity }),
        });
        const data = await res.json().catch(() => ({}));

        if (res.status === 401 && data.login_url) {
          window.location.href = data.login_url;
          return;
        }
        if (!res.ok || !data.success) {
          throw new Error(data.error || `HTTP ${res.status}`);
        }

        const selectedVariant = variantsEl
          ? Array.from(variantsEl.querySelectorAll("span[data-cnt]")).find((el) => {
            return String((el.dataset.color || "").trim()) === String(color).trim()
              && String((el.dataset.size || "").trim()) === String(size).trim();
          })
          : null;
        if (selectedVariant) selectedVariant.dataset.inBasket = "1";
        if (submitBtn) submitBtn.textContent = data.button_text || "Товар уже в корзине";
        setHeaderCartCount(data.cart_total_items);
        showStockMsg(form, data.message || "Товар добавлен в корзину.");
      } catch (e) {
        console.error("QuickView /basket/cart error:", e);
        showStockMsg(form, "Ошибка отправки. Проверьте параметры товара.");
      } finally {
        applyMaxQty(form);
      }
    });
  };

  const initAll = () => {
    document.querySelectorAll("form[data-qv-form]").forEach(initForm);
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAll, { once: true });
  } else {
    initAll();
  }
})();
