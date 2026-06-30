"""context.py — Selección de contexto desde el FAQ (Fase 2).

Qué hace este módulo:
  - `cargar_faq()` lee `data/faq.json` (ya implementada).
  - `seleccionar_faq()` elige las entradas más relevantes para una pregunta.

Para qué sirve:
  - No meter las 6 entradas del FAQ en cada prompt (ahorro de tokens y ruido).
  - Devolver solo la información que el modelo necesita para responder.

Función a implementar:
  - `seleccionar_faq()` — ver README FASE 2, Tarea 1.
"""

import json
from pathlib import Path


def cargar_faq(ruta: Path) -> list[dict]:
    """Carga faq.json desde disco. Ya está implementada; no necesitas modificarla."""
    with ruta.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("faq.json debe ser una lista de entradas")
    return data


def seleccionar_faq(faq: list[dict], consulta: str, max_entradas: int = 1) -> list[dict]:
    """Elige entradas del FAQ por keywords (sin vector DB).

    Entrada: faq (6 entradas), consulta = "¿¿Qué es la live review del bootcamp?"
    Salida: lista con 0 o max_entradas dicts del FAQ más relevantes.
    Salida vacía [] si ninguna keyword coincide.
    """
    consulta_norm = consulta.lower()

    puntuaciones = []
    for entrada in faq:
        # Construir texto de búsqueda combinando pregunta + respuesta + keywords si existen
        texto = " ".join([
            entrada.get("pregunta", ""),
            entrada.get("respuesta", ""),
            " ".join(entrada.get("keywords", [])),
        ]).lower()

        # Contar cuántas palabras de la consulta aparecen en el texto de la entrada
        palabras = set(consulta_norm.split())
        coincidencias = sum(1 for palabra in palabras if palabra in texto)

        if coincidencias > 0:
            puntuaciones.append((coincidencias, entrada))

    # Ordenar por puntuación descendente y devolver las top max_entradas
    puntuaciones.sort(key=lambda x: x[0], reverse=True)
    return [entrada for _, entrada in puntuaciones[:max_entradas]]