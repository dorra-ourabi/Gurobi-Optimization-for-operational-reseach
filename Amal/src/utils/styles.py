from .constants import *

class Styles:
    """Centralized style definitions"""
    
    @staticmethod
    def get_main_window_style():
        return f"background-color: {COLOR_BACKGROUND};"
    
    @staticmethod
    def get_header_style():
        return "background-color: #000000; padding: 15px;"
    
    @staticmethod
    def get_tab_style():
        return """
            QTabWidget::pane {
                border: none;
                background-color: #0f172a;
            }
            QTabBar::tab {
                background-color: #334155;
                color: #94a3b8;
                padding: 12px 40px;
                border: none;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background-color: #1e293b;
                color: white;
            }
        """
    
    @staticmethod
    def get_input_style():
        return f"""
            QLineEdit {{
                background-color: {COLOR_CARD_BG};
                color: {COLOR_TEXT};
                border: 1px solid {COLOR_BORDER};
                padding: 10px;
                border-radius: 6px;
                font-size: 14px;
            }}
        """
    
    @staticmethod
    def get_button_style(color=COLOR_PRIMARY):
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
        """
    
    @staticmethod
    def get_spinbox_style():
        return f"""
            QSpinBox, QDoubleSpinBox {{
                background-color: {COLOR_CARD_BG};
                color: white;
                border: 1px solid {COLOR_BORDER};
                padding: 8px;
                border-radius: 6px;
                min-width: 100px;
            }}
            QSpinBox::up-button, QDoubleSpinBox::up-button {{
                background-color: {COLOR_BORDER};
                border-radius: 3px;
                width: 20px;
            }}
            QSpinBox::down-button, QDoubleSpinBox::down-button {{
                background-color: {COLOR_BORDER};
                border-radius: 3px;
                width: 20px;
            }}
        """
    
    @staticmethod
    def get_combo_style():
        return f"""
            QComboBox {{
                background-color: {COLOR_CARD_BG};
                color: white;
                border: 1px solid {COLOR_BORDER};
                padding: 8px;
                border-radius: 6px;
                min-height: 30px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLOR_CARD_BG};
                color: white;
                selection-background-color: {COLOR_PRIMARY};
                border: 1px solid {COLOR_BORDER};
            }}
        """
