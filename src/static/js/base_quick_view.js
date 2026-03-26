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
    const inputs = Array.from(container.querySelectorAll("input.btn-check"));
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
      if (!(cnt > 0)) return;
      const color = (el.dataset.color || "").trim();
      const size = (el.dataset.size || "").trim();
      if (!color || !size) return;
      pairs.push({ color, size });
    });
    return pairs;
  };

  const buildAvailabilityMaps = (pairs) => {
    const sizesByColor = new Map();
    const colorsBySize = new Map();
    pairs.forEach(({ color, size }) => {
      if (!sizesByColor.has(color)) sizesByColor.set(color, new Set());
      sizesByColor.get(color).add(size);
      if (!colorsBySize.has(size)) colorsBySize.set(size, new Set());
      colorsBySize.get(size).add(color);
    });
    return { sizesByColor, colorsBySize };
  };

  const getVariantCnt = (variantsEl, color, size) => {
    if (!variantsEl || !color || !size) return 0;
    const match = Array.from(variantsEl.querySelectorAll("span[data-cnt]")).find((el) => {
      return String((el.dataset.color || "").trim()) === String(color).trim()
        && String((el.dataset.size || "").trim()) === String(size).trim();
    });
    return match ? (Number.parseInt(match.dataset.cnt || "0", 10) || 0) : 0;
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

    const colorChecked = form.querySelector("[data-qv-colors] input.btn-check:checked");
    const sizeChecked = form.querySelector("[data-qv-sizes] input.btn-check:checked");

    if (colorInput) colorInput.value = colorChecked ? colorChecked.value : "";
    if (sizeInput) sizeInput.value = sizeChecked ? sizeChecked.value : "";
    if (qtyHidden && qtyVisible) qtyHidden.value = String(qtyVisible.value || "1");
  };

  const applyAvailability = (form, maps, direction) => {
    const colors = Array.from(form.querySelectorAll("[data-qv-colors] input.btn-check"));
    const sizes = Array.from(form.querySelectorAll("[data-qv-sizes] input.btn-check"));

    colors.forEach((input) => {
      input.disabled = !maps.sizesByColor.has(String(input.value));
      const label = form.querySelector(`label[for="${CSS.escape(input.id)}"]`);
      if (label) label.classList.toggle("disabled", input.disabled);
    });
    sizes.forEach((input) => {
      input.disabled = !maps.colorsBySize.has(String(input.value));
      const label = form.querySelector(`label[for="${CSS.escape(input.id)}"]`);
      if (label) label.classList.toggle("disabled", input.disabled);
    });

    const checkedColor0 = form.querySelector("[data-qv-colors] input.btn-check:checked");
    if (!checkedColor0 || checkedColor0.disabled) {
      if (checkedColor0) checkedColor0.checked = false;
      setFirstEnabledChecked(colors);
    }
    const checkedSize0 = form.querySelector("[data-qv-sizes] input.btn-check:checked");
    if (!checkedSize0 || checkedSize0.disabled) {
      if (checkedSize0) checkedSize0.checked = false;
      setFirstEnabledChecked(sizes);
    }

    const selectedColor = (form.querySelector("[data-qv-colors] input.btn-check:checked") || {}).value || "";
    const selectedSize = (form.querySelector("[data-qv-sizes] input.btn-check:checked") || {}).value || "";

    if (direction === "color" && selectedColor) {
      const allowedSizes = maps.sizesByColor.get(selectedColor) || new Set();
      sizes.forEach((input) => {
        input.disabled = input.disabled || !allowedSizes.has(String(input.value));
        const label = form.querySelector(`label[for="${CSS.escape(input.id)}"]`);
        if (label) label.classList.toggle("disabled", input.disabled);
      });
      const checkedSize = form.querySelector("[data-qv-sizes] input.btn-check:checked");
      if (checkedSize && checkedSize.disabled) {
        checkedSize.checked = false;
        setFirstEnabledChecked(sizes);
      }
      return;
    }

    if (direction === "size" && selectedSize) {
      const allowedColors = maps.colorsBySize.get(selectedSize) || new Set();
      colors.forEach((input) => {
        input.disabled = input.disabled || !allowedColors.has(String(input.value));
        const label = form.querySelector(`label[for="${CSS.escape(input.id)}"]`);
        if (label) label.classList.toggle("disabled", input.disabled);
      });
      const checkedColor = form.querySelector("[data-qv-colors] input.btn-check:checked");
      if (checkedColor && checkedColor.disabled) {
        checkedColor.checked = false;
        setFirstEnabledChecked(colors);
      }
    }
  };

  const applyMaxQty = (form) => {
    const variantsEl = form.querySelector("[data-qv-variants]");
    const qtyInput = form.querySelector("[data-qv-qty]");
    const plusBtn = form.querySelector("[data-qv-qty-plus]");
    const submitBtn = form.querySelector("[data-qv-submit]");

    if (!qtyInput) return;

    const color = (form.querySelector("[data-qv-colors] input.btn-check:checked") || {}).value || "";
    const size = (form.querySelector("[data-qv-sizes] input.btn-check:checked") || {}).value || "";
    const maxQty = getVariantCnt(variantsEl, color, size);

    if (maxQty > 0) {
      qtyInput.max = String(maxQty);
    } else {
      qtyInput.removeAttribute("max");
    }

    const current = Number.parseInt(qtyInput.value || "1", 10) || 1;
    const clamped = maxQty > 0 ? Math.min(Math.max(1, current), maxQty) : Math.max(1, current);
    if (String(clamped) !== String(qtyInput.value || "")) qtyInput.value = String(clamped);

    if (plusBtn) plusBtn.classList.toggle("disabled", maxQty > 0 && clamped >= maxQty);
    if (submitBtn) submitBtn.disabled = !(color && size && maxQty > 0);
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

  const initForm = (form) => {
    if (!form || form.dataset.qvInit === "1") return;
    form.dataset.qvInit = "1";

    const colorsContainer = form.querySelector("[data-qv-colors]");
    const sizesContainer = form.querySelector("[data-qv-sizes]");
    const variantsEl = form.querySelector("[data-qv-variants]");

    dedupeBtnChecks(colorsContainer);
    dedupeBtnChecks(sizesContainer);

    const pairs = getPairsInStock(variantsEl);
    const maps = buildAvailabilityMaps(pairs);

    const colorInputs = Array.from(form.querySelectorAll("[data-qv-colors] input.btn-check"));
    const sizeInputs = Array.from(form.querySelectorAll("[data-qv-sizes] input.btn-check"));

    if (!form.querySelector("[data-qv-colors] input.btn-check:checked")) {
      setFirstEnabledChecked(colorInputs);
    }
    const checkedSizeOnInit = form.querySelector("[data-qv-sizes] input.btn-check:checked");
    if (checkedSizeOnInit) checkedSizeOnInit.checked = false;

    applyAvailability(form, maps, "color");
    applyMaxQty(form);
    syncHidden(form);

    form.addEventListener("change", (event) => {
      if (event.target && event.target.matches("[data-qv-colors] input.btn-check, [data-qv-sizes] input.btn-check")) {
        const direction = event.target.closest("[data-qv-colors]") ? "color" : "size";
        applyAvailability(form, maps, direction);
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
      const maxQty = getVariantCnt(form.querySelector("[data-qv-variants]"), color, size);

      if (!productId || !color || !size) {
        alert("Выберите цвет и размер.");
        return;
      }
      if (!(maxQty > 0)) {
        alert("Этого варианта нет в наличии.");
        return;
      }
      if (quantity > maxQty) {
        alert(`В наличии только ${maxQty} шт.`);
        return;
      }

      const csrf = getCsrfToken(form);
      const submitBtn = form.querySelector("[data-qv-submit]");
      if (submitBtn) submitBtn.disabled = true;

      try {
        const res = await fetch("/test/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrf,
            "X-Requested-With": "XMLHttpRequest",
          },
          body: JSON.stringify({ product_id: productId, color, size, quantity }),
        });
        const text = await res.text();
        if (!res.ok) throw new Error(text || `HTTP ${res.status}`);
        console.log("QuickView /test/ ok:", text);
      } catch (e) {
        console.error("QuickView /test/ error:", e);
        alert("Ошибка отправки. Проверьте роут /test/.");
      } finally {
        if (submitBtn) submitBtn.disabled = false;
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
