import { Suspense } from 'react'
import type { Metadata } from 'next'
import { Inter, Montserrat, JetBrains_Mono } from 'next/font/google'
import './globals.css'
import { Providers } from './providers'
import { Navigation } from '@/components/layout/Navigation'
import { Footer } from '@/components/layout/Footer'

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-body',
})

const montserrat = Montserrat({
  subsets: ['latin'],
  weight: ['500', '600', '700', '800'],
  display: 'swap',
  variable: '--font-heading',
})

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  weight: ['400', '500'],
  display: 'swap',
  variable: '--font-mono',
})

export const metadata: Metadata = {
  title: 'ApexView | Formula 1 Data Analytics',
  description:
    'Advanced Formula 1 telemetry and race analysis platform covering ' +
    'qualifying, race strategy, practice performance, and circuit intelligence.',
  openGraph: {
    title: 'ApexView | Formula 1 Data Analytics',
    description:
      'Formula 1 data analytics platform — race strategy, qualifying analysis, ' +
      'practice performance, and circuit intelligence for the 2025 season.',
    type: 'website',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={`${inter.variable} ${montserrat.variable} ${jetbrainsMono.variable}`}>
      <body className={`${inter.className} flex min-h-screen flex-col bg-f1dark text-white antialiased`}>
        <Providers>
          <Suspense fallback={
            <nav className="sticky top-0 z-50 border-b border-f1gray bg-f1dark/95 h-16" />
          }>
            <Navigation />
          </Suspense>
          <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-8 sm:px-6 lg:px-8">
          {children}
        </main>
          <Footer />
        </Providers>
      </body>
    </html>
  )
}

