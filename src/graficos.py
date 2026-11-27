"""Graficos de la comparacion Gurobi vs CPLEX a partir de resultados/tabla.csv.

Genera en resultados/figuras/:
  costo.png    mejor horario encontrado por cada solver (costo real verificado, escala log)
  gap.png      gap final de cada solver (con la cota recortada en 0)
  tiempo.png   tiempo hasta demostrar el optimo, en las instancias donde alguno lo demostro
  resumen.md   la misma informacion como tabla, para copiar a las diapositivas o al informe

Usa la ultima corrida sin error de cada (instancia, solver) con el modelo, limite e hilos pedidos.
El orden de las instancias sale de instancias/oficiales.txt (y su grupo, del comentario).

Uso (desde la raiz del repo):
    python src/graficos.py                                   # v1, 3600 s, 8 hilos
    python src/graficos.py --tiempo 600 --modelo v1-base
"""
import argparse
import csv

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

from comun import RAIZ  # noqa: E402

TABLA = RAIZ / "resultados" / "tabla.csv"
SALIDA = RAIZ / "resultados" / "figuras"
OFICIALES = RAIZ / "instancias" / "oficiales.txt"

# colores validados (azul / naranjo); el naranjo tiene poco contraste con el fondo blanco,
# por eso cada solver lleva ademas su propia forma de marcador y hay leyenda + tabla
SOLVERS = {"gurobi": ("Gurobi 13", "#257de0", "o"), "cplex": ("CPLEX 22.2", "#f47230", "s")}
TEXTO, TEXTO_2, GRILLA, CONECTOR = "#191919", "#666666", "#e6e6e6", "#c8c8c8"
DESPLAZA = {"gurobi": -0.14, "cplex": 0.14}  # cada solver en su propia linea: si empatan, no se tapan
GRUPOS = {"pequena": "pequeña", "mediana": "mediana", "grande": "grande"}

plt.rcParams.update({
    "font.size": 11, "axes.edgecolor": GRILLA, "axes.labelcolor": TEXTO_2,
    "xtick.color": TEXTO_2, "ytick.color": TEXTO, "axes.titlesize": 13, "axes.titleweight": "bold",
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
})


def leer_oficiales():
    """[(instancia, grupo)] en el orden del archivo."""
    if not OFICIALES.exists():
        return []
    salida = []
    for linea in OFICIALES.read_text(encoding="utf-8").splitlines():
        nombre, _, comentario = linea.partition("#")
        nombre = nombre.strip()
        if nombre:
            grupo = comentario.split()[-1] if "|" not in comentario else comentario.split("|")[0].split()[-1]
            salida.append((nombre, GRUPOS.get(grupo, grupo)))
    return salida


def cargar(modelo, tiempo, hilos):
    datos = {}
    with open(TABLA, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if (r["estado"] != "ERROR" and r["modelo"] == modelo and r["limite_s"] == tiempo
                    and r["hilos"] == hilos and r["costo_verif"] != ""):
                datos[(r["instancia"], r["solver"])] = r
    return datos


def numeros(r):
    costo, cota = float(r["costo_verif"]), float(r["cota"]) if r["cota"] else 0.0
    cota = max(cota, 0.0)  # ningun horario cuesta menos de 0
    gap = 100 * (costo - cota) / costo if costo > 0 else 0.0
    return costo, cota, gap, float(r["tiempo_s"]), r["estado"] == "OPTIMO"


def ejes_instancias(ax, etiquetas):
    ax.set_yticks(range(len(etiquetas)))
    ax.set_yticklabels(etiquetas)
    ax.invert_yaxis()
    ax.grid(axis="x", color=GRILLA, linewidth=1)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0)


def leyenda(ax):
    for s, (nombre, color, marca) in SOLVERS.items():
        ax.plot([], [], marca, color=color, markersize=9, markeredgecolor="white", label=nombre)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, frameon=False, fontsize=11)


