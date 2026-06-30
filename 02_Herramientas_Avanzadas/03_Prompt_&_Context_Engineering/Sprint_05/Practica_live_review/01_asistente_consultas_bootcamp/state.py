"""state.py — Memoria de la sesión de chat (Fase 2).

Qué hace este módulo:
  - Guarda el perfil del alumno y el historial de mensajes entre turnos.
  - `inicializar_estado()` crea el dict de sesión (ya implementada).
  - `append_user` / `append_model` añaden turnos; `ultimos_n` recorta el historial.

Para qué sirve:
  - Que el asistente recuerde el nombre y el contexto en preguntas siguientes.
  - Alimentar `build_historial_block()` en prompts.py con los últimos mensajes.

Funciones a implementar:
  - `append_user`, `append_model`, `ultimos_n` — ver README FASE 2, Tarea 3.
  - `guardar_clasificacion` — opcional (experimentos).
"""


def inicializar_estado(user_profile: dict | None = None) -> dict:
    """Crea el dict de sesión. Ya está implementada; no necesitas modificarla."""
    return {
        "user_profile": user_profile or {},
        "messages": [],
        "consultas_clasificadas": [],
    }


def append_user(state: dict, texto: str) -> None:
    state["messages"].append({"role": "user", "text": texto.strip()})


def append_model(state: dict, texto: str) -> None:
    state["messages"].append({"role": "model", "text": texto.strip()})


def ultimos_n(state: dict, n: int) -> list[dict]:
    if n <= 0:
        return []
    return state["messages"][-n:]


def guardar_clasificacion(state: dict, consulta: dict, clasificacion: dict) -> None:
    state["consultas_clasificadas"].append({
        "consulta": consulta,
        "clasificacion": clasificacion,
    })
