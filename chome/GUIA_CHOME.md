# Guía del servidor Chome

Las corridas oficiales del proyecto (1 h por instancia y solver) se hacen en **Chome**: `chome.inf.udec.cl`. Contacto: Mauricio Echavarría (mechavarria@udec.cl). Si algo falla, mándenle el mensaje de error exacto.

Las credenciales del grupo **no van en el repo**.

## El servidor

| | |
| --- | --- |
| CPU | Intel Xeon Gold 5320T, 2,30 GHz, 40 núcleos físicos / 80 lógicos |
| RAM | 251 GB (compartida con otros usuarios) |
| Sistema | Debian 11 |
| Home del grupo | `/home/optimizacion-2026/grupo03` (en la terminal: `~`) |
| Disco | compartido y casi lleno: no guardar `.lp`, `.mps` ni archivos grandes |

## Conectarse (desde Git Bash en el PC)

    ssh grupo03@chome.inf.udec.cl

Se entra desde cualquier red, sin VPN. Atajo opcional: agregar esto a `~/.ssh/config` **en el PC**, y después basta con `ssh chome`:

    Host chome
        HostName chome.inf.udec.cl
        User grupo03
        PubkeyAuthentication no
        PreferredAuthentications password
        ServerAliveInterval 60

## Cada vez que se entra

    cd ~/Proyecto_Optimizaci-n
    source .venv/bin/activate
    git pull

El prompt debe quedar como `(.venv) grupo03@chome:~/Proyecto_Optimizaci-n$`.

Regla: en Chome **solo se hace `git pull` y se corre**. Se programa en el PC, se sube con push y se trae al servidor con pull.

## Corridas largas: siempre dentro de tmux

Si se corta el SSH (internet, notebook cerrado), cualquier programa corriendo se cae, salvo que esté dentro de tmux.

    tmux new -s opti          # abre una sesión que sobrevive a la desconexión
    python src/modelo_gurobi.py instancias/itc2007/comp05.ctt --tiempo 3600 --hilos 8
    # salir sin detener la corrida: Ctrl+b y luego d
    tmux attach -t opti       # volver a la sesión más tarde
    tmux ls                   # ver sesiones abiertas

## Reglas para comparar los solvers

- El **mismo** `--hilos` en Gurobi y CPLEX (acordado: 8) y el mismo `--tiempo` (3600 s en las corridas oficiales).
- **Una corrida a la vez.** Dos corridas en paralelo se reparten la CPU y los tiempos dejan de ser comparables.
- El servidor es compartido: antes de una corrida oficial, revisar la carga con `uptime` (el primer número de "load average" no debería acercarse a 80). Anotar la carga junto a los resultados.

## Traer resultados al PC (desde Git Bash en el PC)

    scp -r grupo03@chome.inf.udec.cl:~/Proyecto_Optimizaci-n/resultados ./

## Cómo quedó instalado (por si hay que repetirlo)

1. Repo y entorno, con Python 3.12 instalado con uv (el del sistema es 3.9):

        git clone https://github.com/gescalonaw/Proyecto_Optimizaci-n.git
        cd Proyecto_Optimizaci-n
        curl -LsSf https://astral.sh/uv/install.sh | sh
        source ~/.local/bin/env
        uv venv -p 3.12 .venv
        source .venv/bin/activate
        uv pip install "gurobipy==13.0.*" "cplex==22.*" docplex pandas matplotlib
        git config --global pull.ff only

2. **Gurobi 13 académico** (licencia 2888998, vence el 26-11-2027). La licencia se pidió en gurobi.com desde la red UdeC y se activó en el servidor con:

        /opt/gurobi1300/linux64/bin/grbgetkey <codigo>

   El archivo quedó en `~/gurobi.lic`. La licencia del PC no sirve aquí: cada Named-User queda amarrada a su máquina.

3. **CPLEX 22.2 académico**: se subió el instalador `IBM_ILOG_CPLEX_OptStdv22.2_LIN.bin` con scp, se instaló con `-i console` en `~/ibm/ILOG/CPLEX_Studio` y se conectó con:

        docplex config --upgrade ~/ibm/ILOG/CPLEX_Studio

   El CPLEX de `/opt/ibm` es Community (1.000 variables): no usarlo.

   **Si CPLEX falla con "no CPLEX runtime found" o "libcplex2220.so: file too short"**, la copia de la biblioteca en el `.venv` quedó rota (pasó el 26-11, quedó en 0 bytes). Arreglo: copiarla a mano (`docplex config` no sirve en ese estado, porque necesita que cplex ya funcione):

        cp ~/ibm/ILOG/CPLEX_Studio/cplex/bin/x86-64_linux/libcplex2220.so .venv/lib/python3.12/site-packages/cplex/_internal/
        cp ~/ibm/ILOG/CPLEX_Studio/cplex/bin/x86-64_linux/libcplex2220.so .venv/bin/
        ls -l .venv/lib/python3.12/site-packages/cplex/_internal/libcplex2220.so   # debe pesar 27765784

   Para evitarlo, `~/.bashrc` tiene `export UV_LINK_MODE=copy` (uv instala copias y no enlaces a su caché).

4. Prueba: `python src/prueba_licencias.py` debe dar [OK] en ambos, con obj = 100422.

## Resultados de referencia

comp01, 8 hilos, 26-11-2026: Gurobi óptimo 5 en 19,1 s; CPLEX óptimo 5 en 34,7 s. Ambas soluciones verificadas (capacidad 4 + estabilidad de sala 1). 5 es el mejor valor conocido de comp01.
