"""logic.py — Orquestación: validar, clasificar y responder.

Qué hace este módulo:
  - Fase 1: `clasificar_consulta()` — validar → prompt → Gemini → parsear JSON.
  - Fase 2: `responder_chat()` — prompt con contexto → Gemini → actualizar state.
  - Helpers `respuesta_ok()` y `respuesta_error()` (ya implementados).

Para qué sirve:
  - Es el «cerebro» que conecta validators, prompts, context, state y gemini_client.
  - `main.py` solo llama funciones de aquí; no duplica reglas.

Reglas importantes:
  - No uses `print` en este archivo (la salida la hace main.py).
  - Importa `llamar_gemini_json` / `safe_generate_texto` dentro de las funciones.

Funciones a implementar:
  - Fase 1: `parsear_clasificacion`, `clasificar_consulta`
  - Fase 2: `demo_seleccion_faq`, `responder_chat`
"""

import json
import time
from pathlib import Path

from validators import validar_consulta
from config import CATEGORIAS, PRIORIDADES


def respuesta_ok(mensaje: str, data: dict | None = None) -> dict:
    return {"status": "ok", "mensaje": mensaje, "data": data or {}}


def respuesta_error(mensaje: str, errores: list[str]) -> dict:
    return {"status": "error", "mensaje": mensaje, "data": {"errores": errores}}


def parsear_clasificacion(raw: str) -> dict:
    """json.loads + whitelist de category y priority."""
    try:
        datos = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON invalido: {e}") from e

    for clave in ("category", "priority", "summary"):
        if clave not in datos:
            raise ValueError(f"Falta la clave obligatoria: '{clave}'")

    if datos["category"] not in CATEGORIAS:
        raise ValueError(
            f"Categoria '{datos['category']}' no valida. "
            f"Opciones: {sorted(CATEGORIAS)}"
        )
    if datos["priority"] not in PRIORIDADES:
        raise ValueError(
            f"Prioridad '{datos['priority']}' no valida. "
            f"Opciones: {sorted(PRIORIDADES)}"
        )

    return {
        "category": datos["category"],
        "priority": datos["priority"],
        "summary": str(datos["summary"]),
    }


def clasificar_consulta(datos: dict) -> dict:
    """Orquesta validar -> prompt -> Gemini -> parsear."""
    from gemini_client import llamar_gemini_json
    from prompts import build_clasificacion_prompt

    errores = validar_consulta(datos)
    if errores:
        return respuesta_error("Consulta invalida", errores)

    prompt = build_clasificacion_prompt(datos["mensaje"])
    try:
        raw = llamar_gemini_json(prompt)
    except Exception as e:
        return respuesta_error("Error al llamar a Gemini", [str(e)])

    try:
        clasificacion = parsear_clasificacion(raw)
    except ValueError as e:
        return respuesta_error("Respuesta inesperada del modelo", [str(e)])

    return respuesta_ok("Consulta clasificada correctamente", clasificacion)


def demo_seleccion_faq(faq_path: Path, consulta: str) -> dict:
    """Prueba seleccionar_faq sin chat completo."""
    from context import cargar_faq, seleccionar_faq

    faq = cargar_faq(faq_path)
    entradas = seleccionar_faq(faq, consulta, max_entradas=1)

    if not entradas:
        return respuesta_ok("Sin coincidencias en el FAQ", {"topic_id": None, "entry": None})

    entrada = entradas[0]
    return respuesta_ok(
        "Entrada FAQ encontrada",
        {
            "topic_id": entrada.get("id", entrada.get("pregunta", "")[:40]),
            "entry": entrada,
        },
    )


def responder_chat(
    state: dict,
    pregunta: str,
    faq_entries: list[dict],
) -> dict:
    """Prompt con perfil, FAQ filtrado e historial -> Gemini -> actualiza state."""
    from gemini_client import safe_generate_texto
    from prompts import build_chat_prompt
    from state import append_user, append_model, ultimos_n
    from config import WINDOW

    prompt = build_chat_prompt(
        pregunta=pregunta,
        profile=state.get("user_profile", {}),
        faq_entries=faq_entries,
        recent_messages=ultimos_n(state, WINDOW),
    )

    inicio = time.monotonic()
    try:
        respuesta, tokens = safe_generate_texto(prompt)
    except Exception as e:
        return respuesta_error("Error al llamar a Gemini", [str(e)])
    elapsed_ms = round((time.monotonic() - inicio) * 1000)

    append_user(state, pregunta)
    append_model(state, respuesta)

    return respuesta_ok(
        "Respuesta generada",
        {
            "respuesta": respuesta,
            "metricas": {
                "elapsed_ms": elapsed_ms,
                "tokens": tokens,
            },
        },
    )
