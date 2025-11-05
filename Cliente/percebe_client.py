#!/usr/bin/env python3
"""
P.E.R.C.E.B.E. - Cliente Windows
Programa de Envío y Redirección de Correos Eliminando Basura Electrónica
"""

import sys
import json
import socket
import webbrowser
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QTabWidget, QTextEdit,
    QMessageBox, QSystemTrayIcon, QMenu, QAction, QFormLayout,
    QGroupBox, QScrollArea, QCheckBox, QListWidget, QSpinBox,
    QSplitter
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont, QPixmap, QPainter, QColor


class PercebeClient:
    """Clase para manejar la comunicación con el servidor"""
    
    def __init__(self, server_ip, server_port=5555):
        self.server_ip = server_ip
        self.server_port = server_port
    
    def send_command(self, command_data):
        """Envía un comando al servidor y recibe la respuesta"""
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(5)
            client_socket.connect((self.server_ip, self.server_port))
            
            # Enviar comando
            request = json.dumps(command_data).encode('utf-8')
            client_socket.send(request)
            
            # Recibir respuesta
            response = b''
            while True:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                response += chunk
                try:
                    # Intentar parsear para ver si ya está completo
                    json.loads(response.decode('utf-8'))
                    break
                except:
                    continue
            
            client_socket.close()
            return json.loads(response.decode('utf-8'))
        
        except Exception as e:
            return {'status': 'error', 'message': f'Error de conexión: {str(e)}'}
    
    def get_config(self):
        """Obtiene la configuración del servidor"""
        return self.send_command({'command': 'get_config'})
    
    def set_config(self, config):
        """Establece la configuración en el servidor"""
        return self.send_command({'command': 'set_config', 'config': config})
    
    def get_logs(self, log_type='reenvios'):
        """Obtiene los logs del servidor"""
        return self.send_command({'command': 'get_logs', 'log_type': log_type})
    
    def test_connection(self, cuenta_id=None):
        """Prueba la conexión con una cuenta"""
        return self.send_command({'command': 'test_connection', 'cuenta_id': cuenta_id})


