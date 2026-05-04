(() => {
  const run = () => {
    if (typeof window.__initBasketPage === "function") {
      window.__initBasketPage();
    }
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", run, { once: true });
  } else {
    run();
  }
})();
