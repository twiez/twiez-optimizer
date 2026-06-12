import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# ======================= DPI Ölçeklendirme VE FONT GÜNCELLEME =======================
def update_font_sizes(app):
    """
    Uygulama ekran DPI'sına göre STYLE_CONFIG içindeki font boyutlarını dinamik olarak ölçeklendirir.
    """
    screen = app.primaryScreen()
    dpi = screen.logicalDotsPerInch()  
    scale = dpi / 96  # 96 DPI referans değeri
    
    # Font boyutlarını ölçeklendir
    for key, font_tuple in STYLE_CONFIG['font'].items():
        name = font_tuple[0]
        size = font_tuple[1]
        if len(font_tuple) > 2:
            weight = font_tuple[2]
            STYLE_CONFIG['font'][key] = (name, int(size * scale), weight)
        else:
            STYLE_CONFIG['font'][key] = (name, int(size * scale))
    
    # Widget boyutlarını ölçeklendir
    STYLE_CONFIG['spacing']['default'] = int(12 * scale)
    STYLE_CONFIG['spacing']['tight'] = int(6 * scale)
    STYLE_CONFIG['spacing']['wide'] = int(18 * scale)

# ======================= KONFİGÜRASYON & STİL =======================
CURRENT_VERSION = "1.3.0"
STYLE_CONFIG = {
    'dark': {
        'bg': 'rgba(18, 18, 18, 0.97)',
        'text': '#e0e0e0',
        'primary': 'rgba(103, 58, 183, 0.9)',
        'secondary': 'rgba(40, 40, 40, 0.8)',
        'list_bg': 'rgba(30, 30, 30, 0.9)',
        'chart_line': '#7c4dff',
        'warning': '#ff4444',
        'hover': 'rgba(123, 31, 162, 0.85)',
        'card_bg': 'rgba(45, 45, 45, 0.7)',
        'gradient_start': '#1a237e',
        'gradient_end': '#4a148c'
    },
    'font': {
        'title': ('Segoe UI', 14, QFont.Bold),
        'content': ('Arial', 11),
        'detail': ('Consolas', 10),
        'chart': ('Arial', 9)
    },
    'spacing': {
        'default': 12,
        'tight': 6,
        'wide': 18
    }
}

def set_global_styles(app):
    app.setStyleSheet(f"""
        * {{
            selection-background-color: {STYLE_CONFIG['dark']['primary']};
        }}
        QMessageBox {{
            background-color: {STYLE_CONFIG['dark']['bg']};
            color: {STYLE_CONFIG['dark']['text']};
        }}
        QMessageBox QLabel {{
            color: {STYLE_CONFIG['dark']['text']} !important;
            font: {STYLE_CONFIG['font']['content'][1]}pt '{STYLE_CONFIG['font']['content'][0]}';
        }}
        QMessageBox QPushButton {{
            background: {STYLE_CONFIG['dark']['primary']};
            color: {STYLE_CONFIG['dark']['text']} !important;
            padding: 8px 24px;
            border-radius: 6px;
            min-width: 90px;
        }}
        QMessageBox QPushButton:hover {{ background: {STYLE_CONFIG['dark']['hover']}; }}
        QToolTip {{
            background: {STYLE_CONFIG['dark']['secondary']};
            color: {STYLE_CONFIG['dark']['text']};
            border: 1px solid {STYLE_CONFIG['dark']['primary']};
            border-radius: 4px;
            padding: 4px;
            font: {STYLE_CONFIG['font']['content'][1]}pt '{STYLE_CONFIG['font']['content'][0]}';
        }}
    """)

# Ortak buton stili fonksiyonu
BUTTON_STYLE = """
    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c4dff, stop:1 #bb86fc);
        color: #fff;
        border-radius: 9px;
        font: bold 14px 'Segoe UI', Arial;
        padding: 8px 28px;
        min-width: 120px;
    }
    QPushButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #a67cdb, stop:1 #bb86fc);
    }
"""

def style_all_buttons(widget):
    for btn in widget.findChildren(QPushButton):
        btn.setStyleSheet(BUTTON_STYLE)
