import gurobipy as gp
from gurobipy import GRB
import numpy as np
from typing import Dict

from config.config_manager import ConfigManager
from models.risk_calculator import RiskCalculator, ClientProfile, PretDemande
from models.constraints_manager import ConstraintsManager
from models.market_analyzer import MarketAnalyzer


class GurobiOptimizer:
    """Optimiseur avec fonction objective LINÉARISÉE par morceaux"""
    
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
            # 2. Calcul des paramètres (33 VARIABLES CONSERVÉES)
            PD = self.risk_calc.calculer_probabilite_defaut(client)
            prime_risque_pourcent = self.risk_calc.calculer_prime_risque(PD)
            prime_risque_decimal = prime_risque_pourcent / 100
            
            # 3. Récupération de TOUTES les variables
            c_ref = self.config.get('couts_et_risques', 'cout_refinancement', default=2.7) / 100
            m_min = self.config.get('couts_et_risques', 'marge_minimale', default=0.5) / 100
            LGD = self.config.get('couts_et_risques', 'perte_en_cas_defaut_LGD', default=45.0) / 100
            c_op = self.config.get('couts_et_risques', 'couts_operationnels', pret.type_pret, default=500)
            
            # Taux usure et concurrent
            r_usure = self.constraints.get_taux_usure(pret.type_pret, pret.duree)
            r_bar = self.constraints.get_taux_concurrent(pret.type_pret, pret.duree)
            
            # Paramètres de marché
            D_0 = self.market.get_demande_base()
            epsilon = self.market.get_elasticite(pret.type_pret, client.segment)
            alpha = self.config.get('parametres_marche', 'marge_competitive_max', default=10.0) / 100
            
            R_max = self.config.get('contraintes_reglementaires', 'ratio_endettement_max', default=33.0) / 100
            
            # 4. Calcul des bornes du taux
            r_min = c_ref + m_min + prime_risque_decimal
            r_max = min(r_usure, r_bar * (1 + alpha))
            
            # Ajustements durée et apport
            if self.config.get('parametres_avances', 'activer_ajustement_duree', default=True):
                prime_duree_par_an = self.config.get('parametres_avances', 'prime_duree_par_an', default=0.05) / 100
                prime_duree = pret.duree * prime_duree_par_an
                r_min += prime_duree
            
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
            
            # ===== 5. LINÉARISATION PAR MORCEAUX (PWL) =====
            self.model = gp.Model("Tarification_Lineaire_PWL")
            self.model.setParam('OutputFlag', 0)
            
            # Variable de décision : taux d'intérêt
            r = self.model.addVar(lb=r_min, ub=r_max, name="taux_interet")
            
            # Créer des points pour l'approximation PWL
            n_segments = 20  # Nombre de segments pour l'approximation
            r_points = np.linspace(r_min, r_max, n_segments + 1)
            
            # Calculer la fonction profit EXACTE à chaque point
            profit_points = []
            for r_val in r_points:
                demande = D_0 * (1 + epsilon * (r_bar - r_val))
                demande = max(0, demande)  # Demande non négative
                
                profit_unitaire = (
                    pret.montant * pret.duree * (r_val - c_ref) -
                    c_op -
                    pret.montant * PD * LGD
                )
                
                profit_total = demande * profit_unitaire
                profit_points.append(profit_total)
            
            # Utiliser addGenConstrPWL pour l'approximation linéaire par morceaux
            profit_var = self.model.addVar(lb=-GRB.INFINITY, name="profit_total")
            self.model.addGenConstrPWL(r, profit_var, r_points.tolist(), profit_points, "pwl_profit")
            
            # 6. Contrainte ratio d'endettement (LINÉAIRE)
            mensualite_max = R_max * client.revenu_mensuel - client.charges_mensuelles
            if mensualite_max <= 0:
                return {
                    'status': 'REFUSE',
                    'raison': f'Capacité de remboursement insuffisante. Mensualité max: {mensualite_max:.2f}€'
                }
            
            # Approximation linéaire: mensualité ≈ prêt * taux / (durée * 12)
            self.model.addConstr(
                (pret.montant * r) / (pret.duree * 12) <= mensualite_max,
                "ratio_endettement_lineaire"
            )
            
            # 7. Fonction objectif : MAXIMISER le profit linéarisé
            self.model.setObjective(profit_var, GRB.MAXIMIZE)
            
            # 8. Résolution
            self.model.optimize()
            
            # 9. Extraction résultats
            if self.model.status == GRB.OPTIMAL:
                taux_optimal = r.X
                profit_opt = profit_var.X
                
                # Calcul demande réelle
                demande_opt = D_0 * (1 + epsilon * (r_bar - taux_optimal))
                if demande_opt < 0:
                    demande_opt = 0
                
                return self._construire_resultats_complets(
                    taux_optimal, demande_opt, profit_opt,
                    client, pret, PD, prime_risque_pourcent,
                    r_bar, r_usure, bonus_apport,
                    c_ref, m_min, c_op, LGD, R_max
                )
            elif self.model.status == GRB.INFEASIBLE:
                return self._tenter_relaxation(client, pret, r_min, r_max)
            else:
                return {
                    'status': 'ERROR',
                    'raison': f'Erreur Gurobi: statut {self.model.status}'
                }
                
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
    
    def _tenter_relaxation(self, client, pret, r_min, r_max):
        """Version simplifiée sans contrainte d'endettement"""
        try:
            model2 = gp.Model("Tarification_Relaxee")
            model2.setParam('OutputFlag', 0)
            
            r = model2.addVar(lb=r_min, ub=r_max, name="taux_interet")
            
            # Paramètres simplifiés
            c_ref = self.config.get('couts_et_risques', 'cout_refinancement', default=2.7) / 100
            PD = self.risk_calc.calculer_probabilite_defaut(client)
            LGD = self.config.get('couts_et_risques', 'perte_en_cas_defaut_LGD', default=45.0) / 100
            c_op = self.config.get('couts_et_risques', 'couts_operationnels', pret.type_pret, default=500)
            
            # PWL simplifiée
            r_bar = self.constraints.get_taux_concurrent(pret.type_pret, pret.duree)
            D_0 = self.market.get_demande_base()
            epsilon = self.market.get_elasticite(pret.type_pret, client.segment)
            
            r_points = np.linspace(r_min, r_max, 15)
            profit_points = []
            for r_val in r_points:
                demande = max(0, D_0 * (1 + epsilon * (r_bar - r_val)))
                profit_unit = pret.montant * pret.duree * (r_val - c_ref) - c_op - pret.montant * PD * LGD
                profit_points.append(demande * profit_unit)
            
            profit_var = model2.addVar(lb=-GRB.INFINITY, name="profit")
            model2.addGenConstrPWL(r, profit_var, r_points.tolist(), profit_points, "pwl")
            model2.setObjective(profit_var, GRB.MAXIMIZE)
            model2.optimize()
            
            if model2.status == GRB.OPTIMAL:
                return {
                    'status': 'ACCEPTE_RELAXE',
                    'taux_optimal': r.X * 100,
                    'note': 'Solution relaxée (ratio endettement ignoré)',
                    'mensualite': self._calculate_monthly_payment(pret.montant, r.X, pret.duree)
                }
            else:
                return {'status': 'INFEASIBLE', 'raison': 'Aucune solution trouvée'}
                
        except Exception as e:
            return {'status': 'ERROR_RELAX', 'raison': f'Erreur relaxation: {str(e)}'}
    
    def _construire_resultats_complets(self, taux: float, demande: float, profit: float,
                                      client: ClientProfile, pret: PretDemande,
                                      PD: float, prime_risque: float,
                                      r_bar: float, r_usure: float, 
                                      bonus_apport: float,
                                      c_ref: float, m_min: float, c_op: float,
                                      LGD: float, R_max: float) -> Dict:
        
        mensualite = self._calculate_monthly_payment(pret.montant, taux, pret.duree)
        cout_total = mensualite * pret.duree * 12
        interets_totaux = cout_total - pret.montant
        TAEG = taux
        
        decomposition = {
            'base_refinancement': c_ref * 100,
            'marge_minimale': m_min * 100,
            'prime_risque': prime_risque,
            'bonus_apport': -bonus_apport * 100 if bonus_apport > 0 else 0,
            'ajustement_marche': (taux * 100) - (c_ref * 100 + m_min * 100 + prime_risque - bonus_apport * 100)
        }
        
        nouveau_ratio = ((client.charges_mensuelles + mensualite) / client.revenu_mensuel) * 100
        
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
        
        conformite = {
            'taux_usure': taux <= r_usure,
            'ratio_endettement': nouveau_ratio <= R_max * 100,
            'score_minimum': client.score_credit >= 600,
            'TAEG_conforme': TAEG <= r_usure
        }
        
        ecart = taux * 100 - r_bar * 100
        
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
            'model_status': 'OPTIMAL_LINEARIZED',
            'linearization_method': 'PWL_20_segments'
        }
    
    def _calculate_monthly_payment(self, amount: float, annual_rate: float, years: float) -> float:
        """Calcule la mensualité exacte"""
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