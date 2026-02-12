#!/bin/bash
# Script de Build para Linux

# Verifica se pyinstaller está instalado
if ! command -v pyinstaller &> /dev/null
then
    echo "PyInstaller não encontrado. Instalando..."
    pip install pyinstaller
fi

echo "Iniciando build do AutoREAP v1.0.3.1..."

# Comando PyInstaller (usando : como separador no Linux)
pyinstaller --noconsole --onedir \
    --name="AutoREAPv2_Linux" \
    --icon="img/REAP2.ico" \
    --add-data "img:img" \
    --add-data "ui/theme.qss:ui" \
    --clean \
    main.py

echo "Build concluído! O executável está em dist/AutoREAPv2_Linux"
echo "Agora, copie o arquivo 'install.sh' e 'AutoREAP.desktop' para dentro dessa pasta antes de zipar para o cliente."
