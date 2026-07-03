"""validators.py — Validación de inputs y dominio (Fase 2).

Qué hace este módulo:
  - Capa 1: `validate_input()` — vacío, longitud, patrones sospechosos.
  - Capa 2: `parece_dominio_python()` — filtro didáctico antes del LLM.

Para qué sirve:
  - Rechazar ataques e inputs inválidos sin gastar tokens en Gemini.

Funciones a implementar (Fase 2):
  - validate_input, parece_dominio_python, rechazo_fuera_de_dominio
"""


"""validators.py — Validación de inputs y dominio (Fase 2)."""

from config import DOMINIO_KEYWORDS, MAX_INPUT_CHARS, PATRONES_SOSPECHOSOS


def validate_input(texto: str) -> list[str]:
    """Fase 2 — devuelve lista de errores (vacía = OK).

    Reglas: vacío, MAX_INPUT_CHARS, PATRONES_SOSPECHOSOS en config.py.

    Ver README Fase 2, Tarea 1.
    """
    errores = []

    if not texto or not texto.strip():
        errores.append("El mensaje está vacío.")
        return errores  # sin más texto que validar, cortamos aquí

    if len(texto) > MAX_INPUT_CHARS:
        errores.append(f"El mensaje supera el límite de {MAX_INPUT_CHARS} caracteres.")

    texto_lower = texto.lower()
    for patron in PATRONES_SOSPECHOSOS:
        if patron in texto_lower:
            errores.append(f"Patrón sospechoso detectado: '{patron}'.")

    return errores


def parece_dominio_python(texto: str) -> bool:
    """Fase 2 — True si el mensaje parece de Python/bootcamp.

    Usa DOMINIO_KEYWORDS de config.py.

    Ver README Fase 2, Tarea 2.
    """
    texto_lower = texto.lower()
    return any(keyword in texto_lower for keyword in DOMINIO_KEYWORDS)


def rechazo_fuera_de_dominio() -> str:
    """Fase 2 — mensaje fijo cuando la pregunta no encaja en el producto.

    Ver README Fase 2, Tarea 2.
    """
    return (
        "Solo puedo ayudarte con temas de Python y del bootcamp "
        "(sintaxis, errores, ejercicios, arquitectura de asistentes). "
        "Esa pregunta está fuera de mi alcance."
    )
