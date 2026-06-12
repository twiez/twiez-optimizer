import os, sys, time, subprocess, shutil, psutil, GPUtil, platform, winreg, json, ctypes, requests
from zipfile import ZipFile
from io import BytesIO
from pypresence import Presence
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtChart import *
from config import *
from threads.rpc_thread import RPCThread
from utils.update_manager import UpdateChecker, UpdateManager
from utils.i18n import tr
from utils.settings_manager import get_setting, set_setting
from widgets.home import HomeWidget
from widgets.windows_settings import WindowsSettingsWidget
from widgets.optimization import OptimizationWidget
from widgets.startup import StartupWidget
from widgets.cleaner import CleanerWidget
from widgets.performance import PerformanceWidget
from widgets.hardware import HardwareWidget
from widgets.info import InfoWidget
from widgets.security import SecurityWidget
from widgets.debloater import DebloaterWidget
from widgets.network import NetworkWidget
from ui.custom_dialogs import DarkMessageBox

# ======================= ANA PENCERE VE WIDGET'LAR =======================
class OptimizerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.old_pos = None
        self.rpc_thread = RPCThread()
        self.init_ui()
        self.setWindowTitle("Twiez Optimizer")
        
        # PyInstaller _MEIPASS path resolution for the icon
        base_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_dir, 'fav.ico')
        self.setWindowIcon(QIcon(icon_path))
        
        self.rpc_thread.start()
        self.update_checker = UpdateChecker(CURRENT_VERSION, "https://github.com/twiez/twiez-optimizer")
        self.update_checker.update_available.connect(self.prompt_update)
        self.update_checker.start()

    def animate_minimize(self):
        fade_out = QPropertyAnimation(self, b"windowOpacity")
        fade_out.setDuration(200)
        fade_out.setStartValue(1)
        fade_out.setEndValue(0)
        fade_out.setEasingCurve(QEasingCurve.InOutQuad)
        def on_fade_out_finished():
            self.showMinimized()
            self.setWindowOpacity(1)
        fade_out.finished.connect(on_fade_out_finished)
        fade_out.start()
        self._fade_out_anim = fade_out
    
    def animate_close(self):
        fade_out = QPropertyAnimation(self, b"windowOpacity")
        fade_out.setDuration(200)
        fade_out.setStartValue(1)
        fade_out.setEndValue(0)
        fade_out.setEasingCurve(QEasingCurve.InOutQuad)
        fade_out.finished.connect(self.close)
        fade_out.start()
        self._fade_out_anim = fade_out

    def animate_maximize(self):
        if not self.isMaximized():
            
            fade_out = QPropertyAnimation(self, b"windowOpacity")
            fade_out.setDuration(150)
            fade_out.setStartValue(1)
            fade_out.setEndValue(0)
            fade_out.setEasingCurve(QEasingCurve.InOutQuad)
            
            def on_fade_out_finished():
               
                screen = QApplication.primaryScreen().geometry()
                self.move(screen.center() - self.rect().center())
              
                self.showMaximized()
               
                fade_in = QPropertyAnimation(self, b"windowOpacity")
                fade_in.setDuration(150)
                fade_in.setStartValue(0)
                fade_in.setEndValue(1)
                fade_in.setEasingCurve(QEasingCurve.InOutQuad)
                fade_in.start()
                self._fade_in_anim = fade_in
            
            fade_out.finished.connect(on_fade_out_finished)
            fade_out.start()
            self._fade_out_anim = fade_out
        else:
           
            fade_out = QPropertyAnimation(self, b"windowOpacity")
            fade_out.setDuration(150)
            fade_out.setStartValue(1)
            fade_out.setEndValue(0)
            fade_out.setEasingCurve(QEasingCurve.InOutQuad)
            
            def on_fade_out_finished():
                
                screen = QApplication.primaryScreen().geometry()
                self.showNormal()
                self.move(screen.center() - self.rect().center())
                
                fade_in = QPropertyAnimation(self, b"windowOpacity")
                fade_in.setDuration(150)
                fade_in.setStartValue(0)
                fade_in.setEndValue(1)
                fade_in.setEasingCurve(QEasingCurve.InOutQuad)
                fade_in.start()
                self._fade_in_anim = fade_in
            
            fade_out.finished.connect(on_fade_out_finished)
            fade_out.start()
            self._fade_out_anim = fade_out

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
        title_label = QLabel("Twiez Optimizer")
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
        btn_min.clicked.connect(self.animate_minimize)
        
        btn_max = QPushButton("▢")
        btn_max.setStyleSheet(btn_style)
        btn_max.clicked.connect(self.animate_maximize)
        
        btn_close = QPushButton("×")
        btn_close.setStyleSheet(btn_style)
        btn_close.clicked.connect(self.animate_close)
        
        self.btn_lang = QPushButton("🌐")
        self.btn_lang.setToolTip(tr("btn_lang_tooltip", "Dili Değiştir / Change Language"))
        self.btn_lang.setStyleSheet(btn_style)
        self.btn_lang.clicked.connect(self.toggle_language)
        
        layout.addWidget(title_label)
        layout.addStretch()
        layout.addWidget(self.btn_lang)
        layout.addWidget(btn_min)
        layout.addWidget(btn_max)
        layout.addWidget(btn_close)
        title_bar.mousePressEvent = self.title_bar_mouse_press
        title_bar.mouseMoveEvent = self.title_bar_mouse_move
        return title_bar

    def title_bar_mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()
            
            if self.isMaximized():
                self.showNormal()
                
                new_pos = event.globalPos() - QPoint(self.width() // 2, 0)
                self.move(new_pos)
                self.old_pos = event.globalPos()

    def title_bar_mouse_move(self, event):
        if self.old_pos is not None and event.buttons() == Qt.LeftButton:
            delta = event.globalPos() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def create_menu_panel(self):
        menu_frame = QFrame()
        menu_layout = QVBoxLayout(menu_frame)
        menu_layout.setSpacing(12)
        menu_layout.setContentsMargins(0, 0, 0, 0)
        buttons = [
            (f"🏠 {tr('menu_home', 'Ev')}", self.show_home),
            (f"🪟 {tr('menu_windows', 'Windows')}", self.show_windows),
            (f"⚡ {tr('menu_optimization', 'Optimizasyon')}", self.show_optimization),
            (f"🚀 {tr('menu_startup', 'Başlangıç')}", self.show_startup),
            (f"🧹 {tr('menu_cleaner', 'Temizlik')}", self.show_cleaner),
            (f"🧽 {tr('menu_debloater', 'Debloater')}", self.show_debloater),
            (f"🌐 {tr('menu_network', 'Network')}", self.show_network),
            (f"📊 {tr('menu_performance', 'Performans')}", self.show_performance),
            (f"💻 {tr('menu_hardware', 'Donanım')}", self.show_hardware),
            (f"🔒 {tr('menu_security', 'Güvenlik')}", self.show_security),
            (f"💓 {tr('menu_info', 'Bilgi')}", self.show_info)
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
        self.stacked_widget.addWidget(HomeWidget())               # Index 0: Ev
        self.stacked_widget.addWidget(WindowsSettingsWidget())    # Index 1: Windows
        self.stacked_widget.addWidget(OptimizationWidget())       # Index 2: Optimizasyon
        self.stacked_widget.addWidget(StartupWidget())            # Index 3: Başlangıç
        self.stacked_widget.addWidget(CleanerWidget())            # Index 4: Temizlik
        self.stacked_widget.addWidget(PerformanceWidget())        # Index 5: Performans
        self.stacked_widget.addWidget(HardwareWidget())           # Index 6: Donanım
        self.stacked_widget.addWidget(InfoWidget())               # Index 7: Bilgi
        self.stacked_widget.addWidget(SecurityWidget())           # Index 8: Güvenlik
        self.stacked_widget.addWidget(DebloaterWidget())          # Index 9: Debloater
        self.stacked_widget.addWidget(NetworkWidget())            # Index 10: Network
        return self.stacked_widget

    def show_home(self):
        self.stacked_widget.setCurrentIndex(0)

    def show_windows(self):
        self.stacked_widget.setCurrentIndex(1)

    def show_optimization(self):
        self.stacked_widget.setCurrentIndex(2)

    def show_startup(self):
        self.stacked_widget.setCurrentIndex(3)

    def show_cleaner(self):
        self.stacked_widget.setCurrentIndex(4)

    def show_performance(self):
        self.stacked_widget.setCurrentIndex(5)
        
    def toggle_language(self):
        current_lang = get_setting("language", "en")
        new_lang = "tr" if current_lang == "en" else "en"
        set_setting("language", new_lang)
        
        from ui.custom_dialogs import DarkMessageBox
        DarkMessageBox.show_info(
            self,
            tr("msg_restart_required_title", "Yeniden Başlatma Gerekli"),
            tr("msg_restart_required", "Dil değiştirildi. Uygulamanın yeniden başlatılması gerekiyor.")
        )

    def show_hardware(self):
        self.stacked_widget.setCurrentIndex(6)

    def show_security(self):
        self.stacked_widget.setCurrentIndex(8)

    def show_debloater(self):
        self.stacked_widget.setCurrentIndex(9)

    def show_network(self):
        self.stacked_widget.setCurrentIndex(10)

    def show_info(self):
        self.stacked_widget.setCurrentIndex(7)

    def create_content_area(self):
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.addWidget(self.create_menu_panel(), 1)
        content_layout.addWidget(self.create_stacked_widget(), 4)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(0, 10, 0, 10)
        return content_widget

    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Ekran boyutuna göre pencere boyutunu ayarla
        screen = QApplication.primaryScreen()
        scale = screen.logicalDotsPerInch() / 96
        screen_geometry = screen.geometry()
        
    
        base_width = 1100
        base_height = 750
        max_width = int(screen_geometry.width() * 0.8)  # Ekran genişliğinin %80'i
        max_height = int(screen_geometry.height() * 0.8)  # Ekran yüksekliğinin %80'i
        
        width = min(int(base_width * scale), max_width)
        height = min(int(base_height * scale), max_height)
        
        self.setFixedSize(width, height)
        
        self.main_container = QWidget()
        self.main_container.setStyleSheet(f"""
            background-color: {STYLE_CONFIG['dark']['bg']};
            border-radius: {int(15 * scale)}px;
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(int(35 * scale))
        shadow.setColor(QColor(0, 0, 0, 120))
        shadow.setOffset(0, int(4 * scale))
        self.main_container.setGraphicsEffect(shadow)
        
        main_layout = QVBoxLayout(self.main_container)
        main_layout.addWidget(self.create_title_bar())
        main_layout.addWidget(self.create_content_area())
        main_layout.setContentsMargins(
            int(12 * scale), 
            int(12 * scale), 
            int(12 * scale), 
            int(12 * scale)
        )
        self.setCentralWidget(self.main_container)

    def prompt_update(self, latest_version, download_url):
        reply = DarkMessageBox.ask_question(
            self, "Yeni Sürüm Bulundu",
            f"Yeni bir sürüm bulundu: v{latest_version}\nGüncellemek ister misiniz?",
            yes_text="Evet", no_text="Hayır"
        )
        if reply:
            update_manager = UpdateManager(self, download_url)
            update_manager.download_and_install_update()

    def closeEvent(self, event):
        self.rpc_thread.stop()
        event.accept()

