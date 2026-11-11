"""Compara la previsión de una mañana con lo que se vendió de verdad, cuando ya se conoce.

Lee `produccion/salidas/<dia>/prevision.csv`, le añade la venta real y la referencia (la venta del mismo día de la
semana anterior que se conocía esa mañana) y escribe `evaluacion.json` en la misma carpeta: el error del modelo y de
la referencia en total, por día y por serie, y cuántas previsiones quedan sin medir porque su venta aún no existe.

Uso:  python produccion/evaluar.py --dia 2015-12-24
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from forecast.datos import historia_y_diciembre  # noqa: E402
from forecast.prevision import indice_de_reales, medir, resumen  # noqa: E402
from forecast.produccion import config  # noqa: E402


def evaluar(dia, total=None, carpeta=None):
    """Mide la previsión de `dia` con las ventas reales que haya; devuelve el resumen escrito."""
    c = config()
    carpeta = carpeta or c["salidas"]
    if total is None:
        _, _, total = historia_y_diciembre(c["datos_historia"], c["datos_nuevos"])
    p = pd.read_csv(carpeta / dia / "prevision.csv", dtype={"date": str})
    origen = (pd.Timestamp(dia) - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    medida = medir(p, indice_de_reales(total), origen)
    con_real = medida[medida["real"].notna()]
    d = {"dia": dia, "origen": origen, "previsiones": int(len(medida)), "medidas": int(len(con_real)),
         "sin_medir": int(len(medida) - len(con_real))}
    if len(con_real):
        d |= {"total": resumen(con_real),
              "por_dia": {f: resumen(g) for f, g in con_real.groupby("date", sort=True)},
              "por_serie": {s: resumen(g) for s, g in con_real.groupby("serie", sort=True)},
              "suma_por_dia": {f: {"real": int(g["real"].sum()), "prevision": int(g["prevision"].sum()),
                                   "referencia": int(g["referencia"].sum())}
                               for f, g in con_real.groupby("date", sort=True)}}
    (carpeta / dia / "evaluacion.json").write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    return d


if __name__ == "__main__":
    argumentos = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    argumentos.add_argument("--dia", required=True, help="la mañana de la previsión que se mide, AAAA-MM-DD")
    d = evaluar(argumentos.parse_args().dia)
    if "total" in d:
        print(f"OK: {d['medidas']} previsiones medidas; modelo {d['total']['error']:.2f}, "
              f"referencia {d['total']['referencia']:.2f}")
    else:
        print(f"OK: ninguna previsión con venta real todavía ({d['sin_medir']} sin medir)")
