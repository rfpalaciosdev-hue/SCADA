import time
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from config import r, get_db_connection
from models import ChatRequest, AIAskRequest
from chatbot_service import process_chat
from scada_nlp import resolve_tag

# Importamos get_sensor_context desde sensors para reutilizarlo
from routes.sensors import get_sensor_context

router = APIRouter(tags=["chat"])


@router.post("/chat")
def chat_endpoint(request: ChatRequest):
    try:
        answer = process_chat(request.message, request.history)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai/ask")
async def ai_ask(request: AIAskRequest):
    start_time = time.time()
    resolved_tag = request.tag

    # Si no hay tag, intentar resolverlo de la pregunta
    if not resolved_tag:
        resolved_tag = resolve_tag(request.question)

    context_data = None
    if resolved_tag:
        context_data = await get_sensor_context(resolved_tag)

    # Constructor de prompt industrial
    prompt = (
        "You are an industrial SCADA assistant.\n"
        "Rules:\n"
        "- Use only provided data.\n"
        "- Do not invent technical details.\n"
        "- If information is missing, say 'Data not available'.\n"
        "- Keep answers concise and operational.\n\n"
    )

    if context_data and "error" not in context_data:
        path_parts = context_data["path"].split("/")
        prompt += f"Sensor Path: {context_data['path']}\n"
        prompt += f"Area: {path_parts[1] if len(path_parts) > 1 else 'N/A'}\n"
        prompt += f"Equipment: {path_parts[2] if len(path_parts) > 2 else 'N/A'}\n"
        prompt += f"Sensor: {path_parts[-1]}\n"
        prompt += f"Unit: {context_data['current'].get('u', 'N/A')}\n"
        prompt += f"Description: {context_data['metadata']['description'] or 'N/A'}\n"
        prompt += f"Process Role: {context_data['metadata']['process_role'] or 'N/A'}\n"
        prompt += f"Physical Location: {context_data['metadata']['location'] or 'N/A'}\n"
        prompt += f"Related System: {context_data['metadata']['system'] or 'N/A'}\n"
        prompt += f"Failure Impact: {context_data['metadata']['failure_impact'] or 'N/A'}\n"
        prompt += "Operational Ranges:\n"
        prompt += f"Normal Range: {context_data['metadata']['normal_range'][0]} - {context_data['metadata']['normal_range'][1]}\n"
        prompt += f"Critical Range: {context_data['metadata']['critical_range'][0]} - {context_data['metadata']['critical_range'][1]}\n"
        prompt += "Current Status:\n"
        prompt += f"Current Value: {context_data['current'].get('v', 0)}\n"
        prompt += f"Alarm Active: {'YES' if context_data['active_alarms'] else 'NO'}\n"
        prompt += f"24h Min: {context_data['stats_24h']['min']}\n"
        prompt += f"24h Max: {context_data['stats_24h']['max']}\n"
        prompt += f"24h Avg: {context_data['stats_24h']['avg']}\n"
        prompt += f"Operating Notes: {context_data['metadata']['notes'] or 'N/A'}\n\n"
    else:
        prompt += "CONTEXT NOT FOUND OR TAG NOT RESOLVED.\n\n"

    prompt += f"User Question: {request.question}\n"

    try:
        response = process_chat(f"{prompt}\nAI Response:", [])
    except Exception as e:
        response = f"Error processing AI: {str(e)}"

    duration = time.time() - start_time

    print(f"--- AI INTERACTION ---")
    print(f"Question: {request.question}")
    print(f"Resolved Tag: {resolved_tag}")
    print(f"Prompt Generated: \n{prompt}")
    print(f"Response: {response}")
    print(f"Duration: {duration:.2f}s")
    print(f"-----------------------")

    return {
        "tag": resolved_tag,
        "prompt": prompt,
        "answer": response,
        "duration": duration,
    }


@router.get("/ai-panel", response_class=HTMLResponse)
async def ai_panel_page():
    with open("ai_panel.html", "r") as f:
        return f.read()
