import traceback
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QComboBox, QDoubleSpinBox, QSpinBox, QGroupBox, QFormLayout,
    QTableWidget, QTableWidgetItem, QMessageBox,
    QTextEdit, QProgressBar, QScrollArea, QFrame, QHeaderView, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor
import numpy as np
from typing import Dict, List
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from models.risk_calculator import ClientProfile, PretDemande
from .threads import OptimizationThread


class SensitivityAnalysisThread(QThread):
    """Thread pour analyse de sensibilité"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, optimizer, base_client, base_pret, param_name, 
                 min_val, max_val, num_points):
        super().__init__()
        self.optimizer = optimizer
        self.base_client = base_client
        self.base_pret = base_pret
        self.param_name = param_name
        self.min_val = min_val
        self.max_val = max_val
        self.num_points = num_points
        self.results = []
    
    def run(self):
        try:
            self.results = []
            values = np.linspace(self.min_val, self.max_val, self.num_points)
            
            for i, value in enumerate(values):
                self.progress.emit(int((i / len(values)) * 100))
                
                # Créer copies modifiées
                client = self._modify_client(value)
                pret = self._modify_pret(value)
                
                # Exécuter optimisation
                result = self.optimizer.optimiser_taux(client, pret)
                
                if result.get('status') == 'ACCEPTE':
                    self.results.append({
                        'param_value': value,
                        'taux_optimal': result.get('taux_optimal', 0),
                        'mensualite': result.get('mensualite', 0),
                        'profit': result.get('profitabilite', {}).get('profit_total_estime', 0),
                        'demande': result.get('demande_estimee', 0),
                        'PD': result.get('probabilite_defaut', 0)
                    })
                else:
                    self.results.append({
                        'param_value': value,
                        'taux_optimal': None,
                        'error': result.get('raison', 'Erreur')
                    })
            
            self.progress.emit(100)
            self.finished.emit(self.results)
            
        except Exception as e:
            self.error.emit(f"Erreur analyse: {str(e)}")
    
    def _modify_client(self, value):
        """Modifie le client selon le paramètre"""
        import copy
        client = copy.copy(self.base_client)
        
        if self.param_name == "score_credit":
            client.score_credit = int(value)
        elif self.param_name == "revenu_mensuel":
            client.revenu_mensuel = value
        elif self.param_name == "charges_mensuelles":
            client.charges_mensuelles = value
        
        return client
    
    def _modify_pret(self, value):
        """Modifie le prêt selon le paramètre"""
        import copy
        pret = copy.copy(self.base_pret)
        
        if self.param_name == "montant":
            pret.montant = value
        elif self.param_name == "duree":
            pret.duree = value
        
        return pret


class AnalyseTab(QWidget):
    """Onglet 3: Analyse de sensibilité - Version Scrollable"""
    
    def __init__(self, optimizer, main_window=None):
        super().__init__()
        self.optimizer = optimizer
        self.main_window = main_window
        self.current_results = []
        self.base_client = None
        self.base_pret = None
        self.init_ui()
    
    def init_ui(self):
        scroll_widget = QWidget()
        layout = QVBoxLayout(scroll_widget)
        layout.setSpacing(15)
        title_frame = QFrame()
        title_frame.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        title_layout = QVBoxLayout(title_frame)
        
        title = QLabel("ANALYSE DE SENSIBILITÉ")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setStyleSheet("color: white;")
        title.setAlignment(Qt.AlignCenter)
        
        subtitle = QLabel("Testez l'impact des variables sur votre taux optimal")
        subtitle.setFont(QFont("Arial", 11))
        subtitle.setStyleSheet("color: #bdc3c7;")
        subtitle.setAlignment(Qt.AlignCenter)
        
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        
        layout.addWidget(title_frame)
        explication_frame = QFrame()
        explication_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        explication_layout = QVBoxLayout(explication_frame)
        
        explication_title = QLabel("À QUOI ÇA SERT ?")
        explication_title.setFont(QFont("Arial", 13, QFont.Bold))
        explication_title.setStyleSheet("color: #2c3e50;")
        
        explication_text = QLabel(
            "L'analyse de sensibilité vous permet de comprendre comment une variable\n"
            "(score, revenu, montant, durée) influence votre taux optimal.\n\n"
            "Exemple: 'Si le score du client baisse de 50 points, de combien mon taux augmente-t-il ?'"
        )
        explication_text.setFont(QFont("Arial", 11))
        explication_text.setStyleSheet("color: #495057;")
        
        explication_layout.addWidget(explication_title)
        explication_layout.addWidget(explication_text)
        
        layout.addWidget(explication_frame)
        
        base_group = QGroupBox("ÉTAPE 1: Charger les données du client")
        base_group.setFont(QFont("Arial", 12, QFont.Bold))
        base_layout = QVBoxLayout(base_group)
        
        self.info_label = QLabel("Cliquez sur 'Charger depuis Client' pour importer les données")
        self.info_label.setFont(QFont("Arial", 11))
        self.info_label.setStyleSheet("color: #e67e22; padding: 10px;")
        self.info_label.setAlignment(Qt.AlignCenter)
        
        base_layout.addWidget(self.info_label)
        
        self.btn_charger = QPushButton("Charger depuis l'onglet Client")
        self.btn_charger.setFont(QFont("Arial", 11))
        self.btn_charger.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 12px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.btn_charger.clicked.connect(self.charger_donnees_base)
        self.btn_charger.setCursor(Qt.PointingHandCursor)
        
        base_layout.addWidget(self.btn_charger)
        
        layout.addWidget(base_group)
        param_group = QGroupBox("ÉTAPE 2: Choisir la variable à tester")
        param_group.setFont(QFont("Arial", 12, QFont.Bold))
        param_layout = QFormLayout(param_group)
        param_layout.setVerticalSpacing(10)
        
        self.param_choice = QComboBox()
        self.param_choice.setFont(QFont("Arial", 11))
        self.param_choice.addItems([
            "Score de crédit du client",
            "Revenu mensuel du client",
            "Montant du prêt demandé",
            "Durée du prêt"
        ])
        self.param_choice.currentTextChanged.connect(self.update_param_ranges)
        
        range_frame = QFrame()
        range_layout = QHBoxLayout(range_frame)
        
        self.min_val = QDoubleSpinBox()
        self.min_val.setFont(QFont("Arial", 11))
        self.min_val.setDecimals(2)
        
        range_label = QLabel("à")
        range_label.setFont(QFont("Arial", 11))
        
        self.max_val = QDoubleSpinBox()
        self.max_val.setFont(QFont("Arial", 11))
        self.max_val.setDecimals(2)
        
        range_layout.addWidget(self.min_val)
        range_layout.addWidget(range_label)
        range_layout.addWidget(self.max_val)
        range_layout.addStretch()
        
        self.nb_points = QSpinBox()
        self.nb_points.setFont(QFont("Arial", 11))
        self.nb_points.setRange(5, 20)
        self.nb_points.setValue(8)
        
        param_layout.addRow("Variable à tester:", self.param_choice)
        param_layout.addRow("Plage de valeurs:", range_frame)
        param_layout.addRow("Nombre de simulations:", self.nb_points)
        
        range_expl = QLabel("Exemple: score de 600 à 800 = 8 simulations à 600, 628, 656, ...")
        range_expl.setFont(QFont("Arial", 9))
        range_expl.setStyleSheet("color: #7f8c8d; font-style: italic;")
        param_layout.addRow("", range_expl)
        
        layout.addWidget(param_group)
        
        action_frame = QFrame()
        action_layout = QHBoxLayout(action_frame)
        
        self.btn_analyser = QPushButton("Lancer l'analyse")
        self.btn_analyser.setFont(QFont("Arial", 12, QFont.Bold))
        self.btn_analyser.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 15px 30px;
                border-radius: 8px;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #219653;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.btn_analyser.clicked.connect(self.lancer_analyse)
        self.btn_analyser.setEnabled(False)
        self.btn_analyser.setCursor(Qt.PointingHandCursor)
        
        self.btn_exporter = QPushButton("Exporter résultats")
        self.btn_exporter.setFont(QFont("Arial", 11))
        self.btn_exporter.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                padding: 12px 25px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.btn_exporter.clicked.connect(self.exporter_resultats)
        self.btn_exporter.setEnabled(False)
        self.btn_exporter.setCursor(Qt.PointingHandCursor)
        
        action_layout.addStretch()
        action_layout.addWidget(self.btn_analyser)
        action_layout.addWidget(self.btn_exporter)
        action_layout.addStretch()
        
        layout.addWidget(action_frame)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFont(QFont("Arial", 10))
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 3px;
            }
        """)
        self.progress_bar.setVisible(False)
        
        layout.addWidget(self.progress_bar)
        
        results_group = QGroupBox("RÉSULTATS DÉTAILLÉS")
        results_group.setFont(QFont("Arial", 12, QFont.Bold))
        results_layout = QVBoxLayout(results_group)
        
        self.table_results = QTableWidget()
        self.table_results.setFont(QFont("Arial", 10))
        self.table_results.setColumnCount(6)
        self.table_results.setHorizontalHeaderLabels([
            "Valeur testée", "Taux optimal", "Mensualité", 
            "Profit", "Demande", "Risque PD"
        ])
        self.table_results.horizontalHeader().setFont(QFont("Arial", 11, QFont.Bold))
        self.table_results.horizontalHeader().setStretchLastSection(True)
        self.table_results.setAlternatingRowColors(True)
        
        self.table_results.setMinimumHeight(350)
        self.table_results.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.table_results.verticalHeader().setDefaultSectionSize(40)
        
        self.table_results.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                gridline-color: #e9ecef;
                font-size: 11px;
            }
            QTableWidget::item {
                padding: 10px;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
            }
            QHeaderView::section {
                background-color: #f1f3f4;
                padding: 12px;
                border: none;
                font-weight: bold;
            }
        """)
        
        results_layout.addWidget(self.table_results)
        layout.addWidget(results_group)
        
        graph_group = QGroupBox("VISUALISATION GRAPHIQUE")
        graph_group.setFont(QFont("Arial", 12, QFont.Bold))
        graph_layout = QVBoxLayout(graph_group)
        
        self.figure = Figure(figsize=(14, 8))
        self.canvas = FigureCanvas(self.figure)
        
        self.canvas.setMinimumHeight(650)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        graph_layout.addWidget(self.canvas)
        
        layout.addWidget(graph_group)
        
        analysis_group = QGroupBox("SYNTHÈSE ET RECOMMANDATIONS")
        analysis_group.setFont(QFont("Arial", 12, QFont.Bold))
        analysis_layout = QVBoxLayout(analysis_group)
        
        self.text_analyse = QTextEdit()
        self.text_analyse.setFont(QFont("Arial", 11))
        self.text_analyse.setReadOnly(True)
        self.text_analyse.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 10px;
                min-height: 150px;
            }
        """)
        self.text_analyse.setHtml("""
            <div style='text-align: center; color: #7f8c8d; padding: 40px;'>
                <h3>Lancez une analyse pour voir les résultats ici</h3>
                <p>Les recommandations stratégiques apparaîtront après l'analyse.</p>
            </div>
        """)
        
        analysis_layout.addWidget(self.text_analyse)
        layout.addWidget(analysis_group)
        
        scroll = QScrollArea()
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.addWidget(scroll)
        
        self.update_param_ranges()
    
    def update_param_ranges(self):
        """Met à jour les plages selon le paramètre choisi"""
        param = self.param_choice.currentText()
        
        if "Score" in param:
            self.min_val.setRange(300, 850)
            self.max_val.setRange(300, 850)
            self.min_val.setValue(600)
            self.max_val.setValue(800)
            self.min_val.setSuffix(" points")
            self.max_val.setSuffix(" points")
            
        elif "Revenu" in param:
            self.min_val.setRange(100, 20000)
            self.max_val.setRange(100, 20000)
            self.min_val.setValue(2000)
            self.max_val.setValue(8000)
            self.min_val.setSuffix(" €")
            self.max_val.setSuffix(" €")
            
        elif "Montant" in param:
            self.min_val.setRange(100, 500000)
            self.max_val.setRange(100, 500000)
            self.min_val.setValue(10000)
            self.max_val.setValue(50000)
            self.min_val.setSuffix(" €")
            self.max_val.setSuffix(" €")
            
        elif "Durée" in param:
            self.min_val.setRange(1, 30)
            self.max_val.setRange(1, 30)
            self.min_val.setValue(2)
            self.max_val.setValue(15)
            self.min_val.setSuffix(" ans")
            self.max_val.setSuffix(" ans")
    
    def charger_donnees_base(self):
        try:
            self.base_client = ClientProfile(
                score_credit=720,
                revenu_mensuel=3500,
                charges_mensuelles=400,
                apport_personnel=20.0,
                anciennete_pro=3.0,
                nb_prets_existants=1,
                historique_paiement=0.9,
                type_contrat="CDI",
                segment="particulier_moyen",
                statut_client="fidele"
            )
            
            self.base_pret = PretDemande(
                montant=20000,
                duree=5.0,
                type_pret="automobile",
                apport=4000
            )
            
            self.btn_analyser.setEnabled(True)
            self.info_label.setText("Données chargées (mode démonstration)")
            self.info_label.setStyleSheet("color: #27ae60; font-weight: bold; padding: 10px;")
            
            QMessageBox.information(self, "Prêt à analyser", 
                "Données chargées avec succès !\n\n"
                "Client de démonstration:\n"
                f"• Score: {self.base_client.score_credit}\n"
                f"• Revenu: {self.base_client.revenu_mensuel}€\n"
                f"• Type prêt: {self.base_pret.type_pret}\n"
                f"• Montant: {self.base_pret.montant:,.0f}€\n\n"
                "Vous pouvez maintenant choisir une variable à tester.")
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", 
                f"Erreur chargement données: {str(e)}")
    
    def lancer_analyse(self):
        """Lance l'analyse de sensibilité"""
        if not self.base_client or not self.base_pret:
            QMessageBox.warning(self, "Attention", 
                "Veuillez d'abord charger des données de base.")
            return
        
        self.btn_analyser.setEnabled(False)
        self.btn_charger.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        param_text = self.param_choice.currentText()
        param_map = {
            "Score de crédit du client": "score_credit",
            "Revenu mensuel du client": "revenu_mensuel",
            "Montant du prêt demandé": "montant",
            "Durée du prêt": "duree"
        }
        
        param_name = param_map.get(param_text, "score_credit")
        
        self.analysis_thread = SensitivityAnalysisThread(
            self.optimizer,
            self.base_client,
            self.base_pret,
            param_name,
            self.min_val.value(),
            self.max_val.value(),
            self.nb_points.value()
        )
        
        self.analysis_thread.progress.connect(self.progress_bar.setValue)
        self.analysis_thread.finished.connect(self.analyse_terminee)
        self.analysis_thread.error.connect(self.analyse_erreur)
        self.analysis_thread.start()
    
    def analyse_terminee(self, results):
        self.current_results = results
        
        self.btn_analyser.setEnabled(True)
        self.btn_charger.setEnabled(True)
        self.btn_exporter.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        self.afficher_tableau_agrandi(results)
        self.generer_graphique_ameliore(results)
        self.generer_analyse_simple(results)
        valid_results = len([r for r in results if r['taux_optimal'] is not None])
        QMessageBox.information(self, "Analyse terminée", 
            f"Analyse terminée !\n\n"
            f"• {valid_results} scénarios acceptés sur {len(results)}\n"
            f"• Voir les résultats dans les sections ci-dessous")
    
    def analyse_erreur(self, error_msg):
        self.btn_analyser.setEnabled(True)
        self.btn_charger.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        QMessageBox.critical(self, "Erreur", 
            f"Erreur lors de l'analyse:\n\n{error_msg}")
    
    def afficher_tableau_agrandi(self, results):
        self.table_results.setRowCount(len(results))
        
        for i, result in enumerate(results):
            self.table_results.setItem(i, 0, 
                QTableWidgetItem(f"{result['param_value']:.2f}"))
            if result['taux_optimal'] is not None:
                taux_item = QTableWidgetItem(f"{result['taux_optimal']:.3f} %")
                mens_item = QTableWidgetItem(f"{result['mensualite']:.2f} €")
                profit_item = QTableWidgetItem(f"{result['profit']:.2f} €")
                demande_item = QTableWidgetItem(f"{result['demande']:.2f}")
                pd_item = QTableWidgetItem(f"{result['PD']:.3f} %")
                profit_item.setText(f"{result['profit']:,.2f} €")
                mens_item.setText(f"{result['mensualite']:,.2f} €")
                
                self.table_results.setItem(i, 1, taux_item)
                self.table_results.setItem(i, 2, mens_item)
                self.table_results.setItem(i, 3, profit_item)
                self.table_results.setItem(i, 4, demande_item)
                self.table_results.setItem(i, 5, pd_item)
                
                taux = result['taux_optimal']
                if taux > 6:
                    taux_item.setForeground(QColor('#e74c3c'))  
                    taux_item.setFont(QFont("Arial", 10, QFont.Bold))
                elif taux < 4:
                    taux_item.setForeground(QColor('#27ae60'))  
                    taux_item.setFont(QFont("Arial", 10, QFont.Bold))
                else:
                    taux_item.setForeground(QColor('#f39c12')) 
                profit = result['profit']
                if profit > 2000:
                    profit_item.setForeground(QColor('#27ae60'))
                    profit_item.setFont(QFont("Arial", 10, QFont.Bold))
                elif profit < 0:
                    profit_item.setForeground(QColor('#e74c3c'))
                    profit_item.setFont(QFont("Arial", 10, QFont.Bold))
                else:
                    profit_item.setForeground(QColor('#f39c12'))
                    
                pd = result['PD']
                if pd > 0.05:
                    pd_item.setForeground(QColor('#e74c3c'))
                    pd_item.setFont(QFont("Arial", 10, QFont.Bold))
                elif pd < 0.01:
                    pd_item.setForeground(QColor('#27ae60'))
                    pd_item.setFont(QFont("Arial", 10, QFont.Bold))
                    
            else:
                error_item = QTableWidgetItem("REFUSÉ")
                error_item.setForeground(QColor('#e74c3c'))
                error_item.setFont(QFont("Arial", 10, QFont.Bold))
                error_item.setTextAlignment(Qt.AlignCenter)
                self.table_results.setItem(i, 1, error_item)
                
                for col in range(2, 6):
                    reason_item = QTableWidgetItem(f"({result.get('error', 'Erreur')})")
                    reason_item.setForeground(QColor('#7f8c8d'))
                    reason_item.setFont(QFont("Arial", 9))
                    self.table_results.setItem(i, col, reason_item)
        
        self.table_results.resizeColumnsToContents()
        header = self.table_results.horizontalHeader()
        for i in range(self.table_results.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.Stretch)
    
    def generer_graphique_ameliore(self, results):
        valid_results = [r for r in results if r['taux_optimal'] is not None]
        
        if len(valid_results) < 2:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'Données insuffisantes pour le graphique', 
                   ha='center', va='center', fontsize=14, color='gray')
            ax.set_title("Données insuffisantes", fontsize=12)
            self.canvas.draw()
            return
        
        param_values = [r['param_value'] for r in valid_results]
        taux_values = [r['taux_optimal'] for r in valid_results]
        profit_values = [r['profit'] for r in valid_results]
        mensualite_values = [r['mensualite'] for r in valid_results]
        pd_values = [r['PD'] * 100 for r in valid_results]  
        self.figure.clear()
        
        gs = self.figure.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
        
        ax1 = self.figure.add_subplot(gs[0, 0])
        line1 = ax1.plot(param_values, taux_values, 'b-', linewidth=3, marker='o', 
                        markersize=10, label='Taux optimal')
        ax1.set_xlabel(self.param_choice.currentText().split()[0], fontsize=11)
        ax1.set_ylabel('Taux optimal (%)', color='b', fontsize=11)
        ax1.tick_params(axis='y', labelcolor='b')
        ax1.grid(True, alpha=0.3)
        ax1.set_title("Évolution du taux optimal", fontsize=12, fontweight='bold')
        
        if len(param_values) > 1:
            z = np.polyfit(param_values, taux_values, 1)
            p = np.poly1d(z)
            ax1.plot(param_values, p(param_values), "r--", alpha=0.5, linewidth=1)
        
        ax2 = self.figure.add_subplot(gs[0, 1])
        line2 = ax2.plot(param_values, profit_values, 'g-', linewidth=3, marker='s', 
                        markersize=8, label='Profit (€)')
        ax2.set_xlabel(self.param_choice.currentText().split()[0], fontsize=11)
        ax2.set_ylabel('Profit estimé (€)', color='g', fontsize=11)
        ax2.tick_params(axis='y', labelcolor='g')
        ax2.grid(True, alpha=0.3)
        ax2.set_title("Évolution du profit", fontsize=12, fontweight='bold')
        
        ax2.get_yaxis().set_major_formatter(
            plt.FuncFormatter(lambda x, p: format(int(x), ',')))
        
        ax3 = self.figure.add_subplot(gs[1, 0])
        line3 = ax3.plot(param_values, mensualite_values, 'm-', linewidth=3, marker='^', 
                        markersize=8, label='Mensualité (€)')
        ax3.set_xlabel(self.param_choice.currentText().split()[0], fontsize=11)
        ax3.set_ylabel('Mensualité (€)', color='m', fontsize=11)
        ax3.tick_params(axis='y', labelcolor='m')
        ax3.grid(True, alpha=0.3)
        ax3.set_title("Évolution de la mensualité", fontsize=12, fontweight='bold')
        
        ax4 = self.figure.add_subplot(gs[1, 1])
        line4 = ax4.plot(param_values, pd_values, 'r-', linewidth=3, marker='d', 
                        markersize=8, label='Risque PD (%)')
        ax4.set_xlabel(self.param_choice.currentText().split()[0], fontsize=11)
        ax4.set_ylabel('Probabilité de défaut (%)', color='r', fontsize=11)
        ax4.tick_params(axis='y', labelcolor='r')
        ax4.grid(True, alpha=0.3)
        ax4.set_title("Évolution du risque", fontsize=12, fontweight='bold')
        
        ax4.axhline(y=5, color='orange', linestyle='--', alpha=0.7, linewidth=1)
        ax4.text(param_values[0], 5.2, 'Seuil risque (5%)', color='orange', fontsize=9)
        
        param_name = self.param_choice.currentText()
        self.figure.suptitle(f"Analyse de sensibilité - {param_name}", 
                           fontsize=16, fontweight='bold', y=1.02)
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def generer_analyse_simple(self, results):
        valid_results = [r for r in results if r['taux_optimal'] is not None]
        
        if not valid_results:
            html = """
            <div style='text-align: center; color: #e74c3c; padding: 20px;'>
                <h3>Aucun scénario accepté</h3>
                <p>Tous les scénarios testés ont été refusés par l'optimiseur.</p>
                <p>Essayez une plage de valeurs différentes.</p>
            </div>
            """
            self.text_analyse.setHtml(html)
            return
        taux_values = [r['taux_optimal'] for r in valid_results]
        profit_values = [r['profit'] for r in valid_results]
        param_values = [r['param_value'] for r in valid_results]
        pd_values = [r['PD'] for r in valid_results]
        
        taux_min = min(taux_values)
        taux_max = max(taux_values)
        taux_moy = np.mean(taux_values)
        
        profit_min = min(profit_values)
        profit_max = max(profit_values)
        profit_moy = np.mean(profit_values)
        
        idx_max = np.argmax(profit_values)
        param_optimal = param_values[idx_max]
        taux_optimal = taux_values[idx_max]
        profit_optimal = profit_values[idx_max]
        
        if len(param_values) > 1 and (param_values[-1] - param_values[0]) != 0:
            elasticite = (taux_values[-1] - taux_values[0]) / (param_values[-1] - param_values[0])
            elasticite_text = f"{elasticite:.4f} points par unité"
        else:
            elasticite_text = "Non calculable"
        
        param_name = self.param_choice.currentText()
        param_unit = param_name.split()[-1] if param_name.split()[-1] in ['client', 'mensuel', 'demandé', 'prêt'] else ""
        
        html = f"""
        <div style='padding: 15px;'>
            <h3 style='color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;'>SYNTHÈSE DÉTAILLÉE DE L'ANALYSE</h3>
            
            <div style='background-color: #f8f9fa; padding: 15px; border-radius: 6px; margin: 10px 0;'>
                <h4 style='color: #3498db; margin-top: 0;'>RÉSULTATS STATISTIQUES</h4>
                <table style='width: 100%; border-collapse: collapse;'>
                    <tr>
                        <td style='padding: 8px; border-bottom: 1px solid #dee2e6;'><b>Taux optimal:</b></td>
                        <td style='padding: 8px; border-bottom: 1px solid #dee2e6;'>
                            Min: <span style='color: #27ae60; font-weight: bold;'>{taux_min:.3f}%</span> | 
                            Max: <span style='color: #e74c3c; font-weight: bold;'>{taux_max:.3f}%</span> | 
                            Moy: <span style='color: #3498db; font-weight: bold;'>{taux_moy:.3f}%</span>
                        </td>
                    </tr>
                    <tr>
                        <td style='padding: 8px; border-bottom: 1px solid #dee2e6;'><b>Profit estimé:</b></td>
                        <td style='padding: 8px; border-bottom: 1px solid #dee2e6;'>
                            Min: <span style='color: #e74c3c; font-weight: bold;'>{profit_min:,.0f} €</span> | 
                            Max: <span style='color: #27ae60; font-weight: bold;'>{profit_max:,.0f} €</span> | 
                            Moy: <span style='color: #3498db; font-weight: bold;'>{profit_moy:,.0f} €</span>
                        </td>
                    </tr>
                    <tr>
                        <td style='padding: 8px;'><b>Élasticité:</b></td>
                        <td style='padding: 8px;'>{elasticite_text}</td>
                    </tr>
                </table>
            </div>
            
            <div style='background-color: #e8f5e9; padding: 15px; border-radius: 6px; margin: 10px 0;'>
                <h4 style='color: #27ae60; margin-top: 0;'>RECOMMANDATION OPTIMALE</h4>
                <p style='font-size: 14px;'>
                    Pour maximiser le profit, positionnez le <b>{param_name.split()[0]}</b> à <span style='background-color: #27ae60; color: white; padding: 3px 8px; border-radius: 4px;'><b>{param_optimal:.2f}</b></span>.
                </p>
                <p style='font-size: 14px;'>
                    À cette valeur:<br>
                    • Taux optimal: <b>{taux_optimal:.3f}%</b><br>
                    • Profit estimé: <b>{profit_optimal:,.0f} €</b><br>
                    • Scénarios acceptés: <b>{len(valid_results)}/{len(results)}</b>
                </p>
            </div>
            
            <div style='background-color: #fff3cd; padding: 15px; border-radius: 6px; margin: 10px 0;'>
                <h4 style='color: #f39c12; margin-top: 0;'>POINTS DE VIGILANCE</h4>
                <ul style='font-size: 13px;'>
                    <li>Amplitude des taux: <b>{taux_max - taux_min:.3f} points</b> (différence importante)</li>
                    <li>Nombre de scénarios refusés: <b>{len(results) - len(valid_results)}</b></li>
                    <li>Risque PD moyen: <b>{np.mean(pd_values)*100:.2f}%</b></li>
                    <li>La sensibilité est <b>{'forte' if abs(taux_max - taux_min) > 2 else 'modérée'}</b></li>
                </ul>
            </div>
            
            <div style='background-color: #e3f2fd; padding: 15px; border-radius: 6px; margin: 10px 0;'>
                <h4 style='color: #1976d2; margin-top: 0;'>INTERPRÉTATION GRAPHIQUE</h4>
                <p style='font-size: 13px;'>
                    • Le graphique en haut à gauche montre comment le taux évolue avec {param_name.lower()}<br>
                    • Le graphique en haut à droite montre l'impact sur le profit<br>
                    • Les graphiques du bas montrent les mensualités et le risque associés<br>
                    • Une ligne de tendance rouge indique la direction générale
                </p>
            </div>
        </div>
        """
        
        self.text_analyse.setHtml(html)
    
    def exporter_resultats(self):
        """Exporte les résultats d'analyse en CSV simple"""
        if not self.current_results:
            QMessageBox.warning(self, "Attention", "Aucun résultat à exporter")
            return
        
        try:
            from PyQt5.QtWidgets import QFileDialog
            from datetime import datetime
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Exporter résultats", 
                f"analyse_sensibilite_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                "Fichiers CSV (*.csv)"
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("Valeur testée;Taux optimal (%);Mensualité (€);Profit (€);Demande;PD (%);Statut\n")
                    for result in self.current_results:
                        if result['taux_optimal'] is not None:
                            ligne = f"{result['param_value']:.4f};{result['taux_optimal']:.4f};"
                            ligne += f"{result['mensualite']:.2f};{result['profit']:.2f};"
                            ligne += f"{result['demande']:.4f};{result['PD']:.6f};ACCEPTE\n"
                        else:
                            ligne = f"{result['param_value']:.4f};;;;;;REFUSE ({result.get('error', '')})\n"
                        f.write(ligne)
                
                QMessageBox.information(self, "Succès", 
                    f"Résultats exportés:\n{file_path}\n\n"
                    f"• {len(self.current_results)} scénarios exportés\n"
                    f"• {len([r for r in self.current_results if r['taux_optimal'] is not None])} scénarios acceptés\n"
                    f"• Format: CSV avec séparateur point-virgule")
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", 
                f"Erreur export: {str(e)}\n\n{traceback.format_exc()}")