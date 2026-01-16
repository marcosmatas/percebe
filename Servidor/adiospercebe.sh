#!/bin/bash

# ============================================================================
# Script de DESINSTALACIÓN de P.E.R.C.E.B.E.
# (Procedimiento de Extracción y Retirada Completa de Elementos Binarios Enquistados)
# ============================================================================
# Este script arranca el percebe de la roca con cuidado quirúrgico.
# Como en Galicia, se necesita una navaja afilada y mano firme.
# ============================================================================

set -e  # Los percebes se arrancan de una vez, sin errores a medias

# Colores (los mismos que usamos para instalarlo, por nostalgia)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ============================================================================
# Funciones de mensajería (reutilizadas del script de instalación)
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
# Verificación de privilegios (arrancar percebes requiere fuerza root)
# ============================================================================
if [ "$EUID" -ne 0 ]; then 
    print_error "Este script necesita ejecutarse como root."
    print_info "Inténtalo con: curl -s https://programas.flopy.es/percebe/adiospercebe.sh | sudo bash"
    exit 1
fi

echo ""
echo "========================================================================"
print_warning "Iniciando DESINSTALACIÓN de P.E.R.C.E.B.E..."
echo "========================================================================"
print_info "Preparando navaja y espátula para arrancar el percebe..."
echo ""
sleep 1

# Confirmación de seguridad (por si alguien ejecutó esto sin querer)
print_warning "¡ATENCIÓN! Estás a punto de arrancar el percebe del sistema."
print_info "El proceso es irreversible (como sacarlo de la roca en la vida real)."
echo ""
read -p "¿Estás seguro de que quieres continuar? (escribe 'SI' para confirmar): " confirmacion

if [ "$confirmacion" != "SI" ]; then
    print_info "Desinstalación cancelada. El percebe sigue adherido."
    echo "Si cambias de opinión, ya sabes dónde encontrarlo."
    exit 0
fi

echo ""
print_info "Confirmación recibida. Comenzando extracción..."
sleep 1

# ============================================================================
# PASO 1: Detener el servicio (adormecer al percebe antes de arrancarlo)
# ============================================================================
print_info "Deteniendo el servicio P.E.R.C.E.B.E..."

if systemctl is-active --quiet percebe; then
    systemctl stop percebe
    print_success "Servicio detenido. El percebe ya no filtra correos."
else
    print_warning "El servicio ya estaba detenido (o nunca arrancó)."
fi

# ============================================================================
# PASO 2: Deshabilitar el servicio (evitar que resucite en el próximo reinicio)
# ============================================================================
print_info "Deshabilitando inicio automático..."

if systemctl is-enabled --quiet percebe 2>/dev/null; then
    systemctl disable percebe
    print_success "Servicio deshabilitado. No volverá a arrancar automáticamente."
else
    print_warning "El servicio no estaba habilitado."
fi

# ============================================================================
# PASO 3: Eliminar archivo de servicio systemd (arrancar el percebe de systemd)
# ============================================================================
print_info "Eliminando archivo de servicio de systemd..."

if [ -f /etc/systemd/system/percebe.service ]; then
    rm -f /etc/systemd/system/percebe.service
    print_success "Archivo de servicio eliminado."
else
    print_warning "El archivo de servicio no existía."
fi

print_info "Recargando configuración de systemd..."
systemctl daemon-reload
systemctl reset-failed 2>/dev/null || true
print_success "Systemd ya no recuerda al percebe."

# ============================================================================
# PASO 4: Eliminar el ejecutable (sacar el percebe de la piedra)
# ============================================================================
print_info "Eliminando ejecutable de /usr/local/bin/percebe_server..."

if [ -f /usr/local/bin/percebe_server ]; then
    rm -f /usr/local/bin/percebe_server
    print_success "Ejecutable eliminado. El percebe ha sido arrancado."
else
    print_warning "El ejecutable no existía en /usr/local/bin/percebe_server."
