"""Comprueba que cada cifra con decimales de las dos portadas sale de `informes/resultados.json`, y que las cifras
principales están en las dos.

Una cifra escrita a mano que no está en los resultados, o que se quedó de una versión anterior, hace fallar la
prueba. En `README.md` las cifras van con coma decimal y en `README.en.md`, con punto.
"""

import json
import re

from comun import RAIZ, lanzar

RESULTADOS = RAIZ / "informes" / "resultados.json"
PORTADAS = {"README.md": ",", "README.en.md": "."}
# Las cifras que tienen que estar en las dos portadas, con sus decimales
PRINCIPALES = [("un_dia.error", 2), ("un_dia.referencia", 2), ("ocho_dias.total.error", 2),
               ("ocho_dias.total.referencia", 2), ("backtest.error", 2), ("backtest.referencia", 2)]


def hojas(d, prefijo=""):
    """Todas las cifras del JSON, con su ruta."""
    if isinstance(d, dict):
        for k, v in d.items():
            yield from hojas(v, f"{prefijo}{k}.")
    elif isinstance(d, (int, float)) and not isinstance(d, bool):
        yield prefijo[:-1], float(d)


def formatos(valor, separador):
    """El valor escrito con 1 y 2 decimales, con el separador decimal pedido."""
    return {f"{valor:.{k}f}".replace(".", separador) for k in (1, 2)}


def valor(d, ruta):
    for k in ruta.split("."):
        d = d[k]
    return float(d)


def permitidas(separador):
    d = json.loads(RESULTADOS.read_text(encoding="utf-8"))
    salida = set()
    for _, v in hojas(d):
        salida |= formatos(v, separador)
    return d, salida


def caso_cada_cifra_de_las_portadas_sale_de_los_resultados():
    for portada, sep in PORTADAS.items():
        texto = (RAIZ / portada).read_text(encoding="utf-8")
        _, validas = permitidas(sep)
        validas |= {"3.13", "3,13"}  # la versión de Python
        patron = r"(?<![\d.,])\d+" + re.escape(sep) + r"\d{1,2}(?![\d])"
        sueltas = [c for c in re.findall(patron, texto) if c not in validas]
        assert not sueltas, f"{portada}: cifras que no están en los resultados: {sueltas}"


def caso_las_cifras_principales_estan_en_las_dos_portadas():
    for portada, sep in PORTADAS.items():
        texto = (RAIZ / portada).read_text(encoding="utf-8")
        d, _ = permitidas(sep)
        faltan = [r for r, k in PRINCIPALES if f"{valor(d, r):.{k}f}".replace(".", sep) not in texto]
        assert not faltan, f"{portada}: faltan {faltan}"


if __name__ == "__main__":
    lanzar([caso_cada_cifra_de_las_portadas_sale_de_los_resultados,
            caso_las_cifras_principales_estan_en_las_dos_portadas])
