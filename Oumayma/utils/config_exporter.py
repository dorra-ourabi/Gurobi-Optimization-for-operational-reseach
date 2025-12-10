"""
Export de la configuration avec documentation
"""
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List

class ConfigExporter:
    """Exporte la configuration avec documentation intégrée"""
    
    def __init__(self, config_manager, variables_dict):
        self.config = config_manager
        self.variables_dict = variables_dict
    
    def export_to_excel(self, filepath: str):
        """Exporte la configuration complète en Excel"""
        
        # Créer un DataFrame pour chaque catégorie
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            for category in self.variables_dict.get('categories', []):
                category_data = []
                
                # Trouver toutes les variables de cette catégorie
                variables = self.variables_dict.get('variables', {})
                for var_name, var_info in variables.items():
                    if var_info.get('categorie') == category:
                        # Récupérer la valeur actuelle
                        current_value = self._get_current_value(var_name, var_info)
                        
                        category_data.append({
                            'Variable': var_info.get('nom_complet', var_name),
                            'Symbole': var_info.get('symbole', ''),
                            'Valeur actuelle': current_value,
                            'Unité': var_info.get('unite', ''),
                            'Par défaut': var_info.get('valeur_defaut', ''),
                            'Minimum': var_info.get('plage_min', ''),
                            'Maximum': var_info.get('plage_max', ''),
                            'Description': var_info.get('description', '')[:100] + '...',
                            'Impact': var_info.get('impact', '')[:100] + '...'
                        })
                
                if category_data:
                    df = pd.DataFrame(category_data)
                    sheet_name = category[:31]  # Excel limite à 31 caractères
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Feuille de synthèse
            self._create_summary_sheet(writer)
    
    def _get_current_value(self, var_name: str, var_info: Dict):
        """Récupère la valeur actuelle d'une variable"""
        # Implémenter la logique pour trouver la valeur dans la config
        return var_info.get('valeur_defaut', 'N/A')
    
    def _create_summary_sheet(self, writer):
        """Crée une feuille de synthèse"""
        summary_data = []
        
        for category in self.variables_dict.get('categories', []):
            variables = [v for v in self.variables_dict.get('variables', {}).values() 
                        if v.get('categorie') == category]
            
            summary_data.append({
                'Catégorie': category.replace('_', ' ').title(),
                'Nb variables': len(variables),
                'Description': self._get_category_description(category),
                'Impact global': self._get_category_impact(category)
            })
        
        df = pd.DataFrame(summary_data)
        df.to_excel(writer, sheet_name='Synthèse', index=False)
    
    def export_to_html(self, filepath: str):
        """Exporte en HTML avec documentation complète"""
        html_content = self._generate_html_documentation()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _generate_html_documentation(self) -> str:
        """Génère la documentation HTML complète"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Documentation du Modèle - {datetime.now().strftime('%Y-%m-%d')}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
                h2 {{ color: #34495e; margin-top: 30px; padding-left: 10px; border-left: 4px solid #2ecc71; }}
                h3 {{ color: #7f8c8d; }}
                .variable-card {{
                    background: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 15px 0;
                }}
                .variable-header {{
                    background: #3498db;
                    color: white;
                    padding: 10px;
                    border-radius: 5px;
                    margin-bottom: 15px;
                }}
                .info-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 10px;
                    margin: 15px 0;
                }}
                .info-item {{ background: white; padding: 10px; border-radius: 5px; }}
                .formula {{
                    font-family: 'Courier New', monospace;
                    background: #2c3e50;
                    color: white;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 10px 0;
                }}
                .recommendation {{ background: #d5f4e6; padding: 10px; border-left: 4px solid #2ecc71; }}
                .warning {{ background: #fdebd0; padding: 10px; border-left: 4px solid #e67e22; }}
                .category {{
                    background: #ecf0f1;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <h1>📚 Documentation complète du modèle de tarification</h1>
            <p><strong>Date de génération:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            <p><strong>Version du modèle:</strong> {self.variables_dict.get('metadata', {}).get('version', '1.0')}</p>
            
            <div class="category">
                <h2>🎯 Objectif du modèle</h2>
                <p>Ce modèle permet de déterminer le taux d'intérêt optimal pour des prêts bancaires en maximisant le profit tout en respectant les contraintes réglementaires et de marché.</p>
            </div>
        """
        
        # Ajouter chaque catégorie
        for category in self.variables_dict.get('categories', []):
            html += f"""
            <div class="category">
                <h2>{self._get_category_icon(category)} {category.replace('_', ' ').title()}</h2>
                <p>{self._get_category_description(category)}</p>
            """
            
            # Variables de cette catégorie
            variables = self.variables_dict.get('variables', {})
            for var_name, var_info in variables.items():
                if var_info.get('categorie') == category:
                    html += self._generate_variable_html(var_name, var_info)
            
            html += "</div>"
        
        # Formules principales
        html += """
            <div class="category">
                <h2>🧮 Formules principales du modèle</h2>
        """
        
        formulas = self.variables_dict.get('formules_principales', {})
        for formula_name, formula_info in formulas.items():
            html += f"""
                <div class="variable-card">
                    <h3>{formula_info.get('nom', formula_name)}</h3>
                    <div class="formula">{formula_info.get('formule', '')}</div>
                    <p><strong>Explication:</strong> {formula_info.get('explication', '')}</p>
                    <p><strong>Variables:</strong> {', '.join(formula_info.get('variables', {}).keys())}</p>
                </div>
            """
        
        html += """
            </div>
            <footer style="margin-top: 50px; padding-top: 20px; border-top: 1px solid #ddd; color: #7f8c8d;">
                <p>Documentation générée automatiquement par le système de tarification optimale.</p>
                <p>© 2024 - Tous droits réservés</p>
            </footer>
        </body>
        </html>
        """
        
        return html
    
    def _generate_variable_html(self, var_name: str, var_info: Dict) -> str:
        """Génère le HTML pour une variable"""
        return f"""
        <div class="variable-card">
            <div class="variable-header">
                <h3>{var_info.get('nom_complet', var_name)} ({var_info.get('symbole', '')})</h3>
            </div>
            
            <p><strong>Description:</strong> {var_info.get('description', '')}</p>
            
            <div class="info-grid">
                <div class="info-item"><strong>Catégorie:</strong><br>{var_info.get('categorie', '').replace('_', ' ').title()}</div>
                <div class="info-item"><strong>Type:</strong><br>{var_info.get('type', '')}</div>
                <div class="info-item"><strong>Unité:</strong><br>{var_info.get('unite', '')}</div>
                <div class="info-item"><strong>Valeur par défaut:</strong><br>{var_info.get('valeur_defaut', '')}</div>
            </div>
            
            <p><strong>Impact:</strong> {var_info.get('impact', '')}</p>
            
            <div class="recommendation">
                <strong>💡 Comment déterminer:</strong><br>
                {var_info.get('comment_determiner', '')}
            </div>
            
            <div class="info-grid">
                <div class="info-item"><strong>Plage min:</strong> {var_info.get('plage_min', '')}</div>
                <div class="info-item"><strong>Plage max:</strong> {var_info.get('plage_max', '')}</div>
            </div>
            
            <p><strong>Formule liée:</strong> {var_info.get('formule_liee', '')}</p>
            <p><strong>Exemple:</strong> {var_info.get('exemple_calcul', '')}</p>
            
            <div class="warning">
                <strong>⚠️ Recommandations:</strong><br>
                <ul>
                    {''.join([f'<li>{rec}</li>' for rec in var_info.get('recommandations', [])])}
                </ul>
            </div>
            
            <p><strong>Mots-clés:</strong> {', '.join(var_info.get('mots_cles', []))}</p>
        </div>
        """