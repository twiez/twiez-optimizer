import os, sys
from PyQt5.QtWidgets import QToolButton, QWidget
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, pyqtSignal
from PyQt5.QtGui import QColor, QPainter
from config import STYLE_CONFIG
from ui.custom_dialogs import CustomNotification

class InfoButton(QToolButton):
    def __init__(self, info_text, parent=None):
        super().__init__(parent)
        self.setText("?")  
        self.setStyleSheet(f"""
            QToolButton {{
                background: transparent;
                border: none;
                padding: 4px;
                margin-left: 8px;
                color: {STYLE_CONFIG['dark']['primary']};
                font: bold 14px;
                min-width: 20px;
                min-height: 20px;
            }}
            QToolButton:hover {{
                background: {STYLE_CONFIG['dark']['hover']};
                border-radius: 12px;
                color: white;
            }}
        """)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Bilgi")
        self.clicked.connect(lambda: self.show_info(info_text))

    def show_info(self, info_text):
        CustomNotification(info_text, duration=5000, parent=self).show_notification()

class ToggleSwitch(QWidget):
    stateChanged = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(46, 24)
        self.setCursor(Qt.PointingHandCursor)
        self._is_checked = False
        
        self.bg_color = QColor("#555555")
        self.active_color = QColor(STYLE_CONFIG['dark']['primary'])
        self.circle_color = QColor("#ffffff")
        
        self._circle_pos = 3.0
        
        self.animation = QPropertyAnimation(self, b"circle_pos")
        self.animation.setDuration(250)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)

    @pyqtProperty(float)
    def circle_pos(self):
        return self._circle_pos

    @circle_pos.setter
    def circle_pos(self, pos):
        self._circle_pos = pos
        self.update()

    def isChecked(self):
        return self._is_checked

    def setChecked(self, checked):
        if self._is_checked != checked:
            self._is_checked = checked
            self.circle_pos = self.width() - 21.0 if checked else 3.0
            self.update()
            self.stateChanged.emit(self._is_checked)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setChecked(not self._is_checked)
            
            end_pos = self.width() - 21.0 if self._is_checked else 3.0
            self.animation.setStartValue(self._circle_pos)
            self.animation.setEndValue(end_pos)
            self.animation.start()
            
            super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background
        painter.setPen(Qt.NoPen)
        if self._is_checked:
            painter.setBrush(self.active_color)
        else:
            painter.setBrush(self.bg_color)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 12, 12)
        
        # Draw circle
        painter.setBrush(self.circle_color)
        painter.drawEllipse(int(self._circle_pos), 3, 18, 18)
        painter.end()
