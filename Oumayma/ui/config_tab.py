from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QLabel, QLineEdit, QComboBox,
    QSpinBox, QDoubleSpinBox, QGroupBox, QFormLayout, QTextEdit,
    QTableWidget, QTableWidgetItem, QMessageBox, QFileDialog,
    QScrollArea, QSplitter, QProgressBar, QFrame, QTabWidget,
    QTabBar, QCheckBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
import json

from config.config_manager import ConfigManager


class ConfigurationTab(QWidget):
    """Onglet 1: Configuration des paramètres globaux - Version COMPLÈTE"""
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config = config_manager
        self.field_mapping = {}
        self.init_ui()
        self.apply_styles()
        self.load_current_values()
    
    def init_ui(self):
        """Initialise l'interface avec onglets pour chaque section"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        header = self.create_header()
        main_layout.addWidget(header)
        
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        
        tab_definitions = [
            ("Macro", self.create_macro_tab),
            ("Coûts", self.create_couts_tab),
            ("Réglementation", self.create_reglementaire_tab),
            ("Marché", self.create_marche_tab),
            ("Client", self.create_client_tab),
            ("Scoring", self.create_scoring_tab),
            ("Scénarios", self.create_scenario_tab),
            ("Capital", self.create_capital_tab),
            ("Avancé", self.create_avance_tab)
        ]
        
        for name, create_func in tab_definitions:
            tab = create_func()
            self.tabs.addTab(tab, name)
        
        main_layout.addWidget(self.tabs)
        status_bar = self.create_status_bar()
        main_layout.addWidget(status_bar)
        
        self.setLayout(main_layout)
    
    def create_header(self):
        """Crée l'en-tête avec boutons d'action"""
        header = QFrame()
        header.setObjectName("header")
        layout = QHBoxLayout(header)
        
        # Titre
        title_layout = QHBoxLayout()
        icon = QLabel("⚙️")
        icon.setFont(QFont("Segoe UI Emoji", 24))
        title = QLabel("CONFIGURATION COMPLÈTE")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color: #2c3e50;")
        
        title_layout.addWidget(icon)
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        # Boutons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        buttons = [
            ("Importer", self.import_config, "#3498db"),
            ("Tout réinitialiser", self.reset_all, "#e74c3c"),
            ("Sauvegarder", self.save_config, "#27ae60"),
            ("Exporter", self.export_config, "#9b59b6"),
            ("Tester", self.test_configuration, "#f39c12")
        ]
        
        for text, callback, color in buttons:
            btn = self.create_header_button(text, color)
            btn.clicked.connect(callback)
            btn_layout.addWidget(btn)
        
        layout.addLayout(title_layout)
        layout.addStretch()
        layout.addLayout(btn_layout)
        
        return header
    
    def create_macro_tab(self):
        """Onglet des paramètres macroéconomiques"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(15)
        
        bce_group = QGroupBox("Taux Directeur BCE")
        bce_layout = QFormLayout()
        
        fields = [
            ("Valeur", "parametres_macroeconomiques.taux_directeur_bce.valeur", "%", 0, 10, 2),
            ("Min", "parametres_macroeconomiques.taux_directeur_bce.min", "%", 0, 10, 2),
            ("Max", "parametres_macroeconomiques.taux_directeur_bce.max", "%", 0, 10, 2)
        ]
        
        for label_text, path, suffix, min_val, max_val, decimals in fields:
            label = QLabel(label_text)
            spinbox = self.create_double_spinbox(path, min_val, max_val, suffix, decimals)
            bce_layout.addRow(label, spinbox)
        
        bce_group.setLayout(bce_layout)
        content_layout.addWidget(bce_group)
        
        euribor_group = QGroupBox("Taux EURIBOR")
        euribor_layout = QFormLayout()
        
        euribor_fields = [
            ("EURIBOR 3 mois", "parametres_macroeconomiques.taux_euribor_3m.valeur", "%", 0, 10, 2),
            ("EURIBOR 12 mois", "parametres_macroeconomiques.taux_euribor_12m.valeur", "%", 0, 10, 2)
        ]
        
        for label_text, path, suffix, min_val, max_val, decimals in euribor_fields:
            label = QLabel(label_text)
            spinbox = self.create_double_spinbox(path, min_val, max_val, suffix, decimals)
            euribor_layout.addRow(label, spinbox)
        
        euribor_group.setLayout(euribor_layout)
        content_layout.addWidget(euribor_group)
        
        autres_group = QGroupBox("Autres Indicateurs")
        autres_layout = QFormLayout()
        
        autres_fields = [
            ("Inflation", "parametres_macroeconomiques.taux_inflation.valeur", "%", -2, 15, 2),
            ("Croissance PIB", "parametres_macroeconomiques.croissance_economique.valeur", "%", -10, 15, 2),
            ("Chômage", "parametres_macroeconomiques.taux_chomage.valeur", "%", 0, 30, 1)
        ]
        
        for label_text, path, suffix, min_val, max_val, decimals in autres_fields:
            label = QLabel(label_text)
            spinbox = self.create_double_spinbox(path, min_val, max_val, suffix, decimals)
            autres_layout.addRow(label, spinbox)
        
        autres_group.setLayout(autres_layout)
        content_layout.addWidget(autres_group)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        widget.setLayout(layout)
        return widget
    
    def create_couts_tab(self):
        """Onglet des coûts de la banque"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(15)
        
        base_group = QGroupBox("Coûts de Base")
        base_layout = QFormLayout()
        
        base_fields = [
            ("Coût refinancement", "couts_et_risques.cout_refinancement.valeur", "%", 1, 10, 2),
            ("Spread bancaire", "couts_et_risques.spread_bancaire.valeur", "%", 0.1, 1.5, 2),
            ("Marge minimale", "couts_et_risques.marge_minimale.valeur", "%", 0.3, 3, 2),
            ("Perte défaut (LGD)", "couts_et_risques.perte_en_cas_defaut_LGD.valeur", "%", 20, 80, 1)
        ]
        
        for label_text, path, suffix, min_val, max_val, decimals in base_fields:
            label = QLabel(label_text)
            spinbox = self.create_double_spinbox(path, min_val, max_val, suffix, decimals)
            base_layout.addRow(label, spinbox)
        
        base_group.setLayout(base_layout)
        content_layout.addWidget(base_group)
        
        op_group = QGroupBox("Coûts Opérationnels")
        op_layout = QFormLayout()
        
        op_fields = [
            ("Immobilier", "couts_et_risques.couts_operationnels.immobilier.valeur", "€", 500, 5000, 0),
            ("Automobile", "couts_et_risques.couts_operationnels.automobile.valeur", "€", 200, 2000, 0),
            ("Personnel", "couts_et_risques.couts_operationnels.personnel.valeur", "€", 100, 1000, 0),
            ("Professionnel", "couts_et_risques.couts_operationnels.professionnel.valeur", "€", 300, 5000, 0),
            ("Étudiant", "couts_et_risques.couts_operationnels.etudiant.valeur", "€", 100, 1000, 0)
        ]
        
        for label_text, path, suffix, min_val, max_val, decimals in op_fields:
            label = QLabel(label_text)
            if decimals == 0:
                spinbox = self.create_spinbox(path, min_val, max_val, suffix)
            else:
                spinbox = self.create_double_spinbox(path, min_val, max_val, suffix, decimals)
            op_layout.addRow(label, spinbox)
        
        op_group.setLayout(op_layout)
        content_layout.addWidget(op_group)
        
        provision_group = QGroupBox("Provisions Risque")
        provision_layout = QFormLayout()
        
        provision_fields = [
            ("Taux provision", "couts_et_risques.provisions_risque.taux_provision.valeur", "%", 0.5, 5, 2),
            ("Fonds garantie", "couts_et_risques.provisions_risque.fonds_garantie.valeur", "€", 100000, 10000000, 0)
        ]
        
        for label_text, path, suffix, min_val, max_val, decimals in provision_fields:
            label = QLabel(label_text)
            if decimals == 0:
                spinbox = self.create_spinbox(path, min_val, max_val, suffix)
            else:
                spinbox = self.create_double_spinbox(path, min_val, max_val, suffix, decimals)
            provision_layout.addRow(label, spinbox)
        
        provision_group.setLayout(provision_layout)
        content_layout.addWidget(provision_group)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        widget.setLayout(layout)
        return widget
    
    def create_reglementaire_tab(self):
        """Onglet des contraintes réglementaires"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(15)
        
        base_group = QGroupBox("Contraintes de Base")
        base_layout = QFormLayout()
        
        base_fields = [
            ("Ratio endettement max", "contraintes_reglementaires.ratio_endettement_max.valeur", "%", 25, 45, 1),
            ("Score crédit min", "contraintes_reglementaires.score_credit_minimum.valeur", "points", 300, 850, 0),
            ("Ratio Bâle III", "contraintes_reglementaires.ratio_solvabilite_bale3.valeur", "%", 8, 20, 1),
            ("Ratio liquidité", "contraintes_reglementaires.ratio_liquidite_LCR.valeur", "%", 100, 200, 1)
        ]
        
        for label_text, path, suffix, min_val, max_val, decimals in base_fields:
            label = QLabel(label_text)
            if decimals == 0:
                spinbox = self.create_spinbox(path, min_val, max_val, suffix)
            else:
                spinbox = self.create_double_spinbox(path, min_val, max_val, suffix, decimals)
            base_layout.addRow(label, spinbox)
        
        base_group.setLayout(base_layout)
        content_layout.addWidget(base_group)
        
        usure_group1 = QGroupBox("Taux d'Usure - Court Terme")
        usure_layout1 = QFormLayout()
        
        usure_fields1 = [
            ("Immobilier <2 ans", "contraintes_reglementaires.taux_usure.immobilier.court_terme.valeur", "%", 1, 15, 2),
            ("Automobile <2 ans", "contraintes_reglementaires.taux_usure.automobile.court_terme.valeur", "%", 1, 15, 2),
            ("Personnel <2 ans", "contraintes_reglementaires.taux_usure.personnel.court_terme.valeur", "%", 1, 15, 2)
        ]
        
        for label_text, path, suffix, min_val, max_val, decimals in usure_fields1:
            label = QLabel(label_text)
            spinbox = self.create_double_spinbox(path, min_val, max_val, suffix, decimals)
            usure_layout1.addRow(label, spinbox)
        
        usure_group1.setLayout(usure_layout1)
        content_layout.addWidget(usure_group1)
        
        usure_group2 = QGroupBox("Taux d'Usure - Moyen & Long Terme")
        usure_layout2 = QFormLayout()
        
        usure_fields2 = [
            ("Immobilier 2-7 ans", "contraintes_reglementaires.taux_usure.immobilier.moyen_terme.valeur", "%", 1, 15, 2),
            ("Immobilier >7 ans", "contraintes_reglementaires.taux_usure.immobilier.long_terme.valeur", "%", 1, 15, 2),
            ("Automobile 2-7 ans", "contraintes_reglementaires.taux_usure.automobile.moyen_terme.valeur", "%", 1, 15, 2),
            ("Automobile >7 ans", "contraintes_reglementaires.taux_usure.automobile.long_terme.valeur", "%", 1, 15, 2)
        ]
        
        for label_text, path, suffix, min_val, max_val, decimals in usure_fields2:
            label = QLabel(label_text)
            spinbox = self.create_double_spinbox(path, min_val, max_val, suffix, decimals)
            usure_layout2.addRow(label, spinbox)
        
        usure_group2.setLayout(usure_layout2)
        content_layout.addWidget(usure_group2)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        widget.setLayout(layout)
        return widget
    
    def create_marche_tab(self):
        """Onglet des paramètres de marché"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(15)
        
        general_group = QGroupBox("Paramètres Généraux")
        general_layout = QFormLayout()
        
        general_fields = [
            ("Demande base", "parametres_marche.demande_base.valeur", "clients", 50, 5000, 0),
            ("Part marché cible", "parametres_marche.part_marche_visee.valeur", "%", 5, 30, 1),
            ("Marge compétitive max", "parametres_marche.marge_competitive_max.valeur", "%", 5, 30, 1)
        ]
        
        for label_text, path, suffix, min_val, max_val, decimals in general_fields:
            label = QLabel(label_text)
            if decimals == 0:
                spinbox = self.create_spinbox(path, min_val, max_val, suffix)
            else:
                spinbox = self.create_double_spinbox(path, min_val, max_val, suffix, decimals)
            general_layout.addRow(label, spinbox)
        
        general_group.setLayout(general_layout)
        content_layout.addWidget(general_group)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        widget.setLayout(layout)
        return widget
    
    def create_client_tab(self):
        """Onglet des caractéristiques client"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(15)
        
        plages_group = QGroupBox("Plages de Valeurs Acceptées")
        plages_layout = QFormLayout()
        
        plages_fields = [
            ("Revenu min", "caracteristiques_client.revenu_mensuel.min", "€", 100, 50000, 0),
            ("Revenu max", "caracteristiques_client.revenu_mensuel.max", "€", 100, 50000, 0),
            ("Charges min", "caracteristiques_client.charges_mensuelles.min", "€", 0, 20000, 0),
            ("Charges max", "caracteristiques_client.charges_mensuelles.max", "€", 0, 20000, 0),
            ("Apport recommandé", "caracteristiques_client.apport_personnel.recommande_immo", "%", 0, 100, 0)
        ]
        
        for label_text, path, suffix, min_val, max_val, decimals in plages_fields:
            label = QLabel(label_text)
            if decimals == 0:
                spinbox = self.create_spinbox(path, min_val, max_val, suffix)
            else:
                spinbox = self.create_double_spinbox(path, min_val, max_val, suffix, decimals)
            plages_layout.addRow(label, spinbox)
        
        plages_group.setLayout(plages_layout)
        content_layout.addWidget(plages_group)
        
        bonus_group = QGroupBox("Bonus selon Statut Client")
        bonus_layout = QFormLayout()
        
        bonus_fields = [
            ("Client récent", "caracteristiques_client.statut_client.recent.bonus_taux", "%", -1, 0, 2),
            ("Client fidèle", "caracteristiques_client.statut_client.fidele.bonus_taux", "%", -1, 0, 2),
            ("Client premium", "caracteristiques_client.statut_client.premium.bonus_taux", "%", -1, 0, 2)
        ]
        
        for label_text, path, suffix, min_val, max_val, decimals in bonus_fields:
            label = QLabel(label_text)
            spinbox = self.create_double_spinbox(path, min_val, max_val, suffix, decimals)
            bonus_layout.addRow(label, spinbox)
        
        bonus_group.setLayout(bonus_layout)
        content_layout.addWidget(bonus_group)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        widget.setLayout(layout)
        return widget
    
    def create_scoring_tab(self):
        """Onglet du calcul de probabilité de défaut"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(15)
        
        poids_group = QGroupBox("Poids des Facteurs de Risque")
        poids_layout = QFormLayout()
        
        poids_fields = [
            ("Score crédit", "calcul_probabilite_defaut.poids_score_credit.valeur", "", 2, 8, 1),
            ("Ratio endettement", "calcul_probabilite_defaut.poids_ratio_endettement.valeur", "", 1, 6, 1),
            ("Nb prêts", "calcul_probabilite_defaut.poids_nombre_prets.valeur", "", 0.1, 2, 1),
            ("Ancienneté", "calcul_probabilite_defaut.poids_anciennete_pro.valeur", "", 0, 2, 2),
            ("Historique paiement", "calcul_probabilite_defaut.poids_historique_paiement.valeur", "", 0.5, 4, 1),
            ("Type contrat", "calcul_probabilite_defaut.poids_type_contrat.valeur", "", 0.5, 3, 1)
        ]
        
        for label_text, path, suffix, min_val, max_val, decimals in poids_fields:
            label = QLabel(label_text)
            spinbox = self.create_double_spinbox(path, min_val, max_val, suffix, decimals)
            poids_layout.addRow(label, spinbox)
        
        poids_group.setLayout(poids_layout)
        content_layout.addWidget(poids_group)
        
        pd_group = QGroupBox("Paramètres PD")
        pd_layout = QFormLayout()
        
        pd_fields = [
            ("Décalage logistique", "calcul_probabilite_defaut.decalage_logistique.valeur", "", 1, 5, 1),
            ("PD minimum", "calcul_probabilite_defaut.PD_minimum.valeur", "%", 0.05, 2, 2),
            ("PD maximum", "calcul_probabilite_defaut.PD_maximum.valeur", "%", 5, 30, 1),
            ("Facteur prime risque", "calcul_probabilite_defaut.facteur_prime_risque.valeur", "", 0.1, 0.8, 2)
        ]
        
        for label_text, path, suffix, min_val, max_val, decimals in pd_fields:
            label = QLabel(label_text)
            spinbox = self.create_double_spinbox(path, min_val, max_val, suffix, decimals)
            pd_layout.addRow(label, spinbox)
        
        pd_group.setLayout(pd_layout)
        content_layout.addWidget(pd_group)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        widget.setLayout(layout)
        return widget
    
    def create_scenario_tab(self):
        """Onglet des scénarios économiques"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(15)
        
        select_group = QGroupBox("Scénario Actif")
        select_layout = QFormLayout()
        
        label = QLabel("Scénario actuel:")
        self.scenario_combo = QComboBox()
        self.scenario_combo.addItems(["normal", "crise", "expansion", "recession", "stagnation"])
        self.field_mapping[self.scenario_combo] = "scenarios_economiques.scenario_actif.valeur"
        
        select_layout.addRow(label, self.scenario_combo)
        select_group.setLayout(select_layout)
        content_layout.addWidget(select_group)
        
        facteurs_group = QGroupBox("Facteurs par Scénario")
        facteurs_layout = QFormLayout()
        
        facteurs_fields = [
            ("Normal - PD", "scenarios_economiques.normal.facteur_PD", "×", 1, 3, 1),
            ("Normal - Demande", "scenarios_economiques.normal.facteur_demande", "×", 0.1, 2, 1),
            ("Crise - PD", "scenarios_economiques.crise.facteur_PD", "×", 1, 3, 1),
            ("Crise - Demande", "scenarios_economiques.crise.facteur_demande", "×", 0.1, 2, 1),
            ("Expansion - PD", "scenarios_economiques.expansion.facteur_PD", "×", 0.5, 1.5, 1),
            ("Expansion - Demande", "scenarios_economiques.expansion.facteur_demande", "×", 0.5, 2, 1),
            ("Recession - PD", "scenarios_economiques.recession.facteur_PD", "×", 1, 3, 1),
            ("Recession - Demande", "scenarios_economiques.recession.facteur_demande", "×", 0.1, 2, 1),
            ("Stagnation - PD", "scenarios_economiques.stagnation.facteur_PD", "×", 1, 3, 1),
            ("Stagnation - Demande", "scenarios_economiques.stagnation.facteur_demande", "×", 0.1, 2, 1)
        ]
        
        for label_text, path, suffix, min_val, max_val, decimals in facteurs_fields:
            label = QLabel(label_text)
            spinbox = self.create_double_spinbox(path, min_val, max_val, suffix, decimals)
            facteurs_layout.addRow(label, spinbox)
        
        facteurs_group.setLayout(facteurs_layout)
        content_layout.addWidget(facteurs_group)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        widget.setLayout(layout)
        return widget
    
    def create_capital_tab(self):
        """Onglet du capital et portefeuille"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(15)
        
        capital_group = QGroupBox("Capital Disponible")
        capital_layout = QFormLayout()
        
        capital_fields = [
            ("Capital total", "capital_et_portefeuille.capital_disponible_total.valeur", "€", 1000000, 100000000, 0)
        ]
        
        for label_text, path, suffix, min_val, max_val, decimals in capital_fields:
            label = QLabel(label_text)
            spinbox = self.create_spinbox(path, min_val, max_val, suffix)
            capital_layout.addRow(label, spinbox)
        
        capital_group.setLayout(capital_layout)
        content_layout.addWidget(capital_group)
        
        quotas_group = QGroupBox("Quotas Maximum par Type de Prêt")
        quotas_layout = QFormLayout()
        
        quotas_fields = [
            ("Immobilier", "capital_et_portefeuille.quotas_par_type.immobilier.quota_max", "€", 0, 10000000, 0),
            ("Automobile", "capital_et_portefeuille.quotas_par_type.automobile.quota_max", "€", 0, 10000000, 0),
            ("Personnel", "capital_et_portefeuille.quotas_par_type.personnel.quota_max", "€", 0, 10000000, 0),
            ("Professionnel", "capital_et_portefeuille.quotas_par_type.professionnel.quota_max", "€", 0, 10000000, 0),
            ("Étudiant", "capital_et_portefeuille.quotas_par_type.etudiant.quota_max", "€", 0, 10000000, 0)
        ]
        
        for label_text, path, suffix, min_val, max_val, decimals in quotas_fields:
            label = QLabel(label_text)
            spinbox = self.create_spinbox(path, min_val, max_val, suffix)
            quotas_layout.addRow(label, spinbox)
        
        quotas_group.setLayout(quotas_layout)
        content_layout.addWidget(quotas_group)
        
        divers_group = QGroupBox("Diversification")
        divers_layout = QFormLayout()
        
        self.divers_checkbox = QCheckBox("Activer la diversification")
        self.field_mapping[self.divers_checkbox] = "capital_et_portefeuille.diversification.activer"
        divers_layout.addRow(self.divers_checkbox)
        
        divers_fields = [
            ("Ratio min par type", "capital_et_portefeuille.diversification.ratio_min_par_type", "%", 0, 100, 0),
            ("Ratio max par type", "capital_et_portefeuille.diversification.ratio_max_par_type", "%", 0, 100, 0)
        ]
        
        for label_text, path, suffix, min_val, max_val, decimals in divers_fields:
            label = QLabel(label_text)
            spinbox = self.create_spinbox(path, min_val, max_val, suffix)
            divers_layout.addRow(label, spinbox)
        
        divers_group.setLayout(divers_layout)
        content_layout.addWidget(divers_group)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        widget.setLayout(layout)
        return widget
    
    def create_avance_tab(self):
        """Onglet des paramètres avancés"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(15)
        
        apport_group = QGroupBox("Bonus Apport Personnel")
        apport_layout = QFormLayout()
        
        apport_fields = [
            ("Seuil apport bonus", "parametres_avances.seuil_apport_bonus.valeur", "%", 10, 50, 0),
            ("Réduction taux", "parametres_avances.reduction_taux_apport.valeur", "%", 0, 0.3, 2)
        ]
        
        for label_text, path, suffix, min_val, max_val, decimals in apport_fields:
            label = QLabel(label_text)
            if decimals == 0:
                spinbox = self.create_spinbox(path, min_val, max_val, suffix)
            else:
                spinbox = self.create_double_spinbox(path, min_val, max_val, suffix, decimals)
            apport_layout.addRow(label, spinbox)
        
        apport_group.setLayout(apport_layout)
        content_layout.addWidget(apport_group)
        
        duree_group = QGroupBox("Prime Durée")
        duree_layout = QFormLayout()
        
        duree_fields = [
            ("Prime par année", "parametres_avances.prime_duree_par_an.valeur", "%", 0, 0.15, 3)
        ]
        
        for label_text, path, suffix, min_val, max_val, decimals in duree_fields:
            label = QLabel(label_text)
            spinbox = self.create_double_spinbox(path, min_val, max_val, suffix, decimals)
            duree_layout.addRow(label, spinbox)
        
        duree_group.setLayout(duree_layout)
        content_layout.addWidget(duree_group)
        
        assurance_group = QGroupBox("Assurance")
        assurance_layout = QFormLayout()
        
        assurance_fields = [
            ("Taux assurance moyen", "parametres_avances.taux_assurance_moyen.valeur", "%", 0.1, 0.5, 2)
        ]
        
        for label_text, path, suffix, min_val, max_val, decimals in assurance_fields:
            label = QLabel(label_text)
            spinbox = self.create_double_spinbox(path, min_val, max_val, suffix, decimals)
            assurance_layout.addRow(label, spinbox)
        
        assurance_group.setLayout(assurance_layout)
        content_layout.addWidget(assurance_group)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        widget.setLayout(layout)
        return widget
    
    def create_double_spinbox(self, path, min_val, max_val, suffix="", decimals=2):
        """Crée un QDoubleSpinBox et le mappe"""
        spinbox = QDoubleSpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setDecimals(decimals)
        if suffix:
            spinbox.setSuffix(f" {suffix}")
        spinbox.setStyleSheet(self.get_spinbox_style())
        self.field_mapping[spinbox] = path
        return spinbox
    
    def create_spinbox(self, path, min_val, max_val, suffix=""):
        """Crée un QSpinBox et le mappe"""
        spinbox = QSpinBox()
        spinbox.setRange(min_val, max_val)
        if suffix:
            spinbox.setSuffix(f" {suffix}")
        spinbox.setStyleSheet(self.get_spinbox_style())
        self.field_mapping[spinbox] = path
        return spinbox
    
    def load_current_values(self):
        """Charge les valeurs actuelles dans tous les champs"""
        for widget, config_path in self.field_mapping.items():
            keys = config_path.split('.')
            
            try:
                value = self.config.config
                for key in keys:
                    if key in value:
                        value = value[key]
                    else:
                        value = None
                        break
                
                if value is not None:
                    if isinstance(widget, QDoubleSpinBox):
                        widget.setValue(float(value))
                    elif isinstance(widget, QSpinBox):
                        widget.setValue(int(value))
                    elif isinstance(widget, QComboBox):
                        widget.setCurrentText(str(value))
                    elif isinstance(widget, QCheckBox):
                        widget.setChecked(bool(value))
                        
            except Exception as e:
                print(f"Erreur chargement {config_path}: {e}")
                continue
    
    def save_config(self):
        """Sauvegarde toutes les modifications"""
        try:
            modifications = 0
            
            for widget, config_path in self.field_mapping.items():
                try:
                    if isinstance(widget, QDoubleSpinBox):
                        value = widget.value()
                    elif isinstance(widget, QSpinBox):
                        value = widget.value()
                    elif isinstance(widget, QComboBox):
                        value = widget.currentText()
                    elif isinstance(widget, QCheckBox):
                        value = widget.isChecked()
                    else:
                        continue
                    
                    # Mettre à jour la configuration
                    keys = config_path.split('.')
                    
                    # Naviguer jusqu'au niveau parent
                    current = self.config.config
                    for key in keys[:-1]:
                        if key not in current:
                            current[key] = {}
                        current = current[key]
                    
                    # Mettre la valeur
                    current[keys[-1]] = value
                    modifications += 1
                    
                except Exception as e:
                    print(f"Erreur sauvegarde {config_path}: {e}")
                    continue
            
            # Sauvegarder sur disque
            if self.config.save_user_config():
                self.show_status_message(
                    f"{modifications} paramètres sauvegardés",
                    "#27ae60"
                )
                QMessageBox.information(self, "Succès", 
                    f"Configuration sauvegardée avec succès!\n"
                    f"{modifications} paramètres mis à jour.")
            else:
                self.show_status_message("Erreur sauvegarde", "#e74c3c")
                
        except Exception as e:
            self.show_status_message(f"Erreur: {str(e)[:50]}...", "#e74c3c")
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde:\n\n{str(e)}")
    
    def test_configuration(self):
        """Teste la configuration actuelle"""
        try:
            # Vérifier les taux d'usure
            taux_bce = self.config.get("parametres_macroeconomiques", "taux_directeur_bce", "valeur")
            marge_min = self.config.get("couts_et_risques", "marge_minimale", "valeur")
            
            taux_min = float(taux_bce) + float(marge_min)
            
            # Vérifier un taux d'usure
            taux_usure_auto = self.config.get("contraintes_reglementaires", "taux_usure", "automobile", "moyen_terme", "valeur")
            
            message = f"""
            TEST DE CONFIGURATION
            
            Taux BCE: {taux_bce}%
            Marge min: {marge_min}%
            Taux min théorique: {taux_min:.2f}%
            
            Taux usure auto: {taux_usure_auto}%
            
            Résultat: {'OK' if taux_min < float(taux_usure_auto) else 'Problème potentiel'}
            """
            
            QMessageBox.information(self, "Test Configuration", message)
            self.show_status_message("Test configuration effectué", "#f39c12")
            
        except Exception as e:
            QMessageBox.warning(self, "Test Erreur", f"Impossible de tester:\n\n{str(e)}")
    
    def reset_all(self):
        """Réinitialise toute la configuration"""
        reply = QMessageBox.question(
            self, "Confirmation",
            "Voulez-vous vraiment réinitialiser TOUS les paramètres?\n"
            "Toutes vos modifications seront perdues.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.config.reset_to_default()
            self.load_current_values()
            self.show_status_message("Configuration réinitialisée", "#f39c12")
            QMessageBox.information(self, "Réinitialisation", 
                "Tous les paramètres ont été réinitialisés aux valeurs par défaut.")
    
    def import_config(self):
        """Importe une configuration depuis un fichier"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Importer Configuration",
            "", "Fichiers JSON (*.json)"
        )
        
        if filepath:
            try:
                if self.config.import_config(filepath):
                    self.load_current_values()
                    self.show_status_message(f"Configuration importée", "#3498db")
                    QMessageBox.information(self, "Importation", 
                        f"Configuration importée avec succès depuis:\n{filepath}")
                else:
                    QMessageBox.warning(self, "Importation", "Échec de l'importation.")
                    
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur importation:\n\n{str(e)}")
    
    def export_config(self):
        """Exporte la configuration actuelle"""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Exporter Configuration",
            f"config_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "Fichiers JSON (*.json)"
        )
        
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(self.config.config, f, indent=2, ensure_ascii=False)
                
                self.show_status_message(f"Configuration exportée", "#9b59b6")
                QMessageBox.information(self, "Exportation", 
                    f"Configuration exportée avec succès vers:\n{filepath}")
                    
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur exportation:\n\n{str(e)}")
    
    def create_status_bar(self):
        """Crée la barre de statut"""
        status = QFrame()
        status.setObjectName("statusBar")
        layout = QHBoxLayout(status)
        
        self.status_label = QLabel("Prêt à configurer")
        self.status_label.setFont(QFont("Segoe UI", 9))
        
        # Compter les paramètres
        param_count = len(self.field_mapping)
        count_label = QLabel(f"{param_count} paramètres configurables")
        count_label.setStyleSheet("color: #7f8c8d; font-size: 9px;")
        
        layout.addWidget(self.status_label)
        layout.addStretch()
        layout.addWidget(count_label)
        
        return status
    
    def show_status_message(self, message: str, color: str = "#2c3e50"):
        """Affiche un message dans la barre de statut"""
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold;")
    
    def get_spinbox_style(self):
        """Retourne le style CSS pour les spinboxes"""
        return """
            QSpinBox, QDoubleSpinBox {
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
                min-width: 120px;
                background-color: white;
            }
            QSpinBox:hover, QDoubleSpinBox:hover {
                border-color: #3498db;
            }
        """
    
    def create_header_button(self, text: str, color: str):
        """Crée un bouton d'en-tête stylisé"""
        btn = QPushButton(text)
        btn.setFont(QFont("Segoe UI", 10))
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                min-width: 120px;
            }}
            QPushButton:hover {{
                background-color: {self.darken_color(color, 20)};
            }}
            QPushButton:pressed {{
                background-color: {self.darken_color(color, 40)};
            }}
        """)
        return btn
    
    def darken_color(self, hex_color: str, percent: int):
        """Assombrit une couleur"""
        return hex_color
    
    def apply_styles(self):
        """Applique les styles globaux"""
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f7fa;
                font-family: 'Segoe UI';
            }
            #header {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ffffff, stop:1 #f8f9fa);
                border-radius: 10px;
                padding: 15px;
                border: 1px solid #e1e8ed;
            }
            #statusBar {
                background-color: white;
                border-radius: 6px;
                padding: 8px 15px;
                border: 1px solid #e1e8ed;
            }
            QTabWidget::pane {
                border: 1px solid #e0e0e0;
                background: white;
                border-radius: 8px;
            }
            QTabBar::tab {
                background: #eceff1;
                color: #546e7a;
                padding: 12px 20px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: bold;
                font-size: 11px;
            }
            QTabBar::tab:selected {
                background: white;
                color: #1976D2;
                border-bottom: 3px solid #1976D2;
            }
            QGroupBox {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px 0 5px;
                color: #2c3e50;
                font-weight: bold;
            }
        """)