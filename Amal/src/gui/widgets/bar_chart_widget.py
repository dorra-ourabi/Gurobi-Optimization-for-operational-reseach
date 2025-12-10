from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QPixmap
from PyQt5.QtWidgets import QWidget
class BarChartWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.data = {}
        self.setMinimumSize(800, 300)
        
    def setData(self, data):
        self.data = data
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        painter.fillRect(self.rect(), QColor(15, 23, 42))
        
        if not self.data:
            return
            
        num_machines = len(self.data)
        bar_width = min(400, (self.width() - 200) // (num_machines * 2))
        spacing = 50
        total_width = num_machines * bar_width + (num_machines - 1) * spacing
        start_x = (self.width() - total_width) // 2
        max_count = max(self.data.values()) if self.data.values() else 1
        
        for i, (machine, count) in enumerate(sorted(self.data.items())):
            x = start_x + i * (bar_width + spacing)
            height = (count / max_count) * 150 + 50
            y = self.height() - height - 50
            
            painter.fillRect(int(x), int(y), bar_width, int(height), QColor(6, 182, 212))
            
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont('Arial', 14, QFont.Bold))
            painter.drawText(int(x + bar_width/2 - 10), int(y - 10), str(count))
            
            painter.setPen(QColor(148, 163, 184))
            painter.setFont(QFont('Arial', 12))
            painter.drawText(int(x + bar_width/2 - 50), self.height() - 20, f"Machine {machine}")
