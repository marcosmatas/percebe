#!/usr/bin/env python3
"""
P.E.R.C.E.B.E. - Programa de Envío y Redirección de Correos Eliminando Basura Electrónica
Servidor principal para gestión automática de reenvío de correos
"""

import json
import os
import imaplib
import smtplib
import email
import socket
import threading
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import decode_header
from datetime import datetime
from pathlib import Path
from email.mime.base import MIMEBase
from email import encoders


class PercebeServer:
    def __init__(self, config_dir="./percebe_config"):
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "config.json"
        self.log_file = self.config_dir / "reenvios.log"
        self.error_log_file = self.config_dir / "errores.log"
        self.debug_log_file = self.config_dir / "procesamiento.log"
        self.config = {}
        self.running = False
        self.api_port = 5555
        
        # Crear directorio de configuración si no existe
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Cargar o crear configuración
        self.load_config()
    
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
    
    def log_reenvio(self, asunto, regla_nombre):
        """Registra un reenvío en el log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] Asunto: {asunto} | Regla: {regla_nombre}\n"
        
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








    def forward_email(self, cuenta_config, mail_data, regla, include_attachments=False):
        """Reenvía un correo según la regla especificada"""
        try:
            # --- CORRECCIÓN INICIO ---
            # El contenedor principal debe ser 'mixed' si queremos
            # adjuntos Y cuerpos alternativos (texto/html).
            msg = MIMEMultipart('mixed') 
            # --- CORRECCIÓN FIN ---
            
            msg['From'] = cuenta_config['smtp_user']
            msg['To'] = ', '.join(regla['destinatarios'])
            msg['Subject'] = f"FWD: {mail_data['subject']}"
            
            # --- CORRECCIÓN INICIO ---
            # Crear el contenedor 'alternative' para los cuerpos de texto/html
            msg_alternative = MIMEMultipart('alternative')
            # --- CORRECCIÓN FIN ---
            
            # Agregar encabezado indicando el reenvío
            header_info = f"\n\n--- Correo reenviado automáticamente por P.E.R.C.E.B.E. ---\n"
            header_info += f"De: {mail_data['from']}\n"
            header_info += f"Asunto original: {mail_data['subject']}\n"
            header_info += f"Fecha: {mail_data['date']}\n"
            header_info += "---------------------------------------------------\n\n"
            
            # Agregar cuerpos al contenedor 'alternative'
            has_body = False
            if mail_data['body_text']:
                text_part = MIMEText(header_info + mail_data['body_text'], 'plain', 'utf-8')
                msg_alternative.attach(text_part)
                has_body = True
            
            if mail_data['body_html']:
                html_header = header_info.replace('\n', '<br>')
                html_part = MIMEText(html_header + mail_data['body_html'], 'html', 'utf-8')
                msg_alternative.attach(html_part)
                has_body = True

            # Si no hay cuerpo, añadir al menos el header en texto plano
            if not has_body:
                 text_part = MIMEText(header_info, 'plain', 'utf-8')
                 msg_alternative.attach(text_part)

            # --- CORRECCIÓN INICIO ---
            # Adjuntar el contenedor 'alternative' al principal 'mixed'
            msg.attach(msg_alternative)
            # --- CORRECCIÓN FIN ---
            
            # Si la regla especifica incluir adjuntos, adjuntarlos al 'mixed'
            if include_attachments and mail_data.get('attachments'):
                self.log_debug(f"Adjuntando {len(mail_data['attachments'])} archivos al reenvío")
                for attachment in mail_data['attachments']:
                    msg.attach(attachment) # Esto ahora funciona porque 'msg' es 'mixed'
            
            # Enviar correo
            with smtplib.SMTP(cuenta_config['smtp_server'], cuenta_config['smtp_port']) as server:
                server.starttls()
                server.login(cuenta_config['smtp_user'], cuenta_config['smtp_password'])
                server.send_message(msg)
            
            self.log_reenvio(mail_data['subject'], regla['nombre'])
            return True
            
        except Exception as e:
            self.log_error(f"Error al reenviar correo: {e}")
            return False

    






    
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
                    
                    # Obtener cuerpo
                    mail_data['body_text'], mail_data['body_html'], mail_data['attachments'] = self.get_email_body(msg)
                    self.log_debug(f"Adjuntos detectados: {len(mail_data['attachments'])}")

                    # Log de procesamiento inicial
                    self.log_debug(f"--- PROCESANDO CORREO ---")
                    self.log_debug(f"De: {mail_data['from']}")
                    self.log_debug(f"Asunto: {mail_data['subject']}")
                    self.log_debug(f"Fecha: {mail_data['date']}")
                    
                    # Verificar reglas - IMPORTANTE: No usar break, aplicar TODAS las que coincidan
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
        self.log_info("P.E.R.C.E.B.E. iniciado")
        
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