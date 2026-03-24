(function () {
    var BREAKPOINT_QUERY = '(max-width: 991.98px)';
    var DESKTOP_SIDE_WIDTH_PX = 460;
    var MIN_PANEL_HEIGHT_PX = 200;
    var TOP_CONTENT_RESERVE_PX = 200;

    function isMobile() {
        return window.matchMedia && window.matchMedia(BREAKPOINT_QUERY).matches;
    }

    function getHeaderEl() {
        return document.querySelector('header.header');
    }

    function getHeaderMetrics(mobileNow) {
        var header = getHeaderEl();
        if (!header) return { isSidebar: false, width: 0, height: 0 };

        var rect = header.getBoundingClientRect();
        var cs = window.getComputedStyle(header);

        // В теме используется левый фиксированный сайдбар (height: 100vh, width: 280px).
        // Для него нельзя использовать getBoundingClientRect().height как "высоту хедера сверху".
        var isSidebar =
        !mobileNow &&
        cs.position === 'fixed' &&
        Math.abs(rect.left) < 1 &&
        Math.abs(rect.top) < 1 &&
        rect.height >= window.innerHeight - 1 &&
        rect.width > 0;

        return { isSidebar: isSidebar, width: Math.round(rect.width), height: Math.round(rect.height) };
    }

    function getTopHeaderHeight(headerMetrics) {
        // Высота верхнего хедера (в мобильной верстке header становится обычным блоком сверху).
        var header = getHeaderEl();
        if (!header) return 0;
        if (headerMetrics && headerMetrics.isSidebar) return 0;
        return Math.round(header.getBoundingClientRect().height);
    }

    function getAvailableHeightForTopBottom(placement, topHeaderHeight) {
        var topOffset = placement === 'top' ? topHeaderHeight : 0;
        return Math.max(MIN_PANEL_HEIGHT_PX, window.innerHeight - topOffset);
    }

    function setWrapperPaddings(wrapper, paddings) {
        if (!wrapper) return;
        wrapper.style.paddingLeft = paddings.left || '';
        wrapper.style.paddingRight = paddings.right || '';
        wrapper.style.paddingTop = paddings.top || '';
        wrapper.style.paddingBottom = paddings.bottom || '';
    }

    function restorePlacement(offcanvasEl, placement) {
        offcanvasEl.style.top = '';
        offcanvasEl.style.left = '';
        offcanvasEl.style.right = '';
        offcanvasEl.style.bottom = '';
        offcanvasEl.style.height = '';
        offcanvasEl.style.width = '';

        offcanvasEl.classList.remove('offcanvas-start', 'offcanvas-end', 'offcanvas-top', 'offcanvas-bottom');
        if (placement === 'start') offcanvasEl.classList.add('offcanvas-start');
        else if (placement === 'end') offcanvasEl.classList.add('offcanvas-end');
        else if (placement === 'bottom') offcanvasEl.classList.add('offcanvas-bottom');
        else offcanvasEl.classList.add('offcanvas-top');
    }

    function getMobilePanelForRoot(panelRoot) {
        return (
        panelRoot.querySelector('.search-panel-mobile[data-search-panel-mobile="1"]') ||
        document.querySelector('.search-panel-mobile[data-search-panel-root-id="' + panelRoot.id + '"]')
        );
    }

    function movePanelContent(panelRoot, toMobile) {
        var mobilePanel = getMobilePanelForRoot(panelRoot);
        var mobileHost = mobilePanel ? mobilePanel.querySelector('[data-search-panel-mobile-host="1"]') : null;
        var desktopHost = panelRoot.querySelector('[data-search-panel-desktop-host="1"]');
        if (!mobileHost || !desktopHost) return;

        var inner =
        panelRoot.querySelector('[data-search-panel-inner="1"]') ||
        (mobilePanel ? mobilePanel.querySelector('[data-search-panel-inner="1"]') : null);
        if (!inner) return;

        if (toMobile) {
        if (inner.parentElement !== mobileHost) mobileHost.appendChild(inner);
        } else {
        if (inner.parentElement !== desktopHost) desktopHost.appendChild(inner);
        }
    }

    function layout() {
        var wrapper = document.querySelector('.main-wrapper');
        var mobileNow = isMobile();
        var header = getHeaderMetrics(mobileNow);
        var topHeaderHeight = getTopHeaderHeight(header);

        // Сбрасываем "push" перед пересчетом.
        setWrapperPaddings(wrapper, { left: '', right: '', top: '', bottom: '' });

        var panelRoots = document.querySelectorAll('.search-panel');

        if (mobileNow) {
        // Mobile: переносим панель к началу `.main-wrapper`, чтобы она была под меню.
        panelRoots.forEach(function (panelRoot) {
            movePanelContent(panelRoot, true);
            var mobilePanel = getMobilePanelForRoot(panelRoot);
            if (!mobilePanel || !wrapper) return;
            if (mobilePanel.parentElement === wrapper && mobilePanel === wrapper.firstElementChild) return;
            wrapper.insertBefore(mobilePanel, wrapper.firstChild);
        });
        return;
        }

        // Desktop: панели всегда видимы (через класс `.show`), здесь только размеры и "push" контента.
        panelRoots.forEach(function (panelRoot) {
        movePanelContent(panelRoot, false);
        });

        document.querySelectorAll('.search-panel .offcanvas.d-lg-block').forEach(function (el) {
        var placement = el.dataset.searchPlacement || 'start';
        restorePlacement(el, placement);

        // Если header — левый сайдбар, то левую панель и top/bottom надо смещать вправо.
        if (header.isSidebar) {
            if (placement === 'start') {
            el.style.left = header.width + 'px';
            }
            if (placement === 'top' || placement === 'bottom') {
            el.style.left = header.width + 'px';
            el.style.width = 'calc(100% - ' + header.width + 'px)';
            }
        }

        if (placement === 'top') {
            el.style.top = topHeaderHeight + 'px';
        }

        if (placement === 'top' || placement === 'bottom') {
            el.style.height = 'auto';
            var availableH = getAvailableHeightForTopBottom(placement, topHeaderHeight);
            var maxH = placement === 'top' ? Math.max(MIN_PANEL_HEIGHT_PX, availableH - TOP_CONTENT_RESERVE_PX) : availableH;
            el.style.height = Math.min(el.scrollHeight, maxH) + 'px';
        }

        if (placement === 'start' || placement === 'end') {
            el.style.width = DESKTOP_SIDE_WIDTH_PX + 'px';
            if (!header.isSidebar) {
            el.style.top = topHeaderHeight + 'px';
            }
        }

        var rect = el.getBoundingClientRect();
        if (placement === 'start') setWrapperPaddings(wrapper, { left: rect.width + 'px' });
        else if (placement === 'end') setWrapperPaddings(wrapper, { right: rect.width + 'px' });
        else if (placement === 'top') setWrapperPaddings(wrapper, { top: rect.height + 'px' });
        else if (placement === 'bottom') setWrapperPaddings(wrapper, { bottom: rect.height + 'px' });
        });
    }

    // Запускаем сразу: скрипт стоит в footer и выполнится до select2/noUiSlider.
    layout();

    var raf = null;
    window.addEventListener('resize', function () {
        if (raf) return;
        raf = window.requestAnimationFrame(function () {
        raf = null;
        layout();
        });
    });
})();