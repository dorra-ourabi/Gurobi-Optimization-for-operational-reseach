from typing import Tuple, Dict, Any

from config.config_manager import ConfigManager

class Validators:
    
    def __init__(self,config_manager):
        self.config = config_manager
    
    def validate_client_data(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        # Score crédit - récupéré depuis la config
        min_score = self.config.get('caracteristiques_client', 'score_credit', 'min', default=300)
        max_score = self.config.get('caracteristiques_client', 'score_credit', 'max', default=850)
        
        score = data.get('score_credit', 0)
        if not (min_score <= score <= max_score):
            return False, f"Score crédit invalide ({score}). Doit être entre {min_score} et {max_score}."
        
        # Revenu
        min_revenu = self.config.get('caracteristiques_client', 'revenu_mensuel', 'min', default=800)
        revenu = data.get('revenu_mensuel', 0)
        if revenu <= 0:
            return False, "Le revenu mensuel doit être positif."
        
        if revenu < min_revenu:
            return False, f"Le revenu mensuel doit être au moins {min_revenu}€."
        
        # Charges
        charges = data.get('charges_mensuelles', 0)
        if charges < 0:
            return False, "Les charges mensuelles ne peuvent pas être négatives."
        
        if charges >= revenu:
            return False, "Les charges mensuelles doivent être inférieures au revenu."
        
        # Ratio d'endettement - depuis la config
        ratio_max = self.config.get('contraintes_reglementaires', 'ratio_endettement_max', 'valeur', default=35.0) / 100
        ratio = charges / revenu if revenu > 0 else 0
        if ratio >= ratio_max:
            return False, f"Ratio d'endettement déjà au maximum ({ratio*100:.1f}% ≥ {ratio_max*100:.0f}%)."
        
        # Ancienneté
        anciennete = data.get('anciennete_pro', 0)
        if anciennete < 0:
            return False, "L'ancienneté professionnelle ne peut pas être négative."
        
        # Nombre de prêts - depuis la config
        max_prets = self.config.get('caracteristiques_client', 'nombre_prets_existants', 'max', default=10)
        nb_prets = data.get('nb_prets_existants', 0)
        if nb_prets < 0:
            return False, "Le nombre de prêts ne peut pas être négatif."
        
        if nb_prets > max_prets:
            return False, f"Trop de prêts existants (max {max_prets})."
        
        # Type de contrat - depuis la config
        types_contrat_valides = self.config.get('caracteristiques_client', 'type_contrat', 'options', 
                                               default=['CDI', 'CDD', 'Intérimaire', 'Indépendant', 'Fonctionnaire'])
        type_contrat = data.get('type_contrat', 'CDI')
        if type_contrat not in types_contrat_valides:
            return False, f"Type de contrat invalide. Choisir parmi: {', '.join(types_contrat_valides)}"
        
        return True, ""
    
    def validate_loan_data(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        # Type de prêt - depuis la config
        types_valides = self.config.get('types_prets', 'categories', 
                                       default=['immobilier', 'automobile', 'personnel', 'professionnel', 'etudiant'])
        
        # Montant
        montant = data.get('montant', 0)
        if montant <= 0:
            return False, "Le montant du prêt doit être positif."
        
        # Durée
        duree = data.get('duree', 0)
        if duree <= 0:
            return False, "La durée du prêt doit être positive."
        
        # Type de prêt
        type_pret = data.get('type_pret', '')
        if type_pret not in types_valides:
            return False, f"Type de prêt invalide. Choisir parmi: {', '.join(types_valides)}"
        
        # Apport
        apport = data.get('apport', 0)
        if apport < 0:
            return False, "L'apport ne peut pas être négatif."
        
        if apport >= montant:
            return False, "L'apport doit être inférieur au montant du prêt."
        
        # Validations spécifiques par type
        if type_pret == 'immobilier':
            apport_recommande = self.config.get('caracteristiques_client', 'apport_personnel', 'recommande_immo', default=15)
            apport_pourcent = (apport / montant * 100) if montant > 0 else 0
            if apport_pourcent < apport_recommande:
                return False, f"Apport insuffisant pour l'immobilier ({apport_pourcent:.1f}%). Minimum recommandé: {apport_recommande}%"
        
        # Contraintes générales avec fallback
        min_montant_global = 1000
        max_montant_global = 1000000
        if montant < min_montant_global:
            return False, f"Le montant minimum est de {min_montant_global}€."
        if montant > max_montant_global:
            return False, f"Le montant maximum est de {max_montant_global}€."
        
        min_duree_global = 0.5
        max_duree_global = 30
        if duree < min_duree_global:
            return False, f"La durée minimale est de {min_duree_global} ans."
        if duree > max_duree_global:
            return False, f"La durée maximale est de {max_duree_global} ans."
        
        return True, ""
    
    def validate_all(self, client_data: Dict, loan_data: Dict) -> Tuple[bool, str]:
        # Valider client
        valid_client, msg_client = self.validate_client_data(client_data)
        if not valid_client:
            return False, f"Données client: {msg_client}"
        
        # Valider prêt
        valid_loan, msg_loan = self.validate_loan_data(loan_data)
        if not valid_loan:
            return False, f"Données prêt: {msg_loan}"
        
        # Validations croisées
        revenu = client_data.get('revenu_mensuel', 0)
        montant = loan_data.get('montant', 0)
        duree = loan_data.get('duree', 1)
        
        # Vérifier que la mensualité estimée est raisonnable
        if duree > 0 and revenu > 0:
            mensualite_estimee = montant / (duree * 12)
            ratio_max = self.config.get('contraintes_reglementaires', 'ratio_endettement_max', 'valeur', default=35.0) / 100
            ratio_mensualite = mensualite_estimee / revenu
            
            if ratio_mensualite > ratio_max:
                return False, f"Mensualité estimée trop élevée ({mensualite_estimee:.0f}€, {ratio_mensualite*100:.1f}% du revenu). Maximum autorisé: {ratio_max*100:.0f}%"
        
        return True, "Toutes les validations sont passées"
    
    # Méthodes statiques pour compatibilité ascendante
    @staticmethod
    def validate_client_data_static(data: Dict[str, Any]) -> Tuple[bool, str]:
        """Version statique pour compatibilité (utilise une instance temporaire)"""
        validator = Validators()
        return validator.validate_client_data(data)
    
    @staticmethod
    def validate_loan_data_static(data: Dict[str, Any]) -> Tuple[bool, str]:
        """Version statique pour compatibilité"""
        validator = Validators()
        return validator.validate_loan_data(data)
    
    @staticmethod
    def validate_all_static(client_data: Dict, loan_data: Dict) -> Tuple[bool, str]:
        """Version statique pour compatibilité"""
        validator = Validators()
        return validator.validate_all(client_data, loan_data)