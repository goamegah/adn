from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from agent import AgentExpert

app = Flask(__name__)
CORS(app)

# Configuration
PROJECT_ID = "ai-diagnostic-navigator-475316"
PORT = int(os.environ.get("PORT", 8080))

# Initialize the expert agent
print("🔧 Initializing Agent 3...")
agent3 = AgentExpert()
print("✅ Agent 3 initialized")

@app.route("/", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Agent 3 - ADN Expert/Validator",
        "version": "1.0",
        "project": PROJECT_ID
    }), 200

@app.route("/validate", methods=["POST"])
def validate():
    """
    Complete validation with differential diagnoses, 
    guideline validation, and action plan
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "No JSON data provided"
            }), 400
        
        # Validate with Expert Agent (Agent 3)
        result = agent3.analyser_complet(data)
        
        return jsonify({
            "status": "success",
            "data": result
        }), 200
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route("/diagnoses", methods=["POST"])
def diagnoses():
    """
    Generate differential diagnoses only
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "No JSON data provided"
            }), 400
        
        # Generate differential diagnoses using Agent 3
        diagnostics = agent3.phase_diagnostics_differentiels(data)
        
        return jsonify({
            "status": "success",
            "data": {
                "differential_diagnoses": diagnostics
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route("/validate-alerts", methods=["POST"])
def validate_alerts():
    """
    Validate alerts against medical guidelines
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "No JSON data provided"
            }), 400
        
        # Extract alerts and patient data
        alertes = data.get("critical_alerts", [])
        patient_data = data.get("raw_patient_data", {})
        
        if not alertes:
            return jsonify({
                "error": "No alerts provided in critical_alerts field"
            }), 400
        
        # Validate alerts against medical guidelines
        validated = agent3.phase_validation_guidelines(alertes, patient_data)
        
        return jsonify({
            "status": "success",
            "data": {
                "validated_alerts": validated
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route("/risk-scores", methods=["POST"])
def risk_scores():
    """
    Calculate risk scores for given diagnoses
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "No JSON data provided"
            }), 400
        
        # Extract diagnoses and patient data
        diagnostics = data.get("differential_diagnoses", [])
        patient_data = data.get("raw_patient_data", {})
        
        if not diagnostics:
            return jsonify({
                "error": "No diagnoses provided in differential_diagnoses field"
            }), 400
        
        # Calculate clinical risk scores
        scores = agent3.phase_scores_risque(diagnostics, patient_data)
        
        return jsonify({
            "status": "success",
            "data": {
                "risk_scores": scores
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route("/action-plan", methods=["POST"])
def action_plan():
    """
    Generate prioritized action plan based on validated data
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "No JSON data provided"
            }), 400
        
        # Generate evidence-based action plan
        plan = agent3.phase_plan_action(data)
        
        return jsonify({
            "status": "success",
            "data": {
                "action_plan": plan
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route("/info", methods=["GET"])
def info():
    """Agent information and capabilities endpoint"""
    return jsonify({
        "agent_name": "Agent 3 - Expert/Validator",
        "description": "Expert medical agent that validates alerts, generates differential diagnoses, and creates evidence-based action plans",
        "version": "1.0",
        "project_id": PROJECT_ID,
        "capabilities": [
            "Differential diagnosis generation",
            "Guideline-based validation",
            "Risk score calculation (APACHE II, SOFA, qSOFA, GRACE, TIMI, etc.)",
            "Prioritized action plan generation",
            "Evidence synthesis"
        ],
        "endpoints": {
            "/": "Health check",
            "/validate": "Complete validation (all phases)",
            "/diagnoses": "Differential diagnoses only",
            "/validate-alerts": "Validate alerts against guidelines",
            "/risk-scores": "Calculate clinical risk scores",
            "/action-plan": "Generate action plan",
            "/info": "Agent information"
        },
        "input_format": {
            "/validate": "Output from Agent 2 (Synthesizer)",
            "/diagnoses": "Same as /validate",
            "/validate-alerts": {
                "critical_alerts": "List of alerts",
                "raw_patient_data": "Patient data"
            },
            "/risk-scores": {
                "differential_diagnoses": "List of diagnoses",
                "raw_patient_data": "Patient data"
            },
            "/action-plan": "Output from Agent 2"
        }
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)