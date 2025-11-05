# P.E.R.C.E.B.E.

**Programa de Envío y Redirección de Correos Eliminando Basura Electrónica**

Sistema automático de gestión y reenvío de correos electrónicos con soporte para múltiples cuentas y reglas personalizadas.

## 📋 Requisitos

### Módulos de Python necesarios:

```bash
# Ninguno adicional - todos son parte de la biblioteca estándar de Python 3
# Los módulos usados son:
# - imaplib (cliente IMAP)
# - smtplib (cliente SMTP)
# - email (procesamiento de correos)
# - socket (comunicación de red)
# - threading (multihilo)
# - json (configuración)
# - pathlib (manejo de archivos)
```

### Para compilar con PyInstaller:

```bash
pip install pyinstaller
```

## 🚀 Instalación

### 1. Compilar el ejecutable

```bash
# Desde el directorio donde está percebe_server.py
pyinstaller --onefile --name percebe_server percebe_server.py
```

### 2. Ejecutar el script de instalación

```bash
chmod +x install.sh
sudo ./install.sh
```

### 3. Configurar el servicio

El servicio se instala pero no se inicia automáticamente. Primero debes configurar las cuentas.

## ⚙️ Configuración

### Estructura de la configuración

El archivo de configuración se encuentra en `/opt/percebe/percebe_config/config.json` y tiene la siguiente estructura:

```json
{
    "cuentas": [
        {
            "nombre": "Nombre descriptivo de la cuenta",
            "activa": true,
            "imap_server": "imap.ejemplo.com",
            "imap_user": "usuario@ejemplo.com",
            "imap_password": "contraseña",
            "smtp_server": "smtp.ejemplo.com",
            "smtp_port": 587,
            "smtp_user": "usuario@ejemplo.com",
            "smtp_password": "contraseña",
            "reglas": [...]
        }
    ],
    "intervalo_revision": 60,
    "api_enabled": true,
    "api_port": 5555
}
```

### Configuración de reglas

Cada cuenta puede tener múltiples reglas:

```json
{
    "nombre": "Nombre descriptivo de la regla",
    "activa": true,
    "remitentes": [
        "correo@ejemplo.com",
        "@dominio.com"
    ],
    "palabras_clave": [
        "palabra1",
        "frase completa"
    ],
    "destinatarios": [
        "destino1@ejemplo.com",
        "destino2@ejemplo.com"
    ],
    "incluir_adjuntos": false
}
```

**Campos:**
- `nombre`: Identificador de la regla
- `activa`: Si la regla está activa o no
- `remitentes`: Lista de remitentes o dominios a filtrar (puede estar vacía para cualquier remitente)
- `palabras_clave`: Palabras o frases que deben aparecer en el asunto (puede estar vacía para cualquier asunto)
- `destinatarios`: Lista de correos donde reenviar
- `incluir_adjuntos`: `true` para incluir adjuntos, `false` para omitirlos

### Configuración para Gmail

Si usas Gmail, necesitas usar una "Contraseña de aplicación":

1. Ve a tu cuenta de Google
2. Seguridad → Verificación en dos pasos (actívala si no la tienes)
3. Seguridad → Contraseñas de aplicaciones
4. Genera una contraseña para "Correo"
5. Usa esa contraseña en el campo `imap_password` y `smtp_password`

**Servidores de Gmail:**
- IMAP: `imap.gmail.com`
- SMTP: `smtp.gmail.com` (puerto 587)

## 🎮 Gestión del servicio

```bash
# Iniciar el servicio
sudo systemctl start percebe

# Detener el servicio
sudo systemctl stop percebe

# Reiniciar el servicio
sudo systemctl restart percebe

# Habilitar inicio automático al arrancar
sudo systemctl enable percebe

# Deshabilitar inicio automático
sudo systemctl disable percebe

# Ver estado del servicio
sudo systemctl status percebe

# Ver logs en tiempo real
sudo journalctl -u percebe -f

# Ver logs completos
sudo journalctl -u percebe
```

