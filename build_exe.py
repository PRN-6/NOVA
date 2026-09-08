import os
import sys
import subprocess

def build():
    print("=" * 50)
    print("         NOVA Standalone EXE Build Pipeline       ")
    print("=" * 50)

    # Check for optional CUDA bundling flag
    bundle_cuda = "--bundle-cuda" in sys.argv
    nvidia_bin_datas = []
    
    if bundle_cuda:
        print("[*] Full offline CUDA bundling enabled via --bundle-cuda")
        venv_nvidia = os.path.join(".venv", "Lib", "site-packages", "nvidia")
        if os.path.isdir(venv_nvidia):
            for pkg in ["cublas", "cudnn", "cuda_nvrtc"]:
                bin_path = os.path.join(venv_nvidia, pkg, "bin")
                if os.path.isdir(bin_path):
                    nvidia_bin_datas.append(f"--add-data={bin_path};nvidia/{pkg}/bin")
                    print(f"[+] Added bundled CUDA package: {pkg}")
    else:
        print("[*] Building Slim Lightweight Package (CUDA downloaded on-demand in-app)")

    # 3. Assemble PyInstaller Build Command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name=NOVA",
        "--icon=assets\\icon.ico",
        "--add-data=plugins;plugins",
        "--add-data=skills;skills",
        "--add-data=server;server",
        "--add-data=ui;ui",
        "--add-data=utils;utils",
        "--add-data=config.py;.",
        "--collect-all=faster_whisper",
        "--collect-all=ctranslate2",
        "--collect-all=sounddevice",
        "--collect-all=pystray",
        "--collect-all=PIL",
        "--collect-all=webview",
        "--collect-all=pyautogui",
        "--collect-all=qrcode",
        "--hidden-import=pystray._win32",
        "--hidden-import=scipy.special.cython_special",
        "app.py"
    ] + nvidia_bin_datas

    print("\n[+] Compiling NOVA with PyInstaller...")
    subprocess.run(cmd, check=True)

    print("\n" + "=" * 50)
    print(" [OK] Build Successful! Output directory: dist/NOVA/")
    print(" You can zip 'dist/NOVA' and distribute it to any Windows user.")
    print("=" * 50)

if __name__ == "__main__":
    build()
