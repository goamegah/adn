/** @type {import('next').NextConfig} */
const nextConfig = {
  // Configuration pour Cloud Run
  output: 'standalone',
  
  // Désactiver le strict mode si nécessaire
  reactStrictMode: true,
  
  // Configuration des images si besoin
  images: {
    unoptimized: true, // Pour éviter les problèmes avec Cloud Run
  },

  // Variables d'environnement publiques
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'https://adn-app-759263279097.europe-west1.run.app',
  },

  // Optimisations pour Cloud Run
  compress: true,
  poweredByHeader: false,
}

module.exports = nextConfig