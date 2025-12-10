from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QTreeWidget, QTreeWidgetItem, QTextEdit, QSplitter, QGroupBox,
    QLineEdit, QComboBox, QFrame, QScrollArea, QFormLayout,
    QMessageBox, QFileDialog, QProgressDialog, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QIcon
import json
import os
from typing import Dict, List
from datetime import datetime
import sys

class DocumentationTab(QWidget):
    """Onglet Documentation avec arborescence des catégories/variables"""
    
    # Signal pour demander le changement d'onglet
    request_edit_variable = pyqtSignal(str, str)  # nom_variable, chemin_config
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.variables_dict = self._load_variables_dictionary()
        self.current_variable = None
        self.notes_personnelles = self._load_personal_notes()
        self.init_ui()
    
    def _load_variables_dictionary(self) -> Dict:
        """Charge le dictionnaire des variables"""
        # Cherche dans plusieurs chemins possibles
        possible_paths = [
            "docs/variables_dictionary.json",
            "config/docs/variables_dictionary.json",
            "../docs/variables_dictionary.json",
            "./variables_dictionary.json"
        ]
        
        for dict_path in possible_paths:
            if os.path.exists(dict_path):
                try:
                    with open(dict_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        print(f"   {len(data.get('variables', {}))} variables trouvées")
                        return data
                except Exception as e:
                    print(f"Erreur chargement {dict_path}: {e}")
        return self._create_minimal_dictionary()
    
    def _create_minimal_dictionary(self) -> Dict:
        return {
            "metadata": {
                "version": "1.0",
                "date_creation": datetime.now().strftime("%Y-%m-%d"),
                "description": "Dictionnaire minimal - fichier original non trouvé",
                "total_variables": 0
            },
            "categories": [
                "parametres_macroeconomiques",
                "couts_et_risques",
                "contraintes_reglementaires",
                "parametres_marche",
                "caracteristiques_client",
                "calcul_probabilite_defaut",
                "scenarios_economiques",
                "capital_et_portefeuille",
                "parametres_avances"
            ],
            "variables": {}
        }
    
    def _load_personal_notes(self) -> Dict:
        """Charge les notes personnelles"""
        notes_path = "docs/personal_notes.json"
        if os.path.exists(notes_path):
            try:
                with open(notes_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_personal_notes(self):
        """Sauvegarde les notes personnelles"""
        notes_path = "docs/personal_notes.json"
        os.makedirs(os.path.dirname(notes_path), exist_ok=True)
        try:
            with open(notes_path, 'w', encoding='utf-8') as f:
                json.dump(self.notes_personnelles, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erreur sauvegarde notes: {e}")
            return False
    
    def init_ui(self):
        """Initialise l'interface arborescente"""
        main_layout = QVBoxLayout()
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Rechercher une variable (nom, symbole, mot-clé)...")
        self.search_input.textChanged.connect(self.filter_tree)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #3498db;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #2ecc71;
            }
        """)
        
        self.clear_search_btn = QPushButton("Effacer")
        self.clear_search_btn.clicked.connect(self.clear_search)
        self.clear_search_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.clear_search_btn)
        main_layout.addLayout(search_layout)
        
        # Splitter principal
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(3)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #7f8c8d;
            }
            QSplitter::handle:hover {
                background-color: #3498db;
            }
        """)
        
        # Panneau gauche : Arborescence
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        left_label = QLabel("CATÉGORIES ET VARIABLES")
        left_label.setFont(QFont("Arial", 12, QFont.Bold))
        left_label.setStyleSheet("color: #2c3e50; padding: 5px;")
        left_layout.addWidget(left_label)
        
        # Arbre des catégories/variables
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Variable", "Valeur"])
        self.tree_widget.setColumnCount(2)
        self.tree_widget.setColumnWidth(0, 280)
        self.tree_widget.setColumnWidth(1, 70)
        self.tree_widget.setStyleSheet("""
            QTreeWidget {
                font-size: 12px;
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
            QTreeWidget::item {
                padding: 6px;
                border-bottom: 1px solid #f8f9fa;
            }
            QTreeWidget::item:selected {
                background-color: #3498db;
                color: white;
                font-weight: bold;
            }
            QTreeWidget::item:hover {
                background-color: #f8f9fa;
            }
        """)
        self.tree_widget.itemClicked.connect(self.on_item_clicked)
        
        left_layout.addWidget(self.tree_widget)
        
        # Panneau droit : Détails
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        right_label = QLabel("DÉTAILS DE LA VARIABLE")
        right_label.setFont(QFont("Arial", 12, QFont.Bold))
        right_label.setStyleSheet("color: #2c3e50; padding: 5px;")
        right_layout.addWidget(right_label)
        
        # Zone de détails
        self.details_scroll = QScrollArea()
        self.details_scroll.setWidgetResizable(True)
        self.details_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: white;
            }
        """)
        
        self.details_widget = QWidget()
        self.details_layout = QVBoxLayout(self.details_widget)
        self.details_layout.setAlignment(Qt.AlignTop)
        self.details_layout.setSpacing(10)
        
        # Message par défaut
        default_message = QLabel("Sélectionnez une variable dans l'arborescence")
        default_message.setFont(QFont("Arial", 14))
        default_message.setAlignment(Qt.AlignCenter)
        default_message.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                padding: 50px;
                font-style: italic;
            }
        """)
        self.details_layout.addWidget(default_message)
        
        self.details_scroll.setWidget(self.details_widget)
        right_layout.addWidget(self.details_scroll)
        
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 600])
        
        main_layout.addWidget(splitter)
        
        # Barre d'outils
        toolbar = QFrame()
        toolbar.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 4px;
                padding: 5px;
                border: 1px solid #dee2e6;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar)
        
        self.btn_refresh = QPushButton("Actualiser")
        self.btn_refresh.clicked.connect(self.refresh_tree)
        self.btn_refresh.setToolTip("Recharger le dictionnaire depuis le fichier")
        
        self.btn_export = QPushButton("Exporter")
        self.btn_export.clicked.connect(self.export_documentation)
        self.btn_export.setToolTip("Exporter la documentation complète")
        
        self.btn_print = QPushButton("Imprimer")
        self.btn_print.clicked.connect(self.print_variable_card)
        self.btn_print.setToolTip("Imprimer la fiche de la variable sélectionnée")
        
        
        toolbar_layout.addWidget(self.btn_refresh)
        toolbar_layout.addWidget(self.btn_export)
        toolbar_layout.addWidget(self.btn_print)
        toolbar_layout.addStretch()
        
        
        self.setLayout(main_layout)
        
        # Charger l'arborescence
        self.load_tree_structure()
    
    def load_tree_structure(self):
        """Charge la structure arborescente des catégories et variables"""
        self.tree_widget.clear()
        
        categories = self.variables_dict.get("categories", [])
        variables = self.variables_dict.get("variables", {})
        
        # Compter les variables par catégorie
        category_counts = {}
        for var_data in variables.values():
            category = var_data.get("categorie", "")
            category_counts[category] = category_counts.get(category, 0) + 1
        
        for category in categories:
            # Créer l'élément catégorie
            category_item = QTreeWidgetItem(self.tree_widget)
            count = category_counts.get(category, 0)
            category_name = category.replace('_', ' ').title()
            category_item.setText(0, f"{category_name}")
            category_item.setText(1, f"({count})")
            category_item.setData(0, Qt.UserRole, {"type": "category", "name": category})
            category_item.setFont(0, QFont("Arial", 10, QFont.Bold))
            
            # Ajouter les variables de cette catégorie
            for var_name, var_data in variables.items():
                if var_data.get("categorie") == category:
                    var_item = QTreeWidgetItem(category_item)
                    
                    display_name = var_data.get('nom_complet', var_name)
                    if len(display_name) > 35:
                        display_name = display_name[:35] + "..."
                    
                    var_item.setText(0, f"{display_name}")
                    
                    # Afficher la valeur par défaut si elle existe
                    default_val = var_data.get('valeur_defaut', '')
                    if default_val is not None:
                        unit = var_data.get('unite', '')
                        var_item.setText(1, f"{default_val} {unit}")
                    
                    var_item.setData(0, Qt.UserRole, {
                        "type": "variable", 
                        "name": var_name,
                        "data": var_data
                    })
                    
                    # Colorer selon le type
                    type_color = self._get_type_color(var_data.get("type", ""))
                    var_item.setForeground(0, QColor(type_color))
                    
                    # Tooltip avec description courte
                    description = var_data.get("description", "")
                    if len(description) > 100:
                        description = description[:100] + "..."
                    var_item.setToolTip(0, f"{var_data.get('symbole', '')}\n\n{description}")
            
            # Développer les catégories par défaut
            category_item.setExpanded(True)
    
    def _get_type_color(self, var_type: str) -> str:
        """Retourne la couleur selon le type"""
        colors = {
            "taux_percentage": "#3498db",  
            "pourcentage": "#9b59b6",      
            "probabilite": "#e74c3c",      
            "coefficient": "#f39c12",      
            "multiplicateur": "#1abc9c",  
            "montant": "#27ae60",          
            "score": "#e67e22",            
            "default": "#2c3e50"           
        }
        return colors.get(var_type, colors["default"])
    
    def on_item_clicked(self, item):
        """Gère le clic sur un élément de l'arbre"""
        data = item.data(0, Qt.UserRole)
        
        if data and data.get("type") == "variable":
            self.current_variable = data
            self.display_variable_details(data["name"], data["data"])
    
    
    def update_stats(self):
        """Met à jour les statistiques affichées"""
        total_vars = len(self.variables_dict.get("variables", {}))
        categories = len(self.variables_dict.get("categories", []))
        version = self.variables_dict.get("metadata", {}).get("version", "1.0")
        
        self.stats_label.setText(f"v{version} • {total_vars} variables • {categories} catégories")
    
    def display_variable_details(self, var_name: str, var_data: Dict):
        """Affiche les détails d'une variable"""
        while self.details_layout.count():
            item = self.details_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2c3e50, stop:1 #34495e);
                border-radius: 8px;
                padding: 15px;
            }
        """)
        header_layout = QVBoxLayout(header_frame)
        
        nom_complet = QLabel(var_data.get("nom_complet", var_name))
        nom_complet.setFont(QFont("Arial", 16, QFont.Bold))
        nom_complet.setStyleSheet("color: white;")
        nom_complet.setWordWrap(True)
        
        symbole_label = QLabel(f"Symbole: {var_data.get('symbole', '')}")
        symbole_label.setFont(QFont("Arial", 12))
        symbole_label.setStyleSheet("color: #ecf0f1;")
        
        header_layout.addWidget(nom_complet)
        header_layout.addWidget(symbole_label)
        
        self.details_layout.addWidget(header_frame)
        
        personal_note = self.notes_personnelles.get(var_name, "")
        if personal_note:
            note_frame = QFrame()
            note_frame.setStyleSheet("""
                QFrame {
                    background-color: #fff3cd;
                    border: 2px solid #ffeaa7;
                    border-radius: 6px;
                    padding: 10px;
                }
            """)
            note_layout = QVBoxLayout(note_frame)
            
            note_title = QLabel("📝 NOTE PERSONNELLE")
            note_title.setFont(QFont("Arial", 10, QFont.Bold))
            
            note_text = QLabel(personal_note)
            note_text.setWordWrap(True)
            note_text.setStyleSheet("color: #856404;")
            
            note_layout.addWidget(note_title)
            note_layout.addWidget(note_text)
            
            self.details_layout.addWidget(note_frame)
        
        info_group = QGroupBox("INFORMATIONS GÉNÉRALES")
        info_group.setFont(QFont("Arial", 11, QFont.Bold))
        info_layout = QFormLayout()
        info_layout.setVerticalSpacing(8)
        
        category = var_data.get("categorie", "")
        category_label = QLabel(category.replace('_', ' ').title())
        category_label.setStyleSheet("color: #3498db; font-weight: bold;")
        info_layout.addRow("Catégorie:", category_label)
        
        var_type = var_data.get("type", "")
        type_label = QLabel(var_type)
        type_color = self._get_type_color(var_type)
        type_label.setStyleSheet(f"color: {type_color}; font-weight: bold;")
        info_layout.addRow("Type:", type_label)
        
        unit = var_data.get("unite", "")
        info_layout.addRow("Unité:", QLabel(unit))
        
        info_group.setLayout(info_layout)
        self.details_layout.addWidget(info_group)
        
        desc_group = QGroupBox("DESCRIPTION")
        desc_group.setFont(QFont("Arial", 11, QFont.Bold))
        desc_layout = QVBoxLayout()
        
        desc_text = QTextEdit()
        desc_text.setPlainText(var_data.get("description", "Pas de description disponible."))
        desc_text.setReadOnly(True)
        desc_text.setMaximumHeight(100)
        desc_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
                font-size: 12px;
            }
        """)
        
        desc_layout.addWidget(desc_text)
        desc_group.setLayout(desc_layout)
        self.details_layout.addWidget(desc_group)
        
        config_group = QGroupBox("CONFIGURATION")
        config_group.setFont(QFont("Arial", 11, QFont.Bold))
        config_layout = QFormLayout()
        config_layout.setVerticalSpacing(8)
        
        default_val = var_data.get("valeur_defaut", "")
        default_label = QLabel(str(default_val) if default_val is not None else "Non définie")
        if default_val is not None:
            default_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        config_layout.addRow("Valeur par défaut:", default_label)
        
        min_val = var_data.get("plage_min", "")
        max_val = var_data.get("plage_max", "")
        
        if min_val != '' and max_val != '':
            config_layout.addRow("Plage minimum:", QLabel(str(min_val)))
            config_layout.addRow("Plage maximum:", QLabel(str(max_val)))
        
        config_group.setLayout(config_layout)
        self.details_layout.addWidget(config_group)
        
        determiner = var_data.get("comment_determiner", "")
        if determiner:
            determiner_group = QGroupBox("COMMENT DÉTERMINER CETTE VALEUR")
            determiner_group.setFont(QFont("Arial", 11, QFont.Bold))
            determiner_layout = QVBoxLayout()
            
            determiner_text = QTextEdit()
            determiner_text.setPlainText(determiner)
            determiner_text.setReadOnly(True)
            determiner_text.setMaximumHeight(80)
            determiner_text.setStyleSheet("""
                QTextEdit {
                    background-color: #e8f4f8;
                    border: 1px solid #b3e0f2;
                    border-radius: 5px;
                    padding: 10px;
                    font-size: 12px;
                }
            """)
            
            determiner_layout.addWidget(determiner_text)
            determiner_group.setLayout(determiner_layout)
            self.details_layout.addWidget(determiner_group)
        
        impact = var_data.get("impact", "")
        if impact:
            impact_group = QGroupBox("IMPACT SUR LE MODÈLE")
            impact_group.setFont(QFont("Arial", 11, QFont.Bold))
            impact_layout = QVBoxLayout()
            
            impact_text = QTextEdit()
            impact_text.setPlainText(impact)
            impact_text.setReadOnly(True)
            impact_text.setMaximumHeight(80)
            impact_text.setStyleSheet("""
                QTextEdit {
                    background-color: #f8e8e8;
                    border: 1px solid #f2b3b3;
                    border-radius: 5px;
                    padding: 10px;
                    font-size: 12px;
                }
            """)
            
            impact_layout.addWidget(impact_text)
            impact_group.setLayout(impact_layout)
            self.details_layout.addWidget(impact_group)
        
        formule = var_data.get("formule_liee", "")
        if formule:
            formula_group = QGroupBox("FORMULE LIÉE")
            formula_group.setFont(QFont("Arial", 11, QFont.Bold))
            formula_layout = QVBoxLayout()
            
            formula_frame = QFrame()
            formula_frame.setStyleSheet("""
                QFrame {
                    background-color: #2c3e50;
                    border-radius: 6px;
                    padding: 12px;
                }
            """)
            formula_inner = QVBoxLayout(formula_frame)
            
            formula_label = QLabel(formule)
            formula_label.setFont(QFont("Courier New", 12))
            formula_label.setStyleSheet("color: white;")
            formula_label.setWordWrap(True)
            
            formula_inner.addWidget(formula_label)
            formula_layout.addWidget(formula_frame)
            formula_group.setLayout(formula_layout)
            self.details_layout.addWidget(formula_group)
        
        exemple = var_data.get("exemple_calcul", "")
        if exemple:
            example_group = QGroupBox("EXEMPLE DE CALCUL")
            example_group.setFont(QFont("Arial", 11, QFont.Bold))
            example_layout = QVBoxLayout()
            
            example_text = QTextEdit()
            example_text.setPlainText(exemple)
            example_text.setReadOnly(True)
            example_text.setMaximumHeight(70)
            example_text.setStyleSheet("""
                QTextEdit {
                    background-color: #fff3cd;
                    border: 1px solid #ffeaa7;
                    border-radius: 5px;
                    padding: 10px;
                    font-size: 12px;
                }
            """)
            
            example_layout.addWidget(example_text)
            example_group.setLayout(example_layout)
            self.details_layout.addWidget(example_group)
        
        recommendations = var_data.get("recommandations", [])
        if recommendations:
            rec_group = QGroupBox("RECOMMANDATIONS")
            rec_group.setFont(QFont("Arial", 11, QFont.Bold))
            rec_layout = QVBoxLayout()
            
            rec_text = QTextEdit()
            rec_content = "• " + "\n• ".join(recommendations)
            rec_text.setPlainText(rec_content)
            rec_text.setReadOnly(True)
            rec_text.setMaximumHeight(100)
            rec_text.setStyleSheet("""
                QTextEdit {
                    background-color: #d5f4e6;
                    border: 1px solid #2ecc71;
                    border-radius: 5px;
                    padding: 10px;
                    font-size: 12px;
                }
            """)
            
            rec_layout.addWidget(rec_text)
            rec_group.setLayout(rec_layout)
            self.details_layout.addWidget(rec_group)
        
        keywords = var_data.get("mots_cles", [])
        if keywords:
            kw_group = QGroupBox("MOTS-CLÉS")
            kw_group.setFont(QFont("Arial", 11, QFont.Bold))
            kw_layout = QVBoxLayout()
            
            kw_text = QLabel(", ".join(keywords))
            kw_text.setWordWrap(True)
            kw_text.setStyleSheet("""
                QLabel {
                    background-color: #ecf0f1;
                    padding: 10px;
                    border-radius: 5px;
                    font-style: italic;
                }
            """)
            
            kw_layout.addWidget(kw_text)
            kw_group.setLayout(kw_layout)
            self.details_layout.addWidget(kw_group)
        
        self.details_layout.addStretch()
    
    def filter_tree(self, text):
        """Filtre l'arbre selon le texte de recherche"""
        search_text = text.lower().strip()
        search_type = self.search_type_combo.currentText()
        
        if not search_text:
            self.clear_search()
            return
        
        total_visible = 0
        
        for i in range(self.tree_widget.topLevelItemCount()):
            category_item = self.tree_widget.topLevelItem(i)
            category_visible = False
            category_name = category_item.text(0).lower()
            
            if search_text in category_name:
                category_visible = True
                category_item.setExpanded(True)
            else:
                category_item.setExpanded(False)
            
            for j in range(category_item.childCount()):
                var_item = category_item.child(j)
                var_data = var_item.data(0, Qt.UserRole)
                
                if var_data and var_data.get("type") == "variable":
                    var_info = var_data.get("data", {})
                    
                    matches = False
                    if search_type == "Tout":
                        matches = (
                            search_text in var_item.text(0).lower() or
                            search_text in var_info.get("nom_complet", "").lower() or
                            search_text in var_info.get("symbole", "").lower() or
                            search_text in var_info.get("categorie", "").lower() or
                            search_text in var_info.get("description", "").lower() or
                            any(search_text in kw.lower() for kw in var_info.get("mots_cles", []))
                        )
                    elif search_type == "Nom":
                        matches = search_text in var_info.get("nom_complet", "").lower()
                    elif search_type == "Symbole":
                        matches = search_text in var_info.get("symbole", "").lower()
                    elif search_type == "Catégorie":
                        matches = search_text in var_info.get("categorie", "").lower()
                    elif search_type == "Description":
                        matches = search_text in var_info.get("description", "").lower()
                    
                    var_item.setHidden(not matches)
                    
                    if matches:
                        category_visible = True
                        category_item.setExpanded(True)
                        total_visible += 1
            
            category_item.setHidden(not category_visible)
        
        self.status_label.setText(f"{total_visible} variable(s) trouvée(s)")
    
    def clear_search(self):
        """Efface la recherche et affiche tout"""
        self.search_input.clear()
        
        for i in range(self.tree_widget.topLevelItemCount()):
            category_item = self.tree_widget.topLevelItem(i)
            category_item.setHidden(False)
            category_item.setExpanded(True)
            
            for j in range(category_item.childCount()):
                var_item = category_item.child(j)
                var_item.setHidden(False)
        
        self.status_label.setText("Recherche effacée")
    
    def refresh_tree(self):
        progress = QProgressDialog("Actualisation du dictionnaire...", "Annuler", 0, 100, self)
        progress.setWindowTitle("Actualisation")
        progress.setWindowModality(Qt.WindowModal)
        progress.setValue(0)
        
        for i in range(3):
            QApplication.processEvents()
            if progress.wasCanceled():
                break
            progress.setValue((i + 1) * 33)
        
        self.variables_dict = self._load_variables_dictionary()
        self.notes_personnelles = self._load_personal_notes()
        
        self.load_tree_structure()
        self.update_stats()
        
        progress.setValue(100)
        
        total_vars = len(self.variables_dict.get("variables", {}))
        QMessageBox.information(self, "Actualisation", 
            f"Dictionnaire actualisé avec succès !\n\n"
            f"• {total_vars} variables chargées\n"
            f"• {len(self.variables_dict.get('categories', []))} catégories\n"
            f"• Version: {self.variables_dict.get('metadata', {}).get('version', '1.0')}")
        
        self.status_label.setText("Dictionnaire actualisé")
    
    
    def find_config_path(self, var_name: str) -> str:
        """Trouve le chemin de configuration correspondant à une variable"""
        # Cette méthode doit être adaptée à votre structure de configuration
        # Pour l'instant, retourne une chaîne vide
        return ""
    
    def export_documentation(self):
        """Exporte la documentation complète"""
        filepath, filter_ = QFileDialog.getSaveFileName(
            self, "Exporter Documentation",
            f"documentation_variables_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
            "Fichiers HTML (*.html);;Fichiers JSON (*.json);;Tous les fichiers (*)"
        )
        
        if not filepath:
            return
        
        try:
            if filepath.endswith('.html'):
                self.export_to_html(filepath)
                message = f"Documentation HTML exportée avec succès !\n\n{filepath}"
            elif filepath.endswith('.json'):
                self.export_to_json(filepath)
                message = f"Documentation JSON exportée avec succès !\n\n{filepath}"
            else:
                # Par défaut, exporter en HTML
                filepath = filepath + '.html' if not filepath.endswith('.html') else filepath
                self.export_to_html(filepath)
                message = f"Documentation exportée avec succès !\n\n{filepath}"
            
            QMessageBox.information(self, "Exportation", message)
            self.status_label.setText(f"Exporté: {os.path.basename(filepath)}")
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", 
                f"Erreur lors de l'exportation:\n\n{str(e)}")
            self.status_label.setText("Erreur d'exportation")
    
    def export_to_html(self, filepath: str):
        """Exporte en format HTML"""
        html = self.generate_html_documentation()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
    
    def export_to_json(self, filepath: str):
        """Exporte en format JSON"""
        export_data = {
            "metadata": self.variables_dict.get("metadata", {}),
            "export_date": datetime.now().isoformat(),
            "total_variables": len(self.variables_dict.get("variables", {})),
            "variables": self.variables_dict.get("variables", {})
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    def generate_html_documentation(self) -> str:
        """Génère la documentation HTML"""
        metadata = self.variables_dict.get("metadata", {})
        variables = self.variables_dict.get("variables", {})
        
        html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Documentation des Variables - {metadata.get('version', '1.0')}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f7fa;
        }}
        .header {{
            background: linear-gradient(135deg, #2c3e50, #4a6491);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        h1 {{
            margin: 0;
            font-size: 28px;
        }}
        .subtitle {{
            font-size: 14px;
            opacity: 0.8;
            margin-top: 5px;
        }}
        .stats {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        .variable-card {{
            background: white;
            border-left: 4px solid #3498db;
            padding: 20px;
            margin-bottom: 15px;
            border-radius: 6px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        .variable-header {{
            border-bottom: 2px solid #f0f0f0;
            padding-bottom: 15px;
            margin-bottom: 15px;
        }}
        .variable-name {{
            color: #2c3e50;
            font-size: 18px;
            font-weight: bold;
            margin: 0;
        }}
        .variable-symbol {{
            color: #3498db;
            font-family: 'Courier New', monospace;
            font-size: 16px;
            margin: 5px 0;
        }}
        .section {{
            margin-top: 15px;
        }}
        .section-title {{
            color: #2c3e50;
            font-size: 14px;
            font-weight: bold;
            text-transform: uppercase;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .section-content {{
            background: #f8f9fa;
            padding: 12px;
            border-radius: 4px;
            font-size: 14px;
        }}
        .tag {{
            display: inline-block;
            background: #e8f4f8;
            color: #3498db;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 12px;
            margin-right: 5px;
            margin-bottom: 5px;
        }}
        .default-value {{
            color: #27ae60;
            font-weight: bold;
        }}
        .category-badge {{
            display: inline-block;
            background: #34495e;
            color: white;
            padding: 3px 10px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: bold;
            margin-right: 10px;
        }}
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            .header {{
                box-shadow: none;
                border: 1px solid #ddd;
            }}
            .variable-card {{
                page-break-inside: avoid;
                border: 1px solid #ddd;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📚 Documentation des Variables du Modèle</h1>
        <div class="subtitle">
            Version {metadata.get('version', '1.0')} • 
            Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} • 
            {len(variables)} variables
        </div>
    </div>
    
    <div class="stats">
        <strong>📊 Statistiques:</strong>
        • {len(variables)} variables documentées<br>
        • {len(self.variables_dict.get('categories', []))} catégories<br>
        • {metadata.get('description', 'Documentation complète des variables du modèle')}
    </div>
"""
        
        # Variables par catégorie
        categories = self.variables_dict.get("categories", [])
        for category in categories:
            category_vars = {k: v for k, v in variables.items() if v.get("categorie") == category}
            if not category_vars:
                continue
            
            html += f"""
    <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
        📁 {category.replace('_', ' ').title()} ({len(category_vars)} variables)
    </h2>
"""
            
            for var_name, var_data in category_vars.items():
                html += f"""
    <div class="variable-card">
        <div class="variable-header">
            <h3 class="variable-name">{var_data.get('nom_complet', var_name)}</h3>
            <div class="variable-symbol">🔤 {var_data.get('symbole', '')}</div>
            <div>
                <span class="category-badge">{category.replace('_', ' ').title()}</span>
                <span class="tag">{var_data.get('type', '')}</span>
                <span class="tag">{var_data.get('unite', '')}</span>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">📝 Description</div>
            <div class="section-content">{var_data.get('description', '')}</div>
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
            <div class="section">
                <div class="section-title">⚙️ Configuration</div>
                <div class="section-content">
                    <strong>Valeur par défaut:</strong> 
                    <span class="default-value">{var_data.get('valeur_defaut', 'Non définie')}</span><br>
                    <strong>Plage:</strong> [{var_data.get('plage_min', '')} ; {var_data.get('plage_max', '')}]
                </div>
            </div>
            
            <div class="section">
                <div class="section-title">📈 Impact</div>
                <div class="section-content">{var_data.get('impact', '')[:100]}...</div>
            </div>
        </div>
"""
                
                if var_data.get('formule_liee'):
                    html += f"""
        <div class="section">
            <div class="section-title">🧮 Formule</div>
            <div class="section-content" style="font-family: 'Courier New', monospace; background: #2c3e50; color: white; padding: 10px;">
                {var_data.get('formule_liee', '')}
            </div>
        </div>
"""
                
                if var_data.get('recommandations'):
                    rec_html = "• " + "<br>• ".join(var_data.get('recommandations', []))
                    html += f"""
        <div class="section">
            <div class="section-title">💡 Recommandations</div>
            <div class="section-content">{rec_html}</div>
        </div>
"""
                
                html += """
    </div>
"""
        
        html += """
    <div style="text-align: center; margin-top: 40px; padding: 20px; color: #7f8c8d; font-size: 12px;">
        Document généré automatiquement par l'application de tarification optimale
    </div>
</body>
</html>
"""
        
        return html
    
    def print_variable_card(self):
        """Imprime la fiche de la variable courante"""
        if not self.current_variable:
            QMessageBox.warning(self, "Impression", 
                "Veuillez sélectionner une variable à imprimer.")
            return
        
        var_name = self.current_variable["name"]
        var_data = self.current_variable["data"]
        
        # Créer un HTML pour l'impression
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial; padding: 20px; }}
                h1 {{ color: #2c3e50; }}
                .card {{ border: 2px solid #3498db; padding: 20px; border-radius: 10px; }}
                .section {{ margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h1>{var_data.get('nom_complet', var_name)}</h1>
                <p><strong>Symbole:</strong> {var_data.get('symbole', '')}</p>
                <p><strong>Catégorie:</strong> {var_data.get('categorie', '').replace('_', ' ').title()}</p>
                <p><strong>Description:</strong><br>{var_data.get('description', '')}</p>
                <p><strong>Valeur par défaut:</strong> {var_data.get('valeur_defaut', 'N/A')}</p>
                <p>Généré le {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            </div>
        </body>
        </html>
        """
        
        # Ici, vous pourriez utiliser QTextDocument ou QPrinter pour l'impression
        QMessageBox.information(self, "Impression", 
            f"Fiche de la variable '{var_name}' prête pour impression.\n\n"
            "La fonction d'impression directe sera implémentée dans une version future.")
    
    def add_personal_note(self):
        """Ajoute une note personnelle pour la variable courante"""
        if not self.current_variable:
            return
        
        from PyQt5.QtWidgets import QInputDialog
        
        var_name = self.current_variable["name"]
        current_note = self.notes_personnelles.get(var_name, "")
        
        note, ok = QInputDialog.getMultiLineText(
            self, 
            f"Note pour {var_name}",
            "Entrez votre note personnelle:",
            current_note
        )
        
        if ok and note is not None:
            self.notes_personnelles[var_name] = note.strip()
            if self._save_personal_notes():
                # Recharger les détails pour afficher la nouvelle note
                self.display_variable_details(var_name, self.current_variable["data"])
                self.status_label.setText(f"Note sauvegardée pour {var_name}")
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de sauvegarder la note.")
    
    def copy_to_clipboard(self, text: str):
        """Copie du texte dans le presse-papier"""
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        self.status_label.setText(f"Copié: {text}")