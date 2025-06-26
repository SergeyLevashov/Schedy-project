from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response

router = APIRouter(prefix="/api/voice", tags=["Voice"])

VOICE_FILE = Path(__file__).resolve().parent.parent / "voice.txt"

@router.post("/save", status_code=204)
async def save_voice(payload: dict) -> Response:
    """
    Принимает JSON {"text": "<распознанный_текст>"} и добавляет его в voice.txt.
    Между сообщениями остаётся пустая строка.
    """
    text: str = payload.get("text", "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is empty")

    # .parent.parent => корень проекта рядом с voice.txt
    with VOICE_FILE.open("a", encoding="utf-8") as f:
        f.write(text + "\n\n")       # пустая строка-разделитель

    # 204 No Content — фронт ничего не ждёт
    return Response(status_code=status.HTTP_204_NO_CONTENT)