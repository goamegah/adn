import './globals.css'

export const metadata = {
  title: 'ADN - Agentic Diagnostic Navigator',
  description: 'Système de diagnostic médical assisté par agents IA',
}

export default function RootLayout({ children }) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  )
}
