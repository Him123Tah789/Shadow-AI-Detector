import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
    title: 'ShieldOps — Shadow AI Detector + Breach Monitor',
    description: 'Privacy-first AI usage monitoring for organizations and personal breach monitoring with recovery kit',
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
