# P.E.R.C.E.B.E. - Cliente Windows

Guía completa para instalar y usar el cliente Windows de P.E.R.C.E.B.E.

## 📋 Requisitos

### Módulos de Python necesarios:

```bash
pip install PyQt5
```

Eso es todo. PyQt5 es el único módulo adicional necesario.

## 🔨 Compilación del Cliente

### 1. Instalar PyInstaller

```bash
pip install pyinstaller
```

### 2. Compilar el ejecutable

```bash
# Opción básica
pyinstaller --onefile --windowed --name "P.E.R.C.E.B.E" percebe_client.py

# Opción con icono personalizado (si tienes un archivo .ico)
pyinstaller --onefile --windowed --icon=percebe.ico --name "P.E.R.C.E.B.E" percebe_client.py
```

**Parámetros explicados:**
- `--onefile`: Crea un único ejecutable
- `--windowed`: No muestra consola (interfaz gráfica limpia)
- `--name`: Nombre del ejecutable
- `--icon`: Archivo de icono (opcional)

### 3. Encontrar el ejecutable

El archivo `P.E.R.C.E.B.E.exe` estará en:
```
dist/P.E.R.C.E.B.E.exe
```

## 🚀 Instalación y Configuración

### Instalación Manual

1. **Copiar el ejecutable** a una carpeta permanente:
   ```
   C:\Program Files\PERCEBE\P.E.R.C.E.B.E.exe
   ```
   O cualquier ubicación que prefieras.

2. **El archivo de configuración** se creará automáticamente en la misma carpeta del ejecutable:
   ```
   percebe_client_config.json
   ```

### Inicio Automático con Windows

#### Opción 1: Carpeta de Inicio (Recomendada)

1. Presiona `Win + R` y escribe: `shell:startup`
2. Crea un acceso directo del ejecutable en esa carpeta
3. Hecho. El programa se iniciará con Windows

#### Opción 2: Registro de Windows (Avanzada)

1. Presiona `Win + R` y escribe: `regedit`
2. Navega a: `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`
3. Crea una nueva entrada de tipo String:
   - Nombre: `PERCEBE`
   - Valor: Ruta completa al ejecutable

## 🎮 Uso del Cliente

### Primera Ejecución

1. **El programa se minimiza a la bandeja del sistema** (área de notificaciones junto al reloj)
2. **Busca el icono 🐚** (caracol) en la bandeja
3. **Haz doble clic** en el icono para abrir la interfaz

### Conexión al Servidor

1. **Indica la IP del servidor Linux**: 
   - Si está en la misma máquina: `127.0.0.1`
   - Si está en la red local: Ejemplo `192.168.1.100`
   
2. **Puerto**: Por defecto `5555` (debe coincidir con el servidor)

3. **Prueba la conexión** con el botón "Probar Conexión"

4. **Conecta** con el botón "Conectar"

### Gestión de Cuentas

#### Crear Nueva Cuenta

1. Haz clic en "➕ Nueva Cuenta"
2. Se crea una cuenta con datos de ejemplo
3. **Pestaña "Configuración de la Cuenta"**:
   - Modifica el nombre
   - Configura servidor IMAP (recepción)
   - Configura servidor SMTP (envío)
   - Introduce usuarios y contraseñas

#### Ejemplo para Gmail:

```
Nombre: Mi cuenta Gmail
IMAP Server: imap.gmail.com
IMAP User: tucorreo@gmail.com
IMAP Password: tu_contraseña_de_aplicacion
SMTP Server: smtp.gmail.com
SMTP Port: 587
SMTP User: tucorreo@gmail.com
SMTP Password: tu_contraseña_de_aplicacion
```

**IMPORTANTE para Gmail:** Usa una "Contraseña de Aplicación", no tu contraseña normal:
1. Ve a tu cuenta de Google
2. Seguridad → Verificación en dos pasos (actívala)
3. Seguridad → Contraseñas de aplicaciones
4. Genera una contraseña para "Correo"

### Configuración de Reenvíos

#### Crear Nueva Regla

1. En la pestaña "Configuración de los Reenvíos"
2. Haz clic en "➕ Nueva Regla"
3. Se crea una regla con datos de ejemplo
4. Configura:
   - **Nombre**: Identificador de la regla
   - **Estado**: Activa/Inactiva
   - **Remitentes**: Correos o dominios (uno por línea)
   - **Palabras clave**: Palabras en el asunto (una por línea)
   - **Destinatarios**: A quién reenviar (uno por línea)
   - **Adjuntos**: Marcar si quieres incluir archivos adjuntos

#### Ejemplos de Configuración

**Ejemplo 1: Filtrar por remitente**
```
Nombre: Correos de Francia
Remitentes:
  contacto@empresa-francia.fr
  @dominio-frances.com
Palabras clave: (dejar vacío para cualquier asunto)
Destinatarios:
  gerente@miempresa.com
  comercial@miempresa.com
Incluir adjuntos: No marcado
```

