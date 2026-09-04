import ctypes
import time
import subprocess

user32 = ctypes.windll.user32

# Virtual-Key Codes
VK_CONTROL = 0x11
VK_SHIFT = 0x10
VK_MENU = 0x12  # Alt
VK_LWIN = 0x5B
VK_T = 0x54
VK_W = 0x57
VK_N = 0x4E
VK_S = 0x53
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
VK_SNAPSHOT = 0x2C  # PrintScreen
VK_RETURN = 0x0D    # Enter / Return
VK_TAB = 0x09       # Tab
VK_UP = 0x26        # Up Arrow
VK_DOWN = 0x28      # Down Arrow
VK_LEFT = 0x25      # Left Arrow
VK_RIGHT = 0x27     # Right Arrow
VK_F4 = 0x73        # F4 key

KEYEVENTF_KEYUP = 0x0002

def press_hotkey(*vkeys):
    """Presses and releases a combination of keys in sequence."""
    for vk in vkeys:
        user32.keybd_event(vk, 0, 0, 0)
    time.sleep(0.05)
    for vk in reversed(vkeys):
        user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)

def trigger_press_enter():
    press_hotkey(VK_RETURN)

def trigger_press_tab(times=1):
    for _ in range(times):
        press_hotkey(VK_TAB)
        time.sleep(0.05)

def trigger_press_arrow(direction):
    if direction == "up":
        press_hotkey(VK_UP)
    elif direction == "down":
        press_hotkey(VK_DOWN)
    elif direction == "left":
        press_hotkey(VK_LEFT)
    elif direction == "right":
        press_hotkey(VK_RIGHT)

def trigger_close_window():
    """Simulates Alt+F4 to close the active foreground window."""
    press_hotkey(VK_MENU, VK_F4)

def trigger_maximize_window():
    """Maximizes the active foreground window."""
    hwnd = user32.GetForegroundWindow()
    if hwnd:
        user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
    else:
        press_hotkey(VK_LWIN, VK_UP)

def trigger_minimize_window():
    """Minimizes the active foreground window."""
    hwnd = user32.GetForegroundWindow()
    if hwnd:
        user32.ShowWindow(hwnd, 6)  # SW_MINIMIZE
    else:
        press_hotkey(VK_LWIN, VK_DOWN)

def kill_process(exe_name: str) -> bool:
    """Terminates an application process and its child tree cleanly on Windows."""
    try:
        # If no extension is specified or wildcard given, format accordingly
        target = exe_name if "*" in exe_name else (exe_name if exe_name.lower().endswith(".exe") else f"{exe_name}*")
        subprocess.Popen(f'taskkill /F /T /IM "{target}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        try:
            name_clean = exe_name.replace(".exe", "").replace("*", "")
            subprocess.Popen(f'powershell -Command "Stop-Process -Name {name_clean}* -Force -ErrorAction SilentlyContinue"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            return False

def trigger_new_tab():
    press_hotkey(VK_CONTROL, VK_T)

def trigger_close_tab():
    press_hotkey(VK_CONTROL, VK_W)

def trigger_reopen_tab():
    press_hotkey(VK_CONTROL, VK_SHIFT, VK_T)

def trigger_new_chat():
    press_hotkey(VK_CONTROL, VK_N)

def trigger_volume_up():
    for _ in range(5):
        press_hotkey(VK_VOLUME_UP)
        time.sleep(0.02)

def trigger_volume_down():
    for _ in range(5):
        press_hotkey(VK_VOLUME_DOWN)
        time.sleep(0.02)

def trigger_volume_mute():
    press_hotkey(VK_VOLUME_MUTE)

def trigger_lock_workstation():
    user32.LockWorkStation()

def trigger_snipping_tool():
    press_hotkey(VK_LWIN, VK_SHIFT, VK_S)

def type_text(text: str):
    """Pasting or typing text directly into the focused foreground window."""
    try:
        import pyperclip
        pyperclip.copy(text)
        time.sleep(0.02)
        press_hotkey(VK_CONTROL, 0x56)  # Ctrl+V
    except Exception:
        try:
            import pyautogui
            pyautogui.write(text, interval=0.01)
        except Exception:
            pass
