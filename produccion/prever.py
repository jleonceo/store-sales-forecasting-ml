"""La ejecución de una mañana: prevé las ventas de cada tienda y producto para los 8 días desde `--dia`.

Toma las ventas conocidas hasta la víspera (las de `--dia` en adelante se borran antes de nada, para que no se puedan
usar) y comprueba los datos del día: todas las series, la venta de la víspera en todas y el calendario y el precio del
propio día. Si algo falla, para sin dejar previsión, anota el motivo en el registro de ejecuciones y termina con error.

Deja, en `<salidas>/<dia>/`, `prevision.csv` y `resumen.json` (filas, huella de la entrada, modelo usado, duración y
estado). Si esa mañana ya se había ejecutado, la carpeta anterior se archiva antes. Si la base no trae calendario y
precio de los 8 días, prevé los que haya y lo dice.

Uso:  python produccion/prever.py --dia 2015-12-24
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from forecast.datos import historia_y_diciembre  # noqa: E402
from forecast.prevision import prever_desde  # noqa: E402
from forecast.produccion import (EntradaIncorrecta, anotar_ejecucion, cargar_modelos, comprobar_dia,  # noqa: E402
                                 config, huella_tabla, preparar_salida, ventas_conocidas_hasta)

COLUMNAS_SALIDA = ["serie", "store_id", "item_id", "date", "horizonte", "prevision"]


def prever(dia, total=None, modelos=None, manifiesto=None, c=None):
    """Prevé desde la víspera de `dia` y guarda la previsión y su resumen; devuelve la previsión.

    Si los datos del día no cumplen el contrato, anota el error y lanza `EntradaIncorrecta` sin dejar previsión.
    """
    c = c or config()
    inicio = time.perf_counter()
    momento = datetime.now().isoformat(timespec="seconds")
    if total is None:
        _, _, total = historia_y_diciembre(c["datos_historia"], c["datos_nuevos"])
    if modelos is None:
        modelos, manifiesto = cargar_modelos()
    tabla = ventas_conocidas_hasta(total, dia)
    try:
        comprobar_dia(tabla, dia, c["series_esperadas"])
    except EntradaIncorrecta as e:
        anotar_ejecucion(c["salidas"], {"dia": dia, "momento": momento, "estado": "ERROR",
                                        "duracion_s": round(time.perf_counter() - inicio, 2), "previsiones": 0,
                                        "motivo": str(e)})
        raise
    origen = (pd.Timestamp(dia) - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    p = prever_desde(tabla, modelos, origen, c["dias_a_prever"])[COLUMNAS_SALIDA]
    carpeta = preparar_salida(c["salidas"] / dia)
    p.to_csv(carpeta / "prevision.csv", index=False)
    duracion = round(time.perf_counter() - inicio, 2)
    dias = int(p["date"].nunique())
    resumen = {"dia": dia, "momento": momento, "estado": "OK", "duracion_s": duracion,
               "filas_entrada": int(len(tabla[tabla["date"] < dia])), "huella_entrada": huella_tabla(tabla),
               "series": int(p["serie"].nunique()), "previsiones": int(len(p)), "dias_previstos": dias,
               "dias_pedidos": c["dias_a_prever"],
               "aviso": None if dias == c["dias_a_prever"] else
               f"la base solo trae calendario y precio de {dias} de los {c['dias_a_prever']} días",
               "modelo": {"entrenado_hasta": manifiesto["entrenado_hasta"], "fecha": manifiesto["fecha"]}}
    (carpeta / "resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    anotar_ejecucion(c["salidas"], {"dia": dia, "momento": momento, "estado": "OK", "duracion_s": duracion,
                                    "previsiones": len(p), "motivo": resumen["aviso"] or ""})
    return p


if __name__ == "__main__":
    argumentos = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    argumentos.add_argument("--dia", required=True, help="la mañana en que se ejecuta, AAAA-MM-DD")
    dia = argumentos.parse_args().dia
    try:
        p = prever(dia)
    except EntradaIncorrecta as e:
        sys.exit(f"ERROR: la ejecución del {dia} se para: {e}")
    print(f"OK: {len(p)} previsiones para {p['serie'].nunique()} series y {p['date'].nunique()} días desde el {dia}")
