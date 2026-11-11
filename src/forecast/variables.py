"""Las variables de cada día, construidas solo con el pasado de su propia serie.

Para cada tienda y producto: las ventas de los 15 días anteriores, el precio de los 7 anteriores, tres marcas de
rachas sin venta (3, 7 y 15 días seguidos a cero, vistas el día anterior) y el mínimo, la media y el máximo de las
ventas en ventanas de 2 a 15 días que acaban la víspera. Ninguna usa la venta del propio día.
"""

import pandas as pd

from . import CLAVE, OBJETIVO

ROTURAS = [3, 7, 15]
RETARDOS = {"unidades": 15, "sell_price": 7}
VENTANAS = range(2, 16)

# Columnas que no entran en el modelo: el código del día y de la semana, el precio del propio día (no se conoce al
# prever) y el segundo evento, que solo aparece en tres días
FUERA_DEL_MODELO = ["d", "wm_yr_wk", "sell_price", "event_name_2", "event_type_2"]


def marcar_rotura(unidades, n):
    """1 si el día y los n − 1 anteriores venden cero; 0 si no."""
    ceros = (pd.Series(unidades).reset_index(drop=True) == 0).astype(int)
    marca = (ceros.rolling(n).sum() == n).astype(int)
    return pd.Series(marca.to_numpy(), index=getattr(unidades, "index", None))


def generar_variables(tabla):
    """Retardos, marcas y ventanas de cada serie, con la tabla ordenada por tienda, producto y fecha."""
    df = tabla.sort_values(CLAVE + ["date"], kind="mergesort").reset_index(drop=True)
    grupos = [df[c] for c in CLAVE]
    nuevas = {}
    for variable, k in RETARDOS.items():
        for paso in range(1, k + 1):
            nuevas[f"{variable}_lag_{paso}"] = df.groupby(grupos)[variable].shift(paso)
    for n in ROTURAS:
        marca = df.groupby(grupos)[OBJETIVO].transform(lambda s, n=n: marcar_rotura(s, n))
        nuevas[f"rotura_stock_{n}_lag_1"] = marca.groupby(grupos).shift(1)
    anterior = df.groupby(grupos)[OBJETIVO].shift(1)
    for nombre, funcion in [("minm", "min"), ("mm", "mean"), ("maxm", "max")]:
        for k in VENTANAS:
            nuevas[f"unidades_{nombre}_{k}"] = anterior.groupby(grupos).transform(
                lambda s, k=k, f=funcion: getattr(s.rolling(k), f)())
    return pd.concat([df, pd.DataFrame(nuevas, index=df.index)], axis=1)


def columnas_generadas(tabla):
    """Las columnas que crea `generar_variables`, en su orden."""
    return [c for c in tabla.columns
            if "_lag_" in c or c.startswith(("unidades_minm_", "unidades_mm_", "unidades_maxm_"))]


def transformar(tabla):
    """La tabla de modelado: variables nuevas, sin las filas que aún no tienen 15 días de historia y sin las columnas
    que no entran en el modelo. Devuelve la tabla y cuántas filas salen."""
    df = generar_variables(tabla)
    nuevas = columnas_generadas(df)
    queda = df.dropna(subset=nuevas).reset_index(drop=True)
    quitadas = len(df) - len(queda)
    queda = queda.drop(columns=FUERA_DEL_MODELO)
    enteras = [c for c in nuevas if c.startswith(("rotura_", "unidades_lag_", "unidades_minm_", "unidades_maxm_"))]
    queda[enteras] = queda[enteras].astype("int64")
    return queda, quitadas
