"""Lectura de las bases SQLite y montaje de la tabla diaria: una fila por tienda, producto y día.

Las bases traen tres tablas: el calendario, las ventas con un día por columna y los precios por semana comercial.
La tabla diaria despivota las ventas, une el calendario por el código del día y el precio por tienda, producto y
semana, y comprueba en cada cruce que no se ganan ni se pierden filas ni unidades.
"""

import re
import sqlite3
from contextlib import closing

import pandas as pd

from . import CLAVE, OBJETIVO

PATRON_DIA = re.compile(r"^d_\d+$")

# Columnas de la tabla diaria, en su orden
COLUMNAS = ["store_id", "item_id", "d", "unidades", "date", "wm_yr_wk", "weekday", "wday", "month", "year",
            "event_name_1", "event_type_1", "event_name_2", "event_type_2", "sell_price", "sell_price_faltante"]

# Columnas que no aportan nada: el número de fila heredado, un identificador que repite tienda y producto, y tres
# columnas con un solo valor en todas las filas (departamento, categoría y estado)
SOBRAN = {"calendar": ["index"], "sales": ["index", "id", "dept_id", "cat_id", "state_id"], "sell_prices": ["index"]}

# Un día sin evento es un día normal, no un dato que falta
SIN_EVENTO = "Sin_evento"


class CruceIncorrecto(Exception):
    """Un cruce que gana o pierde filas o unidades, o que deja días sin calendario o sin precio."""


def leer_base(ruta):
    """Las tres tablas de una base SQLite, leídas en modo solo lectura."""
    with closing(sqlite3.connect(f"file:{ruta.as_posix()}?mode=ro", uri=True)) as con:
        return {t: pd.read_sql_query(f'select * from "{t}"', con) for t in ["calendar", "sales", "sell_prices"]}


def limpiar(tablas):
    """Quita las columnas que no aportan y escribe el día sin evento como tal."""
    limpias = {t: df.drop(columns=[c for c in SOBRAN[t] if c in df.columns]) for t, df in tablas.items()}
    for c in ["event_name_1", "event_type_1"]:
        limpias["calendar"][c] = limpias["calendar"][c].fillna(SIN_EVENTO)
    return limpias


def despivotar(ventas):
    """Una fila por tienda, producto y día."""
    dias = [c for c in ventas.columns if PATRON_DIA.match(c)]
    return ventas.melt(id_vars=CLAVE, value_vars=dias, var_name="d", value_name=OBJETIVO)


def cruzar(partida, maestro, clave):
    """Cruce N:1 por la izquierda que para si cambian las filas o la suma de unidades."""
    if maestro.duplicated(clave).any():
        raise CruceIncorrecto(f"el maestro repite claves de {clave}")
    unida = partida.merge(maestro, on=clave, how="left", validate="m:1")
    if len(unida) != len(partida) or unida[OBJETIVO].sum() != partida[OBJETIVO].sum():
        raise CruceIncorrecto(f"el cruce por {clave} cambió las filas o las unidades")
    return unida


def rellenar_precio(tabla):
    """El precio de una semana sin fila de precios, con el precio más frecuente del producto; las filas rellenadas
    quedan marcadas en `sell_price_faltante`."""
    nueva = tabla.copy()
    nueva["sell_price_faltante"] = nueva["sell_price"].isna()

    def moda(registros):
        registros = registros.copy()
        registros.loc[registros["sell_price"].isna(), "sell_price"] = registros["sell_price"].mode().iloc[0]
        return registros

    return nueva.groupby("item_id", group_keys=False)[nueva.columns.tolist()].apply(moda).loc[tabla.index]


def tabla_diaria(tablas, rellenar=True):
    """La tabla diaria de una base: ventas despivotadas con su calendario y su precio, ordenada por serie y fecha.

    Con `rellenar`, las semanas sin precio toman el precio más frecuente del producto. Sin él, un día sin precio para
    el proceso: es lo que se pide a los datos que llegan cada día.
    """
    t = limpiar(tablas)
    largo = despivotar(t["sales"])
    unida = cruzar(largo, t["calendar"], ["d"])
    unida = cruzar(unida, t["sell_prices"], CLAVE + ["wm_yr_wk"])
    if unida["date"].isna().any():
        raise CruceIncorrecto("hay días sin calendario")
    if rellenar:
        unida = rellenar_precio(unida)
    else:
        if unida["sell_price"].isna().any():
            raise CruceIncorrecto("hay días sin precio")
        unida["sell_price_faltante"] = False
    return unida[COLUMNAS].sort_values(CLAVE + ["date"], kind="mergesort").reset_index(drop=True)


def comprobar_continuidad(tabla):
    """Para si alguna serie repite un día o le falta alguno: las ventanas se cuentan por filas."""
    for clave, t in tabla.groupby(CLAVE, sort=True):
        fechas = pd.to_datetime(t["date"], format="%Y-%m-%d").sort_values()
        if fechas.duplicated().any() or len(fechas) != (fechas.iloc[-1] - fechas.iloc[0]).days + 1:
            raise CruceIncorrecto(f"{' · '.join(clave)} tiene días repetidos o huecos")


def historia_y_diciembre(base_historia, base_diciembre):
    """La historia hasta el 30/11/2015, diciembre de 2015 y las dos juntas, ya comprobadas."""
    historia = tabla_diaria(leer_base(base_historia), rellenar=True)
    diciembre = tabla_diaria(leer_base(base_diciembre), rellenar=False)
    total = pd.concat([historia, diciembre], ignore_index=True)
    total = total.sort_values(CLAVE + ["date"], kind="mergesort").reset_index(drop=True)
    comprobar_continuidad(total)
    return historia, diciembre, total
