import os, sys, time, subprocess, shutil, psutil, GPUtil, platform, winreg, json, ctypes, requests
from zipfile import ZipFile
from io import BytesIO
from pypresence import Presence
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtChart import *
from config import *
from utils.i18n import tr

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
        self.chart.setTitle(f"📈 {tr('perf_title', 'Sistem Kaynak Kullanımı')}")
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
        axisX.setTitleText(tr("perf_time", "Zaman (s)"))
        axisX.setTitleBrush(QColor(STYLE_CONFIG['dark']['text']))
        axisX.setLabelsBrush(QColor(STYLE_CONFIG['dark']['text']))
        axisY = QValueAxis()
        axisY.setRange(0, 100)
        axisY.setTitleText(tr("perf_usage", "Kullanım (%)"))
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
        style_all_buttons(self)

    def update_stats(self):
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        try:
            gpus = GPUtil.getGPUs()
            gpu = gpus[0].load * 100 if gpus else 0
        except Exception:
            gpu = 0
        self.lbl_info.setText(tr("perf_realtime", "📊 Gerçek Zamanlı Kullanım:\nCPU: {}% | RAM: {}% | GPU: {:.1f}%").format(cpu, mem, gpu))
        self.series_cpu.append(self.x, cpu)
        self.series_ram.append(self.x, mem)
        if self.series_cpu.count() > 60:
            self.series_cpu.removePoints(0, self.series_cpu.count()-60)
            self.series_ram.removePoints(0, self.series_ram.count()-60)
        axisX = self.chart.axes(Qt.Horizontal)[0]
        axisX.setRange(max(0, self.x-60), self.x)
        self.x += 1
