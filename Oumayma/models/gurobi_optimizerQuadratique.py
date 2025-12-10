import gurobipy as gp
from gurobipy import GRB
import numpy as np
from typing import Dict
import math

from config.config_manager import ConfigManager
from models.risk_calculator import RiskCalculator, ClientProfile, PretDemande
from models.constraints_manager import ConstraintsManager
from models.market_analyzer import MarketAnalyzer


class GurobiOptimizerQuad:
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
            
            # 5. Création du modèle Gurobi
            self.model = gp.Model("Tarification_Optimale_Quadratique")
            self.model.setParam('OutputFlag', 0)
            
            # Variable de décision continue (Prix)
            r = self.model.addVar(lb=r_min, ub=r_max, name="taux_interet")
            
            # 6. Contraintes
            # Ratio endettement (approximation linéaire pour Gurobi)
            mensualite_max = R_max * client.revenu_mensuel - client.charges_mensuelles
            
            # Contrainte linéaire: Montant * r / (12 * Duree) <= Capacité
            # Note: C'est une approximation car la vraie formule des mensualités n'est pas linéaire
            self.model.addConstr(
                (pret.montant * r) / (pret.duree * 12) <= mensualite_max,
                "ratio_endettement_approx"
            )
            
            # 7. Fonction objectif Quadratique (QP)
            # Profit = Marge * Volume
            
            marge_unitaire = (
                pret.montant * pret.duree * (r - c_ref) - # Intérêts nets
                c_op -                                    # Coûts fixes
                pret.montant * PD * LGD                   # Coût du risque
            )
            
            # Correction formule demande ici : (r - r_bar) au lieu de (r_bar - r)
            demande_prevue = D_0 * (1 + epsilon * (r - r_bar))
            
            # Gurobi gère la multiplication (Variable * Variable) automatiquement -> QP
            self.model.setObjective(marge_unitaire * demande_prevue, GRB.MAXIMIZE)
            
            # 8. Résolution
            self.model.optimize()
            
            # 9. Extraction résultats
            if self.model.status == GRB.OPTIMAL:
                taux_optimal = r.X
                profit_opt = self.model.ObjVal
                
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
                # Tentative de relaxation
                return self._tenter_relaxation(client, pret, r_min, r_max, r_bar, epsilon, D_0)
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


def creer_optimiseur(config_path: str = "config/default_config.json") -> GurobiOptimizerQuad:
    """Crée une instance d'optimiseur - version simplifiée"""
    try:
        from config.config_manager import ConfigManager
        config = ConfigManager(config_path)
        return GurobiOptimizerQuad(config)
    except Exception as e:
        print(f"Erreur création optimiseur: {e}")
        raise