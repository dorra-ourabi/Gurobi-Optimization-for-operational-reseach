"""
Fonctions de formatage des données
"""
import locale
from typing import Dict, List, Union

class Formatters:
    """Classe de formatage des données"""
    
    @staticmethod
    def format_currency(value: float) -> str:
        """Formate un montant en euros"""
        try:
            locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')
            return locale.currency(value, grouping=True)
        except:
            # Fallback si locale non disponible
            return f"{value:,.2f} €"
    
    @staticmethod
    def format_percentage(value: float, decimals: int = 2) -> str:
        """Formate un pourcentage"""
        return f"{value:.{decimals}f} %"
    
    @staticmethod
    def format_result_summary(result: Dict) -> str:
        """Formate un résumé des résultats"""
        if not result or 'status' not in result:
            return "❌ Aucun résultat disponible"
        
        if result['status'] != 'ACCEPTE':
            return f"❌ DOSSIER {result['status']}\nRaison: {result.get('raison', 'Non spécifié')}"
        
        summary = f"""
        ✅ DOSSIER ACCEPTÉ
        
        🎯 TAUX OPTIMAL: {result.get('taux_optimal', 0):.3f} %
        💰 Mensualité: {result.get('mensualite', 0):.2f} €
        📈 TAEG: {result.get('TAEG', 0):.3f} %
        ⚠️  Probabilité de défaut: {result.get('probabilite_defaut', 0):.3f} %
        📊 Nouveau ratio d'endettement: {result.get('nouveau_ratio_endettement', 0):.2f} %
        💼 Profit estimé: {result.get('profitabilite', {}).get('profit_total_estime', 0):.2f} €
        """
        return summary
    
    @staticmethod
    def format_risk_level(pd_value: float) -> str:
        """Formate le niveau de risque basé sur PD"""
        if pd_value < 1:
            return "🟢 FAIBLE"
        elif pd_value < 3:
            return "🟡 MODÉRÉ"
        elif pd_value < 6:
            return "🟠 ÉLEVÉ"
        else:
            return "🔴 TRÈS ÉLEVÉ"
    
    @staticmethod
    def format_comparison_market(comparison: Dict) -> str:
        """Formate la comparaison marché"""
        if not comparison:
            return "Comparaison non disponible"
        
        ecart = comparison.get('ecart', 0)
        if ecart < -0.3:
            return f"💚 Très compétitif (-{abs(ecart):.2f}%)"
        elif ecart < 0:
            return f"🟡 Légèrement en dessous (-{abs(ecart):.2f}%)"
        elif ecart < 0.3:
            return f"🟡 Légèrement au-dessus (+{ecart:.2f}%)"
        else:
            return f"🔴 Au-dessus du marché (+{ecart:.2f}%)"
    
    @staticmethod
    def format_date(date_str: str) -> str:
        """Formate une date"""
        from datetime import datetime
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime("%d/%m/%Y %H:%M")
        except:
            return date_str