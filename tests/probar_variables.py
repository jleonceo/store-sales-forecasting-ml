"""Pruebas de las variables: ninguna mira la venta del propio día y cada una sale de su propia serie."""

import numpy as np
import pandas as pd
from comun import lanzar

from forecast.modelo import ajustar_codificadores
from forecast.variables import generar_variables, marcar_rotura, transformar


def dos_series(dias=20):
    fechas = pd.date_range("2015-01-01", periods=dias, freq="D").strftime("%Y-%m-%d")
    filas = []
    for item, base in [("x", 10), ("y", 100)]:
        for k, f in enumerate(fechas):
            filas.append({"store_id": "A", "item_id": item, "date": f, "unidades": base + k, "sell_price": 1.0 + k / 10,
                          "d": f"d_{k}", "wm_yr_wk": 1, "event_name_2": None, "event_type_2": None})
    return pd.DataFrame(filas)


def caso_el_retardo_de_un_dia_es_la_venta_de_ayer():
    v = generar_variables(dos_series())
    x = v[v["item_id"] == "x"].reset_index(drop=True)
    assert (x["unidades_lag_1"].iloc[1:].to_numpy() == x["unidades"].iloc[:-1].to_numpy()).all()


def caso_ninguna_variable_mira_el_propio_dia():
    t = dos_series()
    antes = generar_variables(t)
    cambiada = t.copy()
    fila = cambiada.index[(cambiada["item_id"] == "x") & (cambiada["date"] == "2015-01-18")][0]
    cambiada.loc[fila, "unidades"] = 9_999
    despues = generar_variables(cambiada)
    nuevas = [c for c in antes.columns if "_lag_" in c or c.startswith("unidades_m")]
    mismo_dia = (despues["item_id"] == "x") & (despues["date"] == "2015-01-18")
    assert np.allclose(antes.loc[mismo_dia, nuevas].to_numpy(dtype=float),
                       despues.loc[mismo_dia, nuevas].to_numpy(dtype=float), equal_nan=True)


def caso_un_retardo_no_cruza_de_serie():
    v = generar_variables(dos_series())
    primera_y = v[(v["item_id"] == "y")].iloc[0]
    assert pd.isna(primera_y["unidades_lag_1"])


def caso_la_marca_de_rotura_cuenta_dias_seguidos_a_cero():
    m = marcar_rotura(pd.Series([0, 0, 0, 5, 0, 0]), 3).tolist()
    assert m == [0, 0, 1, 0, 0, 0]


def caso_salen_las_filas_sin_15_dias_de_historia():
    t, quitadas = transformar(dos_series())
    assert quitadas == 30 and len(t) == 10


def caso_la_media_del_mes_distingue_los_meses():
    # Dos años de una serie que vende 10 en enero y 100 en julio: cada mes tiene 62 días, menos que los 100 que pedía
    # el suavizado de la versión anterior, y con aquel valor las dos medias salían casi iguales a la media general.
    fechas = pd.date_range("2013-01-01", "2014-12-31", freq="D")
    t = pd.DataFrame({"date": fechas.strftime("%Y-%m-%d"), "month": fechas.month, "wday": fechas.dayofweek,
                      "weekday": fechas.day_name(), "event_name_1": None})
    t["unidades"] = np.where(t["month"] == 1, 10.0, np.where(t["month"] == 7, 100.0, 50.0))
    media = ajustar_codificadores(t)["media"]["month"]["media"]
    assert media["7"] - media["1"] > 80, f"enero {media['1']:.2f}, julio {media['7']:.2f}"


if __name__ == "__main__":
    lanzar([caso_el_retardo_de_un_dia_es_la_venta_de_ayer, caso_ninguna_variable_mira_el_propio_dia,
            caso_un_retardo_no_cruza_de_serie, caso_la_marca_de_rotura_cuenta_dias_seguidos_a_cero,
            caso_salen_las_filas_sin_15_dias_de_historia, caso_la_media_del_mes_distingue_los_meses])
