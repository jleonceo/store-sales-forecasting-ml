"""Comprueba que ningún fichero del repositorio contiene palabras vetadas, nombres internos ni rutas de una máquina.

Recorre todos los ficheros de texto bajo la carpeta indicada (por defecto, la raíz del repositorio), salvo `.git` y los
generados que no se suben. Sale con 0 si no encuentra nada y con 1 si encuentra algo, e imprime cada aparición con su
fichero y su línea.

Uso:  python tests/probar_sin_origen.py [carpeta]
"""

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

# Palabras que no pueden aparecer en ningún fichero publicado. Cada patrón lleva su motivo.
VETADAS = {
    r"\bejercicio\b": "origen formativo del material",
    r"\bprofesor": "origen formativo del material",
    r"\bcurso\b": "origen formativo del material",
    r"\bm[aá]ster\b": "origen formativo del material",
    r"\blecci[oó]n\b": "origen formativo del material",
    r"\bcuaderno\b": "origen formativo del material",
    r"\baudio\b": "origen formativo del material",
    r"\bR62-\d+": "referencia interna",
    r"\b(CP|RH|WF|SC|HAL|DEC)-\d+": "referencia interna",
    r"\bJuan\b": "nombre interno",
    r"\bClaude\b": "nombre interno",
    r"\bskills?\b": "nombre interno",
    r"mini workflow": "nombre interno",
    r"00_comun": "nombre interno",
    r"contexto-proyecto": "carpeta interna",
    r"reglas §\s*\d": "referencia a un documento interno",
    r"[A-Za-z]:[\\/]+Users": "ruta de una máquina",
    r"\busuario\b": "ruta de una máquina",
    r"anaconda3": "ruta de una máquina",
    r"PYTHON_IA|PROYECTOS_GITHUB": "ruta de una máquina",
}

# Lo que no se sube o no es texto
OMITIR_CARPETAS = {".git", "__pycache__", ".pytest_cache", "modelos"}
OMITIR_SUFIJOS = {".db", ".parquet", ".joblib", ".png", ".svg", ".pyc"}
# La licencia lleva el nombre del autor, que sí tiene que estar
OMITIR_FICHEROS = {"LICENSE"}
# Este propio fichero contiene los patrones a propósito
ESTE = Path(__file__).resolve()


def ficheros(raiz):
    """Los ficheros de texto bajo `raiz`, sin las carpetas y sufijos omitidos."""
    for ruta in sorted(raiz.rglob("*")):
        if not ruta.is_file() or ruta.resolve() == ESTE or ruta.name in OMITIR_FICHEROS:
            continue
        if any(p in OMITIR_CARPETAS for p in ruta.relative_to(raiz).parts):
            continue
        if ruta.suffix.lower() in OMITIR_SUFIJOS:
            continue
        yield ruta


def buscar(raiz):
    """Lista de (fichero, línea, patrón, motivo, texto) con cada aparición."""
    compilados = [(re.compile(p, re.IGNORECASE), p, m) for p, m in VETADAS.items()]
    hallazgos = []
    for ruta in ficheros(raiz):
        try:
            texto = ruta.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for n, linea in enumerate(texto.splitlines(), 1):
            for rx, p, motivo in compilados:
                if rx.search(linea):
                    hallazgos.append((ruta.relative_to(raiz), n, p, motivo, linea.strip()[:120]))
    return hallazgos


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raiz =Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else RAIZ
    encontrados = buscar(raiz)
    for f, n, p, motivo, linea in encontrados:
        print(f"{f}:{n}  [{motivo}]  {linea}")
    afectados = len({f for f, *_ in encontrados})
    if encontrados:
        print(f"ROJO: {len(encontrados)} apariciones en {afectados} ficheros")
        sys.exit(1)
    print("VERDE: ningún fichero con palabras vetadas, nombres internos ni rutas de una máquina")
