"""Reúne en `informes/resultados.json` todas las cifras que cita la portada, leídas de lo que dejan los procesos.

Lee el manifiesto de `modelos/` (la validación de cada serie), las salidas de la simulación de diciembre
(`produccion/salidas/`) y, si existe, `informes/backtest.json`. No calcula ningún modelo: solo resume.

- Validación: la de la búsqueda de hiperparámetros, a un día con las ventas reales, en los 24 últimos días de
  noviembre de 2015 (3 cortes de 8).
- Un día vista: la mañana del 16/12/2015, primer día de su previsión.
- Ocho días vista: la mañana del 24/12/2015, sus 8 días del 24 al 31/12, por serie, por tienda y en el total.
- Simulación: las 31 mañanas de diciembre.

Uso:  python scripts/resultados.py
"""

import json
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from forecast import BASE_DICIEMBRE, BASE_HISTORIA  # noqa: E402
from forecast.datos import historia_y_diciembre  # noqa: E402
from forecast.modelo import error_medio  # noqa: E402
from forecast.prevision import indice_de_reales, medir  # noqa: E402
from forecast.variables import transformar  # noqa: E402
from forecast.produccion import carpetas_modelos, config  # noqa: E402

CARPETA_MODELOS = carpetas_modelos()[0]
CARPETA_SALIDAS = config()["salidas"]
REGISTRO = CARPETA_SALIDAS / "registro.csv"

SALIDA = RAIZ / "informes" / "resultados.json"
BACKTEST = RAIZ / "informes" / "backtest.json"
DIA_UNO = "2015-12-16"
DIA_OCHO = "2015-12-24"


def nivel(filas, por):
    """Error del modelo y de la referencia sumando las series de cada día dentro de cada grupo de `por`."""
    sumas = filas.groupby(por + ["date"])[["real", "prevision", "referencia"]].sum().reset_index()
    if not por:
        return {"error": error_medio(sumas["real"], sumas["prevision"]),
                "referencia": error_medio(sumas["real"], sumas["referencia"])}
    return {k: {"error": error_medio(g["real"], g["prevision"]), "referencia": error_medio(g["real"], g["referencia"])}
            for k, g in sumas.groupby(por[0])}


def resumen_datos(historia, diciembre):
    """Lo que traen los datos: filas, unidades, precios rellenados, filas sin historia y días sin ventas.

    Un día sin ventas dentro de una racha de más de 60 días seguidos a cero se cuenta como producto fuera de la
    tienda; los demás, como días sueltos sin ventas.
    """
    trans, sin_historia = transformar(historia)
    sueltos = fuera = 0
    for _, t in historia.groupby(["store_id", "item_id"], sort=True):
        cero = (t["unidades"] == 0).to_numpy()
        racha = 0
        for c in list(cero) + [False]:
            if c:
                racha += 1
                continue
            if racha > 60:
                fuera += racha
            else:
                sueltos += racha
            racha = 0
    return {"filas": int(len(historia)), "unidades": int(historia["unidades"].sum()),
            "series": int(historia.groupby(["store_id", "item_id"]).ngroups),
            "desde": historia["date"].min(), "hasta": historia["date"].max(),
            "precios_rellenados": int(historia["sell_price_faltante"].sum()), "filas_sin_historia": int(sin_historia),
            "filas_modelado": int(len(trans)),
            "dias_sin_ventas_sueltos": int(sueltos), "dias_fuera_de_la_tienda": int(fuera),
            "diciembre_filas": int(len(diciembre)), "diciembre_unidades": int(diciembre["unidades"].sum())}


def filas_con_real(dia, total):
    """Las previsiones de una mañana que ya tienen venta real, con esa venta y la referencia."""
    p = pd.read_csv(CARPETA_SALIDAS / dia / "prevision.csv", dtype={"date": str})
    origen = (pd.Timestamp(dia) - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    m = medir(p, indice_de_reales(total), origen)
    return m[m["real"].notna()].astype({"real": int})


if __name__ == "__main__":
    manifiesto = json.loads((CARPETA_MODELOS / "manifiesto.json").read_text(encoding="utf-8"))
    val = manifiesto["validacion"]
    validacion = {"error": sum(v["error"] for v in val.values()) / len(val),
                  "referencia": sum(v["referencia"] for v in val.values()) / len(val),
                  "series_mejor": sum(v["error"] < v["referencia"] for v in val.values()), "series": len(val)}

    historia, diciembre, total = historia_y_diciembre(BASE_HISTORIA, BASE_DICIEMBRE)
    uno =filas_con_real(DIA_UNO, total)
    uno = uno[uno["horizonte"] == 1]
    un_dia = {"dia": DIA_UNO, "error": error_medio(uno["real"], uno["prevision"]),
              "referencia": error_medio(uno["real"], uno["referencia"]),
              "series_mejor": int(((uno["real"] - uno["prevision"]).abs()
                                   < (uno["real"] - uno["referencia"]).abs()).sum()), "series": int(len(uno))}

    ocho = filas_con_real(DIA_OCHO, total)
    por_serie = {s: {"error": error_medio(g["real"], g["prevision"]),
                     "referencia": error_medio(g["real"], g["referencia"])} for s, g in ocho.groupby("serie")}
    ocho_dias = {"dia": DIA_OCHO, "desde": ocho["date"].min(), "hasta": ocho["date"].max(),
                 "error": error_medio(ocho["real"], ocho["prevision"]),
                 "referencia": error_medio(ocho["real"], ocho["referencia"]),
                 "sesgo": float((ocho["prevision"] - ocho["real"]).mean()),
                 "series_mejor": sum(v["error"] < v["referencia"] for v in por_serie.values()),
                 "series": len(por_serie), "total": nivel(ocho, []), "por_tienda": nivel(ocho, ["store_id"]),
                 "por_serie": por_serie,
                 "por_dia_total": {f: {"real": int(g["real"].sum()), "prevision": int(g["prevision"].sum()),
                                       "referencia": int(g["referencia"].sum())}
                                   for f, g in ocho.groupby("date", sort=True)}}

    registro = pd.read_csv(REGISTRO)
    simulacion = {"mananas": int(len(registro)), "mejor_que_referencia": int(registro["mejor_que_referencia"].sum()),
                  "previsiones": int(registro["previsiones"].sum()), "medidas": int(registro["medidas"].sum())}

    d = {"datos": resumen_datos(historia, diciembre), "entrenado_hasta": manifiesto["entrenado_hasta"],
         "validacion": validacion, "un_dia": un_dia,
         "ocho_dias": ocho_dias, "simulacion": simulacion,
         "backtest": json.loads(BACKTEST.read_text(encoding="utf-8")) if BACKTEST.exists() else None}
    SALIDA.parent.mkdir(exist_ok=True)
    SALIDA.write_text(json.dumps(d, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    print(f"validación {validacion['error']:.2f} / {validacion['referencia']:.2f} ({validacion['series_mejor']} de 20); "
          f"un día {un_dia['error']:.2f} / {un_dia['referencia']:.2f} ({un_dia['series_mejor']} de 20); "
          f"ocho días {ocho_dias['error']:.4f} / {ocho_dias['referencia']:.4f}; total "
          f"{ocho_dias['total']['error']:.2f} / {ocho_dias['total']['referencia']:.2f}")
