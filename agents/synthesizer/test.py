"""
Simple test of Agent 2 deployed on Cloud Run
"""

import requests
import json

# URL of your deployed service
SERVICE_URL = "https://agent2-synthetiseur-329720391631.us-central1.run.app"

# Simple test patient data
patient_test = {
    "patient_normalized": {
        "id": "TEST-001",
        "age": 70,
        "sex": "female",
        "admission": {
            "type": "EMERGENCY",
            "chief_complaint": "SEPSIS"
        },
        "vitals_current": {
            "temperature": 38.5,
            "heart_rate": 110
        },
        "labs": [
            {"name": "WBC", "value": 18000, "flag": "HIGH"},
            {"name": "Lactate", "value": 3.2, "flag": "HIGH"}
        ],
        "cultures": [
            {
                "status": "POSITIVE",
                "organism": "MRSA",
                "resulted": "2024-10-14T14:30:00"
            }
        ],
        "medications_current": [
            {"name": "Ceftriaxone", "dose": "2g"}
        ]
    }
}

def test_health():
    """Test 1: Health check"""
    print("🔍 Test 1: Health Check")
    response = requests.get(f"{SERVICE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")

def test_analyze():
    """Test 2: Patient analysis"""
    print("🔍 Test 2: Patient Analysis")
    response = requests.post(
        f"{SERVICE_URL}/analyze",
        json=patient_test,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        data = result.get("data", {})
        
        # Display summary
        synthesis = data.get("synthesis", {})
        alerts = data.get("critical_alerts", [])
        
        print("\n✅ Analysis successful!")
        print(f"Severity: {synthesis.get('severity')}")
        print(f"Problems: {', '.join(synthesis.get('key_problems', []))}")
        print(f"Critical alerts: {len(alerts)}")
        print(f"Complete JSON:\n{json.dumps(data, indent=2)}")
        
        if alerts:
            print("\n🚨 First alert:")
            print(f"  Type: {alerts[0].get('type')}")
            print(f"  Action: {alerts[0].get('action_required')}")
    else:
        print(f"❌ Error: {response.text}")

if __name__ == "__main__":
    print("="*50)
    print("🧪 AGENT 2 TEST - CLOUD RUN")
    print("="*50)
    print()
    
    try:
        test_health()
        print()
        test_analyze()
        print()
        print("="*50)
        print("✅ Tests completed")
        print("="*50)
    except Exception as e:
        print(f"❌ Error: {e}")