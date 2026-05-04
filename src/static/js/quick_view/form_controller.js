(() => {
  if (window.ECommerceQuickViewFormController) return;

  const formState = window.ECommerceQuickViewFormState;
  const formSubmitter = window.ECommerceQuickViewFormSubmitter;

  if (!formState || !formSubmitter) {
    console.error(
      "quick_view/form_controller.js requires form_state.js and form_submitter.js",
    );
    return;
  }

  const initForm = (form) => {
    if (!form || form.dataset.qvInit === "1") return;
    form.dataset.qvInit = "1";

    const colorsContainer = form.querySelector("[data-qv-colors]");
    const sizesContainer = form.querySelector("[data-qv-sizes]");
    const variantsEl = form.querySelector(formState.SELECTORS.variants);

    formState.dedupeBtnChecks(colorsContainer);
    formState.dedupeBtnChecks(sizesContainer);

    const pairs = formState.getPairsInStock(variantsEl);
    const sizesByColor = formState.buildSizesByColorMap(pairs);

    const colorInputs = Array.from(form.querySelectorAll(formState.SELECTORS.colors));
    if (!form.querySelector(formState.SELECTORS.colorsChecked)) {
      formState.setFirstEnabledChecked(colorInputs);
    }

    const checkedSizeOnInit = form.querySelector(formState.SELECTORS.sizesChecked);
    if (checkedSizeOnInit) checkedSizeOnInit.checked = false;

    formState.applyAvailability(form, sizesByColor);
    formState.applyMaxQty(form);
    formState.syncHidden(form);

    form.addEventListener("change", (event) => {
      if (!(event.target instanceof HTMLElement)) return;

      if (
        event.target.matches(formState.SELECTORS.colors)
        || event.target.matches(formState.SELECTORS.sizes)
      ) {
        formState.applyAvailability(form, sizesByColor);
        formState.applyMaxQty(form);
        formState.syncHidden(form);
      }

      if (event.target.matches(formState.SELECTORS.qtyInput)) {
        const qty = Math.max(1, Number.parseInt(event.target.value || "1", 10) || 1);
        event.target.value = String(qty);
        formState.applyMaxQty(form);
        formState.syncHidden(form);
      }
    });

    form.addEventListener("click", (event) => {
      if (!(event.target instanceof Element)) return;

      const qtyInput = form.querySelector(formState.SELECTORS.qtyInput);
      if (!qtyInput) return;

      const plus = event.target.closest(formState.SELECTORS.qtyPlus);
      const minus = event.target.closest(formState.SELECTORS.qtyMinus);
      if (!plus && !minus) return;

      event.preventDefault();

      const current = Number.parseInt(qtyInput.value || "1", 10) || 1;
      const max = Number.parseInt(qtyInput.getAttribute("max") || "", 10);
      const hasMax = Number.isFinite(max) && max > 0;

      if (plus && hasMax && current >= max) {
        formState.showStockMsg(
          form,
          `В наличии только ${max} шт. Вы выбрали ${current} шт.`,
        );
        formState.applyMaxQty(form);
        formState.syncHidden(form);
        return;
      }

      const next = plus
        ? (hasMax ? Math.min(max, current + 1) : current + 1)
        : Math.max(1, current - 1);
      qtyInput.value = String(next);

      formState.applyMaxQty(form);
      formState.syncHidden(form);
    });

    form.addEventListener("submit", formSubmitter.handleSubmit);
  };

  const initAll = () => {
    document.querySelectorAll("form[data-qv-form]").forEach(initForm);
  };

  window.ECommerceQuickViewFormController = {
    initAll,
  };
})();
