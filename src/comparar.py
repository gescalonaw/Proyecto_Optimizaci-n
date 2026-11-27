"""Muestra resultados/tabla.csv como comparacion lado a lado: Gurobi vs CPLEX por instancia.

Toma la ultima corrida sin error de cada (instancia, solver) con el limite y los hilos pedidos,
imprime la tabla y la guarda en resultados/comparacion.csv.

Uso:
    python src/comparar.py                       # todo lo que haya
    python src/comparar.py --tiempo 3600 --hilos 8
"""
import argparse
import csv

from comun import RAIZ

TABLA = RAIZ / "resultados" / "tabla.csv"
SALIDA = RAIZ / "resultados" / "comparacion.csv"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tiempo", help="filtrar por limite_s (ej. 3600)")
    ap.add_argument("--hilos", help="filtrar por hilos")
    args = ap.parse_args()

    ultimas = {}
    with open(TABLA, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["estado"] == "ERROR":
                continue
            if args.tiempo and r["limite_s"] != args.tiempo or args.hilos and r["hilos"] != args.hilos:
                continue
            ultimas[(r["instancia"], r["solver"], r["limite_s"], r["hilos"])] = r

    claves = sorted({(i, l, h) for (i, _, l, h) in ultimas})
    filas = []
    for inst, lim, hil in claves:
        g = ultimas.get((inst, "gurobi", lim, hil), {})
        c = ultimas.get((inst, "cplex", lim, hil), {})
        filas.append({
            "instancia": inst, "limite_s": lim, "hilos": hil,
            "gurobi_estado": g.get("estado", "-"), "gurobi_obj": g.get("objetivo", "-"),
            "gurobi_gap_pct": g.get("gap_pct", "-"), "gurobi_gap_abs": g.get("gap_abs", "-"), "gurobi_tiempo_s": g.get("tiempo_s", "-"),
            "cplex_estado": c.get("estado", "-"), "cplex_obj": c.get("objetivo", "-"),
            "cplex_gap_pct": c.get("gap_pct", "-"), "cplex_gap_abs": c.get("gap_abs", "-"), "cplex_tiempo_s": c.get("tiempo_s", "-"),
            "verificado": "SI" if g.get("verif_ok") != "NO" and c.get("verif_ok") != "NO" else "NO",
        })

    with open(SALIDA, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]) if filas else ["instancia"])
        w.writeheader()
        w.writerows(filas)

    def gap(r, s):
        o, p, a = r[f"{s}_obj"], r[f"{s}_gap_pct"], r[f"{s}_gap_abs"]
        if o in ("0", "-") or p in ("", "-"):
            return f"abs {a}" if a not in ("", "-") else "-"
        return p

    print("gap% = gap relativo del solver; si el objetivo es 0 se muestra el gap absoluto (objetivo - cota)\n")
    print(f"{'instancia':<10} {'lim':>5} {'hil':>3} | {'GUROBI estado':<14}{'obj':>7}{'gap%':>11}{'t(s)':>9} | "
          f"{'CPLEX estado':<14}{'obj':>7}{'gap%':>11}{'t(s)':>9} | verif")
    for r in filas:
        print(f"{r['instancia']:<10} {r['limite_s']:>5} {r['hilos']:>3} | "
              f"{r['gurobi_estado']:<14}{r['gurobi_obj']:>7}{gap(r, 'gurobi'):>11}{r['gurobi_tiempo_s']:>9} | "
              f"{r['cplex_estado']:<14}{r['cplex_obj']:>7}{gap(r, 'cplex'):>11}{r['cplex_tiempo_s']:>9} | "
              f"{r['verificado']}")
    print(f"\nGuardado en {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
