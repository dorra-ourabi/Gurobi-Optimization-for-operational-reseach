from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel

class StatCard(QFrame):
    """Widget représentant une carte de statistique"""
    
    def __init__(self, title, value="0", color="#3b82f6"):
        super().__init__()
        self.init_ui(title, value, color)
        
    def init_ui(self, title, value, color):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 12px;
                padding: 20px;
            }}
        """)
        layout = QVBoxLayout(self)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-size: 14px;")
        
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("color: white; font-size: 36px; font-weight: bold;")
        self.value_label.setObjectName("value")
        
        layout.addWidget(title_label)
        layout.addWidget(self.value_label)
    
    def set_value(self, value):
        self.value_label.setText(str(value))
