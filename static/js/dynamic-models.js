// static/js/dynamic-models.js
// Этот файл используется ТОЛЬКО для страницы фильтров (/advertisements/)

console.log('DynamicModelsLoader for filters loaded');

class DynamicModelsLoader {
    constructor(options = {}) {
        console.log('DynamicModelsLoader initialized with options:', options);

        this.brandSelector = options.brandSelector || '#brand-filter';
        this.modelSelector = options.modelSelector || '#model-filter';
        this.apiUrl = options.apiUrl || '/advertisements/models-api/';

        // Проверяем, что это страница фильтров (не форма создания)
        const brandSelect = document.querySelector(this.brandSelector);
        const modelSelect = document.querySelector(this.modelSelector);

        if (brandSelect && modelSelect && !document.getElementById('id_brand')) {
            // Только если есть элементы фильтров и нет формы создания
            this.brandSelect = brandSelect;
            this.modelSelect = modelSelect;
            this.initialize();
        } else {
            console.log('Not a filters page or form creation page detected, skipping initialization');
        }
    }

    initialize() {
        console.log('Initializing filters DynamicModelsLoader...');

        this.brandSelect.addEventListener('change', (event) => {
            console.log('Brand filter changed to:', event.target.value);
            this.loadModels(event.target.value);
        });

        // Если при загрузке уже выбрана марка
        if (this.brandSelect.value) {
            console.log('Brand filter already selected on page load:', this.brandSelect.value);
            setTimeout(() => {
                this.loadModels(this.brandSelect.value);
            }, 100);
        }
    }

    async loadModels(brandId) {
        console.log('Loading filter models for brand ID:', brandId);

        if (!brandId) {
            console.log('No brand ID provided, clearing filter model select');
            this.modelSelect.innerHTML = '<option value="">Все модели</option>';
            this.modelSelect.disabled = true;
            return;
        }

        this.modelSelect.disabled = true;
        this.modelSelect.innerHTML = '<option value="">Загрузка...</option>';

        try {
            const url = `${this.apiUrl}?brand_id=${encodeURIComponent(brandId)}`;
            console.log('Making filter request to:', url);

            const response = await fetch(url, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json'
                }
            });

            console.log('Filter response status:', response.status);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('Filter response data:', data);

            // Очищаем и заполняем select
            this.modelSelect.innerHTML = '<option value="">Все модели</option>';

            if (!data || data.length === 0) {
                console.log('No models found for brand filter ID:', brandId);
            } else {
                console.log(`Found ${data.length} models for filter`);
                data.forEach((model) => {
                    const option = document.createElement('option');
                    option.value = model.id;
                    option.textContent = model.name;
                    this.modelSelect.appendChild(option);
                });
            }

            this.modelSelect.disabled = false;

        } catch (error) {
            console.error('Error loading filter models:', error);
            this.modelSelect.innerHTML = '<option value="">Ошибка загрузки</option>';
        }
    }
}

// Инициализация при загрузке DOM
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, checking for filters...');

    // Инициализируем только если это страница с фильтрами и НЕ страница формы
    if (document.getElementById('brand-filter') &&
        document.getElementById('model-filter') &&
        !document.getElementById('id_brand')) {
        console.log('Initializing filters on list page');
        new DynamicModelsLoader();
    } else {
        console.log('Not a filters page or form creation page');
    }
});