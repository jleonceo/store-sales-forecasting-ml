"""Comprueba que los resultados que deja el proceso son los esperados, con una tolerancia de 0,05 unidades.

Las cifras esperadas están en `tests/cifras_de_referencia.json`. Se calcularon una vez por un camino independiente
(otra implementación de la misma cadena) y aquí se comparan con lo que acaba de salir. Además comprueba la forma de
la simulación: 31 mañanas, ninguna previsión medida con una venta que no existe.
"""

import json

import pandas as pd
from comun import RAIZ, lanzar

TOLERANCIA = 0.05
RESULTADOS = RAIZ / "informes" / "resultados.json"
REFERENCIA = RAIZ / "tests" / "cifras_de_referencia.json"
SALIDAS = RAIZ / "produccion" / "salidas"


def cifras():
    return (json.loads(RESULTADOS.read_text(encoding="utf-8")), json.loads(REFERENCIA.read_text(encoding="utf-8")))


def cerca(obtenida, esperada, nombre):
    assert abs(obtenida - esperada) <= TOLERANCIA, f"{nombre}: {obtenida} frente a {esperada}"


def caso_datos():
    r, e = cifras()
    for k, v in e["datos"].items():
        assert r["datos"][k] == v, f"datos, {k}: {r['datos'][k]} frente a {v}"


def caso_validacion():
    r, e = cifras()
    cerca(r["validacion"]["error"], e["validacion"]["error"], "validación, modelo")
    cerca(r["validacion"]["referencia"], e["validacion"]["referencia"], "validación, regla")
    assert r["validacion"]["series_mejor"] == e["validacion"]["series_mejor"]


def caso_un_dia_vista():
    r, e = cifras()
    cerca(r["un_dia"]["error"], e["un_dia"]["error"], "un día, modelo")
    cerca(r["un_dia"]["referencia"], e["un_dia"]["referencia"], "un día, regla")
    assert r["un_dia"]["series_mejor"] == e["un_dia"]["series_mejor"]


def caso_ocho_dias_vista():
    r, e = cifras()
    for k in ["error", "referencia"]:
        cerca(r["ocho_dias"][k], e["ocho_dias"][k], f"ocho días, {k}")
        cerca(r["ocho_dias"]["total"][k], e["ocho_dias"]["total"][k], f"ocho días total, {k}")
    assert r["ocho_dias"]["series_mejor"] == e["ocho_dias"]["series_mejor"]


def caso_backtest():
    r, e = cifras()
    for k in ["error", "referencia"]:
        cerca(r["backtest"][k], e["backtest"][k], f"backtest, {k}")
    assert r["backtest"]["bloques_mejor"] == e["backtest"]["bloques_mejor"]


def caso_simulacion_de_31_mananas():
    registro = pd.read_csv(SALIDAS / "registro.csv")
    assert len(registro) == 31 and registro["dia"].is_unique
    assert len([p for p in SALIDAS.iterdir() if p.is_dir()]) == 31


def caso_ninguna_prevision_medida_con_una_venta_que_no_existe():
    for carpeta in sorted(p for p in SALIDAS.iterdir() if p.is_dir()):
        ev = json.loads((carpeta / "evaluacion.json").read_text(encoding="utf-8"))
        p = pd.read_csv(carpeta / "prevision.csv", dtype={"date": str})
        assert p["date"].max() <= "2015-12-31" and p["date"].min() >= carpeta.name
        assert ev["medidas"] + ev["sin_medir"] == len(p)


if __name__ == "__main__":
    lanzar([caso_datos, caso_validacion, caso_un_dia_vista, caso_ocho_dias_vista, caso_backtest, caso_simulacion_de_31_mananas,
            caso_ninguna_prevision_medida_con_una_venta_que_no_existe])
