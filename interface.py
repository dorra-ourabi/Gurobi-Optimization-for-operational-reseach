import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QFrame,
                             QScrollArea, QGridLayout, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette


class ProjectButton(QPushButton):
    """Bouton professionnel pour chaque projet"""

    def __init__(self, title, description, icon, category, parent=None):
        super().__init__(parent)
        self.project_title = title
        self.setup_ui(title, description, icon, category)

    def setup_ui(self, title, description, icon, category):
        layout = QHBoxLayout()
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(20)

        # Icône
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI", 32))
        icon_label.setFixedSize(70, 70)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("""
            background-color: #3498db;
            border-radius: 35px;
            color: white;
        """)

        # Texte
        text_layout = QVBoxLayout()
        text_layout.setSpacing(5)

        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50;")

        desc_label = QLabel(description)
        desc_label.setFont(QFont("Segoe UI", 10))
        desc_label.setStyleSheet("color: #7f8c8d;")
        desc_label.setWordWrap(True)

        category_label = QLabel(f"Catégorie: {category}")
        category_label.setFont(QFont("Segoe UI", 9, QFont.StyleItalic))
        category_label.setStyleSheet("color: #95a5a6;")

        text_layout.addWidget(title_label)
        text_layout.addWidget(desc_label)
        text_layout.addWidget(category_label)
        text_layout.addStretch()

        # Flèche
        arrow_label = QLabel("→")
        arrow_label.setFont(QFont("Segoe UI", 28))
        arrow_label.setStyleSheet("color: #3498db;")
        arrow_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(icon_label)
        layout.addLayout(text_layout, 1)
        layout.addWidget(arrow_label)

        self.setLayout(layout)
        self.setFixedHeight(120)
        self.setCursor(Qt.PointingHandCursor)

        self.setStyleSheet("""
            ProjectButton {
                background-color: white;
                border: 2px solid #ecf0f1;
                border-radius: 10px;
                text-align: left;
            }
            ProjectButton:hover {
                background-color: #f8f9fa;
                border: 2px solid #3498db;
            }
            ProjectButton:pressed {
                background-color: #e8f4f8;
            }
        """)

        # Effet d'ombre
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(3)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow)


