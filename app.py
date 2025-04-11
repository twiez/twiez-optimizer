# C0ded by twiez >:
# github/twiez
# buymeacoffee.com/twiez

import sys
import os
import shutil
import psutil
import GPUtil
import platform
import winreg
import subprocess
import json
import ctypes
from PyQt5.QtGui import QIcon, QFont, QColor, QPainter, QCursor, QLinearGradient
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QPushButton,
    QMessageBox, QHBoxLayout, QStackedWidget, QFrame, QCheckBox,
    QListWidget, QListWidgetItem, QGraphicsDropShadowEffect, QGridLayout, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QPoint, QRectF
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis

# ======================= YÖNETİCİ KONTROLÜ =======================
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, None, 1)
    sys.exit()

# ======================= KONFİGÜRASYON & STİL =======================
CURRENT_VERSION = "1.0.0"
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

# ======================= SİSTEM İŞLEM SINIFLARI =======================
class CleanerThread(QThread):
    update_status = pyqtSignal(str)
    complete_signal = pyqtSignal(int)

    def __init__(self, directories):
        super().__init__()
        self.directories = directories

    def run(self):
        total_deleted = 0
        try:
            for path, name in self.directories:
                deleted = self.clean_directory(path, name)
                total_deleted += deleted
                self.update_status.emit(f"{name}: {deleted} dosya silindi")
        except Exception as e:
            self.update_status.emit(f"⛔ Hata: {str(e)}")
        finally:
            self.complete_signal.emit(total_deleted)

    def clean_directory(self, path, name):
        deleted = 0
        try:
            if os.path.exists(path):
                for root, dirs, files in os.walk(path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            os.remove(file_path)
                            deleted += 1
                        except Exception as e:
                            self.update_status.emit(f"⚠️ Silinemedi: {file_path}")
                    for dir in dirs:
                        dir_path = os.path.join(root, dir)
                        try:
                            shutil.rmtree(dir_path)
                            deleted += 1
                        except:
                            pass
                self.update_status.emit(f"✅ {name} temizlendi")
            return deleted
        except Exception as e:
            raise Exception(f"{name} hatası: {str(e)}")

# ======================= ANA PENCERE VE WIDGET'LAR =======================
class OptimizerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.old_pos = None
        self.init_ui()
        self.setWindowTitle(f'Twiez Optimizer v{CURRENT_VERSION}')
        self.setWindowIcon(QIcon('fav.ico'))

    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(1100, 750)

        self.main_container = QWidget()
        self.main_container.setStyleSheet(f"""
            background-color: {STYLE_CONFIG['dark']['bg']};
            border-radius: 15px;
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(35)
        shadow.setColor(QColor(0, 0, 0, 120))
        shadow.setOffset(0, 4)
        self.main_container.setGraphicsEffect(shadow)
        
        main_layout = QVBoxLayout(self.main_container)
        main_layout.addWidget(self.create_title_bar())
        main_layout.addWidget(self.create_content_area())
        main_layout.setContentsMargins(12, 12, 12, 12)
        
        self.setCentralWidget(self.main_container)

    def create_title_bar(self):
        title_bar = QFrame()
        title_bar.setFixedHeight(60)
        title_bar.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {STYLE_CONFIG['dark']['gradient_start']}, 
                stop:1 {STYLE_CONFIG['dark']['gradient_end']});
            border-radius: 15px 15px 0 0;
        """)
        
        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(20, 0, 20, 0)
        title_label = QLabel('Twiez Optimizer')
        title_label.setFont(QFont(*STYLE_CONFIG['font']['title']))
        title_label.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['text']};
            background: transparent;
            padding: 5px;
        """)
        
        btn_style = f"""
            QPushButton {{
                background: transparent;
                color: {STYLE_CONFIG['dark']['text']};
                font: bold 20px;
                min-width: 34px;
                min-height: 34px;
                border-radius: 10px;
            }}
            QPushButton:hover {{ 
                background: rgba(255,255,255,0.15);
                border: 1px solid rgba(255,255,255,0.2);
            }}
        """
        
        btn_min = QPushButton("–")
        btn_min.setStyleSheet(btn_style)
        btn_min.clicked.connect(self.showMinimized)
        
        btn_close = QPushButton("×")
        btn_close.setStyleSheet(btn_style)
        btn_close.clicked.connect(self.close)
        
        layout.addWidget(title_label)
        layout.addStretch()
        layout.addWidget(btn_min)
        layout.addWidget(btn_close)
        
        return title_bar

    def create_content_area(self):
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.addWidget(self.create_menu_panel(), 1)
        content_layout.addWidget(self.create_stacked_widget(), 4)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(0, 10, 0, 10)
        return content_widget

    def create_menu_panel(self):
        menu_frame = QFrame()
        menu_layout = QVBoxLayout(menu_frame)
        menu_layout.setSpacing(12)
        menu_layout.setContentsMargins(0, 0, 0, 0)
        
        buttons = [
            ('🏠 Windows', self.show_windows),
            ('🚀 Başlangıç', self.show_startup),
            ('🧹 Temizlik', self.show_cleaner),
            ('📊 Performans', self.show_performance),
            ('💻 Donanım', self.show_hardware),
            ('🫶 Bilgi', self.show_info)
        ]
        
        for text, callback in buttons:
            btn = QPushButton(text)
            btn.setFont(QFont(*STYLE_CONFIG['font']['title']))
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {STYLE_CONFIG['dark']['secondary']};
                    color: {STYLE_CONFIG['dark']['text']};
                    border-radius: 10px;
                    padding: 14px;
                    text-align: left;
                }}
                QPushButton:hover {{
                    background: {STYLE_CONFIG['dark']['hover']};
                    border: 1px solid {STYLE_CONFIG['dark']['primary']};
                }}
            """)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setFixedHeight(55)
            btn.clicked.connect(callback)
            menu_layout.addWidget(btn)
        
        menu_layout.addStretch()
        return menu_frame

    def create_stacked_widget(self):
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(WindowsSettingsWidget())
        self.stacked_widget.addWidget(StartupWidget())
        self.stacked_widget.addWidget(CleanerWidget())
        self.stacked_widget.addWidget(PerformanceWidget())
        self.stacked_widget.addWidget(HardwareWidget())
        self.stacked_widget.addWidget(InfoWidget())
        return self.stacked_widget

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = event.globalPos() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

    def show_windows(self): self.stacked_widget.setCurrentIndex(0)
    def show_startup(self): self.stacked_widget.setCurrentIndex(1)
    def show_cleaner(self): self.stacked_widget.setCurrentIndex(2)
    def show_performance(self): self.stacked_widget.setCurrentIndex(3)
    def show_hardware(self): self.stacked_widget.setCurrentIndex(4)
    def show_info(self): self.stacked_widget.setCurrentIndex(5)

