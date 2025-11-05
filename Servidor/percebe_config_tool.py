#!/usr/bin/env python3
"""
Herramienta CLI para configurar P.E.R.C.E.B.E.
Útil para configuración inicial y pruebas antes de tener el cliente Windows
"""

import json
import sys
from pathlib import Path
import getpass


class PercebeConfigTool:
    def __init__(self, config_path="/opt/percebe/percebe_config/config.json"):
        self.config_path = Path(config_path)
        self.config = self.load_config()
    
    def load_config(self):
        """Carga la configuración existente"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"cuentas": [], "intervalo_revision": 60, "api_enabled": True, "api_port": 5555}
    
    def save_config(self):
        """Guarda la configuración"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)
        print("✓ Configuración guardada correctamente")
    
    def menu_principal(self):
        """Menú principal"""
        while True:
            print("\n" + "="*50)
            print("P.E.R.C.E.B.E. - Herramienta de Configuración")
            print("="*50)
            print("\n1. Gestionar cuentas")
            print("2. Configuración general")
            print("3. Ver configuración completa")
            print("4. Guardar y salir")
            print("5. Salir sin guardar")
            
            opcion = input("\nSelecciona una opción: ").strip()
            
            if opcion == "1":
                self.menu_cuentas()
            elif opcion == "2":
                self.config_general()
            elif opcion == "3":
                self.mostrar_config()
            elif opcion == "4":
                self.save_config()
                break
            elif opcion == "5":
                print("Saliendo sin guardar...")
                break
    
    def menu_cuentas(self):
        """Menú de gestión de cuentas"""
        while True:
            print("\n" + "-"*50)
            print("GESTIÓN DE CUENTAS")
            print("-"*50)
            
            if not self.config["cuentas"]:
                print("\nNo hay cuentas configuradas")
            else:
                print("\nCuentas configuradas:")
                for i, cuenta in enumerate(self.config["cuentas"]):
                    estado = "✓ Activa" if cuenta.get("activa", True) else "✗ Inactiva"
                    print(f"{i+1}. {cuenta.get('nombre', 'Sin nombre')} - {estado}")
            
            print("\nOpciones:")
            print("1. Añadir nueva cuenta")
            print("2. Editar cuenta existente")
            print("3. Eliminar cuenta")
            print("4. Volver al menú principal")
            
            opcion = input("\nSelecciona una opción: ").strip()
            
            if opcion == "1":
                self.añadir_cuenta()
            elif opcion == "2":
                self.editar_cuenta()
            elif opcion == "3":
                self.eliminar_cuenta()
            elif opcion == "4":
                break
    
    def añadir_cuenta(self):
        """Añade una nueva cuenta"""
        print("\n" + "-"*50)
        print("AÑADIR NUEVA CUENTA")
        print("-"*50)
        
        cuenta = {}
        
        cuenta["nombre"] = input("\nNombre de la cuenta: ").strip()
        cuenta["activa"] = input("¿Activar cuenta? (s/n) [s]: ").strip().lower() != 'n'
        
        print("\n--- Configuración IMAP ---")
        cuenta["imap_server"] = input("Servidor IMAP: ").strip()
        cuenta["imap_user"] = input("Usuario IMAP: ").strip()
        cuenta["imap_password"] = getpass.getpass("Contraseña IMAP: ")
        
        print("\n--- Configuración SMTP ---")
        usar_mismo = input("¿Usar los mismos datos para SMTP? (s/n) [s]: ").strip().lower() != 'n'
        
        if usar_mismo:
            cuenta["smtp_server"] = cuenta["imap_server"].replace("imap", "smtp")
            cuenta["smtp_user"] = cuenta["imap_user"]
            cuenta["smtp_password"] = cuenta["imap_password"]
        else:
            cuenta["smtp_server"] = input("Servidor SMTP: ").strip()
            cuenta["smtp_user"] = input("Usuario SMTP: ").strip()
            cuenta["smtp_password"] = getpass.getpass("Contraseña SMTP: ")
        
        puerto = input("Puerto SMTP [587]: ").strip()
        cuenta["smtp_port"] = int(puerto) if puerto else 587
        
        cuenta["reglas"] = []
        
        self.config["cuentas"].append(cuenta)
        print(f"\n✓ Cuenta '{cuenta['nombre']}' añadida correctamente")
        
        if input("\n¿Añadir reglas ahora? (s/n) [n]: ").strip().lower() == 's':
            self.menu_reglas(len(self.config["cuentas"]) - 1)
    
    def editar_cuenta(self):
        """Edita una cuenta existente"""
        if not self.config["cuentas"]:
            print("\nNo hay cuentas para editar")
            return
        
        print("\nSelecciona la cuenta a editar:")
        for i, cuenta in enumerate(self.config["cuentas"]):
            print(f"{i+1}. {cuenta.get('nombre', 'Sin nombre')}")
        
        try:
            idx = int(input("\nNúmero de cuenta: ").strip()) - 1
            if idx < 0 or idx >= len(self.config["cuentas"]):
                print("Cuenta inválida")
                return
        except ValueError:
            print("Entrada inválida")
            return
        
        self.menu_editar_cuenta(idx)
    
    def menu_editar_cuenta(self, idx):
        """Menú para editar una cuenta específica"""
        while True:
            cuenta = self.config["cuentas"][idx]
            print("\n" + "-"*50)
            print(f"EDITAR: {cuenta.get('nombre', 'Sin nombre')}")
            print("-"*50)
            print("\n1. Cambiar nombre")
            print("2. Activar/Desactivar cuenta")
            print("3. Editar configuración IMAP")
            print("4. Editar configuración SMTP")
            print("5. Gestionar reglas")
            print("6. Volver")
            
            opcion = input("\nSelecciona una opción: ").strip()
            
            if opcion == "1":
                cuenta["nombre"] = input("Nuevo nombre: ").strip()
            elif opcion == "2":
                cuenta["activa"] = not cuenta.get("activa", True)
                estado = "activada" if cuenta["activa"] else "desactivada"
                print(f"✓ Cuenta {estado}")
            elif opcion == "3":
                print("\n--- Configuración IMAP ---")
                cuenta["imap_server"] = input(f"Servidor IMAP [{cuenta.get('imap_server', '')}]: ").strip() or cuenta.get("imap_server")
                cuenta["imap_user"] = input(f"Usuario IMAP [{cuenta.get('imap_user', '')}]: ").strip() or cuenta.get("imap_user")
                if input("¿Cambiar contraseña? (s/n) [n]: ").strip().lower() == 's':
                    cuenta["imap_password"] = getpass.getpass("Nueva contraseña IMAP: ")
            elif opcion == "4":
                print("\n--- Configuración SMTP ---")
                cuenta["smtp_server"] = input(f"Servidor SMTP [{cuenta.get('smtp_server', '')}]: ").strip() or cuenta.get("smtp_server")
                cuenta["smtp_user"] = input(f"Usuario SMTP [{cuenta.get('smtp_user', '')}]: ").strip() or cuenta.get("smtp_user")
                puerto = input(f"Puerto SMTP [{cuenta.get('smtp_port', 587)}]: ").strip()
                if puerto:
                    cuenta["smtp_port"] = int(puerto)
                if input("¿Cambiar contraseña? (s/n) [n]: ").strip().lower() == 's':
                    cuenta["smtp_password"] = getpass.getpass("Nueva contraseña SMTP: ")
            elif opcion == "5":
                self.menu_reglas(idx)
            elif opcion == "6":
                break
    
    def menu_reglas(self, cuenta_idx):
        """Menú de gestión de reglas"""
        while True:
            cuenta = self.config["cuentas"][cuenta_idx]
            print("\n" + "-"*50)
            print(f"REGLAS DE: {cuenta.get('nombre', 'Sin nombre')}")
            print("-"*50)
            
            if not cuenta.get("reglas"):
                print("\nNo hay reglas configuradas")
            else:
                print("\nReglas configuradas:")
                for i, regla in enumerate(cuenta["reglas"]):
                    estado = "✓" if regla.get("activa", True) else "✗"
                    adjuntos = "Con adjuntos" if regla.get("incluir_adjuntos", False) else "Sin adjuntos"
                    print(f"{i+1}. {estado} {regla.get('nombre', 'Sin nombre')} - {adjuntos}")
            
            print("\nOpciones:")
            print("1. Añadir nueva regla")
            print("2. Editar regla existente")
            print("3. Eliminar regla")
            print("4. Volver")
            
            opcion = input("\nSelecciona una opción: ").strip()
            
            if opcion == "1":
                self.añadir_regla(cuenta_idx)
            elif opcion == "2":
                self.editar_regla(cuenta_idx)
            elif opcion == "3":
                self.eliminar_regla(cuenta_idx)
            elif opcion == "4":
                break
    
    def añadir_regla(self, cuenta_idx):
        """Añade una nueva regla"""
        print("\n" + "-"*50)
        print("AÑADIR NUEVA REGLA")
        print("-"*50)
        
        regla = {}
        
        regla["nombre"] = input("\nNombre de la regla: ").strip()
        regla["activa"] = input("¿Activar regla? (s/n) [s]: ").strip().lower() != 'n'
        
        print("\n--- Remitentes ---")
        print("Introduce remitentes uno por uno (vacío para terminar)")
        print("Ejemplos: correo@ejemplo.com o @dominio.com")
        remitentes = []
        while True:
            rem = input("Remitente: ").strip()
            if not rem:
                break
            remitentes.append(rem)
        regla["remitentes"] = remitentes
        
        print("\n--- Palabras clave en asunto ---")
        print("Introduce palabras clave una por una (vacío para terminar)")
        palabras = []
        while True:
            palabra = input("Palabra clave: ").strip()
            if not palabra:
                break
            palabras.append(palabra)
        regla["palabras_clave"] = palabras
        
        print("\n--- Destinatarios ---")
        print("Introduce destinatarios uno por uno (vacío para terminar)")
        destinatarios = []
        while True:
            dest = input("Destinatario: ").strip()
            if not dest:
                break
            destinatarios.append(dest)
        regla["destinatarios"] = destinatarios
        
        regla["incluir_adjuntos"] = input("\n¿Incluir adjuntos? (s/n) [n]: ").strip().lower() == 's'
        
        if "reglas" not in self.config["cuentas"][cuenta_idx]:
            self.config["cuentas"][cuenta_idx]["reglas"] = []
        
        self.config["cuentas"][cuenta_idx]["reglas"].append(regla)
        print(f"\n✓ Regla '{regla['nombre']}' añadida correctamente")
    
    def editar_regla(self, cuenta_idx):
        """Edita una regla existente"""
        cuenta = self.config["cuentas"][cuenta_idx]
        if not cuenta.get("reglas"):
            print("\nNo hay reglas para editar")
            return
        
        print("\nSelecciona la regla a editar:")
        for i, regla in enumerate(cuenta["reglas"]):
            print(f"{i+1}. {regla.get('nombre', 'Sin nombre')}")
        
        try:
            idx = int(input("\nNúmero de regla: ").strip()) - 1
            if idx < 0 or idx >= len(cuenta["reglas"]):
                print("Regla inválida")
                return
        except ValueError:
            print("Entrada inválida")
            return
        
        # Aquí podrías implementar un menú detallado como con las cuentas
        print("\nFuncionalidad de edición detallada pendiente")
        print("Por ahora, considera eliminar y recrear la regla")
    
    def eliminar_cuenta(self):
        """Elimina una cuenta"""
        if not self.config["cuentas"]:
            print("\nNo hay cuentas para eliminar")
            return
        
        print("\nSelecciona la cuenta a eliminar:")
        for i, cuenta in enumerate(self.config["cuentas"]):
            print(f"{i+1}. {cuenta.get('nombre', 'Sin nombre')}")
        
        try:
            idx = int(input("\nNúmero de cuenta: ").strip()) - 1
            if idx < 0 or idx >= len(self.config["cuentas"]):
                print("Cuenta inválida")
                return
        except ValueError:
            print("Entrada inválida")
            return
        
        cuenta = self.config["cuentas"][idx]
        confirmar = input(f"\n¿Eliminar '{cuenta.get('nombre')}'? (s/n): ").strip().lower()
        
        if confirmar == 's':
            del self.config["cuentas"][idx]
            print("✓ Cuenta eliminada")
    
    def eliminar_regla(self, cuenta_idx):
        """Elimina una regla"""
        cuenta = self.config["cuentas"][cuenta_idx]
        if not cuenta.get("reglas"):
            print("\nNo hay reglas para eliminar")
            return
        
        print("\nSelecciona la regla a eliminar:")
        for i, regla in enumerate(cuenta["reglas"]):
            print(f"{i+1}. {regla.get('nombre', 'Sin nombre')}")
        
        try:
            idx = int(input("\nNúmero de regla: ").strip()) - 1
            if idx < 0 or idx >= len(cuenta["reglas"]):
                print("Regla inválida")
                return
        except ValueError:
            print("Entrada inválida")
            return
        
        regla = cuenta["reglas"][idx]
        confirmar = input(f"\n¿Eliminar '{regla.get('nombre')}'? (s/n): ").strip().lower()
        
        if confirmar == 's':
            del cuenta["reglas"][idx]
            print("✓ Regla eliminada")
    
    def config_general(self):
        """Configuración general del sistema"""
        print("\n" + "-"*50)
        print("CONFIGURACIÓN GENERAL")
        print("-"*50)
        
        print(f"\nIntervalo de revisión actual: {self.config.get('intervalo_revision', 60)} segundos")
        nuevo = input("Nuevo intervalo (vacío para mantener): ").strip()
        if nuevo:
            try:
                self.config["intervalo_revision"] = int(nuevo)
            except ValueError:
                print("Valor inválido")
        
        print(f"\nAPI habilitada: {'Sí' if self.config.get('api_enabled', True) else 'No'}")
        cambiar = input("¿Cambiar? (s/n) [n]: ").strip().lower()
        if cambiar == 's':
            self.config["api_enabled"] = not self.config.get("api_enabled", True)
        
        print(f"\nPuerto API actual: {self.config.get('api_port', 5555)}")
        nuevo_puerto = input("Nuevo puerto (vacío para mantener): ").strip()
        if nuevo_puerto:
            try:
                self.config["api_port"] = int(nuevo_puerto)
            except ValueError:
                print("Puerto inválido")
    
    def mostrar_config(self):
        """Muestra la configuración completa"""
        print("\n" + "="*50)
        print("CONFIGURACIÓN COMPLETA")
        print("="*50)
        print(json.dumps(self.config, indent=4, ensure_ascii=False))
        input("\nPresiona Enter para continuar...")


def main():
    print("Herramienta de Configuración para P.E.R.C.E.B.E.")
    
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        config_path = "/opt/percebe/percebe_config/config.json"
    
    try:
        tool = PercebeConfigTool(config_path)
        tool.menu_principal()
    except KeyboardInterrupt:
        print("\n\nInterrumpido por usuario")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()
