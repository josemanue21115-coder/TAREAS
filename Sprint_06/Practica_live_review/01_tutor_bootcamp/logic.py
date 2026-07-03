"""logic.py — Orquestación de turnos (Fase 1 arquitectura + Fase 2 seguridad).

Qué hace este módulo:
  - Fase 1: `procesar_turno()` — pipeline con perfiles, FAQ e historial.
  - Fase 2: `procesar_turno_vulnerable()` vs `procesar_turno_seguro()`.

Para qué sirve:
  - Punto único de reglas de negocio; main.py solo imprime resultados.

Qué NO debes hacer aquí:
  - No uses `print()` — devuelve dicts con respuesta_ok/respuesta_error.

Funciones ya implementadas (código dado):
  - `respuesta_ok`, `respuesta_error`, `crear_estado_demo`, `demo_seleccion_faq`
"""

from pathlib import Path
from gemini_client import safe_generate
from config import TEMPERATURE_VULNERABLE
from prompts import build_vulnerable_prompt
from validators import parece_dominio_python, rechazo_fuera_de_dominio, validate_input

from context import cargar_faq, seleccionar_faq
from prompts import build_assistant_prompt
from gemini_client import MetricasLlamada
from state import (
    inicializar_estado,
    ultimos_n,
    append_user,
    append_assistant,
    actualizar_perfil_desde_mensaje,
)


def respuesta_ok(mensaje: str, data: dict | None = None) -> dict:
    """Formato estándar de éxito. Ya implementada."""
    return {"status": "ok", "mensaje": mensaje, "data": data or {}}


def respuesta_error(mensaje: str, errores: list[str]) -> dict:
    """Formato estándar de error. Ya implementada."""
    return {"status": "error", "mensaje": mensaje, "data": {"errores": errores}}


def _metricas_a_dict(m: MetricasLlamada) -> dict:
    return {
        "elapsed_ms": m.elapsed_ms,
        "prompt_tokens": m.prompt_tokens,
        "output_tokens": m.output_tokens,
        "total_tokens": m.total_tokens,
    }


def procesar_turno(
    state: dict,
    user_message: str,
    assistant_config: dict | None = None,
    faq_entries: list[dict] | None = None,
) -> dict:
    # 1. Validar mensaje
    if not user_message or not user_message.strip():
        return respuesta_error(
            "Mensaje vacío",
            ["El mensaje del usuario no puede estar vacío."],
        )

    # --- AGREGAR ESTA LÍNEA DE SEGURIDAD ---
    # Si no nos pasan config, usamos la configuración por defecto de config.py
    if assistant_config is None:
        from config import ASSISTANT_CONFIG_DEFAULT
        assistant_config = ASSISTANT_CONFIG_DEFAULT

    # 2. Historial reciente 
    # MODIFICADO: Usamos .get() buscando la clave real 'max_turnos_historial' de config.py
    # Si por alguna razón no existiera, cae de respaldo a 'ventana_historial' o un valor fijo (6)
    ventana = assistant_config.get("max_turnos_historial", assistant_config.get("ventana_historial", 6))
    
    historial = ultimos_n(
        state,
        ventana,
    )

    # 3. Construir prompt
    prompt = build_assistant_prompt(
        assistant_config=assistant_config,
        user_state=state,
        user_message=user_message,
        extra_context=faq_entries or [],
        recent_messages=historial,
    )

    # 4. Llamar a Gemini
    try:
        respuesta, metricas = safe_generate(
            prompt,
            temperature=assistant_config["temperature"],
        )
    except Exception as e:
        return respuesta_error(
            "Error al llamar a Gemini",
            [str(e)],
        )

    # 5. Actualizar estado SOLO tras éxito
    actualizar_perfil_desde_mensaje(state, user_message)
    append_user(state, user_message)
    append_assistant(state, respuesta)

    # 6. Respuesta estándar
    return respuesta_ok(
        respuesta,
        {
            "perfil_activo": assistant_config["perfil_activo"],
            "metricas": _metricas_a_dict(metricas),
        },
    )


def crear_estado_demo() -> dict:
    """Estado inicial para las demos de Fase 1. Ya implementada; no necesitas modificarla."""
    return inicializar_estado(
        {
            "nombre": "",
            "nivel": "junior",
            "tema_actual": "",
        }
    )


def demo_seleccion_faq(faq_path: Path, consulta: str) -> dict:
    """Muestra qué entrada FAQ se seleccionó. Ya implementada; no necesitas modificarla."""
    faq = cargar_faq(faq_path)
    seleccion = seleccionar_faq(faq, consulta, max_entradas=1)
    if not seleccion:
        return respuesta_error(
            "FAQ sin coincidencias",
            ["Ninguna entrada del FAQ coincide con la consulta."],
        )
    return respuesta_ok(
        "Entrada FAQ seleccionada",
        {"topic_id": seleccion[0].get("topic_id"), "entry": seleccion[0]},
    )


import json


def parsear_respuesta_tutor(raw: str) -> dict:
    """Fase 2 — parsea y valida JSON del modelo (claves obligatorias).

    Ver README Fase 2, Tarea 5.
    """
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Respuesta del modelo no es JSON válido: {e}") from e

    claves_obligatorias = ("in_scope", "category", "answer")
    faltantes = [clave for clave in claves_obligatorias if clave not in obj]
    if faltantes:
        raise ValueError(f"Faltan claves obligatorias en la respuesta: {faltantes}")

    return obj


def procesar_turno_seguro(user_message: str) -> dict:
    """Fase 2 — pipeline seguro con defensa en capas.

    Ver README Fase 2, Tarea 7 (incluye pseudocódigo).
    """
    errores = validate_input(user_message)
    if errores:
        return respuesta_error("Input rechazado", errores)

    if not parece_dominio_python(user_message):
        return respuesta_ok(
            "Fuera de dominio (sin llamar al modelo)",
            {
                "modo": "seguro",
                "respuesta": rechazo_fuera_de_dominio(),
                "json": {
                    "in_scope": False,
                    "category": "out_of_scope",
                    "answer": rechazo_fuera_de_dominio(),
                },
                "metricas": None,
            },
        )

    prompt = build_secure_prompt(user_message)
    try:
        raw, metricas = safe_generate(prompt, json_mode=True)
        obj = parsear_respuesta_tutor(raw)
    except (ValueError, json.JSONDecodeError) as e:
        return respuesta_error("Error generando respuesta segura", [str(e)])

    return respuesta_ok(
        "Respuesta generada (modo seguro)",
        {
            "modo": "seguro",
            "respuesta": obj["answer"],
            "json": obj,
            "metricas": _metricas_a_dict(metricas),
        },
    )


def procesar_turno_vulnerable(user_message: str) -> dict:
    """Fase 2 — pipeline débil para comparativa.

    Ver README Fase 2, Tarea 6.
    """
    if not user_message or not user_message.strip():
        return respuesta_error("Mensaje vacío", ["El mensaje no puede estar vacío."])

    prompt = build_vulnerable_prompt(user_message)
    raw, metricas = safe_generate(prompt, temperature=TEMPERATURE_VULNERABLE)

    return respuesta_ok(
        "Respuesta generada (modo vulnerable)",
        {
            "modo": "vulnerable",
            "respuesta": raw,
            "metricas": _metricas_a_dict(metricas),
        },
    )
