import type { Metadata } from 'next'
import './globals.css'
import { Providers } from './providers'

export const metadata: Metadata = {
  title: 'F1 Engineering App',
  description: 'Advanced Formula 1 telemetry and race analysis platform',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-f1dark text-white antialiased">
        <Providers>
        <nav className="border-b border-f1gray bg-f1dark/95 backdrop-blur supports-[backdrop-filter]:bg-f1dark/60">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="flex h-16 items-center justify-between">
              <div className="flex items-center">
                <a href="/" className="text-2xl font-bold text-f1red">
                  F1 Engineering
                </a>
              </div>
              <div className="flex space-x-4">
                <a href="/" className="rounded-md px-3 py-2 text-sm font-medium hover:bg-f1gray">
                  Home
                </a>
                <a href="/qualifying" className="rounded-md px-3 py-2 text-sm font-medium hover:bg-f1gray">
                  Qualifying
                </a>
                <a href="/race" className="rounded-md px-3 py-2 text-sm font-medium hover:bg-f1gray">
                  Race
                </a>
                <a href="/practice" className="rounded-md px-3 py-2 text-sm font-medium hover:bg-f1gray">
                  Practice
                </a>
              </div>
            </div>
          </div>
        </nav>
        <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          {children}
        </main>
        </Providers>
      </body>
    </html>
  )
}

