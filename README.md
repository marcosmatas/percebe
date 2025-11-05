# P.E.R.C.E.B.E. - Resumen Completo del Proyecto

**Programa de Envío y Redirección de Correos Eliminando Basura Electrónica**

![percebe](https://github.com/user-attachments/assets/9f703876-81f4-43c6-bb99-f7bbc0eeaac5)


## 📦 Estructura del Proyecto

### Archivos del Servidor (Linux/Ubuntu)

1. **percebe_server.py** - Programa servidor principal
2. **percebe.service** - Archivo de servicio systemd
3. **install.sh** - Script de instalación automatizada
4. **config_tool.py** - Herramienta CLI para configuración
5. **config_example.json** - Ejemplo de configuración
6. **README.md** - Documentación del servidor

### Archivos del Cliente (Windows)

1. **percebe_client.py** - Programa cliente con interfaz gráfica
2. **compile.bat** - Script de compilación automática
3. **generate_icon.py** - Generador de icono (opcional)
4. **README_CLIENTE_WINDOWS.md** - Documentación del cliente

## 🚀 Instalación Rápida

### En el Servidor (Ubuntu Linux)

```bash
# 1. Compilar el servidor
pip install pyinstaller
pyinstaller --onefile --name percebe_server percebe_server.py

# 2. Instalar como servicio
chmod +x install.sh
sudo ./install.sh

# 3. Configurar primera cuenta (opcional, también desde Windows)
sudo python3 config_tool.py /opt/percebe/percebe_config/config.json

# 4. Iniciar servicio
sudo systemctl start percebe
sudo systemctl enable percebe  # Inicio automático

# 5. Ver logs
sudo journalctl -u percebe -f
```

### En el Cliente (Windows)

```bash
# 1. Instalar dependencias
pip install PyQt5

# 2. Compilar (usar compile.bat o manual)
compile.bat

# O manualmente:
pip install pyinstaller
pyinstaller --onefile --windowed --name "PERCEBE" percebe_client.py

# 3. El ejecutable estará en: dist\PERCEBE.exe

# 4. Copiar a ubicación permanente y crear acceso directo en Inicio
# Win+R → shell:startup → Crear acceso directo
```

## 🎯 Flujo de Trabajo

### Primera Configuración

1. **Instala el servidor** en Linux
2. **Asegúrate que el puerto 5555 está abierto** en el firewall
3. **Compila e instala el cliente** en Windows
4. **Ejecuta el cliente** (se minimiza a la bandeja)
5. **Haz doble clic en el icono 🐚** para abrir la interfaz
6. **Conecta al servidor** indicando su IP
7. **Crea una cuenta nueva** o configura una existente
8. **Define reglas de reenvío**
9. **Guarda la configuración**

### Uso Diario

El sistema funciona automáticamente:
- El servidor revisa las cuentas cada 60 segundos (configurable)
- Aplica las reglas definidas
- Reenvía los correos que coincidan
- Elimina todos los correos procesados
- Registra todo en los logs

Solo necesitas el cliente Windows para:
- Modificar configuraciones
- Añadir/editar reglas
- Ver los logs

## 🔑 Características Principales

### Servidor (Linux)
✅ Procesamiento automático de múltiples cuentas  
✅ Sistema de reglas flexible  
✅ Reenvío con o sin adjuntos  
✅ Logs separados (reenvíos y errores)  
✅ API TCP para cliente remoto  
✅ Servicio systemd para ejecución continua  
✅ Sin dependencias externas (solo Python estándar)  

### Cliente (Windows)
✅ Interfaz gráfica moderna  
✅ Icono en bandeja del sistema  
✅ Gestión completa de cuentas  
✅ Editor de reglas visual  
✅ Visualización de logs  
✅ Inicio automático con Windows  
✅ Conexión remota al servidor  

## 📊 Ejemplo de Configuración

### Cuenta de Gmail

```json
{
    "nombre": "Mi Gmail Principal",
    "activa": true,
    "imap_server": "imap.gmail.com",
    "imap_user": "tucorreo@gmail.com",
    "imap_password": "app_password_aqui",
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_user": "tucorreo@gmail.com",
    "smtp_password": "app_password_aqui",
    "reglas": [...]
}
```

### Regla de Reenvío

```json
{
    "nombre": "Facturas Urgentes",
    "activa": true,
    "remitentes": ["facturacion@proveedor.com"],
    "palabras_clave": ["factura", "urgent"],
    "destinatarios": ["contabilidad@miempresa.com"],
    "incluir_adjuntos": false
}
```

## 🔧 Módulos Python Necesarios

### Servidor (Linux)
```bash
# Ninguno - Solo biblioteca estándar de Python 3
# Ya incluidos: imaplib, smtplib, email, socket, json, threading
```

### Cliente (Windows)
```bash
pip install PyQt5
```

### Para Compilar (Ambos)
```bash
pip install pyinstaller
```

## 🛠️ Comandos Útiles

### Servidor Linux
```bash
# Estado del servicio
sudo systemctl status percebe

# Reiniciar servicio
sudo systemctl restart percebe

# Logs en tiempo real
sudo journalctl -u percebe -f

# Ver configuración
sudo cat /opt/percebe/percebe_config/config.json

# Ver logs de reenvíos
sudo tail -f /opt/percebe/percebe_config/reenvios.log

# Ver logs de errores
sudo tail -f /opt/percebe/percebe_config/errores.log
```

### Cliente Windows
```bash
# Compilar
compile.bat

# Generar icono (opcional)
python generate_icon.py
pip install Pillow  # Si no está instalado

# Abrir carpeta de inicio automático
Win+R → shell:startup
```

## 🔐 Consideraciones de Seguridad

### Para Gmail
- Usa **contraseñas de aplicación**, no tu contraseña normal
- Activa verificación en dos pasos
- Ve a: Cuenta Google → Seguridad → Contraseñas de aplicaciones

### Firewall
```bash
# Linux (UFW)
sudo ufw allow 5555/tcp

# Linux (firewalld)
sudo firewall-cmd --permanent --add-port=5555/tcp
sudo firewall-cmd --reload

# Windows
# Permitir la aplicación en el Firewall de Windows
```

### Permisos
```bash
# El servidor se ejecuta con usuario sin privilegios
sudo chown -R percebe:percebe /opt/percebe
sudo chmod 600 /opt/percebe/percebe_config/config.json
```

## 🐛 Solución Rápida de Problemas

### El servidor no procesa correos
1. Ver logs: `sudo journalctl -u percebe -f`
2. Verificar configuración IMAP/SMTP
3. Comprobar contraseñas de aplicación (Gmail)
4. Ver log de errores: `/opt/percebe/percebe_config/errores.log`

### El cliente no conecta
1. Verificar que el servidor está ejecutándose
2. Hacer ping a la IP del servidor
3. Verificar puerto 5555 abierto
4. Probar telnet: `telnet IP_SERVIDOR 5555`

### Gmail bloquea el acceso
1. Usa contraseña de aplicación, no la normal
2. Habilita IMAP en Gmail
3. Verifica actividad sospechosa en la cuenta

## 📈 Capacidades

- **Cuentas**: Ilimitadas
- **Reglas por cuenta**: Ilimitadas
- **Intervalo de revisión**: Configurable (por defecto 60s)
- **Tamaño de adjuntos**: Sin límite (depende del servidor SMTP)
- **Clientes simultáneos**: Múltiples (solo lectura/escritura)

## 🎨 Personalización

### Cambiar intervalo de revisión
Edita la configuración (desde cliente o archivo):
```json
{
    "intervalo_revision": 120,  // segundos
    ...
}
```

### Cambiar puerto API
```json
{
    "api_port": 6666,
    ...
}
```

## 📝 Archivos de Configuración

### Servidor
```
/opt/percebe/percebe_config/
├── config.json          # Configuración principal
├── reenvios.log        # Log de reenvíos
└── errores.log         # Log de errores
```

### Cliente
```
(carpeta del ejecutable)/
└── percebe_client_config.json  # Solo IP y puerto del servidor
```

## 🎯 Ventajas del Sistema

✅ **Automatización total** - El servidor trabaja 24/7  
✅ **Sin adjuntos pesados** - Opción de reenviar sin archivos  
✅ **Múltiples cuentas** - Gestiona todas desde un lugar  
✅ **Reglas flexibles** - Filtra por remitente, asunto o ambos  
✅ **Logs completos** - Sabe qué se procesó y cuándo  
✅ **Limpieza automática** - Elimina correos después de procesar  
✅ **Gestión remota** - Configura desde Windows  
✅ **Inicio automático** - Cliente y servidor arrancan solos  

## 🚦 Estados de Operación

### Servidor
- 🟢 **Running** - Procesando correos normalmente
- 🟡 **Starting** - Iniciando servicio
- 🔴 **Failed** - Error, revisar logs

### Cliente
- 🟢 **Conectado** - Comunicación con servidor OK
- 🟡 **Desconectado** - Sin conexión, solo modo local
- 🔴 **Error** - No puede comunicarse con servidor

## 📞 Soporte y Logs

Para diagnosticar problemas, revisa siempre en orden:

1. **Logs del servidor**: `sudo journalctl -u percebe -n 50`
2. **Log de errores**: `/opt/percebe/percebe_config/errores.log`
3. **Log de reenvíos**: `/opt/percebe/percebe_config/reenvios.log`
4. **Configuración**: `/opt/percebe/percebe_config/config.json`
5. **Estado del servicio**: `sudo systemctl status percebe`

---

**¡Disfruta de P.E.R.C.E.B.E.! 🐚**

*Sistema creado para simplificar la gestión automática de correos electrónicos*
