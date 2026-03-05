import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
    title: 'Shadow AI Detector — Dashboard',
    description: 'Privacy-first AI usage monitoring for organizations',
}

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <html lang="en" className="dark">
            <body>{children}</body>
        </html>
    )
}
