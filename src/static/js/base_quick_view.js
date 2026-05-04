(() => {
  if (window.__quickViewSubmitInit) return;
  window.__quickViewSubmitInit = true;

  const modalFocus = window.ECommerceQuickViewModalFocus;
  const formController = window.ECommerceQuickViewFormController;

  if (!modalFocus || !formController) {
    console.error(
      "base_quick_view.js requires quick_view/modal_focus.js and quick_view/form_controller.js",
    );
    return;
  }

  modalFocus.init();
  window.__quickViewInitAll = () => formController.initAll();

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", window.__quickViewInitAll, {
      once: true,
    });
  } else {
    window.__quickViewInitAll();
  }
})();
