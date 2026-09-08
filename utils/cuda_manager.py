import os
import sys
import ctypes
import shutil
import logging
import zipfile
import threading
import urllib.request
import subprocess
from typing import Dict, Any, List, Optional, Callable

logger = logging.getLogger("NOVA.CUDAManager")

# User AppData directory for persistent external CUDA runtime storage
APPDATA_DIR = os.path.join(os.getenv("APPDATA", os.path.expanduser("~")), "NOVA")
APPDATA_CUDA_DIR = os.path.join(APPDATA_DIR, "cuda")
APPDATA_CUDA_BIN = os.path.join(APPDATA_CUDA_DIR, "bin")

# Official / Community lightweight CUDA 12 runtime zip mirror for faster-whisper (cuBLAS + cuDNN)
# The user can download in-app or click the link to download manually in browser.
CUDA_RUNTIME_DOWNLOAD_URL = "https://github.com/Purfview/whisper-standalone-win/releases/download/libs/CUDA12_cuBLAS_cuDNN_x64.zip"
CUDA_RUNTIME_FALLBACK_URL = "https://github.com/PRN-6/NOVA/releases/download/v1.1.0/cuda12_runtime.zip"

_download_state: Dict[str, Any] = {
    "is_downloading": False,
    "progress": 0,
    "downloaded_mb": 0.0,
    "total_mb": 0.0,
    "status": "idle",
    "error": None
}
_download_lock = threading.Lock()


def get_gpu_info() -> Dict[str, Any]:
    """Detects if an NVIDIA GPU is present on Windows."""
    info = {
        "has_nvidia_gpu": False,
        "gpu_name": "None",
        "total_memory": "0 MB",
        "free_memory": "0 MB",
        "driver_version": "None"
    }

    # Method 1: Check driver DLL
    try:
        ctypes.WinDLL("nvcuda.dll")
        info["has_nvidia_gpu"] = True
    except OSError:
        pass

    # Method 2: Detailed query via nvidia-smi
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.free,driver_version", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=3
        )
        if r.returncode == 0 and r.stdout.strip():
            parts = [p.strip() for p in r.stdout.strip().split(",")]
            info["has_nvidia_gpu"] = True
            info["gpu_name"] = parts[0] if len(parts) > 0 else "NVIDIA GPU"
            info["total_memory"] = parts[1] if len(parts) > 1 else "?"
            info["free_memory"] = parts[2] if len(parts) > 2 else "?"
            info["driver_version"] = parts[3] if len(parts) > 3 else "?"
    except Exception:
        pass

    return info


def get_candidate_cuda_dirs() -> List[str]:
    """Returns candidate directories where CUDA 12 runtime DLLs may reside."""
    candidates = [
        APPDATA_CUDA_BIN,
        APPDATA_CUDA_DIR,
    ]

    # Frozen exe relative dirs
    base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    for pkg in ["cublas", "cudnn", "cuda_nvrtc"]:
        candidates.append(os.path.join(base_dir, "nvidia", pkg, "bin"))
        candidates.append(os.path.join(os.path.dirname(base_dir), "nvidia", pkg, "bin"))

    # Virtual environment site-packages
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    venv_nvidia = os.path.join(project_root, ".venv", "Lib", "site-packages", "nvidia")
    for pkg in ["cublas", "cudnn", "cuda_nvrtc"]:
        candidates.append(os.path.join(venv_nvidia, pkg, "bin"))

    # System CUDA toolkit path fallback
    cuda_path_env = os.environ.get("CUDA_PATH", "")
    if cuda_path_env and os.path.isdir(os.path.join(cuda_path_env, "bin")):
        candidates.append(os.path.join(cuda_path_env, "bin"))

    return [c for c in candidates if os.path.isdir(c)]


def find_cuda_dlls() -> List[str]:
    """Locates any existing CUDA 12 runtime DLLs on the machine."""
    found_dlls = []
    for d in get_candidate_cuda_dirs():
        try:
            for f in os.listdir(d):
                if f.lower().endswith(".dll") and ("cublas" in f.lower() or "cudnn" in f.lower() or "nvrtc" in f.lower()):
                    found_dlls.append(os.path.join(d, f))
        except Exception:
            continue
    return found_dlls


def register_cuda_dlls() -> bool:
    """
    Registers CUDA runtime directories with Windows DLL loader and PATH.
    Returns True if at least one valid CUDA directory was registered.
    """
    valid_dirs = get_candidate_cuda_dirs()
    registered = False
    for d in valid_dirs:
        try:
            if hasattr(os, "add_dll_directory"):
                os.add_dll_directory(d)
            if d not in os.environ.get("PATH", ""):
                os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")
            registered = True
        except Exception as e:
            logger.debug(f"Could not register DLL dir {d}: {e}")
    return registered


