"""Utilidades de las pruebas: la ruta del paquete y un lanzador de casos que sale con 0 o con 1."""

import sys
import traceback
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "produccion"))


def lanzar(casos):
    """Ejecuta cada caso (una función sin argumentos que lanza AssertionError si falla) y sale con 0 o 1."""
    sys.stdout.reconfigure(encoding="utf-8")
    fallos = 0
    for caso in casos:
        try:
            caso()
            print(f"  ok     {caso.__name__}")
        except Exception:  # noqa: BLE001 - se informa de cualquier fallo del caso
            fallos += 1
            print(f"  FALLA  {caso.__name__}")
            traceback.print_exc(limit=2)
    print(f"{len(casos) - fallos} de {len(casos)}")
    sys.exit(1 if fallos else 0)


def esperar_error(funcion, tipo):
    """Comprueba que `funcion()` lanza `tipo`."""
    try:
        funcion()
    except tipo:
        return
    raise AssertionError(f"se esperaba {tipo.__name__} y no saltó")
