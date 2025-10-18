from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime
from backend.app.db import get_connection

router = APIRouter(prefix="/interventions", tags=["Interventions"])

class InterventionCreate(BaseModel):
    caller_phone: str
    location_address: str | None = None
    urgency_level: int = 3  # 1 = P0, 2 = P1, 3 = P2, 4 = P3
    transcript: str | None = None

@router.post("/create_intervention")
def create_intervention(data: InterventionCreate):
    conn = get_connection()
    cur = conn.cursor()

    try:
        new_id = str(uuid4())
        cur.execute("""
            INSERT INTO emergency_interventions 
            (id, call_datetime, caller_phone, transcript, urgency_level, status, location_address, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            RETURNING id;
        """, (
            new_id,
            datetime.utcnow(),
            data.caller_phone,
            data.transcript,
            data.urgency_level,
            "new",
            data.location_address
        ))
        conn.commit()
        cur.close()
        conn.close()
        return {"message": "✅ Intervention créée avec succès", "id": new_id}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création : {e}")
