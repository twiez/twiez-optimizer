import subprocess
import os

def create_restore_point(description="Twiez Optimizer Point"):
    """
    Creates a Windows System Restore point using PowerShell.
    Note: Requires Administrator privileges.
    """
    try:
        # Checkpoint-Computer is the PowerShell cmdlet to create restore points
        # RestorePointType 'MODIFY_SETTINGS' is suitable for registry/app changes
        ps_cmd = f"Checkpoint-Computer -Description '{description}' -RestorePointType 'MODIFY_SETTINGS'"
        
        # CREATE_NO_WINDOW flag to run invisibly
        creationflags = 0
        if os.name == 'nt':
            creationflags = subprocess.CREATE_NO_WINDOW
            
        result = subprocess.run(
            ["powershell", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            creationflags=creationflags
        )
        
        if result.returncode == 0:
            return True, "Success"
        else:
            stderr_lower = result.stderr.lower()
            if "disabled" in stderr_lower or "not enabled" in stderr_lower:
                return False, "DISABLED"
            return False, result.stderr.strip()
    except Exception as e:
        return False, str(e)
