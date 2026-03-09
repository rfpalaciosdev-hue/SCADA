def build_industrial_prompt(question: str, context: dict | None) -> str:
    """
    Construye el prompt industrial estructurado
    para el asistente SCADA.
    """

    base_prompt = (
        "You are an industrial SCADA assistant.\n"
        "Rules:\n"
        "- Use only provided data.\n"
        "- Do not invent technical details.\n"
        "- If information is missing, say 'Data not available'.\n"
        "- Keep answers concise and operational.\n\n"
    )

    if not context or "error" in context:
        return (
            base_prompt
            + "CONTEXT NOT FOUND OR TAG NOT RESOLVED.\n\n"
            + f"User Question: {question}\n"
        )

    path = context.get("path", "")
    path_parts = path.split("/")

    metadata = context.get("metadata", {})
    current = context.get("current", {})
    stats = context.get("stats_24h", {})
    active_alarms = context.get("active_alarms", [])

    prompt = base_prompt

    prompt += f"Sensor Path: {path}\n"
    prompt += f"Area: {path_parts[1] if len(path_parts) > 1 else 'N/A'}\n"
    prompt += f"Equipment: {path_parts[2] if len(path_parts) > 2 else 'N/A'}\n"
    prompt += f"Sensor: {path_parts[-1] if path_parts else 'N/A'}\n"

    prompt += f"Unit: {current.get('u', 'N/A')}\n"
    prompt += f"Description: {metadata.get('description') or 'N/A'}\n"
    prompt += f"Process Role: {metadata.get('process_role') or 'N/A'}\n"
    prompt += f"Physical Location: {metadata.get('location') or 'N/A'}\n"
    prompt += f"Related System: {metadata.get('system') or 'N/A'}\n"
    prompt += f"Failure Impact: {metadata.get('failure_impact') or 'N/A'}\n"

    normal_range = metadata.get("normal_range", (None, None))
    critical_range = metadata.get("critical_range", (None, None))

    prompt += "Operational Ranges:\n"
    prompt += f"Normal Range: {normal_range[0]} - {normal_range[1]}\n"
    prompt += f"Critical Range: {critical_range[0]} - {critical_range[1]}\n"

    prompt += "Current Status:\n"
    prompt += f"Current Value: {current.get('v', 0)}\n"
    prompt += f"Alarm Active: {'YES' if active_alarms else 'NO'}\n"

    prompt += f"24h Min: {stats.get('min', 'N/A')}\n"
    prompt += f"24h Max: {stats.get('max', 'N/A')}\n"
    prompt += f"24h Avg: {stats.get('avg', 'N/A')}\n"

    prompt += f"Operating Notes: {metadata.get('notes') or 'N/A'}\n\n"

    prompt += f"User Question: {question}\n"

    return prompt