"""Pruebas de la lectura y del montaje de la tabla diaria, con datos pequeños escritos aquí y con la base real."""

import pandas as pd
from comun import esperar_error, lanzar

from forecast import BASE_DICIEMBRE, BASE_HISTORIA
from forecast.datos import (CruceIncorrecto, comprobar_continuidad, cruzar, despivotar, historia_y_diciembre,
                            rellenar_precio)


def ventas_pequenas():
    return pd.DataFrame({"store_id": ["A", "A"], "item_id": ["x", "y"], "d_1": [1, 0], "d_2": [3, 5]})


def caso_despivotar_conserva_las_unidades():
    largo = despivotar(ventas_pequenas())
    assert len(largo) == 4 and largo["unidades"].sum() == 9


def caso_cruce_para_si_el_maestro_repite_claves():
    largo = despivotar(ventas_pequenas())
    maestro = pd.DataFrame({"d": ["d_1", "d_1", "d_2"], "date": ["2015-01-01", "2015-01-01", "2015-01-02"]})
    esperar_error(lambda: cruzar(largo, maestro, ["d"]), CruceIncorrecto)


def caso_precio_que_falta_toma_la_moda_del_producto():
    t = pd.DataFrame({"item_id": ["x", "x", "x", "y"], "sell_price": [2.0, 2.0, None, 1.0]})
    r = rellenar_precio(t)
    assert r.loc[2, "sell_price"] == 2.0 and bool(r.loc[2, "sell_price_faltante"])
    assert int(r["sell_price_faltante"].sum()) == 1


def caso_continuidad_para_con_un_hueco():
    t = pd.DataFrame({"store_id": ["A"] * 3, "item_id": ["x"] * 3, "date": ["2015-01-01", "2015-01-02", "2015-01-04"]})
    esperar_error(lambda: comprobar_continuidad(t), CruceIncorrecto)


def caso_base_real_da_las_cifras_conocidas():
    historia, diciembre, total = historia_y_diciembre(BASE_HISTORIA, BASE_DICIEMBRE)
    assert len(historia) == 21_280 and int(historia["unidades"].sum()) == 614_451
    assert len(diciembre) == 620 and int(historia["sell_price_faltante"].sum()) == 71
    assert total["date"].min() == "2013-01-01" and total["date"].max() == "2015-12-31"


if __name__ == "__main__":
    lanzar([caso_despivotar_conserva_las_unidades, caso_cruce_para_si_el_maestro_repite_claves,
            caso_precio_que_falta_toma_la_moda_del_producto, caso_continuidad_para_con_un_hueco,
            caso_base_real_da_las_cifras_conocidas])