# ======================= WINDOWS AYARLARI WIDGET =======================
class WindowsSettingsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.checkbox_references = {}
        self.init_ui()
        self.setup_triggers()

    def init_ui(self):
        self.setContentsMargins(20, 15, 20, 15)
        layout = QVBoxLayout(self)
        layout.setSpacing(18)
        
        self.setup_title(layout)
        self.setup_checkboxes(layout)
        self.setup_apply_button(layout)

    def setup_title(self, layout):
        title = QLabel("⚙️ Windows Optimizasyon Ayarları")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['primary']};
            font: bold 20px;
            padding: 12px 0;
        """)
        layout.addWidget(title)

    def setup_checkboxes(self, layout):
        grid = QGridLayout()
        grid.setVerticalSpacing(15)
        grid.setHorizontalSpacing(35)
        grid.setContentsMargins(15, 0, 15, 0)
        
        left_items = self.left_column_items()
        right_items = self.right_column_items()
        
        max_rows = max(len(left_items), len(right_items))
        for row in range(max_rows):
            if row < len(left_items):
                text, name = left_items[row]
                self.add_checkbox(grid, text, name, row, 0)
            if row < len(right_items):
                text, name = right_items[row]
                self.add_checkbox(grid, text, name, row, 1)

        layout.addLayout(grid)

    def left_column_items(self):
        return [
            ("Yüksek Performans Modu", "chk_performance"),
            ("Cortana'yı Devre Dışı Bırak", "chk_cortana"),
            ("Yazdırma Hizmetini Kapat", "chk_print"),
            ("Ağ Kısıtlamalarını Kaldır", "chk_throttling"),
            ("GameDVR'ı Devre Dışı Bırak", "chk_gamedvr"),
            ("Oyun Modunu Etkinleştir", "chk_gamemode")
        ]

    def right_column_items(self):
        return [
            ("HPET'i Devre Dışı Bırak", "chk_hpet"),
            ("Windows Ink'i Kapat", "chk_ink"),
            ("Windows Hello'yu Devre Dışı Bırak", "chk_hello"),
            ("Yapışkan Tuşları Kapat", "chk_stickkeys"),
            ("Disk Temizleme", "chk_clean"),
            ("OneDrive'ı Devre Dışı Bırak", "chk_onedrive"),
            ("Superfetch'i Kapat", "chk_superfetch"),
            ("Uzun Yol Desteğini Etkinleştir", "chk_paths")
        ]

    def add_checkbox(self, grid, text, name, row, col):
        checkbox = QCheckBox(text)
        self.checkbox_references[name] = checkbox
        checkbox.setObjectName(name)
        checkbox.setMinimumHeight(36)
        checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {STYLE_CONFIG['dark']['text']};
                font: 14px;
                spacing: 15px;
                padding: 6px 0;
            }}
            QCheckBox::indicator {{
                width: 24px;
                height: 24px;
                subcontrol-position: center left;
            }}
        """)
        grid.addWidget(checkbox, row, col, alignment=Qt.AlignLeft)

    def setup_apply_button(self, layout):
        btn_apply = QPushButton("🚀 AYARLARI UYGULA")
        btn_apply.setMinimumHeight(50)
        btn_apply.setStyleSheet(f"""
            QPushButton {{
                background: {STYLE_CONFIG['dark']['primary']};
                color: {STYLE_CONFIG['dark']['text']};
                border-radius: 10px;
                font: bold 15px;
                min-width: 260px;
                padding: 0 30px;
            }}
            QPushButton:hover {{
                background: {STYLE_CONFIG['dark']['hover']};
                padding: 2px 32px;
            }}
        """)
        layout.addWidget(btn_apply, alignment=Qt.AlignCenter)

    def setup_triggers(self):
        self.findChild(QPushButton).clicked.connect(self.apply_settings)

    def apply_settings(self):
        try:
            operations = [
                ("chk_performance", self.enable_high_performance),
                ("chk_cortana", self.disable_cortana),
                ("chk_print", self.disable_print_service),
                ("chk_throttling", self.disable_network_throttling),
                ("chk_gamedvr", self.disable_gamedvr),
                ("chk_gamemode", self.enable_game_mode),
                ("chk_hpet", self.disable_hpet),
                ("chk_ink", self.disable_windows_ink),
                ("chk_hello", self.disable_windows_hello),
                ("chk_stickkeys", self.disable_sticky_keys),
                ("chk_clean", self.clean_disk),
                ("chk_onedrive", self.disable_onedrive),
                ("chk_superfetch", self.disable_superfetch),
                ("chk_paths", self.enable_long_paths)
            ]

            for name, operation in operations:
                if self.checkbox_references[name].isChecked():
                    operation()

            QMessageBox.information(self, "✅ Başarılı", "Ayarlar başarıyla uygulandı!")
            
        except Exception as e:
            QMessageBox.critical(self, "⛔ Hata", f"İşlem başarısız:\n{str(e)}")

    #region System Operations
    def enable_high_performance(self):
        self.run_powershell('powercfg /setactive "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"')  # High Performance GUID

    def disable_cortana(self):
        self.set_registry(r"HKLM\SOFTWARE\Policies\Microsoft\Windows\Windows Search", "AllowCortana", 0)

    def disable_print_service(self):
        self.manage_service("Spooler", "stop", "disabled")

    def disable_network_throttling(self):
        self.set_registry(r"HKLM\SOFTWARE\Policies\Microsoft\Windows\Psched", "NonBestEffortLimit", 0)

    def disable_gamedvr(self):
        self.set_registry(r"HKCU\System\GameConfigStore", "GameDVR_Enabled", 0)
        self.set_registry(r"HKLM\SOFTWARE\Policies\Microsoft\Windows\GameDVR", "AllowGameDVR", 0)

    def enable_game_mode(self):
        self.set_registry(r"HKCU\Software\Microsoft\GameBar", "AllowAutoGameMode", 1)

    def disable_hpet(self):
        self.run_command('bcdedit /deletevalue useplatformclock')

    def disable_windows_ink(self):
        self.set_registry(r"HKCU\Software\Microsoft\Windows\CurrentVersion\Pen", "PenEducation", 0)

    def disable_windows_hello(self):
        self.set_registry(r"HKLM\SOFTWARE\Policies\Microsoft\Biometrics", "Enabled", 0)

    def disable_sticky_keys(self):
        self.set_registry(r"HKCU\Control Panel\Accessibility\StickyKeys", "Flags", "506")

    def clean_disk(self):
        self.run_command('cleanmgr /sagerun:1')

    def disable_onedrive(self):
        self.run_command('taskkill /f /im OneDrive.exe')
        self.run_command(r'rd /s /q "%localappdata%\Microsoft\OneDrive"')   
        self.run_command(r'rd /s /q "%programdata%\Microsoft OneDrive"')

    def disable_superfetch(self):
        self.manage_service("SysMain", "stop", "disabled")

    def enable_long_paths(self):
        self.set_registry(r"HKLM\SYSTEM\CurrentControlSet\Control\FileSystem", "LongPathsEnabled", 1)
    #endregion

    #region Helper Methods
    def set_registry(self, key_path, value_name, value):
        hive_map = {"HKLM": winreg.HKEY_LOCAL_MACHINE, "HKCU": winreg.HKEY_CURRENT_USER}
        hive_name, subkey = key_path.split("\\", 1)
        try:
            with winreg.CreateKey(hive_map[hive_name], subkey) as key:
                reg_type = winreg.REG_DWORD if isinstance(value, int) else winreg.REG_SZ
                winreg.SetValueEx(key, value_name, 0, reg_type, value)
        except Exception as e:
            raise Exception(f"Kayıt defteri hatası: {str(e)}")

    def manage_service(self, service_name, action, startup_type=None):
        try:
            if startup_type:
                subprocess.run(f'sc config "{service_name}" start= {startup_type}', check=True, shell=True)
            subprocess.run(f'sc {action} "{service_name}"', check=True, shell=True)
        except subprocess.CalledProcessError as e:
            raise Exception(f"Hizmet yönetimi hatası: {str(e)}")

    def run_command(self, command):
        try:
            subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            raise Exception(f"Komut hatası: {e.stderr.decode()}")

    def run_powershell(self, script):
        try:
            subprocess.run(["powershell", "-Command", script], check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            raise Exception(f"PowerShell hatası: {e.stderr.decode()}")
    #endregion

# ======================= BAŞLANGIÇ PROGRAMLARI WIDGET =======================
class StartupWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setContentsMargins(20, 15, 20, 20)
        layout = QVBoxLayout(self)
        layout.setSpacing(18)
        
        title = QLabel("📌 Başlangıç Programları")
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
        """)
        
        for entry in self.get_startup_programs():
            item = QListWidgetItem(f"📦 {entry['name']}\n🔗 {entry['path']}")
            item.setFont(QFont(*STYLE_CONFIG['font']['content']))
            self.list.addItem(item)
        
        btn_disable = QPushButton("🚫 SEÇİLİYİ DEVRE DIŞI BIRAK")
        btn_disable.setStyleSheet(f"""
            QPushButton {{
                background: {STYLE_CONFIG['dark']['primary']};
                color: {STYLE_CONFIG['dark']['text']};
                border-radius: 10px;
                font: bold 14px;
                min-width: 240px;
                padding: 14px;
            }}
            QPushButton:hover {{ background: {STYLE_CONFIG['dark']['hover']}; }}
        """)
        btn_disable.clicked.connect(self.disable_selected)
        
        layout.addWidget(title)
        layout.addWidget(self.list, 1)
        layout.addWidget(btn_disable, alignment=Qt.AlignCenter)

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
                reply = QMessageBox.question(
                    self, "Onay",
                    f"{name} başlangıçtan kaldırılsın mı?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    found = False
                    for hive, subkey in [
                        (winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run'),
                        (winreg.HKEY_LOCAL_MACHINE, r'Software\Microsoft\Windows\CurrentVersion\Run')
                    ]:
                        try:
                            with winreg.OpenKey(hive, subkey, 0, winreg.KEY_WRITE) as key:
                                winreg.DeleteValue(key, name)
                                found = True
                        except:
                            continue
                    if found:
                        QMessageBox.information(self, "✅ Başarılı", f"{name} devre dışı bırakıldı!")
                        self.list.takeItem(self.list.currentRow())
                    else:
                        QMessageBox.warning(self, "⚠️ Uyarı", "Program bulunamadı!")
            except Exception as e:
                QMessageBox.critical(self, "⛔ Hata", f"İşlem başarısız:\n{str(e)}")

# ======================= TEMİZLİK WIDGET =======================
class CleanerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setContentsMargins(20, 15, 20, 20)
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        title = QLabel("🧹 Sistem Temizleme")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"color: {STYLE_CONFIG['dark']['primary']}; font: bold 18px;")
        
        
        options_layout = QGridLayout()
        options_layout.setSpacing(20)

       
        self.chk_temp = self.create_option_checkbox("🗑️ Geçici Dosyalar")
        self.lbl_temp = self.create_description_label("Geçici dosyalar silinir, genellikle önemsiz dosyalardır.")
        self.chk_recycle_bin = self.create_option_checkbox("🗑️ Geri Dönüşüm Kutusu")
        self.lbl_recycle_bin = self.create_description_label("Geri dönüşüm kutusundaki dosyalar tamamen silinir.")
        
        
        self.chk_prefetch = self.create_option_checkbox("📂 Prefetch Dosyaları")
        self.lbl_prefetch = self.create_description_label("Prefetch dosyaları bilgisayarın hızlanması için silinebilir boş dosyalardır.")
        self.chk_browsers = self.create_option_checkbox("🌐 Tarayıcı Önbelleği")
        self.lbl_browsers = self.create_description_label("Tarayıcı önbelleği silinir, tarayıcınızın hızını artırır.")

       
        options_layout.addWidget(self.chk_temp, 0, 0)
        options_layout.addWidget(self.lbl_temp, 1, 0)
        options_layout.addWidget(self.chk_recycle_bin, 2, 0)
        options_layout.addWidget(self.lbl_recycle_bin, 3, 0)

        
        options_layout.addWidget(self.chk_prefetch, 0, 1)
        options_layout.addWidget(self.lbl_prefetch, 1, 1)
        options_layout.addWidget(self.chk_browsers, 2, 1)
        options_layout.addWidget(self.lbl_browsers, 3, 1)

        layout.addWidget(title)
        layout.addLayout(options_layout)

        self.lbl_status = QLabel()
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['text']};
            font: italic 12px;
            min-height: 40px;
        """)

        btn_clean = QPushButton("✨ TEMİZLİĞİ BAŞLAT")
        btn_clean.setStyleSheet(f"""
            QPushButton {{
                background: {STYLE_CONFIG['dark']['primary']};
                color: {STYLE_CONFIG['dark']['text']};
                border-radius: 10px;
                font: bold 15px;
                min-width: 220px;
                padding: 14px 35px;
            }}
            QPushButton:hover {{ background: {STYLE_CONFIG['dark']['hover']}; }}
        """)
        btn_clean.clicked.connect(self.start_clean)
        
        layout.addWidget(self.lbl_status)
        layout.addWidget(btn_clean, alignment=Qt.AlignCenter)

    def create_option_checkbox(self, text):
        chk = QCheckBox(text)
        chk.setStyleSheet(f"""
            QCheckBox {{
                color: {STYLE_CONFIG['dark']['text']};
                font: 14px;
                spacing: 20px;
                padding: 12px 0;
            }}
            QCheckBox::indicator {{ width: 26px; height: 26px; }}
        """)
        return chk

    def create_description_label(self, text):
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignLeft)
        lbl.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['text']};
            font-size: 12px;
            padding: 5px;
        """)
        return lbl

    def start_clean(self):
        directories = []
        if self.chk_temp.isChecked():
            directories.append((os.getenv('TEMP'), "Geçici Dosyalar"))
            directories.append((os.getenv('TMP'), "Geçici Dosyalar"))
        if self.chk_prefetch.isChecked():
            directories.append((os.path.join(os.getenv('WINDIR'), 'Prefetch'), "Prefetch"))
        if self.chk_browsers.isChecked():
            browsers = [
                ('Chrome', os.path.expanduser('~\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Cache')),
                ('Edge', os.path.expanduser('~\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\Cache')),
                ('Firefox', os.path.expanduser('~\\AppData\\Local\\Mozilla\\Firefox\\Profiles'))
            ]
            for name, path in browsers:
                if os.path.exists(path):
                    directories.append((path, f"{name} Önbelleği"))
        if self.chk_recycle_bin.isChecked():
           
            self.clean_recycle_bin()

        if directories:
            self.thread = CleanerThread(directories)
            self.thread.update_status.connect(self.lbl_status.setText)
            self.thread.complete_signal.connect(lambda total: (
                self.lbl_status.setText(f"✅ Toplam {total} dosya silindi!"),
                QMessageBox.information(self, "✅ Başarılı", "Temizlik tamamlandı!")
            ))
            self.thread.start()
        else:
            QMessageBox.warning(self, "⚠️ Uyarı", "Lütfen en az bir seçenek işaretleyin!")

    def clean_recycle_bin(self):
    
        try:
            import winshell
            winshell.recycle_bin().empty(confirm=False, show_progress=False, sound=False)
            self.lbl_status.setText("✅ Geri Dönüşüm Kutusu başarıyla temizlendi!")
        except Exception as e:
            self.lbl_status.setText(f"❌ Geri Dönüşüm Kutusu temizlenemedi: {e}")



# ======================= PERFORMANS WIDGET =======================
class PerformanceWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 20)
        
        self.lbl_info = QLabel()
        self.lbl_info.setStyleSheet(f"color: {STYLE_CONFIG['dark']['text']}; font: 14px;")
        
        self.chart = QChart()
        self.chart.setBackgroundBrush(QColor(STYLE_CONFIG['dark']['list_bg']))
        self.chart.setTitle("📈 Sistem Kaynak Kullanımı")
        self.chart.setTitleBrush(QColor(STYLE_CONFIG['dark']['text']))
        self.chart.legend().setVisible(False)
        
        self.series_cpu = QLineSeries()
        self.series_cpu.setColor(QColor(STYLE_CONFIG['dark']['chart_line']))
        self.series_cpu.setName("CPU")
        
        self.series_ram = QLineSeries()
        self.series_ram.setColor(QColor("#4CAF50"))
        self.series_ram.setName("RAM")
        
        axisX = QValueAxis()
        axisX.setLabelFormat("%d")
        axisX.setTitleText("Zaman (s)")
        axisX.setTitleBrush(QColor(STYLE_CONFIG['dark']['text']))
        axisX.setLabelsBrush(QColor(STYLE_CONFIG['dark']['text']))
        
        axisY = QValueAxis()
        axisY.setRange(0, 100)
        axisY.setTitleText("Kullanım (%)")
        axisY.setTitleBrush(QColor(STYLE_CONFIG['dark']['text']))
        axisY.setLabelsBrush(QColor(STYLE_CONFIG['dark']['text']))
        
        self.chart.addSeries(self.series_cpu)
        self.chart.addSeries(self.series_ram)
        self.chart.addAxis(axisX, Qt.AlignBottom)
        self.chart.addAxis(axisY, Qt.AlignLeft)
        
        self.series_cpu.attachAxis(axisX)
        self.series_cpu.attachAxis(axisY)
        self.series_ram.attachAxis(axisX)
        self.series_ram.attachAxis(axisY)
        
        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000)
        self.x = 0
        
        layout.addWidget(self.lbl_info)
        layout.addWidget(self.chart_view)

    def update_stats(self):
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        gpu = GPUtil.getGPUs()[0].load*100 if GPUtil.getGPUs() else 0
        
        self.lbl_info.setText(f"📊 Gerçek Zamanlı Kullanım:\nCPU: {cpu}% | RAM: {mem}% | GPU: {gpu:.1f}%")
        
        self.series_cpu.append(self.x, cpu)
        self.series_ram.append(self.x, mem)
        
        if self.series_cpu.count() > 60:
            self.series_cpu.removePoints(0, self.series_cpu.count()-60)
            self.series_ram.removePoints(0, self.series_ram.count()-60)
        
        self.chart.axisX().setRange(max(0, self.x-60), self.x)
        self.x += 1

# ======================= DONANIM WİDGET =======================

from GPUtil import GPU
import subprocess



class HardwareWidget(QWidget):
    
    def __init__(self):
        super().__init__()
        self.show_network_ip = False  
        self.init_ui()
        self.update_hardware_info()
        QTimer.singleShot(1000, self.update_hardware_info)  

    def get_gpus_with_no_console():
        try:
           
            output = subprocess.check_output(
                "nvidia-smi --query-gpu=name,memory.total,utilization.gpu --format=csv,noheader,nounits",
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW  
            ).decode("utf-8").strip()
        
            
            gpus = []
            for line in output.split("\n"):
                name, mem_total, util = line.split(", ")
                gpu = GPU()
                gpu.name = name
                gpu.memoryTotal = int(mem_total)
                gpu.load = float(util) / 100
                gpus.append(gpu)
            return gpus
        except:
            return []

    def init_ui(self):
        self.labels = {}  
        layout = QGridLayout(self)
        layout.setVerticalSpacing(15)
        layout.setHorizontalSpacing(20)
        layout.setContentsMargins(20, 15, 20, 20)
        
        title = QLabel("🔧 Detaylı Donanım Bilgileri")
        title.setStyleSheet(f"color: {STYLE_CONFIG['dark']['primary']}; font: bold 18px;")
        layout.addWidget(title, 0, 0, 1, 3)
        
        self.cards = {
            'cpu': self.create_card("💻 İşlemci", self.get_cpu_info(), 'cpu'),
            'gpu': self.create_card("🎮 GPU", self.get_gpu_info(), 'gpu'),
            'ram': self.create_card("🧠 Bellek", self.get_ram_info(), 'ram'),
            'disk': self.create_card("💾 Depolama", self.get_disk_info(), 'disk'),
            'network': self.create_network_card("🌐 Ağ", self.get_network_info(), 'network'),
            'score': self.create_score_card()
        }
        
        layout.addWidget(self.cards['cpu'], 1, 0)
        layout.addWidget(self.cards['gpu'], 1, 1)
        layout.addWidget(self.cards['ram'], 2, 0)
        layout.addWidget(self.cards['disk'], 2, 1)
        layout.addWidget(self.cards['network'], 3, 0)
        layout.addWidget(self.cards['score'], 1, 2, 3, 1)

    def create_card(self, title, content, key):
        frame = QFrame()
        frame.setStyleSheet(f"""
            background: {STYLE_CONFIG['dark']['card_bg']};
            border-radius: 12px;
            padding: 10px;
        """)

        layout = QVBoxLayout(frame)
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['primary']};
            font: bold 14px;
            margin-bottom: 10px;
        """)

        lbl_content = QLabel(content)
        lbl_content.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['text']};
            font: 13px '{STYLE_CONFIG['font']['content'][0]}';
            line-height: 1.4;
        """)
        lbl_content.setWordWrap(True)

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_content)
        
        self.labels[key] = lbl_content 

        return frame

    def create_network_card(self, title, content, key):
        """
        Ağ kartı; başlık kısmı toggle buton ile aynı satırda yer alacak şekilde düzenlendi.
        Alt kısımda ise ağ bilgilerini gösteren label bulunuyor.
        """
        frame = QFrame()
        frame.setStyleSheet(f"""
            background: {STYLE_CONFIG['dark']['card_bg']};
            border-radius: 12px;
            padding: 10px;
        """)

        main_layout = QVBoxLayout(frame)
        
     
        header_layout = QHBoxLayout()
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['primary']};
            font: bold 14px;
        """)
        header_layout.addWidget(lbl_title)

    
        toggle_btn = QPushButton("👁️")
        toggle_btn.setFixedSize(30, 30)
        toggle_btn.setStyleSheet("background: transparent; border: none;")
        toggle_btn.setCursor(Qt.PointingHandCursor)
        toggle_btn.clicked.connect(self.toggle_network_ip)
        header_layout.addWidget(toggle_btn, alignment=Qt.AlignRight)
        header_layout.setStretch(0, 1) 

        main_layout.addLayout(header_layout)
        
       
        lbl_content = QLabel(content)
        lbl_content.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['text']};
            font: 13px '{STYLE_CONFIG['font']['content'][0]}';
            line-height: 1.2;
            border-radius: 10px;
            padding: 4px;
        """)
        lbl_content.setWordWrap(True)
        main_layout.addWidget(lbl_content)
        
        self.labels[key] = lbl_content 
        
        return frame

    def create_score_card(self):
        frame = QFrame()
        frame.setStyleSheet(f"""
            background: {STYLE_CONFIG['dark']['card_bg']};
            border-radius: 12px;
            padding: 18px;
        """)
        
        layout = QVBoxLayout(frame)
        lbl_title = QLabel("🏆 Sistem Puanları")
        lbl_title.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['primary']};
            font: bold 14px;
            margin-bottom: 12px;
        """)
        
        self.lbl_scores = QLabel()
        self.lbl_scores.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['text']};
            font: 13px '{STYLE_CONFIG['font']['content'][0]}';
            line-height: 1.6;
        """)
        self.lbl_scores.setWordWrap(True)
        
        layout.addWidget(lbl_title)
        layout.addWidget(self.lbl_scores)
        return frame

    def toggle_network_ip(self):
        """
        Toggle butonuna basıldığında IP gösterme bayrağını tersine çevirip,
        ağ kartındaki label'ı güncelliyoruz.
        """
        self.show_network_ip = not self.show_network_ip
        self.labels['network'].setText(self.get_network_info())

    def get_winsat_scores(self):
        try:
            result = subprocess.run(
                ['powershell', '-Command', 'Get-CimInstance Win32_WinSat | ConvertTo-Json'],
                capture_output=True, text=True
            )
            data = json.loads(result.stdout)
            return (
                f"• CPU: {data.get('CPUScore', 'N/A')}\n"
                f"• 3D Grafik: {data.get('D3DScore', 'N/A')}\n"
                f"• Depolama: {data.get('DiskScore', 'N/A')}\n"
                f"• 2D Grafik: {data.get('GraphicsScore', 'N/A')}\n"
                f"• Bellek: {data.get('MemoryScore', 'N/A')}"
            )
        except:
            return "Sistem puanları alınamadı"

    def get_cpu_info(self):
        try:
            freq = psutil.cpu_freq()
            return (
                f"Model: {platform.processor()}\n"
                f"Çekirdek: {os.cpu_count()}\n"
                f"Frekans: {freq.current/1000:.2f} GHz\n"
                f"Maks. Frekans: {freq.max/1000:.2f} GHz"
            )
        except:
            return "Bilgi alınamadı"

    def get_gpu_info(self):
        try:
            gpus = self.get_gpus_with_no_console() 
            if not gpus:
                return "GPU bulunamadı"
            return "\n\n".join([
                f"{gpu.name}\nVRAM: {gpu.memoryTotal}MB\nKullanım: {gpu.load*100:.1f}%"
                for gpu in gpus
            ])
        except:
            return "GPU bilgisi yok"

    def get_ram_info(self):
        mem = psutil.virtual_memory()
        return (
            f"Toplam: {mem.total//(1024**3)} GB\n"
            f"Kullanım: {mem.percent}%\n"
            f"Kullanılan: {mem.used//(1024**3)} GB"
        )

    def get_disk_info(self):
        parts = psutil.disk_partitions()
        info = []
        for part in parts:
            usage = psutil.disk_usage(part.mountpoint)
            info.append(f"{part.device}\n• Boyut: {usage.total//(1024**3)}GB\n• Boş: {usage.free//(1024**3)}GB")
        return "\n\n".join(info) if info else "Disk bilgisi yok"

    def get_network_info(self):
        """
        Tüm ağ arayüzlerindeki IPv4 adreslerini (yerel ağ bağlantıları dahil) getirir.
        IP, show_network_ip bayrağı True ise gerçek adres, False ise gizlenmiş olarak döndürülür.
        """
        addrs = psutil.net_if_addrs()
        info = []
        for name, addresses in addrs.items():
            for addr in addresses:
                if addr.family == 2: 
                    ip_str = addr.address if self.show_network_ip else "••••••"
                    info.append(f"{name}\n• IP: {ip_str}")
        return "\n\n".join(info) if info else "Ağ bilgisi yok"

    def update_hardware_info(self):
        self.labels['cpu'].setText(self.get_cpu_info())
        self.labels['gpu'].setText(self.get_gpu_info())
        self.labels['ram'].setText(self.get_ram_info())
        self.labels['disk'].setText(self.get_disk_info())
        self.labels['network'].setText(self.get_network_info())
        self.lbl_scores.setText(self.get_winsat_scores())


# ======================= BİLGİ WIDGET =======================
class InfoWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)
        
        title = QLabel("Twiez Optimizer Hakkında")
        title.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['primary']};
            font: bold 22px;
            padding-bottom: 10px;
        """)
        title.setAlignment(Qt.AlignCenter)
        
        info_frame = QFrame()
        info_frame.setStyleSheet(f"""
            background: {STYLE_CONFIG['dark']['card_bg']};
            border-radius: 12px;
            padding: 20px;
        """)
        
        info_layout = QVBoxLayout(info_frame)
        
        description = QLabel(
            "Twiez Optimizer, Windows sistemler için geliştirilmiş kapsamlı bir optimizasyon aracıdır. "
            "Bu uygulama ile sisteminizi hızlandırabilir, gereksiz dosyaları temizleyebilir ve "
            "donanım bilgilerinizi görüntüleyebilirsiniz.\n\n"
            "Uygulama Python ve PyQt5 kullanılarak geliştirilmiştir. "
            "Açık kaynak kodlu olup GitHub üzerinden erişilebilir."
        )
        description.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['text']};
            font: 13px '{STYLE_CONFIG['font']['content'][0]}';
            line-height: 1.6;
        """)
        description.setWordWrap(True)
        
        github_label = QLabel("GitHub Reposu:")
        github_label.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['primary']};
            font: bold 14px;
            margin-top: 15px;
        """)
        
        github_link = QLabel("<a href='https://github.com/twiez/twiez-optimizer'>Github Link</a>")
        github_link.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['text']};
            font: 13px '{STYLE_CONFIG['font']['content'][0]}';
        """)
        github_link.setOpenExternalLinks(True)
        
      
        version_label = QLabel(f"Versiyon: {CURRENT_VERSION}")
        version_label.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['text']};
            font: italic 12px;
            margin-top: 10px;
        """)
        version_label.setAlignment(Qt.AlignCenter) 
        
        info_layout.addWidget(description)
        info_layout.addWidget(github_label)
        info_layout.addWidget(github_link)
        info_layout.addWidget(version_label)
        
        layout.addWidget(title)
        layout.addWidget(info_frame)
        
     
        footer = QLabel("© 2025 Twiez Optimizer - Tüm hakları saklıdır")
        footer.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['text']};
            font: italic 11px;
            padding-top: 15px;
        """)
        footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer)


# ======================= UYGULAMA BAŞLATMA =======================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    set_global_styles(app)
    window = OptimizerWindow()
    window.show()
    sys.exit(app.exec_())