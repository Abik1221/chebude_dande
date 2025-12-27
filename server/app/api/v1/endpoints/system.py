from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database import get_db
from app.services.logging_service import logging_service
from app.models.job import Job
from app.models.system import SystemLog
from sqlalchemy import func


router = APIRouter()


@router.get("/logs", summary="Get system logs")
async def get_system_logs(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Retrieve recent system logs from the database
    """
    logs = logging_service.get_logs(db, limit, offset)
    return [
        {
            "id": log.id,
            "level": log.level,
            "module": log.module,
            "message": log.message,
            "timestamp": log.timestamp
        } for log in logs
    ]


@router.get("/stats", summary="Get system statistics")
async def get_system_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Retrieve aggregate statistics about the system
    """
    try:
        # Get total jobs
        total_jobs = db.query(Job).count()
        
        # Get success rate
        completed_jobs = db.query(Job).filter(Job.status == "COMPLETED").count()
        success_rate = (completed_jobs / total_jobs * 100) if total_jobs > 0 else 100
        
        # Compute jobs (ongoing or all) - Dashboard uses jobs.length
        
        # Simplified metrics for the dashboard summary
        return {
            "total_jobs": total_jobs,
            "completed_jobs": completed_jobs,
            "success_rate": f"{round(success_rate)}%",
            "network_uptime": "99.99%",  # Simulated for now
            "stream_latency": "0.8ms"    # Simulated for now
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
