from config.config_manager import ConfigManager


class MarketAnalyzer:
    """Analyseur de marché et élasticité"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
    
    def get_elasticite(self, type_pret: str, segment: str) -> float:
        """
        Récupère l'élasticité ε_{i,j,k} pour le type de prêt et segment
        """
        elasticite = self.config.get(
            'parametres_marche', 'elasticite_prix_demande',
            type_pret, segment, default=-100
        )
        
        return elasticite
    
    def get_demande_base(self) -> float:
        """Récupère la demande de base D_0"""
        D_0 = self.config.get('parametres_marche', 'demande_base', default=100)
        
        # Ajustement selon scénario économique
        scenario = self.config.get('scenarios_economiques', 'scenario_actif', default='normal')
        facteur = self.config.get('scenarios_economiques', scenario, 'facteur_demande', default=1.0)
        
        return D_0 * facteur


