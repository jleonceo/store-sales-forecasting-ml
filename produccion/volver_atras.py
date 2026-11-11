"""Vuelve al modelo anterior: restaura como vigente el último guardado en `modelos/anteriores/`.

El vigente que se retira no se borra: queda también en `modelos/anteriores/`, con «_retirado» en el nombre. El código
se vuelve atrás con git, a la versión etiquetada que se quiera restaurar.

Uso:  python produccion/volver_atras.py
"""

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from forecast.produccion import volver_atras  # noqa: E402

if __name__ == "__main__":
    print(f"OK: restaurado como vigente el modelo de {volver_atras()}")
