import os, sys, time, subprocess, shutil, psutil, GPUtil, platform, winreg, json, ctypes, requests
from zipfile import ZipFile
from io import BytesIO
from pypresence import Presence
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtChart import *
from config import *

# ======================= DARK MESSAGEBOX =======================
class DarkMessageBox(QDialog):
    def __init__(self, title, message, icon="info", parent=None, buttons=("Tamam",), default=0):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setModal(True)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("")
        self.result_index = default

        # Main wrapper frame to fix translucency bug
        self.main_frame = QFrame()
        self.main_frame.setStyleSheet(f"""
            QFrame#MainFrame {{
                background-color: {STYLE_CONFIG['dark']['bg']};
                border-radius: 12px;
                border: 1px solid rgba(124, 77, 255, 0.3);
            }}
        """)
        self.main_frame.setObjectName("MainFrame")

        # Üst bar
        bar = QFrame()
        bar.setObjectName("TitleBar")
        bar.setFixedHeight(40)
        bar.setStyleSheet(f"""
            QFrame#TitleBar {{
                background: {STYLE_CONFIG['dark']['secondary']};
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }}
        """)
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(14, 0, 14, 0)
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"color: {STYLE_CONFIG['dark']['primary']}; font: bold 14px; background: transparent;")
        bar_layout.addWidget(lbl_title)
        bar_layout.addStretch()
        btn_close = QPushButton("×")
        btn_close.setFixedSize(28, 28)
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {STYLE_CONFIG['dark']['text']};
                font: bold 18px;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background: {STYLE_CONFIG['dark']['hover']};
                color: white;
            }}
        """)
        btn_close.clicked.connect(self.reject)
        bar_layout.addWidget(btn_close)

        # Hareket ettirmek için mouse event'leri
        bar.mousePressEvent = self._mouse_press
        bar.mouseMoveEvent = self._mouse_move
        self._drag_pos = None

        # İçerik
        icon_label = QLabel()
        if icon == "info":
            icon_label.setText("ℹ️")
        elif icon == "warning":
            icon_label.setText("⚠️")
        elif icon == "error":
            icon_label.setText("⛔")
        elif icon == "success":
            icon_label.setText("✅")
        icon_label.setStyleSheet("font-size: 28px; margin-right: 10px; background: transparent;")
        icon_label.setFixedWidth(45)
        icon_label.setAlignment(Qt.AlignCenter)

        msg_label = QLabel(message)
        msg_label.setStyleSheet(f"color: {STYLE_CONFIG['dark']['text']}; font: 13px '{STYLE_CONFIG['font']['content'][0]}'; background: transparent;")
        msg_label.setWordWrap(True)

        content_layout = QHBoxLayout()
        content_layout.addWidget(icon_label)
        content_layout.addWidget(msg_label)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btns = []
        for i, text in enumerate(buttons):
            btn = QPushButton(text)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {STYLE_CONFIG['dark']['primary']};
                    color: white;
                    border-radius: 8px;
                    padding: 7px 28px;
                    font: bold 13px;
                }}
                QPushButton:hover {{
                    background: {STYLE_CONFIG['dark']['hover']};
                }}
            """)
            btn.clicked.connect(lambda _, idx=i: self._done(idx))
            self.btns.append(btn)
            btn_layout.addWidget(btn)
        btn_layout.addStretch()

        # Ana layout
        frame_layout = QVBoxLayout(self.main_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)
        frame_layout.addWidget(bar)
        content_wrapper = QWidget()
        content_wrapper.setStyleSheet("background: transparent;")
        cw_layout = QVBoxLayout(content_wrapper)
        cw_layout.setContentsMargins(20, 16, 20, 16)
        cw_layout.setSpacing(16)
        cw_layout.addLayout(content_layout)
        cw_layout.addLayout(btn_layout)
        frame_layout.addWidget(content_wrapper)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.main_frame)

        self.setFixedWidth(420)
        self.adjustSize()

    def _mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def _mouse_move(self, event):
        if self._drag_pos and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)

    def _done(self, idx):
        self.result_index = idx
        self.accept()

    def showEvent(self, event):
        super().showEvent(event)
        # Pencereyi ekranın ortasına konumlandır
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    @staticmethod
    def show_info(parent, title, message):
        from utils.i18n import tr
        dlg = DarkMessageBox(title, message, icon="info", parent=parent,
                             buttons=(tr("btn_ok", "Tamam"),))
        dlg.exec_()

    @staticmethod
    def show_success(parent, title, message):
        from utils.i18n import tr
        dlg = DarkMessageBox(title, message, icon="success", parent=parent,
                             buttons=(tr("btn_ok", "Tamam"),))
        dlg.exec_()

    @staticmethod
    def show_warning(parent, title, message):
        from utils.i18n import tr
        dlg = DarkMessageBox(title, message, icon="warning", parent=parent,
                             buttons=(tr("btn_ok", "Tamam"),))
        dlg.exec_()

    @staticmethod
    def show_error(parent, title, message):
        dlg = DarkMessageBox(title, message, icon="error", parent=parent)
        dlg.exec_()

    @staticmethod
    def ask_question(parent, title, message, yes_text="Evet", no_text="Hayır"):
        dlg = CustomConfirmation(title, message, yes_text, no_text, parent)
        return dlg.show_confirmation()

