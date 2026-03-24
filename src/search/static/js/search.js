// search/static/search/js/search.js
class UniversalSearch {
    constructor(formElement) {
        this.form = formElement;
        this.resultsContainer = document.querySelector(`#results-${this.form.id}`);
        this.resultsList = this.resultsContainer
            ? this.resultsContainer.querySelector('.search-results-list')
            : null;
        this.loadingElement = this.resultsContainer
            ? this.resultsContainer.querySelector('.search-loading')
            : null;
        this.configId = this.form.dataset.configId;
        this.contentTypeId = this.form.dataset.contentType;
        this.resultsLimit = this.form.dataset.resultsLimit || 10;
        this.init();
    }
    
    async loadFieldChoices(fieldElement) {
        
        const fieldName = fieldElement.dataset.fieldName;
        const fieldType = fieldElement.dataset.fieldType;
        if (!['select', 'radio'].includes(fieldType)) {
            return;
        }
        
        try {
            const response = await fetch(
                `/search/api/field-choices/${this.configId}/${fieldElement.dataset.fieldId}/`
            );
            
            if (!response.ok) return;
            
            const data = await response.json();
            if (data.success && data.choices.length > 0) {
                this.populateFieldChoices(fieldElement, data.choices, fieldType);
            }
            
        } catch (error) {
            console.error('Error loading choices:', error);
        }
    }
    
    populateFieldChoices(fieldElement, choices, fieldType) {
if (fieldType === 'select') {
    const select = fieldElement;
    if (select) {
        // Получаем выбранные значения из data-selected
        const selectedValues = select.dataset.selected 
            ? select.dataset.selected.split(',').map(v => v.trim()) 
            : [];
        
        // Очищаем существующие опции кроме первой
        while (select.options.length > 1) {
            select.remove(1);
        }
        
        // Добавляем новые опции
        choices.forEach(choice => {
            const option = document.createElement('option');
            option.value = choice.value;
            option.textContent = choice.label;
            
            // Устанавливаем selected для всех подходящих значений
            if (selectedValues.includes(String(choice.value))) {
                option.selected = true;
            }
            
            select.appendChild(option);
        });
        
        // ЕСЛИ ИСПОЛЬЗУЕТСЯ SELECT2 - ОБНОВЛЯЕМ
        if (typeof $ !== 'undefined' && $(select).data('select2')) {
            $(select).trigger('change');  // Просто триггерим change для обновления
        }
    }
} else if (fieldType === 'radio') {
            const container = fieldElement;
            // Очищаем существующие радиокнопки
            container.innerHTML = `<label class="form-label">${fieldElement.dataset.label || 'Выберите'}</label>`;
            
            // Добавляем новые радиокнопки
            choices.forEach((choice, index) => {
                const radioId = `field_${fieldElement.dataset.fieldId}_${index}`;
                const radioHtml = `
                    <div class="form-check">
                        <input class="form-check-input" 
                               type="radio" 
                               name="${fieldElement.dataset.fieldName}"
                               value="${choice.value}"
                               id="${radioId}">
                        <label class="form-check-label" for="${radioId}">
                            ${choice.label}
                        </label>
                    </div>
                `;
                container.insertAdjacentHTML('beforeend', radioHtml);
            });
        }
    }