fi

# ============================================================================
# PASO 5: Eliminar usuario del sistema (borrar la identidad del percebe)
# ============================================================================
print_info "Eliminando usuario 'percebe' del sistema..."

if id "percebe" &>/dev/null; then
    # Primero intentar eliminar el grupo si existe
    if getent group percebe &>/dev/null; then
        deluser --system percebe 2>/dev/null || userdel percebe 2>/dev/null || true
        # Eliminar el grupo si quedó huérfano
        groupdel percebe 2>/dev/null || true
        print_success "Usuario y grupo 'percebe' eliminados."
    else
        deluser --system percebe 2>/dev/null || userdel percebe 2>/dev/null || true
        print_success "Usuario 'percebe' eliminado."
    fi
else
    print_warning "El usuario 'percebe' no existía."
fi

# ============================================================================
# PASO 6: Verificación final (comprobar que no queda ni rastro)
# ============================================================================
echo ""
print_info "Realizando verificación final..."
sleep 1

ERRORES=0

# Verificar que el servicio no está activo
if systemctl is-active --quiet percebe 2>/dev/null; then
    print_error "El servicio sigue activo."
    ((ERRORES++))
fi

# Verificar que el archivo de servicio no existe
if [ -f /etc/systemd/system/percebe.service ]; then
    print_error "El archivo de servicio todavía existe."
    ((ERRORES++))
fi

# Verificar que el ejecutable no existe
if [ -f /usr/local/bin/percebe_server ]; then
    print_error "El ejecutable todavía existe."
    ((ERRORES++))
fi

# Verificar que el usuario no existe
if id "percebe" &>/dev/null; then
    print_error "El usuario 'percebe' todavía existe."
    ((ERRORES++))
fi

# ============================================================================
# PASO 7: Mensaje final (despedida emotiva del percebe)
# ============================================================================
echo ""
echo "========================================================================"

if [ $ERRORES -eq 0 ]; then
    print_success "Desinstalación completada exitosamente."
    echo ""
    sleep 1
    echo "Verificando que no quedan restos de caparazón..."
    sleep 1
    echo "Limpiando adherencias residuales..."
    sleep 1
    echo "Resultado: 0% Percebe, 100% Roca limpia."
    echo ""
    echo "P.E.R.C.E.B.E. ha sido arrancado del sistema completamente."
    echo "Tu servidor está ahora libre de crustáceos digitales."
    echo ""
    sleep 1
    echo -e "${YELLOW}"
    cat << "EOF"
       .---.
      /     \
     | x_x  |  <-- ¡Adiós, mundo cruel!
      \  _  /       Me arrancaron de la roca...
       |||||        Al menos fue con una buena navaja.
       |||||        
  ~~~~~~~~~~~~~~~~~~~~~~~
     ¡Hasta siempre, percebe!
EOF
    echo -e "${NC}"
    echo "========================================================================"
    echo ""
    print_info "Si algún día cambias de opinión, siempre puedes volver a instalarlo:"
    echo "  curl -s https://programas.flopy.es/percebe/percebe.sh | sudo bash"
    echo ""
    print_success "¡Gracias por haber usado P.E.R.C.E.B.E.!"
    echo ""
else
    print_error "Se encontraron $ERRORES errores durante la desinstalación."
    print_warning "Es posible que necesites limpiar manualmente algunos componentes."
    echo ""
    print_info "Componentes que podrían necesitar limpieza manual:"
    echo "  • Servicio:      sudo systemctl stop percebe && sudo systemctl disable percebe"
    echo "  • Archivo:       sudo rm /etc/systemd/system/percebe.service"
    echo "  • Ejecutable:    sudo rm /usr/local/bin/percebe_server"
    echo "  • Usuario:       sudo deluser --system percebe"
    echo "  • Recargar:      sudo systemctl daemon-reload"
    echo ""
    exit 1
fi