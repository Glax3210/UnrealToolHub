# 🔧 Unreal Plugin Rebuilder

A cross-platform GUI application for rebuilding Unreal Engine plugins with ease.

![Python](https://img.shields.io/badge/python-3.7+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)
![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)

## 📋 Description

Unreal Plugin Rebuilder is a user-friendly desktop application that simplifies the process of rebuilding Unreal Engine plugins. It automatically detects installed Unreal Engine versions, provides a clean interface for selecting plugin files, and displays real-time build progress.

## ✨ Features

- 🎯 **Auto-Detection** - Automatically finds installed Unreal Engine versions on your system
- 🖥️ **Cross-Platform** - Works on Windows, macOS, and Linux
- 📊 **Real-Time Output** - Monitor build progress with live console output
- 💾 **Smart Memory** - Remembers your last used paths and settings
- 🎨 **Modern UI** - Clean, intuitive interface with helpful tooltips
- ⚡ **Build Control** - Start, stop, and monitor builds with ease
- 📁 **Quick Access** - Open output folder directly after successful build
- 🔍 **Validation** - Automatic validation of files and directories
- 📝 **Logging** - Comprehensive logging for troubleshooting

## 🚀 Installation

### Prerequisites

- Python 3.7 or higher
- Unreal Engine (any version) installed on your system
- tkinter (usually comes with Python)

### Setup

```bash
# Clone the repository
git clone https://github.com/Glax3210/UnrealToolHub.git

# Navigate to the directory
cd UnrealToolHub

# Run the application
python unreal_plugin_rebuilder.py
```

### Dependencies

The application uses only Python standard library modules:
- `tkinter` - GUI framework
- `os`, `pathlib` - File operations
- `platform` - System detection
- `subprocess` - Running build commands
- `logging` - Event logging
- `winreg` - Windows registry access (Windows only)
- `threading` - Async operations
- `json` - Config file management

## 📖 Usage

### Step-by-Step Guide

1. **Launch the Application**
   ```bash
   python unreal_plugin_rebuilder.py
   ```

2. **Select Your Plugin**
   - Click "Browse .uplugin" button
   - Navigate to your plugin's `.uplugin` file
   - Select it

3. **Choose Engine Version** (Optional)
   - The latest installed version is selected by default
   - Change if needed from the dropdown menu

4. **Select Output Folder**
   - Click "Browse Folder" button
   - Choose where you want the rebuilt plugin saved

5. **Start Building**
   - Click "▶ Start Rebuild" button
   - Monitor progress in the build output section
   - Wait for completion

6. **Access Output**
   - Click "📁 Open Output Folder" to view rebuilt plugin

### Screenshot Workflow

```
[Plugin Selection] → [Engine Version] → [Output Folder] → [Start Build] → [Success!]
```

## ⚙️ Configuration

The application automatically saves your preferences in `rebuilder_config.json`:

```json
{
  "last_uplugin": "/path/to/your/plugin.uplugin",
  "last_output": "/path/to/output/folder",
  "last_engine": "5.3"
}
```

This file is created automatically and updated each time you start a build.

## 🔧 How It Works

1. **Engine Detection**: Scans system registry (Windows) or common installation directories (macOS/Linux) for Unreal Engine installations
2. **Path Resolution**: Locates `RunUAT.bat` (Windows) or `RunUAT.sh` (macOS/Linux) for the selected engine version
3. **Build Execution**: Runs the command:
   ```bash
   RunUAT BuildPlugin -Plugin="path/to/plugin.uplugin" -Package="output/folder"
   ```
4. **Output Monitoring**: Captures and displays real-time build output
5. **Completion**: Notifies user and enables quick access to output folder

## 📁 Project Structure

```
UnrealToolHub/
├── unreal_plugin_rebuilder.py    # Main application
├── rebuilder_config.json          # Auto-generated config (after first run)
├── unreal_plugin_rebuilder.log    # Auto-generated log file
├── LICENSE                        # Apache License 2.0
└── README.md                      # This file
```

## 🐛 Troubleshooting

### Engine Not Detected

**Problem**: No Unreal Engine versions found

**Solutions**:
- Ensure Unreal Engine is properly installed
- On Windows: Check registry at `HKEY_LOCAL_MACHINE\SOFTWARE\EpicGames\Unreal Engine`
- On macOS: Check `/Users/Shared/Epic Games/`
- On Linux: Check `~/Epic Games/`

### Build Fails

**Problem**: Build process fails with errors

**Solutions**:
- Check the build output for specific error messages
- Ensure the plugin is compatible with the selected engine version
- Verify you have write permissions to the output folder
- Check `unreal_plugin_rebuilder.log` for detailed error information

### RunUAT Not Found

**Problem**: "RunUAT not found for Unreal Engine X.X"

**Solutions**:
- Verify your Unreal Engine installation is complete
- Check that `Engine/Build/BatchFiles/RunUAT.bat` (or `.sh`) exists
- Reinstall the engine version if necessary

## 📝 Logging

All operations are logged to `unreal_plugin_rebuilder.log` in the application directory. Check this file for detailed information about builds and errors.

## 🔐 Platform-Specific Notes

### Windows
- Requires Unreal Engine installed via Epic Games Launcher
- Uses registry to detect engine installations
- Uses `RunUAT.bat`

### macOS
- Checks `/Users/Shared/Epic Games/`
- Uses `RunUAT.sh`

### Linux
- Checks `~/Epic Games/`
- Uses `RunUAT.sh`
- May require executable permissions: `chmod +x RunUAT.sh`

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests
- Improve documentation

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

```
Copyright (C) Glax Akash - All Rights Reserved

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

## 👨‍💻 Author

**Glax Akash** - [GitHub](https://github.com/Glax3210)

Created with ❤️ for the Unreal Engine community

## 🙏 Acknowledgments

- Built with Python and Tkinter
- Uses Unreal Engine's BuildPlugin automation
- Inspired by the need for simpler plugin rebuilding workflows

## 📞 Support

If you encounter any issues:
1. Check the `unreal_plugin_rebuilder.log` file
2. Review the troubleshooting section above
3. Open an issue on GitHub with:
   - Your OS and Python version
   - Unreal Engine version
   - Error messages from the log
   - Steps to reproduce the issue

**Contact**: Akashtheskyofunivers@gmial.com

Project Link: [https://github.com/Glax3210/UnrealToolHub](https://github.com/Glax3210/UnrealToolHub)

---

**Note**: This tool is a wrapper around Unreal Engine's official BuildPlugin automation tool and requires a valid Unreal Engine installation to function.

---

Made with ❤️ by [Glax Akash](https://github.com/Glax3210)