    init() {
        // Перед submit нормализуем значения range: если стоят дефолты, не отправляем их.
        this.form.addEventListener('submit', () => {
            this.normalizeRangeForSubmit();
        });
        
        // Событие очистки
        const clearBtn = this.form.querySelector('.search-clear');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearSearch());
        }
        
        // Автопоиск при вводе
        const searchInput = this.form.querySelector('.search-input');
        if (searchInput) {
            let timeout;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(timeout);
                timeout = setTimeout(() => {
                    if (e.target.value.length >= 2) {
                        this.performSearch();
                    } else {
                        this.hideResults();
                    }
                }, 500);
            });
        }
        
        // Загружаем динамические choices для полей
        const dynamicFields = this.form.querySelectorAll('[data-field-type="select"], [data-field-type="radio"]');
        dynamicFields.forEach(field => {
            if (field.dataset.fieldId) {
                
                this.loadFieldChoices(field);
            }
        });
    }
    
    getFormData() {
        const formData = new FormData(this.form);
        const data = {};

        // Вспомогательная функция для парсинга значений
        const parseValue = (val) => {
            if (!val?.trim()) return null;
            const num = Number(val);
            return isNaN(num) ? val : num;
        };

        const parseDate = (val) => {
            if (!val?.trim()) return null;
            const str = val.trim();

            // Проверяем формат DD.MM.YYYY с помощью регулярного выражения
            const dateMatch = str.match(/^(\d{2})\.(\d{2})\.(\d{4})$/);
            
            if (dateMatch) {
                const [, day, month, year] = dateMatch;
                // Создаём дату в UTC, чтобы избежать проблем с часовыми поясами
                const date = new Date(Date.UTC(year, month - 1, day));
                
                // Проверяем, что дата корректна (например, не 32.13.2027)
                if (
                    date.getUTCFullYear() == year &&
                    date.getUTCMonth() == month - 1 &&
                    date.getUTCDate() == day
                ) {
                    // Форматируем как YYYY-MM-DD
                    const pad = (n) => n.toString().padStart(2, '0');
                    return `${year}-${pad(month)}-${pad(day)}`;
                }
            }

            // Если не дата — пробуем число
            const num = Number(str);
            if (!isNaN(num)) {
                return num;
            }

            // Иначе возвращаем строку
            return str;
        };

        const getScalar = (val) => (Array.isArray(val) ? val[val.length - 1] : val);

        // Собираем все поля из формы (single/multiple)
        for (const [key, value] of formData.entries()) {

            const element = document.querySelector(`[name="${key}"]`);
            const elementType = element ? element.type || element.tagName.toLowerCase() : 'unknown';
            if (!value?.trim()) continue;

            if (data[key] === undefined) {
                if (elementType != "text"){
                    data[key] = [value];
                }
                else {
                    data[key] = value;
                }
                console.log(elementType)
                continue;
            }

            if (Array.isArray(data[key])) {
                data[key].push(value);
            } else {
                data[key] = [data[key], value];
            }
        }

        // Обрабатываем rangeFields
        const rangeFields = this.form.querySelectorAll('[data-field-type="range"]');
        
        rangeFields.forEach(field => {
            let fieldName = field.dataset.fieldName;
            let minKey = `${fieldName}_min`;
            let maxKey = `${fieldName}_max`;

            // Извлекаем и парсим значения
            let minValue = data[minKey] !== undefined ? parseValue(getScalar(data[minKey])) : null;
            let maxValue = data[maxKey] !== undefined ? parseValue(getScalar(data[maxKey])) : null;

            // Если есть хотя бы одно значение, создаем массив и удаляем исходные поля
            if (minValue !== null || maxValue !== null) {
                delete data[minKey];
                delete data[maxKey];
                data[fieldName] = [minValue, maxValue];
            }
        });

        // Обрабатываем dateRangeFields
        const dateRangeFields = this.form.querySelectorAll('[data-field-type="date"]');
        
        dateRangeFields.forEach(field => {
            let fieldName = field.dataset.fieldName;
            let minKey = `${fieldName}_min`;
            let maxKey = `${fieldName}_max`;

            // Извлекаем и парсим значения
            let minValue = data[minKey] !== undefined ? parseDate(getScalar(data[minKey])) : null;
            let maxValue = data[maxKey] !== undefined ? parseDate(getScalar(data[maxKey])) : null;

            // Если есть хотя бы одно значение, создаем массив и удаляем исходные поля
            if (minValue !== null || maxValue !== null) {
                delete data[minKey];
                delete data[maxKey];
                data[fieldName] = [minValue, maxValue];
            }
        });

        return data;
    }
    
    async performSearch() {
        const data = this.getFormData();
        console.log('Search data:', data);
        // Показываем загрузку
        this.showLoading();
        this.showResults();
        try {
            const response = await fetch('/search/api/search/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken(),
                },
                body: JSON.stringify({
                    config_id: this.configId,
                    content_type_id: this.contentTypeId,
                    search_data: data,
                    limit: this.resultsLimit
                })
            });
            
            if (!response.ok) throw new Error('Ошибка поиска');
            
            const result = await response.json();
            this.displayResults(result);
            
        } catch (error) {
            console.error('Search error:', error);
            this.displayError('Ошибка при выполнении поиска');
        } finally {
            this.hideLoading();
        }
    }
    
    displayResults(result) {
        if (!this.resultsList) return;
        this.resultsList.innerHTML = '';
        
        if (!result.success) {
            this.displayError(result.message || 'Ошибка поиска');
            return;
        }
        
        if (result.results.length === 0) {
            this.resultsList.innerHTML = `
                <div class="alert alert-info m-2">
                    Ничего не найдено
                </div>
            `;
            return;
        }
        
        // Показываем количество результатов
        if (result.show_count) {
            const countHtml = `
                <div class="search-results-count p-2 border-bottom">
                    <small class="text-muted">Найдено: ${result.total}</small>
                </div>
            `;
            this.resultsList.innerHTML = countHtml;
        }
        
        // Добавляем результаты
        result.results.forEach(item => {
            const resultItem = document.createElement('div');
            resultItem.className = 'search-result-item';
            resultItem.dataset.objectId = item.id;
            resultItem.dataset.objectType = item.content_type;
            resultItem.innerHTML = this.formatResultItem(item);
            
            // Событие клика
            resultItem.addEventListener('click', () => {
                this.onResultClick(item);
            });
            
            this.resultsList.appendChild(resultItem);
        });
        
        // Кнопка "Показать все"
        if (result.has_more) {
            const showAllBtn = document.createElement('button');
            showAllBtn.className = 'btn btn-link btn-sm w-100 text-center';
            showAllBtn.textContent = 'Показать все...';
            showAllBtn.addEventListener('click', () => this.showAllResults(result.search_id));
            this.resultsList.appendChild(showAllBtn);
        }
    }
    
    formatResultItem(item) {
        // Кастомизируйте отображение под ваши нужды
        return `
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <strong>${item.title || `Объект #${item.id}`}</strong>
                    ${item.description ? `<div class="small text-muted">${item.description}</div>` : ''}
                </div>
                <span class="badge bg-secondary">ID: ${item.id}</span>
            </div>
        `;
    }
    
    onResultClick(item) {
        // Событие при клике на результат
        const event = new CustomEvent('search-result-click', {
            detail: {
                id: item.id,
                content_type: item.content_type,
                object: item,
                config_id: this.configId
            },
            bubbles: true
        });
        this.form.dispatchEvent(event);
        
        // По умолчанию - переход на страницу объекта
        if (item.url) {
            window.location.href = item.url;
        }
    }
    
    showAllResults(searchId) {
        // Загрузить все результаты
        console.log('Show all for search:', searchId);
    }
    
    showLoading() {
        if (this.loadingElement) {
            this.loadingElement.style.display = 'block';
        }
    }
    
    hideLoading() {
        if (this.loadingElement) {
            this.loadingElement.style.display = 'none';
        }
    }
    
    showResults() {
        if (this.resultsContainer) {
            this.resultsContainer.style.display = 'block';
        }
    }
    
    hideResults() {
        if (this.resultsContainer) {
            this.resultsContainer.style.display = 'none';
        }
    }
    
    clearSearch() {
        this.form.reset();
        this.hideResults();
        this.resetAllSliders();
        this.resetAllTextInputs();
        this.resetAllDatePickers();
        this.resetAllSelect2();
        this.collapseAllAccordions();
        if (this.resultsList) {
            this.resultsList.innerHTML = '';
        }
    }
    
    displayError(message) {
        if (!this.resultsList) return;
        this.resultsList.innerHTML = `
            <div class="alert alert-danger m-2">
                ${message}
            </div>
        `;
    }
    
    resetAllSliders() {
        // Находим слайдеры внутри этой формы
        this.form.querySelectorAll('.slider').forEach(sliderElement => {
            try {
                // Получаем родительский контейнер
                const container = sliderElement.closest('.range-slider-wrapper');
                if (!container) return;
                
                // Получаем исходные значения из data-атрибутов
                const minLimit = parseInt(container.dataset.min) || 0;
                const maxLimit = parseInt(container.dataset.max) || 100;
                
                // Сбрасываем слайдер
                if (sliderElement.noUiSlider) {
                    sliderElement.noUiSlider.set([minLimit, maxLimit]);
                }
            } catch (error) {
                console.error('Error resetting slider:', error);
            }
        });
        
        console.log('All sliders reset to default values');
    }

    resetAllSelect2() {
        this.form.querySelectorAll('select.select, select.select_multiple').forEach(selectElement => {
            try {
                // Если Select2 инициализирован — сбрасываем через него, иначе нативно.
                if (typeof $ !== 'undefined') {
                    const $select = $(selectElement);
                    if ($select.data('select2')) {
                        if (selectElement.classList.contains('select_multiple')) {
                            $select.val([]).trigger('change');
                        } else {
                            $select.val(null).trigger('change');
                        }
                        return;
                    }
                }

                // Fallback: нативный select
                if (selectElement.multiple) {
                    Array.from(selectElement.options).forEach((opt) => {
                        opt.selected = false;
                    });
                } else {
                    selectElement.selectedIndex = 0;
                }
                
            } catch (error) {
                console.error('Error resetting Select2:', error);
            }
        });
    }

    resetAllDatePickers() {
        // Очищаем поля date range и, если подключен bootstrap-datepicker, вызываем его API.
        this.form.querySelectorAll('input.date-start, input.date-end').forEach((input) => {
            try {
                input.value = '';
                if (typeof $ !== 'undefined') {
                    const $input = $(input);
                    if (typeof $input.datepicker === 'function') {
                        // bootstrap-datepicker
                        $input.datepicker('clearDates');
                    }
                }
            } catch (error) {
                console.error('Error resetting datepicker:', error);
            }
        });
    }

    resetAllTextInputs() {
        // `form.reset()` возвращает значения к тем, что были в HTML (value="...").
        // Для поисковых форм нам нужен "чистый" сброс, поэтому принудительно очищаем текстовые поля.
        this.form
            .querySelectorAll('input[type="text"], input[type="search"], textarea')
            .forEach((el) => {
                // Не трогаем date-range, они чистятся отдельно.
                if (
                    el.classList &&
                    (el.classList.contains('date-start') || el.classList.contains('date-end'))
                ) {
                    return;
                }
                el.value = '';
            });
    }

    collapseAllAccordions() {
        // Возвращаем все поля в свернутое состояние (после очистки).
        this.form.querySelectorAll('.accordion-collapse.show').forEach((collapseEl) => {
            collapseEl.classList.remove('show');
        });
        this.form.querySelectorAll('.accordion-button').forEach((btn) => {
            btn.classList.add('collapsed');
            btn.setAttribute('aria-expanded', 'false');
        });
    }

    normalizeRangeForSubmit() {
        // Если range на дефолтах — убираем hidden значения, чтобы сервер не фильтровал.
        this.form.querySelectorAll('.range-slider-wrapper').forEach((container) => {
            try {
                const minLimit = parseInt(container.dataset.min) || 0;
                const maxLimit = parseInt(container.dataset.max) || 100;

                const minHidden = container.querySelector('.slider-hidden-min');
                const maxHidden = container.querySelector('.slider-hidden-max');
                if (!minHidden || !maxHidden) return;

                const minVal = String(minHidden.value ?? '').trim();
                const maxVal = String(maxHidden.value ?? '').trim();

                if (minVal === String(minLimit) && maxVal === String(maxLimit)) {
                    minHidden.value = '';
                    maxHidden.value = '';
                }
            } catch (error) {
                console.error('Error normalizing range for submit:', error);
            }
        });
    }

    getCsrfToken() {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        return cookieValue || '';
    }
}

// Инициализация всех форм поиска на странице
document.addEventListener('DOMContentLoaded', function() {
    const searchForms = document.querySelectorAll('.search-form');
    searchForms.forEach(form => {
        new UniversalSearch(form);
    });
});
