import os, sys, time, subprocess, shutil, psutil, GPUtil, platform, winreg, json, ctypes, requests
from zipfile import ZipFile
from io import BytesIO
from pypresence import Presence
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtChart import *
from config import *
from ui.components import InfoButton
from ui.custom_dialogs import CustomNotification, DarkMessageBox
from utils.i18n import tr

# ======================= BAŞLANGIÇ PROGRAMLARI WIDGET =======================
class StartupWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setContentsMargins(20, 15, 20, 20)
        layout = QVBoxLayout(self)
        layout.setSpacing(18)
        title = QLabel(f"📌 {tr('start_title_main', 'Başlangıç Programları')}")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"color: {STYLE_CONFIG['dark']['primary']}; font: bold 18px;")
        self.list = QListWidget()
        self.list.setStyleSheet(f"""
    QListWidget {{ 
        background: {STYLE_CONFIG['dark']['list_bg']};
        color: {STYLE_CONFIG['dark']['text']};
        border-radius: 10px;
        padding: 8px;
    }}
    QListWidget::item {{
        height: 55px;
        padding: 10px;
        border-bottom: 1px solid {STYLE_CONFIG['dark']['secondary']};
    }}
    QListWidget::item:hover {{ 
        background: {STYLE_CONFIG['dark']['hover']};
    }}
    QScrollBar:vertical {{
        background: {STYLE_CONFIG['dark']['secondary']};
        width: 12px;
        margin: 0px;
        border-radius: 6px;
    }}
    QScrollBar::handle:vertical {{
        background: {STYLE_CONFIG['dark']['primary']};
        min-height: 20px;
        border-radius: 6px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {STYLE_CONFIG['dark']['hover']};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        background: none;
        height: 0px;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: {STYLE_CONFIG['dark']['secondary']};
    }}
    QScrollBar:horizontal {{
        background: {STYLE_CONFIG['dark']['secondary']};
        height: 12px;
        margin: 0px;
        border-radius: 6px;
    }}
    QScrollBar::handle:horizontal {{
        background: {STYLE_CONFIG['dark']['primary']};
        min-width: 20px;
        border-radius: 6px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {STYLE_CONFIG['dark']['hover']};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        background: none;
        width: 0px;
    }}
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: {STYLE_CONFIG['dark']['secondary']};
    }}
""")
        for entry in self.get_startup_programs():
            item = QListWidgetItem(f"📦 {entry['name']}\n🔗 {entry['path']}")
            item.setFont(QFont(*STYLE_CONFIG['font']['content']))
            self.list.addItem(item)
        btn_disable = QPushButton(f"🚫 {tr('btn_disable_selected', 'SEÇİLİYİ DEVRE DIŞI BIRAK')}")
        btn_disable.clicked.connect(self.disable_selected)
        layout.addWidget(title)
        layout.addWidget(self.list, 1)
        layout.addWidget(btn_disable, alignment=Qt.AlignCenter)
        style_all_buttons(self)

    def get_startup_programs(self):
        programs = []
        locations = [
            (winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run'),
            (winreg.HKEY_LOCAL_MACHINE, r'Software\Microsoft\Windows\CurrentVersion\Run')
        ]
        for hive, subkey in locations:
            try:
                with winreg.OpenKey(hive, subkey) as key:
                    i = 0
                    while True:
                        try:
                            name, value, _ = winreg.EnumValue(key, i)
                            programs.append({'name': name, 'path': value})
                            i += 1
                        except OSError:
                            break
            except Exception as e:
                print(f"Kayıt defteri hatası: {e}")
        return programs

    def disable_selected(self):
        selected = self.list.currentItem()
        if selected:
            name = selected.text().split('\n')[0][2:]
            try:
                reply = DarkMessageBox(
                    tr("start_confirm_title", "Onay"),
                    tr("start_confirm_msg", "{} başlangıçtan kaldırılsın mı?").format(name),
                    buttons=[tr("start_confirm_yes", "Evet"), tr("start_confirm_no", "Hayır")]
                )
                if reply.exec_() == 0:
                    found = False
                    for hive, subkey in [
                        (winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run'),
                        (winreg.HKEY_LOCAL_MACHINE, r'Software\Microsoft\Windows\CurrentVersion\Run')
                    ]:
                        try:
                            with winreg.OpenKey(hive, subkey, 0, winreg.KEY_WRITE) as key:
                                winreg.DeleteValue(key, name)
                                found = True
                        except Exception:
                            continue
                    if found:
                        CustomNotification(tr("start_disabled_ok", "✅ {} devre dışı bırakıldı!").format(name), duration=3000, parent=self).show_notification()
                        self.list.takeItem(self.list.currentRow())
                    else:
                        CustomNotification(f"⚠️ {tr('msg_not_found', 'Program bulunamadı!')}", duration=3000, parent=self).show_notification()
            except Exception as e:
                CustomNotification(f"⛔ {tr('msg_error', 'İşlem başarısız')}:\n{str(e)}", duration=3000, parent=self).show_notification()

