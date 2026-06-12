import sys
import os
import subprocess
import multiprocessing
import io

if sys.platform == 'win32':
    # Patch subprocess.Popen to prevent console windows from flashing when using PyInstaller --windowed
    class PatchedPopen(subprocess.Popen):
        def __init__(self, *args, **kwargs):
            if 'creationflags' not in kwargs:
                kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
            super().__init__(*args, **kwargs)
    subprocess.Popen = PatchedPopen

if __name__ == '__main__':
    multiprocessing.freeze_support()
    
    # Hide stdout/stderr to prevent OSErrors in PyInstaller windowed mode when print() is called
    if getattr(sys, 'frozen', False):
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()

    import ctypes
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt
    from config import set_global_styles, update_font_sizes
    from utils.admin import is_admin
    from main_window import OptimizerWindow

    if sys.platform == 'win32':
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    
    # Font boyutlarini DPI'a gore olceklendir
    update_font_sizes(app)
    set_global_styles(app)
    
    window = OptimizerWindow()
    window.show()
    sys.exit(app.exec_())
