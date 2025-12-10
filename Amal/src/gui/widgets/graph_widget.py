from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QPen, QFont
from PyQt5.QtCore import Qt
import math

class GraphWidget(QWidget):
    """Widget de visualisation du graphe des tâches"""
    
    def __init__(self, tasks, incompatibilities, assignment=None):
        super().__init__()
        self.tasks = tasks
        self.incompatibilities = incompatibilities
        self.assignment = assignment
        self.setMinimumSize(800, 500)
        
    def set_assignment(self, assignment):
        self.assignment = assignment
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(30, 41, 59))
        
        if not self.tasks:
            return
        
        positions = self._calculate_positions()
        self._draw_incompatibilities(painter, positions)
        self._draw_tasks(painter, positions)
    
    def _calculate_positions(self):
        """Calcule les positions circulaires des tâches"""
        positions = {}
        center_x = self.width() / 2
        center_y = self.height() / 2
        radius = min(self.width(), self.height()) / 3
        
        for i, task in enumerate(self.tasks):
            angle = (2 * math.pi * i) / len(self.tasks)
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            positions[task['id']] = (x, y)
        
        return positions
    
    def _draw_incompatibilities(self, painter, positions):
        """Dessine les lignes d'incompatibilité"""
        painter.setPen(QPen(QColor(71, 85, 105), 2))
        for id1, id2 in self.incompatibilities:
            if id1 in positions and id2 in positions:
                x1, y1 = positions[id1]
                x2, y2 = positions[id2]
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))
    
    def _draw_tasks(self, painter, positions):
        """Dessine les nœuds des tâches"""
        from src.utils.constants import MACHINE_COLORS
        
        for task in self.tasks:
            x, y = positions[task['id']]
            
            if self.assignment and task['id'] in self.assignment:
                machine_id = self.assignment[task['id']]
                color = MACHINE_COLORS[machine_id % len(MACHINE_COLORS)]
            else:
                color = QColor(14, 165, 233) if task['id'] % 2 == 0 else QColor(59, 130, 246)
            
            painter.setBrush(color)
            painter.setPen(QPen(QColor(255, 255, 255), 3))
            painter.drawEllipse(int(x - 30), int(y - 30), 60, 60)
            
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont('Arial', 16, QFont.Bold))
            painter.drawText(int(x - 20), int(y + 8), str(task['id']))
