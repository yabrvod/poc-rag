# PoC: RAG desde cero

Un RAG (*Retrieval-Augmented Generation*) mínimo, sin frameworks, que responde preguntas sobre la **Constitución Política de Chile** citando el artículo. Todo corre local con [Ollama](https://ollama.com).

Escrito en el blog: <https://www.yabd.cl/blog/poc-rag-desde-cero/>

## Cómo funciona

```
Constitución (texto BCN) → preparar.py → chunks por artículo
                                            ↓ bge-m3
pregunta → embedding → similitud coseno → top 4 chunks → prompt → qwen3:4b-instruct → respuesta con citas
```

## Ejecutar

Requisitos: Python 3.12 y Ollama.

```bash
ollama pull bge-m3
ollama pull qwen3:4b-instruct
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt     # en Linux/macOS: .venv/bin/pip
.venv/Scripts/jupyter notebook rag_desde_cero.ipynb
```

`data/chunks.jsonl` ya viene generado. Para regenerarlo, guarda el texto de
<https://www.bcn.cl/leychile/navegar?idNorma=242302> en `data/constitucion_raw.txt` y ejecuta `python preparar.py`.

## Archivos

| Archivo                  | Qué es                                                         |
| ------------------------ | -------------------------------------------------------------- |
| `preparar.py`            | Limpia el texto de la BCN y lo divide en chunks por artículo   |
| `rag_desde_cero.ipynb`   | El RAG paso a paso: embeddings, búsqueda, generación, pruebas  |
| `data/chunks.jsonl`      | Los 378 chunks con su fuente                                   |
| `data/constitucion_raw.txt` | Texto original copiado desde bcn.cl                         |

Fuente del texto: Biblioteca del Congreso Nacional de Chile, versión vigente al 16-04-2026.
