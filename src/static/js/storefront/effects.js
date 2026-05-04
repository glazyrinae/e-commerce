(() => {
  if (window.ECommerceStorefrontEffects) return;

  const $ = window.jQuery;
  if (!$) {
    console.error("storefront/effects.js requires jQuery");
    return;
  }

  const toPositiveInt = (value, fallback = 0) => {
    const parsed = Number.parseInt(value, 10);
    if (!Number.isFinite(parsed) || parsed < 0) return fallback;
    return parsed;
  };

  const initJarallax = () => {
    if (typeof window.jarallax !== "function") return;

    window.jarallax(document.querySelectorAll(".jarallax"));
    window.jarallax(document.querySelectorAll(".jarallax-img"), { keepImg: true });
  };

  const initProductQty = () => {
    $(".product-qty").each(function initForProductQty() {
      const $product = $(this);

      $product.find(".quantity-right-plus").on("click", (event) => {
        event.preventDefault();

        const current = toPositiveInt($product.find(".quantity").val(), 0);
        $product.find(".quantity").val(current + 1);
      });

      $product.find(".quantity-left-minus").on("click", (event) => {
        event.preventDefault();

        const current = toPositiveInt($product.find(".quantity").val(), 0);
        if (current > 0) {
          $product.find(".quantity").val(current - 1);
        }
      });
    });
  };

  const initChocolat = () => {
    if (typeof window.Chocolat !== "function") return;

    window.Chocolat(document.querySelectorAll(".image-link"), {
      imageSize: "contain",
      loop: true,
    });
  };

  const initTextFx = () => {
    $(".txt-fx").each(function initForTextFx() {
      if (this.dataset.txtFxReady === "1") return;

      let preparedText = "";
      let letterIndex = 0;
      const delay = 0;
      const stagger = 10;
      const words = this.textContent.split(/\s/);

      $.each(words, (_key, word) => {
        preparedText += '<span class="word">';

        for (let index = 0; index < word.length; index += 1) {
          preparedText += `<span class="letter" style="transition-delay:${delay + stagger * letterIndex}ms;">${word[index]}</span>`;
          letterIndex += 1;
        }

        preparedText += "</span>";
        preparedText += `<span class="letter" style="transition-delay:${delay}ms;">&nbsp;</span>`;
        letterIndex += 1;
      });

      this.innerHTML = preparedText;
      this.dataset.txtFxReady = "1";
    });
  };

  const bindSearchBox = () => {
    $(".user-items .search-item").on("click", () => {
      $(".search-box").toggleClass("active");
      $(".search-box .search-input").focus();
    });

    $(".close-button").on("click", () => {
      $(".search-box").toggleClass("active");
    });
  };

  const bindPreloaderFadeout = () => {
    $(window).on("load", () => {
      $(".preloader").fadeOut();
    });
  };

  const init = () => {
    if (window.__storefrontEffectsInit) return;
    window.__storefrontEffectsInit = true;

    initProductQty();
    initJarallax();
    initChocolat();
    initTextFx();
    bindSearchBox();
    bindPreloaderFadeout();
  };

  window.ECommerceStorefrontEffects = {
    init,
  };
})();
