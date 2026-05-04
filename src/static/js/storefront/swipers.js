(() => {
  if (window.ECommerceStorefrontSwipers) return;

  const initHomeSwipers = () => {
    const isMobile = window.matchMedia("(max-width:61.93rem)").matches;
    if (isMobile) return;

    if (document.querySelector(".main-swiper")) {
      new Swiper(".main-swiper", {
        slidesPerView: 1,
        spaceBetween: 48,
        pagination: {
          el: ".swiper-pagination",
          clickable: true,
        },
        breakpoints: {
          900: {
            slidesPerView: 2,
            spaceBetween: 48,
          },
        },
      });
    }

    const hasThumbs = document.querySelector(".thumb-swiper");
    const hasLarge = document.querySelector(".large-swiper");
    if (!hasThumbs || !hasLarge) return;

    const thumbSwiper = new Swiper(".thumb-swiper", {
      direction: "horizontal",
      slidesPerView: 6,
      spaceBetween: 6,
      breakpoints: {
        900: {
          direction: "vertical",
          spaceBetween: 6,
        },
      },
    });

    new Swiper(".large-swiper", {
      spaceBetween: 48,
      effect: "fade",
      slidesPerView: 1,
      pagination: {
        el: ".swiper-pagination",
        clickable: true,
      },
      thumbs: {
        swiper: thumbSwiper,
      },
    });
  };

  const initProductSwipers = () => {
    const hasThumb = document.querySelector(".product-thumbnail-slider");
    const hasLarge = document.querySelector(".product-large-slider");

    if (!hasThumb && !hasLarge) return;

    let thumbSwiper = null;
    if (hasThumb) {
      thumbSwiper = new Swiper(".product-thumbnail-slider", {
        slidesPerView: 5,
        spaceBetween: 10,
        direction: "vertical",
        breakpoints: {
          0: {
            direction: "horizontal",
          },
          992: {
            direction: "vertical",
          },
        },
      });
    }

    if (hasLarge) {
      new Swiper(".product-large-slider", {
        slidesPerView: 1,
        spaceBetween: 0,
        effect: "fade",
        thumbs: thumbSwiper ? { swiper: thumbSwiper } : undefined,
        pagination: {
          el: ".swiper-pagination",
          clickable: true,
        },
      });
    }
  };

  const init = () => {
    if (window.__storefrontSwipersInit) return;
    window.__storefrontSwipersInit = true;

    if (typeof window.Swiper !== "function") return;

    initHomeSwipers();
    initProductSwipers();
  };

  window.ECommerceStorefrontSwipers = {
    init,
  };
})();
