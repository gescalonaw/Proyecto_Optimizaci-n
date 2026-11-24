# Guía rápida de Luthier

Las credenciales **no van en el repo**. Cada uno guarda las suyas fuera de la carpeta, o en `.env`, que está en `.gitignore`.

## 1. Conectarse (desde Windows: PowerShell o Git Bash)

    ssh USUARIO@HOST

Si piden VPN o estar en la red UdeC, conéctense primero a eso.

## 2. Primera vez: ver qué hay en el servidor

    # desde tu PC, en la carpeta del repo:
    scp luthier/revisar_servidor.sh USUARIO@HOST:~
    # en Luthier:
    bash revisar_servidor.sh > info_luthier.txt
    cat info_luthier.txt

Guarden `info_luthier.txt` en `informe/`, porque el hardware se declara en la presentación.
- Si **Gurobi o CPLEX no aparecen**, pregúntenle a Mauricio Echavarría (mechavarria@udec.cl) cómo están instalados (ruta o `module load`) antes de instalar nada.
- Si hay que instalar con pip: `python3 -m venv ~/venv && source ~/venv/bin/activate && pip install -r requirements.txt`. Ojo: el gurobipy de pip trae licencia limitada y en el servidor hace falta una licencia académica válida para esa máquina.

## 3. Subir el repo

Opción A (recomendada):

    git clone URL_DEL_REPO

Opción B:

    scp -r horarios-ple USUARIO@HOST:~

## 4. Corridas largas sin quedarse conectado

    tmux new -s opti          # abre una sesión que sobrevive si se corta el SSH
    python3 src/prueba_licencias.py
    # salir sin cortar: Ctrl+b y luego d    |  volver: tmux attach -t opti

Sin tmux:

    nohup python3 src/correr.py ... > resultados/logs/corrida.out 2>&1 &

## 5. Traer resultados

    scp -r USUARIO@HOST:~/horarios-ple/resultados ./

## Reglas del grupo

- Todas las corridas oficiales se hacen **en Luthier**, con el mismo número de hilos para ambos solvers (p. ej., `Threads=4`) y 1 h de límite.
- **Una corrida a la vez** por instancia y solver. Si corren varias en paralelo se reparten la CPU y los tiempos dejan de ser comparables.
