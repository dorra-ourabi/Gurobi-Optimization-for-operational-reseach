import gurobipy as gp
from gurobipy import GRB
import numpy as np
from typing import Dict
import math

from Oumayma.config.config_manager import ConfigManager
from Oumayma.models.risk_calculator import RiskCalculator, ClientProfile, PretDemande
from Oumayma.models.constraints_manager import ConstraintsManager
from Oumayma.models.market_analyzer import MarketAnalyzer


class GurobiOptimizer:
    def __init__(self, config: ConfigManager):
        self.config = config
        self.risk_calc = RiskCalculator(config)
        self.constraints = ConstraintsManager(config)
        self.market = MarketAnalyzer(config)
        self.model = None
        
    def optimiser_taux(self, client: ClientProfile, pret: PretDemande) -> Dict:
        # 1. Vérification d'éligibilité
        eligible, raisons = self.constraints.verifier_eligibilite(client, pret)
        if not eligible:
            return {
                'status': 'REFUSE',
                'raisons': raisons,
                'eligible': False
            }
        
        try:
            # 2. Calcul des paramètres
            PD = self.risk_calc.calculer_probabilite_defaut(client)
            prime_risque_pourcent = self.risk_calc.calculer_prime_risque(PD)
            prime_risque_decimal = prime_risque_pourcent / 100
            
            # 3. Récupération des paramètres
            c_ref = self.config.get('couts_et_risques', 'cout_refinancement', default=2.7) / 100
            m_min = self.config.get('couts_et_risques', 'marge_minimale', default=0.5) / 100
            LGD = self.config.get('couts_et_risques', 'perte_en_cas_defaut_LGD', default=45.0) / 100
            c_op = self.config.get('couts_et_risques', 'couts_operationnels', pret.type_pret, default=500)
            
            # Taux usure et concurrent selon durée
            r_usure = self.constraints.get_taux_usure(pret.type_pret, pret.duree)
            r_bar = self.constraints.get_taux_concurrent(pret.type_pret, pret.duree)
            
            # Paramètres de marché
            D_0 = self.market.get_demande_base()
            epsilon = self.market.get_elasticite(pret.type_pret, client.segment)
            alpha = self.config.get('parametres_marche', 'marge_competitive_max', default=10.0) / 100
            
            R_max = self.config.get('contraintes_reglementaires', 'ratio_endettement_max', default=33.0) / 100
            
            # 4. Calcul des bornes du taux
            # Formule corrigée: r_min = coût de refinancement + marge min + prime risque
            r_min = c_ref + m_min + prime_risque_decimal
            r_max = min(r_usure, r_bar * (1 + alpha))
            
            # Ajustement prime durée
            if self.config.get('parametres_avances', 'activer_ajustement_duree', default=True):
                prime_duree_par_an = self.config.get('parametres_avances', 'prime_duree_par_an', default=0.05) / 100
                prime_duree = pret.duree * prime_duree_par_an
                r_min += prime_duree
            
            # Bonus apport
            bonus_apport = 0
            if self.config.get('parametres_avances', 'activer_bonus_apport', default=True):
                seuil_apport = self.config.get('parametres_avances', 'seuil_apport_bonus', default=20)
                apport_pourcent = (pret.apport / pret.montant * 100) if pret.montant > 0 else 0
                if apport_pourcent >= seuil_apport:
                    bonus_apport = self.config.get('parametres_avances', 'reduction_taux_apport', default=0.10) / 100
                    r_max = min(r_max, r_bar * (1 + alpha) - bonus_apport)
            
            # Vérification faisabilité
            if r_min > r_max:
                return {
                    'status': 'IMPOSSIBLE',
                    'raison': f'Taux minimum rentable ({r_min*100:.2f}%) supérieur au taux maximum autorisé ({r_max*100:.2f}%)',
                    'r_min_pourcent': r_min * 100,
                    'r_max_pourcent': r_max * 100
                }
            
            # 1. Définition de la grille de recherche (Discrétisation)
            # On teste par exemple tous les taux entre r_min et r_max avec un pas de 0.05%
            # Plus le pas est fin, plus c'est précis, mais plus il y a de variables binaires.
            pas = 0.0005 # 0.05%
            grid_taux = np.arange(r_min, r_max + pas, pas)
            
            scenarios = []
            
            # 2. Pré-calcul Python (C'est ici qu'on utilise les 33 variables avec exactitude)
            for i, r_test in enumerate(grid_taux):
                
                # A. Calcul EXACT de la mensualité (Formule non-linéaire complexe)
                # On peut le faire ici car c'est du Python, pas une contrainte Gurobi
                mensualite_exacte = self._calculate_monthly_payment(pret.montant, r_test, pret.duree)
                
                # B. Vérification stricte des contraintes (Hard Filtering)
                # Ratio d'endettement
                nouveau_ratio = (client.charges_mensuelles + mensualite_exacte) / client.revenu_mensuel
                if nouveau_ratio > R_max:
                    continue # On jette ce scénario, il est illégal
                    
                # C. Calcul de la demande et du profit (Votre formule quadratique)
                # Attention à la formule corrigée de l'élasticité !
                demande_prevue = D_0 * (1 + epsilon * (r_test - r_bar))
                if demande_prevue <= 0:
                    continue
                    
                marge_unitaire = (
                    pret.montant * pret.duree * (r_test - c_ref) - 
                    c_op - 
                    pret.montant * PD * LGD
                )
                
                profit_total = marge_unitaire * demande_prevue
                
                # On stocke ce scénario valide
                scenarios.append({
                    'id': i,
                    'taux': r_test,
                    'profit': profit_total,
                    'demande': demande_prevue,
                    'mensualite': mensualite_exacte,
                    'ratio': nouveau_ratio
                })
            
            if not scenarios:
                return {'status': 'IMPOSSIBLE', 'raison': 'Aucun taux ne respecte les critères'}

            # 3. Modèle Gurobi PLM (Programmation Linéaire Mixte)
            self.model = gp.Model("Tarification_Discrete")
            self.model.setParam('OutputFlag', 0)
            
            # Variables Binaires : x[i] = 1 si on choisit le scénario i
            x = {}
            for s in scenarios:
                x[s['id']] = self.model.addVar(vtype=GRB.BINARY, name=f"scen_{s['id']}")
                
            # Contrainte 1 : On doit choisir EXACTEMENT UN scénario
            self.model.addConstr(gp.quicksum(x[s['id']] for s in scenarios) == 1, "choix_unique")
            
            # Fonction Objectif : Maximiser la somme des (Profit_i * x_i)
            # Comme un seul x_i vaut 1, cela revient à maximiser le profit du scénario choisi
            obj_expr = gp.quicksum(s['profit'] * x[s['id']] for s in scenarios)
            self.model.setObjective(obj_expr, GRB.MAXIMIZE)
            
            # 4. Résolution
            self.model.optimize()
            
            # 5. Récupération
            if self.model.status == GRB.OPTIMAL:
                # Retrouver quel scénario a été choisi
                best_scen = None
                for s in scenarios:
                    if x[s['id']].X > 0.5: # Si la variable binaire est à 1
                        best_scen = s
                        break
                
                return self._construire_resultats_complets(
                    best_scen['taux'], best_scen['demande'], best_scen['profit'],
                    client, pret, PD, prime_risque_pourcent,
                    r_bar, r_usure, bonus_apport,
                    c_ref, m_min, c_op, LGD, R_max
                )
                
        except gp.GurobiError as e:
            return {
                'status': 'ERROR_GUROBI',
                'raison': f'Erreur Gurobi: {str(e)}'
            }
        except Exception as e:
            return {
                'status': 'ERROR',
                'raison': f'Erreur générale: {str(e)}'
            }
    
    def _tenter_relaxation(self, client, pret, r_min, r_max, r_bar, epsilon, D_0):
        """Tente une relaxation des contraintes"""
        try:
            # Créer un nouveau modèle sans contrainte de ratio
            model2 = gp.Model("Tarification_Relaxee")
            model2.setParam('OutputFlag', 0)
            
            # Variables
            r = model2.addVar(lb=r_min, ub=r_max, name="taux_interet")
            
            # Paramètres simplifiés
            c_ref = self.config.get('couts_et_risques', 'cout_refinancement', default=2.7) / 100
            PD = self.risk_calc.calculer_probabilite_defaut(client)
            LGD = self.config.get('couts_et_risques', 'perte_en_cas_defaut_LGD', default=45.0) / 100
            c_op = self.config.get('couts_et_risques', 'couts_operationnels', pret.type_pret, default=500)
            
            # Objectif simplifié
            profit_unitaire = pret.montant * pret.duree * (r - c_ref) - c_op - pret.montant * PD * LGD
            demande = D_0 * (1 + epsilon * (r_bar - r))
            profit_total = demande * profit_unitaire
            
            model2.setObjective(profit_total, GRB.MAXIMIZE)
            model2.optimize()
            
            if model2.status == GRB.OPTIMAL:
                taux_optimal = r.X
                return {
                    'status': 'ACCEPTE_RELAXE',
                    'taux_optimal': taux_optimal * 100,
                    'note': 'Solution relaxée (ratio endettement ignoré)',
                    'mensualite': self._calculate_monthly_payment(pret.montant, taux_optimal, pret.duree)
                }
            else:
                return {
                    'status': 'INFEASIBLE',
                    'raison': 'Aucune solution même avec relaxation'
                }
                
        except Exception as e:
            return {
                'status': 'ERROR_RELAX',
                'raison': f'Erreur relaxation: {str(e)}'
            }
    
    def _construire_resultats_complets(self, taux: float, demande: float, profit: float,
                                      client: ClientProfile, pret: PretDemande,
                                      PD: float, prime_risque: float,
                                      r_bar: float, r_usure: float, 
                                      bonus_apport: float,
                                      c_ref: float, m_min: float, c_op: float,
                                      LGD: float, R_max: float) -> Dict:
        
        # Calcul mensualité exacte
        mensualite = self._calculate_monthly_payment(pret.montant, taux, pret.duree)
        
        # Calculs financiers
        cout_total = mensualite * pret.duree * 12
        interets_totaux = cout_total - pret.montant
        
        # TAEG (simplifié)
        TAEG = taux  # Pour simplifier, on prend le taux nominal
        
        # Décomposition du taux
        decomposition = {
            'base_refinancement': c_ref * 100,
            'marge_minimale': m_min * 100,
            'prime_risque': prime_risque,
            'bonus_apport': -bonus_apport * 100 if bonus_apport > 0 else 0,
            'ajustement_marche': (taux * 100) - (c_ref * 100 + m_min * 100 + prime_risque - bonus_apport * 100)
        }
        
        # Nouveau ratio d'endettement
        charges_totales = client.charges_mensuelles + mensualite
        nouveau_ratio = (charges_totales / client.revenu_mensuel) * 100 if client.revenu_mensuel > 0 else 0
        
        # Profitabilité détaillée
        revenus = pret.montant * taux * pret.duree
        cout_ref_total = pret.montant * c_ref * pret.duree
        perte_attendue = pret.montant * PD * LGD
        
        profit_unitaire = revenus - cout_ref_total - c_op - perte_attendue
        
        profitabilite = {
            'revenus_interets': round(revenus, 2),
            'cout_refinancement': round(cout_ref_total, 2),
            'cout_operationnel': round(c_op, 2),
            'perte_attendue': round(perte_attendue, 2),
            'profit_unitaire': round(profit_unitaire, 2),
            'profit_total_estime': round(profit, 2),
            'marge_nette': round((profit_unitaire / revenus * 100) if revenus > 0 else 0, 2)
        }
        
        # Conformité
        conformite = {
            'taux_usure': taux <= r_usure,
            'ratio_endettement': nouveau_ratio <= R_max * 100,
            'score_minimum': client.score_credit >= 600,
            'TAEG_conforme': TAEG <= r_usure
        }
        
        # Comparaison marché
        ecart = taux * 100 - r_bar * 100
        
        # Résultat final
        return {
            'status': 'ACCEPTE',
            'taux_optimal': round(taux * 100, 3),
            'TAEG': round(TAEG * 100, 3),
            'mensualite': round(mensualite, 2),
            'cout_total': round(cout_total, 2),
            'interets_totaux': round(interets_totaux, 2),
            'demande_estimee': round(demande, 1),
            'probabilite_defaut': round(PD * 100, 3),
            'nouveau_ratio_endettement': round(nouveau_ratio, 2),
            'decomposition_taux': decomposition,
            'profitabilite': profitabilite,
            'conformite': conformite,
            'comparaison_marche': {
                'taux_concurrent': round(r_bar * 100, 3),
                'ecart': round(ecart, 3),
                'position': 'Au-dessus' if ecart > 0 else ('Égal' if ecart == 0 else 'En-dessous'),
                'competitivite': 'Excellent' if abs(ecart) < 0.2 else 'Bon' if abs(ecart) < 0.5 else 'Moyen'
            },
            'metriques_risque': {
                'score_credit': client.score_credit,
                'segment': client.segment,
                'PD_pourcent': round(PD * 100, 3),
                'LGD_pourcent': round(LGD * 100, 1),
                'EL_euros': round(perte_attendue, 2)
            },
            'eligible': True,
            'model_status': 'OPTIMAL'
        }
    
    def _calculate_monthly_payment(self, amount: float, annual_rate: float, years: float) -> float:
        """Calcule la mensualité exacte avec formule d'annuité"""
        if annual_rate == 0:
            return amount / (years * 12)
        
        monthly_rate = annual_rate / 12
        months = years * 12
        
        mensualite = amount * (monthly_rate * (1 + monthly_rate) ** months) / \
                    ((1 + monthly_rate) ** months - 1)
        
        return mensualite
    
    def cleanup(self):
        """Nettoie les ressources"""
        if self.model:
            self.model.dispose()
            self.model = None


def creer_optimiseur(config_path: str = "config/default_config.json") -> GurobiOptimizer:
    """Crée une instance d'optimiseur - version simplifiée"""
    try:
        from config.config_manager import ConfigManager
        config = ConfigManager(config_path)
        return GurobiOptimizer(config)
    except Exception as e:
        print(f"Erreur création optimiseur: {e}")
        raise