class ProfessionalHub(QMainWindow):
    def __init__(self):
        super().__init__()
        self.projects_windows = {}
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Centre de Gestion - Projets d'Optimisation")
        self.setGeometry(100, 100, 1400, 900)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Barre supérieure
        header = self.create_header()
        main_layout.addWidget(header)

        # Contenu principal
        content = QWidget()
        content.setStyleSheet("background-color: #f5f6fa;")
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(50, 40, 50, 40)
        content_layout.setSpacing(30)

        # Titre de section
        section_title = QLabel("Projets Disponibles")
        section_title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        section_title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        content_layout.addWidget(section_title)

        # Zone scrollable
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: #ecf0f1;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #bdc3c7;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #95a5a6;
            }
        """)

        # Container des projets
        projects_widget = QWidget()
        projects_layout = QVBoxLayout()
        projects_layout.setSpacing(20)

        # Définition des 4 projets
        projects_data = [
            {
                "title": "Calcul de Taux d'Intérêt de Prêt",
                "description": "Simulation et optimisation des taux d'intérêt pour différents types de prêts bancaires",
                "icon": "💰",
                "category": "Finance",
                "key": "loan_interest"
            },
            {
                "title": "Placement Optimal d'Ambulances",
                "description": "Optimisation géographique du positionnement des ambulances pour minimiser les temps d'intervention",
                "icon": "🚑",
                "category": "Logistique Médicale",
                "key": "ambulance_placement"
            },
            {
                "title": "Planification d'Expériences en Laboratoire",
                "description": "Sélection optimale des expériences sous contraintes de réactifs et de temps de laboratoire",
                "icon": "🧪",
                "category": "Recherche & Développement",
                "key": "lab_experiments"
            },
            {
                "title": "Distribution de Gaz",
                "description": "Optimisation des circuits de distribution et d'approvisionnement en gaz",
                "icon": "⚙️",
                "category": "Énergie & Industrie",
                "key": "gas_distribution"
            }
        ]

        # Créer les boutons de projets
        for project in projects_data:
            btn = ProjectButton(
                project["title"],
                project["description"],
                project["icon"],
                project["category"]
            )
            btn.clicked.connect(lambda checked, key=project["key"]: self.open_project(key))
            projects_layout.addWidget(btn)

        projects_layout.addStretch()
        projects_widget.setLayout(projects_layout)
        scroll.setWidget(projects_widget)

        content_layout.addWidget(scroll)
        content.setLayout(content_layout)

        main_layout.addWidget(content)

        # Barre inférieure
        footer = self.create_footer()
        main_layout.addWidget(footer)

        central_widget.setLayout(main_layout)

        # Style global
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f6fa;
            }
        """)

    def create_header(self):
        """Crée la barre d'en-tête professionnelle"""
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2c3e50, stop:1 #3498db);
                border: none;
            }
        """)

        layout = QHBoxLayout()
        layout.setContentsMargins(50, 0, 50, 0)

        # Logo/Titre
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)

        title = QLabel("Centre de Gestion")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setStyleSheet("color: white; background: transparent;")

        subtitle = QLabel("Systèmes d'Optimisation & Décision")
        subtitle.setFont(QFont("Segoe UI", 11))
        subtitle.setStyleSheet("color: rgba(255, 255, 255, 0.8); background: transparent;")

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)

        # Info utilisateur
        user_label = QLabel("👤 Utilisateur")
        user_label.setFont(QFont("Segoe UI", 11))
        user_label.setStyleSheet("color: white; background: transparent;")

        layout.addLayout(title_layout)
        layout.addStretch()
        layout.addWidget(user_label)

        header.setLayout(layout)
        return header

    def create_footer(self):
        """Crée le pied de page"""
        footer = QFrame()
        footer.setFixedHeight(60)
        footer.setStyleSheet("""
            QFrame {
                background-color: white;
                border-top: 1px solid #ecf0f1;
            }
        """)

        layout = QHBoxLayout()
        layout.setContentsMargins(50, 0, 50, 0)

        info_label = QLabel("© 2025 - Centre de Gestion des Projets")
        info_label.setFont(QFont("Segoe UI", 9))
        info_label.setStyleSheet("color: #95a5a6;")

        quit_btn = QPushButton("Quitter l'application")
        quit_btn.setFixedSize(180, 35)
        quit_btn.setCursor(Qt.PointingHandCursor)
        quit_btn.setFont(QFont("Segoe UI", 10))
        quit_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        quit_btn.clicked.connect(self.close)

        layout.addWidget(info_label)
        layout.addStretch()
        layout.addWidget(quit_btn)

        footer.setLayout(layout)
        return footer

    def open_project(self, project_key):
        """Ouvre le projet sélectionné"""
        print(f"Ouverture du projet: {project_key}")

        # Dispatcher vers la bonne méthode selon le projet
        project_methods = {
            "loan_interest": self.open_loan_interest,
            "ambulance_placement": self.open_ambulance_placement,
            "lab_experiments": self.open_lab_experiments,
            "gas_distribution": self.open_gas_distribution
        }

        if project_key in project_methods:
            project_methods[project_key]()

    # ===== MÉTHODES D'OUVERTURE DES PROJETS =====

    def open_loan_interest(self):
        """Ouvre le projet Oumayma - Taux d'intérêt"""
        try:
            from Oumayma.ui import MainWindow

            if "loan" not in self.projects_windows or not self.projects_windows["loan"].isVisible():
                self.projects_windows["loan"] = MainWindow()
                self.projects_windows["loan"].show()
            else:
                self.projects_windows["loan"].raise_()
                self.projects_windows["loan"].activateWindow()
        except ImportError as e:
            print(f"Erreur d'import: {e}")
            print("→ Vérifiez que le fichier Oumayma/main.py existe et contient une classe MainWindow")
        except Exception as e:
            print(f"Erreur lors de l'ouverture: {e}")

    def open_ambulance_placement(self):
        """Ouvre le projet Alla - Placement d'ambulances"""
        try:
            import sys
            import os

            # DEBUG: Afficher le PYTHONPATH actuel
            print("PYTHONPATH avant:", sys.path)

            # Obtenir le chemin absolu du répertoire Alla
            current_dir = os.path.dirname(os.path.abspath(__file__))
            alla_dir = os.path.join(current_dir, "Alla")
            parent_dir = os.path.dirname(current_dir)  # Répertoire parent

            # Ajouter les chemins nécessaires
            if alla_dir not in sys.path:
                sys.path.insert(0, alla_dir)
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)

            print("PYTHONPATH après:", sys.path)
            print("Alla existe?", os.path.exists(alla_dir))

            from Alla.main import MainWindow

            if "ambulance" not in self.projects_windows or not self.projects_windows["ambulance"].isVisible():
                self.projects_windows["ambulance"] = MainWindow()
                self.projects_windows["ambulance"].show()
            else:
                self.projects_windows["ambulance"].raise_()
                self.projects_windows["ambulance"].activateWindow()
        except ImportError as e:
            print(f"Erreur d'import: {e}")
            print("→ Vérifiez que le fichier Alla/main.py existe et contient une classe MainWindow")
            import traceback
            traceback.print_exc()
        except Exception as e:
            print(f"Erreur lors de l'ouverture: {e}")
            import traceback
            traceback.print_exc()

    def open_lab_experiments(self):
        """Ouvre le projet Ghaida - Expériences laboratoire"""
        try:
            from Ghaida.mkp_lab_exp import MainWindow

            if "lab" not in self.projects_windows or not self.projects_windows["lab"].isVisible():
                self.projects_windows["lab"] = MainWindow()
                self.projects_windows["lab"].show()
            else:
                self.projects_windows["lab"].raise_()
                self.projects_windows["lab"].activateWindow()
        except ImportError as e:
            print(f"Erreur d'import: {e}")
            print("→ Vérifiez que le fichier Ghaida/main.py existe et contient une classe MainWindow")
        except Exception as e:
            print(f"Erreur lors de l'ouverture: {e}")

    def open_gas_distribution(self):
        """Ouvre le projet Dorra - Distribution de gaz"""
        try:
            from Dorra.IHM import MainWindow

            if "gas" not in self.projects_windows or not self.projects_windows["gas"].isVisible():
                self.projects_windows["gas"] = MainWindow()
                self.projects_windows["gas"].show()
            else:
                self.projects_windows["gas"].raise_()
                self.projects_windows["gas"].activateWindow()
        except ImportError as e:
            print(f"Erreur d'import: {e}")
            print("→ Vérifiez que le fichier Dorra/main.py existe et contient une classe MainWindow")
        except Exception as e:
            print(f"❌ Erreur lors de l'ouverture: {e}")


def main():
    app = QApplication(sys.argv)

    # Configuration de l'application
    app.setStyle("Fusion")

    # Palette moderne
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(245, 246, 250))
    palette.setColor(QPalette.WindowText, QColor(44, 62, 80))
    app.setPalette(palette)

    # Police

    # Lancement du hub
    hub = ProfessionalHub()
    hub.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()