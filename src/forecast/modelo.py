"""Un modelo por tienda y producto: codificación del calendario, preselección de variables y búsqueda de
hiperparámetros con validación temporal.

Para cada serie, con los días hasta la fecha de entrenamiento:
1. codifica el calendario: una columna por evento y, para el mes y el día de la semana, la media suavizada de las
   ventas de la serie en ese valor;
2. ordena todas las variables por información mutua con las ventas y se queda con las 70 primeras;
3. busca los hiperparámetros de un `HistGradientBoostingRegressor` con 10 candidatos y tres cortes temporales de 8
   días, puntuando con el error absoluto medio, y reentrena el mejor con todos los días.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.feature_selection import mutual_info_regression
from sklearn.model_selection import RandomizedSearchCV, TimeSeriesSplit

from . import DIAS, OBJETIVO, SEMILLA

# Calendario: qué columnas se codifican y cómo; el año y el tipo de evento no entran
UNA_POR_VALOR = ["event_name_1"]
MEDIA_POR_VALOR = ["month", "wday", "weekday"]
NO_ENTRAN = ["year", "event_type_1"]
NO_SON_VARIABLES = ["date", "store_id", "item_id", OBJETIVO, "sell_price_faltante", "serie"]
# Media suavizada: peso de un valor con n días = 1 / (1 + e^(−(n − MIN_HOJA) / SUAVE))
MIN_HOJA = 100
SUAVE = 1.0

N_VARIABLES = 70
CORTES = 3
REJILLA = {"learning_rate": [0.03, 0.05, 0.1, 0.2], "max_iter": [100, 200, 400], "max_leaf_nodes": [15, 31, 63],
           "min_samples_leaf": [10, 20, 50], "l2_regularization": [0.0, 0.1, 1.0]}
CANDIDATOS = 10
# La referencia: la venta del mismo día de la semana anterior
DIAS_ATRAS = 7


def error_medio(real, previsto):
    """Error absoluto medio."""
    return float(np.mean(np.abs(np.asarray(real, dtype=float) - np.asarray(previsto, dtype=float))))


def columnas_variables(trans):
    """Las variables numéricas de la tabla de modelado, sin claves, objetivo ni calendario por codificar."""
    fuera = NO_SON_VARIABLES + UNA_POR_VALOR + MEDIA_POR_VALOR + NO_ENTRAN
    return [c for c in trans.columns if c not in fuera]


def ajustar_codificadores(t):
    """Aprende de los días de entrenamiento de una serie los eventos que existen y la media suavizada de las ventas
    por mes y por día de la semana."""
    y = t[OBJETIVO]
    media = {}
    for c in MEDIA_POR_VALOR:
        valores = t[c].astype(str)
        cifras = y.groupby(valores).agg(["count", "mean"])
        peso = 1 / (1 + np.exp(-(cifras["count"] - MIN_HOJA) / SUAVE))
        m = y.mean() * (1 - peso) + cifras["mean"] * peso
        m[cifras["count"] == 1] = y.mean()
        media[c] = {"previa": float(y.mean()), "media": {str(k): float(v) for k, v in m.items()}}
    return {"una_por_valor": {c: sorted(t[c].astype(str).unique()) for c in UNA_POR_VALOR}, "media": media}


def aplicar_codificadores(t, cod, columnas):
    """Las variables de una tabla con lo aprendido: un evento no visto da ceros y un valor nuevo, la media de la serie."""
    partes = []
    for c, valores in cod["una_por_valor"].items():
        texto = t[c].astype(str)
        partes.append(pd.DataFrame({f"{c}_{v}": (texto == v).astype(float) for v in valores}, index=t.index))
    partes.append(pd.DataFrame({f"{c}_te": t[c].astype(str).map(m["media"]).fillna(m["previa"]).astype(float)
                                for c, m in cod["media"].items()}, index=t.index))
    resto = [c for c in columnas if c in t.columns]
    return pd.concat(partes + [t[resto]], axis=1)


def ranking(nombres, importancias):
    """Variables de mayor a menor importancia, con los empates deshechos por nombre."""
    return [v for v, _ in sorted(zip(nombres, importancias), key=lambda x: (-x[1], x[0]))]


def validar_y_entrenar(x, y):
    """Búsqueda de hiperparámetros con cortes temporales; devuelve el modelo reentrenado y su validación."""
    busqueda = RandomizedSearchCV(HistGradientBoostingRegressor(early_stopping=False, random_state=SEMILLA), REJILLA,
                                  n_iter=CANDIDATOS, cv=TimeSeriesSplit(CORTES, test_size=DIAS),
                                  scoring="neg_mean_absolute_error", random_state=SEMILLA, n_jobs=1).fit(x, y)
    mejor = busqueda.best_index_
    errores = [float(-busqueda.cv_results_[f"split{k}_test_score"][mejor]) for k in range(CORTES)]
    prueba = np.concatenate([p for _, p in TimeSeriesSplit(CORTES, test_size=DIAS).split(np.arange(len(y)))])
    valores = np.asarray(y)
    validacion = {"error": float(np.mean(errores)), "error_por_corte": errores,
                  "referencia": error_medio(valores[prueba], valores[prueba - DIAS_ATRAS]),
                  "media_unidades": float(valores[prueba].mean()),
                  "parametros": {k: (float(v) if isinstance(v, float) else int(v))
                                 for k, v in busqueda.best_params_.items()}}
    return busqueda.best_estimator_, validacion


def entrenar(trans, hasta, aviso=None):
    """Un modelo por serie con los días hasta `hasta`. Devuelve {serie: (modelo, codificadores, columnas)} y la
    validación de cada serie."""
    columnas = columnas_variables(trans)
    modelos, validacion = {}, {}
    for s, t in trans[trans["date"] <= hasta].groupby("serie", sort=True):
        cod = ajustar_codificadores(t)
        x_todas = aplicar_codificadores(t, cod, columnas)
        orden = ranking(list(x_todas.columns), mutual_info_regression(x_todas, t[OBJETIVO], random_state=SEMILLA))
        if len(orden) < N_VARIABLES:
            raise ValueError(f"{s}: solo hay {len(orden)} variables y se eligen {N_VARIABLES}")
        x = x_todas[orden[:N_VARIABLES]]
        modelo, val = validar_y_entrenar(x, t[OBJETIVO].astype(float))
        modelos[s], validacion[s] = (modelo, cod, columnas), val
        if aviso:
            aviso(f"{s}: validación {val['error']:.2f} frente a {val['referencia']:.2f} de la referencia")
    return modelos, validacion
