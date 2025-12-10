import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, 
    QTabWidget, QMessageBox
)
from Oumayma.config.config_manager import ConfigManager
from Oumayma.models.gurobi_optimizer import GurobiOptimizer

# Imports des onglets
from Oumayma.models.gurobi_optimizerQuadratique import GurobiOptimizerQuad
from Oumayma.models.risk_calculator import ClientProfile, PretDemande
from Oumayma.ui.config_tab import ConfigurationTab
from Oumayma.ui.client_tab import ClientTab
from Oumayma.ui.analyse_tab import AnalyseTab
from Oumayma.ui.portefeuille_tab import PortefeuilleTab
from Oumayma.ui.documentation_tab import DocumentationTab
from Oumayma.utils.validators import Validators


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application"""
    
    def __init__(self):
        super().__init__()
        self.config = None
        # Remplacement de self.optimizer par les deux optimiseurs
        self.optimizer_linear = None
        self.optimizer_quad = None
        
        self.init_backend()
        self.init_ui()
        self.connect_signals()
    
    def init_backend(self):
        try:
            self.config = ConfigManager("config/default_config.json")
            self.validators = Validators(self.config)
            self.optimizer_linear = GurobiOptimizer(self.config)
            self.optimizer_quad = GurobiOptimizerQuad(self.config)
            
        except FileNotFoundError as e:
            QMessageBox.critical(
                self, "Fichier manquant",
                f"Fichier de configuration introuvable:\n{str(e)}\n\n"
                "Assurez-vous que 'config/default_config.json' existe."
            )
            sys.exit(1)
            
        except Exception as e:
            QMessageBox.critical(
                self, "Erreur d'initialisation",
                f"Erreur lors de l'initialisation:\n\n{str(e)}\n\n"
                "Vérifiez que Gurobi est correctement installé et licencié."
            )
            sys.exit(1)
    
    def init_ui(self):
        self.setWindowTitle("Système de Tarification Optimale")
        self.setGeometry(100, 100, 1400, 900)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        
        # Onglets
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        
        try:
            self.config_tab = ConfigurationTab(self.config)
            self.tabs.addTab(self.config_tab, "Configuration")
            self.client_tab = ClientTab(self.optimizer_linear, self.optimizer_quad,self.validators)
            self.tabs.addTab(self.client_tab, "Nouveau Client")
            self.analyse_tab = AnalyseTab(self.optimizer_linear, self)
            self.tabs.addTab(self.analyse_tab, "Analyse de Sensibilité")
            self.portefeuille_tab = PortefeuilleTab(self.optimizer_linear)
            self.tabs.addTab(self.portefeuille_tab, "Portefeuille")
            self.documentation_tab = DocumentationTab(self.config)
            self.tabs.addTab(self.documentation_tab, "Documentation")
            

        except Exception as e:
            QMessageBox.critical(
                self, "Erreur",
                f" Erreur lors de la création des onglets:\n\n{str(e)}"
            )
            import traceback
            traceback.print_exc()
            sys.exit(1)
        
        main_layout.addWidget(self.tabs)
        
        # Barre de statut
        self.statusBar().showMessage("Prêt - Gurobi chargé")
        
        # Appliquer les styles
        self.apply_styles()
    
    def connect_signals(self):
        """Connecte les signaux entre les onglets"""
        if hasattr(self, 'client_tab') and hasattr(self, 'portefeuille_tab'):
            # Connecter le signal dossier_accepte
            self.client_tab.dossier_accepte.connect(
                self.portefeuille_tab.ajouter_dossier
            )
    
    def apply_styles(self):
        """Applique les styles CSS globaux (inchangé)"""
        # ... (le corps de cette fonction est inchangé)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f7fa;
            }
            
            #header {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1976D2,
                    stop:1 #1565C0
                );
                border-bottom: 2px solid #0D47A1;
            }
            
            QTabWidget::pane {
                border: 1px solid #e0e0e0;
                background: white;
                border-radius: 4px;
            }
            
            QTabBar::tab {
                background: #eceff1;
                color: #546e7a;
                padding: 12px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-weight: bold;
            }
            
            QTabBar::tab:selected {
                background: white;
                color: #1976D2;
                border-bottom: 3px solid #1976D2;
            }
            
            QTabBar::tab:hover:!selected {
                background: #cfd8dc;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 12px;
                background: white;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            
            QPushButton {
                padding: 10px 15px;
                border-radius: 5px;
                background-color: #2196F3;
                color: white;
                border: none;
                font-weight: bold;
            }
            
            QPushButton:hover {
                background-color: #1976D2;
            }
            
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            
            QPushButton:disabled {
                background-color: #bdbdbd;
                color: #757575;
            }
            
            QTableWidget {
                border: 1px solid #e0e0e0;
                gridline-color: #e0e0e0;
                background: white;
                border-radius: 4px;
            }
            
            QTableWidget::item {
                padding: 5px;
            }
            
            QTableWidget::item:selected {
                background-color: #E3F2FD;
                color: #0D47A1;
            }
            
            QTableWidget QHeaderView::section {
                background-color: #f5f5f5;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #2196F3;
                font-weight: bold;
                color: #424242;
            }
            
            QStatusBar {
                background: #eceff1;
                color: #546e7a;
                font-weight: bold;
            }
        """)
    
    def closeEvent(self, event):
        """Gère la fermeture de l'application"""
        reply = QMessageBox.question(
            self, "Confirmation",
            "Êtes-vous sûr de vouloir quitter l'application?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            
            # Sauvegarder la configuration si modifiée
            if self.config:
                try:
                    self.config.save_user_config()
                except:
                    pass
            
            # 🆕 Nettoyer les deux optimiseurs
            if self.optimizer_linear:
                try:
                    self.optimizer_linear.cleanup()
                except:
                    pass
            
            if self.optimizer_quad:
                try:
                    self.optimizer_quad.cleanup()
                except:
                    pass
            
            event.accept()
        else:
            event.ignore()

    def get_current_client_data(self):
        """Récupère les données client actuelles (inchangé)"""
        # ... (le corps de cette fonction est inchangé)
        try:
            if hasattr(self, 'client_tab') and self.client_tab:
                # Essayer d'abord les dernières données analysées
                if hasattr(self.client_tab, 'get_last_analysis_data'):
                    last_data = self.client_tab.get_last_analysis_data()
                    if last_data and last_data.get('result', {}).get('status') == 'ACCEPTE':
                        return last_data
                
                # Sinon, créer depuis le formulaire
                client_tab = self.client_tab
                
                # Vérifier si le formulaire est vide
                if client_tab.score_credit.value() == 720 and client_tab.revenu.value() == 3500:
                    return None
                
                client = ClientProfile(
                    score_credit=client_tab.score_credit.value(),
                    revenu_mensuel=client_tab.revenu.value(),
                    charges_mensuelles=client_tab.charges.value(),
                    apport_personnel=(client_tab.apport.value() / client_tab.montant.value() * 100) if client_tab.montant.value() > 0 else 0,
                    anciennete_pro=client_tab.anciennete.value(),
                    nb_prets_existants=client_tab.nb_prets.value(),
                    historique_paiement=client_tab.historique.value(),
                    type_contrat=client_tab.type_contrat.currentText(),
                    segment=client_tab.segment.currentText(),
                    statut_client=client_tab.statut.currentText()
                )
                
                pret = PretDemande(
                    montant=client_tab.montant.value(),
                    duree=client_tab.duree.value(),
                    type_pret=client_tab.type_pret.currentText(),
                    apport=client_tab.apport.value()
                )
                
                return {
                    'client': client,
                    'pret': pret,
                    'is_valid': True,
                    'source': 'formulaire'
                }
                
        except Exception as e:
            print(f"Erreur récupération données client: {e}")
        
        return None