**Ejemplo 2: Filtrar por palabras clave**
```
Nombre: Facturas Urgentes
Remitentes: (dejar vacío para cualquier remitente)
Palabras clave:
  factura
  invoice
  urgent
Destinatarios:
  contabilidad@miempresa.com
Incluir adjuntos: Marcado
```

### Guardar Cambios

**IMPORTANTE:** Después de modificar cualquier configuración, haz clic en:
```
💾 Guardar Configuración
```

Esto enviará todos los cambios al servidor Linux.

### Ver Logs

#### Logs de Reenvíos
- Pestaña "Logs de Reenvíos"
- Muestra todos los correos que se han reenviado
- Formato: `[Fecha] Asunto: ... | Regla: ...`
- Botón "🔄 Actualizar Logs" para recargar

#### Logs de Errores
- Pestaña "Logs de Errores"
- Muestra solo errores del sistema
- Útil para diagnóstico
- Botón "🔄 Actualizar Errores" para recargar

## 🎵 Modo Percebeiro Pro

El botón "Modo Percebeiro Pro" es un easter egg que abre un video musical. Es solo por diversión 😉

## 🔧 Configuración Avanzada

### Archivo de Configuración

El cliente guarda su configuración en `percebe_client_config.json`:

```json
{
    "server_ip": "192.168.1.100",
    "server_port": 5555
}
```

Puedes editarlo manualmente si es necesario.

### Iconos de la Bandeja del Sistema

- **Clic derecho**: Muestra menú con opciones
  - "Abrir Interfaz": Abre la ventana
  - "Salir": Cierra completamente el programa
- **Doble clic**: Abre directamente la interfaz

### Cerrar vs Minimizar

- **X (cerrar ventana)**: Minimiza a la bandeja, NO cierra el programa
- **Salir desde menú**: Cierra completamente

## 🐛 Solución de Problemas

### No puedo conectar al servidor

1. **Verifica que el servidor esté ejecutándose**:
   ```bash
   # En el servidor Linux
   sudo systemctl status percebe
   ```

2. **Verifica la IP**:
   - Desde el servidor Linux: `ip addr` o `hostname -I`
   - Prueba hacer ping desde Windows: `ping IP_SERVIDOR`

3. **Verifica el firewall**:
   - El puerto 5555 debe estar abierto en el servidor
   - En Windows, permite la aplicación en el Firewall

### El icono no aparece en la bandeja

1. Verifica que el programa esté ejecutándose (Task Manager)
2. Comprueba la configuración de iconos ocultos de Windows:
   - Click derecho en la bandeja → "Configuración de la bandeja"
   - Activa "Mostrar siempre todos los iconos"

### Error al compilar con PyInstaller

Si aparecen errores al compilar:

```bash
# Reinstala PyQt5
pip uninstall PyQt5
pip install PyQt5

# Limpia archivos previos
rmdir /s /q build dist
del *.spec

# Compila de nuevo
pyinstaller --onefile --windowed --name "P.E.R.C.E.B.E" percebe_client.py
```

### Los logs no se actualizan

1. Verifica la conexión con el servidor
2. Haz clic en el botón "🔄 Actualizar"
3. Los logs se cargan bajo demanda, no en tiempo real

## 📝 Notas Importantes

1. **El cliente NO procesa correos**, solo gestiona la configuración
2. **Todo el procesamiento ocurre en el servidor Linux**
3. **Múltiples clientes** pueden conectarse al mismo servidor
4. **Los cambios se sincronizan** cuando te conectas al servidor
5. **Guarda siempre** después de hacer cambios

## 🔐 Seguridad

- El archivo de configuración local solo contiene la IP del servidor
- Las contraseñas se almacenan en el servidor, no en el cliente
- La comunicación NO está cifrada por defecto
- **Recomendación**: Usa solo en redes locales confiables

## 🆘 Soporte

Si encuentras problemas:

1. Revisa los logs de errores en el cliente
2. Revisa los logs del servidor:
   ```bash
   sudo journalctl -u percebe -n 50
   ```
3. Verifica la configuración del firewall
4. Prueba la conexión manualmente con telnet:
   ```bash
   telnet IP_SERVIDOR 5555
   ```

## 🎯 Flujo de Trabajo Recomendado

1. **Instala el servidor** en Linux
2. **Configura al menos una cuenta** de correo
3. **Instala el cliente** en Windows
4. **Conéctate y verifica** que todo funciona
5. **Crea reglas de prueba** con correos que sepas que llegarán
6. **Monitorea los logs** para verificar que funciona correctamente
7. **Ajusta las reglas** según necesites

## 🚀 Próximos Pasos

Una vez que el cliente esté funcionando:
1. Configura todas tus cuentas
2. Define todas las reglas de reenvío
3. Prueba enviando correos de prueba
4. Verifica los logs
5. Ajusta según sea necesario

¡Disfruta de P.E.R.C.E.B.E.! 🐚
