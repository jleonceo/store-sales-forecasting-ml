"""Reproduce el proyecto entero desde las dos bases de `datos/`.

1. Pruebas unitarias (datos, variables, producción y que ningún fichero lleva rutas ni nombres internos).
2. Simulación de diciembre: reentrena con las ventas hasta el 30/11/2015 y ejecuta las 31 mañanas.
3. Resultados y gráficos.
4. Pruebas de resultados: las cifras de la portada contra lo que acaba de salir.

Con `--backtest`, añade antes la prueba desde 12 fechas de 2015, que tarda entre una y dos horas. Sin él, usa el
`informes/backtest.json` que ya está en el repositorio.

Uso:  python ejecutar_todo.py [--backtest]
"""

import argparse
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
UNITARIAS = ["tests/probar_sin_origen.py", "tests/probar_datos.py", "tests/probar_variables.py",
             "tests/probar_produccion.py", "tests/probar_evaluar.py"]
DE_RESULTADOS = ["tests/probar_resultados.py", "tests/probar_portada.py"]


def paso(script, *argumentos):
    """Ejecuta un script con el mismo Python y para todo si falla."""
    print(f"\n=== {script} {' '.join(argumentos)}", flush=True)
    r = subprocess.run([sys.executable, "-W", "error", str(RAIZ / script), *argumentos], cwd=RAIZ)
    if r.returncode != 0:
        sys.exit(f"PARADO: {script} terminó con {r.returncode}")


if __name__ == "__main__":
    argumentos = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    argumentos.add_argument("--backtest", action="store_true", help="repetir también la prueba desde 12 fechas")
    con_backtest = argumentos.parse_args().backtest
    for prueba in UNITARIAS:
        paso(prueba)
    if con_backtest:
        paso("scripts/backtest.py")
    paso("produccion/simular_diciembre.py")
    paso("scripts/resultados.py")
    paso("scripts/graficos.py")
    for prueba in DE_RESULTADOS:
        paso(prueba)
    print("\nOK: todo reproducido y comprobado")
