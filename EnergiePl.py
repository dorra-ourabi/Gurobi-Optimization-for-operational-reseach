# modele_gaz.py
import gurobipy as gp
from gurobipy import GRB


class ModeleGaz:
    """ Modélise et résout le problème de Flux à Coût Minimum (PL) avec Gurobi. """

    def __init__(self, donnees):
        self.donnees = donnees
        self.resultats = {}

    def resoudre(self):
        try:
            m = gp.Model("DistributionGaz_PL")
            m.setParam('OutputFlag', 0)

            Arcs = gp.tuplelist(self.donnees['Arcs'])
            Noeuds = self.donnees['Noeuds']
            Bilan = self.donnees['Bilan']
            Cout_Var = self.donnees['Cout_Var']
            Capacite = self.donnees['Capacite']

            # Variables de flux avec capacité et coût unitaire
            x = m.addVars(
                Arcs,
                vtype=GRB.CONTINUOUS,
                lb=0.0,
                ub=Capacite,
                obj=Cout_Var,
                name="Debit"
            )

            # Définir le sens de l'objectif (Minimisation)
            m.modelSense = GRB.MINIMIZE

            # Contraintes de Conservation de Flux
            m.addConstrs(
                (x.sum(i, '*') - x.sum('*', i) == Bilan[i] for i in Noeuds),
                name="Conservation"
            )

            m.optimize()

            self.resultats['statut'] = m.status

            if m.status == GRB.OPTIMAL:
                self.resultats['statut_text'] = "OPTIMAL"
                self.resultats['cout_total'] = m.ObjVal
                self.resultats['debits_optimaux'] = {
                    (i, j): x[i, j].X for i, j in Arcs
                }
            elif m.status == GRB.INFEASIBLE:
                self.resultats['statut_text'] = "IRRÉALISABLE (INFEASIBLE)"
            else:
                self.resultats['statut_text'] = f"Statut non optimal (Code Gurobi: {m.status})"

        except gp.GurobiError as e:
            self.resultats['statut_text'] = f"Erreur Gurobi : {e.message}"
        except Exception as e:
            self.resultats['statut_text'] = f"Erreur générale dans le modèle : {str(e)}"

        return self.resultats