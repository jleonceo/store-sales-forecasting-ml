"""Piezas del proceso por lotes: configuración, modelos vigentes y candidatos, comprobación de los datos del día,
resumen y registro de cada ejecución."""

import csv
import hashlib
import json
import platform
import shutil
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
import sklearn

from . import CLAVE, OBJETIVO, RAIZ
from .datos import COLUMNAS, comprobar_continuidad

CONFIG = RAIZ / "produccion" / "config.json"

# Lo que tiene que traer la tabla de cada día (produccion/contrato_entrada.md)
TIPOS = {"store_id": "texto", "item_id": "texto", "date": "texto", "unidades": "número", "wm_yr_wk": "número",
         "weekday": "texto", "wday": "número", "month": "número", "year": "número", "event_name_1": "texto",
         "event_type_1": "texto", "sell_price": "número"}
CAMPOS_EJECUCIONES = ["dia", "momento", "estado", "duracion_s", "previsiones", "motivo"]


class EntradaIncorrecta(Exception):
    """Los datos del día no cumplen el contrato de entrada: la ejecución para sin dejar salida."""


# --- Configuración y rutas

def config():
    """La configuración del proceso, con las rutas ya resueltas desde la raíz del repositorio."""
    c = json.loads(CONFIG.read_text(encoding="utf-8"))
    for k in ["datos_historia", "datos_nuevos", "modelos", "salidas", "informe_despliegue"]:
        c[k] = RAIZ / c[k]
    return c


def carpetas_modelos(c=None):
    """Vigente, candidato y anteriores, dentro de la carpeta de modelos."""
    raiz = (c or config())["modelos"]
    return raiz / "vigente", raiz / "candidato", raiz / "anteriores"


def huella(ruta):
    """SHA-256 de un fichero."""
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def huella_tabla(tabla):
    """Huella de una tabla en memoria, para saber con qué datos se ejecutó."""
    return hashlib.sha256(pd.util.hash_pandas_object(tabla, index=False).to_numpy().tobytes()).hexdigest()


def versiones():
    """Las versiones con que se entrena y se ejecuta."""
    return {"python": platform.python_version(), "pandas": pd.__version__, "scikit-learn": sklearn.__version__,
            "numpy": np.__version__}


# --- Modelos: guardar, cargar, promover y volver atrás

