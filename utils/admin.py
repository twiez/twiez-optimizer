import ctypes, sys

# ======================= YÖNETİCİ KONTROLÜ =======================
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False
