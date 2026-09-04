import os
import sys
import json
import logging
import platform
import shutil
import subprocess
from typing import Dict, Any, List
import sounddevice as sd
import numpy as np

from plugins.manager import plugin_manager
from plugins.profile_manager import profile_manager

logger = logging.getLogger("NOVA.DashboardBridge")

class DashboardAPI:
    """
    Python-to-JavaScript IPC Bridge.
    All public methods in this class are accessible inside the WebView window
    via `window.pywebview.api.<method_name>()`.
    """
    def __init__(self, window=None):
        self._window = window

    def set_window(self, window):
        self._window = window

    # ---------------- Profile & Settings ---------------- #

    def get_profile(self) -> Dict[str, Any]:
        """Returns the full user profile & settings dictionary."""
        try:
            return {
                "user_name": profile_manager.get("user_name", "User"),
                "assistant_name": profile_manager.get("assistant_name", "Nova"),
                "wake_word": profile_manager.get("wake_word", "alexa"),
                "wake_threshold": float(profile_manager.get("wake_threshold", 0.50)),
                "whisper_model": profile_manager.get("whisper_model", "base.en"),
                "whisper_device": profile_manager.get("whisper_device", "cuda"),
                "hud_enabled": bool(profile_manager.get("hud_enabled", True)),
                "theme": profile_manager.get("theme", "dark_cyberpunk")
            }
        except Exception as e:
            logger.error(f"Error getting profile: {e}")
            return {}

    def save_profile(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Saves updated settings to user_profile.json."""
        try:
            profile_manager.update_multiple(data)
            logger.info("Saved user profile via Dashboard API.")
            return {"success": True, "message": "Preferences saved successfully!"}
        except Exception as e:
            logger.error(f"Error saving profile: {e}")
            return {"success": False, "message": str(e)}

    # ---------------- Plugin Management ---------------- #

    def get_plugins(self) -> List[Dict[str, Any]]:
        """Returns a list of all installed plugins with metadata."""
        try:
            plugins = plugin_manager.get_all_plugins()
            result = []
            for p in plugins:
                # Gather voice trigger phrases
                triggers = []
                for phrases in p.fast_intents.values():
                    if phrases:
                        triggers.extend(phrases[:2])

                result.append({
                    "id": p.id,
                    "name": p.name,
                    "version": p.version,
                    "description": p.description,
                    "icon": p.icon,
                    "is_enabled": bool(p.is_enabled),
                    "is_builtin": getattr(p, "is_builtin", False),
                    "triggers": triggers[:5]
                })
            return result
        except Exception as e:
            logger.error(f"Error getting plugins: {e}")
            return []

    def toggle_plugin(self, plugin_id: str, enabled: bool) -> Dict[str, Any]:
        """Enables or disables a specific plugin."""
        try:
            plugin_manager.set_plugin_enabled(plugin_id, enabled)
            return {"success": True, "plugin_id": plugin_id, "enabled": enabled}
        except Exception as e:
            logger.error(f"Error toggling plugin {plugin_id}: {e}")
            return {"success": False, "message": str(e)}

    def uninstall_plugin(self, plugin_id: str) -> Dict[str, Any]:
        """Uninstalls and deletes a custom user plugin."""
        try:
            success = plugin_manager.uninstall_plugin(plugin_id)
            if success:
                return {"success": True, "message": f"Plugin '{plugin_id}' uninstalled."}
            else:
                return {"success": False, "message": "Cannot uninstall built-in core plugins."}
        except Exception as e:
            logger.error(f"Error uninstalling plugin: {e}")
            return {"success": False, "message": str(e)}

    def create_plugin(self, data: Dict[str, str]) -> Dict[str, Any]:
        """Generates a new plugin from template."""
        try:
            pid = data.get("id", "").strip().lower().replace(" ", "_")
            pname = data.get("name", "").strip()
            picon = data.get("icon", "🔌").strip() or "🔌"
            pdesc = data.get("desc", f"Controls {pname} application").strip()
            pcmd = data.get("cmd", f"open {pname}").strip()

            if not pid or not pname:
                return {"success": False, "message": "Plugin ID and Name are required."}

            file_created = plugin_manager.create_plugin_template(pid, pname, picon, pdesc, pcmd)
            return {
                "success": True,
                "message": f"Plugin '{pname}' created and activated!",
                "filename": os.path.basename(file_created)
            }
        except Exception as e:
            logger.error(f"Error creating plugin: {e}")
            return {"success": False, "message": str(e)}

    def pick_plugin_file(self) -> str:
        """Opens native file picker to select a .py or .zip plugin."""
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            file_path = filedialog.askopenfilename(
                title="Select NOVA Plugin File",
                filetypes=[("NOVA Plugin Files", "*.py *.zip"), ("Python Files", "*.py"), ("All Files", "*.*")]
            )
            root.destroy()
            return file_path or ""
        except Exception as e:
            logger.error(f"Error opening file dialog: {e}")
            return ""

    def install_plugin_file(self, file_path: str) -> Dict[str, Any]:
        """Installs a plugin from selected file path."""
        try:
            if not file_path or not os.path.exists(file_path):
                return {"success": False, "message": "Invalid file path selected."}

            success = plugin_manager.install_plugin_from_file(file_path)
            if success:
                return {"success": True, "message": f"Plugin installed successfully: {os.path.basename(file_path)}"}
            else:
                return {"success": False, "message": "Could not install plugin file."}
        except Exception as e:
            logger.error(f"Error installing plugin file: {e}")
            return {"success": False, "message": str(e)}

    # ---------------- System Diagnostics & Telemetry ---------------- #

    def get_system_diagnostics(self) -> List[Dict[str, Any]]:
        """Runs hardware and environment health checks."""
        sections = []

        # 1. AI & Speech Engines
        ai_checks = []
        
        # Ollama Server
        ollama_path = shutil.which("ollama")
        if ollama_path:
            try:
                r = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=4)
                models = [l.split()[0] for l in r.stdout.strip().split("\n")[1:] if l.strip()]
                if models:
                    ai_checks.append({
                        "name": "Ollama Server",
                        "status": "ok",
                        "detail": f"Installed & Running • {len(models)} model(s) available ({', '.join(models[:2])})",
                        "link": None
                    })
                else:
                    ai_checks.append({
                        "name": "Ollama Server",
                        "status": "warn",
                        "detail": "Running, but no models found. Run: ollama pull qwen2.5:0.5b",
                        "link": None
                    })
            except Exception:
                ai_checks.append({
                    "name": "Ollama Server",
                    "status": "warn",
                    "detail": "Installed but not responding. Start Ollama from your system tray.",
                    "link": None
                })
        else:
            ai_checks.append({
                "name": "Ollama Server",
                "status": "fail",
                "detail": "Ollama not found. Required for local AI reasoning and skills.",
                "link": "https://ollama.com/download"
            })

        # faster-whisper
        try:
            import faster_whisper
            ai_checks.append({
                "name": "faster-whisper (ASR)",
                "status": "ok",
                "detail": f"Loaded v{getattr(faster_whisper, '__version__', '1.0+')} • High-speed Whisper Engine",
                "link": None
            })
        except ImportError:
            ai_checks.append({
                "name": "faster-whisper (ASR)",
                "status": "fail",
                "detail": "Not installed in environment.",
                "link": None
            })

        sections.append({"title": "Core AI & Speech Engines", "icon": "cpu", "items": ai_checks})

        # 2. NVIDIA GPU & CUDA Acceleration
        gpu_checks = []
        try:
            r = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total,memory.free,driver_version", "--format=csv,noheader"],
                capture_output=True, text=True, timeout=4
            )
            if r.returncode == 0 and r.stdout.strip():
                parts = [p.strip() for p in r.stdout.strip().split(",")]
                name = parts[0] if len(parts) > 0 else "NVIDIA GPU"
                total_mem = parts[1] if len(parts) > 1 else "?"
                free_mem = parts[2] if len(parts) > 2 else "?"
                driver = parts[3] if len(parts) > 3 else "?"
                gpu_checks.append({
                    "name": "NVIDIA GPU",
                    "status": "ok",
                    "detail": f"{name} • {free_mem} free / {total_mem} • Driver {driver}",
                    "link": None
                })
            else:
                gpu_checks.append({
                    "name": "NVIDIA GPU",
                    "status": "warn",
                    "detail": "nvidia-smi returned no data. Speech recognition will run on CPU.",
                    "link": None
                })
        except Exception:
            gpu_checks.append({
                "name": "NVIDIA GPU",
                "status": "warn",
                "detail": "No dedicated NVIDIA GPU detected. Whisper will use multi-core CPU.",
                "link": None
            })

        # CUDA Runtime & cuBLAS DLL check
        cublas_found = False
        project_root = os.path.dirname(os.path.dirname(__file__))
        for search_dir in [
            os.path.join(project_root, ".venv", "Lib", "site-packages", "nvidia", "cublas", "bin"),
            os.path.join(project_root, "nvidia", "cublas", "bin")
        ]:
            if os.path.isdir(search_dir):
                dlls = [f for f in os.listdir(search_dir) if f.endswith(".dll")]
                if dlls:
                    cublas_found = True
                    gpu_checks.append({
                        "name": "CUDA 12 Runtime (cuBLAS)",
                        "status": "ok",
                        "detail": f"Active • {len(dlls)} CUDA runtime libraries loaded",
                        "link": None
                    })
                    break
        if not cublas_found:
            gpu_checks.append({
                "name": "CUDA 12 Runtime (cuBLAS)",
                "status": "warn",
                "detail": "cuBLAS DLLs not detected in package paths. GPU mode may fallback to CPU.",
                "link": None
            })

        sections.append({"title": "NVIDIA GPU & Acceleration", "icon": "zap", "items": gpu_checks})

        # 3. Audio & Hardware Input
        hw_checks = []
        try:
            devices = sd.query_devices()
            input_devs = [d for d in devices if d['max_input_channels'] > 0]
            if input_devs:
                default_in = sd.query_devices(kind='input')
                hw_checks.append({
                    "name": "Microphone Hardware",
                    "status": "ok",
                    "detail": f"{len(input_devs)} input device(s) • Default: {default_in['name'][:35]}",
                    "link": None
                })
            else:
                hw_checks.append({
                    "name": "Microphone Hardware",
                    "status": "fail",
                    "detail": "No audio recording devices found! Please connect a microphone.",
                    "link": None
                })
        except Exception as e:
            hw_checks.append({
                "name": "Microphone Hardware",
                "status": "fail",
                "detail": f"Audio subsystem error: {e}",
                "link": None
            })

        hw_checks.append({
            "name": "Operating System",
            "status": "ok",
            "detail": f"{platform.system()} {platform.release()} ({platform.architecture()[0]})",
            "link": None
        })

        sections.append({"title": "Audio Input & System Specs", "icon": "mic", "items": hw_checks})

        return sections

    def test_microphone(self) -> Dict[str, Any]:
        """Records a 0.4s audio slice to measure current mic volume/energy."""
        try:
            duration = 0.4
            sr = 16000
            recording = sd.rec(int(duration * sr), samplerate=sr, channels=1, dtype="float32")
            sd.wait()
            rms = float(np.sqrt(np.mean(recording**2)))
            level_pct = min(100, int(rms * 500))
            return {"success": True, "level": level_pct, "rms": rms}
        except Exception as e:
            return {"success": False, "level": 0, "message": str(e)}

    # ---------------- System Utilities ---------------- #

    def open_external_url(self, url: str) -> bool:
        """Safely opens an external URL in the default browser."""
        try:
            if url.startswith("http://") or url.startswith("https://"):
                os.startfile(url)
                return True
        except Exception as e:
            logger.error(f"Failed to open URL {url}: {e}")
        return False

    def close_window(self):
        """Closes the dashboard window."""
        if hasattr(self, "_window") and self._window:
            self._window.destroy()
