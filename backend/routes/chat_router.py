from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from models import ChatRequest, AIAskRequest
from services.chat_service import ChatService

router = APIRouter(tags=["chat"])
service = ChatService()


@router.post("/chat")
def chat_endpoint(request: ChatRequest):
    try:
        answer = service.basic_chat(request.message, request.history)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai/ask")
async def ai_ask(request: AIAskRequest):
    try:
        result = await service.ask_ai(request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ai-panel", response_class=HTMLResponse)
async def ai_panel_page():
    try:
        with open("ai_panel.html", "r") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="AI panel not found")