## 📊 Logs

El sistema mantiene tres tipos de logs:

1. **Log de reenvíos** (`/opt/percebe/percebe_config/reenvios.log`):
   - Registra cada correo reenviado
   - Formato: `[Fecha] Asunto: ... | Regla: ...`

2. **Log de errores** (`/opt/percebe/percebe_config/errores.log`):
   - Registra únicamente errores
   - Útil para diagnóstico de problemas

3. **Journal de systemd**:
   - Información general del sistema
   - Accesible con `journalctl -u percebe`

## 🔌 API para cliente Windows

El servidor expone una API TCP en el puerto 5555 (configurable) para comunicación con el cliente Windows.

### Comandos disponibles:

#### Obtener configuración
```json
{
    "command": "get_config"
}
```

#### Establecer configuración
```json
{
    "command": "set_config",
    "config": { ... }
}
```

#### Obtener logs
```json
{
    "command": "get_logs",
    "log_type": "reenvios"  // o "errores"
}
```

#### Probar conexión de cuenta
```json
{
    "command": "test_connection",
    "cuenta_id": 0
}
```

## 🔒 Seguridad

### Permisos de archivos

El servicio se ejecuta con un usuario dedicado (`percebe`) sin privilegios de administrador.

```bash
# Cambiar permisos manualmente si es necesario
sudo chown -R percebe:percebe /opt/percebe
sudo chmod 600 /opt/percebe/percebe_config/config.json
```

### Firewall

Si usas el cliente Windows desde otra máquina, asegúrate de abrir el puerto 5555:

```bash
# UFW
sudo ufw allow 5555/tcp

# firewalld
sudo firewall-cmd --permanent --add-port=5555/tcp
sudo firewall-cmd --reload
```

### Contraseñas

**IMPORTANTE:** El archivo de configuración contiene contraseñas en texto plano. Asegúrate de:
- Restringir permisos del archivo
- No compartir el archivo de configuración
- Usar contraseñas de aplicación cuando sea posible (Gmail, Outlook, etc.)

## 🐛 Solución de problemas

### El servicio no inicia

```bash
# Ver errores detallados
sudo journalctl -u percebe -n 50

# Verificar permisos
ls -la /opt/percebe/
```

### No se procesan correos

1. Verifica la configuración IMAP/SMTP
2. Prueba la conexión manualmente
3. Revisa el log de errores
4. Verifica que las reglas estén activas

### Problemas con Gmail

- Asegúrate de usar una contraseña de aplicación
- Verifica que IMAP esté habilitado en Gmail
- Comprueba que no haya bloqueos de seguridad en tu cuenta

### No se puede conectar desde Windows

1. Verifica que el firewall permita el puerto 5555
2. Comprueba que el servicio esté ejecutándose
3. Prueba la conexión con telnet: `telnet IP_SERVIDOR 5555`

## 📝 Notas importantes

- **Eliminación de correos**: Todos los correos se eliminan del servidor después de procesarlos, cumplan o no con las reglas
- **Intervalo de revisión**: Por defecto 60 segundos, ajustable en la configuración
- **Múltiples cuentas**: Cada cuenta es completamente independiente con sus propias reglas
- **Orden de reglas**: Se aplica la primera regla que coincida

## 🔄 Actualización

Para actualizar el programa:

```bash
# 1. Detener el servicio
sudo systemctl stop percebe

# 2. Compilar nueva versión
pyinstaller --onefile --name percebe_server percebe_server.py

# 3. Copiar ejecutable
sudo cp ./dist/percebe_server /opt/percebe/

# 4. Establecer permisos
sudo chown percebe:percebe /opt/percebe/percebe_server
sudo chmod +x /opt/percebe/percebe_server

# 5. Iniciar servicio
sudo systemctl start percebe
```

## 📞 Soporte

Para reportar problemas o sugerencias, revisa los logs y el archivo de configuración antes de contactar soporte.
