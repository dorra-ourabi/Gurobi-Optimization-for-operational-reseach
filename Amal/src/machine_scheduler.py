import gurobipy as gp
from gurobipy import GRB
import networkx as nx
from typing import List, Dict, Tuple
import math
class MachineScheduler:
    def __init__(self, tasks: List[str], conflicts: List[Tuple[str, str]]):
        self.tasks = tasks
        self.n_tasks = len(tasks)
        self.conflicts = conflicts
        # Créer le graphe de conflits
        self.conflict_graph = nx.Graph()
        self.conflict_graph.add_nodes_from(tasks)
        self.conflict_graph.add_edges_from(conflicts)
        self.model = None
        self.assignment = {}  # tache -> machine
        self.n_machines_used = 0

    def solve_assignment_model(self, 
                               task_capacities: Dict[int, int] = None,
                               time_capacities: Dict[int, float] = None,
                               durations: Dict[str, float] = None,
                               max_machines_dispo=None, 
                               time_limit=300):
    
        print("\n" + "="*60)
        print("MODÈLE D'ASSIGNATION DE MACHINES (Gurobi)")
        print("="*60)
        if durations is None:
            durations = {t: 1 for t in self.tasks}

        degrees = dict(self.conflict_graph.degree()).values()
        max_degree = max(degrees) if degrees else 0
        max_machines = max_degree + 1          # Au pire: degré maximum + 1 (theoreme de Brooks)

        if max_machines_dispo is not None:
            max_machines = min(max_machines, max_machines_dispo)

        if not(task_capacities) :
            task_capacities = {m: len(self.tasks) for m in range(max_machines)}
        else:   
            default_task_cap = max(task_capacities.values())             
            for m in range(max_machines):
                if m not in task_capacities:
                    task_capacities[m] = default_task_cap

        if not(time_capacities):
            time_capacities = {m: sum(durations.values()) for m in range(max_machines)}
        else:
            default_time_cap = max(time_capacities.values())
            for m in range(max_machines):
                if m not in time_capacities:
                    time_capacities[m] = default_time_cap

         # Calcul de la borne inférieure théorique (Bin Packing Relaxation)
        total_duration = sum(durations.values())
        max_time_cap = max(time_capacities.values()) 
        min_machines_needed = math.ceil(total_duration / max_time_cap)
        print(f"Borne inférieure théorique calculée : {min_machines_needed} machines")
        print(f"Tâches: {self.n_tasks}")
        print(f"Conflits: {len(self.conflicts)}")
        print(f"Machines max: {max_machines}")
        self.model = gp.Model("MachineAssignment")
        self.model.setParam('TimeLimit', time_limit)
        self.model.setParam('MIPGap', 0.01)  # 1% d'optimalité
        # x[t,m] = 1 si tâche t est assignée à machine m
        x = {}
        for t in self.tasks:
            for m in range(max_machines):
                x[t, m] = self.model.addVar(vtype=GRB.BINARY, 
                                           name=f'x_{t}_{m}')
        # y[m] = 1 si machine m est utilisée
        y = {}
        for m in range(max_machines):
            y[m] = self.model.addVar(vtype=GRB.BINARY, 
                                    name=f'y_{m}')
        # Warm Start (Solution initiale greedy) On donne une piste au solveur pour trouver la première solution vite
        for t_idx, t in enumerate(self.tasks):
            m_target = t_idx % max_machines
            x[t, m_target].Start = 1
            y[m_target].Start = 1
        # Fonction objectif: minimiser le nombre de machines utilisées
        self.model.setObjective(
            gp.quicksum(y[m] for m in range(max_machines)),
            GRB.MINIMIZE)
        print("\nAjout des contraintes...")
        # Contrainte 1: Chaque tâche assignée à exactement une machine
        for t in self.tasks:
            self.model.addConstr(
                gp.quicksum(x[t, m] for m in range(max_machines)) == 1,
                name=f'assign_{t}')
        # Contrainte 2: Tâches en conflit sur des machines différentes
        # Au lieu de boucler sur self.conflicts(clique est un sous ensemble de tâches en conflit dans lequel chaque tache est en conflit avec toutes les autres du meme clique)
         # on utilise la détection de cliques pour renforcer le modèle
        cliques = list(nx.find_cliques(self.conflict_graph))
        for clique in cliques:
            for m in range(max_machines):
                self.model.addConstr(
                    gp.quicksum(x[t, m] for t in clique) <= y[m],
                    name=f'clique_m{m}')
        # Contrainte 3: Lier x et y (si tâche sur machine, alors machine utilisée)
        for t in self.tasks:
            for m in range(max_machines):
                self.model.addConstr(
                    x[t, m] <= y[m],
                    name=f'link_{t}_{m}')
        # Contrainte 4: Brisure de symétrie (ordre des machines)
        for m in range(max_machines - 1):
            self.model.addConstr(
                y[m] >= y[m + 1],
                name=f'symmetry_{m}')
        print(f"Variables: {self.model.NumVars}")
        print(f"Contraintes: {self.model.NumConstrs}")
        # Contrainte 5 : capacité machine (max tâches sur une même machine)
        for m in range(max_machines):
            self.model.addConstr(
                gp.quicksum(x[t, m] for t in self.tasks) <= float(task_capacities[m]) * y[m],
                name=f'cap_vol_{m}')
        # Contrainte 6 : charge cumulée (durée × tâche)
        for m in range(max_machines):
            self.model.addConstr(
                gp.quicksum(durations[t] * x[t, m] for t in self.tasks) <= time_capacities[m] * y[m],
                name=f'cap_time_{m}'
            )
        #  Limite sur le nombre de machines utilisées
        if max_machines is not None:
            # Vérification de sécurité pour éviter une infaisabilité immédiate
            if min_machines_needed > max_machines_dispo:
                print(f"ATTENTION: Le problème est mathématiquement infaisable !")
                print(f"Requis: {min_machines_needed}, Dispo: {max_machines_dispo}")
            
            self.model.addConstr(
                gp.quicksum(y[m] for m in range(max_machines)) <= max_machines_dispo,
                name='hard_limit_max_machines'
            )
        # Contrainte pour relaxation de Bin Packing
        self.model.addConstr(
            gp.quicksum(y[m] for m in range(max_machines)) >= min_machines_needed,
            name="lower_bound_machines")
        print("\nRésolution en cours...")
        self.model.optimize()
        if self.model.status == GRB.OPTIMAL or self.model.status == GRB.TIME_LIMIT:
            print("\n" + "="*60)
            print("SOLUTION TROUVÉE")
            print("="*60)
            self.n_machines_used = int(self.model.objVal)
            print(f"Nombre de machines utilisées: {self.n_machines_used}")
            # Extraire l'assignation
            self.assignment = {}
            for t in self.tasks:
                for m in range(max_machines):
                    if x[t, m].X > 0.5:
                        self.assignment[t] = m
                        break
            print(self.assignment)
            return self.assignment
        else:
            print(f"\nÉchec de résolution. Status: {self.model.status}")
            return None  
    """
    def solve_set_covering_model(self, time_limit=300):
        
        print("\n" + "="*60)
        print("MODÈLE SET COVERING (Ensembles Indépendants)")
        print("="*60)
        # Trouver tous les ensembles indépendants maximaux (ensemble de tâches qui peuvent s'executer sur la même machine)
        print("Génération des ensembles indépendants maximaux...")
        independent_sets = list(nx.find_cliques(nx.complement(self.conflict_graph)))
        print(f"Ensembles trouvés: {len(independent_sets)}")
        self.model = gp.Model("SetCovering")
        self.model.setParam('TimeLimit', time_limit)
        # Variables: z[S] = 1 si ensemble independant S est sélectionné (= machine)
        z = {}
        for i, S in enumerate(independent_sets):
            z[i] = self.model.addVar(vtype=GRB.BINARY, name=f'z_{i}')
        
        # Objectif: minimiser le nombre d'ensembles (machines)
        self.model.setObjective(
            gp.quicksum(z[i] for i in range(len(independent_sets))),
            GRB.MINIMIZE
        )
        # Contrainte: chaque tâche couverte par au moins un ensemble
        for t in self.tasks:
            sets_with_task = [i for i, S in enumerate(independent_sets) if t in S]
            self.model.addConstr(
                gp.quicksum(z[i] for i in sets_with_task) >= 1,
                name=f'cover_{t}'
            )
        print(f"Variables: {self.model.NumVars}")
        print(f"Contraintes: {self.model.NumConstrs}")
        print("\nRésolution en cours...")
        self.model.optimize()
        if self.model.status == GRB.OPTIMAL or self.model.status == GRB.TIME_LIMIT:
            print("\n" + "="*60)
            print("SOLUTION TROUVÉE")
            print("="*60)
            self.n_machines_used = int(self.model.objVal)
            print(f"Nombre de machines: {self.n_machines_used}")
            self.assignment = {}
            machine_id = 0
            for i, S in enumerate(independent_sets):
                if z[i].X > 0.5:
                    for t in S:
                        if t not in self.assignment:
                            self.assignment[t] = machine_id
                    machine_id += 1
            return self.assignment
        else:
            print(f"\nÉchec. Status: {self.model.status}")
            return None
    """
    