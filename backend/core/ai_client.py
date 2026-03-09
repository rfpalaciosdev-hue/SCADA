import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def process_chat(message: str, history: list | None = None):
    """
    Cliente IA (Groq).
    Solo se encarga de hablar con el modelo.
    """
    history = history or []
    messages = []

    for h in history:
        role = "user" if h.get("sender") == "user" else "assistant"
        messages.append({"role": role, "content": h.get("text")})

    messages.append({"role": "user", "content": message})

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.2,
        max_tokens=1024,
        top_p=1,
        stream=False,
    )

    return completion.choices[0].message.content