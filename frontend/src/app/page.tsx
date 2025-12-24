export default function HomePage() {
  return (
    <div className="text-center">
      <div className="max-w-2xl mx-auto">
        <h2 className="text-3xl font-bold mb-4">
          Добро пожаловать в AutoPlaza!
        </h2>
        <p className="text-gray-600 mb-8">
          Современная платформа для покупки и продажи автомобилей
        </p>

        <div className="grid md:grid-cols-3 gap-6 mt-8">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="text-blue-500 text-2xl mb-3">🚀</div>
            <h3 className="font-semibold mb-2">Быстрая продажа</h3>
            <p className="text-sm text-gray-500">
              Разместите объявление за 5 минут
            </p>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="text-green-500 text-2xl mb-3">🤖</div>
            <h3 className="font-semibold mb-2">AI-оценка</h3>
            <p className="text-sm text-gray-500">
              Умная оценка стоимости автомобиля
            </p>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="text-purple-500 text-2xl mb-3">🚗</div>
            <h3 className="font-semibold mb-2">Тест-драйвы</h3>
            <p className="text-sm text-gray-500">
              Организация тест-драйвов онлайн
            </p>
          </div>
        </div>

        <div className="mt-12 p-6 bg-blue-50 rounded-lg">
          <h3 className="font-bold text-lg mb-3">✅ Фронтенд успешно запущен!</h3>
          <div className="text-left bg-white p-4 rounded mt-3">
            <p className="font-medium mb-2">Следующие шаги:</p>
            <ul className="list-disc pl-5 space-y-1 text-sm">
              <li>Запустить бэкенд Django</li>
              <li>Настроить базу данных</li>
              <li>Создать API endpoints</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}