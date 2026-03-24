(function() {
    'use strict';

    // Конфигурация
    const CONFIG = {
        SELECTORS: {
            FORM: '.search-form',
            SLIDER: '.slider',
            CONTAINER: '.range-slider-wrapper',
            MIN_DISPLAY: '.slider-value-min',
            MAX_DISPLAY: '.slider-value-max',
            MIN_INPUT: '.slider-min-input',
            MAX_INPUT: '.slider-max-input',
            MIN_HIDDEN: '.slider-hidden-min',
            MAX_HIDDEN: '.slider-hidden-max'
        },
        KEYS: {
            ALLOWED: ['Backspace', 'Delete', 'Tab', 'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', '.', ',']
        },
        LOG_PREFIX: '[RangeSlider]'
    };

    /**
     * Класс для управления слайдером с поддержкой свободного ввода
     */
    class SmartRangeSlider {
        constructor(container, index) {
            this.container = container;
            this.index = index;
            this.sliderElement = container.querySelector(CONFIG.SELECTORS.SLIDER);
            this.minLimit = parseInt(container.dataset.min) || 0;
            this.maxLimit = parseInt(container.dataset.max) || 100;
            this.minStart = parseInt(container.dataset.startMin) || 0;
            this.maxStart = parseInt(container.dataset.startMax) || 100;
            this.stepValue = parseInt(container.dataset.step) || 1;
            this.slider = null;
            
            // Храним предыдущие значения для восстановления
            this.previousValues = {
                min: this.minLimit,
                max: this.maxLimit
            };
            
            // Отслеживаем фокус
            this.activeInput = null;
            
            this.elements = {
                minDisplay: container.querySelector(CONFIG.SELECTORS.MIN_DISPLAY),
                maxDisplay: container.querySelector(CONFIG.SELECTORS.MAX_DISPLAY),
                minInput: container.querySelector(CONFIG.SELECTORS.MIN_INPUT),
                maxInput: container.querySelector(CONFIG.SELECTORS.MAX_INPUT),
                minHidden: container.querySelector(CONFIG.SELECTORS.MIN_HIDDEN),
                maxHidden: container.querySelector(CONFIG.SELECTORS.MAX_HIDDEN)
            };
        }

        /**
         * Инициализация слайдера
         */
        init() {
            if (!this.sliderElement) {
                console.warn(`${CONFIG.LOG_PREFIX} Slider element not found`);
                return false;
            }

            try {
                this.createSlider();
                this.setupEventListeners();
                this.setInitialValues();
                console.log(`${CONFIG.LOG_PREFIX} Slider ${this.index + 1} initialized successfully`);
                return true;
            } catch (error) {
                console.error(`${CONFIG.LOG_PREFIX} Failed to initialize slider ${this.index + 1}:`, error);
                return false;
            }
        }

        /**
         * Создание экземпляра noUiSlider
         */
        createSlider() {
            noUiSlider.create(this.sliderElement, {
                start: [this.minLimit, this.maxLimit],
                connect: true,
                step: this.stepValue,
                start: [this.minStart, this.maxStart],
                range: {
                    min: this.minLimit,
                    max: this.maxLimit
                },
                pips: null
            });

            this.slider = this.sliderElement.noUiSlider;
        }

        /**
         * Настройка обработчиков событий
         */
        setupEventListeners() {
            // Событие обновления слайдера
            this.slider.on('update', this.handleSliderUpdate.bind(this));

            // Настройка обработчиков для полей ввода
            this.setupInputHandlers();
        }

        /**
         * Обработка обновления слайдера
         */
        handleSliderUpdate(values) {
            const [minVal, maxVal] = values.map(val => Math.round(val));
            
            // Сохраняем новые значения
            this.previousValues.min = minVal;
            this.previousValues.max = maxVal;
            
            // Обновляем все отображения
            this.updateAllFields(minVal, maxVal);
        }

        /**
         * Обновление всех полей
         */
        updateAllFields(minVal, maxVal) {
            // Обновляем отображение
            if (this.elements.minDisplay) {
                this.elements.minDisplay.textContent = minVal;
            }
            if (this.elements.maxDisplay) {
                this.elements.maxDisplay.textContent = maxVal;
            }
            
            // Обновляем скрытые поля
            if (this.elements.minHidden) {
                this.elements.minHidden.value = minVal;
            }
            if (this.elements.maxHidden) {
                this.elements.maxHidden.value = maxVal;
            }
            
            // Обновляем input поля только если они не в фокусе
            if (this.elements.minInput && this.activeInput !== this.elements.minInput) {
                this.elements.minInput.value = minVal;
            }
            if (this.elements.maxInput && this.activeInput !== this.elements.maxInput) {
                this.elements.maxInput.value = maxVal;
            }
        }

        /**
         * Настройка обработчиков для полей ввода
         */
        setupInputHandlers() {
            if (this.elements.minInput) {
                this.setupInputHandler(this.elements.minInput, true);
            }
            
            if (this.elements.maxInput) {
                this.setupInputHandler(this.elements.maxInput, false);
            }
        }

        /**
         * Настройка обработчика для конкретного поля ввода
         */
        setupInputHandler(inputElement, isMinField) {
            // Сохраняем предыдущее значение при фокусе
            inputElement.addEventListener('focus', () => {
                this.activeInput = inputElement;
                this.previousValues[isMinField ? 'min' : 'max'] = inputElement.value;
            });
            
            // Восстанавливаем значение при потере фокуса, если новое значение некорректно
            inputElement.addEventListener('blur', () => {
                this.handleInputBlur(inputElement, isMinField);
                this.activeInput = null;
            });
            
            // Валидация при вводе
            inputElement.addEventListener('keydown', this.handleKeyDown.bind(this));
            
            // Обработка ввода в реальном времени
            inputElement.addEventListener('input', () => {
                this.handleInputChange(inputElement, isMinField);
            });
            
            // Обработка вставки
            inputElement.addEventListener('paste', (e) => {
                this.handlePaste(e, inputElement, isMinField);
            });
            
            // Настройка HTML5 атрибутов
            this.setupInputAttributes(inputElement, isMinField);
        }

        /**
         * Обработка нажатия клавиш
         */
        handleKeyDown(e) {
            // Разрешаем цифры и управляющие клавиши
            if (!/[0-9]/.test(e.key) && !CONFIG.KEYS.ALLOWED.includes(e.key)) {
                e.preventDefault();
            }
        }

        /**
         * Обработка изменения значения в поле ввода
         */
        handleInputChange(inputElement, isMinField) {
            const value = inputElement.value.trim();
            
            // Если поле пустое, ничего не делаем
            if (value === '') {
                return;
            }
            
            // Парсим число
            const numValue = parseInt(value);
            if (isNaN(numValue)) {
                return;
            }
            
            // Проверяем лимиты
            if (numValue < this.minLimit || numValue > this.maxLimit) {
                return;
            }
            
            // Получаем текущие значения слайдера
            const currentValues = this.slider.get().map(v => parseInt(v));
            let newMin = currentValues[0];
            let newMax = currentValues[1];
            
            // Обновляем соответствующее значение
            if (isMinField) {
                newMin = numValue;
            } else {
                newMax = numValue;
            }
            
            // Применяем изменения к слайдеру (разрешаем min > max)
            this.slider.set([newMin, newMax]);
        }

        /**
         * Обработка потери фокуса с полем ввода
         */
        handleInputBlur(inputElement, isMinField) {
            const value = inputElement.value.trim();
            const fieldType = isMinField ? 'min' : 'max';
            
            // Если поле пустое, восстанавливаем предыдущее значение
            if (value === '') {
                inputElement.value = this.previousValues[fieldType];
                return;
            }
            
            // Парсим число
            const numValue = parseInt(value);
            
            // Если некорректное число, восстанавливаем предыдущее значение
            if (isNaN(numValue)) {
                inputElement.value = this.previousValues[fieldType];
                return;
            }
            
            // Проверяем лимиты
            if (numValue < this.minLimit || numValue > this.maxLimit) {
                inputElement.value = this.previousValues[fieldType];
                return;
            }
            
            // Если значение корректное, обновляем слайдер
            const currentValues = this.slider.get().map(v => parseInt(v));
            let newMin = currentValues[0];
            let newMax = currentValues[1];
            
            if (isMinField) {
                newMin = numValue;
            } else {
                newMax = numValue;
            }
            
            // Обновляем слайдер
            this.slider.set([newMin, newMax]);
        }

        /**
         * Обработка вставки текста
         */
        handlePaste(event, inputElement, isMinField) {
            event.preventDefault();
            
            // Получаем текст из буфера обмена
            const clipboardData = event.clipboardData || window.clipboardData;
            const pastedText = clipboardData.getData('text');
            const pastedNumber = parseInt(pastedText);
            
            // Если это число, вставляем его
            if (!isNaN(pastedNumber)) {
                // Ограничиваем лимитами
                const limitedValue = Math.max(this.minLimit, Math.min(this.maxLimit, pastedNumber));
                inputElement.value = limitedValue;
                
                // Обновляем слайдер
                const currentValues = this.slider.get().map(v => parseInt(v));
                let newMin = currentValues[0];
                let newMax = currentValues[1];
                
                if (isMinField) {
                    newMin = limitedValue;
                } else {
                    newMax = limitedValue;
                }
                
                this.slider.set([newMin, newMax]);
            }
        }

        /**
         * Настройка HTML5 атрибутов полей ввода
         */
        setupInputAttributes(inputElement, isMinField) {
            inputElement.min = this.minLimit;
            inputElement.max = this.maxLimit;
            inputElement.step = this.stepValue;
            inputElement.placeholder = `${this.minLimit}-${this.maxLimit}`;
            
            // Добавляем подсказку
            inputElement.title = `Введите значение от ${this.minLimit} до ${this.maxLimit}`;
        }

        /**
         * Установка начальных значений
         */
        setInitialValues() {
            const initialMin = this.minStart || this.minLimit;
            const initialMax = this.maxStart || this.maxLimit;
            // Сохраняем как предыдущие значения
            this.previousValues.min = initialMin;
            this.previousValues.max = initialMax;
            
            // Устанавливаем значения
            if (this.elements.minDisplay) {
                this.elements.minDisplay.textContent = initialMin;
            }
            if (this.elements.maxDisplay) {
                this.elements.maxDisplay.textContent = initialMax;
            }
            if (this.elements.minInput) {
                this.elements.minInput.value = initialMin;
            }
            if (this.elements.maxInput) {
                this.elements.maxInput.value = initialMax;
            }
            if (this.elements.minHidden) {
                this.elements.minHidden.value = initialMin;
            }
            if (this.elements.maxHidden) {
                this.elements.maxHidden.value = initialMax;
            }
        }
    }

    /**
     * Основная функция инициализации
     */
    function initRangeSliders() {
        console.log(`${CONFIG.LOG_PREFIX} Initializing...`);
        
        // Проверяем внешнюю реализацию
        if (typeof window.initSearchRangeSliders === 'function') {
            console.log(`${CONFIG.LOG_PREFIX} Using external implementation`);
            window.initSearchRangeSliders(document.querySelector(CONFIG.SELECTORS.FORM));
            return;
        }
        
        const form = document.querySelector(CONFIG.SELECTORS.FORM);
        if (!form) {
            console.warn(`${CONFIG.LOG_PREFIX} Form not found`);
            return;
        }
        
        const sliderElements = form.querySelectorAll(CONFIG.SELECTORS.SLIDER);
        console.log(`${CONFIG.LOG_PREFIX} Found ${sliderElements.length} sliders`);
        
        if (sliderElements.length === 0) {
            console.warn(`${CONFIG.LOG_PREFIX} No slider elements found`);
            return;
        }
        
        // Инициализируем все слайдеры
        const sliders = [];
        sliderElements.forEach((sliderElement, index) => {
            const container = sliderElement.closest(CONFIG.SELECTORS.CONTAINER);
            if (!container) {
                console.error(`${CONFIG.LOG_PREFIX} Container not found for slider ${index + 1}`);
                return;
            }
            
            try {
                const slider = new SmartRangeSlider(container, index);
                if (slider.init()) {
                    sliders.push(slider);
                }
            } catch (error) {
                console.error(`${CONFIG.LOG_PREFIX} Error initializing slider ${index + 1}:`, error);
            }
        });
        
        console.log(`${CONFIG.LOG_PREFIX} Successfully initialized ${sliders.length}/${sliderElements.length} sliders`);
        
        // Сохраняем ссылку для отладки
        window.rangeSliders = sliders;
    }

    function resetToDefaults() {
        const initialMin = this.minLimit;
        const initialMax = this.maxLimit;
        
        // Сбрасываем слайдер
        this.slider.set([initialMin, initialMax]);
        
        // Обновляем предыдущие значения
        this.previousValues.min = initialMin;
        this.previousValues.max = initialMax;
        
        // Обновляем все поля
        this.updateAllFields(initialMin, initialMax);
        
        console.log(`${CONFIG.LOG_PREFIX} Slider ${this.index + 1} reset to defaults`);
        
        // Генерируем событие сброса
        const event = new CustomEvent('sliderReset', {
            detail: { min: initialMin, max: initialMax, sliderIndex: this.index }
        });
        this.container.dispatchEvent(event);
    }

    // Инициализируем при загрузке DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initRangeSliders);
    } else {
        initRangeSliders();
    }

    // Экспортируем для повторного использования
    window.initRangeSliders = initRangeSliders;

})();