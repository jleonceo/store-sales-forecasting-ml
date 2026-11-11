"""Prueba a 8 días desde 12 orígenes de 2015, sin tocar diciembre.

Para cada origen, cada 28 días del 18/01/2015 al 22/11/2015, entrena los 20 modelos solo con los días hasta ese
origen (codificación, preselección y búsqueda incluidas), prevé los 8 días siguientes de forma recursiva y los
compara con la venta real y con la referencia: la venta del mismo día de la semana anterior, o de dos semanas antes
si aquella aún no se conocía. Es la medida más sólida del modelo a 8 días: 240 bloques de serie y origen.

Compara además con dos referencias más difíciles de batir, calculadas con lo que se conocía en cada origen: la media
de los 7 últimos días y la media del mismo día de la semana en las 4 semanas anteriores. Y mide el error al sumar las
series de cada tienda y de las dos tiendas.

Tarda entre una y dos horas. Deja `informes/backtest.json` e `informes/backtest_previsiones.csv`.

Uso:  python scripts/backtest.py
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from forecast import BASE_DICIEMBRE, BASE_HISTORIA, DIAS, SEMILLA  # noqa: E402
from forecast.datos import historia_y_diciembre  # noqa: E402
from forecast.modelo import entrenar, error_medio  # noqa: E402
from forecast.prevision import (indice_de_reales, media_mismo_dia, media_ultimos_dias, medir,  # noqa: E402
                                nombre_serie, prever_desde)
from forecast.variables import transformar  # noqa: E402

ULTIMO_ORIGEN = "2015-11-22"
ORIGENES = 12
PASO = 28
REMUESTREOS = 1000
SALIDA = RAIZ / "informes" / "backtest.json"
SALIDA_CSV = RAIZ / "informes" / "backtest_previsiones.csv"
# Las otras referencias: nombre de su columna y cómo se describe
OTRAS = {"media_7_dias": "media de los 7 últimos días", "media_4_semanas": "media del mismo día en 4 semanas"}


def origenes():
    """Los orígenes, del más antiguo al más reciente."""
    ultimo = pd.Timestamp(ULTIMO_ORIGEN)
    return [(ultimo - pd.Timedelta(days=PASO * k)).strftime("%Y-%m-%d") for k in range(ORIGENES - 1, -1, -1)]


def intervalo_diferencia(filas, columna="referencia", semilla=SEMILLA, grupos=("origen", "serie")):
    """Intervalo del 95 % de la diferencia de error (modelo − referencia), remuestreando bloques: de serie y origen
    por defecto, o solo de origen, que es más prudente porque las 20 series de un mismo origen comparten semanas."""
    dif = (filas["real"] - filas["prevision"]).abs() - (filas["real"] - filas[columna]).abs()
    bloques = filas.assign(dif=dif).groupby(list(grupos))["dif"].agg(["sum", "count"]).to_numpy()
    azar = np.random.default_rng(semilla)
    medias = []
    for _ in range(REMUESTREOS):
        k = azar.integers(0, len(bloques), len(bloques))
        medias.append(bloques[k, 0].sum() / bloques[k, 1].sum())
    return [float(np.percentile(medias, 2.5)), float(np.percentile(medias, 97.5))]


def contra(filas, columna):
    """El modelo frente a una referencia: errores, intervalo de la diferencia, bloques y orígenes en que gana."""
    bloques = filas.groupby(["origen", "serie"]).apply(
        lambda g: error_medio(g["real"], g["prevision"]) < error_medio(g["real"], g[columna]), include_groups=False)
    por_origen = filas.groupby("origen").apply(
        lambda g: error_medio(g["real"], g["prevision"]) < error_medio(g["real"], g[columna]), include_groups=False)
    return {"error": error_medio(filas["real"], filas["prevision"]), "referencia": error_medio(filas["real"], filas[columna]),
            "intervalo_diferencia": intervalo_diferencia(filas, columna),
            "intervalo_por_origen": intervalo_diferencia(filas, columna, grupos=("origen",)),
            "bloques_mejor": int(bloques.sum()),
            "bloques": int(len(bloques)), "origenes_mejor": int(por_origen.sum()), "origenes": int(len(por_origen))}


def nivel(filas, por):
    """Error al sumar las series de cada día dentro de cada origen (y de cada grupo de `por`)."""
    sumas = filas.groupby(["origen", "date"] + por)[["real", "prevision", "referencia"]].sum().reset_index()
    def medida(g):
        return {"error": error_medio(g["real"], g["prevision"]), "referencia": error_medio(g["real"], g["referencia"]),
                "real": int(g["real"].sum()), "prevision": int(g["prevision"].sum()),
                "prevision_referencia": int(g["referencia"].sum())}
    if not por:
        return medida(sumas)
    return {k: medida(g) for k, g in sumas.groupby(por[0])}


def resumir(filas):
    """Error del modelo y de la referencia, por horizonte, bloques en que gana el modelo, intervalo, otras referencias
    y niveles agregados."""
    bloques = filas.groupby(["origen", "serie"]).apply(
        lambda g: error_medio(g["real"], g["prevision"]) < error_medio(g["real"], g["referencia"]),
        include_groups=False)
    por_origen = filas.groupby("origen").apply(
        lambda g: error_medio(g["real"], g["prevision"]) < error_medio(g["real"], g["referencia"]),
        include_groups=False)
    return {"origenes_mejor": int(por_origen.sum()), "origenes": int(len(por_origen)),
            "error": error_medio(filas["real"], filas["prevision"]),
            "referencia": error_medio(filas["real"], filas["referencia"]),
            "sesgo": float((filas["prevision"] - filas["real"]).mean()),
            "por_horizonte": {int(h): {"error": error_medio(g["real"], g["prevision"]),
                                       "referencia": error_medio(g["real"], g["referencia"])}
                              for h, g in filas.groupby("horizonte", sort=True)},
            "por_origen": {o: {"error": error_medio(g["real"], g["prevision"]),
                               "referencia": error_medio(g["real"], g["referencia"])}
                           for o, g in filas.groupby("origen", sort=True)},
            "bloques_mejor": int(bloques.sum()), "bloques": int(len(bloques)),
            "intervalo_diferencia": intervalo_diferencia(filas),
            "intervalo_por_origen": intervalo_diferencia(filas, grupos=("origen",)), "filas": int(len(filas)),
            "otras_referencias": {c: {"descripcion": d, **contra(filas, c)} for c, d in OTRAS.items()},
            "total": nivel(filas, []), "por_tienda": nivel(filas, ["store_id"])}


if __name__ == "__main__":
    historia, _, _ = historia_y_diciembre(BASE_HISTORIA, BASE_DICIEMBRE)
    trans, _ = transformar(historia)
    trans["serie"] = nombre_serie(trans)
    reales = indice_de_reales(historia)
    partes = []
    for origen in origenes():
        modelos, _ = entrenar(trans, origen)
        p = medir(prever_desde(historia, modelos, origen), reales, origen)
        p["media_7_dias"] = [media_ultimos_dias(reales, s, origen) for s in p["serie"]]
        p["media_4_semanas"] = [media_mismo_dia(reales, s, f, origen) for s, f in zip(p["serie"], p["date"])]
        partes.append(p.assign(origen=origen))
        print(f"origen {origen}: modelo {error_medio(p['real'], p['prevision']):.2f}, "
              f"referencia {error_medio(p['real'], p['referencia']):.2f}", flush=True)
    filas = pd.concat(partes, ignore_index=True)
    SALIDA.parent.mkdir(exist_ok=True)
    filas.to_csv(SALIDA_CSV, index=False)
    d = {"fechas_origen": origenes(), "dias": DIAS, "semilla": SEMILLA, **resumir(filas)}
    SALIDA.write_text(json.dumps(d, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    print(f"backtest: modelo {d['error']:.2f}, referencia {d['referencia']:.2f}, "
          f"gana en {d['bloques_mejor']} de {d['bloques']} bloques")
    for c, o in d["otras_referencias"].items():
        print(f"  frente a {o['descripcion']}: {o['error']:.2f} / {o['referencia']:.2f}, "
              f"intervalo {o['intervalo_diferencia'][0]:.2f} a {o['intervalo_diferencia'][1]:.2f}")
    print(f"  total de las dos tiendas: {d['total']['error']:.2f} / {d['total']['referencia']:.2f}")
