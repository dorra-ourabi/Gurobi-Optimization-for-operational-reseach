from gurobipy import Model, GRB, quicksum
from typing import List, Dict, Tuple
import sys

sys.path.append('..')
from data.parser import distance


def optimize_placement(sites: List[Dict], zones: List[Dict],
                       total_ambulances: int, max_distance: float,
                       mode: str = 'entier') -> Tuple[Dict[str, int], Dict]:

    if not sites or not zones:
        return {}, {'error': 'Données manquantes'}
    if total_ambulances <= 0:
        return {}, {'error': 'Budget invalide'}

    n_sites = len(sites)
    n_zones = len(zones)

    # Matrice de couverture
    coverage = [[0] * n_sites for _ in range(n_zones)]
    for j, zone in enumerate(zones):
        for i, site in enumerate(sites):
            if distance(site, zone) <= max_distance:
                coverage[j][i] = 1

    AVAIL_PROB = 0.60

    model = Model("Ambulances")
    model.Params.OutputFlag = 0
    model.Params.TimeLimit = 30

    # Variables : nombre d'ambulances par site
    if mode == 'binaire':
        x = model.addVars(n_sites, vtype=GRB.BINARY, lb=0, name="x")
    else:  # entier
        x = model.addVars(n_sites, vtype=GRB.INTEGER, lb=0, name="x")

    # Contrainte budget
    model.addConstr(quicksum(x[i] for i in range(n_sites)) <= total_ambulances, "Budget")

    # Capacités des sites
    for i, site in enumerate(sites):
        cap = site.get('capacity', 0)
        if cap > 0:
            model.addConstr(x[i] <= cap, f"Capacite_{i}")

    # Variable z[j] = 1 si zone couverte, k[j] = nb d'ambulances couvrantes
    z = model.addVars(n_zones, vtype=GRB.BINARY, name="z")

    # Variable k[j] = nombre d'ambulances couvrant la zone j
    k = model.addVars(n_zones, vtype=GRB.INTEGER, lb=0, name="k")

    M = total_ambulances
    for j in range(n_zones):
        model.addConstr(k[j] == quicksum(coverage[j][i] * x[i] for i in range(n_sites)))
        # Contraintes pour z[j]
        # Si z[j] = 1 → k[j] ≥ 1, si z[j] = 0 → k[j] = 0
        model.addConstr(k[j] >= z[j])
        model.addConstr(k[j] <= M * z[j])


    if mode == 'binaire':
        # objectif : maximiser population×priorité×z
        # logique : esk la zone est couverte ou non
        objective = quicksum(
            zones[j]['population'] *
            zones[j].get('priority', 1) *
            z[j]  # 1 si couverte, 0 sinon
            for j in range(n_zones)
        )

    else:  # mode entier
        # objectif : maximiser population×priorité×k
        # logique : "plus il y a d'ambulances, mieux c'est
        objective = quicksum(
            zones[j]['population'] *
            zones[j].get('priority', 1) *
            k[j]
            for j in range(n_zones)
        )
    model.setObjective(objective, GRB.MAXIMIZE)
    model.optimize()

    if model.status != GRB.OPTIMAL:
        return {}, {'error': 'Aucune solution trouvée. Essayez avec plus d\'ambulances ou une plus grande distance.'}

    # === Placement final ===
    placement = {}
    total_placed = 0
    for i in range(n_sites):
        nb = int(round(x[i].X))
        if nb > 0:
            placement[sites[i]['name']] = nb
            total_placed += nb

    # === Stats avec probabilité réelle ===
    pop_expected = 0
    details = []
    for j, zone in enumerate(zones):
        k_j = int(round(k[j].X))
        proba = 1 - (1 - AVAIL_PROB) ** k_j if k_j > 0 else 0
        contrib = zone['population'] * proba
        pop_expected += contrib
        details.append({
            'nom': zone['name'],
            'population': zone['population'],
            'ambulances': k_j,
            'probabilite_%': round(proba * 100, 1),
            'contribution': int(contrib)
        })

    total_pop = sum(z['population'] for z in zones) or 1

    stats = {
        'status': 'optimal',
        'total_ambulances_placed': total_placed,
        'total_ambulances_budget': total_ambulances,
        'population_covered': int(pop_expected),
        'total_population': total_pop,
        'coverage_percentage': round(pop_expected / total_pop * 100, 2),
        'details_zones': details
    }

    return placement, stats
