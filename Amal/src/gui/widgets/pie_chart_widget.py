from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QPixmap
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
import math
class PieChartWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.data = {}
        self.setMinimumSize(400, 400)
        
    def setData(self, data):
        self.data = data
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(15, 23, 42))
        if not self.data:
            return
        total = sum(self.data.values())
        if total == 0:
            return
        center_x = self.width() / 2
        center_y = self.height() / 2
        radius = 120
        start_angle = 0
        colors = [
            QColor(6, 182, 212), QColor(59, 130, 246), QColor(168, 85, 247),
            QColor(236, 72, 153), QColor(34, 197, 94), QColor(234, 179, 8)]
        for i, (machine, count) in enumerate(sorted(self.data.items())):
            span_angle = int((count / total) * 360 * 16)
            painter.setBrush(colors[i % len(colors)])
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.drawPie(int(center_x - radius), int(center_y - radius), 
                          int(radius * 2), int(radius * 2), 
                          start_angle, span_angle)
            mid_angle = start_angle + span_angle / 2
            label_angle = mid_angle / 16 * math.pi / 180
            label_x = center_x + (radius + 50) * math.cos(label_angle)
            label_y = center_y - (radius + 50) * math.sin(label_angle)
            painter.setPen(colors[i % len(colors)])
            painter.setFont(QFont('Arial', 12, QFont.Bold))
            painter.drawText(int(label_x - 60), int(label_y), f"M{machine}: {count}")
            start_angle += span_angle
