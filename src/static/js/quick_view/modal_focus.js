(() => {
  if (window.ECommerceQuickViewModalFocus) return;

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

  const init = () => {
    if (window.__quickViewModalFocusInit) return;
    window.__quickViewModalFocusInit = true;

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
  };

  window.ECommerceQuickViewModalFocus = { init };
})();
