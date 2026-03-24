(function() {
    // Инициализация всех форм поиска на странице
    const form = document.querySelector('.search-form');
    if (!form) return;
    
    // Проверяем, что Select2 доступен
    if (typeof $.fn.select2 === 'undefined') {
        console.error('Select2 не загружен!');
        return;
    }
    
    // Функция для определения родительского элемента dropdown
    function getDropdownParent() {
        // Определяем родительский элемент для dropdown
        // Если форма в модальном окне - используем модальное окно
        const modal = form.closest('.modal');
        if (modal) {
            return $(modal);
        }
        
        // Иначе используем body
        return $(document.body);
    }
    
    // Функция для проверки нужно ли выполнять автоматический поиск
    // function shouldAutoSearch() {
    //     // Автопоиск только если в основном поле есть текст
    //     const mainSearch = form;
    //     return mainSearch && mainSearch.value.length >= 2;
    // }
    
    // Функция для выполнения поиска
    // function performSearch() {
    //     // Ваша логика поиска здесь
    //     console.log('Выполняем поиск...');
    // }
    
    // Инициализация Select2 с настройками для модальных окон
    const select2Options = {
        theme: 'bootstrap-5',
        width: '100%',
        dropdownParent: getDropdownParent(), // ВАЖНО для модалок!
        minimumInputLength: 0,
        allowClear: true
    };
    
    // Одиночный выбор
    $(form).find('.select').each(function() {
        $(this).select2({
            ...select2Options,
            placeholder: $(this).data('placeholder') || 'Выберите...'
        });
    });
    
    // Множественный выбор
    $(form).find('.select_multiple').each(function() {
        $(this).select2({
            ...select2Options,
            placeholder: $(this).data('placeholder') || 'Выберите варианты...'
        });
    });
    
    // Событие изменения
    $(form).on('change', '.select, .select_multiple', function() {
        // if (shouldAutoSearch()) {
        //     performSearch();
        // }
    });
    
    // Обработка фокуса в модальных окнах
    function setupModalFocus() {
        const modal = form.closest('.modal');
        if (!modal) return;

        let lastActiveElementBeforeModal = null;

        $(modal).on('show.bs.modal', function() {
            lastActiveElementBeforeModal = document.activeElement;
        });
        
        // При открытии модалки - фокус на первое поле
        $(modal).on('shown.bs.modal', function() {
            // Даем время на отрисовку Select2
            setTimeout(function() {
                const firstSelect = form.querySelector('.select');
                if (firstSelect) {
                    $(firstSelect).focus();
                } else {
                    const firstInput = form.querySelector('input, select, textarea');
                    if (firstInput) {
                        firstInput.focus();
                    }
                }
            }, 100);
        });
        
        // При закрытии модалки: закрываем Select2 и убираем фокус
        $(modal).on('hide.bs.modal', function() {
            $(form)
                .find('.select, .select_multiple')
                .each(function() {
                    const $select = $(this);
                    if ($select.data('select2')) {
                        $select.select2('close');
                    }
                });

            const active = document.activeElement;
            if (active && modal.contains(active)) {
                active.blur();
            }
        });

        $(modal).on('hidden.bs.modal', function() {
            const el = lastActiveElementBeforeModal;
            if (el && typeof el.focus === 'function') {
                el.focus();
            }
        });
    }
    
    // Вызываем функцию настройки фокуса
    setupModalFocus();
})();