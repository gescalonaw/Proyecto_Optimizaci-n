"""Iteracion 3: corre Gurobi y CPLEX sobre varias instancias y anota todo en resultados/tabla.csv.

Por cada (instancia, solver):
  1. arma y resuelve el modelo con el limite de tiempo y los hilos pedidos,
  2. guarda la solucion en resultados/soluciones/ y el log en resultados/logs/,
  3. la revisa con verificar.py (sin el solver),
  4. agrega UNA fila a la tabla apenas termina (si algo se cae a mitad, lo ya corrido queda guardado).

Si una combinacion (instancia, solver, tiempo, hilos) ya esta en la tabla, se salta: se puede
relanzar el mismo comando despues de un corte y sigue donde quedo. Para repetir, usar --repetir.

Uso (desde la raiz del repo, en Chome dentro de tmux):
    python src/correr.py comp01 comp11 --tiempo 60 --hilos 8                 # piloto
    python src/correr.py comp01 comp05 comp12 --tiempo 3600 --hilos 8        # oficial
    python src/correr.py --lista instancias/oficiales.txt --tiempo 3600 --hilos 8
    python src/correr.py comp01 --solvers cplex --tiempo 300                 # un solo solver
"""
import argparse
import csv
import os
import platform
import socket
import sys
import traceback
from datetime import datetime
from pathlib import Path

from comun import RAIZ, guardar_solucion
from leer_ctt import leer_ctt
from verificar import verificar

TABLA = RAIZ / "resultados" / "tabla.csv"
COLUMNAS = ["fecha", "instancia", "solver", "version", "hilos", "limite_s", "estado",
            "tiempo_s", "objetivo", "cota", "gap_pct", "nodos", "variables", "restricciones",
            "duras_verif", "costo_verif", "verif_ok", "tiempo_modelo_s", "carga_1min", "maquina",
            "error"]


def ruta_instancia(nombre):
    """Acepta 'comp01', 'comp01.ctt' o una ruta completa."""
    p = Path(nombre)
    if p.suffix == ".ctt" and p.exists():
        return p
    for carpeta in (RAIZ / "instancias" / "itc2007", RAIZ / "instancias" / "propias"):
        c = carpeta / (p.stem + ".ctt")
        if c.exists():
            return c
    sys.exit(f"No encuentro la instancia '{nombre}'")


def ya_corridas():
    """Combinaciones ya terminadas (sin error) en la tabla."""
    if not TABLA.exists():
        return set()
    with open(TABLA, newline="", encoding="utf-8") as f:
        return {(r["instancia"], r["solver"], r["limite_s"], r["hilos"])
                for r in csv.DictReader(f) if r["estado"] != "ERROR"}


def anotar(fila):
    nueva = not TABLA.exists()
    TABLA.parent.mkdir(parents=True, exist_ok=True)
    with open(TABLA, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS)
        if nueva:
            w.writeheader()
        w.writerow(fila)


def fmt(v, dec=2):
    return "" if v is None else (f"{v:.{dec}f}" if isinstance(v, float) else v)


def correr_uno(ruta, solver, tiempo, hilos, gap):
    inst = leer_ctt(ruta)
    nombre = ruta.stem
    fila = {"fecha": datetime.now().isoformat(timespec="seconds"), "instancia": nombre,
            "solver": solver, "hilos": hilos, "limite_s": fmt(float(tiempo), 0),
            "carga_1min": fmt(os.getloadavg()[0]) if hasattr(os, "getloadavg") else "",
            "maquina": f"{socket.gethostname()} ({platform.processor() or platform.machine()})"}
    try:
        if solver == "gurobi":
            import modelo_gurobi as mod
        else:
            import modelo_cplex as mod
        r = mod.resolver(inst, nombre, tiempo, hilos, gap, mostrar=False)
        fila.update({k: fmt(r[k]) for k in ("version", "estado", "tiempo_s", "cota", "tiempo_modelo_s")})
        fila.update({"objetivo": fmt(r["objetivo"], 0) if r["objetivo"] is not None else "",
                     "gap_pct": fmt(100 * r["gap"]) if r["gap"] is not None else "",
                     "nodos": r["nodos"], "variables": r["variables"], "restricciones": r["restricciones"]})
        if r["solucion"]:
            guardar_solucion(r["solucion"], nombre, solver)
            duras, blandas, _ = verificar(inst, r["solucion"])
            d, b = sum(duras.values()), sum(blandas.values())
            fila.update({"duras_verif": d, "costo_verif": b,
                         "verif_ok": "SI" if d == 0 and b == round(r["objetivo"]) else "NO"})
    except Exception as e:  # una corrida que falla no detiene las demas
        fila.update({"estado": "ERROR", "error": f"{type(e).__name__}: {e}"[:300]})
        traceback.print_exc()
    anotar(fila)
    return fila


def main():
    ap = argparse.ArgumentParser(description="Corridas por lote de Gurobi y CPLEX")
    ap.add_argument("instancias", nargs="*", help="nombres (comp01) o rutas .ctt")
    ap.add_argument("--lista", help="archivo de texto con una instancia por linea")
    ap.add_argument("--solvers", nargs="+", default=["gurobi", "cplex"], choices=["gurobi", "cplex"])
    ap.add_argument("--tiempo", type=float, default=60, help="limite por corrida, en segundos")
    ap.add_argument("--hilos", type=int, default=8, help="el mismo para ambos solvers")
    ap.add_argument("--gap", type=float, default=0.0)
    ap.add_argument("--repetir", action="store_true", help="correr aunque ya este en la tabla")
    args = ap.parse_args()

    nombres = list(args.instancias)
    if args.lista:
        nombres += [l.split("#")[0].strip() for l in open(args.lista, encoding="utf-8")]
    nombres = [n for n in nombres if n]
    if not nombres:
        ap.error("indica instancias o --lista")

    hechas = set() if args.repetir else ya_corridas()
    trabajos = [(ruta_instancia(n), s) for n in nombres for s in args.solvers]
    pendientes = [(r, s) for r, s in trabajos
                  if (r.stem, s, fmt(float(args.tiempo), 0), str(args.hilos)) not in hechas]
    print(f"{len(trabajos)} corridas pedidas, {len(trabajos) - len(pendientes)} ya en la tabla, "
          f"{len(pendientes)} por correr (maximo ~{len(pendientes) * args.tiempo / 3600:.1f} h)")

    for i, (ruta, solver) in enumerate(pendientes, 1):
        print(f"\n[{i}/{len(pendientes)}] {ruta.stem} con {solver} "
              f"({args.tiempo:.0f} s, {args.hilos} hilos) - {datetime.now():%H:%M:%S}", flush=True)
        f = correr_uno(ruta, solver, args.tiempo, args.hilos, args.gap)
        print(f"   {f.get('estado')}  obj={f.get('objetivo', '')}  cota={f.get('cota', '')}  "
              f"gap={f.get('gap_pct', '')}%  t={f.get('tiempo_s', '')}s  verificado={f.get('verif_ok', '')}",
              flush=True)

    print(f"\nListo. Resultados en {TABLA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
