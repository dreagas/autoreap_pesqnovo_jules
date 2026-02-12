#!/bin/bash

# Define nome do executável e diretório de instalação
EXEC_NAME="AutoREAPv2_Linux"
INSTALL_DIR="$HOME/AutoREAP"
DESKTOP_FILE="AutoREAP.desktop"
ICON_REL_PATH="img/REAP2.ico"

echo "--- INSTALADOR DO AUTOREAP PARA LINUX ---"

# Verifica se o executável existe na pasta atual
if [ ! -f "./$EXEC_NAME" ]; then
    echo "ERRO: O arquivo '$EXEC_NAME' não foi encontrado nesta pasta."
    echo "Certifique-se de executar este script de DENTRO da pasta do programa."
    exit 1
fi

# Cria a pasta de destino
echo "Criando pasta em $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"

# Copia todos os arquivos da pasta atual para o destino
echo "Copiando arquivos..."
cp -r * "$INSTALL_DIR/"

# Caminho final do ícone e executável
FINAL_EXEC="$INSTALL_DIR/$EXEC_NAME"
FINAL_ICON="$INSTALL_DIR/$ICON_REL_PATH"

# Caminho do arquivo .desktop no sistema do usuário
USER_APPS_DIR="$HOME/.local/share/applications"
mkdir -p "$USER_APPS_DIR"
TARGET_DESKTOP="$USER_APPS_DIR/$DESKTOP_FILE"

# Prepara o arquivo .desktop
if [ -f "$DESKTOP_FILE" ]; then
    echo "Configurando atalho no menu..."
    cp "$DESKTOP_FILE" "$TARGET_DESKTOP"

    # Substitui os placeholders pelos caminhos reais
    sed -i "s|PLACEHOLDER_EXEC|$FINAL_EXEC|g" "$TARGET_DESKTOP"
    sed -i "s|PLACEHOLDER_ICON|$FINAL_ICON|g" "$TARGET_DESKTOP"
else
    echo "AVISO: Arquivo $DESKTOP_FILE não encontrado. Criando um básico..."
    echo "[Desktop Entry]
Version=1.0
Type=Application
Name=AutoREAP v2
Comment=Automação PesqBrasil
Exec=$FINAL_EXEC
Icon=$FINAL_ICON
Terminal=false
Categories=Utility;Office;
StartupNotify=true" > "$TARGET_DESKTOP"
fi

# Permissões de execução
chmod +x "$TARGET_DESKTOP"
chmod +x "$FINAL_EXEC"

# Tenta atualizar o banco de dados de ícones/menu
update-desktop-database "$USER_APPS_DIR" 2>/dev/null || true

echo ""
echo "SUCESSO! A instalação foi concluída."
echo "Você pode encontrar o AutoREAP no menu de aplicativos do seu sistema."
echo "Ou executar diretamente: $FINAL_EXEC"
