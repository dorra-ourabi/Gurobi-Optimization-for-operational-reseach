from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QComboBox,
    QSpinBox, QDoubleSpinBox, QGroupBox, QFormLayout, QTextEdit,
    QMessageBox, QSplitter, QProgressBar
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, pyqtSignal
from Oumayma.models.risk_calculator import ClientProfile, PretDemande
from Oumayma.ui.shared_data import SharedData
from .threads import OptimizationThread
from Oumayma.utils.validators import Validators

class ClientTab(QWidget):
    dossier_accepte = pyqtSignal(dict, int, float, str)  
    
    def __init__(self, optimizer_linear, optimizer_quad,validators):
        """Initialise l'onglet avec les deux optimiseurs disponibles."""
        super().__init__()
        # Stocke les deux optimiseurs (Linéaire par défaut, Quad si choisi)
        self.optimizer_linear = optimizer_linear
        self.optimizer_quad = optimizer_quad
        self.validators = validators
        
        self.init_ui()
    
        
    def connect_signals(self):
        """Connecte les signaux du thread (conservé pour complétude)"""
        if hasattr(self, 'thread'):
            self.thread.error.connect(self.handle_optimization_error)
    
    def handle_optimization_error(self, error_msg):
        self.btn_analyser.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        # Afficher erreur détaillée
        html_error = f"""
        <h2 style='color: red;'>ERREUR D'OPTIMISATION</h2>
        <div style='background-color: #ffebee; padding: 10px; border-radius: 5px;'>
            <p><b>Message:</b> {error_msg[:200]}...</p>
            <p><i>Vérifiez les données et réessayez</i></p>
        </div>
        """
        self.results_text.setHtml(html_error)
        
        QMessageBox.critical(self, "Erreur d'optimisation", 
            f"Erreur lors de l'optimisation:\n\n{error_msg[:500]}")
    
        
    def init_ui(self):
        """Initialise l'interface client"""
        layout = QVBoxLayout()
        
        # Titre
        title = QLabel("NOUVEAU DOSSIER CLIENT")
        title.setFont(QFont("Arial", 13, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setMaximumHeight(30)
        layout.addWidget(title)
        
        # Splitter horizontal
        splitter = QSplitter(Qt.Horizontal)
        
        # Partie gauche: Formulaire
        form_widget = QWidget()
        form_layout = QVBoxLayout()
        
        # Groupe Client
        client_group = self.create_client_group()
        form_layout.addWidget(client_group)
        
        # Groupe Prêt
        pret_group = self.create_pret_group()
        form_layout.addWidget(pret_group)
        
        solver_group = self.create_solver_group()
        form_layout.addWidget(solver_group)
        # -----------------------------
        
        # Bouton Analyser
        self.btn_analyser = QPushButton("ANALYSER ET OPTIMISER")
        self.btn_analyser.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.btn_analyser.clicked.connect(self.analyser)
        form_layout.addWidget(self.btn_analyser)
        
        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        form_layout.addWidget(self.progress_bar)
        
        form_widget.setLayout(form_layout)
        splitter.addWidget(form_widget)
        
        # Partie droite: Résultats
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setPlaceholderText("Les résultats s'afficheront ici...")
        splitter.addWidget(self.results_text)
        
        splitter.setSizes([400, 600])
        
        layout.addWidget(splitter)
        self.setLayout(layout)
    
    def create_client_group(self):
        group = QGroupBox("Informations Client")
        layout = QFormLayout()
        
        self.score_credit = QSpinBox()
        self.score_credit.setRange(300, 850)
        self.score_credit.setValue(720)
        
        self.revenu = QSpinBox()
        self.revenu.setRange(0, 50000)
        self.revenu.setSuffix(" €")
        self.revenu.setValue(3500)
        
        self.charges = QSpinBox()
        self.charges.setRange(0, 20000)
        self.charges.setSuffix(" €")
        self.charges.setValue(400)
        
        self.anciennete = QDoubleSpinBox()
        self.anciennete.setRange(0, 50)
        self.anciennete.setDecimals(1)
        self.anciennete.setSuffix(" ans")
        self.anciennete.setValue(3.0)
        
        self.nb_prets = QSpinBox()
        self.nb_prets.setRange(0, 10)
        self.nb_prets.setValue(1)
        
        self.historique = QDoubleSpinBox()
        self.historique.setRange(0, 1)
        self.historique.setDecimals(2)
        self.historique.setValue(0.90)
        
        self.type_contrat = QComboBox()
        self.type_contrat.addItems(["CDI", "CDD", "Intérimaire", "Indépendant", "Fonctionnaire"])
        
        self.segment = QComboBox()
        self.segment.addItems([
            "particulier_faible", "particulier_moyen", "particulier_eleve",
            "professionnel_pme", "primo_accedant"
        ])
        self.segment.setCurrentText("particulier_moyen")
        
        self.statut = QComboBox()
        self.statut.addItems(["nouveau", "recent", "fidele", "premium"])
        self.statut.setCurrentText("fidele")
        
        layout.addRow("Score de crédit (S_credit):", self.score_credit)
        layout.addRow("Revenu mensuel (R_mensuel):", self.revenu)
        layout.addRow("Charges mensuelles:", self.charges)
        layout.addRow("Ancienneté pro (A_prof):", self.anciennete)
        layout.addRow("Nombre de prêts (N_prets):", self.nb_prets)
        layout.addRow("Historique paiement (H_pay):", self.historique)
        layout.addRow("Type de contrat:", self.type_contrat)
        layout.addRow("Segment client:", self.segment)
        layout.addRow("Statut client:", self.statut)
        
        group.setLayout(layout)
        return group
    
    def create_pret_group(self):
        group = QGroupBox("Demande de Prêt")
        layout = QFormLayout()
        
        self.type_pret = QComboBox()
        self.type_pret.addItems(["immobilier", "automobile", "personnel", "professionnel", "etudiant"])
        self.type_pret.setCurrentText("automobile")
        
        self.montant = QSpinBox()
        self.montant.setRange(1000, 1000000)
        self.montant.setSuffix(" €")
        self.montant.setValue(20000)
        
        self.duree = QDoubleSpinBox()
        self.duree.setRange(0.5, 30)
        self.duree.setDecimals(1)
        self.duree.setSuffix(" ans")
        self.duree.setValue(5.0)
        
        self.apport = QSpinBox()
        self.apport.setRange(0, 1000000)
        self.apport.setSuffix(" €")
        self.apport.setValue(4000)
        
        layout.addRow("Type de prêt:", self.type_pret)
        layout.addRow("Montant demandé:", self.montant)
        layout.addRow("Durée souhaitée:", self.duree)
        layout.addRow("Apport personnel (A_p):", self.apport)
        
        group.setLayout(layout)
        return group

    def create_solver_group(self):
        group = QGroupBox("Paramètres d'Optimisation")
        layout = QFormLayout()
        
        self.solver_choice = QComboBox()
        self.solver_choice.addItems([
            "PLM (Linéaire par Discrétisation - Rapide/Fidèle)", 
            "QP (Quadratique Non-Linéaire - Exact/Lent)"
        ])
        self.solver_choice.setCurrentIndex(0) 
        
        layout.addRow("Méthode Solveur:", self.solver_choice)
        
        group.setLayout(layout)
        return group
    
    def _get_client_and_pret_objects(self) -> tuple[ClientProfile, PretDemande, str] | tuple[None, None, str]:
        """Récupère les données de l'UI et valide, puis crée les objets Profil."""
        
        # Dictionnaires de validation
        client_dict = {
            'score_credit': self.score_credit.value(),
            'revenu_mensuel': self.revenu.value(),
            'charges_mensuelles': self.charges.value(),
            'anciennete_pro': self.anciennete.value(),
            'nb_prets_existants': self.nb_prets.value()
        }
        
        pret_dict = {
            'montant': self.montant.value(),
            'duree': self.duree.value(),
            'type_pret': self.type_pret.currentText(),
            'apport': self.apport.value()
        }
        # Valider
        valid_client, msg_client = self.validators.validate_client_data(client_dict)
        if not valid_client:
            QMessageBox.warning(self, "Données client invalides", msg_client)
            return None, None, self.solver_choice.currentText()
        
        valid_pret, msg_pret = self.validators.validate_loan_data(pret_dict)
        if not valid_pret:
            QMessageBox.warning(self, "Données prêt invalides", msg_pret)
            return None, None, self.solver_choice.currentText()
        
        # Créer le profil client
        client = ClientProfile(
            score_credit=self.score_credit.value(),
            revenu_mensuel=self.revenu.value(),
            charges_mensuelles=self.charges.value(),
            apport_personnel=(self.apport.value() / self.montant.value() * 100) if self.montant.value() > 0 else 0,
            anciennete_pro=self.anciennete.value(),
            nb_prets_existants=self.nb_prets.value(),
            historique_paiement=self.historique.value(),
            type_contrat=self.type_contrat.currentText(),
            segment=self.segment.currentText(),
            statut_client=self.statut.currentText()
        )
        
        # Créer la demande de prêt
        pret = PretDemande(
            montant=self.montant.value(),
            duree=self.duree.value(),
            type_pret=self.type_pret.currentText(),
            apport=self.apport.value()
        )
        
        return client, pret, self.solver_choice.currentText()

    def analyser(self):
        """Lance l'analyse et l'optimisation"""
        self.btn_analyser.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 1. Validation et création des objets
        client, pret, solver_type = self._get_client_and_pret_objects()
        
        if client is None or pret is None:
            self.btn_analyser.setEnabled(True)
            self.progress_bar.setVisible(False)
            return
            
        # 2. Sélection de l'optimiseur
        if "PLM" in solver_type:
            current_optimizer = self.optimizer_linear
        else: # "QP"
            # Utilisation de l'optimiseur Quadratique
            current_optimizer = self.optimizer_quad 

        # 3. Lancer l'optimisation dans un thread
        self.thread = OptimizationThread(current_optimizer, client, pret)
        self.thread.progress.connect(self.progress_bar.setValue)
        self.thread.finished.connect(self.afficher_resultats)
        self.thread.error.connect(self.handle_optimization_error)
        self.thread.start()
    
    def afficher_resultats(self, resultat):
        """Affiche les résultats de l'optimisation"""
        self.btn_analyser.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        # Formater les résultats
        html = self.formater_resultats_html(resultat)
        self.results_text.setHtml(html)
        
        # Émettre un signal et sauvegarder si accepté
        if resultat.get('status') == 'ACCEPTE':
            client, pret, _ = self._get_client_and_pret_objects()
            if client and pret:
                self.dossier_accepte.emit(
                    resultat,
                    self.montant.value(),
                    self.duree.value(),
                    self.type_pret.currentText()
                )
                
                if 'SharedData' in globals():
                    SharedData.set_last_client_analysis(client, pret, resultat)

    def formater_resultats_html(self, res):
        if res['status'] != 'ACCEPTE':
            return f"""
            <h2 style='color: red;'>DOSSIER REFUSÉ</h2>
            <p><b>Statut:</b> {res['status']}</p>
            <p><b>Raison:</b> {res.get('raison', 'Non spécifié')}</p>
            """
        
        html = f"""
        <h2 style='color: green;'>DOSSIER ACCEPTÉ</h2>
        
        <h3>TAUX OPTIMAL</h3>
        <div style='background-color: #e8f5e9; padding: 10px; border-radius: 5px;'>
            <p style='font-size: 24px; font-weight: bold; color: #2e7d32; margin: 0;'>
                {res['taux_optimal']:.3f} %
            </p>
        </div>
        
        <h3>Détails Financiers</h3>
        <table style='width: 100%; border-collapse: collapse;'>
            <tr><td><b>TAEG:</b></td><td>{res['TAEG']:.3f} %</td></tr>
            <tr><td><b>Mensualité:</b></td><td>{res['mensualite']:.2f} €</td></tr>
            <tr><td><b>Coût total:</b></td><td>{res['cout_total']:.2f} €</td></tr>
            <tr><td><b>Dont intérêts:</b></td><td>{res['interets_totaux']:.2f} €</td></tr>
        </table>
        
        <h3>Analyse de Risque</h3>
        <table style='width: 100%;'>
            <tr><td><b>Probabilité de défaut (PD):</b></td><td>{res['probabilite_defaut']:.3f} %</td></tr>
            <tr><td><b>Nouveau ratio endettement:</b></td><td>{res['nouveau_ratio_endettement']:.2f} %</td></tr>
            <tr><td><b>Demande estimée:</b></td><td>{res['demande_estimee']:.1f} clients</td></tr>
        </table>
        
        <h3>Profitabilité Banque</h3>
        <table style='width: 100%;'>
            <tr><td><b>Revenus d'intérêts:</b></td><td>{res['profitabilite']['revenus_interets']:.2f} €</td></tr>
            <tr><td><b>Coût refinancement:</b></td><td>{res['profitabilite']['cout_refinancement']:.2f} €</td></tr>
            <tr><td><b>Coût opérationnel:</b></td><td>{res['profitabilite']['cout_operationnel']:.2f} €</td></tr>
            <tr><td><b>Perte attendue:</b></td><td>{res['profitabilite']['perte_attendue']:.2f} €</td></tr>
            <tr style='background-color: #fff3cd;'><td><b>Profit net:</b></td><td><b>{res['profitabilite']['profit_total_estime']:.2f} €</b></td></tr>
        </table>
        
        <h3>Comparaison Marché</h3>
        <table style='width: 100%;'>
            <tr><td><b>Taux concurrent:</b></td><td>{res['comparaison_marche']['taux_concurrent']:.3f} %</td></tr>
            <tr><td><b>Écart:</b></td><td>{res['comparaison_marche']['ecart']:.3f} %</td></tr>
            <tr><td><b>Position:</b></td><td>{res['comparaison_marche']['position']}</td></tr>
            <tr><td><b>Compétitivité:</b></td><td>{res['comparaison_marche']['competitivite']}</td></tr>
        </table>
        
        <h3>Décomposition du Taux</h3>
        <table style='width: 100%;'>
            <tr><td>Base refinancement:</td><td>{res['decomposition_taux']['base_refinancement']:.2f} %</td></tr>
            <tr><td>Marge minimale:</td><td>{res['decomposition_taux']['marge_minimale']:.2f} %</td></tr>
            <tr><td>Prime de risque:</td><td>{res['decomposition_taux']['prime_risque']:.2f} %</td></tr>
            <tr><td>Bonus apport:</td><td>{res['decomposition_taux']['bonus_apport']:.2f} %</td></tr>
            <tr><td>Ajustement marché:</td><td>{res['decomposition_taux']['ajustement_marche']:.2f} %</td></tr>
        </table>
        
        <h3>Conformité Réglementaire</h3>
        <table style='width: 100%;'>
            <tr><td>Taux d'usure:</td><td>{'✅' if res['conformite']['taux_usure'] else '❌'}</td></tr>
            <tr><td>Ratio endettement:</td><td>{'✅' if res['conformite']['ratio_endettement'] else '❌'}</td></tr>
            <tr><td>Score minimum:</td><td>{'✅' if res['conformite']['score_minimum'] else '❌'}</td></tr>
            <tr><td>TAEG conforme:</td><td>{'✅' if res['conformite']['TAEG_conforme'] else '❌'}</td></tr>
        </table>
        """
        
        return html