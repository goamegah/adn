#!/usr/bin/env python3
"""
Installation Simple - Vertex AI Agent Engine
=============================================
Crée un Agent Engine basique pour ADN (sans config avancée).
"""

import vertexai

PROJECT_ID = "ai-diagnostic-navigator-475316"
LOCATION = "us-east4"

print()
print("🚀 Création Agent Engine pour ADN")
print("=" * 60)
print()

try:
    print("🔧 Connexion à Vertex AI...")
    client = vertexai.Client(
        project=PROJECT_ID,
        location=LOCATION
    )
    print("✅ Connecté")
    print()
    
    print("🏗️ Création de l'Agent Engine...")
    print("   (Environ 5 secondes)")
    
    # Création basique (configuration par défaut)
    agent_engine = client.agent_engines.create()
    
    # Récupérer l'ID
    agent_engine_id = agent_engine.api_resource.name.split("/")[-1]
    
    print()
    print("✅ Agent Engine créé avec succès!")
    print()
    print("=" * 60)
    print("📝 AGENT ENGINE ID")
    print("=" * 60)
    print()
    print(f"   {agent_engine_id}")
    print()
    print("=" * 60)
    print("🎯 PROCHAINES ÉTAPES")
    print("=" * 60)
    print()
    print("1️⃣ Exporter la variable:")
    print()
    print(f"   export GOOGLE_CLOUD_AGENT_ENGINE_ID={agent_engine_id}")
    print()
    print("2️⃣ Ajouter au .env:")
    print()
    print(f"   echo 'GOOGLE_CLOUD_AGENT_ENGINE_ID={agent_engine_id}' >> .env")
    print()
    print("3️⃣ Tester le diagnostic:")
    print()
    print("   python3 scripts/diagnostic_memory.py")
    print()
    print("4️⃣ Relancer adk web avec mémoire:")
    print()
    print(f"   adk web agents/clinical_agent --memory_service_uri=agentengine://{agent_engine_id}")
    print()
    print("=" * 60)
    print()

except Exception as e:
    print()
    print(f"❌ Erreur: {e}")
    print()
    print("💡 Solutions:")
    print()
    print("1. Vérifier l'authentification:")
    print("   gcloud auth application-default login")
    print()
    print("2. Activer l'API Vertex AI:")
    print("   gcloud services enable aiplatform.googleapis.com")
    print()
    print("3. Vérifier les permissions:")
    print("   gcloud projects get-iam-policy ai-diagnostic-navigator-475316")
    print()
    exit(1)