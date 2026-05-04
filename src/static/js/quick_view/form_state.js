(() => {
  if (window.ECommerceQuickViewFormState) return;

  const cartUtils = window.ECommerceCartUtils;
  if (!cartUtils) {
    console.error("quick_view/form_state.js requires cart_common.js");
    return;
  }

  const SELECTORS = {
    colors: '[data-qv-colors] input[type="radio"]',
    colorsChecked: '[data-qv-colors] input[type="radio"]:checked',
    sizes: '[data-qv-sizes] input[type="radio"]',
    sizesChecked: '[data-qv-sizes] input[type="radio"]:checked',
    qtyInput: "[data-qv-qty]",
    qtyPlus: "[data-qv-qty-plus]",
    qtyMinus: "[data-qv-qty-minus]",
    submit: "[data-qv-submit]",
    variants: "[data-qv-variants]",
    stockMsg: "[data-qv-stock-msg]",
  };

  const queryAll = (root, selector) => Array.from(root.querySelectorAll(selector));

  const escapeCss = (value) => {
    try {
      return CSS.escape(value);
    } catch {
      return value;
    }
  };

  const findLabel = (container, input) => {
    if (!container || !input || !input.id) return null;
    return container.querySelector(`label[for="${escapeCss(input.id)}"]`);
  };

  const getCheckedValue = (form, selector) => {
    const checked = form.querySelector(selector);
    return checked ? checked.value : "";
  };

  const setFirstEnabledChecked = (inputs) => {
    const firstEnabled = inputs.find((input) => !input.disabled);
    if (firstEnabled) firstEnabled.checked = true;
  };

  const dedupeBtnChecks = (container) => {
    if (!container) return;
    const seenValues = new Set();

    queryAll(container, 'input[type="radio"]').forEach((input) => {
      const value = String(input.value || "").trim();
      const label = findLabel(container, input);

      if (!value || seenValues.has(value)) {
        input.remove();
        if (label) label.remove();
        return;
      }

      seenValues.add(value);
    });
  };

  const getPairsInStock = (variantsEl) => {
    const pairs = [];
    if (!variantsEl) return pairs;

    queryAll(variantsEl, "span[data-cnt]").forEach((variant) => {
      const cnt = Number.parseInt(variant.dataset.cnt || "0", 10);
      const inBasket = String(variant.dataset.inBasket || "0") === "1";

      if (!(cnt > 0) && !inBasket) return;

      const color = (variant.dataset.color || "").trim();
      const size = (variant.dataset.size || "").trim();
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

  const syncHidden = (form) => {
    const colorInput = form.querySelector('input[name="color"]');
    const sizeInput = form.querySelector('input[name="size"]');
    const qtyHidden = form.querySelector('input[name="quantity"]');
    const qtyVisible = form.querySelector(SELECTORS.qtyInput);

    if (colorInput) colorInput.value = getCheckedValue(form, SELECTORS.colorsChecked);
    if (sizeInput) sizeInput.value = getCheckedValue(form, SELECTORS.sizesChecked);
    if (qtyHidden && qtyVisible) qtyHidden.value = String(qtyVisible.value || "1");
  };

  const setLabelDisabled = (form, input, withStrike = false) => {
    const label = findLabel(form, input);
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
    const colorInputs = queryAll(form, SELECTORS.colors);
    const sizeInputs = queryAll(form, SELECTORS.sizes);

    colorInputs.forEach((input) => {
      input.disabled = !sizesByColor.has(String(input.value));
      setLabelDisabled(form, input);
    });

    const checkedColor = form.querySelector(SELECTORS.colorsChecked);
    if (!checkedColor || checkedColor.disabled) {
      if (checkedColor) checkedColor.checked = false;
      setFirstEnabledChecked(colorInputs);
    }

    const checkedSizeOnColorChange = form.querySelector(SELECTORS.sizesChecked);
    if (checkedSizeOnColorChange && checkedSizeOnColorChange.disabled) {
      checkedSizeOnColorChange.checked = false;
    }

    const selectedColor = getCheckedValue(form, SELECTORS.colorsChecked);
    const allowedSizes = selectedColor
      ? (sizesByColor.get(selectedColor) || new Set())
      : new Set();

    sizeInputs.forEach((input) => {
      input.disabled = !selectedColor || !allowedSizes.has(String(input.value));
      setLabelDisabled(form, input, true);
    });

    if (!form.querySelector(SELECTORS.sizesChecked)) {
      setFirstEnabledChecked(sizeInputs);
    }
  };

  const applyMaxQty = (form) => {
    const variantsEl = form.querySelector(SELECTORS.variants);
    const qtyInput = form.querySelector(SELECTORS.qtyInput);
    const plusBtn = form.querySelector(SELECTORS.qtyPlus);
    const submitBtn = form.querySelector(SELECTORS.submit);

    if (!qtyInput) return;

    const color = getCheckedValue(form, SELECTORS.colorsChecked);
    const size = getCheckedValue(form, SELECTORS.sizesChecked);
    const maxQty = cartUtils.getVariantCnt(variantsEl, color, size);
    const inBasket = cartUtils.isVariantInBasket(variantsEl, color, size);

    if (maxQty > 0) {
      qtyInput.max = String(maxQty);
    } else {
      qtyInput.removeAttribute("max");
    }

    const current = Number.parseInt(qtyInput.value || "1", 10) || 1;
    const clamped =
      maxQty > 0
        ? Math.min(Math.max(1, current), maxQty)
        : Math.max(1, current);

    if (String(clamped) !== String(qtyInput.value || "")) {
      qtyInput.value = String(clamped);
    }

    if (plusBtn) {
      plusBtn.classList.toggle("disabled", maxQty > 0 && clamped >= maxQty);
    }

    if (submitBtn) {
      if (!submitBtn.dataset.defaultText) {
        submitBtn.dataset.defaultText = (submitBtn.textContent || "").trim();
      }

      submitBtn.disabled = inBasket || !(color && size && maxQty > 0);
      submitBtn.textContent = inBasket
        ? "В корзине"
        : (submitBtn.dataset.defaultText || "В корзину");
    }
  };

  const showStockMsg = (form, text) => {
    const messageNode = form.querySelector(SELECTORS.stockMsg);
    cartUtils.showTimedMessage(messageNode, text, { timerKey: "__qvTimer" });
  };

  const readSelection = (form) => {
    const productIdInput = form.querySelector('input[name="product_id"]');
    const colorInput = form.querySelector('input[name="color"]');
    const sizeInput = form.querySelector('input[name="size"]');
    const quantityInput = form.querySelector('input[name="quantity"]');

    return {
      productId: productIdInput ? productIdInput.value : "",
      color: colorInput ? colorInput.value : "",
      size: sizeInput ? sizeInput.value : "",
      quantity: Number.parseInt(quantityInput ? quantityInput.value : "1", 10) || 1,
    };
  };

  window.ECommerceQuickViewFormState = {
    SELECTORS,
    applyAvailability,
    applyMaxQty,
    buildSizesByColorMap,
    dedupeBtnChecks,
    getPairsInStock,
    readSelection,
    setFirstEnabledChecked,
    showStockMsg,
    syncHidden,
  };
})();
