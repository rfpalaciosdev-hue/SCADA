import time
from core.ai_client import process_chat
from scada_nlp import resolve_tag
from services.sensors_service import SensorsService
from modules.prompt_builder import build_industrial_prompt


class ChatService:

    def __init__(self):
        self.sensor_service = SensorsService()

    def basic_chat(self, message: str, history: list):
        return process_chat(message, history)

    async def ask_ai(self, request):
        start_time = time.time()

        resolved_tag = request.tag or resolve_tag(request.question)

        context_data = None
        if resolved_tag:
            context_data = await self.sensor_service.get_sensor_context(resolved_tag)

        prompt = build_industrial_prompt(
            question=request.question,
            context=context_data
        )

        try:
            response = process_chat(f"{prompt}\nAI Response:", [])
        except Exception as e:
            response = f"Error processing AI: {str(e)}"

        duration = time.time() - start_time

        return {
            "tag": resolved_tag,
            "answer": response,
            "duration": duration,
        }