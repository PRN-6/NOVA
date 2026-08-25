# NOVA Extra & Community Plugins

This directory contains standalone, optional plugins that are separated from NOVA's default built-in core.

---

## 📦 Available Extra Plugins

1. **`whatsapp_plugin.py`** (💬 WhatsApp Desktop)
   - Launch app (`"open whatsapp"`)
   - Clean tree termination (`"close whatsapp"`)
   - New conversation shortcut (`"new chat in whatsapp"`)

2. **`brave_plugin.py`** (🦁 Brave Browser)
   - Launch browser (`"open brave"`)
   - Close browser (`"close brave"`)
   - Tab controls (`"new tab in brave"`, `"close tab in brave"`, `"reopen tab in brave"`)

---

## 🚀 How to Install Them into NOVA

You can install any of these plugins in **two ways**:

### Method 1: Via the NOVA Control Center GUI (Recommended)
1. Open the **NOVA Control Center** (right-click the tray icon $\to$ **Plugins & Skills**).
2. Go to the **🛠️ Create / Install Plugin** tab.
3. Click **"📁 Browse & Install Plugin File..."** and select `extra_plugins/whatsapp_plugin.py` or `extra_plugins/brave_plugin.py`.
4. It will automatically install into your `%APPDATA%\NOVA\plugins\` folder and hot-reload immediately!

### Method 2: Manual Copy
Copy the `.py` file directly to your User AppData folder:
```powershell
Copy-Item "extra_plugins\whatsapp_plugin.py" -Destination "$env:APPDATA\NOVA\plugins\"
```
Restart or open the Control Center, and NOVA will automatically discover it.
