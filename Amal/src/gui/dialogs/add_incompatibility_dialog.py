import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QMessageBox
)
from PyQt5.QtCore import Qt

class AddIncompatibilityDialog(QWidget):
    def __init__(self, tasks, parent_widget):
        super().__init__()
        self.parent_widget = parent_widget
        self.tasks = tasks
        
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.setWindowModality(Qt.ApplicationModal)
        
        self.setWindowTitle("Ajouter une incompatibilité")
        self.setStyleSheet("""
            QWidget {
                background-color: #0f172a;
            }
            QLabel {
                color: white;
            }
        """)
        self.setMinimumSize(450, 250)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("Sélectionner deux tâches incompatibles")
        title.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        layout.addSpacing(20)
        
        self.combo1 = QComboBox()
        self.combo2 = QComboBox()
        
        combo_style = """
            QComboBox {
                background-color: #1e293b;
                color: white;
                border: 1px solid #334155;
                padding: 8px;
                border-radius: 6px;
                min-height: 30px;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid white;
                margin-right: 10px;
            }
            QComboBox QAbstractItemView {
                background-color: #1e293b;
                color: white;
                selection-background-color: #3b82f6;
                border: 1px solid #334155;
            }
        """
        
        for combo in [self.combo1, self.combo2]:
            combo.setStyleSheet(combo_style)
            for task in tasks:
                combo.addItem(f"{task['name']} (ID: {task['id']})", task['id'])
        
        label1 = QLabel("Première tâche:")
        label1.setStyleSheet("color: #94a3b8; font-size: 14px; margin-top: 10px;")
        layout.addWidget(label1)
        layout.addWidget(self.combo1)
        
        label2 = QLabel("Deuxième tâche:")
        label2.setStyleSheet("color: #94a3b8; font-size: 14px; margin-top: 10px;")
        layout.addWidget(label2)
        layout.addWidget(self.combo2)
        
        layout.addSpacing(20)
        
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("Ajouter")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        add_btn.clicked.connect(self.add_incompatibility)
        
        cancel_btn = QPushButton("Annuler")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: white;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #475569;
            }
        """)
        cancel_btn.clicked.connect(self.close)
        
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(add_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
    def add_incompatibility(self):
        task1 = self.combo1.currentData()
        task2 = self.combo2.currentData()
        
        if task1 == task2:
            QMessageBox.warning(self, "Erreur", "Une tâche ne peut pas être incompatible avec elle-même")
            return
        
        self.parent_widget.add_incompatibility(task1, task2)
        self.close()
