from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton

class IncompatibilityCard(QFrame):
    """Widget représentant une carte d'incompatibilité"""
    
    def __init__(self, task1, task2, parent_widget):
        super().__init__()
        self.task1 = task1
        self.task2 = task2
        self.parent_widget = parent_widget
        self.init_ui()
        
    def init_ui(self):
        self.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        layout = QHBoxLayout()
        
        label = QLabel(f"Tâche {self.task1}  ⟷  Tâche {self.task2}")
        label.setStyleSheet("color: #06b6d4; font-size: 14px;")
        
        delete_btn = QPushButton("🗑")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #ef4444;
                border: none;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #7f1d1d;
                border-radius: 4px;
            }
        """)
        delete_btn.clicked.connect(self.on_delete)
        
        layout.addWidget(label)
        layout.addStretch()
        layout.addWidget(delete_btn)
        
        self.setLayout(layout)
    
    def on_delete(self):
        self.parent_widget.remove_incompatibility(self.task1, self.task2)
