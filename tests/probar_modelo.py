"""Pruebas de la búsqueda de hiperparámetros (los candidatos incluyen siempre los valores por defecto) y de las
referencias del backtest (solo usan lo que se conocía en el origen)."""

import pandas as pd
from comun import lanzar
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import ParameterSampler

from forecast import SEMILLA
from forecast.modelo import CANDIDATOS, REJILLA, candidatos, variables_utiles
from forecast.prevision import media_mismo_dia, media_ultimos_dias


def caso_el_candidato_por_defecto_siempre_entra():
    defecto = HistGradientBoostingRegressor().get_params()
    esperado = {k: defecto[k] for k in REJILLA}
    assert esperado in candidatos(), "los valores por defecto no están entre los candidatos"


def caso_los_sorteados_son_los_de_siempre():
    # Los 10 sorteados son los mismos que antes del cambio: solo se añade uno
    sorteados = list(ParameterSampler(REJILLA, CANDIDATOS, random_state=SEMILLA))
    assert candidatos()[:CANDIDATOS] == sorteados and len(candidatos()) == CANDIDATOS + 1


def reales_de_prueba():
    # Una serie que vende el número del día del mes: el 1 vende 1, el 2 vende 2...
    fechas = pd.date_range("2015-01-01", "2015-02-28", freq="D")
    return {("s", f.strftime("%Y-%m-%d")): f.day for f in fechas}


def caso_la_media_de_7_dias_solo_usa_lo_conocido():
    # Origen el 31/01: los 7 últimos días son del 25 al 31, media 28
    assert media_ultimos_dias(reales_de_prueba(), "s", "2015-01-31") == 28.0


def caso_la_media_de_4_semanas_salta_lo_que_no_se_conocia():
    # Origen el 31/01 y día previsto el 10/02: el mismo día de la semana más reciente conocido es el 27/01
    # (14 días antes); las cuatro semanas son el 27, 20, 13 y 6 de enero, media 16,5
    assert media_mismo_dia(reales_de_prueba(), "s", "2015-02-10", "2015-01-31") == 16.5


def caso_solo_entran_variables_que_el_arbol_puede_usar():
    # Una columna constante y un evento de 3 días no los puede cortar ningún árbol con hojas de 10 días o más
    n = 100
    x = pd.DataFrame({"constante": [1.0] * n, "event_name_1_Raro": [1.0] * 3 + [0.0] * (n - 3),
                      "event_name_1_Sin_evento": [0.0] * 15 + [1.0] * (n - 15), "unidades_lag_1": range(n)})
    assert variables_utiles(x) == ["event_name_1_Sin_evento", "unidades_lag_1"], variables_utiles(x)


if __name__ == "__main__":
    lanzar([caso_solo_entran_variables_que_el_arbol_puede_usar,
            caso_el_candidato_por_defecto_siempre_entra, caso_los_sorteados_son_los_de_siempre,
            caso_la_media_de_7_dias_solo_usa_lo_conocido, caso_la_media_de_4_semanas_salta_lo_que_no_se_conocia])
