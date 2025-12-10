"""
Module pour partager les données entre les onglets
"""

class SharedData:
    """Classe singleton pour partager les données entre onglets"""
    _instance = None
    _last_client_data = None
    _last_loan_data = None
    _last_analysis_result = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def set_last_client_analysis(cls, client, pret, result):
        """Sauvegarde les dernières données analysées"""
        cls._last_client_data = client
        cls._last_loan_data = pret
        cls._last_analysis_result = result
    
    @classmethod
    def get_last_client_analysis(cls):
        """Récupère les dernières données analysées"""
        if cls._last_client_data and cls._last_loan_data:
            return {
                'client': cls._last_client_data,
                'pret': cls._last_loan_data,
                'result': cls._last_analysis_result
            }
        return None
    
    @classmethod
    def clear_data(cls):
        """Efface toutes les données partagées"""
        cls._last_client_data = None
        cls._last_loan_data = None
        cls._last_analysis_result = None