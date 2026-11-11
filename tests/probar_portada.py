"""Comprueba que cada cifra con decimales, cada recuento «N de M» y cada porcentaje de las dos portadas sale de
`informes/resultados.json`, y que las cifras principales están en las dos.

Una cifra escrita a mano que no está en los resultados, o que se quedó de una versión anterior, hace fallar la
prueba. En `README.md` las cifras van con coma decimal y en `README.en.md`, con punto.
"""

import json
import re

from comun import RAIZ, lanzar

RESULTADOS = RAIZ / "informes" / "resultados.json"
PORTADAS = {"README.md": ",", "README.en.md": "."}
# Las cifras que tienen que estar en las dos portadas, con sus decimales
PRINCIPALES = [("diciembre_entero.un_dia.error", 2), ("diciembre_entero.un_dia.referencia", 2), ("ocho_dias.total.error", 2),
               ("ocho_dias.total.referencia", 2), ("backtest.error", 2), ("backtest.referencia", 2)]
# Las medidas que la portada cita como «el error es un N % menor»
PORCENTAJES = ["un_dia", "diciembre_entero.un_dia", "ocho_dias.total", "backtest", "validacion"]


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


def recuentos(d):
    """Los pares «cuántas gana, de cuántas» del JSON: cada clave `x_mejor` con su `x`, y `mejor_que_referencia` con
    `mananas`."""
    pares = set()
    if isinstance(d, dict):
        for k, v in d.items():
            if k.endswith("_mejor") and k[:-6] in d:
                pares.add((int(v), int(d[k[:-6]])))
            pares |= recuentos(v)
        if "mejor_que_referencia" in d and "mananas" in d:
            pares.add((int(d["mejor_que_referencia"]), int(d["mananas"])))
    return pares


def porcentajes(d):
    """Cuánto menos se equivoca el modelo que la referencia, en porcentaje entero, en las medidas que la portada puede
    citar en porcentaje. Se limitan a una lista para que un porcentaje equivocado no encuentre por casualidad otra
    pareja de cifras que lo dé."""
    salida = set()
    for ruta in PORCENTAJES:
        m = d
        for k in ruta.split("."):
            m = m[k]
        salida.add(round(100 * (m["referencia"] - m["error"]) / m["referencia"]))
    return salida


def caso_cada_recuento_de_las_portadas_sale_de_los_resultados():
    d = json.loads(RESULTADOS.read_text(encoding="utf-8"))
    validos = recuentos(d)
    for portada in PORTADAS:
        texto = (RAIZ / portada).read_text(encoding="utf-8")
        pares = {(int(a), int(b)) for a, b in re.findall(r"(?<![\d.,])(\d+) (?:de|of)(?: los| las| the)? (\d+)", texto)}
        sueltos = sorted(pares - validos)
        assert not sueltos, f"{portada}: recuentos que no están en los resultados: {sueltos}"


def caso_cada_porcentaje_de_las_portadas_sale_de_los_resultados():
    validos = porcentajes(json.loads(RESULTADOS.read_text(encoding="utf-8")))
    for portada in PORTADAS:
        texto = (RAIZ / portada).read_text(encoding="utf-8")
        sueltos = sorted({int(p) for p in re.findall(r"(?<![\d.,])(\d+) ?%", texto)} - validos)
        assert not sueltos, f"{portada}: porcentajes que no están en los resultados: {sueltos}"


if __name__ == "__main__":
    lanzar([caso_cada_cifra_de_las_portadas_sale_de_los_resultados,
            caso_las_cifras_principales_estan_en_las_dos_portadas,
            caso_cada_recuento_de_las_portadas_sale_de_los_resultados,
            caso_cada_porcentaje_de_las_portadas_sale_de_los_resultados])
