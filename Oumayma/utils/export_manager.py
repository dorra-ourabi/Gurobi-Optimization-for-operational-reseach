"""
Gestionnaire d'export des résultats
"""
import csv
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
from PyQt5.QtWidgets import QFileDialog
import os

class ExportManager:
    """Classe pour exporter les résultats"""
    
    @staticmethod
    def export_portfolio_to_csv(portfolio_data: List[Dict], file_path: str) -> bool:
        """Exporte le portefeuille en CSV"""
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                if portfolio_data:
                    writer = csv.DictWriter(f, fieldnames=portfolio_data[0].keys())
                    writer.writeheader()
                    writer.writerows(portfolio_data)
            return True
        except Exception as e:
            print(f"Erreur export CSV: {e}")
            return False
    
    @staticmethod
    def export_results_to_pdf(results: Dict, file_path: str):
        """Exporte les résultats en PDF (simplifié)"""
        try:
            # Pour un vrai PDF, utiliser ReportLab ou WeasyPrint
            # Ici, on crée un simple HTML qui peut être converti
            html_content = ExportManager._create_html_report(results)
            
            # Créer fichier HTML (peut être ouvert dans un navigateur)
            with open(file_path.replace('.pdf', '.html'), 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return True
        except Exception as e:
            print(f"Erreur export PDF: {e}")
            return False
    
    @staticmethod
    def _create_html_report(results: Dict) -> str:
        """Crée un rapport HTML"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Rapport Tarification - {datetime.now().strftime('%Y-%m-%d')}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #1976D2; }}
                .result-box {{ background-color: #f5f5f5; padding: 20px; border-radius: 10px; margin: 20px 0; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #4CAF50; color: white; }}
                .success {{ color: green; font-weight: bold; }}
                .warning {{ color: orange; }}
                .error {{ color: red; }}
            </style>
        </head>
        <body>
            <h1>🏦 Rapport d'Optimisation de Taux</h1>
            <p>Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <div class="result-box">
                <h2>📊 Résumé</h2>
                <p><strong>Statut:</strong> <span class="success">✓ ACCEPTÉ</span></p>
                <p><strong>Taux optimal:</strong> {results.get('taux_optimal', 0):.3f} %</p>
                <p><strong>Mensualité:</strong> {results.get('mensualite', 0):.2f} €</p>
                <p><strong>Probabilité de défaut:</strong> {results.get('probabilite_defaut', 0):.3f} %</p>
            </div>
            
            <h2>📈 Détails Financiers</h2>
            <table>
                <tr><th>Indicateur</th><th>Valeur</th></tr>
                <tr><td>Coût total</td><td>{results.get('cout_total', 0):.2f} €</td></tr>
                <tr><td>Intérêts totaux</td><td>{results.get('interets_totaux', 0):.2f} €</td></tr>
                <tr><td>Profit estimé</td><td>{results.get('profitabilite', {}).get('profit_total_estime', 0):.2f} €</td></tr>
            </table>
            
            <h2>⚖️ Conformité</h2>
            <table>
                <tr><th>Contrainte</th><th>Statut</th></tr>
                <tr><td>Taux d'usure</td><td>{'✅ Conforme' if results.get('conformite', {}).get('taux_usure', False) else '❌ Non conforme'}</td></tr>
                <tr><td>Ratio endettement</td><td>{'✅ Conforme' if results.get('conformite', {}).get('ratio_endettement', False) else '❌ Non conforme'}</td></tr>
                <tr><td>Score minimum</td><td>{'✅ Conforme' if results.get('conformite', {}).get('score_minimum', False) else '❌ Non conforme'}</td></tr>
            </table>
        </body>
        </html>
        """
        return html
    
    @staticmethod
    def export_sensitivity_analysis(data: Dict, file_path: str):
        """Exporte l'analyse de sensibilité"""
        try:
            # Créer un DataFrame pandas
            df = pd.DataFrame(data)
            df.to_excel(file_path, index=False)
            return True
        except Exception as e:
            print(f"Erreur export Excel: {e}")
            return False