# ======================= CUSTOM CONFIRMATION =======================
class CustomConfirmation(QDialog):
    def __init__(self, title, message, yes_text="Evet", no_text="Hayır", parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)
        self.setAttribute(Qt.WA_StyledBackground)
        bg_color = STYLE_CONFIG['dark']['card_bg']
        # CSS tabanlı gölge efekti (frameless pencerelerde uyumlu)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_color};
                border-radius: 12px;
                padding: 15px;
                border: 1px solid rgba(124, 77, 255, 0.3);
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['primary']};
            font: bold 16px;
            background-color: {STYLE_CONFIG['dark']['card_bg']};
            padding: 8px;
            border-radius: 8px;
        """)
        layout.addWidget(title_label, alignment=Qt.AlignCenter)

        msg_label = QLabel(message)
        msg_label.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['text']};
            font: 13px '{STYLE_CONFIG['font']['content'][0]}';
            line-height: 1.4;
            background-color: {STYLE_CONFIG['dark']['card_bg']};
            padding: 10px;
            border-radius: 8px;
        """)
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignCenter)
        msg_label.setMinimumWidth(300)
        layout.addWidget(msg_label, alignment=Qt.AlignCenter)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)

        self.no_btn = QPushButton(no_text)
        self.no_btn.setCursor(Qt.PointingHandCursor)
        self.no_btn.setStyleSheet(f"""
            QPushButton {{
                background: {STYLE_CONFIG['dark']['secondary']};
                color: {STYLE_CONFIG['dark']['text']};
                border-radius: 8px;
                padding: 10px 20px;
                font: bold 13px;
            }}
            QPushButton:hover {{
                background: {STYLE_CONFIG['dark']['hover']};
            }}
        """)

        self.yes_btn = QPushButton(yes_text)
        self.yes_btn.setCursor(Qt.PointingHandCursor)
        self.yes_btn.setStyleSheet(f"""
            QPushButton {{
                background: {STYLE_CONFIG['dark']['primary']};
                color: white;
                border-radius: 8px;
                padding: 10px 20px;
                font: bold 13px;
            }}
            QPushButton:hover {{
                background: {STYLE_CONFIG['dark']['hover']};
            }}
        """)

        btn_layout.addWidget(self.no_btn)
        btn_layout.addWidget(self.yes_btn)
        layout.addLayout(btn_layout)

        self.yes_btn.clicked.connect(self.accept)
        self.no_btn.clicked.connect(self.reject)
        self.adjustSize()

    def show_confirmation(self):
        self.adjustSize()
        screen_geometry = QApplication.primaryScreen().geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)
        return self.exec_() == QDialog.Accepted

# ======================= CUSTOM NOTIFICATION =======================
class CustomNotification(QFrame):
    def __init__(self, message, duration=3000, parent=None):
        super().__init__(parent)
        bg_color = STYLE_CONFIG['dark']['warning'] if message.strip().startswith("⛔") else STYLE_CONFIG['dark']['bg']
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: 12px;
                padding: 15px;
                border: 1px solid rgba(124, 77, 255, 0.3);
            }}
        """)
        # Not: QGraphicsDropShadowEffect kaldırıldı - frameless translucent
        # pencerelerde UpdateLayeredWindowIndirect hatasına neden oluyordu.
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        label = QLabel(message)
        label.setStyleSheet(f"""
            QLabel {{
                color: {STYLE_CONFIG['dark']['text']};
                font: 13px '{STYLE_CONFIG['font']['content'][0]}';
            }}
        """)
        label.setWordWrap(True)
        layout.addWidget(label)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.close)
        self.timer.start(duration)

    def show_notification(self, x=None, y=None):
        self.adjustSize()
        if x is None or y is None:
            screen_geometry = QApplication.primaryScreen().geometry()
            x = screen_geometry.width() - self.width() - 20
            y = screen_geometry.height() - self.height() - 50
        try:
            self.move(x, y)
            self.show()
        except Exception:
            # Hata durumunda varsayılan konuma yerleştir
            self.move(20, 20)
            self.show()

    def showEvent(self, event):
        super().showEvent(event)
        try:
            # Pencereyi ekranın sağ alt köşesine konumlandır
            screen = QApplication.primaryScreen().geometry()
            x = screen.width() - self.width() - 20
            y = screen.height() - self.height() - 50
            self.move(x, y)
        except Exception:
            # Hata durumunda varsayılan konuma yerleştir
            self.move(20, 20)

