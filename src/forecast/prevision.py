"""Previsión recursiva de varios días y su comparación con la referencia.

Desde un día de origen, con las ventas reales hasta ese día, prevé el día siguiente; esa previsión pasa a ser la
venta de ese día para calcular las variables del siguiente, y así hasta completar el horizonte. La previsión se
acota en cero y se pasa a unidades enteras quitando los decimales.
"""

import numpy as np
import pandas as pd

from . import CLAVE, DIAS, OBJETIVO
from .modelo import aplicar_codificadores, error_medio
from .variables import generar_variables

# Las variables más largas miran 15 días atrás: con 20 de historia basta
DIAS_DE_HISTORIA = 20


def nombre_serie(tabla):
    """El nombre de cada serie: tienda · producto."""
    return tabla["store_id"] + " · " + tabla["item_id"]


def variables_del_dia(historia, dia):
    """Las variables de las filas de `dia` con la historia anterior; la venta del propio día se borra antes."""
    fecha = dia["date"].min()
    desde = (pd.Timestamp(fecha) - pd.Timedelta(days=DIAS_DE_HISTORIA)).strftime("%Y-%m-%d")
    vacio = dia.copy()
    vacio[OBJETIVO] = np.nan
    junta = pd.concat([historia[historia["date"] >= desde], vacio], ignore_index=True)
    v = generar_variables(junta)
    return v[v["date"] == fecha].reset_index(drop=True)


def prever_desde(tabla, modelos, origen, dias=DIAS):
    """Los `dias` días después de `origen`, cada uno con la previsión de los anteriores como venta.

    `tabla` trae las ventas reales hasta el origen y, para los días siguientes, al menos su calendario y su precio.
    Cada previsión se escribe como venta de su día uniéndola por tienda y producto, nunca por posición.
    """
    tabla = tabla.sort_values(CLAVE + ["date"], kind="mergesort").reset_index(drop=True)
    historia = tabla[tabla["date"] <= origen]
    fechas = sorted(tabla.loc[tabla["date"] > origen, "date"].unique())[:dias]
    salida = []
    for h, fecha in enumerate(fechas, start=1):
        dia = tabla[tabla["date"] == fecha]
        v = variables_del_dia(historia, dia)
        v["serie"] = nombre_serie(v)
        filas = []
        for s, t in v.groupby("serie", sort=True):
            modelo, cod, columnas = modelos[s]
            x = aplicar_codificadores(t, cod, columnas)[list(modelo.feature_names_in_)]
            decimal = float(modelo.predict(x)[0])
            filas.append({"serie": s, "store_id": t["store_id"].iloc[0], "item_id": t["item_id"].iloc[0],
                          "date": fecha, "horizonte": h, "prevision_decimal": decimal,
                          "prevision": int(max(decimal, 0.0))})
        p = pd.DataFrame(filas)
        if len(p) != len(dia):
            raise ValueError(f"el {fecha} hay series sin previsión")
        nueva = dia.drop(columns=OBJETIVO).merge(p[CLAVE + ["prevision"]], on=CLAVE, how="inner", validate="1:1")
        historia = pd.concat([historia, nueva.rename(columns={"prevision": OBJETIVO})], ignore_index=True)
        salida.append(p)
    return pd.concat(salida, ignore_index=True)


def indice_de_reales(tabla):
    """Las ventas reales por (serie, fecha)."""
    return dict(zip(zip(nombre_serie(tabla), tabla["date"]), tabla[OBJETIVO].astype(int)))


def referencia(reales, serie, fecha, origen):
    """La referencia desde un origen: la venta del mismo día de la semana anterior, o de dos semanas antes si aquella
    aún no se conocía el día del origen."""
    paso = 7
    while (pd.Timestamp(fecha) - pd.Timedelta(days=paso)).strftime("%Y-%m-%d") > origen:
        paso += 7
    return reales[(serie, (pd.Timestamp(fecha) - pd.Timedelta(days=paso)).strftime("%Y-%m-%d"))]


def medir(previsiones, reales, origen):
    """Añade la venta real y la referencia a cada previsión que ya tiene venta real; las demás quedan sin medir."""
    p = previsiones.copy()
    p["real"] = [reales.get((s, f)) for s, f in zip(p["serie"], p["date"])]
    p["referencia"] = [referencia(reales, s, f, origen) for s, f in zip(p["serie"], p["date"])]
    return p


def resumen(filas):
    """Error del modelo y de la referencia en un grupo de previsiones con venta real."""
    return {"error": error_medio(filas["real"], filas["prevision"]),
            "referencia": error_medio(filas["real"], filas["referencia"]), "filas": int(len(filas))}
