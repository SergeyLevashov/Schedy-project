from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from .utils import auth


router = APIRouter(prefix="/api/tasks", dependencies=[Depends(auth)])

@router.get("/all")
async def get_all_tasks() -> JSONResponse:
    # This is a mock response.
    # In a real application, you would fetch this data from a database.
    tasks = [
        { "id": 1, "name": "First task from server", "time": "10:00 AM" },
        { "id": 2, "name": "Second task from server", "time": "2:00 PM" }
    ]
    return JSONResponse({"tasks": tasks}) 