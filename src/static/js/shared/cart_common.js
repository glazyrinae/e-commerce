(() => {
  if (window.ECommerceCartUtils) return;

  const getCookie = (name) => {
    const cookieValue = document.cookie
      .split("; ")
      .find((row) => row.startsWith(`${name}=`));
    return cookieValue ? decodeURIComponent(cookieValue.split("=")[1]) : "";
  };

  const getCsrfToken = ({ form = null, hiddenInputSelector = "#js-csrf-token" } = {}) => {
    if (form && hiddenInputSelector) {
      const formToken = form.querySelector(hiddenInputSelector);
      if (formToken) {
        const value = String(formToken.value || "").trim();
        if (value) return value;
      }
    }

    const cookieToken = getCookie("csrftoken");
    if (cookieToken) return cookieToken;

    if (hiddenInputSelector) {
      const hiddenToken = document.querySelector(hiddenInputSelector);
      if (hiddenToken) {
        return String(hiddenToken.value || "").trim();
      }
    }

    return "";
  };

  const showTimedMessage = (
    target,
    message,
    { timeout = 1800, timerKey = "__timer" } = {},
  ) => {
    if (!target) return;
    target.textContent = message;
    target.style.display = "";
    window.clearTimeout(target[timerKey]);
    target[timerKey] = window.setTimeout(() => {
      target.textContent = "";
      target.style.display = "none";
    }, timeout);
  };

  const setHeaderCartCount = (count) => {
    const badge = document.querySelector(".cart-count");
    if (!badge) return;
    const parsed = Number.parseInt(String(count), 10);
    if (!Number.isFinite(parsed) || parsed < 0) return;
    badge.textContent = String(parsed);
  };

  const findVariantNode = (variantsEl, color, size) => {
    if (!variantsEl || !color || !size) return null;
    const colorKey = String(color).trim();
    const sizeKey = String(size).trim();
    return (
      Array.from(variantsEl.querySelectorAll("span[data-cnt]")).find((el) => {
        return (
          String((el.dataset.color || "").trim()) === colorKey
          && String((el.dataset.size || "").trim()) === sizeKey
        );
      }) || null
    );
  };

  const getVariantCnt = (variantsEl, color, size) => {
    const variant = findVariantNode(variantsEl, color, size);
    if (!variant) return 0;
    return Number.parseInt(variant.dataset.cnt || "0", 10) || 0;
  };

  const isVariantInBasket = (variantsEl, color, size) => {
    const variant = findVariantNode(variantsEl, color, size);
    return !!variant && String(variant.dataset.inBasket || "0") === "1";
  };

  window.ECommerceCartUtils = {
    getCookie,
    getCsrfToken,
    showTimedMessage,
    setHeaderCartCount,
    findVariantNode,
    getVariantCnt,
    isVariantInBasket,
  };
})();