def get_cuda_status() -> Dict[str, Any]:
    """Provides a complete health and acceleration status summary."""
    gpu = get_gpu_info()
    dlls = find_cuda_dlls()
    has_dlls = len(dlls) > 0
    is_ready = gpu["has_nvidia_gpu"] and has_dlls

    return {
        "has_gpu": gpu["has_nvidia_gpu"],
        "gpu_name": gpu["gpu_name"],
        "total_memory": gpu["total_memory"],
        "free_memory": gpu["free_memory"],
        "driver_version": gpu["driver_version"],
        "has_cuda_dlls": has_dlls,
        "dll_count": len(dlls),
        "is_ready": is_ready,
        "cuda_appdata_dir": APPDATA_CUDA_DIR,
        "download_url": CUDA_RUNTIME_DOWNLOAD_URL,
        "manual_guide_url": "https://github.com/PRN-6/NOVA#gpu-acceleration-setup",
        "download_state": get_download_progress()
    }


def get_download_progress() -> Dict[str, Any]:
    """Returns thread-safe current download state."""
    with _download_lock:
        return dict(_download_state)


def start_cuda_runtime_download(
    on_complete: Optional[Callable[[bool, str], None]] = None,
    custom_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Starts asynchronous download and extraction of CUDA 12 runtime DLLs
    into AppData/NOVA/cuda/bin.
    """
    global _download_state
    with _download_lock:
        if _download_state["is_downloading"]:
            return {"success": False, "message": "Download is already in progress."}
        _download_state = {
            "is_downloading": True,
            "progress": 0,
            "downloaded_mb": 0.0,
            "total_mb": 0.0,
            "status": "Starting download...",
            "error": None
        }

    url = custom_url or CUDA_RUNTIME_DOWNLOAD_URL

    def _worker():
        global _download_state
        zip_path = os.path.join(APPDATA_DIR, "cuda_runtime_temp.zip")
        try:
            os.makedirs(APPDATA_CUDA_BIN, exist_ok=True)

            logger.info(f"Downloading CUDA runtime from {url}...")
            with _download_lock:
                _download_state["status"] = "Connecting to server..."

            # Setup HTTP Request with browser-like user agent
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) NOVA-Assistant/1.1"})
            with urllib.request.urlopen(req, timeout=30) as response, open(zip_path, "wb") as out_file:
                total_size = response.length or 0
                total_mb = round(total_size / (1024 * 1024), 1) if total_size > 0 else 0.0

                with _download_lock:
                    _download_state["total_mb"] = total_mb
                    _download_state["status"] = f"Downloading CUDA runtime (~{total_mb} MB)..."

                downloaded = 0
                chunk_size = 1024 * 64  # 64 KB chunks

                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    out_file.write(chunk)
                    downloaded += len(chunk)
                    dl_mb = round(downloaded / (1024 * 1024), 1)
                    pct = int((downloaded / total_size) * 100) if total_size > 0 else 50

                    with _download_lock:
                        _download_state["progress"] = pct
                        _download_state["downloaded_mb"] = dl_mb

            # Extraction
            with _download_lock:
                _download_state["status"] = "Extracting runtime libraries..."
                _download_state["progress"] = 95

            logger.info(f"Extracting {zip_path} to {APPDATA_CUDA_BIN}...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for member in zip_ref.namelist():
                    filename = os.path.basename(member)
                    if not filename:
                        continue
                    # Extract DLLs directly into APPDATA_CUDA_BIN
                    if filename.lower().endswith(".dll"):
                        source = zip_ref.open(member)
                        target_file = os.path.join(APPDATA_CUDA_BIN, filename)
                        with open(target_file, "wb") as target:
                            shutil.copyfileobj(source, target)

            # Cleanup temp zip
            try:
                os.remove(zip_path)
            except Exception:
                pass

            # Register DLLs immediately into runtime
            register_cuda_dlls()

            with _download_lock:
                _download_state["is_downloading"] = False
                _download_state["progress"] = 100
                _download_state["status"] = "Installation Complete! Restart NOVA to activate GPU mode."
                _download_state["error"] = None

            logger.info("CUDA runtime successfully downloaded, extracted and registered.")
            if on_complete:
                on_complete(True, "CUDA runtime installed successfully!")

        except Exception as e:
            logger.error(f"CUDA runtime download failed: {e}", exc_info=True)
            with _download_lock:
                _download_state["is_downloading"] = False
                _download_state["status"] = "Download failed"
                _download_state["error"] = str(e)
            if on_complete:
                on_complete(False, str(e))

    thread = threading.Thread(target=_worker, daemon=True, name="CUDADownloadWorker")
    thread.start()
    return {"success": True, "message": "Download started in background."}
