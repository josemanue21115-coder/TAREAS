"""validators.py — Validación de consultas en Python (Fase 1).

Qué hace este módulo:
  - Comprueba nombre, email y mensaje antes de llamar a Gemini.
  - Devuelve una lista de errores (vacía = consulta válida).

Para qué sirve:
  - Ahorrar tokens y evitar llamadas a la API con datos mal formados.
  - Es el primer paso del flujo en `clasificar_consulta()` (logic.py).

Función a implementar:
  - `validar_consulta(datos)` — ver README FASE 1, Tarea 1.
"""

from config import (
    MAX_CHARS_MENSAJE,
    MIN_CHARS_MENSAJE,
    PATRON_EMAIL,
)


def validar_consulta(datos: dict) -> list[str]:
    errores = []

    nombre = (datos.get("nombre") or "").strip()
    email = (datos.get("email") or "").strip()
    mensaje = (datos.get("mensaje") or "").strip()

    if not nombre:
        errores.append("Nombre inválido: no puede estar vacío")

    if not email:
        errores.append("Email inválido: no puede estar vacío")
    elif not PATRON_EMAIL.match(email):
        errores.append(f"Email inválido: '{email}' no tiene un formato válido")

    if not mensaje:
        errores.append("Mensaje inválido: no puede estar vacío")
    elif len(mensaje) < MIN_CHARS_MENSAJE:
        errores.append(
            f"Mensaje inválido: tiene {len(mensaje)} caracteres, mínimo {MIN_CHARS_MENSAJE}"
        )
    elif len(mensaje) > MAX_CHARS_MENSAJE:
        errores.append(
            f"Mensaje inválido: tiene {len(mensaje)} caracteres, máximo {MAX_CHARS_MENSAJE}"
        )

    return errores
