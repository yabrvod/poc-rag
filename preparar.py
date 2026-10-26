"""Limpia el texto de la Constitución copiado desde bcn.cl y lo divide en chunks por artículo.

Entrada:  data/constitucion_raw.txt  (texto de https://www.bcn.cl/leychile/navegar?idNorma=242302)
Salida:   data/chunks.jsonl          (un JSON por línea: id, fuente, texto)
"""

import json
import re
from pathlib import Path

RAW = Path("data/constitucion_raw.txt")
OUT = Path("data/chunks.jsonl")
MAX_CHARS = 1500  # los artículos más largos se parten en trozos de este tamaño aprox.

# Notas al margen de la BCN (qué ley modificó cada parte). Vienen sin sangría y
# a veces cortan una palabra por la mitad, por eso se eliminan antes de unir líneas.
NOTA_MARGEN = re.compile(
    r"^(D\.O|Ley\s*\d|LEY|CPR|Art\b|Art\.|N[°º]|letra [a-z]\)|NOTA\b|TRANSITORIA\b|"
    r"DISPOSICION TRANSITORIA|[ÚU]NICO|[Úú]nico|Inciso|DTO|Decreto|DS\b|y \d|\d[\d.\s°º]*(D\.O.*)?$|\.$)"
)
CAPITULO = re.compile(r"^Capítulo ([IVXL]+)$")
ARTICULO = re.compile(r"^Artículo (\d+)[°º]?(?: (bis|ter|quáter))?\.?-?(?:\s|$)")
ORDINAL = "PRIMER|SEGUND|TERCER|CUART|QUINT|SEXT|SÉPTIM|OCTAV|NOVEN|DÉCIM|UNDÉCIM|DUODÉCIM|VIGÉSIM|VIGESIM|TRIGÉSIM|CUADRAGÉSIM|QUINCUAGÉSIM|SEXAGÉSIM"
TRANSITORIA = re.compile(rf"^((?:{ORDINAL})[A-ZÁÉÍÓÚ ]*?)\.-?\s")


def limpiar(raw: str) -> list[str]:
    """Quita las notas al margen y reconstruye los párrafos partidos."""
    parrafos: list[str] = []
    for linea in raw.replace("\r", "").split("\n"):
        linea = linea.replace(" ", " ")
        texto = linea.strip()
        if not texto:
            continue
        con_sangria = linea.startswith("  ")
        # Un encabezado sin sangría abre párrafo, salvo que el anterior haya quedado
        # cortado por una nota (p. ej. "CUADRAGÉSIMA " + "TERCERA.-" o "QUINCUAGÉSIMA" + " CUARTA.").
        encabezado = (ARTICULO.match(texto) or TRANSITORIA.match(texto)) and not (
            parrafos and (parrafos[-1].endswith(" ") or linea.startswith(" "))
        )
        if con_sangria or encabezado or not parrafos:
            # Se conserva el espacio final: la línea puede seguir después de una nota.
            parrafos.append(linea.lstrip())
        elif NOTA_MARGEN.match(texto):
            continue
        else:
            # Línea sin sangría que no es nota: es la continuación del párrafo anterior.
            parrafos[-1] += linea
    return [re.sub(r"\s+", " ", p).strip() for p in parrafos]


def agrupar(parrafos: list[str]) -> list[dict]:
    """Agrupa los párrafos en artículos y disposiciones transitorias."""
    secciones: list[dict] = []
    capitulo = None
    en_transitorias = False
    actual = None
    for p in parrafos:
        if m := CAPITULO.match(p):
            capitulo = m.group(1)
            continue
        if p.startswith("DISPOSICIONES TRANSITORIAS"):
            en_transitorias = True
            continue
        nombre = None
        if not en_transitorias and (m := ARTICULO.match(p)):
            nombre = f"Artículo {m.group(1)}" + (f" {m.group(2)}" if m.group(2) else "")
            nombre += f" (Capítulo {capitulo})" if capitulo else ""
        elif en_transitorias and (m := TRANSITORIA.match(p)):
            nombre = f"Disposición transitoria {m.group(1).strip().lower()}"
        if nombre:
            actual = {"fuente": nombre, "parrafos": [p]}
            secciones.append(actual)
        elif actual:
            actual["parrafos"].append(p)
    return secciones


def partir(seccion: dict) -> list[str]:
    """Divide una sección larga en trozos de hasta MAX_CHARS sin cortar párrafos."""
    trozos, actual = [], ""
    for p in seccion["parrafos"]:
        if actual and len(actual) + len(p) > MAX_CHARS:
            trozos.append(actual)
            actual = ""
        actual += ("\n" if actual else "") + p
    trozos.append(actual)
    return trozos


def main():
    secciones = agrupar(limpiar(RAW.read_text(encoding="utf-8")))
    chunks = []
    for s in secciones:
        trozos = partir(s)
        for i, texto in enumerate(trozos, 1):
            fuente = s["fuente"] + (f", parte {i} de {len(trozos)}" if len(trozos) > 1 else "")
            chunks.append({"id": len(chunks), "fuente": fuente, "texto": texto})
    with OUT.open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"{len(secciones)} secciones -> {len(chunks)} chunks en {OUT}")


if __name__ == "__main__":
    main()
