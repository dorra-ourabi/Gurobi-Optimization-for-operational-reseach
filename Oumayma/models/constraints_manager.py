from Oumayma.config.config_manager import ConfigManager
from Oumayma.models.risk_calculator import ClientProfile, PretDemande

class ConstraintsManager:
    
    def __init__(self, config: ConfigManager):
        self.config = config
    
    def verifier_eligibilite(self, client: ClientProfile, pret: PretDemande) -> tuple[bool, list[str]]:
        """
        Vérifie l'éligibilité avant optimisation
        Retourne (eligible, liste_raisons_refus)
        """
        raisons = []
        
        # Score minimum
        score_min = self.config.get('contraintes_reglementaires', 'score_credit_minimum', default=600)
        if client.score_credit < score_min:
            raisons.append(f"Score crédit insuffisant ({client.score_credit} < {score_min})")
        
        # Ratio d'endettement actuel
        ratio_actuel = client.charges_mensuelles / client.revenu_mensuel if client.revenu_mensuel > 0 else 1
        ratio_max = self.config.get('contraintes_reglementaires', 'ratio_endettement_max', default=33) / 100
        
        if ratio_actuel >= ratio_max:
            raisons.append(f"Ratio d'endettement déjà au maximum ({ratio_actuel*100:.1f}% ≥ {ratio_max*100}%)")
        
        # Apport minimum pour immobilier
        if pret.type_pret == 'immobilier':
            apport_pourcent = (pret.apport / pret.montant * 100) if pret.montant > 0 else 0
            apport_min = self.config.get('caracteristiques_client', 'apport_personnel', 'recommande_immo', default=10)
            
            if apport_pourcent < apport_min:
                raisons.append(f"Apport insuffisant pour immobilier ({apport_pourcent:.1f}% < {apport_min}%)")
        
        return (len(raisons) == 0, raisons)
    
    def get_taux_usure(self, type_pret: str, duree: float) -> float:
        """Récupère le taux d'usure selon type et durée"""
        # Déterminer la catégorie de durée
        if duree < 2:
            categorie = 'court_terme'
        elif duree <= 7:
            categorie = 'moyen_terme'
        else:
            categorie = 'long_terme'
        
        taux = self.config.get(
            'contraintes_reglementaires', 'taux_usure', 
            type_pret, categorie, default=10.0
        )
        
        return taux / 100  # Retourne en décimal
    
    def get_taux_concurrent(self, type_pret: str, duree: float) -> float:
        """Récupère le taux concurrent selon type et durée"""
        if duree < 2:
            categorie = 'court_terme'
        elif duree <= 7:
            categorie = 'moyen_terme'
        else:
            categorie = 'long_terme'
        
        taux = self.config.get(
            'parametres_marche', 'taux_concurrents',
            type_pret, categorie, default=5.0
        )
        
        return taux / 100
