#!/usr/bin/env python3
"""
P.E.R.C.E.B.E. - Programa de Envío y Redirección de Correos Eliminando Basura Electrónica
Servidor principal para gestión automática de reenvío de correos
Versión 2.1 - Con sistema de reintentos y cola persistente
"""

import json
import os
import imaplib
import smtplib
import email
import socket
import threading
import time
import random
import string
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import decode_header
from email.utils import formatdate
from datetime import datetime
from pathlib import Path
from email.mime.base import MIMEBase
from email import encoders


class PercebeServer:
    # Marca especial para detectar reenvíos (ΡCΒ: con espacio alt+255)
    REENVIO_MARKER = "ΡCΒ: "  # Rho griega C y Beta griega + dos puntos + espacio alt+255
    DELAY_ENTRE_ENVIOS = 3  # Segundos de espera entre envíos a distintos destinatarios
    
    # Configuración de reintentos
    MAX_REINTENTOS = 50  # Máximo número de reintentos por correo
    REINTENTO_BASE_DELAY = 60  # Segundos base para el primer reintento (1 min)
    REINTENTO_MAX_DELAY = 3600  # Máximo delay entre reintentos (1 hora)
    
    def __init__(self, config_dir="./percebe_config"):
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "config.json"
        self.log_file = self.config_dir / "reenvios.log"
        self.error_log_file = self.config_dir / "errores.log"
        self.debug_log_file = self.config_dir / "procesamiento.log"
        self.retry_queue_file = self.config_dir / "cola_reintentos.json"
        self.config = {}
        self.running = False
        self.api_port = 5555
        self.retry_queue = []
        
        # Crear directorio de configuración si no existe
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Cargar o crear configuración
        self.load_config()
        self.load_retry_queue()
    
    def load_config(self):
        """Carga la configuración desde el archivo JSON o crea uno vacío"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                self.log_info("Configuración cargada correctamente")
            except Exception as e:
                self.log_error(f"Error al cargar configuración: {e}")
                self.config = self._default_config()
        else:
            self.config = self._default_config()
            self.save_config()
            self.log_info("Archivo de configuración creado")
    
    def _default_config(self):
        """Estructura por defecto de la configuración"""
        return {
            "cuentas": [],
            "intervalo_revision": 60,  # segundos entre revisiones
            "api_enabled": True,
            "api_port": 5555,
            "logs_completos": False  # Si está activado, registra detalles de procesamiento
        }
    
    def save_config(self):
        """Guarda la configuración en el archivo JSON"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, indent=4, fp=f, ensure_ascii=False)
            return True
        except Exception as e:
            self.log_error(f"Error al guardar configuración: {e}")
            return False
    
    def load_retry_queue(self):
        """Carga la cola de reintentos desde el archivo JSON"""
        if self.retry_queue_file.exists():
            try:
                with open(self.retry_queue_file, 'r', encoding='utf-8') as f:
                    self.retry_queue = json.load(f)
                if self.retry_queue:
                    self.log_info(f"Cola de reintentos cargada: {len(self.retry_queue)} correos pendientes")
            except Exception as e:
                self.log_error(f"Error al cargar cola de reintentos: {e}")
                self.retry_queue = []
        else:
            self.retry_queue = []
    
    def save_retry_queue(self):
        """Guarda la cola de reintentos en el archivo JSON"""
        try:
            with open(self.retry_queue_file, 'w', encoding='utf-8') as f:
                json.dump(self.retry_queue, indent=4, fp=f, ensure_ascii=False)
            return True
        except Exception as e:
            self.log_error(f"Error al guardar cola de reintentos: {e}")
            return False
    
    def add_to_retry_queue(self, cuenta_config, mail_data, regla, destinatario, include_attachments=False):
        """Añade un correo a la cola de reintentos"""
        retry_item = {
            'cuenta_config': cuenta_config,
            'mail_data': mail_data,
            'regla': regla,
            'destinatario': destinatario,
            'include_attachments': include_attachments,
            'intentos': 0,
            'proximo_intento': time.time() + self.REINTENTO_BASE_DELAY,
            'timestamp_creacion': datetime.now().isoformat()
        }
        
        self.retry_queue.append(retry_item)
        self.save_retry_queue()
        self.log_info(f"Correo añadido a cola de reintentos: {mail_data['subject']} -> {destinatario}")
    
    def process_retry_queue(self):
        """Procesa la cola de reintentos"""
        if not self.retry_queue:
            return
        
        self.log_debug(f"Procesando cola de reintentos: {len(self.retry_queue)} items")
        
        now = time.time()
        items_to_remove = []
        items_to_update = []
        
        for i, item in enumerate(self.retry_queue):
            # Verificar si es momento de reintentar
            if item['proximo_intento'] > now:
                continue
            
            self.log_debug(f"Reintentando envío (intento {item['intentos'] + 1}/{self.MAX_REINTENTOS}): {item['mail_data']['subject']} -> {item['destinatario']}")
            
            # Intentar reenviar
            success = self.forward_email_single(
                item['cuenta_config'],
                item['mail_data'],
                item['regla'],
                item['destinatario'],
                item['include_attachments']
            )
            
            if success:
                # Éxito: marcar para eliminar de la cola
                items_to_remove.append(i)
                self.log_info(f"Reintento exitoso: {item['mail_data']['subject']} -> {item['destinatario']}")
            else:
                # Fallo: incrementar contador de intentos
                item['intentos'] += 1
                
                if item['intentos'] >= self.MAX_REINTENTOS:
                    # Máximo de reintentos alcanzado: eliminar y registrar error
                    items_to_remove.append(i)
                    self.log_error(f"Máximo de reintentos alcanzado para: {item['mail_data']['subject']} -> {item['destinatario']}")
                else:
                    # Calcular próximo intento con backoff exponencial
                    delay = min(
                        self.REINTENTO_BASE_DELAY * (2 ** item['intentos']),
                        self.REINTENTO_MAX_DELAY
                    )
                    item['proximo_intento'] = now + delay
                    items_to_update.append(i)
                    
                    proximo_str = datetime.fromtimestamp(item['proximo_intento']).strftime("%H:%M:%S")
                    self.log_info(f"Reintento fallido. Próximo intento a las {proximo_str} (delay: {delay}s)")
        
        # Eliminar items completados o que excedieron reintentos
        for i in sorted(items_to_remove, reverse=True):
            del self.retry_queue[i]
        
        # Guardar cola actualizada si hubo cambios
        if items_to_remove or items_to_update:
            self.save_retry_queue()
            self.log_debug(f"Cola de reintentos actualizada: {len(self.retry_queue)} items restantes")
    
    def log_reenvio(self, asunto, regla_nombre, destinatario):
        """Registra un reenvío en el log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] Asunto: {asunto} | Regla: {regla_nombre} | Destinatario: {destinatario}\n"
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            self.log_error(f"Error al escribir log de reenvío: {e}")
    
    def log_error(self, mensaje):
        """Registra un error en el log de errores"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] ERROR: {mensaje}\n"
        
        try:
            with open(self.error_log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Error crítico al escribir log de errores: {e}")
    
    def log_info(self, mensaje):
        """Imprime información en consola (para systemd journal)"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] INFO: {mensaje}")
    
    def log_debug(self, mensaje):
        """Registra información de debug/procesamiento detallado"""
        if not self.config.get('logs_completos', False):
            return
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] DEBUG: {mensaje}\n"
        
        try:
            with open(self.debug_log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Error al escribir log de debug: {e}")
    
    def decode_mime_header(self, header):
        """Decodifica headers MIME codificados"""
        if header is None:
            return ""
        
        decoded_parts = decode_header(header)
        result = []
        
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                try:
                    result.append(part.decode(encoding or 'utf-8', errors='ignore'))
                except:
                    result.append(part.decode('utf-8', errors='ignore'))
            else:
                result.append(part)
        
        return ''.join(result)
    
    def is_autoforward_loop(self, subject):
        """
        Detecta si un correo es parte de un bucle de reenvío automático
        comprobando si contiene la marcaΡCΒ: 
        """
        if self.REENVIO_MARKER in subject:
            self.log_debug(f"Detectado bucle de reenvío: asunto contiene marca '{self.REENVIO_MARKER}'")
            self.log_info(f"Correo descartado por bucle de reenvío: {subject}")
            return True
        return False
    
    def check_rule_match(self, mail_data, regla):
        """Verifica si un correo coincide con una regla"""
        # Verificar remitente (si hay remitentes especificados)
        remitentes_config = regla.get("remitentes", [])
        
        # Si la lista está vacía o no existe, se acepta cualquier remitente
        if remitentes_config:
            remitente_match = False
            for rem in remitentes_config:
                if rem.lower() in mail_data["from"].lower():
                    remitente_match = True
                    self.log_debug(f"Regla '{regla.get('nombre')}': Remitente coincide con '{rem}'")
                    break
            
            if not remitente_match:
                self.log_debug(f"Regla '{regla.get('nombre')}': Remitente '{mail_data['from']}' NO coincide con ninguno configurado")
                return False
        else:
            self.log_debug(f"Regla '{regla.get('nombre')}': Sin filtro de remitentes (acepta cualquiera)")
        
        # Verificar palabras clave en asunto (si hay palabras especificadas)
        palabras_config = regla.get("palabras_clave", [])
        
        # Si la lista está vacía o no existe, se acepta cualquier asunto
        if palabras_config:
            asunto_lower = mail_data["subject"].lower()
            keyword_match = False
            for keyword in palabras_config:
                if keyword.lower() in asunto_lower:
                    keyword_match = True
                    self.log_debug(f"Regla '{regla.get('nombre')}': Palabra clave '{keyword}' encontrada en asunto")
                    break
            
            if not keyword_match:
                self.log_debug(f"Regla '{regla.get('nombre')}': Asunto '{mail_data['subject']}' NO contiene ninguna palabra clave")
                return False
        else:
            self.log_debug(f"Regla '{regla.get('nombre')}': Sin filtro de palabras clave (acepta cualquier asunto)")
        
        self.log_debug(f"Regla '{regla.get('nombre')}': COINCIDE con el correo")
        return True

    def get_email_body(self, msg):
        """Extrae el cuerpo del correo (texto plano, HTML y adjuntos)"""
        body_text = ""
        body_html = ""
        attachments = []

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                # Si es adjunto
                if "attachment" in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        try:
                            # Decodificar nombre (por si tiene caracteres MIME)
                            decoded_name = self.decode_mime_header(filename)
                            payload = part.get_payload(decode=True)
                            if payload:
                                # Crear objeto MIME para reenviar
                                attachment = MIMEBase(part.get_content_maintype(), part.get_content_subtype())
                                attachment.set_payload(payload)
                                encoders.encode_base64(attachment)
                                attachment.add_header('Content-Disposition', 'attachment', filename=decoded_name)
                                attachments.append(attachment)
                        except Exception as e:
                            self.log_error(f"Error al procesar adjunto '{filename}': {e}")
                    continue
    
                # Si no es adjunto, procesar cuerpo
                if content_type == "text/plain" and not body_text:
                    try:
                        body_text = part.get_payload(decode=True).decode(errors='ignore')
                    except Exception as e:
                        self.log_error(f"Error decodificando cuerpo de texto: {e}")
    
                elif content_type == "text/html" and not body_html:
                    try:
                        body_html = part.get_payload(decode=True).decode(errors='ignore')
                    except Exception as e:
                        self.log_error(f"Error decodificando cuerpo HTML: {e}")
    
        else:
            # Mensaje no multipart
            content_type = msg.get_content_type()
            if content_type == "text/plain":
                try:
                    body_text = msg.get_payload(decode=True).decode(errors='ignore')
                except:
                    pass
            elif content_type == "text/html":
                try:
                    body_html = msg.get_payload(decode=True).decode(errors='ignore')
                except:
                    pass

        return body_text, body_html, attachments

    def forward_email_single(self, cuenta_config, mail_data, regla, destinatario, include_attachments=False):
        """
        Reenvía un correo a UN SOLO destinatario
        Versión 2.1 - Con manejo de errores de conexión
        """
        try:
            msg = MIMEMultipart('mixed') 
            
            # ===== CABECERAS CRÍTICAS ANTI-SPAM =====
            msg['From'] = cuenta_config['smtp_user']
            msg['To'] = destinatario
            
            # 1. Message-ID (CRÍTICO - elimina ~4.29 puntos de spam)
            domain = cuenta_config['smtp_user'].split('@')[-1]
            random_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))
            timestamp = int(time.time())
            msg['Message-ID'] = f"<{random_id}.{timestamp}@{domain}>"
            
            # 2. Date (CRÍTICO - elimina ~1.36 puntos de spam)
            msg['Date'] = formatdate(localtime=True)
            
            # 3. Asunto con marca de reenvío
            msg['Subject'] = f"{self.REENVIO_MARKER}{mail_data['subject']}"
            
            # 4. Cabeceras adicionales recomendadas
            msg['MIME-Version'] = '1.0'
            msg['X-Mailer'] = 'P.E.R.C.E.B.E. v2.1'
            
            # 5. Cabeceras de procedencia (ayudan a la trazabilidad)
            msg['X-Forwarded-From'] = mail_data['from']
            msg['X-Original-Date'] = mail_data['date']
            
            # ===== CONSTRUCCIÓN DEL CUERPO (MEJORADA) =====
            # Crear el contenedor 'alternative' para texto/HTML
            msg_alternative = MIMEMultipart('alternative')
            
            # Encabezado de reenvío (versión completa del nombre del programa)
            header_info = f"\n\n--- Correo reenviado automáticamente por Programa de Envío y Redirección de Correo Eliminando Basura Electrónica ---\n"
            header_info += f"De: {mail_data['from']}\n"
            header_info += f"Asunto original: {mail_data['subject']}\n"
            header_info += f"Fecha: {mail_data['date']}\n"
            header_info += "---------------------------------------------------\n\n"
            
            # Agregar cuerpos al contenedor 'alternative'
            has_body = False
            
            if mail_data['body_text']:
                # Normalizar saltos de línea (evita DOS_BODY_HIGH)
                body_text_clean = mail_data['body_text'].replace('\r\n', '\n').replace('\r', '\n')
                text_part = MIMEText(header_info + body_text_clean, 'plain', 'utf-8')
                msg_alternative.attach(text_part)
                has_body = True
            
            if mail_data['body_html']:
                html_header = header_info.replace('\n', '<br>')
                # Asegurar que el HTML esté bien formado
                html_body = mail_data['body_html']
                if not html_body.strip().startswith('<'):
                    html_body = f"<html><body>{html_header}{html_body}</body></html>"
                else:
                    html_body = html_header + html_body
                
                html_part = MIMEText(html_body, 'html', 'utf-8')
                msg_alternative.attach(html_part)
                has_body = True

            # Si no hay cuerpo, añadir al menos el header
            if not has_body:
                text_part = MIMEText(header_info, 'plain', 'utf-8')
                msg_alternative.attach(text_part)

            # Adjuntar el contenedor 'alternative' al principal 'mixed'
            msg.attach(msg_alternative)
            
            # Si la regla especifica incluir adjuntos, adjuntarlos al 'mixed'
            if include_attachments and mail_data.get('attachments'):
                for attachment in mail_data['attachments']:
                    msg.attach(attachment)
            
            # ===== ENVÍO CON MANEJO MEJORADO =====
            with smtplib.SMTP(cuenta_config['smtp_server'], cuenta_config['smtp_port'], timeout=30) as server:
                server.starttls()
                server.login(cuenta_config['smtp_user'], cuenta_config['smtp_password'])
                server.send_message(msg)
            
            self.log_reenvio(mail_data['subject'], regla['nombre'], destinatario)
            return True
            
        except (smtplib.SMTPException, socket.error, OSError, TimeoutError) as e:
            # Errores de red/conexión: estos justifican reintento
            self.log_error(f"Error de conexión al reenviar correo a {destinatario}: {e}")
            return False
        except Exception as e:
            # Otros errores: registrar pero no reintentar
            self.log_error(f"Error al reenviar correo a {destinatario}: {e}")
            return False

    def forward_email(self, cuenta_config, mail_data, regla, include_attachments=False):
        """
        Reenvía un correo según la regla especificada
        Envía a cada destinatario por separado con delay de 3 segundos entre cada uno
        Versión 2.1 - Añade a cola de reintentos si falla
        """
        destinatarios = regla.get('destinatarios', [])
        
        if not destinatarios:
            self.log_error(f"Regla '{regla['nombre']}' no tiene destinatarios configurados")
            return False
        
        total_enviados = 0
        total_errores = 0
        
        self.log_debug(f"Iniciando reenvío a {len(destinatarios)} destinatarios con delay de {self.DELAY_ENTRE_ENVIOS}s")
        
        for i, destinatario in enumerate(destinatarios):
            self.log_debug(f"Enviando a destinatario {i+1}/{len(destinatarios)}: {destinatario}")
            
            if self.forward_email_single(cuenta_config, mail_data, regla, destinatario, include_attachments):
                total_enviados += 1
                self.log_info(f"Correo reenviado a {destinatario} - Regla '{regla['nombre']}'")
            else:
                total_errores += 1
                self.log_error(f"Fallo al reenviar a {destinatario}, añadiendo a cola de reintentos")
                # Añadir a cola de reintentos
                self.add_to_retry_queue(cuenta_config, mail_data, regla, destinatario, include_attachments)
            
            # Esperar entre envíos (excepto después del último)
            if i < len(destinatarios) - 1:
                self.log_debug(f"Esperando {self.DELAY_ENTRE_ENVIOS} segundos antes del siguiente envío...")
                time.sleep(self.DELAY_ENTRE_ENVIOS)
        
        self.log_debug(f"Reenvío completado: {total_enviados} exitosos, {total_errores} errores")
        
        # Retornar True si al menos un envío fue exitoso
        return total_enviados > 0
    
    def process_mailbox(self, cuenta_config):
        """Procesa una cuenta de correo"""
        try:
            # Conectar a IMAP
            mail = imaplib.IMAP4_SSL(cuenta_config['imap_server'])
            mail.login(cuenta_config['imap_user'], cuenta_config['imap_password'])
            mail.select('INBOX')
            
            # Buscar todos los correos no leídos
            status, messages = mail.search(None, 'UNSEEN')
            
            if status != 'OK':
                return
            
            mail_ids = messages[0].split()
            
            for mail_id in mail_ids:
                try:
                    # Obtener correo
                    status, msg_data = mail.fetch(mail_id, '(RFC822)')
                    
                    if status != 'OK':
                        continue
                    
                    # Parsear correo
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    
                    # Extraer información
                    mail_data = {
                        'from': self.decode_mime_header(msg.get('From', '')),
                        'subject': self.decode_mime_header(msg.get('Subject', '')),
                        'date': msg.get('Date', ''),
                        'body_text': '',
                        'body_html': '',
                        'attachments': []
                    }
                    
                    # Log de procesamiento inicial
                    self.log_debug(f"--- PROCESANDO CORREO ---")
                    self.log_debug(f"De: {mail_data['from']}")
                    self.log_debug(f"Asunto: {mail_data['subject']}")
                    self.log_debug(f"Fecha: {mail_data['date']}")
                    
                    # COMPROBAR BUCLE DE REENVÍO ANTES DE CUALQUIER PROCESAMIENTO
                    if self.is_autoforward_loop(mail_data['subject']):
                        self.log_debug(f"Correo descartado por bucle de autorrespuesta")
                        # Eliminar correo del servidor
                        mail.store(mail_id, '+FLAGS', '\\Deleted')
                        self.log_debug(f"Correo marcado para eliminación")
                        self.log_debug(f"--- FIN PROCESAMIENTO ---\n")
                        continue  # Pasar al siguiente correo
                    
                    # Obtener cuerpo (solo si no es bucle)
                    mail_data['body_text'], mail_data['body_html'], mail_data['attachments'] = self.get_email_body(msg)
                    self.log_debug(f"Adjuntos detectados: {len(mail_data['attachments'])}")
                    
                    # Verificar reglas - Aplicar TODAS las que coincidan
                    reglas_activas = [r for r in cuenta_config.get('reglas', []) if r.get('activa', True)]
                    
                    self.log_debug(f"Evaluando {len(reglas_activas)} reglas activas")
                    
                    reglas_aplicadas = 0
                    for regla in reglas_activas:
                        self.log_debug(f"Evaluando regla: '{regla.get('nombre', 'sin nombre')}'")
                        
                        if self.check_rule_match(mail_data, regla):
                            # Aplicar regla
                            include_attachments = regla.get('incluir_adjuntos', False)
                            
                            self.log_debug(f"Aplicando regla '{regla['nombre']}' (adjuntos: {include_attachments})")
                            
                            if self.forward_email(cuenta_config, mail_data, regla, include_attachments):
                                self.log_info(f"Regla '{regla['nombre']}' aplicada: {mail_data['subject']}")
                                self.log_debug(f"Correo reenviado exitosamente")
                                reglas_aplicadas += 1
                            else:
                                self.log_debug(f"Error al reenviar correo con regla '{regla['nombre']}'")
                        # NO USAR BREAK - continuar evaluando el resto de reglas
                    
                    if reglas_aplicadas == 0:
                        self.log_debug(f"Ninguna regla coincidió con este correo")
                    else:
                        self.log_debug(f"Total de reglas aplicadas: {reglas_aplicadas}")
                    
                    # Eliminar correo del servidor
                    mail.store(mail_id, '+FLAGS', '\\Deleted')
                    self.log_debug(f"Correo marcado para eliminación")
                    self.log_debug(f"--- FIN PROCESAMIENTO ---\n")
                    
                except Exception as e:
                    self.log_error(f"Error procesando correo individual: {e}")
            
            # Expunge para eliminar permanentemente
            mail.expunge()
            mail.close()
            mail.logout()
            
        except Exception as e:
            self.log_error(f"Error procesando buzón '{cuenta_config.get('nombre', 'desconocida')}': {e}")
    
    def run_check_cycle(self):
        """Ejecuta un ciclo de revisión de todas las cuentas"""
        self.log_info("Iniciando ciclo de revisión de correos")
        
        # Primero procesar la cola de reintentos
        self.process_retry_queue()
        
        # Luego revisar nuevos correos
        for cuenta in self.config.get('cuentas', []):
            if cuenta.get('activa', True):
                self.log_info(f"Revisando cuenta: {cuenta.get('nombre', 'sin nombre')}")
                self.process_mailbox(cuenta)
        
        self.log_info("Ciclo de revisión completado")
    
    def start_api_server(self):
        """Inicia el servidor API para comunicación con el cliente Windows"""
        def handle_client(client_socket):
            try:
                # Recibir datos en chunks para evitar truncamiento con configs grandes
                chunks = []
                client_socket.settimeout(5)  # Timeout de 5 segundos (más robusto)
                
                while True:
                    try:
                        chunk = client_socket.recv(4096)
                        if not chunk:
                            break
                        chunks.append(chunk)
                        
                        # Si el chunk es menor que 4096, probablemente sea el último
                        if len(chunk) < 4096:
                            break
                    except socket.timeout:
                        # Si llevamos datos y hay timeout, asumimos que terminó
                        if chunks:
                            break
                        raise
                
                request = b''.join(chunks).decode('utf-8')
                data = json.loads(request)
                
                command = data.get('command')
                response = {'status': 'error', 'message': 'Comando desconocido'}
                
                if command == 'get_config':
                    response = {'status': 'ok', 'data': self.config}
                
                elif command == 'set_config':
                    self.config = data.get('config', self.config)
                    if self.save_config():
                        response = {'status': 'ok', 'message': 'Configuración guardada'}
                    else:
                        response = {'status': 'error', 'message': 'Error al guardar'}
                
                elif command == 'get_logs':
                    log_type = data.get('log_type', 'reenvios')
                    
                    if log_type == 'reenvios':
                        log_file = self.log_file
                    elif log_type == 'errores':
                        log_file = self.error_log_file
                    elif log_type == 'procesamiento':
                        log_file = self.debug_log_file
                    else:
                        log_file = self.log_file
                    
                    if log_file.exists():
                        with open(log_file, 'r', encoding='utf-8') as f:
                            logs = f.readlines()
                        response = {'status': 'ok', 'data': logs}
                    else:
                        response = {'status': 'ok', 'data': []}
                
                elif command == 'get_retry_queue':
                    # Nuevo comando para ver la cola de reintentos
                    queue_info = []
                    for item in self.retry_queue:
                        queue_info.append({
                            'asunto': item['mail_data']['subject'],
                            'destinatario': item['destinatario'],
                            'intentos': item['intentos'],
                            'proximo_intento': datetime.fromtimestamp(item['proximo_intento']).isoformat(),
                            'timestamp_creacion': item['timestamp_creacion']
                        })
                    response = {'status': 'ok', 'data': queue_info}
                
                elif command == 'test_connection':
                    cuenta_id = data.get('cuenta_id')
                    if cuenta_id is not None and cuenta_id < len(self.config.get('cuentas', [])):
                        cuenta = self.config['cuentas'][cuenta_id]
                        try:
                            mail = imaplib.IMAP4_SSL(cuenta['imap_server'])
                            mail.login(cuenta['imap_user'], cuenta['imap_password'])
                            mail.logout()
                            response = {'status': 'ok', 'message': 'Conexión exitosa'}
                        except Exception as e:
                            response = {'status': 'error', 'message': str(e)}
                
                # Enviar respuesta (también en chunks si es grande)
                response_json = json.dumps(response).encode('utf-8')
                client_socket.sendall(response_json)
                
            except Exception as e:
                error_response = {'status': 'error', 'message': str(e)}
                try:
                    client_socket.sendall(json.dumps(error_response).encode('utf-8'))
                except:
                    pass
            
            finally:
                try:
                    client_socket.close()
                except:
                    pass
        
        # Servidor TCP
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('0.0.0.0', self.config.get('api_port', self.api_port)))
        server.listen(5)
        
        self.log_info(f"Servidor API iniciado en puerto {self.config.get('api_port', self.api_port)}")
        
        while self.running:
            try:
                server.settimeout(1.0)
                client_socket, address = server.accept()
                client_thread = threading.Thread(target=handle_client, args=(client_socket,))
                client_thread.daemon = True
                client_thread.start()
            except socket.timeout:
                continue
            except Exception as e:
                self.log_error(f"Error en servidor API: {e}")
        
        server.close()
    
    def start(self):
        """Inicia el servidor P.E.R.C.E.B.E."""
        self.running = True
        self.log_info("P.E.R.C.E.B.E. v2.1 iniciado")
        
        # Iniciar servidor API en hilo separado
        if self.config.get('api_enabled', True):
            api_thread = threading.Thread(target=self.start_api_server)
            api_thread.daemon = True
            api_thread.start()
        
        # Bucle principal
        try:
            while self.running:
                self.run_check_cycle()
                intervalo = self.config.get('intervalo_revision', 60)
                time.sleep(intervalo)
        except KeyboardInterrupt:
            self.log_info("P.E.R.C.E.B.E. detenido por usuario")
        except Exception as e:
            self.log_error(f"Error crítico: {e}")
        finally:
            self.running = False
    
    def stop(self):
        """Detiene el servidor"""
        self.running = False


def main():
    """Función principal"""
    server = PercebeServer()
    server.start()


if __name__ == "__main__":
    main()
