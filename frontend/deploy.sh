#!/bin/bash

# Script de déploiement du frontend sur Cloud Run

set -e  # Arrêter en cas d'erreur

# Configuration
PROJECT_ID="ai-diagnostic-navigator-475316"  # À REMPLACER
REGION="us-east4"              # Même région que ton backend
SERVICE_NAME="adn-frontend"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Couleurs pour les logs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Déploiement du frontend ADN sur Cloud Run${NC}"
echo ""


# Build de l'image Docker
echo -e "${GREEN}🐳 Build de l'image Docker...${NC}"
docker build -t ${IMAGE_NAME} .

# Push de l'image vers GCR
echo -e "${GREEN}📦 Push de l'image vers Google Container Registry...${NC}"
docker push ${IMAGE_NAME}

# Déploiement sur Cloud Run
echo -e "${GREEN}☁️  Déploiement sur Cloud Run...${NC}"
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0 \
  --set-env-vars "NODE_ENV=production,NEXT_TELEMETRY_DISABLED=1"

# Récupérer l'URL du service
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --platform managed --region ${REGION} --format 'value(status.url)')

echo ""
echo -e "${GREEN}✅ Déploiement réussi!${NC}"
echo ""
echo -e "${GREEN}🌐 URL du service:${NC} ${SERVICE_URL}"
echo ""
echo -e "${YELLOW}📝 Prochaines étapes:${NC}"
echo "  1. Tester l'application: ${SERVICE_URL}"
echo "  2. Configurer un domaine personnalisé (optionnel)"
echo "  3. Configurer les variables d'environnement si nécessaire"
echo ""