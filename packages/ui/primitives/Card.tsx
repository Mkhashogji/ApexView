import React from 'react'

interface CardProps {
  children: React.ReactNode
  className?: string
  title?: string
}

export function Card({ children, className = '', title }: CardProps) {
  return (
    <div className={`rounded-lg border border-gray-700 bg-gray-800/50 p-6 ${className}`}>
      {title && <h3 className="mb-4 text-xl font-semibold">{title}</h3>}
      {children}
    </div>
  )
}

