from dataclasses import dataclass
import numpy as np
from typing import Dict
from Oumayma.config.config_manager import ConfigManager

@dataclass
class ClientProfile:
    score_credit: float
    revenu_mensuel: float
    charges_mensuelles: float
    apport_personnel: float
    anciennete_pro: float
    nb_prets_existants: int
    historique_paiement: float
    type_contrat: str
    segment: str
    statut_client: str

@dataclass
class PretDemande:
    montant: float
    duree: float
    type_pret: str
    apport: float = 0

class RiskCalculator:
    """Calculateur de risque avec tous les paramètres"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
    
    def calculer_probabilite_defaut(self, client: ClientProfile) -> float:
        """
        Calcule PD avec TOUS les facteurs configurables
        PD_j = f(S_credit, D/R, A_prof, N_prets, H_pay, type_contrat, segment)
        """
        # Récupération des poids
        w1 = self.config.get('calcul_probabilite_defaut', 'poids_score_credit', default=5.0)
        w2 = self.config.get('calcul_probabilite_defaut', 'poids_ratio_endettement', default=3.0)
        w3 = self.config.get('calcul_probabilite_defaut', 'poids_nombre_prets', default=0.5)
        w4 = self.config.get('calcul_probabilite_defaut', 'poids_anciennete_pro', default=0.3)
        w5 = self.config.get('calcul_probabilite_defaut', 'poids_historique_paiement', default=2.0)
        w6 = self.config.get('calcul_probabilite_defaut', 'poids_type_contrat', default=1.5)
        z_offset = self.config.get('calcul_probabilite_defaut', 'decalage_logistique', default=3.0)
        
        # Normalisation du score (300-850 → 0-1)
        score_norm = (client.score_credit - 300) / (850 - 300)
        
        # Ratio d'endettement
        ratio_endettement = client.charges_mensuelles / client.revenu_mensuel if client.revenu_mensuel > 0 else 1
        
        # Poids du type de contrat
        poids_contrat = self.config.get('caracteristiques_client', 'type_contrat', 'poids_risque', 
                                       client.type_contrat, default=1.0)
        
        # Calcul du z-score composite
        z = (
            w1 * (1 - score_norm) +                      # Score faible = risque élevé
            w2 * ratio_endettement +                     # Endettement élevé = risque
            w3 * client.nb_prets_existants -             # Plusieurs prêts = risque
            w4 * min(client.anciennete_pro, 10) / 10 -   # Ancienneté = sécurité
            w5 * client.historique_paiement +            # Mauvais historique = risque
            w6 * (poids_contrat - 1)                     # Contrat précaire = risque
        )
        
        # Fonction logistique
        PD_base = 1 / (1 + np.exp(-z + z_offset))
        
        # Ajustement selon le segment
        multiplicateur_segment = self.config.get(
            'calcul_probabilite_defaut', 'ajustement_segment', 
            client.segment, 'multiplicateur_PD', default=1.0
        )
        PD_base *= multiplicateur_segment
        
        # Ajustement selon statut client (fidèle = moins de risque)
        bonus_statut = self.config.get(
            'caracteristiques_client', 'statut_client', 
            client.statut_client, 'bonus_taux', default=0.0
        )
        # Convertir bonus taux en réduction PD (approximatif)
        PD_base *= (1 + bonus_statut / 10)
        
        # Ajustement selon scénario économique
        scenario = self.config.get('scenarios_economiques', 'scenario_actif', default='normal')
        facteur_scenario = self.config.get(
            'scenarios_economiques', scenario, 'facteur_PD', default=1.0
        )
        PD_base *= facteur_scenario
        
        # Bornes min/max
        PD_min = self.config.get('calcul_probabilite_defaut', 'PD_minimum', default=0.1) / 100
        PD_max = self.config.get('calcul_probabilite_defaut', 'PD_maximum', default=15.0) / 100
        
        PD_final = max(PD_min, min(PD_max, PD_base))
        
        return PD_final
    
    def calculer_prime_risque(self, PD: float) -> float:
        """Convertit PD en prime de risque (en %)"""
        beta = self.config.get('calcul_probabilite_defaut', 'facteur_prime_risque', default=2.5)
        return PD * beta * 100  # Retourne en %

