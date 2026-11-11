"""Los tres gráficos de la portada, dibujados con las cifras de `informes/resultados.json`.

Cada título es la conclusión del gráfico y se escribe a partir de los datos: si los datos no la sostienen, el título
cambia. El modelo va en azul, la regla de compras (repetir la venta de la semana anterior) en gris y discontinua, y la
venta real en negro.

Uso:  python scripts/graficos.py
"""

import json
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
ENTRADA = RAIZ / "informes" / "resultados.json"
CARPETA = RAIZ / "docs" / "graficos"

# Colores: superficie, tinta principal y secundaria, gris recesivo y el azul del modelo
FONDO, TINTA, TINTA_2, GRIS, AZUL = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#2a78d6"
REJILLA = "#e4e3df"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": GRIS,
                     "axes.labelcolor": TINTA_2, "xtick.color": TINTA_2, "ytick.color": TINTA_2,
                     "figure.facecolor": FONDO, "axes.facecolor": FONDO, "savefig.facecolor": FONDO})


def es(valor, decimales=1):
    """Un número con coma decimal."""
    return f"{valor:,.{decimales}f}".replace(",", " ").replace(".", ",").replace(" ", ".")


def ejes_limpios(ax):
    """Sin marco arriba ni a la derecha, rejilla horizontal suave."""
    for lado in ["top", "right", "left"]:
        ax.spines[lado].set_visible(False)
    ax.grid(axis="y", color=REJILLA, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)


def titulo(fig, texto, subtitulo):
    """Título con la conclusión y subtítulo con las cifras, partido en líneas para que no se salga del lienzo."""
    fig.text(0.02, 0.96, texto, fontsize=15, fontweight="bold", color=TINTA, ha="left", va="top")
    fig.text(0.02, 0.89, textwrap.fill(subtitulo, 120), fontsize=10.5, color=TINTA_2, ha="left", va="top",
             linespacing=1.4)


