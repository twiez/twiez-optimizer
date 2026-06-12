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

# ======================= DONANIM WIDGET =======================
from GPUtil import GPU
class HardwareWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.show_network_ip = False  
        self.init_ui()
        self.update_hardware_info()
        QTimer.singleShot(1000, self.update_hardware_info)  

    @staticmethod
    def get_gpus_with_no_console():
        try:
            output = subprocess.check_output(
                "nvidia-smi --query-gpu=name,memory.total,utilization.gpu --format=csv,noheader,nounits",
                shell=True,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)  
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
        except Exception:
            return []

    def init_ui(self):
        self.labels = {}  
        layout = QGridLayout(self)
        layout.setVerticalSpacing(15)
        layout.setHorizontalSpacing(20)
        layout.setContentsMargins(20, 15, 20, 20)
        title = QLabel(f"🔧 {tr('hw_title', 'Detaylı Donanım Bilgileri')}")
        title.setStyleSheet(f"color: {STYLE_CONFIG['dark']['primary']}; font: bold 18px;")
        layout.addWidget(title, 0, 0, 1, 3)
        self.cards = {
            'cpu': self.create_card(f"💻 {tr('hw_cpu', 'İşlemci')}", self.get_cpu_info(), 'cpu'),
            'gpu': self.create_card(f"🎮 {tr('hw_gpu', 'GPU')}", self.get_gpu_info(), 'gpu'),
            'ram': self.create_card(f"🧠 {tr('hw_mem', 'Bellek')}", self.get_ram_info(), 'ram'),
            'disk': self.create_card(f"💾 {tr('hw_disk', 'Depolama')}", self.get_disk_info(), 'disk'),
            'network': self.create_network_card(f"🌐 {tr('hw_network', 'Ağ')}", self.get_network_info(), 'network'),
            'score': self.create_score_card()
        }
        layout.addWidget(self.cards['cpu'], 1, 0)
        layout.addWidget(self.cards['gpu'], 1, 1)
        layout.addWidget(self.cards['ram'], 2, 0)
        layout.addWidget(self.cards['disk'], 2, 1)
        layout.addWidget(self.cards['network'], 3, 0)
        layout.addWidget(self.cards['score'], 1, 2, 3, 1)
        style_all_buttons(self)

    def create_card(self, title, content, key):
        frame = QFrame()
        frame.setStyleSheet(f"""
            background: {STYLE_CONFIG['dark']['card_bg']};
            border-radius: 12px;
            padding: 10px;
        """)
        layout = QVBoxLayout(frame)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)
        frame.setLayout(layout)
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['primary']};
            font: bold 14px;
            margin-bottom: 10px;
        """)
        layout.addWidget(lbl_title)
        lbl_content = QLabel(content)
        lbl_content.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['text']};
            font: 13px '{STYLE_CONFIG['font']['content'][0]}';
            line-height: 1.2;
            border-radius: 10px;
            padding: 4px;
        """)
        lbl_content.setWordWrap(True)
        layout.addWidget(lbl_content)
        self.labels[key] = lbl_content 
        return frame

    def create_network_card(self, title, content, key):
        frame = QFrame()
        frame.setStyleSheet(f"""
            background: {STYLE_CONFIG['dark']['card_bg']};
            border-radius: 12px;
            padding: 10px;
        """)
        main_layout = QVBoxLayout(frame)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(0, 0, 0, 0)
        frame.setLayout(main_layout)
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
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)
        frame.setLayout(layout)
        lbl_title = QLabel(f"🏆 {tr('hw_scores', 'Sistem Puanları')}")
        lbl_title.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['primary']};
            font: bold 14px;
            margin-bottom: 12px;
        """)
        layout.addWidget(lbl_title)
        self.lbl_scores = QLabel()
        self.lbl_scores.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['text']};
            font: 13px '{STYLE_CONFIG['font']['content'][0]}';
            line-height: 1.6;
        """)
        self.lbl_scores.setWordWrap(True)
        layout.addWidget(self.lbl_scores)
        return frame

    def toggle_network_ip(self):
        self.show_network_ip = not self.show_network_ip
        self.labels['network'].setText(self.get_network_info())

    def get_winsat_scores(self):
        try:
            result = subprocess.run(
                ['powershell', '-Command', 'Get-CimInstance Win32_WinSat | ConvertTo-Json'],
                capture_output=True, text=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)
            )
            data = json.loads(result.stdout)
            return (
                f"• {tr('hw_cpu', 'CPU')}: {data.get('CPUScore', 'N/A')}\n"
                f"• {tr('hw_3d', '3D Grafik')}: {data.get('D3DScore', 'N/A')}\n"
                f"• {tr('hw_disk', 'Depolama')}: {data.get('DiskScore', 'N/A')}\n"
                f"• {tr('hw_2d', '2D Grafik')}: {data.get('GraphicsScore', 'N/A')}\n"
                f"• {tr('hw_mem', 'Bellek')}: {data.get('MemoryScore', 'N/A')}"
            )
        except Exception:
            return tr("hw_score_err", "Sistem puanları alınamadı")

    def get_cpu_info(self):
        try:
            freq = psutil.cpu_freq()
            return (
                f"{tr('hw_model', 'Model')}: {platform.processor()}\n"
                f"{tr('hw_cores', 'Çekirdek')}: {os.cpu_count()}\n"
                f"{tr('hw_freq', 'Frekans')}: {freq.current/1000:.2f} GHz\n"
                f"{tr('hw_max_freq', 'Maks. Frekans')}: {freq.max/1000:.2f} GHz"
            )
        except Exception:
            return tr("hw_no_info", "Bilgi alınamadı")

    def get_gpu_info(self):
        try:
            gpus = GPUtil.getGPUs()
            if not gpus:
                return tr("hw_no_gpu", "GPU bulunamadı")
            return "\n\n".join([
                f"{gpu.name}\nVRAM: {gpu.memoryTotal} MB\n{tr('hw_usage', 'Kullanım')}: {gpu.load * 100:.1f}%"
                for gpu in gpus
            ])
        except Exception as e:
            return f"{tr('hw_gpu_err', 'GPU bilgisi alınamadı:')} {str(e)}"
            
    def get_ram_info(self):
        mem = psutil.virtual_memory()
        return (
            f"{tr('hw_total', 'Toplam')}: {mem.total//(1024**3)} GB\n"
            f"{tr('hw_usage', 'Kullanım')}: {mem.percent}%\n"
            f"{tr('hw_used', 'Kullanılan')}: {mem.used//(1024**3)} GB"
        )

    def get_disk_info(self):
        parts = psutil.disk_partitions()
        info = []
        for part in parts:
            usage = psutil.disk_usage(part.mountpoint)
            info.append(f"{part.device}\n• {tr('hw_size', 'Boyut')}: {usage.total//(1024**3)}GB\n• {tr('hw_free', 'Boş')}: {usage.free//(1024**3)}GB")
        return "\n\n".join(info) if info else tr("hw_no_disk", "Disk bilgisi yok")

    def get_network_info(self):
        addrs = psutil.net_if_addrs()
        info = []
        for name, addresses in addrs.items():
            for addr in addresses:
                if addr.family == 2:
                    ip_str = addr.address if self.show_network_ip else "••••••"
                    info.append(f"{name}\n• IP: {ip_str}")
        return "\n\n".join(info) if info else tr("hw_no_net", "Ağ bilgisi yok")

    def update_hardware_info(self):
        self.labels['cpu'].setText(self.get_cpu_info())
        self.labels['gpu'].setText(self.get_gpu_info())
        self.labels['ram'].setText(self.get_ram_info())
        self.labels['disk'].setText(self.get_disk_info())
        self.labels['network'].setText(self.get_network_info())
        self.lbl_scores.setText(self.get_winsat_scores())

