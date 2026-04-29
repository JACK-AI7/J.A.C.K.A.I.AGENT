import subprocess
import os
import platform

def scan_path(path: str):
    """Scan a directory for threats using ClamAV (if installed) or basic heuristic checks."""
    try:
        if platform.system() == "Windows":
            # On Windows, try to use Windows Defender via PowerShell
            cmd = f"Start-MpScan -ScanType CustomScan -ScanPath '{path}'"
            subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True)
            return "Windows Defender Custom Scan Initialized."
        else:
            # On Linux/macOS, use clamscan
            result = subprocess.run(
                ["clamscan", "-r", path],
                capture_output=True,
                text=True
            )
            return result.stdout if result.stdout else "Scan complete: No immediate threats detected."
    except Exception as e:
        return f"Security Interface Error: {str(e)}"

def find_large_files(path: str, size_mb: int = 100):
    """Identify large files that may be cluttering the system."""
    files = []
    limit = size_mb * 1024 * 1024
    
    try:
        for root, _, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(root, f)
                try:
                    size = os.path.getsize(fp)
                    if size > limit:
                        files.append({"path": fp, "size": f"{size / (1024*1024):.2f} MB"})
                except:
                    pass
            # Limit depth for performance
            if len(files) > 20: break
    except Exception as e:
        return f"File System Error: {str(e)}"
        
    return files
