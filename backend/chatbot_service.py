import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def process_chat(message: str, history: list = []):
    """
    Procesa una pregunta del usuario usando Groq con el historial proporcionado.
    """
    messages = []
    
    # Agregar historial si existe
    for h in history:
        role = "user" if h.get("sender") == "user" else "assistant"
        messages.append({"role": role, "content": h.get("text")})
    
    # Agregar mensaje actual
    messages.append({"role": "user", "content": message})
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.2,
            max_tokens=1024,
            top_p=1,
            stream=False,
            stop=None,
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Error en el servicio de chat: {str(e)}"
