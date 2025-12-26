// autoplaza/static/js/filters.js
document.addEventListener('DOMContentLoaded', function() {
    // Функция для загрузки моделей
    function loadModels(brandSlug, modelSelect, callback) {
        if (!brandSlug) {
            if (modelSelect) {
                modelSelect.innerHTML = '<option value="">Все модели</option>';
                modelSelect.disabled = true;
            }
            return;
        }

        if (modelSelect) {
            modelSelect.disabled = true;
            modelSelect.innerHTML = '<option value="">Загрузка...</option>';
        }

        fetch(`/advertisements/models-api/?brand=${brandSlug}`)
            .then(response => response.json())
            .then(data => {
                if (modelSelect) {
                    let options = '<option value="">Все модели</option>';
                    data.forEach(model => {
                        options += `<option value="${model.slug}">${model.name}</option>`;
                    });

                    modelSelect.innerHTML = options;
                    modelSelect.disabled = false;

                    // Вызываем callback если он есть
                    if (callback) callback();
                }
            })
            .catch(error => {
                console.error('Ошибка загрузки моделей:', error);
                if (modelSelect) {
                    modelSelect.innerHTML = '<option value="">Ошибка загрузки</option>';
                }
            });
    }

    // Обработка главного фильтра на странице списка объявлений
    const mainBrandSelect = document.getElementById('brand-filter');
    const mainModelSelect = document.getElementById('model-filter');

    if (mainBrandSelect && mainModelSelect) {
        mainBrandSelect.addEventListener('change', function() {
            loadModels(this.value, mainModelSelect, function() {
                // Восстанавливаем выбранное значение из GET параметров
                const selectedModel = new URLSearchParams(window.location.search).get('model');
                if (selectedModel && mainModelSelect) {
                    mainModelSelect.value = selectedModel;
                }
            });
        });

        // Если при загрузке уже выбрана марка
        if (mainBrandSelect.value) {
            loadModels(mainBrandSelect.value, mainModelSelect);
        }
    }

    // Обработка фильтра в форме создания/редактирования объявления
    const formBrandSelect = document.getElementById('id_brand');
    const formModelSelect = document.getElementById('id_model');

    if (formBrandSelect && formModelSelect) {
        // Для формы нужно использовать другой endpoint или адаптировать
        formBrandSelect.addEventListener('change', function() {
            // Здесь может быть другая логика
        });
    }
});