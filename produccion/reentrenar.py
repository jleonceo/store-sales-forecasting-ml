"""Reentrena los 20 modelos con las ventas hasta una fecha, sin pisar los que están en uso.

Entrena en `modelos/candidato/` y lo compara con `modelos/vigente/` por su error de validación. Si el candidato no es
peor (con la tolerancia de `config.json`), pasa a vigente y el anterior se guarda en `modelos/anteriores/`. Si es peor,
el vigente sigue en uso y el candidato se queda para revisarlo. Las rutas y la fecha por defecto salen de
`produccion/config.json`.

Uso:  python produccion/reentrenar.py [--hasta AAAA-MM-DD]
"""

import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from forecast.datos import historia_y_diciembre  # noqa: E402
from forecast.modelo import entrenar  # noqa: E402
from forecast.prevision import nombre_serie  # noqa: E402
from forecast.produccion import carpetas_modelos, config, guardar_modelos, huella, promover  # noqa: E402
from forecast.variables import transformar  # noqa: E402


def reentrenar(hasta=None, c=None):
    """Entrena el candidato con las ventas hasta `hasta` y decide si pasa a vigente; devuelve la decisión."""
    c = c or config()
    hasta = hasta or c["entrenar_hasta"]
    _, _, total = historia_y_diciembre(c["datos_historia"], c["datos_nuevos"])
    trans, _ = transformar(total[total["date"] <= hasta])
    trans["serie"] = nombre_serie(trans)
    modelos, validacion = entrenar(trans, hasta, aviso=print)
    huellas = {p.name: huella(p) for p in [c["datos_historia"], c["datos_nuevos"]]}
    guardar_modelos(modelos, validacion, hasta, huellas, carpetas_modelos(c)[1])
    return promover(c) | {"entrenado_hasta": hasta}


if __name__ == "__main__":
    argumentos = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    argumentos.add_argument("--hasta", default=None, help="último día de ventas con que se entrena")
    d = reentrenar(argumentos.parse_args().hasta)
    estado = "pasa a vigente" if d["promovido"] else "NO pasa a vigente"
    print(f"OK: candidato entrenado hasta el {d['entrenado_hasta']}, validación {d['nuevo']:.2f}; {estado} "
          f"({d['motivo']})")
