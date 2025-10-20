/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  
  // Désactiver le timeout pour les API routes
  experimental: {
    proxyTimeout: 300000, // 5 minutes en millisecondes
  },
  
  // Permet les requêtes API vers le backend FastAPI
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8000/api/:path*',
      },
    ]
  },
}

module.exports = nextConfig