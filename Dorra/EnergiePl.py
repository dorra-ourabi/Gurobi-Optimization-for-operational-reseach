import gurobipy as gp
from gurobipy import GRB

class ModeleGaz:
    """
    Modèle de Flux à Coût Minimum pour un réseau de gaz,
    avec options avancées : coûts fixes, capacité min, pressions, pertes, diamètres, redondance.
    """

    def __init__(self, donnees):
        """
        donnees: dict contenant
            - 'Noeuds': liste de nœuds
            - 'Arcs': liste de tuples (i,j)
            - 'Bilan': dict {noeud: bilan}
            - 'Cout_Var': dict {(i,j): coût variable}
            - 'Capacite': dict {(i,j): capacité max}
        Optionnel selon activation :
            - 'Cout_Fixe', 'Capacite_Min', 'Pression_Min', 'Pression_Max',
              'Perte_Charge', 'Longueur', 'Diametre', 'Vitesse_Max', 'Contrainte_Redondance', 'Noeuds_Critiques'
        """
        self.donnees = donnees
        self.resultats = {}

    def resoudre(self):
        try:
            m = gp.Model("DistributionGaz_Enrichi")
            m.setParam('OutputFlag', 0)

            Arcs = gp.tuplelist(self.donnees['Arcs'])
            Noeuds = self.donnees['Noeuds']
            Bilan = self.donnees['Bilan']
            Cout_Var = self.donnees['Cout_Var']
            Capacite = self.donnees['Capacite']

            # Détection des fonctionnalités activées
            use_fixed = 'Cout_Fixe' in self.donnees
            use_min = 'Capacite_Min' in self.donnees
            use_press = 'Pression_Min' in self.donnees or 'Pression_Max' in self.donnees
            use_losses = 'Perte_Charge' in self.donnees
            use_diam = 'Diametre' in self.donnees
            use_redund = self.donnees.get('Contrainte_Redondance', False)

            # === VARIABLES ===
            x = m.addVars(Arcs, vtype=GRB.CONTINUOUS, lb=0.0, ub=Capacite, name="Debit")
            if use_fixed or use_min:
                y = m.addVars(Arcs, vtype=GRB.BINARY, name="ArcActif")
            if use_press or use_losses:
                p_min = self.donnees.get('Pression_Min', {})
                p_max = self.donnees.get('Pression_Max', {})
                p = m.addVars(Noeuds, vtype=GRB.CONTINUOUS,
                              lb={i: p_min.get(i, 1.0) for i in Noeuds},
                              ub={i: p_max.get(i, 10.0) for i in Noeuds},
                              name="Pression")

            # === OBJECTIF ===
            obj = gp.quicksum(Cout_Var[i,j]*x[i,j] for i,j in Arcs)
            if use_fixed:
                Cout_Fixe = self.donnees['Cout_Fixe']
                obj += gp.quicksum(Cout_Fixe[i,j]*y[i,j] for i,j in Arcs)
            m.setObjective(obj, GRB.MINIMIZE)

            # === CONTRAINTES ===
            # Conservation de flux
            m.addConstrs((x.sum(i,'*') - x.sum('*',i) == Bilan[i] for i in Noeuds), name="Conservation")

            # Liaison flux-activation
            if use_fixed or use_min:
                M = {arc: Capacite[arc] for arc in Arcs}
                m.addConstrs((x[i,j] <= M[i,j]*y[i,j] for i,j in Arcs), name="BigM")
            # Capacités minimales
            if use_min:
                Capacite_Min = self.donnees['Capacite_Min']
                m.addConstrs((x[i,j] >= Capacite_Min[i,j]*y[i,j] for i,j in Arcs if Capacite_Min[i,j]>0),
                             name="CapMin")
            # Pertes de charge
            if use_losses:
                Perte_Charge = self.donnees['Perte_Charge']
                Longueur = self.donnees.get('Longueur', {arc:1.0 for arc in Arcs})
                M_pres = 20.0
                for i,j in Arcs:
                    if Perte_Charge[i,j]>0:
                        perte = Perte_Charge[i,j]*Longueur.get((i,j),1.0)
                        if use_fixed or use_min:
                            m.addConstr(p[i]-p[j] >= perte*x[i,j]-M_pres*(1-y[i,j]), name=f"Perte_{i}_{j}")
                        else:
                            m.addConstr(p[i]-p[j] >= perte*x[i,j], name=f"Perte_{i}_{j}")
            # Diamètre / vitesse
            if use_diam:
                Diametre = self.donnees['Diametre']
                V_max = self.donnees.get('Vitesse_Max',20.0)
                for i,j in Arcs:
                    if Diametre[i,j]>0:
                        section = 3.14159*(Diametre[i,j]/2)**2
                        debit_max_v = section*V_max
                        if debit_max_v < Capacite[i,j]:
                            m.addConstr(x[i,j]<=debit_max_v, name=f"Vmax_{i}_{j}")
            # Redondance
            if use_redund and use_fixed:
                noeuds_crit = self.donnees.get('Noeuds_Critiques', [])
                for node in noeuds_crit:
                    arcs_in = [arc for arc in Arcs if arc[1]==node]
                    if len(arcs_in)>=2:
                        m.addConstr(gp.quicksum(y[arc] for arc in arcs_in)>=2,
                                    name=f"Redondance_{node}")

            # === RÉSOLUTION ===
            m.optimize()

            self.resultats['statut'] = m.status
            if m.status==GRB.OPTIMAL:
                self.resultats['statut_text']="OPTIMAL"
                self.resultats['cout_total']=m.ObjVal
                self.resultats['debits_optimaux']={(i,j):x[i,j].X for i,j in Arcs}
                if use_fixed or use_min:
                    self.resultats['arcs_actifs']={(i,j):y[i,j].X for i,j in Arcs}
                if use_press or use_losses:
                    self.resultats['pressions']={i:p[i].X for i in Noeuds}
            elif m.status==GRB.INFEASIBLE:
                self.resultats['statut_text']="IRRÉALISABLE"
            else:
                self.resultats['statut_text']=f"Statut non optimal (code {m.status})"

        except gp.GurobiError as e:
            self.resultats['statut_text']=f"Erreur Gurobi : {e.message}"
        except Exception as e:
            self.resultats['statut_text']=f"Erreur générale : {str(e)}"

        return self.resultats