"""prompts.py — Construcción de textos para enviar a Gemini.

Qué hace este módulo:
  - Ensambla strings (rol + instrucciones + contexto + pregunta).
  - Fase 1: `build_clasificacion_prompt()` para clasificar en JSON.
  - Fase 2: bloques de perfil, FAQ, historial y `build_chat_prompt()`.

Para qué sirve:
  - Separar el diseño del prompt de la lógica y de las llamadas a la API.
  - Aquí solo devuelves texto; no llamas a Gemini.

Funciones a implementar:
  - Fase 1: `build_clasificacion_prompt`
  - Fase 2: `build_perfil_block`, `build_faq_block`, `build_historial_block`, `build_chat_prompt`
"""

import json

ROLE_CLASIFICADOR = (
    "Eres un analista de consultas del bootcamp AI Engineering. "
    "Respondes únicamente con JSON válido según las instrucciones."
)

TASK_CLASIFICAR = """
Tarea: clasifica el mensaje del alumno sobre el bootcamp.

Devuelve EXCLUSIVAMENTE un objeto JSON con estas claves:
- "category": una de academico, tecnico, administrativo, otro
- "priority": una de baja, media, alta
- "summary": resumen en una frase

Sin markdown ni texto fuera del JSON.
"""

PLANTILLA_CHAT = """
Eres un asistente oficial del bootcamp AI Engineering. Respondes con claridad y sin inventar políticas.

{perfil_bloque}

{faq_bloque}

{historial_bloque}

Pregunta actual del alumno:
{pregunta}
"""


# ── Fase 1 ────────────────────────────────────────────────────────────────────

def build_clasificacion_prompt(mensaje: str) -> str:
    return f"{ROLE_CLASIFICADOR}\n\n{TASK_CLASIFICAR}\nMensaje del alumno:\n{mensaje}"


# ── Fase 2 ────────────────────────────────────────────────────────────────────

def build_perfil_block(profile: dict) -> str:
    if not profile:
        return ""
    lineas = "\n".join(f"  {k}: {v}" for k, v in profile.items())
    return f"--- PERFIL DEL ALUMNO ---\n{lineas}\n--- FIN PERFIL ---"


def build_faq_block(faq_entries: list[dict]) -> str:
    if not faq_entries:
        return ""
    lineas = []
    for entrada in faq_entries:
        pregunta = entrada.get("pregunta", entrada.get("question", ""))
        respuesta = entrada.get("respuesta", entrada.get("answer", ""))
        lineas.append(f"  P: {pregunta}\n  R: {respuesta}")
    contenido = "\n\n".join(lineas)
    return f"--- FAQ RELEVANTE ---\n{contenido}\n--- FIN FAQ ---"


def build_historial_block(messages: list[dict]) -> str:
    if not messages:
        return ""
    lineas = "\n".join(
        f"  {m.get('role', 'user')}: {m.get('text', '')}"
        for m in messages
    )
    return f"--- HISTORIAL ---\n{lineas}\n--- FIN HISTORIAL ---"


def build_chat_prompt(
    *,
    pregunta: str,
    profile: dict,
    faq_entries: list[dict],
    recent_messages: list[dict],
) -> str:
    return PLANTILLA_CHAT.format(
        perfil_bloque=build_perfil_block(profile),
        faq_bloque=build_faq_block(faq_entries),
        historial_bloque=build_historial_block(recent_messages),
        pregunta=pregunta,
    )