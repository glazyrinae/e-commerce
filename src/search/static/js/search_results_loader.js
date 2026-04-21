(function () {
    'use strict';

    const DEFAULT_RESULTS_LIMIT = 5;
    const NO_RESULTS_HTML = `
        <div class="col-12 py-5 text-center" style="grid-column: 1 / -1; width: 100%;">
            <div class="text-muted fs-5">Товары не найдены :(</div>
        </div>
    `;

    class SearchResultsLoader {
        static activeInstance = null;

        constructor(form) {
            this.form = form;
            this.contentContainer = document.getElementById('content-container');
            if (!this.contentContainer) return;

            this.quickViewContainer = this.ensureQuickViewContainer();
            this.sortWrapper = null;
            this.sortSelect = null;
            this.loadMoreWrapper = null;
            this.loadMoreButton = null;
            this.formOverlay = null;
            this.contentOverlay = null;
            this.abortController = null;
            this.isLoading = false;

            this.state = {
                page: 1,
                perPage: this.parsePositiveInt(form.dataset.resultsLimit, DEFAULT_RESULTS_LIMIT),
                hasNext: false,
                orderBy: this.getOrderBy(),
                lastSearchData: {},
            };

            this.init();
        }

        init() {
            this.removeLegacyLoadMore();
            this.ensureSortControls();
            this.ensureLoadMoreControls();

            this.formOverlay = this.createOverlay(this.form);
            this.contentOverlay = this.createOverlay(this.contentContainer);

            this.form.addEventListener(
                'submit',
                (event) => {
                    event.preventDefault();
                    event.stopImmediatePropagation();

                    SearchResultsLoader.activeInstance = this;
                    this.state.page = 1;
                    this.state.orderBy = this.getOrderBy();
                    this.search({ append: false });
                },
                true,
            );

            if (this.loadMoreButton) {
                this.loadMoreButton.addEventListener('click', () => {
                    if (SearchResultsLoader.activeInstance !== this) return;
                    if (!this.state.hasNext || this.isLoading) return;
                    this.state.page += 1;
                    this.search({ append: true });
                });
            }

            // На первой загрузке страницы сразу запрашиваем данные,
            // чтобы заполнить список сортировки и синхронизировать результаты.
            if (!SearchResultsLoader.activeInstance) {
                SearchResultsLoader.activeInstance = this;
                this.search({ append: false });
            }
        }

        parsePositiveInt(value, fallback) {
            const parsed = parseInt(value, 10);
            return Number.isNaN(parsed) || parsed <= 0 ? fallback : parsed;
        }

        ensureQuickViewContainer() {
            let container = document.getElementById('search-quick-view-container');
            if (container) return container;

            container = document.createElement('div');
            container.id = 'search-quick-view-container';
            document.body.appendChild(container);
            return container;
        }

        removeLegacyLoadMore() {
            const legacyButton = document.getElementById('load-more-btn');
            if (legacyButton) {
                const parent = legacyButton.parentElement;
                legacyButton.remove();
                if (parent && parent.children.length === 0) {
                    parent.remove();
                }
            }

            const legacyIndicator = document.getElementById('loading-indicator');
            if (legacyIndicator) {
                legacyIndicator.remove();
            }
        }

        ensureSortControls() {
            let wrapper = this.contentContainer.querySelector(
                '.search-ordering-wrap[data-search-ordering="1"]',
            );
            if (!wrapper) {
                wrapper = document.createElement('div');
                wrapper.className = 'search-ordering-wrap d-flex align-items-center mb-3';
                wrapper.dataset.searchOrdering = '1';
                wrapper.style.display = 'none';
                wrapper.style.gap = '10px';
                wrapper.style.justifyContent = 'flex-start';
                wrapper.style.gridColumn = '1 / -1';
                wrapper.style.width = '100%';
            }

            let label = wrapper.querySelector('label[data-search-ordering-label="1"]');
            if (!label) {
                label = document.createElement('label');
                label.dataset.searchOrderingLabel = '1';
                label.className = 'small fw-semibold mb-0';
                label.textContent = 'Сортировать:';
                wrapper.appendChild(label);
            }

            let select = wrapper.querySelector('select[data-search-ordering-select="1"]');
            if (!select) {
                select = document.createElement('select');
                select.dataset.searchOrderingSelect = '1';
                select.className = 'form-select form-select-sm';
                select.style.width = 'auto';
                wrapper.appendChild(select);
            }

            this.contentContainer
                .querySelectorAll('.search-ordering-wrap[data-search-ordering="1"]')
                .forEach((node) => {
                    if (node !== wrapper) node.remove();
                });

            this.contentContainer.prepend(wrapper);

            this.sortWrapper = wrapper;
            this.sortSelect = select;

            this.sortSelect.onchange = () => {
                const instance = SearchResultsLoader.activeInstance || this;
                const nextOrder = String(this.sortSelect.value || '');
                instance.setOrderBy(nextOrder);
                SearchResultsLoader.activeInstance = instance;
                instance.state.page = 1;
                instance.search({ append: false });
            };
        }

        setOrderBy(value) {
            const orderBy = String(value || '');
            this.state.orderBy = orderBy;
            const field = this.form.querySelector('input[name="order_by"]');
            if (field) {
                field.value = orderBy;
            }
        }

        updateOrdering(ordering) {
            if (!this.sortWrapper || !this.sortSelect) return;

            const options = Array.isArray(ordering && ordering.options) ? ordering.options : [];
            const current = String(
                ordering && typeof ordering.current === 'string'
                    ? ordering.current
                    : this.state.orderBy || '',
            );

            if (options.length === 0) {
                this.sortSelect.innerHTML = '';
                this.sortWrapper.style.display = 'none';
                return;
            }

            this.sortSelect.innerHTML = '';
            options.forEach((option) => {
                const opt = document.createElement('option');
                const value = String(option && option.value !== undefined ? option.value : '');
                opt.value = value;
                opt.textContent = this.getOrderingLabel(option, value);
                this.sortSelect.appendChild(opt);
            });

            const hasCurrent = options.some((option) => String(option.value) === current);
            const nextValue = hasCurrent ? current : String(options[0].value || '');
            this.sortSelect.value = nextValue;
            this.setOrderBy(nextValue);
            this.sortWrapper.style.display = 'flex';
        }

        getOrderingLabel(option, value) {
            const raw = option && typeof option.label === 'string' ? option.label.trim() : '';
            if (raw) return raw;

            if (value === '-pk') return 'Сначала новые (ID)';
            if (value === 'pk') return 'Сначала старые (ID)';

            if (/^-?(created|created_at|publish|published_at|date_created)$/i.test(value)) {
                return value.startsWith('-') ? 'Сначала новые' : 'Сначала старые';
            }

            if (/^-?(title|name)$/i.test(value)) {
                return value.startsWith('-') ? 'По названию (Я–А)' : 'По названию (А–Я)';
            }

            if (/^-?(price|discount_price|sale_price|cost|amount)$/i.test(value)) {
                return value.startsWith('-')
                    ? 'По цене (сначала дороже)'
                    : 'По цене (сначала дешевле)';
            }

            return value || 'Без названия';
        }

        ensureLoadMoreControls() {
            let wrapper = document.querySelector('.search-load-more-wrap[data-search-load-more="1"]');
            if (!wrapper) {
                wrapper = document.createElement('div');
                wrapper.className = 'search-load-more-wrap mt-4';
                wrapper.dataset.searchLoadMore = '1';
            }

            let button = wrapper.querySelector('button[data-search-load-more-btn="1"]');
            if (!button) {
                button = document.createElement('button');
                button.type = 'button';
                button.className = 'btn btn-primary px-4';
                button.textContent = 'Подгрузить еще';
                button.dataset.searchLoadMoreBtn = '1';
                wrapper.appendChild(button);
            }

            document
                .querySelectorAll('.search-load-more-wrap[data-search-load-more="1"]')
                .forEach((node) => {
                    if (node !== wrapper) node.remove();
                });

            wrapper.style.gridColumn = '1 / -1';
            wrapper.style.width = '100%';
            wrapper.style.justifyContent = 'center';

            this.contentContainer.appendChild(wrapper);
            this.loadMoreWrapper = wrapper;
            this.loadMoreButton = button;
            this.hideLoadMore();
        }

        createOverlay(target) {
            if (window.getComputedStyle(target).position === 'static') {
                target.style.position = 'relative';
            }

            const overlay = document.createElement('div');
            overlay.style.position = 'absolute';
            overlay.style.inset = '0';
            overlay.style.display = 'none';
            overlay.style.alignItems = 'center';
            overlay.style.justifyContent = 'center';
            overlay.style.background = 'rgba(255, 255, 255, 0.78)';
            overlay.style.zIndex = '20';
            overlay.style.pointerEvents = 'all';

            if (target === this.contentContainer) {
                overlay.style.minHeight = '120px';
            }

            overlay.innerHTML = this.getPreloaderMarkup();
            target.appendChild(overlay);
            return overlay;
        }

        getPreloaderMarkup() {
            const svg = document.querySelector('.preloader svg');
            if (svg) return svg.outerHTML;

            return '<div class="spinner-border text-dark" role="status"><span class="visually-hidden">Загрузка...</span></div>';
        }

        getOrderBy() {
            const field = this.form.querySelector('input[name="order_by"]');
            return field ? String(field.value || '') : '';
        }

        getCsrfToken() {
            return (
                document.cookie
                    .split('; ')
                    .find((row) => row.startsWith('csrftoken='))
                    ?.split('=')[1] || ''
            );
        }

        setFormBlocked(blocked) {
            this.form.querySelectorAll('input, select, textarea, button').forEach((control) => {
                if (blocked) {
                    control.dataset.searchPrevDisabled = control.disabled ? '1' : '0';
                    control.disabled = true;
                    return;
                }

                control.disabled = control.dataset.searchPrevDisabled === '1';
                delete control.dataset.searchPrevDisabled;
            });
        }

        setOverlayVisible(overlay, visible) {
            if (!overlay) return;
            overlay.style.display = visible ? 'flex' : 'none';
        }

        setLoadingState(loading) {
            this.isLoading = loading;
            this.setFormBlocked(loading);
            this.setOverlayVisible(this.formOverlay, loading);
            this.setOverlayVisible(this.contentOverlay, loading);

            if (this.loadMoreButton) {
                this.loadMoreButton.disabled = loading;
            }
        }

        normalizeRangeForSubmit() {
            this.form.querySelectorAll('.range-slider-wrapper').forEach((container) => {
                const minLimit = parseInt(container.dataset.min, 10) || 0;
                const maxLimit = parseInt(container.dataset.max, 10) || 100;

                const minHidden = container.querySelector('.slider-hidden-min');
                const maxHidden = container.querySelector('.slider-hidden-max');
                if (!minHidden || !maxHidden) return;

                const minVal = String(minHidden.value ?? '').trim();
                const maxVal = String(maxHidden.value ?? '').trim();

                if (minVal === String(minLimit) && maxVal === String(maxLimit)) {
                    minHidden.value = '';
                    maxHidden.value = '';
                }
            });
        }

        collapseRangeFields(data, fieldType) {
            const getScalar = (val) => (Array.isArray(val) ? val[val.length - 1] : val);

            this.form.querySelectorAll(`[data-field-type="${fieldType}"]`).forEach((field) => {
                const fieldName = field.dataset.fieldName;
                if (!fieldName) return;

                const minKey = `${fieldName}_min`;
                const maxKey = `${fieldName}_max`;

                const minValue = data[minKey] !== undefined ? getScalar(data[minKey]) : null;
                const maxValue = data[maxKey] !== undefined ? getScalar(data[maxKey]) : null;

                if (minValue !== null || maxValue !== null) {
                    delete data[minKey];
                    delete data[maxKey];
                    data[fieldName] = [minValue, maxValue];
                }
            });
        }

        buildSearchData() {
            this.normalizeRangeForSubmit();

            const data = {};
            const formData = new FormData(this.form);

            for (const [key, value] of formData.entries()) {
                const stringValue = String(value ?? '').trim();
                if (!stringValue) continue;

                if (data[key] === undefined) {
                    data[key] = [value];
                } else {
                    data[key].push(value);
                }
            }

            this.collapseRangeFields(data, 'range');
            this.collapseRangeFields(data, 'date_range');

            return data;
        }

        hasCards(cardsHtml, meta) {
            const total = Number(meta && meta.total);
            if (Number.isFinite(total) && total === 0) return false;
            if (!cardsHtml || !cardsHtml.trim()) return false;

            const tmp = document.createElement('div');
            tmp.innerHTML = cardsHtml;
            return tmp.children.length > 0;
        }

        renderNoResults() {
            this.contentContainer.innerHTML = NO_RESULTS_HTML;
        }

        hideLoadMore() {
            this.state.hasNext = false;
            if (this.loadMoreWrapper) {
                this.loadMoreWrapper.style.setProperty('display', 'none', 'important');
            }
        }

        updateLoadMore(meta) {
            this.state.hasNext = Boolean(meta && meta.has_next);
            if (!this.loadMoreWrapper) return;

            const total = Number(meta && meta.total);
            const perPage = Number(meta && meta.per_page);
            const exceededLimit =
                Number.isFinite(total) && Number.isFinite(perPage)
                    ? total > perPage
                    : this.state.hasNext;

            this.loadMoreWrapper.style.setProperty(
                'display',
                this.state.hasNext && exceededLimit ? 'flex' : 'none',
                'important',
            );
        }

        injectQuickViews(html, append) {
            if (!append) {
                this.quickViewContainer.innerHTML = '';
            }

            if (!html || !html.trim()) return;

            const tmp = document.createElement('div');
            tmp.innerHTML = html;

            tmp.querySelectorAll('.modal[id]').forEach((modal) => {
                const existing = document.getElementById(modal.id);
                if (existing) existing.remove();
            });

            while (tmp.firstChild) {
                this.quickViewContainer.appendChild(tmp.firstChild);
            }
        }

        renderResponse(result, append) {
            const blocks = result.blocks || {};
            const cardsHtml = blocks.cards_html || '';
            const quickViewHtml = blocks.quick_view_html || '';
            const hasCards = this.hasCards(cardsHtml, result.meta || {});

            if (append) {
                if (hasCards) {
                    if (this.loadMoreWrapper && this.loadMoreWrapper.parentElement === this.contentContainer) {
                        this.loadMoreWrapper.insertAdjacentHTML('beforebegin', cardsHtml);
                    } else {
                        this.contentContainer.insertAdjacentHTML('beforeend', cardsHtml);
                    }
                }
            } else {
                if (hasCards) {
                    this.contentContainer.innerHTML = cardsHtml;
                } else {
                    this.renderNoResults();
                }

                if (this.sortWrapper) {
                    this.contentContainer.prepend(this.sortWrapper);
                }
                if (this.loadMoreWrapper) {
                    this.contentContainer.appendChild(this.loadMoreWrapper);
                }
                this.contentContainer.appendChild(this.contentOverlay);
            }

            this.injectQuickViews(quickViewHtml, append);
            if (typeof window.__quickViewInitAll === 'function') {
                window.__quickViewInitAll();
            }
            this.updateOrdering(result.ordering || null);

            if (hasCards) {
                this.updateLoadMore(result.meta || {});
            } else {
                this.hideLoadMore();
                if (this.sortWrapper) {
                    this.sortWrapper.style.display = 'none';
                }
            }
        }

        async search({ append }) {
            if (this.isLoading) return;

            if (this.abortController) {
                this.abortController.abort();
            }
            this.abortController = new AbortController();

            if (!append) {
                this.state.page = 1;
                this.state.lastSearchData = this.buildSearchData();
            }

            const payload = {
                config_id: this.form.dataset.configId,
                content_type_id: this.form.dataset.contentType,
                search_data: this.state.lastSearchData,
                order_by: this.state.orderBy,
                page: this.state.page,
                per_page: this.state.perPage,
                limit: this.state.perPage,
                category_slug: String(this.form.dataset.categorySlug || '').trim(),
            };

            this.setLoadingState(true);

            try {
                const response = await fetch('/search/api/search/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCsrfToken(),
                    },
                    body: JSON.stringify(payload),
                    signal: this.abortController.signal,
                });

                if (!response.ok) {
                    throw new Error(`Search request failed: ${response.status}`);
                }

                const result = await response.json();
                if (!result.success) {
                    throw new Error(result.message || 'Search request failed');
                }

                this.renderResponse(result, append);
            } catch (error) {
                if (error && error.name === 'AbortError') return;

                console.error('Search loader error:', error);
                if (append) {
                    this.state.page = Math.max(1, this.state.page - 1);
                }
            } finally {
                this.setLoadingState(false);
            }
        }
    }

    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('.search-form').forEach((form) => {
            if (form.dataset.searchLoaderInit === '1') return;
            form.dataset.searchLoaderInit = '1';
            new SearchResultsLoader(form);
        });
    });
})();
