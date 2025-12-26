// static/js/dynamic-models.js
console.log('DynamicModelsLoader loaded');

class DynamicModelsLoader {
    constructor(options = {}) {
        console.log('DynamicModelsLoader initialized with options:', options);

        this.brandSelector = options.brandSelector || '#id_brand';
        this.modelSelector = options.modelSelector || '#id_model';
        // Используем относительный путь, так как этот файл статический
        this.apiUrl = options.apiUrl || '/advertisements/models-api/';
        this.initialize();
    }

    initialize() {
        console.log('Initializing DynamicModelsLoader...');

        const brandSelect = document.querySelector(this.brandSelector);
        const modelSelect = document.querySelector(this.modelSelector);

        console.log('Brand select found:', brandSelect);
        console.log('Model select found:', modelSelect);

        if (!brandSelect || !modelSelect) {
            console.warn('DynamicModelsLoader: brand or model select not found');
            return;
        }

        // Сохраняем первоначальное состояние
        this.originalBrandValue = brandSelect.value;

        brandSelect.addEventListener('change', (event) => {
            console.log('Brand changed to:', event.target.value);
            this.loadModels(event.target.value);
        });

        // Загружаем модели при загрузке страницы, если бренд уже выбран
        if (brandSelect.value) {
            console.log('Brand already selected on page load:', brandSelect.value);
            setTimeout(() => {
                this.loadModels(brandSelect.value);
            }, 100);
        }
    }

    async loadModels(brandId) {
        console.log('Loading models for brand ID:', brandId);

        const modelSelect = document.querySelector(this.modelSelector);
        const loadingIndicator = document.getElementById('model-loading');

        if (!brandId) {
            console.log('No brand ID provided, clearing model select');
            modelSelect.innerHTML = '<option value="">Сначала выберите марку</option>';
            modelSelect.disabled = true;
            return;
        }

        // Показываем индикатор загрузки
        if (loadingIndicator) {
            loadingIndicator.style.display = 'block';
            console.log('Showing loading indicator');
        }

        modelSelect.disabled = true;
        modelSelect.innerHTML = '<option value="">Загрузка моделей...</option>';

        try {
            const url = `${this.apiUrl}?brand_id=${encodeURIComponent(brandId)}`;
            console.log('Making request to:', url);

            const startTime = Date.now();
            const response = await fetch(url, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json'
                }
            });

            console.log('Response status:', response.status);
            console.log('Response time:', Date.now() - startTime, 'ms');

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('Response data:', data);

            // Очищаем и заполняем select
            modelSelect.innerHTML = '<option value="">Выберите модель</option>';

            if (!data || data.length === 0) {
                console.log('No models found for brand ID:', brandId);
                modelSelect.innerHTML += '<option value="" disabled>Нет доступных моделей</option>';
            } else {
                console.log(`Found ${data.length} models`);
                data.forEach((model, index) => {
                    const option = document.createElement('option');
                    option.value = model.id;
                    // Используем только имя модели без марки
                    option.textContent = model.name;

                    // Добавляем data-атрибуты если есть
                    if (model.year_start) option.dataset.yearStart = model.year_start;
                    if (model.year_end) option.dataset.yearEnd = model.year_end;
                    if (model.body_type) option.dataset.bodyType = model.body_type;

                    modelSelect.appendChild(option);
                });
            }

            modelSelect.disabled = false;

            // Триггерим событие изменения
            modelSelect.dispatchEvent(new Event('change'));

        } catch (error) {
            console.error('Error loading models:', error);
            modelSelect.innerHTML = '<option value="">Ошибка загрузки моделей</option>';
        } finally {
            // Скрываем индикатор загрузки
            if (loadingIndicator) {
                loadingIndicator.style.display = 'none';
                console.log('Hiding loading indicator');
            }
        }
    }
}

// Инициализация при загрузке DOM
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing DynamicModelsLoader');

    // Проверяем, есть ли на странице поля для загрузки моделей
    if (document.getElementById('id_brand') && document.getElementById('id_model')) {
        new DynamicModelsLoader();
    }
});

// Экспорт для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DynamicModelsLoader;
}