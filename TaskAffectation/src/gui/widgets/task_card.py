from PyQt5.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
class TaskCard(QFrame):
    """Widget représentant une carte de tâche"""
    
    def __init__(self, task_id, task_name, parent_widget):
        super().__init__()
        self.task_id = task_id
        self.parent_widget = parent_widget
        self.init_ui(task_name)
        
    def init_ui(self, task_name):
        self.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        layout = QHBoxLayout()
        
        title_layout = QVBoxLayout()
        title = QLabel(task_name)
        title.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        task_id_label = QLabel(f"ID: {self.task_id}")
        task_id_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        
        title_layout.addWidget(title)
        title_layout.addWidget(task_id_label)
        
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
        
        layout.addLayout(title_layout)
        layout.addStretch()
        layout.addWidget(delete_btn)
        
        self.setLayout(layout)
    
    def on_delete(self):
        self.parent_widget.remove_task(self.task_id)

