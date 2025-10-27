from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from agent import AgentSynthetiseur

app = Flask(__name__)
CORS(app)

# Configuration
PROJECT_ID = "ai-diagnostic-navigator-475316"
PORT = int(os.environ.get("PORT", 8080))

# Initialize the agent
print("🔧 Initializing Agent 2...")
agent2 = AgentSynthetiseur()
print("✅ Agent 2 initialized")

@app.route("/", methods=["GET"])
def health():
    """Health check"""
    return jsonify({
        "status": "healthy",
        "service": "Agent 2 - ADN Synthesizer/Critic",
        "version": "1.0",
        "project": PROJECT_ID
    }), 200

@app.route("/analyze", methods=["POST"])
def analyze():
    """Complete patient analysis"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "No JSON data provided"
            }), 400
        
        # Analyze with Agent 2
        result = agent2.analyser_patient(data)
        
        return jsonify({
            "status": "success",
            "data": result
        }), 200
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route("/info", methods=["GET"])
def info():
    """Agent information"""
    return jsonify({
        "agent_name": "Agent 2 - Synthesizer/Critic",
        "description": "Synthesizes and criticizes patient data",
        "version": "1.0",
        "project_id": PROJECT_ID,
        "endpoints": {
            "/": "Health check",
            "/analyze": "Complete analysis",
            "/info": "Information"
        }
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)