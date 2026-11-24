"""Lector de instancias CB-CTT (ITC-2007, track 3) en formato .ctt.

Uso:
    from leer_ctt import leer_ctt
    inst = leer_ctt("instancias/itc2007/comp01.ctt")

Dias y periodos parten en 0. Un "slot" t = dia * periodos_por_dia + periodo.
"""
from pathlib import Path


def leer_ctt(ruta):
    lineas = [l.strip() for l in Path(ruta).read_text(encoding="utf-8").splitlines()]
    inst = {"cursos": {}, "salas": {}, "curriculos": {}, "indisponibles": set()}
    seccion = None
    for l in lineas:
        if not l or l == "END.":
            continue
        if l.endswith(":") and l[:-1] in ("COURSES", "ROOMS", "CURRICULA", "UNAVAILABILITY_CONSTRAINTS"):
            seccion = l[:-1]
            continue
        if seccion is None:  # cabecera "Clave: valor"
            k, v = [x.strip() for x in l.split(":", 1)]
            inst[k] = v if k == "Name" else int(v)
        elif seccion == "COURSES":
            c, prof, n_clases, min_dias, n_alumnos = l.split()
            inst["cursos"][c] = {"profesor": prof, "clases": int(n_clases),
                                 "min_dias": int(min_dias), "alumnos": int(n_alumnos)}
        elif seccion == "ROOMS":
            r, cap = l.split()
            inst["salas"][r] = int(cap)
        elif seccion == "CURRICULA":
            p = l.split()
            inst["curriculos"][p[0]] = p[2:2 + int(p[1])]
        elif seccion == "UNAVAILABILITY_CONSTRAINTS":
            c, d, p = l.split()
            inst["indisponibles"].add((c, int(d), int(p)))

    D, P = inst["Days"], inst["Periods_per_day"]
    inst["dias"], inst["periodos"] = list(range(D)), list(range(P))
    inst["slots"] = list(range(D * P))
    # chequeos basicos contra la cabecera
    assert len(inst["cursos"]) == inst["Courses"], "n.º de cursos no calza con la cabecera"
    assert len(inst["salas"]) == inst["Rooms"], "n.º de salas no calza"
    assert len(inst["curriculos"]) == inst["Curricula"], "n.º de curriculos no calza"
    assert len(inst["indisponibles"]) == inst["Constraints"], "n.º de indisponibilidades no calza"
    return inst


if __name__ == "__main__":
    import sys
    i = leer_ctt(sys.argv[1] if len(sys.argv) > 1 else "instancias/itc2007/toytoy.ctt")
    print(i["Name"], "| cursos:", len(i["cursos"]), "| salas:", len(i["salas"]),
          "| slots:", len(i["slots"]), "| curriculos:", len(i["curriculos"]))
