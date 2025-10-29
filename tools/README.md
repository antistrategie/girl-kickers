# Development Tools

## AssetStudio

This directory contains `Asset Studio.zip` - a fork of AssetStudio by kenji1997 that is compatible with Girls' Frontline 2 assets.

### Setup

1. Extract the zip file:
```bash
cd tools
unzip "Asset Studio.zip"
```

2. Install .NET 8.0 Desktop Runtime:
```bash
wget https://builds.dotnet.microsoft.com/dotnet/WindowsDesktop/8.0.21/windowsdesktop-runtime-8.0.21-win-x64.exe
wine windowsdesktop-runtime-8.0.21-win-x64.exe
```

### Running AssetStudio

```bash
wine "tools/Asset Studio/AssetStudio.GUI.exe"
```

If using Windows 🤮, you can probably just run the `.exe` (I think).
