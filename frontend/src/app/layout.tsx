import './globals.css'

export const metadata = {
  title: 'AutoPlaza - Продажа автомобилей',
  description: 'Лучшая площадка для покупки и продажи автомобилей',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ru">
      <body className="bg-gray-50">
        <div className="min-h-screen">
          <header className="bg-white shadow">
            <div className="container mx-auto px-4 py-4">
              <h1 className="text-2xl font-bold text-blue-600">
                🚗 AutoPlaza
              </h1>
            </div>
          </header>
          <main className="container mx-auto px-4 py-8">
            {children}
          </main>
          <footer className="bg-gray-800 text-white py-6">
            <div className="container mx-auto px-4 text-center">
              <p>© 2024 AutoPlaza. Все права защищены.</p>
            </div>
          </footer>
        </div>
      </body>
    </html>
  )
}