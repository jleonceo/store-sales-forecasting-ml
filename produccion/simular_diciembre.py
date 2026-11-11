"""Simula un mes de funcionamiento: las 31 mañanas de diciembre de 2015, una detrás de otra.

1. Reentrena con las ventas hasta el 30/11/2015 (sin pisar el modelo vigente si el nuevo valida peor).
2. Para cada mañana del 01/12 al 31/12, ejecuta la previsión con las ventas conocidas hasta la víspera, como haría el
   proceso diario: cada día llega una venta más y la previsión se rehace.
3. Mide cada previsión con lo que se vendió y escribe el registro de las 31 mañanas.
4. Comprueba el despliegue de principio a fin y escribe `informes/despliegue.json`: que no falte ninguna mañana (aviso
   por ausencia), que la mañana del 24/12 da las cifras de la prueba final y que cada día nuevo cambia la previsión.

Diciembre ya se usó como prueba final del modelo: esta simulación demuestra cómo funciona el proceso día a día, no es
una prueba nueva. Las salidas de una simulación anterior se borran al empezar, porque se regeneran enteras.

Uso:  python produccion/simular_diciembre.py [--sin-reentrenar]
"""

import argparse
import csv
import json
import shutil
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "produccion"))

from evaluar import evaluar  # noqa: E402
from prever import prever  # noqa: E402
from reentrenar import reentrenar  # noqa: E402

from forecast.datos import historia_y_diciembre  # noqa: E402
from forecast.produccion import cargar_modelos, config  # noqa: E402

CAMPOS = ["dia", "previsiones", "dias_previstos", "medidas", "error_modelo", "error_referencia", "mejor_que_referencia"]
REFERENCIA = RAIZ / "tests" / "cifras_de_referencia.json"
DIA_CONTROL = "2015-12-24"


def cambia_con_el_dia_nuevo(salidas, dia_a, dia_b):
    """Cuántas previsiones de los días comunes cambian entre la mañana `dia_a` y la siguiente, `dia_b`."""
    a = pd.read_csv(salidas / dia_a / "prevision.csv", dtype={"date": str})
    b = pd.read_csv(salidas / dia_b / "prevision.csv", dtype={"date": str})
    juntas = a.merge(b, on=["serie", "date"], suffixes=("_a", "_b"))
    return int((juntas["prevision_a"] != juntas["prevision_b"]).sum()), int(len(juntas))


def simular(reentrenar_antes=True):
    """Las mañanas de la ventana de `config.json`; devuelve el informe del despliegue."""
    c = config()
    mananas = pd.date_range(c["simulacion"]["desde"], c["simulacion"]["hasta"]).strftime("%Y-%m-%d").tolist()
    decision = reentrenar(c=c) if reentrenar_antes else None
    modelos, manifiesto = cargar_modelos()
    _, _, total = historia_y_diciembre(c["datos_historia"], c["datos_nuevos"])
    if c["salidas"].exists():
        shutil.rmtree(c["salidas"])
    for dia in mananas:
        p = prever(dia, total=total, modelos=modelos, manifiesto=manifiesto, c=c)
        print(f"{dia}: {len(p)} previsiones", flush=True)

    # Aviso por ausencia: tienen que estar todas las mañanas de la ventana, en OK
    ejecuciones = pd.read_csv(c["salidas"] / "ejecuciones.csv", dtype={"dia": str})
    hechas = set(ejecuciones.loc[ejecuciones["estado"] == "OK", "dia"])
    faltan = [d for d in mananas if d not in hechas]

    filas = []
    for dia in mananas:
        d = evaluar(dia, total=total, carpeta=c["salidas"])
        resumen = json.loads((c["salidas"] / dia / "resumen.json").read_text(encoding="utf-8"))
        filas.append({"dia": dia, "previsiones": d["previsiones"], "dias_previstos": resumen["dias_previstos"],
                      "medidas": d["medidas"], "error_modelo": round(d["total"]["error"], 4),
                      "error_referencia": round(d["total"]["referencia"], 4),
                      "mejor_que_referencia": d["total"]["error"] < d["total"]["referencia"]})
    with (c["salidas"] / "registro.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        w.writeheader()
        w.writerows(filas)

    # Prueba de principio a fin: la mañana de control da las cifras de la prueba final, y un día nuevo cambia la
    # previsión de los días que ya estaban previstos
    esperado = json.loads(REFERENCIA.read_text(encoding="utf-8"))["ocho_dias"]
    control = json.loads((c["salidas"] / DIA_CONTROL / "evaluacion.json").read_text(encoding="utf-8"))["total"]
    coincide = (abs(control["error"] - esperado["error"]) <= 0.05
                and abs(control["referencia"] - esperado["referencia"]) <= 0.05)
    cambian, comunes = cambia_con_el_dia_nuevo(c["salidas"], "2015-12-23", DIA_CONTROL)
    informe = {
        "forma": "proceso por lotes",
        "configuracion": "produccion/config.json",
        "programacion": c["programacion"],
        "avisos": c["avisos"],
        "vuelta_atras": {"modelo": "python produccion/volver_atras.py", "codigo": "git checkout <etiqueta>"},
        "reentreno": decision,
        "modelo_en_uso": {"entrenado_hasta": manifiesto["entrenado_hasta"], "fecha": manifiesto["fecha"],
                          "error_validacion": manifiesto["error_validacion"]},
        "ventana": {"desde": mananas[0], "hasta": mananas[-1], "esperadas": len(mananas), "hechas": len(hechas),
                    "faltan": faltan},
        "prueba_de_principio_a_fin": {
            "datos": "diciembre de 2015, que no se usó para entrenar",
            "control": {"manana": DIA_CONTROL, "error": control["error"], "referencia": control["referencia"],
                        "esperado": {"error": esperado["error"], "referencia": esperado["referencia"]},
                        "coincide": coincide},
            "dia_nuevo_cambia_la_prevision": {"entre": ["2015-12-23", DIA_CONTROL], "previsiones_comunes": comunes,
                                              "cambian": cambian},
            "resultado": "OK" if (coincide and not faltan and cambian > 0) else "ERROR"},
    }
    c["informe_despliegue"].parent.mkdir(exist_ok=True)
    c["informe_despliegue"].write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
    return informe, filas


if __name__ == "__main__":
    argumentos = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    argumentos.add_argument("--sin-reentrenar", action="store_true", help="usar el modelo vigente sin reentrenar")
    informe, filas = simular(not argumentos.parse_args().sin_reentrenar)
    p = informe["prueba_de_principio_a_fin"]
    if informe["ventana"]["faltan"]:
        sys.exit(f"ERROR: faltan ejecuciones (aviso por ausencia): {informe['ventana']['faltan']}")
    if p["resultado"] != "OK":
        sys.exit(f"ERROR: la prueba de principio a fin no pasa: {json.dumps(p, ensure_ascii=False)}")
    mejores = sum(f["mejor_que_referencia"] for f in filas)
    print(f"OK: {len(filas)} mañanas simuladas, ninguna falta; el modelo mejora la referencia en {mejores}; "
          f"control del {DIA_CONTROL}: {p['control']['error']:.4f} frente a {p['control']['referencia']:.4f}")
