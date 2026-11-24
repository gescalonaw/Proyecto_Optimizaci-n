# Proyecto Optimización: plan iterativo

Tema: asignación óptima de horarios y salas mediante PLE (CB-CTT, ITC-2007 track 3). Se resuelve con Gurobi y CPLEX y se comparan.

Presentación final: 15 min. La fecha cae el 20 nov, el 25 nov o el 2 dic (**por confirmar cuál le toca al grupo**). El plan está hecho para el 2 dic; al final va la versión comprimida.

Estado al 17/11: la carpeta pROYECTO_OPTIMIZACIÓN solo tiene la rúbrica y el enunciado. Todavía no hay código ni instancias.

## La idea del plan iterativo

Cada iteración termina con algo que **funciona y se puede mostrar**, aunque sea pequeño. Nunca se avanza a la siguiente con la anterior rota. Si se acaba el tiempo, igual queda algo que presentar.

## Ponderación final (para priorizar)

Comparación computacional 30 % · Modelo matemático 25 % · Instancias 20 % · Supuestos y limitaciones 10 % · Oral 10 % · Correcciones de la presentación inicial 5 %.

## Iteración 0: preparación (mié 18 en la tarde, después del pitch de la TC3)

- Confirmar la fecha de la presentación final y los roles.
- Crear una carpeta compartida (Drive o GitHub) con esta estructura: `instancias/`, `src/`, `resultados/`, `informe/`.
- Licencias: Gurobi Academic WLS en gurobi.com (el PC de Gabriela tiene la limitada de 2.000 variables, que no alcanza) y CPLEX, que ya funciona. Pedir acceso a Luthier a Mauricio Echavarría (mechavarria@udec.cl), porque las corridas de 1 h se hacen ahí.
- Descargar los .ctt de github.com/Docheinstein/itc2007-cct (carpeta `datasets/`).
- Anotar el feedback de la profesora sobre la presentación inicial (vale 5 %).

**Listo cuando:** todos tienen la carpeta, las dos licencias funcionan con un modelo de prueba y la fecha está confirmada.

## Iteración 1: lector de instancias + modelo con restricciones duras (jue 19 – vie 20)

- `leer_ctt.py`: lee el .ctt y lo deja en diccionarios (cursos, salas, currículos, indisponibilidades).
- Crear a mano una instancia de juguete (3–4 cursos, 2 salas, 2 días × 2 periodos) donde la solución se pueda verificar en papel.
- Modelo en Gurobi **solo con las restricciones duras**: (1) todas las clases asignadas, (2) una clase por sala y periodo, (3) sin choques de currículo ni de profesor, (4) indisponibilidades. Objetivo = 0 (solo factibilidad).
- `verificar.py`: revisa la solución por fuera del solver y cuenta violaciones.

**Listo cuando:** el juguete y Fis0506-1/comp01 dan una solución factible con 0 violaciones duras.

## Iteración 2: restricciones blandas + CPLEX (sáb 21 – dom 22)

- Agregar las variables y[c,d], w[c], e[q,t] y v[c,r] y el objetivo con pesos: capacidad (1), días mínimos (5), compacidad (2), estabilidad de sala (1).
- `verificar.py` calcula también la penalización. Debe dar el mismo número que el objetivo del solver.
- Pasar el mismo modelo a CPLEX (docplex), en el mismo archivo o en uno paralelo.

**Listo cuando:** en el juguete, Gurobi y CPLEX dan el mismo óptimo y el verificador lo confirma.

(Lun 23 es la entrega de EDAA; ese día no se toca este proyecto.)

## Iteración 3: experimento piloto (mar 24 – mié 25)

- `correr.py`: recibe instancia, solver y límite de tiempo. Guarda en `resultados/tabla.csv`: tiempo, estado, mejor objetivo (incumbente), cota y MIPGap %. Guarda también el .log de cada corrida.
- Prueba con límite de 60 s en 2–3 instancias pequeñas, en un solo PC.

**Listo cuando:** la tabla se llena sola y los números tienen sentido (gap ≥ 0 y objetivo ≥ cota).

## Iteración 4: diseño de instancias + corridas oficiales (jue 26 – sáb 28)

- Elegir **al menos 3 instancias por característica**. Por ejemplo:
  - tamaño (pequeña, mediana, grande: n.º de cursos y clases);
  - ocupación de salas (clases ÷ (salas × periodos): baja, media, alta);
  - densidad de conflictos (n.º de currículos o indisponibilidades).
- Sirven las comp01–comp21 y además sub-instancias recortadas (quitando cursos), si faltan casos pequeños.
- Hacer una tabla de las instancias con sus características (va al informe y a las diapositivas).
- Correr en Luthier con 1 h por instancia y por solver. **Calcular el tiempo antes:** 9 instancias × 2 solvers × 1 h = 18 h. Hay que dejarlas corriendo de noche o en paralelo, y partir apenas termine la iteración 3.

**Listo cuando:** `tabla.csv` está completa con las dos corridas de cada instancia.

## Iteración 5: análisis y presentación (dom 29 nov – mar 1 dic)

- Gráficos: tiempo por instancia, gap final y objetivo de Gurobi vs CPLEX. Discutir dónde gana cada uno y por qué (si no cierra en 1 h, se comparan cota y gap, no solo tiempo).
- Supuestos y limitaciones: periodos de igual duración, sin preferencias de profesor, modelo monolítico (no la descomposición de Lach y Lübbecke), límite de 1 h, hardware de Luthier.
- Diapositivas de 15 min hechas por el grupo (no se permite una presentación generada por IA) y 2 ensayos cronometrados con banco de preguntas.

**Listo cuando:** ensayo completo en ≤ 15 min.

## Reparto sugerido (4–5 personas)

| Rol | Tareas principales |
| --- | --- |
| Modelador/a principal | Formulación escrita (ecuaciones y explicación), coherencia modelo–código |
| Modeladora secundaria (Gabriela) | Revisar la formulación, supuestos y limitaciones, coordinación y plan |
| Programación Gurobi | lector .ctt, modelo Gurobi, verificador |
| Programación CPLEX | modelo docplex, `correr.py`, corridas en Luthier |
| Instancias y análisis | selección y tabla de instancias, gráficos, discusión de resultados |

## Si la presentación es el 20 nov (versión mínima)

- Mié 18: iteración 0, más el lector y las duras en Gurobi esa misma noche.
- Jue 19: blandas, CPLEX, y corridas de 10–15 min (no 1 h) en 3 instancias pequeñas, declarándolo como limitación.
- Vie 20: tabla, 2 gráficos, ensayo.

Con 3 días es imposible cumplir "≥3 por característica con 1 h". Conviene hablar con la profesora antes.

## Riesgos

- Licencia de Gurobi: sin la WLS no se puede comparar → resolverlo el mié 18.
- Instancias grandes (comp05, comp12…) pueden no encontrar ni una solución factible en 1 h. Eso también es un resultado, pero hay que incluir instancias medianas que sí resuelvan.
- Que se crucen la TC3 (17–18 nov) y EDAA (23 nov) con este proyecto.
