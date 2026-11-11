"""Previsión diaria de ventas por tienda y producto: datos, variables, modelo y previsión recursiva."""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DATOS = RAIZ / "datos"
BASE_HISTORIA = DATOS / "ventas_2013_2015.db"
BASE_DICIEMBRE = DATOS / "diciembre_2015.db"

CLAVE = ["store_id", "item_id"]
OBJETIVO = "unidades"
SEMILLA = 42
DIAS = 8
FIN_DESARROLLO = "2015-11-30"
