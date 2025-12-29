// static/js/fallback.js
function initializeModelFallback() {
    const modelSelect = document.getElementById('id_model');
    const brandSelect = document.getElementById('id_brand');

    if (!modelSelect || !brandSelect) return;

    // Предзагруженные данные моделей (если есть)
    const preloadedModels = window.PRELOADED_MODELS || {};

    brandSelect.addEventListener('change', function() {
        const brandId = this.value;

        if (preloadedModels[brandId]) {
            // Используем предзагруженные данные
            updateModelSelect(preloadedModels[brandId]);
        } else if (window.MODELS_API_URL) {
            // Пробуем API
            loadModelsFromAPI(brandId);
        } else {
            // Просим пользователя обновить страницу
            modelSelect.innerHTML = '<option value="">Выберите марку и обновите страницу</option>';
            modelSelect.disabled = true;
        }
    });
}