class MainWindow(QMainWindow):
    """Ventana principal de la aplicación"""
    
    def __init__(self):
        super().__init__()
        self.config_file = Path("percebe_client_config.json")
        self.client_config = self.load_client_config()
        self.client = None
        self.server_config = None
        self.current_account_index = None
        
        self.init_ui()
        self.setup_tray_icon()
    
    def load_client_config(self):
        """Carga la configuración del cliente"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {'server_ip': '127.0.0.1', 'server_port': 5555}
    
    def save_client_config(self):
        """Guarda la configuración del cliente"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.client_config, f, indent=4)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al guardar configuración: {e}")
    
    def init_ui(self):
        """Inicializa la interfaz de usuario"""
        self.setWindowTitle("P.E.R.C.E.B.E. - Cliente de Gestión")
        self.setMinimumSize(1000, 700)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Encabezado
        self.create_header(layout)
        
        # Barra de conexión
        self.create_connection_bar(layout)
        
        # Selector de cuenta
        self.create_account_selector(layout)
        
        # Pestañas principales
        self.tabs = QTabWidget()
        self.tabs.setEnabled(False)
        layout.addWidget(self.tabs)
        
        # Crear las pestañas
        self.create_config_tab()
        self.create_rules_tab()
        self.create_logs_tab()
        self.create_errors_tab()
        
        # Aplicar estilos
        self.apply_styles()
    
    def create_header(self, layout):
        """Crea el encabezado de la aplicación"""
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 10)
        
        # Título
        title_layout = QVBoxLayout()
        title = QLabel("🐚 P.E.R.C.E.B.E.")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title_layout.addWidget(title)
        
        subtitle = QLabel("Programa de Envío y Redirección de Correos Eliminando Basura Electrónica")
        subtitle.setFont(QFont("Arial", 10))
        subtitle.setStyleSheet("color: #666;")
        title_layout.addWidget(subtitle)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        # Botón Percebeiro Pro
        btn_pro = QPushButton("🎵 Modo Percebeiro Pro")
        btn_pro.setFixedHeight(40)
        btn_pro.setCursor(Qt.PointingHandCursor)
        btn_pro.clicked.connect(self.activate_percebeiro_pro)
        header_layout.addWidget(btn_pro)
        
        layout.addWidget(header)
    
    def create_connection_bar(self, layout):
        """Crea la barra de conexión con el servidor"""
        conn_group = QGroupBox("Conexión con Servidor")
        conn_layout = QHBoxLayout()
        
        conn_layout.addWidget(QLabel("IP del Servidor:"))
        
        self.ip_input = QLineEdit()
        self.ip_input.setText(self.client_config.get('server_ip', '127.0.0.1'))
        self.ip_input.setPlaceholderText("192.168.1.100")
        self.ip_input.setMaximumWidth(150)
        conn_layout.addWidget(self.ip_input)
        
        conn_layout.addWidget(QLabel("Puerto:"))
        
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(self.client_config.get('server_port', 5555))
        self.port_input.setMaximumWidth(80)
        conn_layout.addWidget(self.port_input)
        
        btn_test = QPushButton("🔌 Probar Conexión")
        btn_test.clicked.connect(self.test_server_connection)
        conn_layout.addWidget(btn_test)
        
        btn_connect = QPushButton("✓ Conectar")
        btn_connect.clicked.connect(self.connect_to_server)
        btn_connect.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        conn_layout.addWidget(btn_connect)
        
        conn_layout.addStretch()
        conn_group.setLayout(conn_layout)
        layout.addWidget(conn_group)
    
    def create_account_selector(self, layout):
        """Crea el selector de cuentas"""
        account_group = QGroupBox("Selección de Cuenta")
        account_layout = QHBoxLayout()
        
        account_layout.addWidget(QLabel("Cuenta:"))
        
        self.account_combo = QComboBox()
        self.account_combo.setEnabled(False)
        self.account_combo.currentIndexChanged.connect(self.on_account_selected)
        account_layout.addWidget(self.account_combo, 1)
        
        btn_new = QPushButton("➕ Nueva Cuenta")
        btn_new.setEnabled(False)
        btn_new.clicked.connect(self.create_new_account)
        self.btn_new_account = btn_new
        account_layout.addWidget(btn_new)
        
        btn_save = QPushButton("💾 Guardar Configuración")
        btn_save.setEnabled(False)
        btn_save.clicked.connect(self.save_configuration)
        btn_save.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        self.btn_save_config = btn_save
        account_layout.addWidget(btn_save)
        
        account_group.setLayout(account_layout)
        layout.addWidget(account_group)
    
    def create_config_tab(self):
        """Crea la pestaña de configuración de cuenta"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Scroll area para todo el contenido
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # Información general
        general_group = QGroupBox("Información General")
        general_layout = QFormLayout()
        
        self.account_name_input = QLineEdit()
        self.account_name_input.setPlaceholderText("Ej: Cuenta Principal")
        general_layout.addRow("Nombre de la cuenta:", self.account_name_input)
        
        self.account_active_check = QCheckBox("Cuenta activa")
        self.account_active_check.setChecked(True)
        general_layout.addRow("Estado:", self.account_active_check)
        
        general_group.setLayout(general_layout)
        scroll_layout.addWidget(general_group)
        
        # Configuración IMAP
        imap_group = QGroupBox("Configuración IMAP (Recepción)")
        imap_layout = QFormLayout()
        
        self.imap_server_input = QLineEdit()
        self.imap_server_input.setPlaceholderText("imap.gmail.com")
        imap_layout.addRow("Servidor IMAP:", self.imap_server_input)
        
        self.imap_user_input = QLineEdit()
        self.imap_user_input.setPlaceholderText("usuario@gmail.com")
        imap_layout.addRow("Usuario:", self.imap_user_input)
        
        self.imap_password_input = QLineEdit()
        self.imap_password_input.setEchoMode(QLineEdit.Password)
        self.imap_password_input.setPlaceholderText("contraseña o app password")
        imap_layout.addRow("Contraseña:", self.imap_password_input)
        
        imap_group.setLayout(imap_layout)
        scroll_layout.addWidget(imap_group)
        
        # Configuración SMTP
        smtp_group = QGroupBox("Configuración SMTP (Envío)")
        smtp_layout = QFormLayout()
        
        self.smtp_server_input = QLineEdit()
        self.smtp_server_input.setPlaceholderText("smtp.gmail.com")
        smtp_layout.addRow("Servidor SMTP:", self.smtp_server_input)
        
        self.smtp_port_input = QSpinBox()
        self.smtp_port_input.setRange(1, 65535)
        self.smtp_port_input.setValue(587)
        smtp_layout.addRow("Puerto SMTP:", self.smtp_port_input)
        
        self.smtp_user_input = QLineEdit()
        self.smtp_user_input.setPlaceholderText("usuario@gmail.com")
        smtp_layout.addRow("Usuario:", self.smtp_user_input)
        
        self.smtp_password_input = QLineEdit()
        self.smtp_password_input.setEchoMode(QLineEdit.Password)
        self.smtp_password_input.setPlaceholderText("contraseña o app password")
        smtp_layout.addRow("Contraseña:", self.smtp_password_input)
        
        smtp_group.setLayout(smtp_layout)
        scroll_layout.addWidget(smtp_group)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        self.tabs.addTab(tab, "Configuración de la Cuenta")
        self.config_widgets = {
            'name': self.account_name_input,
            'active': self.account_active_check,
            'imap_server': self.imap_server_input,
            'imap_user': self.imap_user_input,
            'imap_password': self.imap_password_input,
            'smtp_server': self.smtp_server_input,
            'smtp_port': self.smtp_port_input,
            'smtp_user': self.smtp_user_input,
            'smtp_password': self.smtp_password_input
        }
    
    def create_rules_tab(self):
        """Crea la pestaña de configuración de reenvíos"""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        
        # Panel izquierdo - Lista de reglas
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        left_layout.addWidget(QLabel("Reglas de Reenvío:"))
        
        self.rules_list = QListWidget()
        self.rules_list.currentRowChanged.connect(self.on_rule_selected)
        left_layout.addWidget(self.rules_list)
        
        btn_new_rule = QPushButton("➕ Nueva Regla")
        btn_new_rule.clicked.connect(self.create_new_rule)
        left_layout.addWidget(btn_new_rule)
        
        btn_delete_rule = QPushButton("🗑️ Eliminar Regla")
        btn_delete_rule.clicked.connect(self.delete_rule)
        left_layout.addWidget(btn_delete_rule)
        
        # Panel derecho - Configuración de la regla
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # Información general de la regla
        rule_general = QGroupBox("Información General")
        rule_general_layout = QFormLayout()
        
        self.rule_name_input = QLineEdit()
        self.rule_name_input.setPlaceholderText("Ej: Reenvíos de Francia")
        rule_general_layout.addRow("Nombre:", self.rule_name_input)
        
        self.rule_active_check = QCheckBox("Regla activa")
        self.rule_active_check.setChecked(True)
        rule_general_layout.addRow("Estado:", self.rule_active_check)
        
        self.rule_attachments_check = QCheckBox("Incluir adjuntos en el reenvío")
        rule_general_layout.addRow("Adjuntos:", self.rule_attachments_check)
        
        rule_general.setLayout(rule_general_layout)
        scroll_layout.addWidget(rule_general)
        
        # Remitentes
        senders_group = QGroupBox("Remitentes")
        senders_layout = QVBoxLayout()
        senders_layout.addWidget(QLabel("Lista de remitentes (uno por línea):"))
        self.rule_senders_text = QTextEdit()
        self.rule_senders_text.setPlaceholderText("correo@ejemplo.com\n@dominio.com")
        self.rule_senders_text.setMaximumHeight(100)
        senders_layout.addWidget(self.rule_senders_text)
        senders_group.setLayout(senders_layout)
        scroll_layout.addWidget(senders_group)
        
        # Palabras clave
        keywords_group = QGroupBox("Palabras Clave en Asunto")
        keywords_layout = QVBoxLayout()
        keywords_layout.addWidget(QLabel("Lista de palabras clave (una por línea):"))
        self.rule_keywords_text = QTextEdit()
        self.rule_keywords_text.setPlaceholderText("urgente\nimportante\nfactura")
        self.rule_keywords_text.setMaximumHeight(100)
        keywords_layout.addWidget(self.rule_keywords_text)
        keywords_group.setLayout(keywords_layout)
        scroll_layout.addWidget(keywords_group)
        
        # Destinatarios
        recipients_group = QGroupBox("Destinatarios del Reenvío")
        recipients_layout = QVBoxLayout()
        recipients_layout.addWidget(QLabel("Lista de destinatarios (uno por línea):"))
        self.rule_recipients_text = QTextEdit()
        self.rule_recipients_text.setPlaceholderText("destino1@ejemplo.com\ndestino2@ejemplo.com")
        self.rule_recipients_text.setMaximumHeight(100)
        recipients_layout.addWidget(self.rule_recipients_text)
        recipients_group.setLayout(recipients_layout)
        scroll_layout.addWidget(recipients_group)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        right_layout.addWidget(scroll)
        
        # Splitter para dividir la ventana
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        
        self.tabs.addTab(tab, "📧 Configuración de los Reenvíos")
        self.rule_widgets = {
            'name': self.rule_name_input,
            'active': self.rule_active_check,
            'attachments': self.rule_attachments_check,
            'senders': self.rule_senders_text,
            'keywords': self.rule_keywords_text,
            'recipients': self.rule_recipients_text
        }
    
    def create_logs_tab(self):
        """Crea la pestaña de logs"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Botón de actualizar
        btn_layout = QHBoxLayout()
        btn_refresh = QPushButton("🔄 Actualizar Logs")
        btn_refresh.clicked.connect(lambda: self.load_logs('reenvios'))
        btn_layout.addWidget(btn_refresh)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Área de texto para logs
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        self.logs_text.setFont(QFont("Courier New", 9))
        layout.addWidget(self.logs_text)
        
        self.tabs.addTab(tab, "📋 Logs de Reenvíos")
    
    def create_errors_tab(self):
        """Crea la pestaña de errores"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Botón de actualizar
        btn_layout = QHBoxLayout()
        btn_refresh = QPushButton("🔄 Actualizar Errores")
        btn_refresh.clicked.connect(lambda: self.load_logs('errores'))
        btn_layout.addWidget(btn_refresh)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Área de texto para errores
        self.errors_text = QTextEdit()
        self.errors_text.setReadOnly(True)
        self.errors_text.setFont(QFont("Courier New", 9))
        layout.addWidget(self.errors_text)
        
        self.tabs.addTab(tab, "⚠️ Logs de Errores")
    
    def setup_tray_icon(self):
        """Configura el icono de la bandeja del sistema"""
        self.tray_icon = QSystemTrayIcon(self)
        
        # Crear icono de caracol
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setFont(QFont("Segoe UI Emoji", 20))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "🐚")
        painter.end()
        
        icon = QIcon(pixmap)
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("P.E.R.C.E.B.E.")
        
        # Crear menú contextual
        tray_menu = QMenu()
        
        action_show = QAction("Abrir Interfaz", self)
        action_show.triggered.connect(self.show_window)
        tray_menu.addAction(action_show)
        
        tray_menu.addSeparator()
        
        action_exit = QAction("Salir", self)
        action_exit.triggered.connect(self.exit_application)
        tray_menu.addAction(action_exit)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()
    
    def tray_icon_activated(self, reason):
        """Maneja los clics en el icono de la bandeja"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window()
    
    def show_window(self):
        """Muestra la ventana principal"""
        self.show()
        self.activateWindow()
        self.raise_()
    
    def closeEvent(self, event):
        """Maneja el cierre de la ventana"""
        event.ignore()
        self.hide()
    
    def exit_application(self):
        """Sale de la aplicación completamente"""
        self.tray_icon.hide()
        QApplication.quit()
    
    def activate_percebeiro_pro(self):
        """Activa el modo Percebeiro Pro (rickroll)"""
        webbrowser.open("https://shattereddisk.github.io/rickroll/rickroll.mp4")
    
    def test_server_connection(self):
        """Prueba la conexión con el servidor"""
        ip = self.ip_input.text().strip()
        port = self.port_input.value()
        
        if not ip:
            QMessageBox.warning(self, "Error", "Introduce la IP del servidor")
            return
        
        try:
            test_client = PercebeClient(ip, port)
            result = test_client.send_command({'command': 'get_config'})
            
            if result.get('status') == 'ok':
                QMessageBox.information(self, "Éxito", "✓ Conexión establecida correctamente")
            else:
                QMessageBox.warning(self, "Error", f"Error del servidor: {result.get('message', 'Desconocido')}")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo conectar al servidor:\n{str(e)}")
    
    def connect_to_server(self):
        """Conecta al servidor y carga la configuración"""
        ip = self.ip_input.text().strip()
        port = self.port_input.value()
        
        if not ip:
            QMessageBox.warning(self, "Error", "Introduce la IP del servidor")
            return
        
        try:
            self.client = PercebeClient(ip, port)
            result = self.client.get_config()
            
            if result.get('status') == 'ok':
                self.server_config = result.get('data', {})
                self.client_config['server_ip'] = ip
                self.client_config['server_port'] = port
                self.save_client_config()
                
                self.load_accounts()
                self.tabs.setEnabled(True)
                self.account_combo.setEnabled(True)
                self.btn_new_account.setEnabled(True)
                self.btn_save_config.setEnabled(True)
                
                QMessageBox.information(self, "Éxito", "✓ Conectado al servidor correctamente")
            else:
                QMessageBox.warning(self, "Error", f"Error del servidor: {result.get('message', 'Desconocido')}")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo conectar al servidor:\n{str(e)}")
    
    def load_accounts(self):
        """Carga las cuentas en el combo box"""
        self.account_combo.clear()
        
        if not self.server_config:
            return
        
        cuentas = self.server_config.get('cuentas', [])
        
        for cuenta in cuentas:
            self.account_combo.addItem(cuenta.get('nombre', 'Sin nombre'))
        
        if cuentas:
            self.account_combo.setCurrentIndex(0)
    
    def on_account_selected(self, index):
        """Maneja la selección de una cuenta"""
        if index < 0 or not self.server_config:
            return
        
        self.current_account_index = index
        cuentas = self.server_config.get('cuentas', [])
        
        if index < len(cuentas):
            cuenta = cuentas[index]
            self.load_account_data(cuenta)
            self.load_rules()
    
    def load_account_data(self, cuenta):
        """Carga los datos de una cuenta en la interfaz"""
        self.config_widgets['name'].setText(cuenta.get('nombre', ''))
        self.config_widgets['active'].setChecked(cuenta.get('activa', True))
        self.config_widgets['imap_server'].setText(cuenta.get('imap_server', ''))
        self.config_widgets['imap_user'].setText(cuenta.get('imap_user', ''))
        self.config_widgets['imap_password'].setText(cuenta.get('imap_password', ''))
        self.config_widgets['smtp_server'].setText(cuenta.get('smtp_server', ''))
        self.config_widgets['smtp_port'].setValue(cuenta.get('smtp_port', 587))
        self.config_widgets['smtp_user'].setText(cuenta.get('smtp_user', ''))
        self.config_widgets['smtp_password'].setText(cuenta.get('smtp_password', ''))
    
    def load_rules(self):
        """Carga las reglas de la cuenta actual"""
        self.rules_list.clear()
        
        if self.current_account_index is None or not self.server_config:
            return
        
        cuentas = self.server_config.get('cuentas', [])
        if self.current_account_index < len(cuentas):
            cuenta = cuentas[self.current_account_index]
            reglas = cuenta.get('reglas', [])
            
            for regla in reglas:
                estado = "✓" if regla.get('activa', True) else "✗"
                nombre = f"{estado} {regla.get('nombre', 'Sin nombre')}"
                self.rules_list.addItem(nombre)
            
            if reglas:
                self.rules_list.setCurrentRow(0)
    
    def on_rule_selected(self, index):
        """Maneja la selección de una regla"""
        if index < 0 or self.current_account_index is None or not self.server_config:
            return
        
        cuentas = self.server_config.get('cuentas', [])
        if self.current_account_index < len(cuentas):
            cuenta = cuentas[self.current_account_index]
            reglas = cuenta.get('reglas', [])
            
            if index < len(reglas):
                regla = reglas[index]
                self.load_rule_data(regla)
    
    def load_rule_data(self, regla):
        """Carga los datos de una regla en la interfaz"""
        self.rule_widgets['name'].setText(regla.get('nombre', ''))
        self.rule_widgets['active'].setChecked(regla.get('activa', True))
        self.rule_widgets['attachments'].setChecked(regla.get('incluir_adjuntos', False))
        
        senders = '\n'.join(regla.get('remitentes', []))
        self.rule_widgets['senders'].setPlainText(senders)
        
        keywords = '\n'.join(regla.get('palabras_clave', []))
        self.rule_widgets['keywords'].setPlainText(keywords)
        
        recipients = '\n'.join(regla.get('destinatarios', []))
        self.rule_widgets['recipients'].setPlainText(recipients)
    
    def create_new_account(self):
        """Crea una nueva cuenta con datos de ejemplo"""
        if not self.server_config:
            return
        
        nueva_cuenta = {
            'nombre': 'Nueva Cuenta',
            'activa': True,
            'imap_server': 'imap.gmail.com',
            'imap_user': 'usuario@gmail.com',
            'imap_password': 'contraseña_aqui',
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'smtp_user': 'usuario@gmail.com',
            'smtp_password': 'contraseña_aqui',
            'reglas': []
        }
        
        if 'cuentas' not in self.server_config:
            self.server_config['cuentas'] = []
        
        self.server_config['cuentas'].append(nueva_cuenta)
        self.load_accounts()
        self.account_combo.setCurrentIndex(len(self.server_config['cuentas']) - 1)
        
        QMessageBox.information(self, "Cuenta Creada", 
                               "Nueva cuenta creada con datos de ejemplo.\n"
                               "Modifica los datos y guarda la configuración.")
    
    def create_new_rule(self):
        """Crea una nueva regla con datos de ejemplo"""
        if self.current_account_index is None or not self.server_config:
            QMessageBox.warning(self, "Error", "Selecciona una cuenta primero")
            return
        
        nueva_regla = {
            'nombre': 'Nueva Regla',
            'activa': True,
            'remitentes': ['ejemplo@dominio.com'],
            'palabras_clave': ['urgente', 'importante'],
            'destinatarios': ['destino@ejemplo.com'],
            'incluir_adjuntos': False
        }
        
        cuentas = self.server_config.get('cuentas', [])
        if self.current_account_index < len(cuentas):
            if 'reglas' not in cuentas[self.current_account_index]:
                cuentas[self.current_account_index]['reglas'] = []
            
            cuentas[self.current_account_index]['reglas'].append(nueva_regla)
            self.load_rules()
            self.rules_list.setCurrentRow(len(cuentas[self.current_account_index]['reglas']) - 1)
            
            QMessageBox.information(self, "Regla Creada", 
                                   "Nueva regla creada con datos de ejemplo.\n"
                                   "Modifica los datos y guarda la configuración.")
    
    def delete_rule(self):
        """Elimina la regla seleccionada"""
        current_row = self.rules_list.currentRow()
        
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Selecciona una regla para eliminar")
            return
        
        reply = QMessageBox.question(self, "Confirmar Eliminación",
                                    "¿Estás seguro de eliminar esta regla?",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            if self.current_account_index is not None and self.server_config:
                cuentas = self.server_config.get('cuentas', [])
                if self.current_account_index < len(cuentas):
                    reglas = cuentas[self.current_account_index].get('reglas', [])
                    if current_row < len(reglas):
                        del reglas[current_row]
                        self.load_rules()
                        QMessageBox.information(self, "Éxito", "Regla eliminada correctamente")
    
    def save_configuration(self):
        """Guarda la configuración actual en el servidor"""
        if not self.server_config or self.current_account_index is None:
            QMessageBox.warning(self, "Error", "No hay configuración para guardar")
            return
        
        try:
            # Actualizar datos de la cuenta actual desde la interfaz
            cuentas = self.server_config.get('cuentas', [])
            if self.current_account_index < len(cuentas):
                cuenta = cuentas[self.current_account_index]
                
                # Actualizar configuración de cuenta
                cuenta['nombre'] = self.config_widgets['name'].text().strip()
                cuenta['activa'] = self.config_widgets['active'].isChecked()
                cuenta['imap_server'] = self.config_widgets['imap_server'].text().strip()
                cuenta['imap_user'] = self.config_widgets['imap_user'].text().strip()
                cuenta['imap_password'] = self.config_widgets['imap_password'].text()
                cuenta['smtp_server'] = self.config_widgets['smtp_server'].text().strip()
                cuenta['smtp_port'] = self.config_widgets['smtp_port'].value()
                cuenta['smtp_user'] = self.config_widgets['smtp_user'].text().strip()
                cuenta['smtp_password'] = self.config_widgets['smtp_password'].text()
                
                # Actualizar regla actual si hay una seleccionada
                current_rule = self.rules_list.currentRow()
                if current_rule >= 0 and 'reglas' in cuenta:
                    reglas = cuenta['reglas']
                    if current_rule < len(reglas):
                        regla = reglas[current_rule]
                        regla['nombre'] = self.rule_widgets['name'].text().strip()
                        regla['activa'] = self.rule_widgets['active'].isChecked()
                        regla['incluir_adjuntos'] = self.rule_widgets['attachments'].isChecked()
                        
                        senders_text = self.rule_widgets['senders'].toPlainText().strip()
                        regla['remitentes'] = [s.strip() for s in senders_text.split('\n') if s.strip()]
                        
                        keywords_text = self.rule_widgets['keywords'].toPlainText().strip()
                        regla['palabras_clave'] = [k.strip() for k in keywords_text.split('\n') if k.strip()]
                        
                        recipients_text = self.rule_widgets['recipients'].toPlainText().strip()
                        regla['destinatarios'] = [r.strip() for r in recipients_text.split('\n') if r.strip()]
            
            # Enviar configuración al servidor
            result = self.client.set_config(self.server_config)
            
            if result.get('status') == 'ok':
                QMessageBox.information(self, "Éxito", "✓ Configuración guardada correctamente en el servidor")
                # Recargar para mantener sincronización
                self.connect_to_server()
            else:
                QMessageBox.warning(self, "Error", f"Error al guardar: {result.get('message', 'Desconocido')}")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar configuración:\n{str(e)}")
    
    def load_logs(self, log_type):
        """Carga los logs del servidor"""
        if not self.client:
            QMessageBox.warning(self, "Error", "Conéctate al servidor primero")
            return
        
        try:
            result = self.client.get_logs(log_type)
            
            if result.get('status') == 'ok':
                logs = result.get('data', [])
                log_text = ''.join(logs) if logs else "No hay logs disponibles"
                
                if log_type == 'reenvios':
                    self.logs_text.setPlainText(log_text)
                else:
                    self.errors_text.setPlainText(log_text)
            else:
                QMessageBox.warning(self, "Error", f"Error al cargar logs: {result.get('message', 'Desconocido')}")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar logs:\n{str(e)}")
    
    def apply_styles(self):
        """Aplica estilos modernos a la interfaz"""
        style = """
            QMainWindow {
                background-color: #f5f5f5;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-height: 30px;
            }
            
            QPushButton:hover {
                background-color: #1976D2;
            }
            
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            
            QPushButton:disabled {
                background-color: #BDBDBD;
            }
            
            QLineEdit, QSpinBox, QComboBox {
                padding: 6px;
                border: 2px solid #ddd;
                border-radius: 4px;
                background-color: white;
                min-height: 25px;
            }
            
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
                border: 2px solid #2196F3;
            }
            
            QTextEdit {
                border: 2px solid #ddd;
                border-radius: 4px;
                background-color: white;
                padding: 5px;
            }
            
            QTextEdit:focus {
                border: 2px solid #2196F3;
            }
            
            QTabWidget::pane {
                border: 2px solid #ddd;
                border-radius: 4px;
                background-color: white;
                padding: 5px;
            }
            
            QTabBar::tab {
                background-color: #e0e0e0;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid white;
            }
            
            QTabBar::tab:hover {
                background-color: #f0f0f0;
            }
            
            QListWidget {
                border: 2px solid #ddd;
                border-radius: 4px;
                background-color: white;
                padding: 5px;
            }
            
            QListWidget::item {
                padding: 8px;
                border-radius: 3px;
            }
            
            QListWidget::item:selected {
                background-color: #2196F3;
                color: white;
            }
            
            QListWidget::item:hover {
                background-color: #E3F2FD;
            }
            
            QCheckBox {
                spacing: 8px;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #ddd;
                border-radius: 3px;
                background-color: white;
            }
            
            QCheckBox::indicator:checked {
                background-color: #2196F3;
                border-color: #2196F3;
            }
            
            QScrollBar:vertical {
                border: none;
                background-color: #f0f0f0;
                width: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #BDBDBD;
                border-radius: 6px;
                min-height: 30px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #9E9E9E;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """
        self.setStyleSheet(style)


def main():
    """Función principal"""
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # No cerrar al ocultar la ventana
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()