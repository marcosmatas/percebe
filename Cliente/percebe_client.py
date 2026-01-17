#!/usr/bin/env python3
import sys
import json
import socket
import webbrowser
import ctypes
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QTabWidget, QTextEdit,
    QMessageBox, QSystemTrayIcon, QMenu, QAction, QFormLayout,
    QGroupBox, QScrollArea, QCheckBox, QListWidget, QSpinBox,
    QSplitter
)
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QFont, QPixmap, QPainter, QColor

# --- HILO PARA ESCUCHAR LA SEGUNDA INSTANCIA ---
class InstanceListener(QThread):
    instance_requested = pyqtSignal()

    def run(self):
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.bind(('127.0.0.1', 45678))
            server.listen(5)
            while True:
                conn, addr = server.accept()
                data = conn.recv(1024)
                if data == b"SHOW_WINDOW":
                    self.instance_requested.emit()
                conn.close()
        except:
            pass

class NoWheelSpinBox(QSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
    def wheelEvent(self, event):
        event.ignore()

class PercebeClient:
    def __init__(self, server_ip, server_port=5555):
        self.server_ip = server_ip
        self.server_port = server_port
    
    def send_command(self, command_data):
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(5)
            client_socket.connect((self.server_ip, self.server_port))
            request = json.dumps(command_data).encode('utf-8')
            client_socket.send(request)
            response = b''
            while True:
                chunk = client_socket.recv(4096)
                if not chunk: break
                response += chunk
                try:
                    json.loads(response.decode('utf-8'))
                    break
                except: continue
            client_socket.close()
            return json.loads(response.decode('utf-8'))
        except Exception as e:
            return {'status': 'error', 'message': f'Error de conexión: {str(e)}'}

    def get_config(self): return self.send_command({'command': 'get_config'})
    def set_config(self, config): return self.send_command({'command': 'set_config', 'config': config})
    def get_logs(self, log_type='reenvios'): return self.send_command({'command': 'get_logs', 'log_type': log_type})

class MainWindow(QMainWindow):
    def __init__(self, icon_path=None):
        super().__init__()
        self.icon_path = icon_path
        self.config_file = Path("percebe_client_config.json")
        self.client_config = self.load_client_config()
        self.client = None
        self.server_config = None
        self.current_account_index = None
        
        if self.icon_path and Path(self.icon_path).exists():
            self.setWindowIcon(QIcon(self.icon_path))
            
        self.init_ui()
        self.setup_tray_icon()

        self.listener = InstanceListener()
        self.listener.instance_requested.connect(self.show_window)
        self.listener.start()

    def load_client_config(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: pass
        return {'server_ip': '127.0.0.1', 'server_port': 5555}

    def save_client_config(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.client_config, f, indent=4)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al guardar configuración local: {e}")

    def init_ui(self):
        self.setWindowTitle("P.E.R.C.E.B.E. - Cliente de Gestión")
        self.setMinimumSize(1000, 700)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        self.create_header(layout)
        self.create_connection_bar(layout)
        self.create_account_selector(layout)
        
        self.tabs = QTabWidget()
        self.tabs.setEnabled(False)
        layout.addWidget(self.tabs)
        
        self.create_config_tab()
        self.create_rules_tab()
        self.create_logs_tab()
        self.create_errors_tab()
        self.apply_styles()

    def create_header(self, layout):
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 10)
        
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
        
        btn_coffee = QPushButton("☕ Si te gusta invítame a un café")
        btn_coffee.setFixedHeight(40)
        btn_coffee.setCursor(Qt.PointingHandCursor)
        btn_coffee.clicked.connect(lambda: webbrowser.open("https://buymeacoffee.com/flopy"))
        header_layout.addWidget(btn_coffee)
        
        btn_pro = QPushButton("🎵 Modo Percebeiro Pro")
        btn_pro.setFixedHeight(40)
        btn_pro.setCursor(Qt.PointingHandCursor)
        btn_pro.clicked.connect(self.activate_percebeiro_pro)
        header_layout.addWidget(btn_pro)
        
        layout.addWidget(header)

    def create_connection_bar(self, layout):
        conn_group = QGroupBox("Conexión con Servidor")
        conn_layout = QHBoxLayout()
        conn_layout.addWidget(QLabel("IP del Servidor:"))
        self.ip_input = QLineEdit()
        self.ip_input.setText(self.client_config.get('server_ip', '127.0.0.1'))
        self.ip_input.setMaximumWidth(150)
        conn_layout.addWidget(self.ip_input)
        
        conn_layout.addWidget(QLabel("Puerto:"))
        self.port_input = NoWheelSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(self.client_config.get('server_port', 5555))
        self.port_input.setButtonSymbols(QSpinBox.NoButtons)
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
        tab = QWidget()
        layout = QVBoxLayout(tab)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        general_group = QGroupBox("Información General")
        general_layout = QFormLayout()
        self.account_name_input = QLineEdit()
        general_layout.addRow("Nombre de la cuenta:", self.account_name_input)
        self.account_active_check = QCheckBox("Cuenta activa")
        self.account_active_check.setChecked(True)
        general_layout.addRow("Estado:", self.account_active_check)
        general_group.setLayout(general_layout)
        scroll_layout.addWidget(general_group)
        
        imap_group = QGroupBox("Configuración IMAP (Recepción)")
        imap_layout = QFormLayout()
        self.imap_server_input = QLineEdit()
        imap_layout.addRow("Servidor IMAP:", self.imap_server_input)
        self.imap_user_input = QLineEdit()
        imap_layout.addRow("Usuario:", self.imap_user_input)
        self.imap_password_input = QLineEdit()
        self.imap_password_input.setEchoMode(QLineEdit.Password)
        imap_layout.addRow("Contraseña:", self.imap_password_input)
        imap_group.setLayout(imap_layout)
        scroll_layout.addWidget(imap_group)
        
        smtp_group = QGroupBox("Configuración SMTP (Envío)")
        smtp_layout = QFormLayout()
        self.smtp_server_input = QLineEdit()
        smtp_layout.addRow("Servidor SMTP:", self.smtp_server_input)
        
        self.smtp_port_input = NoWheelSpinBox()
        self.smtp_port_input.setRange(1, 65535)
        self.smtp_port_input.setValue(587)
        self.smtp_port_input.setButtonSymbols(QSpinBox.NoButtons)
        smtp_layout.addRow("Puerto SMTP:", self.smtp_port_input)
        
        self.smtp_user_input = QLineEdit()
        smtp_layout.addRow("Usuario:", self.smtp_user_input)
        self.smtp_password_input = QLineEdit()
        self.smtp_password_input.setEchoMode(QLineEdit.Password)
        smtp_layout.addRow("Contraseña:", self.smtp_password_input)
        smtp_group.setLayout(smtp_layout)
        scroll_layout.addWidget(smtp_group)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        self.tabs.addTab(tab, "Configuración de la Cuenta")

    def create_rules_tab(self):
        tab = QWidget()
        layout = QHBoxLayout(tab)
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
        
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        rule_general = QGroupBox("Información General")
        rule_general_layout = QFormLayout()
        self.rule_name_input = QLineEdit()
        rule_general_layout.addRow("Nombre:", self.rule_name_input)
        self.rule_active_check = QCheckBox("Regla activa")
        rule_general_layout.addRow("Estado:", self.rule_active_check)
        self.rule_attachments_check = QCheckBox("Incluir adjuntos en el reenvío")
        rule_general_layout.addRow("Adjuntos:", self.rule_attachments_check)
        rule_general.setLayout(rule_general_layout)
        scroll_layout.addWidget(rule_general)
        
        senders_group = QGroupBox("Remitentes (uno por línea)")
        senders_layout = QVBoxLayout()
        self.rule_senders_text = QTextEdit()
        senders_layout.addWidget(self.rule_senders_text)
        senders_group.setLayout(senders_layout)
        scroll_layout.addWidget(senders_group)
        
        keywords_group = QGroupBox("Palabras Clave en Asunto (una por línea)")
        keywords_layout = QVBoxLayout()
        self.rule_keywords_text = QTextEdit()
        keywords_layout.addWidget(self.rule_keywords_text)
        keywords_group.setLayout(keywords_layout)
        scroll_layout.addWidget(keywords_group)
        
        recipients_group = QGroupBox("Destinatarios del Reenvío (uno por línea)")
        recipients_layout = QVBoxLayout()
        self.rule_recipients_text = QTextEdit()
        recipients_layout.addWidget(self.rule_recipients_text)
        recipients_group.setLayout(recipients_layout)
        scroll_layout.addWidget(recipients_group)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        right_layout.addWidget(scroll)
        
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter)
        
        self.tabs.addTab(tab, "📧 Reglas de Reenvío")

    def create_logs_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        btn_refresh = QPushButton("🔄 Actualizar Logs")
        btn_refresh.clicked.connect(lambda: self.load_logs('reenvios'))
        layout.addWidget(btn_refresh)
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        self.logs_text.setFont(QFont("Consolas", 10))
        layout.addWidget(self.logs_text)
        self.tabs.addTab(tab, "📋 Registro de Reenvíos")

    def create_errors_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        btn_refresh = QPushButton("🔄 Actualizar Errores")
        btn_refresh.clicked.connect(lambda: self.load_logs('errores'))
        layout.addWidget(btn_refresh)
        self.errors_text = QTextEdit()
        self.errors_text.setReadOnly(True)
        self.errors_text.setFont(QFont("Consolas", 10))
        layout.addWidget(self.errors_text)
        self.tabs.addTab(tab, "⚠️ Registro de Errores")

    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setFont(QFont("Arial", 20))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "🐚")
        painter.end()
        self.tray_icon.setIcon(QIcon(pixmap))
        
        tray_menu = QMenu()
        action_show = QAction("Abrir Interfaz", self)
        action_show.triggered.connect(self.show_window)
        tray_menu.addAction(action_show)
        tray_menu.addSeparator()
        action_exit = QAction("Salir Completamente", self)
        action_exit.triggered.connect(self.exit_application)
        tray_menu.addAction(action_exit)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def show_window(self):
        self.show()
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        self.activateWindow()
        self.raise_()

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def exit_application(self):
        self.tray_icon.hide()
        QApplication.quit()

    def activate_percebeiro_pro(self):
        webbrowser.open("https://shattereddisk.github.io/rickroll/rickroll.mp4")

    def test_server_connection(self):
        ip = self.ip_input.text().strip()
        port = self.port_input.value()
        test_client = PercebeClient(ip, port)
        result = test_client.get_config()
        if result.get('status') == 'ok':
            QMessageBox.information(self, "Éxito", "✓ Conexión establecida correctamente.")
        else:
            QMessageBox.warning(self, "Error", f"Fallo: {result.get('message')}")

    def connect_to_server(self):
        ip = self.ip_input.text().strip()
        port = self.port_input.value()
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
        else:
            QMessageBox.critical(self, "Error", "Error al conectar.")

    def load_accounts(self):
        self.account_combo.clear()
        cuentas = self.server_config.get('cuentas', [])
        for cuenta in cuentas:
            self.account_combo.addItem(cuenta.get('nombre', 'Sin nombre'))
        if cuentas:
            self.on_account_selected(0)

    def on_account_selected(self, index):
        if index < 0: return
        self.current_account_index = index
        cuenta = self.server_config['cuentas'][index]
        self.load_account_data(cuenta)
        self.load_rules()

    def load_account_data(self, cuenta):
        self.account_name_input.setText(cuenta.get('nombre', ''))
        self.account_active_check.setChecked(cuenta.get('activa', True))
        self.imap_server_input.setText(cuenta.get('imap_server', ''))
        self.imap_user_input.setText(cuenta.get('imap_user', ''))
        self.imap_password_input.setText(cuenta.get('imap_password', ''))
        self.smtp_server_input.setText(cuenta.get('smtp_server', ''))
        self.smtp_port_input.setValue(cuenta.get('smtp_port', 587))
        self.smtp_user_input.setText(cuenta.get('smtp_user', ''))
        self.smtp_password_input.setText(cuenta.get('smtp_password', ''))

    def load_rules(self):
        self.rules_list.clear()
        reglas = self.server_config['cuentas'][self.current_account_index].get('reglas', [])
        for i, regla in enumerate(reglas):
            estado = "✓" if regla.get('activa') else "✗"
            self.rules_list.addItem(f"{estado} {regla.get('nombre', f'Regla {i+1}')}")

    def on_rule_selected(self, index):
        if index < 0: return
        regla = self.server_config['cuentas'][self.current_account_index]['reglas'][index]
        self.load_rule_data(regla)

    def load_rule_data(self, regla):
        self.rule_name_input.setText(regla.get('nombre', ''))
        self.rule_active_check.setChecked(regla.get('activa', True))
        self.rule_attachments_check.setChecked(regla.get('incluir_adjuntos', True))
        self.rule_senders_text.setPlainText('\n'.join(regla.get('remitentes', [])))
        self.rule_keywords_text.setPlainText('\n'.join(regla.get('palabras_clave', [])))
        self.rule_recipients_text.setPlainText('\n'.join(regla.get('destinatarios', [])))

    def create_new_account(self):
        nueva_cuenta = {
            'nombre': 'Nueva Cuenta', 'activa': True,
            'imap_server': '', 'imap_user': '', 'imap_password': '',
            'smtp_server': '', 'smtp_port': 587, 'smtp_user': '', 'smtp_password': '',
            'reglas': []
        }
        self.server_config.setdefault('cuentas', []).append(nueva_cuenta)
        self.load_accounts()

    def create_new_rule(self):
        nueva_regla = {
            'nombre': 'Nueva Regla', 'activa': True, 'incluir_adjuntos': True,
            'remitentes': [], 'palabras_clave': [], 'destinatarios': []
        }
        self.server_config['cuentas'][self.current_account_index]['reglas'].append(nueva_regla)
        self.load_rules()

    def delete_rule(self):
        idx = self.rules_list.currentRow()
        if idx >= 0:
            del self.server_config['cuentas'][self.current_account_index]['reglas'][idx]
            self.load_rules()

    def save_configuration(self):
        """LEE LOS DATOS DE LA UI Y LOS ENVÍA AL SERVIDOR"""
        if self.current_account_index is None: return
        
        # 1. Actualizar datos de la CUENTA desde la UI
        cuenta = self.server_config['cuentas'][self.current_account_index]
        cuenta['nombre'] = self.account_name_input.text()
        cuenta['activa'] = self.account_active_check.isChecked()
        cuenta['imap_server'] = self.imap_server_input.text()
        cuenta['imap_user'] = self.imap_user_input.text()
        cuenta['imap_password'] = self.imap_password_input.text()
        cuenta['smtp_server'] = self.smtp_server_input.text()
        cuenta['smtp_port'] = self.smtp_port_input.value()
        cuenta['smtp_user'] = self.smtp_user_input.text()
        cuenta['smtp_password'] = self.smtp_password_input.text()
        
        # 2. Actualizar datos de la REGLA seleccionada desde la UI
        rule_idx = self.rules_list.currentRow()
        if rule_idx >= 0:
            regla = cuenta['reglas'][rule_idx]
            regla['nombre'] = self.rule_name_input.text()
            regla['activa'] = self.rule_active_check.isChecked()
            regla['incluir_adjuntos'] = self.rule_attachments_check.isChecked()
            
            # Convertir texto multilínea en listas
            regla['remitentes'] = [s.strip() for s in self.rule_senders_text.toPlainText().split('\n') if s.strip()]
            regla['palabras_clave'] = [s.strip() for s in self.rule_keywords_text.toPlainText().split('\n') if s.strip()]
            regla['destinatarios'] = [s.strip() for s in self.rule_recipients_text.toPlainText().split('\n') if s.strip()]
            
        # 3. Enviar todo el objeto server_config al servidor
        result = self.client.set_config(self.server_config)
        if result.get('status') == 'ok':
            QMessageBox.information(self, "Éxito", "Configuración guardada correctamente en el servidor.")
            self.load_rules() # Refrescar lista de reglas (por si cambió el nombre o estado)
        else:
            QMessageBox.warning(self, "Error", f"No se pudo guardar: {result.get('message')}")

    def load_logs(self, log_type):
        result = self.client.get_logs(log_type)
        if result.get('status') == 'ok':
            content = "".join(result.get('data', []))
            if log_type == 'reenvios': self.logs_text.setPlainText(content)
            else: self.errors_text.setPlainText(content)

    def apply_styles(self):
        style = """
            QMainWindow { background-color: #f5f5f5; }
            QGroupBox { font-weight: bold; border: 2px solid #ddd; border-radius: 8px; margin-top: 10px; padding-top: 10px; background-color: white; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px; }
            QPushButton { background-color: #2196F3; color: white; border: none; padding: 8px 16px; border-radius: 4px; font-weight: bold; min-height: 30px; }
            QPushButton:hover { background-color: #1976D2; }
            QLineEdit, QSpinBox, QComboBox, QTextEdit, QListWidget { padding: 6px; border: 2px solid #ddd; border-radius: 4px; background-color: white; }
            QTabWidget::pane { border: 2px solid #ddd; border-radius: 4px; background-color: white; }
            QTabBar::tab { background-color: #e0e0e0; padding: 10px 20px; margin-right: 2px; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background-color: white; border: 2px solid #ddd; border-bottom: none; }
            QCheckBox::indicator { width: 18px; height: 18px; border: 2px solid #ddd; border-radius: 3px; background-color: white; }
            QCheckBox::indicator:checked { background-color: #2196F3; border-color: #2196F3; }
            QScrollBar:vertical { border: none; background-color: #f0f0f0; width: 12px; border-radius: 6px; }
            QScrollBar::handle:vertical { background-color: #BDBDBD; border-radius: 6px; min-height: 30px; }
        """
        self.setStyleSheet(style)

def main():
    myappid = 'flopy.percebe.client.1.0' 
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    
    app = QApplication(sys.argv)
    
    try:
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.bind(('127.0.0.1', 45678))
        test_socket.close()
    except socket.error:
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('127.0.0.1', 45678))
            client.send(b"SHOW_WINDOW")
            client.close()
        except: pass
        sys.exit(0)
    
    app.setQuitOnLastWindowClosed(False)
    icon_path = r"C:\Users\marcosms\python\Percebecliente\percebe.ico"
    
    window = MainWindow(icon_path)
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