def mancuerna(ax, filas, valor):
    """Un punto por solver y una linea gris entre ambos (el largo = la diferencia)."""
    for i, (inst, _) in enumerate(filas):
        xs = [valor(inst, s) for s in SOLVERS]
        ys = [i + DESPLAZA[s] for s in SOLVERS]
        if None not in xs:
            ax.plot(xs, ys, color=CONECTOR, linewidth=2, zorder=1)
        for (s, (_, color, marca)), x, y in zip(SOLVERS.items(), xs, ys):
            if x is not None:
                ax.plot(x, y, marca, color=color, markersize=10, markeredgecolor="white",
                        markeredgewidth=2, zorder=3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelo", default="v1-base")
    ap.add_argument("--tiempo", default="3600")
    ap.add_argument("--hilos", default="8")
    args = ap.parse_args()

    datos = cargar(args.modelo, args.tiempo, args.hilos)
    instancias = leer_oficiales() or sorted({(i, "") for i, _ in datos})
    filas = [(i, g) for i, g in instancias if any((i, s) in datos for s in SOLVERS)]
    if not filas:
        raise SystemExit(f"No hay corridas con modelo={args.modelo}, tiempo={args.tiempo}, hilos={args.hilos}")
    etiquetas = [f"{i}  ({g})" if g else i for i, g in filas]
    num = {k: numeros(r) for k, r in datos.items()}
    SALIDA.mkdir(parents=True, exist_ok=True)
    pie = f"Chome, {args.hilos} hilos, límite {int(float(args.tiempo))} s, modelo {args.modelo}"
    alto = 1.2 + 0.55 * len(filas)

    # ---- 1. costo ----
    fig, ax = plt.subplots(figsize=(10, alto))
    mancuerna(ax, filas, lambda i, s: num[(i, s)][0] if (i, s) in num else None)
    ax.set_xscale("symlog", linthresh=1)
    ax.set_xlim(left=0)
    ax.set_xlabel("costo real del mejor horario (penalización ITC-2007, escala logarítmica; menor es mejor)")
    for i, (inst, _) in enumerate(filas):
        opt = [SOLVERS[s][0].split()[0] for s in SOLVERS if (inst, s) in num and num[(inst, s)][4]]
        if opt:
            x = max(num[(inst, s)][0] for s in SOLVERS if (inst, s) in num)
            ax.annotate("óptimo: " + ", ".join(opt), (x, i), xytext=(12, 0), textcoords="offset points",
                        va="center", fontsize=9, color=TEXTO_2)
    ejes_instancias(ax, etiquetas)
    leyenda(ax)
    ax.set_title("Mejor horario encontrado por cada solver", pad=34, loc="left")
    fig.text(0.01, 0.005, pie, fontsize=8, color=TEXTO_2)
    fig.tight_layout()
    fig.savefig(SALIDA / "costo.png", dpi=200)
    plt.close(fig)

    # ---- 2. gap ----
    fig, ax = plt.subplots(figsize=(10, alto))
    mancuerna(ax, filas, lambda i, s: num[(i, s)][2] if (i, s) in num else None)
    ax.set_xlim(-3, 103)
    ax.set_xlabel("gap final (%) = (costo − cota) / costo;  0 % = óptimo demostrado,  100 % = sin cota útil")
    ejes_instancias(ax, etiquetas)
    leyenda(ax)
    ax.set_title("Gap al terminar el tiempo límite", pad=34, loc="left")
    fig.text(0.01, 0.005, pie, fontsize=8, color=TEXTO_2)
    fig.tight_layout()
    fig.savefig(SALIDA / "gap.png", dpi=200)
    plt.close(fig)

    # ---- 3. tiempo (solo instancias donde alguno demostro el optimo) ----
    resueltas = [(i, g) for i, g in filas if any((i, s) in num and num[(i, s)][4] for s in SOLVERS)]
    if resueltas:
        fig, ax = plt.subplots(figsize=(10, 1.4 + 0.9 * len(resueltas)))
        alto_barra = 0.36
        limite = float(args.tiempo)
        for j, (s, (nombre, color, _)) in enumerate(SOLVERS.items()):
            for i, (inst, _) in enumerate(resueltas):
                if (inst, s) not in num:
                    continue
                _, _, _, t, opt = num[(inst, s)]
                y = i + (j - 0.5) * (alto_barra + 0.04)
                ax.barh(y, t, height=alto_barra, color=color if opt else "white",
                        edgecolor=color, hatch=None if opt else "//", linewidth=1.5)
                ax.annotate(f"{t:,.0f} s" + ("" if opt else " (no cerró)"), (t, y), xytext=(6, 0),
                            textcoords="offset points", va="center", fontsize=9, color=TEXTO)
        ax.set_yticks(range(len(resueltas)))
        ax.set_yticklabels([f"{i}  ({g})" if g else i for i, g in resueltas])
        ax.invert_yaxis()
        ax.set_xlim(0, limite * 1.15)
        ax.grid(axis="x", color=GRILLA)
        ax.set_axisbelow(True)
        ax.tick_params(axis="y", length=0)
        ax.set_xlabel("segundos hasta demostrar el óptimo (barra rayada = no lo demostró en el límite)")
        ax.legend(handles=[Patch(color=c, label=n) for n, c, _ in SOLVERS.values()],
                  loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, frameon=False)
        ax.set_title("Tiempo hasta el óptimo", pad=34, loc="left")
        fig.text(0.01, 0.005, pie, fontsize=8, color=TEXTO_2)
        fig.tight_layout()
        fig.savefig(SALIDA / "tiempo.png", dpi=200)
        plt.close(fig)

    # ---- 4. tabla en markdown ----
    lineas = [f"Resultados: {pie}. Costo = costo real verificado; gap con la cota recortada en 0.", "",
              "| Instancia | Grupo | Gurobi: estado | Gurobi: costo | Gurobi: gap | Gurobi: tiempo (s) "
              "| CPLEX: estado | CPLEX: costo | CPLEX: gap | CPLEX: tiempo (s) |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for inst, g in filas:
        celdas = [inst, g]
        for s in SOLVERS:
            if (inst, s) in num:
                costo, _, gap, t, opt = num[(inst, s)]
                celdas += ["óptimo" if opt else "límite de tiempo", f"{costo:,.0f}", f"{gap:.1f} %", f"{t:,.0f}"]
            else:
                celdas += ["-"] * 4
        lineas.append("| " + " | ".join(celdas) + " |")
    (SALIDA / "resumen.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")

    print(f"Listo: {len(filas)} instancias. Figuras en {SALIDA.relative_to(RAIZ)}/")
    for f in sorted(SALIDA.iterdir()):
        print("  ", f.name)


if __name__ == "__main__":
    main()
