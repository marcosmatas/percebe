#!/bin/bash

# Script de instalación para P.E.R.C.E.B.E.

echo "====================================="
echo "Instalador de P.E.R.C.E.B.E."
echo "====================================="
echo ""

# Verificar si se ejecuta como root
if [ "$EUID" -ne 0 ]; then 
    echo "Por favor ejecuta este script como root (sudo ./install.sh)"
    exit 1
fi

# Crear usuario del sistema si no existe
if ! id -u percebe > /dev/null 2>&1; then
    echo "Creando usuario del sistema 'percebe'..."
    useradd -r -s /bin/false -d /opt/percebe percebe
fi

# Crear directorios
echo "Creando directorios..."
mkdir -p /opt/percebe
mkdir -p /opt/percebe/percebe_config

# Copiar ejecutable (asumiendo que ya está compilado con pyinstaller)
if [ -f "./dist/percebe_server" ]; then
    echo "Copiando ejecutable..."
    cp ./dist/percebe_server /opt/percebe/
    chmod +x /opt/percebe/percebe_server
else
    echo "ADVERTENCIA: No se encontró el ejecutable en ./dist/percebe_server"
    echo "Deberás compilarlo con pyinstaller y copiarlo manualmente a /opt/percebe/"
fi

# Establecer permisos
echo "Configurando permisos..."
chown -R percebe:percebe /opt/percebe

# Copiar archivo de servicio systemd
echo "Instalando servicio systemd..."
cp percebe.service /etc/systemd/system/

# Recargar systemd
echo "Recargando systemd..."
systemctl daemon-reload

# Configurar firewall (opcional)
echo ""
echo "¿Deseas abrir el puerto 5555 en el firewall para la comunicación con el cliente? (s/n)"
read -r response
if [[ "$response" =~ ^([sS][iI]|[sS])$ ]]; then
    if command -v ufw &> /dev/null; then
        echo "Configurando UFW..."
        ufw allow 5555/tcp
        ufw reload
    elif command -v firewall-cmd &> /dev/null; then
        echo "Configurando firewalld..."
        firewall-cmd --permanent --add-port=5555/tcp
        firewall-cmd --reload
    else
        echo "No se detectó UFW ni firewalld. Configura el firewall manualmente para el puerto 5555."
    fi
fi

echo ""
echo "====================================="
echo "Instalación completada"
echo "====================================="
echo ""
echo "Comandos útiles:"
echo "  sudo systemctl start percebe    # Iniciar servicio"
echo "  sudo systemctl stop percebe     # Detener servicio"
echo "  sudo systemctl restart percebe  # Reiniciar servicio"
echo "  sudo systemctl enable percebe   # Habilitar inicio automático"
echo "  sudo systemctl status percebe   # Ver estado del servicio"
echo "  sudo journalctl -u percebe -f   # Ver logs en tiempo real"
echo ""
echo "Archivos de configuración en: /opt/percebe/percebe_config/"
echo ""
