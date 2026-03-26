// Comments System - Чистый JavaScript без зависимостей
(function() {
    'use strict';
    
    // Конфигурация по умолчанию
    const DEFAULT_CONFIG = {
        apiBaseUrl: '/comments/',
        itemsPerPage: 10,
        autoLoad: true,
        enableSorting: true,
        enableFiltering: true,
        showStats: true,
        showForm: true,
        modalEnabled: true
    };
    
    // Класс системы комментариев
    class CommentsSystem {
        constructor(container, config = {}) {
            this.container = container;
            this.config = { ...DEFAULT_CONFIG, ...config };
            this.currentPage = 1;
            this.currentSort = 'newest';
            this.currentFilter = 'all';
            this.hasMore = true;
            this.isLoading = false;
            this.userComment = null;
            
            this.init();
        }
        
        init() {
            // Получаем данные из контейнера
            this.contentTypeId = this.container.dataset.contentTypeId;
            this.objectId = this.container.dataset.objectId;
            this.hasRating = this.container.dataset.hasRating === 'true';
            this.loadComments(true);
            // Инициализация компонентов
            this.initForm();
            this.initStars();
            this.initControls();
            this.initModal();
            
            // Загрузка данных
            if (this.config.autoLoad) {
                this.loadStatistics();
                this.loadComments();
            }
            
            // Проверка комментария пользователя
            this.checkUserComment();
        }
        
        // ========== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ==========
        
        getCookie(name) {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }
        
        showMessage(message, type = 'success', container = null) {
            const target = container || this.container;
            
            // Ищем сообщение с таким же текстом
            const existing = target.querySelector(`.message[data-text="${message}"]`);
            if (existing) {
                return; // Уже есть такое сообщение
            }
            
            // Создаем новое сообщение
            const messageEl = document.createElement('div');
            messageEl.className = `message message-${type}`;
            messageEl.textContent = message;
            messageEl.dataset.text = message; // Сохраняем текст в data-атрибут
            
            target.prepend(messageEl);
            
            // Автоматическое скрытие
            if (type === 'success') {
                setTimeout(() => {
                    if (messageEl.parentNode) {
                        messageEl.remove();
                    }
                }, 5000);
            }
        }
        
        showLoading(show = true) {
            const loadingEl = this.container.querySelector('.loading-indicator');
            if (loadingEl) {
                loadingEl.style.display = show ? 'block' : 'none';
            }
        }
        
        // ========== ФОРМА КОММЕНТАРИЯ ==========
        
        initForm() {
            const form = this.container.querySelector('.comment-form');
            if (!form) return;
            
            // Инициализация счетчика символов
            const textarea = form.querySelector('textarea');
            if (textarea) {
                textarea.addEventListener('input', this.updateCharCounter.bind(this));
                this.updateCharCounter({ target: textarea });
            }
            
            // Отправка формы
            form.addEventListener('submit', this.handleFormSubmit.bind(this));
            
            // Автозаполнение для авторизованных пользователей
            this.autoFillForm();
        }
        
        autoFillForm() {
            if (!this.config.autoFill) return;
            
            const form = this.container.querySelector('.comment-form');
            if (!form) return;
            
            // Здесь можно добавить логику автозаполнения
            // из localStorage или других источников
        }
        
        updateCharCounter(event) {
            const textarea = event.target;
            const counter = textarea.closest('.form-group').querySelector('.char-counter');
            if (!counter) return;
            
            const maxLength = textarea.getAttribute('maxlength') || 2000;
            const currentLength = textarea.value.length;
            const remaining = maxLength - currentLength;
            
            counter.textContent = `${currentLength}/${maxLength}`;
            counter.classList.remove('warning', 'error');
            
            if (remaining < 50) {
                counter.classList.add('warning');
            }
            
            if (remaining < 10) {
                counter.classList.add('error');
            }
        }
        
        async handleFormSubmit(event) {
            event.preventDefault();
            const form = event.target;
            
            // Валидация
            if (!this.validateForm(form)) {
                return;
            }
            
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            
            // Показываем индикатор загрузки
            submitBtn.disabled = true;
            submitBtn.innerHTML = `
                <span class="spinner"></span>
                Отправка...
            `;
            
            try {
                const formData = new FormData(form);
                
                // Добавляем CSRF токен
                const csrfToken = this.getCookie('csrftoken');
                if (csrfToken) {
                    formData.append('csrfmiddlewaretoken', csrfToken);
                }
                
                const response = await fetch(
                    `${this.config.apiBaseUrl}submit/${this.contentTypeId}/${this.objectId}/`,
                    {
                        method: 'POST',
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest',
                        },
                        body: formData
                    }
                );
                
                const data = await response.json();
                
                if (data.success) {
                    this.showMessage(data.message, 'success');
                    
                    // Сброс формы
                    form.reset();
                    
                    // Скрываем форму если нужно
                    if (this.config.modalEnabled) {
                        const modal = bootstrap.Modal.getInstance(
                            this.container.querySelector('.comment-modal')
                        );
                        if (modal) {
                            modal.hide();
                        }
                    }
                    
                    // Обновляем статистику
                    if (data.statistics) {
                        this.updateStatistics(data.statistics);
                    }
                    
                    // Добавляем новый комментарий в список
                    if (data.comment) {
                        this.addNewComment(data.comment);
                        this.hasRating = true;
                        this.container.dataset.hasRating = 'true';
                    }
                } else {
                    this.showMessage(data.errors || data.error, 'error', form);
                }
            } catch (error) {
                console.error('Error submitting comment:', error);
                this.showMessage('Ошибка соединения. Попробуйте позже.', 'error', form);
            } finally {
                // Восстанавливаем кнопку
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
            }
        }
        
        validateForm(form) {
            let isValid = true;
            const errors = [];
            
            // Проверка рейтинга
            const rating = form.querySelector('input[name="rating"]');
            if (!rating || !rating.value || rating.value < 1 || rating.value > 5) {
                errors.push('Выберите оценку от 1 до 5 звезд');
                isValid = false;
            }
            
            // Проверка имени
            const name = form.querySelector('input[name="name"]');
            if (name && name.required && !name.value.trim()) {
                errors.push('Введите ваше имя');
                isValid = false;
            }
            
            // Проверка комментария
            const text = form.querySelector('textarea[name="text"]');
            if (text && text.value.trim().length < 10) {
                errors.push('Комментарий должен содержать минимум 10 символов');
                isValid = false;
            }
            
            // Показываем ошибки
            if (errors.length > 0) {
                this.showMessage(errors.join('<br>'), 'error', form);
            }
            
            return isValid;
        }
        
        // ========== ЗВЕЗДЫ РЕЙТИНГА ==========
        
        initStars() {
            // Звезды в форме
            const starButtons = this.container.querySelectorAll('.star-btn');
            starButtons.forEach(btn => {
                btn.addEventListener('click', this.handleStarClick.bind(this));
                btn.addEventListener('mouseenter', this.handleStarHover.bind(this));
                btn.addEventListener('mouseleave', this.handleStarLeave.bind(this));
            });
            
            // Звезды отображения
            this.initDisplayStars();
        }
        
        handleStarClick(event) {
            const button = event.currentTarget;
            const value = parseInt(button.dataset.value);
            const hiddenInput = button.closest('.rating-input').querySelector('input[name="rating"]');
            
            if (hiddenInput) {
                hiddenInput.value = value;
            }
            
            // Обновляем отображение
            const container = button.closest('.stars-selector');
            if (container) {
                const buttons = container.querySelectorAll('.star-btn');
                buttons.forEach((btn, index) => {
                    if (index < value) {
                        btn.classList.add('active');
                    } else {
                        btn.classList.remove('active');
                    }
                });
            }
        }
        
        handleStarHover(event) {
            const button = event.currentTarget;
            const value = parseInt(button.dataset.value);
            const container = button.closest('.stars-selector');
            
            if (container) {
                const buttons = container.querySelectorAll('.star-btn');
                buttons.forEach((btn, index) => {
                    if (index < value) {
                        btn.style.opacity = '0.7';
                    }
                });
            }
        }
        
        handleStarLeave(event) {
            const container = event.currentTarget.closest('.stars-selector');
            if (container) {
                const buttons = container.querySelectorAll('.star-btn');
                buttons.forEach(btn => {
                    btn.style.opacity = '';
                });
            }
        }
        
        initDisplayStars() {
            // Автоматическое отображение звезд на основе рейтинга
            const ratingElements = this.container.querySelectorAll('[data-rating]');
            ratingElements.forEach(el => {
                const rating = parseFloat(el.dataset.rating);
                this.renderStars(el, rating);
            });
        }
        
        renderStars(container, rating) {
            if (!container || !rating) return;
            
            let starsHtml = '';
            const fullStars = Math.floor(rating);
            const hasHalfStar = rating % 1 >= 0.5;
            
            for (let i = 1; i <= 5; i++) {
                if (i <= fullStars) {
                    starsHtml += '<span class="star filled">★</span>';
                } else if (i === fullStars + 1 && hasHalfStar) {
                    starsHtml += '<span class="star half">★</span>';
                } else {
                    starsHtml += '<span class="star">☆</span>';
                }
            }
            
            container.innerHTML = starsHtml;
        }
        
        // ========== УПРАВЛЕНИЕ ==========
        
        initControls() {
            // Сортировка
            const sortButtons = this.container.querySelectorAll('.sort-btn');
            sortButtons.forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.handleSortChange(btn.dataset.sort);
                });
            });
            
            // Фильтрация
            const filterButtons = this.container.querySelectorAll('.filter-badge');
            filterButtons.forEach(btn => {
                btn.addEventListener('click', () => {
                    this.handleFilterChange(btn.dataset.filter);
                });
            });
            
            // Кнопка "Загрузить еще"
            const loadMoreBtn = this.container.querySelector('.load-more-btn');
            if (loadMoreBtn) {
                loadMoreBtn.addEventListener('click', () => {
                    this.loadMoreComments();
                });
            }
            
            // Кнопка добавления комментария
            const addCommentBtn = this.container.querySelector('.add-comment-btn');
            if (addCommentBtn) {
                addCommentBtn.addEventListener('click', () => {
                    this.showCommentForm();
                });
            }
        }
        
        handleSortChange(sortBy) {
            if (this.currentSort === sortBy || this.isLoading) return;
            
            this.currentSort = sortBy;
            this.currentPage = 1;
            
            // Обновляем активную кнопку
            const sortButtons = this.container.querySelectorAll('.sort-btn');
            sortButtons.forEach(btn => {
                btn.classList.toggle('active', btn.dataset.sort === sortBy);
            });
            
            // Загружаем комментарии с новой сортировкой
            this.loadComments(true);
        }
        
        handleFilterChange(filterBy) {
            if (this.currentFilter === filterBy || this.isLoading) return;
            
            this.currentFilter = filterBy;
            this.currentPage = 1;
            
            // Обновляем активный фильтр
            const filterButtons = this.container.querySelectorAll('.filter-badge');
            filterButtons.forEach(btn => {
                btn.classList.toggle('active', btn.dataset.filter === filterBy);
            });
            
            // Загружаем комментарии с новым фильтром
            this.loadComments(true);
        }
        
        // ========== МОДАЛЬНОЕ ОКНО ==========
        
        initModal() {
            if (!this.config.modalEnabled) return;
            
            const modal = this.container.querySelector('.comment-modal');
            if (!modal) return;
            
            // При открытии модального окна
            modal.addEventListener('show.bs.modal', () => {
                this.prepareModalForm();
            });
            
            // При закрытии модального окна
            modal.addEventListener('hidden.bs.modal', () => {
                this.resetModalForm();
            });
        }
        
        prepareModalForm() {
            const form = this.container.querySelector('.comment-form');
            if (!form) return;
            
            // Сброс формы
            form.reset();
            
            // Сброс звезд
            const starButtons = form.querySelectorAll('.star-btn');
            starButtons.forEach(btn => {
                btn.classList.remove('active');
            });
            
            const ratingInput = form.querySelector('input[name="rating"]');
            if (ratingInput) {
                ratingInput.value = '';
            }
        }
        
        resetModalForm() {
            const form = this.container.querySelector('.comment-form');
            if (!form) return;
            
            // Очищаем сообщения
            const messages = form.querySelectorAll('.message');
            messages.forEach(msg => msg.remove());
        }
        
        showCommentForm() {
            if (!this.config.modalEnabled) {
                // Показываем форму напрямую
                const formContainer = this.container.querySelector('.comments-form-container');
                if (formContainer) {
                    formContainer.classList.remove('hidden');
                    formContainer.scrollIntoView({ behavior: 'smooth' });
                }
                return;
            }
            
            // Показываем модальное окно
            const modal = new bootstrap.Modal(
                this.container.querySelector('.comment-modal')
            );
            modal.show();
        }
        
        // ========== ЗАГРУЗКА ДАННЫХ ==========
        
        async loadStatistics() {
            if (!this.config.showStats) return;
            
            try {
                const response = await fetch(
                    `${this.config.apiBaseUrl}stats/${this.contentTypeId}/${this.objectId}/`,
                    {
                        headers: {
                            'Accept': 'application/json',
                        }
                    }
                );
                
                const data = await response.json();
                
                if (data.success) {
                    this.updateStatistics(data.statistics);
                }
            } catch (error) {
                console.error('Error loading statistics:', error);
            }
        }
        
        async loadComments(clear = false) {
            if (this.isLoading) return;
            
            this.isLoading = true;
            this.showLoading(true);
            
            const commentsList = this.container.querySelector('.comments-list');
            if (!commentsList) return;
            
            if (clear) {
                commentsList.innerHTML = '';
                this.hasMore = true;
            }
            
            try {
                const params = new URLSearchParams({
                    page: this.currentPage,
                    per_page: this.config.itemsPerPage,
                    sort: this.currentSort,
                    filter: this.currentFilter
                });
                
                const response = await fetch(
                    `${this.config.apiBaseUrl}list/${this.contentTypeId}/${this.objectId}/?${params}`,
                    {
                        headers: {
                            'Accept': 'application/json',
                        }
                    }
                );
                
                const data = await response.json();
                
                if (data.success) {
                    // Обновляем список комментариев
                    if (data.comments.length > 0) {
                        this.renderComments(data.comments, clear);
                    } else if (clear) {
                        this.showEmptyState();
                    }
                    
                    // Обновляем пагинацию
                    this.hasMore = data.pagination.has_next;
                    this.updatePagination(data.pagination);
                    
                    // Сохраняем данные пользователя
                    if (data.user_comment) {
                        this.userComment = data.user_comment;
                    }
                }
            } catch (error) {
                console.error('Error loading comments:', error);
                if (clear) {
                    this.showErrorState();
                }
            } finally {
                this.isLoading = false;
                this.showLoading(false);
            }
        }
        
        async loadMoreComments() {
            if (!this.hasMore || this.isLoading) return;
            
            this.currentPage++;
            await this.loadComments(false);
        }
        
        // ========== ОТОБРАЖЕНИЕ ДАННЫХ ==========
        
        updateStatistics(stats) {
            // Средний рейтинг
            const avgElement = this.container.querySelector('.average-number');
            if (avgElement && stats.average_rating) {
                avgElement.textContent = stats.average_rating.toFixed(1);
            }
            
            // Количество комментариев
            const countElement = this.container.querySelector('.average-text');
            if (countElement && stats.total !== undefined) {
                countElement.textContent = `${stats.total} оценок`;
            }
            
            // Звезды отображения
            const starsContainer = this.container.querySelector('.stars-display');
            if (starsContainer && stats.average_rating) {
                this.renderStars(starsContainer, stats.average_rating);
            }
            
            // Распределение
            if (stats.ratings_distribution && stats.total > 0) {
                for (let i = 1; i <= 5; i++) {
                    const row = this.container.querySelector(`.distribution-row:nth-child(${6 - i})`);
                    if (row) {
                        const count = stats.ratings_distribution[i] || 0;
                        const percentage = (count / stats.total) * 100;
                        
                        const fill = row.querySelector('.distribution-fill');
                        const countEl = row.querySelector('.distribution-count');
                        
                        if (fill) {
                            fill.style.width = `${percentage}%`;
                        }
                        
                        if (countEl) {
                            countEl.textContent = count;
                        }
                    }
                }
            }
        }
        
        renderComments(comments, clear) {
            const commentsList = this.container.querySelector('.comments-list');
            if (!commentsList) return;
            
            if (clear) {
                commentsList.innerHTML = '';
            }
            
            comments.forEach(comment => {
                const commentEl = this.createCommentElement(comment);
                commentsList.appendChild(commentEl);
            });
        }
        
        createCommentElement(comment) {
            const li = document.createElement('li');
            li.className = 'comment-item';
            li.dataset.commentId = comment.id;
            
            // Аватар
            const avatarText = comment.name ? comment.name[0].toUpperCase() : '?';
            const avatarClass = comment.is_verified ? 'user-avatar verified' : 'user-avatar';
            
            // Бейджи пользователя
            let userBadge = '';
            if (comment.user_type === 'staff') {
                userBadge = '<span class="badge bg-danger">Админ</span>';
            } else if (comment.user_type === 'authenticated') {
                userBadge = '<span class="badge bg-success">Пользователь</span>';
            } else {
                userBadge = '<span class="badge bg-secondary">Аноним</span>';
            }
            
            // Звезды рейтинга
            let starsHtml = '';
            for (let i = 1; i <= 5; i++) {
                starsHtml += i <= comment.rating ? '★' : '☆';
            }
            
            // Ответ администратора
            let adminReplyHtml = '';
            if (comment.has_admin_reply && comment.admin_reply) {
                adminReplyHtml = `
                    <div class="admin-reply">
                        <div class="admin-reply-header">
                            <h6 class="admin-reply-title">
                                <span class="text-success">✓</span>
                                Ответ администратора
                            </h6>
                            ${comment.replied_at ? `
                                <span class="admin-reply-date">${comment.replied_at}</span>
                            ` : ''}
                        </div>
                        <div class="admin-reply-content">
                            ${comment.admin_reply.replace(/\n/g, '<br>')}
                        </div>
                    </div>
                `;
            }
            
            li.innerHTML = `
                <div class="comment-header">
                    <div class="comment-user">
                        <div class="${avatarClass}">${avatarText}</div>
                        <div class="user-info">
                            <div class="user-name">
                                ${comment.name}
                                ${userBadge}
                                ${comment.is_verified ? '<span class="verified-badge">✓ Проверено</span>' : ''}
                            </div>
                            <div class="user-meta">
                                <span>${comment.created_at}</span>
                            </div>
                        </div>
                    </div>
                    <div class="comment-rating" title="${comment.rating_display}">
                        ${starsHtml}
                    </div>
                </div>
                <div class="comment-content">
                    ${comment.text.replace(/\n/g, '<br>')}
                </div>
                ${adminReplyHtml}
            `;
            
            return li;
        }
        
        addNewComment(comment) {
            const commentsList = this.container.querySelector('.comments-list');
            if (!commentsList) return;
            
            // Если список пустой, удаляем пустое состояние
            const emptyState = commentsList.querySelector('.empty-state');
            if (emptyState) {
                emptyState.remove();
            }
            
            // Добавляем новый комментарий в начало
            const commentEl = this.createCommentElement(comment);
            commentsList.prepend(commentEl);
            
            // Плавное появление
            commentEl.style.animation = 'fadeIn 0.3s ease';
        }
        
        updatePagination(pagination) {
            const loadMoreBtn = this.container.querySelector('.load-more-btn');
            if (!loadMoreBtn) return;
            
            if (this.hasMore) {
                loadMoreBtn.classList.remove('hidden');
                loadMoreBtn.disabled = false;
                loadMoreBtn.innerHTML = `
                    Загрузить еще
                    <span class="text-muted">(${pagination.current_page}/${pagination.total_pages})</span>
                `;
            } else {
                loadMoreBtn.classList.add('hidden');
            }
        }
        
        showEmptyState() {
            const commentsList = this.container.querySelector('.comments-list');
            if (!commentsList) return;
            
            commentsList.innerHTML = `
                <li class="empty-state">
                    <div class="empty-icon">💬</div>
                    <h4 class="empty-title">Пока нет комментариев</h4>
                    <p class="empty-text">Будьте первым, кто оставит отзыв!</p>
                    <button type="button" class="btn btn-primary add-comment-btn">
                        Оставить комментарий
                    </button>
                </li>
            `;
            
            // Добавляем обработчик кнопки
            const addBtn = commentsList.querySelector('.add-comment-btn');
            if (addBtn) {
                addBtn.addEventListener('click', () => {
                    this.showCommentForm();
                });
            }
        }
        
        showErrorState() {
            const commentsList = this.container.querySelector('.comments-list');
            if (!commentsList) return;
            
            commentsList.innerHTML = `
                <li class="empty-state">
                    <div class="empty-icon text-danger">⚠️</div>
                    <h4 class="empty-title">Ошибка загрузки</h4>
                    <p class="empty-text">Не удалось загрузить комментарии. Пожалуйста, попробуйте позже.</p>
                    <button type="button" class="btn btn-outline-primary" onclick="location.reload()">
                        Обновить страницу
                    </button>
                </li>
            `;
        }
        
        // ========== ПРОВЕРКА КОММЕНТАРИЯ ПОЛЬЗОВАТЕЛЯ ==========
        
        async checkUserComment() {
            // Можно добавить проверку через API
            // или использовать данные из data-атрибутов
        }
        
        // ========== АДМИНСКИЕ ФУНКЦИИ ==========
        
        initAdminFeatures() {
            if (!this.container.dataset.isStaff === 'true') return;
            
            // Кнопки ответа администратора
            const replyButtons = this.container.querySelectorAll('.admin-reply-btn');
            replyButtons.forEach(btn => {
                btn.addEventListener('click', (e) => {
                    this.showAdminReplyForm(e.target.dataset.commentId);
                });
            });
            
            // Кнопки верификации
            const verifyButtons = this.container.querySelectorAll('.verify-btn');
            verifyButtons.forEach(btn => {
                btn.addEventListener('click', (e) => {
                    this.toggleVerification(e.target.dataset.commentId);
                });
            });
        }
        
        showAdminReplyForm(commentId) {
            // Реализация формы ответа администратора
            console.log('Admin reply to comment:', commentId);
        }
        
        toggleVerification(commentId) {
            // Реализация верификации комментария
            console.log('Toggle verification for comment:', commentId);
        }
    }
    
    // ========== ИНИЦИАЛИЗАЦИЯ НА СТРАНИЦЕ ==========
    
    document.addEventListener('DOMContentLoaded', () => {
        // Инициализация всех виджетов комментариев на странице
        const widgets = document.querySelectorAll('.comments-widget');
        widgets.forEach(widget => {
            try {
                new CommentsSystem(widget);
            } catch (error) {
                console.error('Error initializing comments widget:', error);
            }
        });
        
        // Глобальные обработчики
        initGlobalHandlers();
    });
    
    function initGlobalHandlers() {
        // Открытие формы комментария по хешу
        if (window.location.hash === '#add-comment') {
            const widget = document.querySelector('.comments-widget');
            if (widget) {
                const commentsSystem = new CommentsSystem(widget);
                setTimeout(() => {
                    commentsSystem.showCommentForm();
                }, 500);
            }
        }
        
        // Плавная прокрутка к комментариям
        const commentLinks = document.querySelectorAll('a[href="#comments"]');
        commentLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const commentsSection = document.querySelector('.comments-widget');
                if (commentsSection) {
                    commentsSection.scrollIntoView({ behavior: 'smooth' });
                }
            });
        });
    }
    
    // Экспорт для использования в других скриптах
    window.CommentsSystem = CommentsSystem;
    
})();
