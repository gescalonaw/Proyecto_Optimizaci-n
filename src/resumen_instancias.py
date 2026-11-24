"""Calcula las caracteristicas de cada instancia y las guarda en instancias/resumen.csv.
Sirve para elegir >= 3 instancias por caracteristica (iteracion 4).

Uso (desde la raiz del repo):  python src/resumen_instancias.py
"""
import csv
from pathlib import Path
from leer_ctt import leer_ctt

RAIZ = Path(__file__).resolve().parent.parent
filas = []
for ruta in sorted((RAIZ / "instancias").rglob("*.ctt")):
    i = leer_ctt(ruta)
    clases = sum(c["clases"] for c in i["cursos"].values())
    slots = len(i["slots"])
    salas = len(i["salas"])
    filas.append({
        "archivo": ruta.relative_to(RAIZ / "instancias").as_posix(),
        "nombre": i["Name"],
        "cursos": len(i["cursos"]),
        "clases": clases,
        "salas": salas,
        "dias": i["Days"],
        "periodos_dia": i["Periods_per_day"],
        "slots": slots,
        "curriculos": len(i["curriculos"]),
        "indisponibilidades": i["Constraints"],
        "ocupacion_%": round(100 * clases / (salas * slots), 1),
        "vars_x (cursos*salas*slots)": len(i["cursos"]) * salas * slots,
    })

with open(RAIZ / "instancias" / "resumen.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
    w.writeheader()
    w.writerows(filas)

for f in filas:
    print(f"{f['archivo']:<22} cursos={f['cursos']:>3} clases={f['clases']:>4} salas={f['salas']:>2} "
          f"slots={f['slots']:>2} ocup={f['ocupacion_%']:>5}%  x={f['vars_x (cursos*salas*slots)']:>6}")