def grafico_total(d):
    """Venta real, modelo y regla en el total de las dos tiendas, del 24 al 31/12/2015."""
    o = d["ocho_dias"]
    dias = list(o["por_dia_total"])
    real = [v["real"] for v in o["por_dia_total"].values()]
    modelo = [v["prevision"] for v in o["por_dia_total"].values()]
    regla = [v["referencia"] for v in o["por_dia_total"].values()]
    etiquetas = [f"{int(f[8:])}/12" for f in dias]
    fig, ax = plt.subplots(figsize=(10, 5.4))
    fig.subplots_adjust(top=0.74, left=0.07, right=0.98, bottom=0.12)
    x = range(len(dias))
    ax.plot(x, real, color=TINTA, linewidth=2.4, marker="o", markersize=6, label="Venta real")
    ax.plot(x, modelo, color=AZUL, linewidth=2.4, marker="o", markersize=6, label="Modelo")
    ax.plot(x, regla, color=GRIS, linewidth=2, linestyle=(0, (4, 3)), marker="o", markersize=5,
            label="Regla: la semana anterior")
    # Los días con una venta casi nula (menos del 10 % de la mediana de la semana) se señalan, para que la caída de la
    # línea negra se lea sola
    umbral = sorted(real)[len(real) // 2] * 0.10
    for i, v in enumerate(real):
        if v < umbral:
            unidades = "unidad vendida" if v == 1 else "unidades vendidas"
            ax.annotate(f"{etiquetas[i]}: {v} {unidades}\nen las dos tiendas", xy=(i, v), xytext=(i + 0.4, 40),
                        fontsize=9.5, color=TINTA_2, arrowprops={"arrowstyle": "-", "color": GRIS, "lw": 0.8})
    ax.set_xticks(list(x), etiquetas)
    ax.legend(frameon=False, loc="upper right", fontsize=10, ncol=3, bbox_to_anchor=(1.0, 1.08))
    ax.set_ylabel("Unidades vendidas al día, 20 productos")
    ax.set_ylim(0, max(real + modelo + regla) * 1.12)
    ejes_limpios(ax)
    t = o["total"]
    mejora = (1 - t["error"] / t["referencia"]) * 100
    if t["error"] < t["referencia"]:
        texto = f"En la semana de Navidad, el modelo se equivoca un {es(mejora, 0)} % menos que la regla"
    else:
        texto = "El modelo y la regla de compras, frente a la venta real"
    titulo(fig, texto, f"Total de las dos tiendas, del 24 al 31/12/2015, previsto el 23/12. Error medio: modelo "
                       f"{es(t['error'], 2)} unidades al día, regla {es(t['referencia'], 2)}.")
    fig.savefig(CARPETA / "01_total_dos_tiendas.png", dpi=150)
    plt.close(fig)


def grafico_horizonte(d):
    """Error medio por día de horizonte, desde los 12 orígenes de 2015."""
    b = d["backtest"]
    h = sorted(b["por_horizonte"], key=int)
    modelo = [b["por_horizonte"][k]["error"] for k in h]
    regla = [b["por_horizonte"][k]["referencia"] for k in h]
    fig, ax = plt.subplots(figsize=(10, 5.4))
    fig.subplots_adjust(top=0.74, left=0.07, right=0.98, bottom=0.12)
    ancho = 0.38
    xs = range(len(h))
    ax.bar([x - ancho / 2 - 0.01 for x in xs], regla, width=ancho, color=GRIS, label="Regla: la semana anterior")
    ax.bar([x + ancho / 2 + 0.01 for x in xs], modelo, width=ancho, color=AZUL, label="Modelo")
    for x, v in zip(xs, modelo):
        ax.text(x + ancho / 2 + 0.01, v + 0.15, es(v), ha="center", va="bottom", fontsize=9, color=TINTA)
    ax.set_xticks(list(xs), [f"Día {k}" for k in h])
    ax.set_ylabel("Error medio, unidades por producto y día")
    ax.legend(frameon=False, loc="upper left", fontsize=10, ncol=2)
    ax.set_ylim(0, max(modelo + regla) * 1.25)
    ejes_limpios(ax)
    gana = sum(m < r for m, r in zip(modelo, regla))
    texto = (f"El modelo se equivoca menos que la regla en los {len(h)} días del horizonte" if gana == len(h)
             else f"El modelo se equivoca menos que la regla en {gana} de los {len(h)} días del horizonte")
    titulo(fig, texto, f"Prueba desde 12 fechas de 2015, cada una con su propio entrenamiento: {es(b['error'], 2)} "
                       f"frente a {es(b['referencia'], 2)} unidades de error medio; gana en {b['bloques_mejor']} de "
                       f"{b['bloques']} previsiones de 8 días.")
    fig.savefig(CARPETA / "02_error_por_horizonte.png", dpi=150)
    plt.close(fig)


def grafico_series(d):
    """Error de cada serie con el modelo y con la regla, en la validación de noviembre de 2015, a un día vista."""
    val = json.loads((RAIZ / "modelos" / "vigente" / "manifiesto.json").read_text(encoding="utf-8"))["validacion"]
    orden = sorted(val, key=lambda s: val[s]["referencia"] - val[s]["error"])
    fig, ax = plt.subplots(figsize=(10, 7.6))
    fig.subplots_adjust(top=0.85, left=0.2, right=0.97, bottom=0.08)
    for y, s in enumerate(orden):
        m, r = val[s]["error"], val[s]["referencia"]
        ax.plot([m, r], [y, y], color=REJILLA, linewidth=3, solid_capstyle="round", zorder=1)
        ax.scatter([r], [y], s=55, color=GRIS, zorder=2, edgecolor=FONDO, linewidth=1.5)
        ax.scatter([m], [y], s=70, color=AZUL, zorder=3, edgecolor=FONDO, linewidth=1.5)
    ax.set_yticks(range(len(orden)), orden, fontsize=9.5)
    ax.set_xlabel("Error medio, unidades por día")
    ax.scatter([], [], s=70, color=AZUL, label="Modelo")
    ax.scatter([], [], s=55, color=GRIS, label="Regla: la semana anterior")
    ax.legend(frameon=False, loc="lower right", fontsize=10)
    for lado in ["top", "right", "left"]:
        ax.spines[lado].set_visible(False)
    ax.grid(axis="x", color=REJILLA, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    v = d["validacion"]
    titulo(fig, f"El modelo mejora la regla en {v['series_mejor']} de los {v['series']} productos",
           f"Validación de noviembre de 2015, a un día vista: {es(v['error'], 2)} frente a {es(v['referencia'], 2)} "
           f"unidades de error medio.")
    fig.savefig(CARPETA / "03_error_por_producto.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    datos = json.loads(ENTRADA.read_text(encoding="utf-8"))
    CARPETA.mkdir(parents=True, exist_ok=True)
    grafico_total(datos)
    grafico_series(datos)
    if datos.get("backtest"):
        grafico_horizonte(datos)
    print(f"OK: gráficos en {CARPETA.relative_to(RAIZ)}")
