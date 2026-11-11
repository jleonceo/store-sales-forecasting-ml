"""Pruebas del proceso por lotes: el contrato de entrada, que la previsión no ve ventas del futuro, la referencia y
que los modelos no se cargan con otras versiones."""

import json
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from comun import esperar_error, lanzar

from forecast.prevision import prever_desde, referencia
from forecast.produccion import (EntradaIncorrecta, cargar_modelos, carpetas_modelos, comprobar_dia,
                                 guardar_modelos, preparar_salida, promover, validar_entrada, ventas_conocidas_hasta,
                                 volver_atras)


class ModeloDeAyer:
    """Un modelo mínimo para probar la previsión: prevé la venta de ayer."""
    feature_names_in_ = np.array(["unidades_lag_1"])

    def predict(self, x):
        return x["unidades_lag_1"].to_numpy(dtype=float)


def tabla(dias=30):
    fechas = pd.date_range("2015-12-01", periods=dias, freq="D").strftime("%Y-%m-%d")
    filas = [{"store_id": "A", "item_id": "x", "d": f"d_{k}", "unidades": 10 + k, "date": f, "wm_yr_wk": 1,
              "weekday": "Monday", "wday": 3, "month": 12, "year": 2015, "event_name_1": "Sin_evento",
              "event_type_1": "Sin_evento", "event_name_2": None, "event_type_2": None, "sell_price": 1.0,
              "sell_price_faltante": False} for k, f in enumerate(fechas)]
    return pd.DataFrame(filas)


def modelos():
    cod = {"una_por_valor": {}, "media": {}}
    return {"A · x": (ModeloDeAyer(), cod, ["unidades_lag_1"])}


def caso_la_prevision_no_ve_las_ventas_del_futuro():
    t = tabla()
    a = prever_desde(ventas_conocidas_hasta(t, "2015-12-20"), modelos(), "2015-12-19")
    cambiada = t.copy()
    cambiada.loc[cambiada["date"] >= "2015-12-20", "unidades"] = 5_000
    b = prever_desde(ventas_conocidas_hasta(cambiada, "2015-12-20"), modelos(), "2015-12-19")
    assert a["prevision"].tolist() == b["prevision"].tolist()


def caso_la_prevision_es_recursiva():
    p = prever_desde(ventas_conocidas_hasta(tabla(), "2015-12-20"), modelos(), "2015-12-19")
    # La venta del 19/12 es 28: el modelo de ayer la repite los 8 días, porque cada previsión pasa a ser historia
    assert len(p) == 8 and set(p["prevision"]) == {28}


def caso_la_referencia_usa_solo_lo_conocido_el_dia_del_origen():
    reales = {("s", f): k for k, f in enumerate(pd.date_range("2015-12-01", "2015-12-31").strftime("%Y-%m-%d"))}
    assert referencia(reales, "s", "2015-12-25", "2015-12-23") == reales[("s", "2015-12-18")]
    assert referencia(reales, "s", "2015-12-31", "2015-12-23") == reales[("s", "2015-12-17")]


def caso_contrato_para_si_falta_una_columna():
    esperar_error(lambda: validar_entrada(tabla().drop(columns="sell_price")), EntradaIncorrecta)


def caso_contrato_para_si_un_tipo_no_es_el_suyo():
    t = tabla()
    t["unidades"] = t["unidades"].astype(str)
    esperar_error(lambda: validar_entrada(t), EntradaIncorrecta)


def caso_contrato_para_con_un_dia_repetido_o_sin_precio():
    esperar_error(lambda: validar_entrada(pd.concat([tabla(), tabla().iloc[[0]]])), EntradaIncorrecta)
    t = tabla()
    t.loc[3, "sell_price"] = None
    esperar_error(lambda: validar_entrada(t), EntradaIncorrecta)


def caso_modelos_no_se_cargan_con_otra_version():
    with tempfile.TemporaryDirectory() as d:
        carpeta = Path(d)
        guardar_modelos(modelos(), {}, "2015-11-30", {}, carpeta)
        cargar_modelos(carpeta)
        m = json.loads((carpeta / "manifiesto.json").read_text(encoding="utf-8"))
        m["versiones"]["scikit-learn"] = "0.0.1"
        (carpeta / "manifiesto.json").write_text(json.dumps(m), encoding="utf-8")
        esperar_error(lambda: cargar_modelos(carpeta), RuntimeError)


