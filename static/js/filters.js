// autoplaza/static/js/filters.js
console.log('Filters.js loaded');

class CarFilters {
    constructor() {
        console.log('CarFilters constructor called');

        this.mainBrandSelect = document.getElementById('brand-filter');
        this.mainModelSelect = document.getElementById('model-filter');

        console.log('Found elements:', {
            brand: this.mainBrandSelect,
            model: this.mainModelSelect
        });

        this.init();
    }

    init() {
        console.log('CarFilters init called');

        // Инициализируем главный фильтр
        if (this.mainBrandSelect && this.mainModelSelect) {
            console.log('Setting up event listener for brand select');
            this.mainBrandSelect.addEventListener('change', () => {
                console.log('Brand changed to:', this.mainBrandSelect.value);
                this.updateMainModels();
            });

            // Если при загрузке уже выбрана марка (например, из URL)
            if (this.mainBrandSelect.value) {
                console.log('Brand already selected on load:', this.mainBrandSelect.value);
                this.updateMainModels().then(() => {
                    // Восстанавливаем выбранную модель
                    const urlParams = new URLSearchParams(window.location.search);
                    const modelId = urlParams.get('model');
                    if (modelId && this.mainModelSelect) {
                        this.mainModelSelect.value = modelId;
                    }
                });
            }
        } else {
            console.warn('Filter elements not found on this page');
        }
    }

    async updateMainModels() {
        return this.updateModels(this.mainBrandSelect, this.mainModelSelect);
    }

    async updateModels(brandSelect, modelSelect) {
        const brandId = brandSelect.value;

        // Очищаем поле моделей
        modelSelect.innerHTML = '<option value="">Все модели</option>';

        if (!brandId) {
            modelSelect.disabled = true;
            return;
        }

        // Показываем загрузку
        modelSelect.disabled = true;
        modelSelect.innerHTML = '<option value="">Загрузка...</option>';

        try {
            // AJAX запрос
            const response = await fetch(`/api/models/?brand_id=${brandId}`);

            if (!response.ok) {
                throw new Error(`Ошибка HTTP: ${response.status}`);
            }

            const data = await response.json();

            let options = '<option value="">Все модели</option>';
            data.forEach(model => {
                options += `<option value="${model.id}">${model.name}</option>`;
            });

            modelSelect.innerHTML = options;
            modelSelect.disabled = false;

        } catch (error) {
            console.error('Ошибка загрузки моделей:', error);
            modelSelect.innerHTML = '<option value="">Ошибка загрузки</option>';
        }
    }
}

// Инициализация
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new CarFilters();
    });
} else {
    new CarFilters();
}

document.addEventListener('DOMContentLoaded', function() {
    const brandSelect = document.getElementById('brand-filter');
    const modelSelect = document.getElementById('model-filter');

    if (brandSelect && modelSelect) {
        brandSelect.addEventListener('change', function() {
            const brandId = this.value;
            updateModels(brandId);
        });

        // Инициализация при загрузке
        if (brandSelect.value) {
            updateModels(brandSelect.value);
        }
    }

    function updateModels(brandId) {
        if (!brandId) {
            modelSelect.innerHTML = '<option value="">Сначала выберите марку</option>';
            modelSelect.disabled = true;
            return;
        }

        // Показать индикатор загрузки
        modelSelect.disabled = true;
        modelSelect.innerHTML = '<option value="">Загрузка моделей...</option>';

        // AJAX запрос для получения моделей
        fetch(`/api/models/?brand_id=${brandId}`)
            .then(response => {
                if (!response.ok) throw new Error('Network response was not ok');
                return response.json();
            })
            .then(data => {
                let options = '<option value="">Все модели</option>';
                data.forEach(model => {
                    options += `<option value="${model.id}">${model.name}</option>`;
                });

                modelSelect.innerHTML = options;
                modelSelect.disabled = false;
            })
            .catch(error => {
                console.error('Error loading models:', error);
                modelSelect.innerHTML = '<option value="">Ошибка загрузки</option>';
            });
    }
});

console.log('=== Autoplaza Filters Debug ===');
console.log('API URL:', '/api/models/');
console.log('Brand select found:', document.getElementById('brand-filter') !== null);
console.log('Model select found:', document.getElementById('model-filter') !== null);