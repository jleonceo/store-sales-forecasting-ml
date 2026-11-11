"""Pruebas de `produccion/evaluar.py` con una previsión pequeña escrita aquí y cifras calculadas a mano.

Una serie con ventas de 10 × día del 01/12 al 10/12. La previsión de la mañana del 08/12 dice 80, 95, 100 y 50 para
los días 8 a 11. Real: 80, 90 y 100; el 11 aún no tiene venta. Error del modelo: (0 + 5 + 0) / 3 = 1,67. Referencia
desde el origen del 07/12: la venta del 01, 02 y 03, es decir 10, 20 y 30; error (70 + 70 + 70) / 3 = 70.
"""

import json
import tempfile
from pathlib import Path

import pandas as pd
from comun import lanzar
from evaluar import evaluar


def total():
    fechas = pd.date_range("2015-12-01", "2015-12-10").strftime("%Y-%m-%d")
    return pd.DataFrame({"store_id": "A", "item_id": "x", "date": fechas, "unidades": [10 * (k + 1) for k in range(10)]})


def preparar(carpeta, previsiones=(80, 95, 100, 50)):
    (carpeta / "2015-12-08").mkdir(parents=True)
    fechas = ["2015-12-08", "2015-12-09", "2015-12-10", "2015-12-11"]
    pd.DataFrame({"serie": "A · x", "store_id": "A", "item_id": "x", "date": fechas, "horizonte": [1, 2, 3, 4],
                  "prevision": list(previsiones)}).to_csv(carpeta / "2015-12-08" / "prevision.csv", index=False)


def con_carpeta(funcion):
    with tempfile.TemporaryDirectory() as d:
        carpeta = Path(d)
        return funcion(carpeta)


def caso_error_del_modelo_y_de_la_referencia_a_mano():
    def f(c):
        preparar(c)
        d = evaluar("2015-12-08", total=total(), carpeta=c)
        assert abs(d["total"]["error"] - 5 / 3) < 1e-9 and d["total"]["referencia"] == 70
    con_carpeta(f)


def caso_el_dia_sin_venta_real_queda_sin_medir():
    def f(c):
        preparar(c)
        d = evaluar("2015-12-08", total=total(), carpeta=c)
        assert d["medidas"] == 3 and d["sin_medir"] == 1 and "2015-12-11" not in d["por_dia"]
    con_carpeta(f)


def caso_una_prevision_peor_da_un_error_mayor():
    def f(c):
        preparar(c, previsiones=(0, 0, 0, 0))
        d = evaluar("2015-12-08", total=total(), carpeta=c)
        assert d["total"]["error"] == 90 and d["total"]["error"] > d["total"]["referencia"]
    con_carpeta(f)


def caso_sin_ninguna_venta_real_no_inventa_un_error():
    def f(c):
        preparar(c)
        corto = total()
        corto = corto[corto["date"] <= "2015-12-07"]
        d = evaluar("2015-12-08", total=corto, carpeta=c)
        assert d["medidas"] == 0 and "total" not in d
        assert json.loads((c / "2015-12-08" / "evaluacion.json").read_text(encoding="utf-8"))["sin_medir"] == 4
    con_carpeta(f)


if __name__ == "__main__":
    lanzar([caso_error_del_modelo_y_de_la_referencia_a_mano, caso_el_dia_sin_venta_real_queda_sin_medir,
            caso_una_prevision_peor_da_un_error_mayor, caso_sin_ninguna_venta_real_no_inventa_un_error])
