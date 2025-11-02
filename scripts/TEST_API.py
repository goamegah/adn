#!/usr/bin/env python3
"""
Test direct de l'agent ADK déployé sur Cloud Run
"""
import httpx
import json
import asyncio

CLINICAL_AGENT_URL = "https://clinical-pipeline-service-329720391631.us-east4.run.app"

async def test_agent():
    async with httpx.AsyncClient(timeout=120.0) as client:
        print("🔍 Test 1: Liste des apps disponibles")
        try:
            response = await client.get(f"{CLINICAL_AGENT_URL}/list-apps")
            print(f"✅ Status: {response.status_code}")
            print(f"📄 Response: {response.text[:500]}")
        except Exception as e:
            print(f"❌ Erreur: {e}")
        
        print("\n🔍 Test 2: Création de session")
        try:
            response = await client.post(
                f"{CLINICAL_AGENT_URL}/apps/clinical_agent/users/user/sessions",
                json={}
            )
            print(f"✅ Status: {response.status_code}")
            data = response.json()
            print(f"📄 Response: {json.dumps(data, indent=2)}")
            session_id = data.get("id")
            
            if session_id:
                print(f"\n🔍 Test 3: Envoi d'un message")
                response = await client.post(
                    f"{CLINICAL_AGENT_URL}/apps/clinical_agent/users/user/sessions/{session_id}/events",
                    json={"text": "Analyse complète du patient 12548"}
                )
                print(f"✅ Status: {response.status_code}")
                event_data = response.json()
                print(f"📄 Response: {json.dumps(event_data, indent=2)[:1000]}")
                
        except Exception as e:
            print(f"❌ Erreur: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent())