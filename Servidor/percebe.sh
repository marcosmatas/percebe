#!/bin/bash

# ============================================================================
# Script de instalación de P.E.R.C.E.B.E.
# (Programa de Envío y Redirección de Correo Eliminando Basura Electrónica)
# ============================================================================
# Este script instala un percebe digital en tu servidor.
# Como su primo marino, se adhiere firmemente y no se suelta ni con espátula.
# ============================================================================

set -e  # Porque los percebes no toleran errores, son duros como rocas

# Colores para hacer esto más bonito que un percebe recién sacado del mar
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color - volvemos al gris piedra natural

# ============================================================================
# Función: Mostrar mensajes con estilo (porque hasta los crustáceos tienen clase)
# ============================================================================
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✔]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# ============================================================================
# Verificación de privilegios (los percebes necesitan acceso root para adherirse)
# ============================================================================
if [ "$EUID" -ne 0 ]; then 
    print_error "Este script necesita ejecutarse como root."
    print_info "Inténtalo con: curl -s https://programas.flopy.es/percebe/percebe.sh | sudo bash"
    exit 1
fi

echo ""
print_info "Iniciando instalación de P.E.R.C.E.B.E..."
print_info "Preparando la roca... digo, el servidor..."
echo ""
sleep 1

# ============================================================================
# PASO 1: Descargar el ejecutable a temporal (pescando el percebe del océano)
# ============================================================================
print_info "Descargando percebe_server desde el mar de internet..."

# Descargar primero a /tmp que siempre tiene permisos
if curl -fsSL "https://programas.flopy.es/percebe/percebe_server" -o /tmp/percebe_server; then
    print_success "Percebe capturado exitosamente"
else
    print_error "No se pudo descargar el percebe. ¿Hay marea baja en el servidor?"
    exit 1
fi

# ============================================================================
# PASO 2: Mover e instalar el ejecutable (plantando el percebe en su sitio)
# ============================================================================
print_info "Trasplantando el percebe a su ubicación definitiva..."
mv /tmp/percebe_server /usr/local/bin/percebe_server

print_info "Ajustando la dureza del caparazón (permisos 755)..."
chmod 755 /usr/local/bin/percebe_server
chown root:root /usr/local/bin/percebe_server
print_success "Caparazón endurecido. Este percebe ya puede moverse solo."

# ============================================================================
# PASO 3: Crear usuario del sistema (cada percebe necesita su identidad)
# ============================================================================
print_info "Creando identidad para el percebe en el sistema..."

# Verificar si el usuario ya existe (los percebes son territoriales)
if id "percebe" &>/dev/null; then
    print_warning "El usuario 'percebe' ya existe. Reutilizando..."
else
    adduser --system --no-create-home --group percebe
    print_success "Usuario 'percebe' creado. Sin casa, como buen habitante de las rocas."
fi

# ============================================================================
# PASO 4: Crear directorios de trabajo (la cueva del percebe)
# ============================================================================
print_info "Excavando cueva para el percebe (creando directorios)..."

# Directorio de configuración
if [ ! -d /etc/percebe ]; then
    mkdir -p /etc/percebe
    print_success "Directorio de configuración creado en /etc/percebe"
else
    print_warning "Directorio /etc/percebe ya existe"
fi

chown percebe:percebe /etc/percebe
chmod 755 /etc/percebe

# Directorio de datos y logs
if [ ! -d /var/lib/percebe ]; then
    mkdir -p /var/lib/percebe
    print_success "Directorio de datos creado en /var/lib/percebe"
else
    print_warning "Directorio /var/lib/percebe ya existe"
fi

chown percebe:percebe /var/lib/percebe
chmod 755 /var/lib/percebe

print_success "Cueva acondicionada. El percebe tiene donde guardar sus cosas."

# ============================================================================
# PASO 5: Crear archivo de servicio systemd (adherir el percebe al sistema)
# ============================================================================
print_info "Creando el archivo de servicio systemd. Situando el percebe sobre la roca."

cat > /etc/systemd/system/percebe.service << 'EOF'
[Unit]
Description=Demonio de P.E.R.C.E.B.E.
After=network.target

[Service]
Type=simple
User=percebe
WorkingDirectory=/var/lib/percebe
ExecStart=/usr/local/bin/percebe_server
Restart=always
RestartSec=10

# Opciones de seguridad (Protección contra mareas)
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

print_success "Archivo de servicio creado en /etc/systemd/system/percebe.service"
print_info "Nota: El servicio usará el usuario 'percebe' con directorio /var/lib/percebe"

# ============================================================================
# PASO 6: Activar y arrancar el servicio (momento de adherencia definitiva)
# ============================================================================
print_info "Iniciando proceso de adherencia al sistema..."
sleep 1

print_info "Recargando configuración de systemd..."
systemctl daemon-reload

print_info "Habilitando P.E.R.C.E.B.E. para inicio automático..."
systemctl enable percebe

print_info "Arrancando el servicio percebe..."
systemctl start percebe

sleep 2

# ============================================================================
# PASO 7: Verificación (comprobar que el percebe está bien pegado)
# ============================================================================
print_info "Verificando adherencia del percebe al sistema..."
sleep 1

if systemctl is-active --quiet percebe; then
    print_success "¡El percebe está vivo y adherido!"
    INSTALLATION_SUCCESS=true
else
    print_error "Error: El percebe no logró adherirse correctamente."
    print_error "Estado del servicio:"
    systemctl status percebe --no-pager
    echo ""
    print_info "Mostrando últimas líneas del log para diagnóstico:"
    journalctl -u percebe -n 20 --no-pager
    INSTALLATION_SUCCESS=false
    exit 1
fi

# ============================================================================
# PASO 8: Huevo de Pascua (celebración de percebe feliz)
# ============================================================================
if [ "$INSTALLATION_SUCCESS" = true ]; then
    echo ""
    echo "========================================================================"
    sleep 1
    echo -e "${GREEN}[✔] Configuración de P.E.R.C.E.B.E. completada con éxito.${NC}"
    sleep 1
    echo "Verificando adherencia al servidor..."
    sleep 2
    echo "Analizando pureza del flujo de datos..."
    sleep 1
    echo "Resultado: 0% Spam, 100% Granito Galego."
    echo ""
    echo "A partir de ahora si un mail que no cumple las reglas intenta entrar,"
    echo "será golpeado repetidamente contra las rocas hasta que"
    echo "confiese quién es su remitente y será eliminado de la cuenta."
    echo ""
    sleep 1
    echo -e "${YELLOW}"
    cat << "EOF"
       .---.
      /     \
     | () () |  <-- ¡Instalación completada! 
      \  ^  /       Ahora P.E.R.C.E.B.E es parte de tu sistema.
       |||||        
       |||||        
  ~~~~~~~~~~~~~~~~~~~~~~~
EOF
    echo -e "${NC}"
    echo "========================================================================"
    echo ""
    print_info "Comandos útiles para gestionar tu percebe:"
    echo "  • Ver estado:    sudo systemctl status percebe"
    echo "  • Ver logs:      sudo journalctl -u percebe -f"
    echo "  • Reiniciar:     sudo systemctl restart percebe"
    echo "  • Detener:       sudo systemctl stop percebe"
    echo ""
    print_info "Archivos y directorios importantes:"
    echo "  • Ejecutable:    /usr/local/bin/percebe_server"
    echo "  • Configuración: /etc/percebe/"
    echo "  • Datos:         /var/lib/percebe/"
    echo "  • Servicio:      /etc/systemd/system/percebe.service"
    echo ""
    print_success "¡Que disfrutes de tu nuevo reenviador de correo!"
    echo ""
fi
