TAG_LIMITS = {
    "planta_central/servicios/caldera/temperatura": (150, 180),
    "planta_central/servicios/caldera/presion": (6, 8),
    "planta_central/cocimiento/tanque_01/temperatura": (88, 92),
    "planta_central/cocimiento/tanque_01/presion": (2, 4),
}

def evaluate_tag(tag, value):
    if tag not in TAG_LIMITS:
        return None

    low, high = TAG_LIMITS[tag]

    if value < low:
        return f"⚠️ Valor BAJO (normal {low}-{high}). Posible falla o pérdida de eficiencia."
    elif value > high:
        return f"🚨 Valor ALTO (normal {low}-{high}). Riesgo de daño o activación de alarmas."
    else:
        return f"✅ Valor NORMAL dentro del rango operativo ({low}-{high})."