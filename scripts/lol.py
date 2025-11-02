#!/usr/bin/env python3
"""
Diagnostic de la Mémoire ADN
=============================
Vérifie pourquoi l'agent ne peut pas accéder aux analyses passées.
"""

import os
import asyncio
from google.adk.sessions import VertexAiSessionService
from google.adk.memory import VertexAiMemoryBankService
import vertexai

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "ai-diagnostic-navigator-475316")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-east4")
AGENT_ENGINE_ID = os.getenv("GOOGLE_CLOUD_AGENT_ENGINE_ID")

async def diagnostic():
    print("🔍 DIAGNOSTIC DE LA MÉMOIRE ADN")
    print("=" * 70)
    print()
    
    # 1. Vérifier la configuration
    print("📋 Configuration:")
    print(f"   Project: {PROJECT_ID}")
    print(f"   Location: {LOCATION}")
    print(f"   Agent Engine ID: {AGENT_ENGINE_ID}")
    print()
    
    if not AGENT_ENGINE_ID:
        print("❌ GOOGLE_CLOUD_AGENT_ENGINE_ID non défini!")
        print("   C'est pour ça que la mémoire ne fonctionne pas.")
        print()
        print("💡 Solution:")
        print("   1. Créer un Agent Engine: python installer_agent_engine.py")
        print("   2. export GOOGLE_CLOUD_AGENT_ENGINE_ID=<id>")
        return
    
    # 2. Initialiser les services
    print("🔧 Initialisation des services...")
    try:
        session_service = VertexAiSessionService(
            project=PROJECT_ID,
            location=LOCATION
        )
        
        memory_service = VertexAiMemoryBankService(
            project=PROJECT_ID,
            location=LOCATION,
            agent_engine_id=AGENT_ENGINE_ID
        )
        print("✅ Services initialisés")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return
    
    print()
    
    # 3. Lister les sessions existantes
    print("📂 Sessions existantes:")
    try:
        # Récupérer l'ID de session depuis l'image
        session_id = "7938f53e-eacd-47a4-8a88-3a6d64a9e6db"
        
        session = await session_service.get_session(
            app_name="clinical_agent",  # ou le nom de votre app
            user_id="default",  # ou votre user_id
            session_id=session_id
        )
        
        print(f"✅ Session trouvée: {session_id}")
        print(f"   Événements: {len(session.events) if hasattr(session, 'events') else 0}")
        print(f"   State keys: {list(session.state.keys()) if hasattr(session, 'state') else []}")
        
        # Vérifier si les données patient sont dans le state
        if "adn:pipeline_result" in session.state:
            print("   ✅ Résultats pipeline trouvés dans le state")
            import json
            results = json.loads(session.state["adn:pipeline_result"])
            print(f"      Status: {results.get('pipeline_status')}")
        else:
            print("   ❌ Pas de résultats pipeline dans le state")
        
    except Exception as e:
        print(f"⚠️ Impossible de récupérer la session: {e}")
    
    print()
    
    # 4. Vérifier Memory Bank
    print("🧠 Vérification Memory Bank:")
    try:
        # Rechercher "patient 10006"
        search_result = await memory_service.search_memory(
            app_name="clinical_agent",
            user_id="default",
            query="patient 10006"
        )
        
        if search_result and hasattr(search_result, 'memories') and search_result.memories:
            print(f"✅ {len(search_result.memories)} mémoire(s) trouvée(s)")
            for i, memory in enumerate(search_result.memories[:3], 1):
                print(f"\n   🧠 Mémoire {i}:")
                if hasattr(memory, 'content'):
                    content = memory.content
                    if hasattr(content, 'parts') and content.parts:
                        text = content.parts[0].text
                        print(f"      {text[:150]}...")
                print(f"      Scope: {getattr(memory, 'scope', 'N/A')}")
                print(f"      Créé: {getattr(memory, 'create_time', 'N/A')}")
        else:
            print("❌ AUCUNE mémoire trouvée dans Memory Bank")
            print()
            print("🔎 CAUSE PROBABLE:")
            print("   1. La session n'a pas été sauvegardée en Memory Bank")
            print("   2. Memory Bank n'a pas encore extrait les infos (peut prendre 2-5 min)")
            print("   3. Le callback save_pipeline_final_results n'a pas été appelé")
            print("   4. L'agent_engine_id est incorrect")
            print()
            print("💡 SOLUTION:")
            print("   Vérifiez les logs Cloud Run pour voir si on trouve:")
            print("   '🧠 Session xxx sauvegardée en mémoire longue'")
            print()
            print("   gcloud run services logs read clinical-pipeline-service \\")
            print("     --project=$GOOGLE_CLOUD_PROJECT \\")
            print("     --region=$GOOGLE_CLOUD_LOCATION \\")
            print("     --limit=100 | grep 'mémoire longue'")
    
    except Exception as e:
        print(f"❌ Erreur lors de la recherche: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # 5. Vérifier si le callback est bien configuré
    print("🔍 Vérification du code agent:")
    try:
        with open("agents/clinical_agent/agent.py", "r") as f:
            content = f.read()
            
        checks = {
            "VertexAiMemoryBankService importé": "VertexAiMemoryBankService" in content,
            "save_pipeline_final_results existe": "save_pipeline_final_results" in content,
            "add_session_to_memory appelé": "add_session_to_memory" in content,
            "PreloadMemoryTool utilisé": "PreloadMemoryTool" in content,
        }
        
        all_ok = True
        for check, result in checks.items():
            status = "✅" if result else "❌"
            print(f"   {status} {check}")
            if not result:
                all_ok = False
        
        if not all_ok:
            print()
            print("❌ PROBLÈME DÉTECTÉ dans agent.py")
            print("💡 Solution: Utilisez agent_with_memory.py")
            print("   cp agent_with_memory.py agents/clinical_agent/agent.py")
    
    except FileNotFoundError:
        print("   ⚠️ Fichier agent.py non trouvé")
    
    print()
    print("=" * 70)
    
    # 6. Diagnostic final
    print()
    print("📊 DIAGNOSTIC FINAL:")
    print()
    print("Si Memory Bank est vide, c'est normal si:")
    print("   • L'analyse a été faite il y a < 5 minutes (extraction en cours)")
    print("   • Le callback n'a pas été appelé (vérifier logs)")
    print("   • L'agent déployé n'utilise pas agent_with_memory.py")
    print()
    print("Si vous voyez '❌ AUCUNE mémoire trouvée', faites:")
    print("   1. Vérifier que agent_with_memory.py est déployé")
    print("   2. Faire une nouvelle analyse complète")
    print("   3. Attendre 5 minutes")
    print("   4. Relancer ce diagnostic")
    print()


if __name__ == "__main__":
    asyncio.run(diagnostic())