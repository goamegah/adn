# app/main.py
import os
import logging
from typing import Optional
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import StreamingResponse
import asyncio
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
import google.auth
import os
from dotenv import load_dotenv


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_REGION = os.getenv("GCP_REGION", "europe-west1")
MODEL_NAME = "gemini-2.0-flash"
vertexai.init(project=GCP_PROJECT_ID, location=GCP_REGION)


app = FastAPI(
    title="AI Agent API",
    description="Serverless AI Agent using Vertex AI Gemini",
    version="1.0.0"
)

model = GenerativeModel(MODEL_NAME)

generation_config = GenerationConfig(
    temperature=0.7,
    max_output_tokens=2048,
    top_p=0.9,
    top_k=40,
)

@app.get("/")
async def root():
    return {
        "message": "Welcome to the AI Agent API",
        "description": "Serverless AI Agent powered by Vertex AI Gemini",
        "project": GCP_PROJECT_ID,
        "region": GCP_REGION,
        "endpoints": {
            "/": "This welcome message",
            "/health": "Health check endpoint",
            "/chat": "Chat with AI agent (query parameter: prompt)",
            "/docs": "API documentation (Swagger UI)",
            "/redoc": "API documentation (ReDoc)"
        }
    }

@app.get("/health")
async def health_check():
    try:
        credentials, project = google.auth.default()
        return {
            "status": "healthy",
            "project": GCP_PROJECT_ID,
            "region": GCP_REGION,
            "service": "ai-agent-api"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

async def generate_stream(prompt: str):
    response_stream = model.generate_content(
        prompt,
        generation_config=generation_config,
        stream=True
    )
    for chunk in response_stream:
        yield chunk.text
        await asyncio.sleep(0.01)

@app.get("/chat")
async def chat(
    prompt: Optional[str] = Query(
        None,
        description="The prompt to send to the AI agent",
        min_length=1,
        max_length=4000
    )
):
    if not prompt:
        raise HTTPException(
            status_code=400,
            detail="Prompt parameter is required"
        )
    
    logger.info(f"Received chat request with prompt length: {len(prompt)}")
    

    return StreamingResponse(
        generate_stream(prompt),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            }
        )

@app.get("/chat/simple")
async def chat_simple(
    prompt: Optional[str] = Query(
        None,
        description="The prompt to send to the AI agent",
        min_length=1,
        max_length=4000
    )
):
    if not prompt:
        raise HTTPException(
            status_code=400,
            detail="Prompt parameter is required"
        )
    
    logger.info(f"Received simple chat request with prompt length: {len(prompt)}")

    response = model.generate_content(
        prompt,
        generation_config=generation_config
    )
    
    return {
        "prompt": prompt,
        "response": response.text,
        "project": GCP_PROJECT_ID,
        "model": MODEL_NAME
    }
