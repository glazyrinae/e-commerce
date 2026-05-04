(() => {
  if (window.ECommerceQuickViewFormSubmitter) return;

  const cartUtils = window.ECommerceCartUtils;
  const formState = window.ECommerceQuickViewFormState;

  if (!cartUtils || !formState) {
    console.error(
      "quick_view/form_submitter.js requires shared/cart_common.js and quick_view/form_state.js",
    );
    return;
  }

  const handleSubmit = async (event) => {
    event.preventDefault();

    const form = event.currentTarget;
    if (!(form instanceof HTMLFormElement)) return;

    formState.syncHidden(form);

    const { productId, color, size, quantity } = formState.readSelection(form);
    const variantsEl = form.querySelector(formState.SELECTORS.variants);
    const maxQty = cartUtils.getVariantCnt(variantsEl, color, size);
    const inBasket = cartUtils.isVariantInBasket(variantsEl, color, size);

    if (!productId || !color || !size) {
      formState.showStockMsg(form, "Выберите цвет и размер.");
      return;
    }
    if (!(maxQty > 0)) {
      formState.showStockMsg(form, "Этого варианта нет в наличии.");
      return;
    }
    if (inBasket) {
      formState.showStockMsg(form, "В корзине.");
      return;
    }
    if (quantity > maxQty) {
      formState.showStockMsg(form, `В наличии только ${maxQty} шт.`);
      return;
    }

    const csrf = cartUtils.getCsrfToken({
      form,
      hiddenInputSelector: 'input[name="csrfmiddlewaretoken"]',
    });

    const submitBtn = form.querySelector(formState.SELECTORS.submit);
    if (submitBtn) submitBtn.disabled = true;

    try {
      const response = await fetch(`/basket/cart/${productId}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrf,
          "X-Requested-With": "XMLHttpRequest",
        },
        body: JSON.stringify({ product_id: productId, color, size, quantity }),
      });

      const data = await response.json().catch(() => ({}));

      if (response.status === 401 && data.login_url) {
        window.location.href = data.login_url;
        return;
      }

      if (!response.ok || !data.success) {
        throw new Error(data.error || `HTTP ${response.status}`);
      }

      const selectedVariant = cartUtils.findVariantNode(variantsEl, color, size);
      if (selectedVariant) selectedVariant.dataset.inBasket = "1";

      if (submitBtn) submitBtn.textContent = data.button_text || "В корзине";
      cartUtils.setHeaderCartCount(data.cart_total_items);
      formState.showStockMsg(form, data.message || "Товар добавлен в корзину.");
    } catch (error) {
      console.error("QuickView /basket/cart error:", error);
      formState.showStockMsg(form, "Ошибка отправки. Проверьте параметры товара.");
    } finally {
      formState.applyMaxQty(form);
    }
  };

  window.ECommerceQuickViewFormSubmitter = {
    handleSubmit,
  };
})();
