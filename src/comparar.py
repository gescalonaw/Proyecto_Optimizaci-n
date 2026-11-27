"""Muestra resultados/tabla.csv como comparacion lado a lado: Gurobi vs CPLEX por instancia.

Toma la ultima corrida sin error de cada (modelo, instancia, solver, limite, hilos), imprime la
tabla y la guarda en resultados/comparacion.csv.

"costo" es el costo REAL del horario (calculado por verificar.py) y "gap" se calcula con ese costo:
    gap % = 100 * (costo - max(cota, 0)) / costo
La cota se recorta en 0: ningun horario cuesta menos de 0, asi que una cota negativa del solver
no aporta informacion (pasa por el termino "salas usadas - 1" en la relajacion). En ese caso el
gap queda en 100 % y la tabla lo marca con "*".
Con el modelo v2 coinciden con lo que reporta el solver; con v1 el solver puede sobreestimar el
objetivo, por eso se usa el costo verificado para comparar. Si el costo es 0, el gap % no tiene
sentido y se muestra el gap absoluto (costo - cota).

Uso:
    python src/comparar.py                       # todo lo que haya
    python src/comparar.py --tiempo 3600 --hilos 8
"""
import argparse
import csv

from comun import RAIZ

TABLA = RAIZ / "resultados" / "tabla.csv"
SALIDA = RAIZ / "resultados" / "comparacion.csv"
SOLVERS = ("gurobi", "cplex")


def gap_real(r):
    """(gap %, gap absoluto, cota usada) con el costo verificado y la cota recortada en 0."""
    try:
        costo, cota = float(r["costo_verif"]), float(r["cota"])
    except (KeyError, ValueError):
        return "", "", ""
    cota_util = max(cota, 0.0)
    absoluto = costo - cota_util
    pct = 100 * absoluto / costo if costo > 0 else None
    marca = "*" if cota < 0 else ""
    return ("" if pct is None else f"{pct:.2f}{marca}"), f"{absoluto:.2f}{marca}", f"{cota_util:.2f}"


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
            ultimas[(r["modelo"], r["instancia"], r["solver"], r["limite_s"], r["hilos"])] = r

    claves = sorted({(i, m, l, h) for (m, i, _, l, h) in ultimas})
    filas = []
    for inst, mod, lim, hil in claves:
        fila = {"instancia": inst, "modelo": mod, "limite_s": lim, "hilos": hil}
        verif = []
        for s in SOLVERS:
            r = ultimas.get((mod, inst, s, lim, hil), {})
            pct, ab, cota_util = gap_real(r) if r else ("", "", "")
            fila.update({f"{s}_estado": r.get("estado", "-"), f"{s}_objetivo_solver": r.get("objetivo", "-"),
                         f"{s}_costo": r.get("costo_verif", "-"), f"{s}_cota_solver": r.get("cota", "-"), f"{s}_cota_usada": cota_util or "-",
                         f"{s}_gap_pct": pct, f"{s}_gap_abs": ab, f"{s}_tiempo_s": r.get("tiempo_s", "-")})
            if r:
                verif.append(r.get("verif_ok", ""))
        fila["verificado"] = "NO" if "NO" in verif else ("SOBREESTIMA" if "SOBREESTIMA" in verif else "SI")
        filas.append(fila)

    with open(SALIDA, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]) if filas else ["instancia"])
        w.writeheader()
        w.writerows(filas)

    def gap(fila, s):
        if fila[f"{s}_gap_pct"]:
            return fila[f"{s}_gap_pct"]
        return f"abs {fila[f'{s}_gap_abs']}" if fila[f"{s}_gap_abs"] else "-"

    print("costo = costo real verificado; gap% = (costo - max(cota, 0)) / costo; si el costo es 0 se muestra el gap absoluto")
    print("* = la cota del solver era negativa (sin informacion util), se uso 0\n")
    print(f"{'instancia':<10}{'modelo':<11}{'lim':>5}{'hil':>4} | {'GUROBI estado':<14}{'costo':>7}{'gap%':>11}{'t(s)':>9} | "
          f"{'CPLEX estado':<14}{'costo':>7}{'gap%':>11}{'t(s)':>9} | verif")
    for r in filas:
        print(f"{r['instancia']:<10}{r['modelo']:<11}{r['limite_s']:>5}{r['hilos']:>4} | "
              f"{r['gurobi_estado']:<14}{r['gurobi_costo']:>7}{gap(r, 'gurobi'):>11}{r['gurobi_tiempo_s']:>9} | "
              f"{r['cplex_estado']:<14}{r['cplex_costo']:>7}{gap(r, 'cplex'):>11}{r['cplex_tiempo_s']:>9} | "
              f"{r['verificado']}")
    print(f"\nGuardado en {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