def guardar_modelos(modelos, validacion, hasta, huellas, carpeta):
    """Un fichero joblib por serie y un manifiesto con la fecha, las versiones, las huellas y la validación."""
    if carpeta.exists():
        shutil.rmtree(carpeta)
    carpeta.mkdir(parents=True)
    ficheros = {}
    for s, contenido in modelos.items():
        nombre = s.replace(" · ", "__") + ".joblib"
        joblib.dump(contenido, carpeta / nombre)
        ficheros[s] = nombre
    errores = [v["error"] for v in validacion.values()]
    manifiesto = {"entrenado_hasta": hasta, "fecha": datetime.now().isoformat(timespec="seconds"),
                  "versiones": versiones(), "datos": huellas, "modelos": ficheros,
                  "error_validacion": float(np.mean(errores)) if errores else None, "validacion": validacion}
    (carpeta / "manifiesto.json").write_text(json.dumps(manifiesto, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifiesto


def cargar_modelos(carpeta=None):
    """Los modelos de una carpeta (por defecto, los vigentes); para si las librerías no son las del entrenamiento."""
    carpeta = carpeta or carpetas_modelos()[0]
    manifiesto = json.loads((carpeta / "manifiesto.json").read_text(encoding="utf-8"))
    ahora = versiones()
    for lib in ["scikit-learn", "pandas"]:
        if manifiesto["versiones"][lib] != ahora[lib]:
            raise RuntimeError(f"los modelos se entrenaron con {lib} {manifiesto['versiones'][lib]} y ahora hay "
                               f"{ahora[lib]}: hay que reentrenar")
    return {s: joblib.load(carpeta / f) for s, f in manifiesto["modelos"].items()}, manifiesto


def promover(c=None):
    """Compara el candidato con el vigente y lo pone en uso si no es peor. El vigente pasa a `anteriores/`.

    Devuelve la decisión con sus cifras. Sin modelo vigente, el candidato pasa siempre.
    """
    c = c or config()
    vigente, candidato, anteriores = carpetas_modelos(c)
    nuevo = json.loads((candidato / "manifiesto.json").read_text(encoding="utf-8"))
    tolerancia = c["reentreno"]["tolerancia"]
    if (vigente / "manifiesto.json").exists():
        actual = json.loads((vigente / "manifiesto.json").read_text(encoding="utf-8"))
        if nuevo["error_validacion"] > actual["error_validacion"] + tolerancia:
            return {"promovido": False, "nuevo": nuevo["error_validacion"], "vigente": actual["error_validacion"],
                    "motivo": "el candidato valida peor que el vigente; el vigente sigue en uso"}
        destino = anteriores / datetime.now().strftime("%Y%m%d_%H%M%S")
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(vigente), str(destino))
        previo = actual["error_validacion"]
    else:
        previo = None
    shutil.move(str(candidato), str(vigente))
    return {"promovido": True, "nuevo": nuevo["error_validacion"], "vigente": previo,
            "motivo": "no había modelo vigente" if previo is None else "el candidato no valida peor que el vigente"}


def volver_atras(c=None):
    """Restaura el último modelo de `anteriores/` como vigente; el vigente se guarda también en `anteriores/`."""
    vigente, _, anteriores = carpetas_modelos(c)
    previos = sorted(p for p in anteriores.iterdir() if p.is_dir()) if anteriores.exists() else []
    if not previos:
        raise RuntimeError("no hay ningún modelo anterior al que volver")
    restaurar = previos[-1]
    if vigente.exists():
        shutil.move(str(vigente), str(anteriores / (datetime.now().strftime("%Y%m%d_%H%M%S") + "_retirado")))
    shutil.move(str(restaurar), str(vigente))
    return restaurar.name


# --- Datos del día

def validar_entrada(tabla):
    """El contrato de entrada: columnas, tipos, una fila por serie y día, días seguidos y precio en todos."""
    faltan = [c for c in TIPOS if c not in tabla.columns]
    if faltan:
        raise EntradaIncorrecta(f"faltan columnas: {', '.join(faltan)}")
    for c, tipo in TIPOS.items():
        if (tipo == "número") != pd.api.types.is_numeric_dtype(tabla[c]):
            raise EntradaIncorrecta(f"la columna {c} tiene que ser {tipo}")
    if tabla.duplicated(CLAVE + ["date"]).any():
        raise EntradaIncorrecta("hay series con el mismo día repetido")
    if tabla["sell_price"].isna().any():
        raise EntradaIncorrecta("hay días sin precio")
    comprobar_continuidad(tabla)


def comprobar_dia(tabla, dia, series_esperadas):
    """Lo que tiene que cumplir la mañana de `dia`: todas las series, la venta de la víspera en todas y el calendario
    y el precio del propio día. Si falla algo, para."""
    validar_entrada(tabla)
    vispera = (pd.Timestamp(dia) - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    series = tabla.groupby(CLAVE).ngroups
    if series != series_esperadas:
        raise EntradaIncorrecta(f"llegan {series} series y se esperan {series_esperadas}")
    conocidas = tabla[tabla[OBJETIVO].notna()]
    ultimo = conocidas.groupby(CLAVE)["date"].max()
    if (ultimo != vispera).any():
        raise EntradaIncorrecta(f"la última venta conocida no es la de la víspera ({vispera}) en todas las series: "
                                f"{sorted(set(ultimo))}")
    if (tabla["date"] == dia).sum() != series_esperadas:
        raise EntradaIncorrecta(f"no llega el calendario y el precio del {dia} para todas las series")


def ventas_conocidas_hasta(total, dia):
    """La tabla tal como se conoce la mañana de `dia`: con ventas hasta la víspera; desde `dia`, solo calendario y
    precio. Así el proceso no puede usar ventas que todavía no existen."""
    tabla = total.copy()
    tabla[OBJETIVO] = tabla[OBJETIVO].astype(float)
    tabla.loc[tabla["date"] >= dia, OBJETIVO] = np.nan
    return tabla[COLUMNAS]


# --- Salida y registro de cada ejecución

def preparar_salida(carpeta_dia):
    """La carpeta de una mañana; si ya existía, la anterior se archiva antes de escribir nada."""
    if carpeta_dia.exists():
        archivo = carpeta_dia.parent / "_archivo" / f"{carpeta_dia.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        archivo.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(carpeta_dia), str(archivo))
    carpeta_dia.mkdir(parents=True)
    return carpeta_dia


def anotar_ejecucion(salidas, fila):
    """Añade una fila al registro de ejecuciones: día, momento, estado, duración, previsiones y motivo."""
    registro = salidas / "ejecuciones.csv"
    nuevo = not registro.exists()
    registro.parent.mkdir(parents=True, exist_ok=True)
    with registro.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS_EJECUCIONES)
        if nuevo:
            w.writeheader()
        w.writerow({k: fila.get(k) for k in CAMPOS_EJECUCIONES})
