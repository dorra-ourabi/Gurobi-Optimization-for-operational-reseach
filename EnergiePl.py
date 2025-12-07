import gurobipy as gp
from gurobipy import GRB

# 1. Définition des données (Le Réseau de Gaz)
# Liste des nœuds
noeuds = ['S', 'A', 'B', 'T']

# Arcs (Tuyaux) et leurs attributs : (Départ, Arrivée) -> [Coût, Capacité]
arcs, couts, capacites = gp.multidict({
    ('S', 'A'): [2, 10],
    ('S', 'B'): [1, 10],
    ('A', 'B'): [1, 5],
    ('A', 'T'): [3, 8],
    ('B', 'T'): [5, 8]
})

# Demande/Offre aux nœuds (b_i)
# S produit 15, T consomme 15, les autres sont neutres
bilan = {'S': 15, 'A': 0, 'B': 0, 'T': -15}

# 2. Création du modèle
model = gp.Model("Distribution_Gaz_Gurobi")

# 3. Création des variables de décision
# model.addVars crée toutes les variables d'un coup basées sur la liste des arcs
# ub=capacites : fixe la borne supérieure (Upper Bound) pour chaque arc
# obj=couts : définit directement le coefficient dans la fonction objectif (minimisation par défaut)
x = model.addVars(arcs, ub=capacites, obj=couts, name="flux")

# 4. Sens de l'optimisation (Optionnel car Minimiser est le défaut, mais explicite c'est mieux)
model.modelSense = GRB.MINIMIZE

# 5. Contraintes de Conservation de Flux
# Pour chaque nœud i, la somme des flux sortants moins les entrants doit égaler le bilan
# x.sum(i, '*') : Somme de tout ce qui part de i vers n'importe où (*)
# x.sum('*', i) : Somme de tout ce qui arrive à i de n'importe où (*)
model.addConstrs(
    (x.sum(i, '*') - x.sum('*', i) == bilan[i] for i in noeuds),
    name="Conservation"
)

# 6. Résolution
model.optimize()

# 7. Affichage des résultats
if model.status == GRB.OPTIMAL:
    print(f"\nCoût Total Minimum : {model.objVal}")
    print("Flux optimal dans le réseau :")
    for i, j in arcs:
        # x[i,j].x permet d'accéder à la valeur numérique de la variable
        if x[i, j].x > 0:
            print(f"Tuyau {i} -> {j} : {x[i, j].x} unités")
else:
    print("Pas de solution optimale trouvée.")