// Функция инициализации datepicker для всех полей
(function() {
    // Настройки для календаря
    const options = {
        format: 'dd.mm.yyyy',
        language: 'ru',
        autoclose: true
    };
    
    // Для каждого блока date-range-group
    $('.date-range-group').each(function() {
        const $range = $(this);
        const $start = $range.find('.date-start');
        const $end = $range.find('.date-end');
        
        // Инициализируем datepicker
        $start.datepicker(options);
        $end.datepicker(options);
        
        // Делаем валидацию: конец не может быть раньше начала
        $start.on('changeDate', function(e) {
            $end.datepicker('setStartDate', e.date);
        });
        
        $end.on('changeDate', function(e) {
            $start.datepicker('setEndDate', e.date);
        });
    });
}());