def dos_series_hasta(dia):
    """Dos series con ventas hasta la víspera de `dia` y el calendario y el precio de los 8 días siguientes."""
    a = tabla()
    b = tabla().assign(item_id="y")
    return ventas_conocidas_hasta(pd.concat([a, b], ignore_index=True), dia)


def caso_el_dia_correcto_pasa():
    comprobar_dia(dos_series_hasta("2015-12-20"), "2015-12-20", 2)


def caso_el_dia_para_si_falta_una_serie():
    esperar_error(lambda: comprobar_dia(dos_series_hasta("2015-12-20"), "2015-12-20", 3), EntradaIncorrecta)


def caso_el_dia_para_si_la_ultima_venta_es_de_anteayer():
    t = dos_series_hasta("2015-12-20")
    t.loc[(t["item_id"] == "y") & (t["date"] == "2015-12-19"), "unidades"] = np.nan
    esperar_error(lambda: comprobar_dia(t, "2015-12-20", 2), EntradaIncorrecta)


def caso_el_dia_para_sin_calendario_del_propio_dia():
    t = dos_series_hasta("2015-12-20")
    t = t[t["date"] < "2015-12-20"]
    esperar_error(lambda: comprobar_dia(t, "2015-12-20", 2), EntradaIncorrecta)


def con_config(funcion):
    with tempfile.TemporaryDirectory() as d:
        c = {"modelos": Path(d), "reentreno": {"tolerancia": 0.05}}
        return funcion(c)


def guardar_con_error(c, carpeta, error):
    guardar_modelos(modelos(), {"A · x": {"error": error}}, "2015-11-30", {}, carpeta)


def caso_un_candidato_peor_no_sustituye_al_vigente():
    def f(c):
        vigente, candidato, _ = carpetas_modelos(c)
        guardar_con_error(c, vigente, 5.0)
        guardar_con_error(c, candidato, 6.0)
        d = promover(c)
        assert not d["promovido"] and json.loads((vigente / "manifiesto.json").read_text())["error_validacion"] == 5.0
    con_config(f)


def caso_un_candidato_igual_o_mejor_sustituye_y_se_puede_volver_atras():
    def f(c):
        vigente, candidato, anteriores = carpetas_modelos(c)
        guardar_con_error(c, vigente, 5.0)
        guardar_con_error(c, candidato, 4.0)
        assert promover(c)["promovido"]
        assert json.loads((vigente / "manifiesto.json").read_text())["error_validacion"] == 4.0
        assert len(list(anteriores.iterdir())) == 1
        volver_atras(c)
        assert json.loads((vigente / "manifiesto.json").read_text())["error_validacion"] == 5.0
    con_config(f)


def caso_una_manana_repetida_archiva_la_anterior():
    with tempfile.TemporaryDirectory() as d:
        carpeta = Path(d) / "2015-12-20"
        preparar_salida(carpeta)
        (carpeta / "prevision.csv").write_text("primera", encoding="utf-8")
        preparar_salida(carpeta)
        archivadas = list((Path(d) / "_archivo").iterdir())
        assert not (carpeta / "prevision.csv").exists() and len(archivadas) == 1
        assert (archivadas[0] / "prevision.csv").read_text(encoding="utf-8") == "primera"


if __name__ == "__main__":
    lanzar([caso_el_dia_correcto_pasa, caso_el_dia_para_si_falta_una_serie,
            caso_el_dia_para_si_la_ultima_venta_es_de_anteayer, caso_el_dia_para_sin_calendario_del_propio_dia,
            caso_un_candidato_peor_no_sustituye_al_vigente,
            caso_un_candidato_igual_o_mejor_sustituye_y_se_puede_volver_atras,
            caso_una_manana_repetida_archiva_la_anterior,caso_la_prevision_no_ve_las_ventas_del_futuro, caso_la_prevision_es_recursiva,
            caso_la_referencia_usa_solo_lo_conocido_el_dia_del_origen, caso_contrato_para_si_falta_una_columna,
            caso_contrato_para_si_un_tipo_no_es_el_suyo, caso_contrato_para_con_un_dia_repetido_o_sin_precio,
            caso_modelos_no_se_cargan_con_otra_version])
