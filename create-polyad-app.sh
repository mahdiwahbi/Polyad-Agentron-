#!/bin/bash
# Script pour créer une application Polyad.app

# Définition des chemins
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
APP_PATH="$SCRIPT_DIR/Polyad.app"
CONTENTS_PATH="$APP_PATH/Contents"
MACOS_PATH="$CONTENTS_PATH/MacOS"
RESOURCES_PATH="$CONTENTS_PATH/Resources"

# Suppression de l'application existante si nécessaire
if [ -d "$APP_PATH" ]; then
    rm -rf "$APP_PATH"
fi

# Création de la structure de l'application
mkdir -p "$MACOS_PATH"
mkdir -p "$RESOURCES_PATH"

# Création du script principal de l'application
cat > "$MACOS_PATH/PolyadLauncher" << 'EOF'
#!/bin/bash

# Chemin absolu du répertoire de l'application
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd ../../.. && pwd )"

# Exécution du script de lancement
"$DIR/launch-polyad.sh"
EOF

# Rendre le script exécutable
chmod +x "$MACOS_PATH/PolyadLauncher"

# Création du fichier Info.plist
cat > "$CONTENTS_PATH/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>PolyadLauncher</string>
    <key>CFBundleIconFile</key>
    <string>polyad-icon</string>
    <key>CFBundleIdentifier</key>
    <string>com.polyad.app</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>Polyad</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.14</string>
    <key>LSUIElement</key>
    <false/>
    <key>NSHumanReadableCopyright</key>
    <string>Copyright © 2025 Polyad. All rights reserved.</string>
</dict>
</plist>
EOF

# Création d'une icône de base (cercle coloré)
# Note: Ceci crée une icône très basique. Pour une meilleure icône, utilisez un fichier .icns préparé
cat > "$RESOURCES_PATH/polyad-icon.svg" << 'EOF'
<svg width="1024" height="1024" xmlns="http://www.w3.org/2000/svg">
  <circle cx="512" cy="512" r="450" fill="#3498db" />
  <circle cx="512" cy="512" r="350" fill="#2980b9" />
  <circle cx="512" cy="512" r="250" fill="#1e6091" />
  <text x="512" y="550" font-family="Arial" font-size="150" text-anchor="middle" fill="white">P</text>
</svg>
EOF

# Conversion de SVG en icns (si les outils sont disponibles)
if command -v sips &> /dev/null && command -v iconutil &> /dev/null; then
    # Création d'un dossier temporaire pour les icônes
    ICON_SET="$SCRIPT_DIR/polyad.iconset"
    mkdir -p "$ICON_SET"
    
    # Conversion SVG en PNG
    sips -s format png "$RESOURCES_PATH/polyad-icon.svg" --out "$ICON_SET/icon_512x512.png"
    
    # Création des différentes tailles
    sips -z 16 16 "$ICON_SET/icon_512x512.png" --out "$ICON_SET/icon_16x16.png"
    sips -z 32 32 "$ICON_SET/icon_512x512.png" --out "$ICON_SET/icon_16x16@2x.png"
    sips -z 32 32 "$ICON_SET/icon_512x512.png" --out "$ICON_SET/icon_32x32.png"
    sips -z 64 64 "$ICON_SET/icon_512x512.png" --out "$ICON_SET/icon_32x32@2x.png"
    sips -z 128 128 "$ICON_SET/icon_512x512.png" --out "$ICON_SET/icon_128x128.png"
    sips -z 256 256 "$ICON_SET/icon_512x512.png" --out "$ICON_SET/icon_128x128@2x.png"
    sips -z 256 256 "$ICON_SET/icon_512x512.png" --out "$ICON_SET/icon_256x256.png"
    sips -z 512 512 "$ICON_SET/icon_512x512.png" --out "$ICON_SET/icon_256x256@2x.png"
    cp "$ICON_SET/icon_512x512.png" "$ICON_SET/icon_512x512@2x.png"
    
    # Création du fichier icns
    iconutil -c icns "$ICON_SET" -o "$RESOURCES_PATH/polyad-icon.icns"
    
    # Suppression des fichiers temporaires
    rm -rf "$ICON_SET"
    rm "$RESOURCES_PATH/polyad-icon.svg"
else
    echo "Les outils sips et iconutil ne sont pas disponibles pour créer une vraie icône"
    mv "$RESOURCES_PATH/polyad-icon.svg" "$RESOURCES_PATH/polyad-icon.icns"
fi

echo "Application Polyad.app créée avec succès dans $APP_PATH"
