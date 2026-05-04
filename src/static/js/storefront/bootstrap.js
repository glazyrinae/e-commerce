(() => {
  const $ = window.jQuery;
  if (!$) {
    console.error("storefront/bootstrap.js requires jQuery");
    return;
  }

  const effects = window.ECommerceStorefrontEffects;
  const swipers = window.ECommerceStorefrontSwipers;

  if (!effects && !swipers) {
    console.error(
      "storefront/bootstrap.js requires storefront/effects.js or storefront/swipers.js",
    );
    return;
  }

  $(document).ready(() => {
    if (effects) effects.init();
    if (swipers) swipers.init();
  });
})();
