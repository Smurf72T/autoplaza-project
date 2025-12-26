// static/js/dynamic-models.js
class DynamicModelsLoader {
    constructor(options = {}) {
        this.brandSelector = options.brandSelector || '#id_brand';
        this.modelSelector = options.modelSelector || '#id_model';
        this.apiUrl = options.apiUrl || '/advertisements/models-api/';
        this.initialize();
    }

    initialize() {
        const brandSelect = document.querySelector(this.brandSelector);
        const modelSelect = document.querySelector(this.modelSelector);

        if (!brandSelect || !modelSelect) {
            console.warn('DynamicModelsLoader: brand or model select not found');
            return;
        }

        brandSelect.addEventListener('change', (event) => {
            this.loadModels(event.target.value);
        });

        // Загружаем модели при загрузке страницы, если бренд уже выбран
        if (brandSelect.value) {
            this.loadModels(brandSelect.value);
        }
    }

    async loadModels(brandId) {
        const modelSelect = document.querySelector(this.modelSelector);
        const loadingIndicator = document.getElementById('model-loading');

        if (!brandId) {
            modelSelect.innerHTML = '<option value="">Сначала выберите марку</option>';
            modelSelect.disabled = true;
            return;
        }

        // Показываем индикатор загрузки
        if (loadingIndicator) {
            loadingIndicator.style.display = 'block';
        }
        modelSelect.disabled = true;
        modelSelect.innerHTML = '<option value="">Загрузка...</option>';

        try {
            const response = await fetch(`${this.apiUrl}?brand_id=${brandId}`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Очищаем и заполняем select
            modelSelect.innerHTML = '<option value="">Выберите модель</option>';

            if (data.length === 0) {
                modelSelect.innerHTML += '<option value="" disabled>Нет доступных моделей</option>';
            } else {
                data.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model.id;
                    option.textContent = model.full_name || model.name;
                    option.dataset.yearStart = model.year_start || '';
                    option.dataset.yearEnd = model.year_end || '';
                    option.dataset.bodyType = model.body_type || '';
                    modelSelect.appendChild(option);
                });
            }

            modelSelect.disabled = false;

        } catch (error) {
            console.error('Ошибка загрузки моделей:', error);
            modelSelect.innerHTML = '<option value="">Ошибка загрузки</option>';
        } finally {
            // Скрываем индикатор загрузки
            if (loadingIndicator) {
                loadingIndicator.style.display = 'none';
            }
        }
    }
}

// Инициализация при загрузке DOM
document.addEventListener('DOMContentLoaded', () => {
    new DynamicModelsLoader();
});