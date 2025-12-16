import datetime
import hashlib
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext


# ======================== BASE DE DATOS ========================
class Database:
    def __init__(self):
        self.conn = sqlite3.connect('alan_automotriz.db')
        self.cursor = self.conn.cursor()
        self.crear_tablas()
        self.crear_usuarios_default()

    def crear_tablas(self):
        # Tabla de usuarios
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                rol TEXT NOT NULL,
                nombre TEXT NOT NULL,
                activo INTEGER DEFAULT 1
            )
        ''')

        # Tabla de clientes
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                telefono TEXT NOT NULL,
                correo TEXT,
                direccion TEXT,
                activo INTEGER DEFAULT 1
            )
        ''')

        # Tabla de vehículos
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS vehiculos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                marca TEXT NOT NULL,
                modelo TEXT NOT NULL,
                placa TEXT UNIQUE NOT NULL,
                anio TEXT,
                color TEXT,
                activo INTEGER DEFAULT 1
            )
        ''')

        # Tabla de ingresos (relación cliente-vehículo)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS ingresos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER NOT NULL,
                vehiculo_id INTEGER NOT NULL,
                estado TEXT DEFAULT 'Ingreso',
                fecha_ingreso TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_entrega TIMESTAMP,
                asignado_a INTEGER,
                motivo_ingreso TEXT,
                plazo_dias INTEGER,
                plazo_horas INTEGER,
                plazo_minutos INTEGER,
                fecha_inicio_plazo TIMESTAMP,
                plazo_activo INTEGER DEFAULT 0,
                FOREIGN KEY (cliente_id) REFERENCES clientes(id),
                FOREIGN KEY (vehiculo_id) REFERENCES vehiculos(id),
                FOREIGN KEY (asignado_a) REFERENCES usuarios(id)
            )
        ''')

        # Tabla de servicios/historial
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS servicios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingreso_id INTEGER NOT NULL,
                tipo_servicio TEXT NOT NULL,
                descripcion TEXT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                realizado_por INTEGER,
                FOREIGN KEY (ingreso_id) REFERENCES ingresos(id),
                FOREIGN KEY (realizado_por) REFERENCES usuarios(id)
            )
        ''')

        self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS pagos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ingreso_id INTEGER NOT NULL,
                    monto_total REAL DEFAULT 0,
                    monto_pagado REAL DEFAULT 0,
                    estado_pago TEXT DEFAULT 'Pendiente',
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ultimo_pago REAL DEFAULT 0,
                    ultimo_metodo_pago TEXT,
                    ultimo_fecha_pago TIMESTAMP,
                    ultimo_registrado_por INTEGER,
                    historial_pagos TEXT,
                    notas TEXT,
                    FOREIGN KEY (ingreso_id) REFERENCES ingresos(id),
                    FOREIGN KEY (ultimo_registrado_por) REFERENCES usuarios(id)
                )
            ''')

        # Tabla de mensajes/reportes entre gerente y técnicos
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS mensajes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingreso_id INTEGER NOT NULL,
                de_usuario INTEGER NOT NULL,
                para_usuario INTEGER NOT NULL,
                mensaje TEXT NOT NULL,
                tipo TEXT NOT NULL,
                leido INTEGER DEFAULT 0,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ingreso_id) REFERENCES ingresos(id),
                FOREIGN KEY (de_usuario) REFERENCES usuarios(id),
                FOREIGN KEY (para_usuario) REFERENCES usuarios(id)
            )
        ''')

        self.conn.commit()

    def crear_usuarios_default(self):
        usuarios = [
            ('ejecutivo', self.hash_password('123'), 'Ejecutivo', 'Ejecutivo de Cuenta'),
            ('gerente', self.hash_password('123'), 'Gerente', 'Gerente del Taller')
        ]

        for usuario, password, rol, nombre in usuarios:
            try:
                self.cursor.execute(
                    'INSERT INTO usuarios (usuario, password, rol, nombre) VALUES (?, ?, ?, ?)',
                    (usuario, password, rol, nombre)
                )
            except sqlite3.IntegrityError:
                pass
        self.conn.commit()

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def autenticar(self, usuario, password):
        password_hash = self.hash_password(password)
        self.cursor.execute(
            'SELECT id, rol, nombre FROM usuarios WHERE usuario = ? AND password = ? AND activo = 1',
            (usuario, password_hash)
        )
        return self.cursor.fetchone()


# ======================== VENTANA DE LOGIN ========================
class LoginWindow:
    def __init__(self, root, db):
        self.root = root
        self.db = db
        self.root.title("Alan Automotriz - Login")
        self.root.geometry("450x400")
        self.root.resizable(False, False)

        self.centrar_ventana()

        main_frame = ttk.Frame(root, padding="30")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(main_frame, text="Sistema Alan Automotriz",
                  font=('Arial', 16, 'bold')).grid(row=0, column=0, columnspan=2, pady=20)

        ttk.Label(main_frame, text="Usuario:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.usuario_entry = ttk.Entry(main_frame, width=25)
        self.usuario_entry.grid(row=1, column=1, pady=5)

        ttk.Label(main_frame, text="Contraseña:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.password_entry = ttk.Entry(main_frame, width=25, show="*")
        self.password_entry.grid(row=2, column=1, pady=5)

        ttk.Button(main_frame, text="Iniciar Sesión",
                   command=self.login).grid(row=3, column=0, columnspan=2, pady=10)

        ttk.Separator(main_frame, orient='horizontal').grid(row=4, column=0, columnspan=2,
                                                            sticky='ew', pady=10)

        ttk.Button(main_frame, text="Registrar Nuevo Empleado (Técnico)",
                   command=self.registrar_empleado).grid(row=5, column=0, columnspan=2, pady=5)

        info_frame = ttk.LabelFrame(main_frame, text="Usuarios Predeterminados", padding="10")
        info_frame.grid(row=6, column=0, columnspan=2, pady=10)

        ttk.Label(info_frame, text="ejecutivo.\ngerente.",
                  font=('Arial', 9)).pack()

        self.password_entry.bind('<Return>', lambda e: self.login())

    def centrar_ventana(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def login(self):
        usuario = self.usuario_entry.get()
        password = self.password_entry.get()

        if not usuario or not password:
            messagebox.showerror("Error", "Complete todos los campos")
            return

        resultado = self.db.autenticar(usuario, password)

        if resultado:
            user_id, rol, nombre = resultado
            self.root.destroy()
            self.abrir_sistema(user_id, rol, nombre)
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos")

    def registrar_empleado(self):
        registro_win = tk.Toplevel(self.root)
        registro_win.title("Registrar Nuevo Empleado")
        registro_win.geometry("400x350")
        registro_win.resizable(False, False)

        frame = ttk.Frame(registro_win, padding="20")
        frame.pack(fill='both', expand=True)

        ttk.Label(frame, text="Registrar Empleado Técnico",
                  font=('Arial', 14, 'bold')).grid(row=0, column=0, columnspan=2, pady=15)

        ttk.Label(frame, text="Nombre Completo:").grid(row=1, column=0, sticky=tk.W, pady=5)
        nombre_entry = ttk.Entry(frame, width=30)
        nombre_entry.grid(row=1, column=1, pady=5)

        ttk.Label(frame, text="Usuario:").grid(row=2, column=0, sticky=tk.W, pady=5)
        usuario_entry = ttk.Entry(frame, width=30)
        usuario_entry.grid(row=2, column=1, pady=5)

        ttk.Label(frame, text="Contraseña:").grid(row=3, column=0, sticky=tk.W, pady=5)
        password_entry = ttk.Entry(frame, width=30, show="*")
        password_entry.grid(row=3, column=1, pady=5)

        ttk.Label(frame, text="Confirmar Contraseña:").grid(row=4, column=0, sticky=tk.W, pady=5)
        confirm_entry = ttk.Entry(frame, width=30, show="*")
        confirm_entry.grid(row=4, column=1, pady=5)

        def guardar():
            nombre = nombre_entry.get().strip()
            usuario = usuario_entry.get().strip()
            password = password_entry.get()
            confirm = confirm_entry.get()

            if not all([nombre, usuario, password]):
                messagebox.showerror("Error", "Complete todos los campos")
                return

            if password != confirm:
                messagebox.showerror("Error", "Las contraseñas no coinciden")
                return

            if len(password) < 3:
                messagebox.showerror("Error", "La contraseña debe tener al menos 3 caracteres")
                return

            try:
                password_hash = self.db.hash_password(password)
                self.db.cursor.execute(
                    'INSERT INTO usuarios (usuario, password, rol, nombre) VALUES (?, ?, ?, ?)',
                    (usuario, password_hash, 'Tecnico', nombre)
                )
                self.db.conn.commit()
                messagebox.showinfo("Éxito", f"Empleado '{nombre}' registrado correctamente")
                registro_win.destroy()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "El usuario ya existe")

        ttk.Button(frame, text="Registrar", command=guardar).grid(row=5, column=0,
                                                                  columnspan=2, pady=20)

    def abrir_sistema(self, user_id, rol, nombre):
        root = tk.Tk()
        if rol == 'Ejecutivo':
            EjecutivoWindow(root, self.db, user_id, nombre)
        elif rol == 'Gerente':
            GerenteWindow(root, self.db, user_id, nombre)
        elif rol == 'Tecnico':
            TecnicoWindow(root, self.db, user_id, nombre)
        root.mainloop()


# ======================== VENTANA EJECUTIVO DE CUENTA ========================
class EjecutivoWindow:
    def __init__(self, root, db, user_id, nombre):
        self.root = root
        self.db = db
        self.user_id = user_id
        self.nombre = nombre

        self.root.title(f"Alan Automotriz - {nombre}")
        self.root.geometry("1000x650")

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Pestaña: Gestionar Clientes
        self.tab_clientes = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_clientes, text="Gestionar Clientes")
        self.crear_tab_clientes()

        # Pestaña: Gestionar Vehículos
        self.tab_vehiculos = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_vehiculos, text="Gestionar Vehículos")
        self.crear_tab_vehiculos()

        # Pestaña: Registrar Ingreso
        self.tab_ingreso = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_ingreso, text="Registrar Ingreso")
        self.crear_tab_ingreso()

        # Pestaña: Consultar Ingresos
        self.tab_consulta = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_consulta, text="Consultar Ingresos")
        self.crear_tab_consulta()

        # Pestaña: Historial
        self.tab_historial = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_historial, text="Generar Historial")
        self.crear_tab_historial()

        # Pestaña: Facturación y Pagos
        self.tab_facturacion = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_facturacion, text="Facturación y Pagos")
        self.crear_tab_facturacion()

    def crear_tab_clientes(self):
        frame = ttk.Frame(self.tab_clientes, padding="20")
        frame.pack(fill='both', expand=True)

        # Frame superior - Formulario
        form_frame = ttk.LabelFrame(frame, text="Datos del Cliente", padding="10")
        form_frame.pack(fill='x', pady=10)

        ttk.Label(form_frame, text="Nombre:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.cli_nombre = ttk.Entry(form_frame, width=30)
        self.cli_nombre.grid(row=0, column=1, pady=5, padx=5)

        ttk.Label(form_frame, text="Teléfono:").grid(row=0, column=2, sticky=tk.W, pady=5)
        self.cli_telefono = ttk.Entry(form_frame, width=20)
        self.cli_telefono.grid(row=0, column=3, pady=5, padx=5)

        ttk.Label(form_frame, text="Correo:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.cli_correo = ttk.Entry(form_frame, width=30)
        self.cli_correo.grid(row=1, column=1, pady=5, padx=5)

        ttk.Label(form_frame, text="Dirección:").grid(row=1, column=2, sticky=tk.W, pady=5)
        self.cli_direccion = ttk.Entry(form_frame, width=20)
        self.cli_direccion.grid(row=1, column=3, pady=5, padx=5)

        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=2, column=0, columnspan=4, pady=10)

        ttk.Button(btn_frame, text="Registrar Cliente",
                   command=self.registrar_cliente).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Actualizar Cliente",
                   command=self.actualizar_cliente).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Limpiar",
                   command=self.limpiar_form_cliente).pack(side='left', padx=5)

        # Frame inferior - Lista
        list_frame = ttk.LabelFrame(frame, text="Clientes Registrados", padding="10")
        list_frame.pack(fill='both', expand=True, pady=10)

        search_frame = ttk.Frame(list_frame)
        search_frame.pack(fill='x', pady=5)

        ttk.Label(search_frame, text="Buscar:").pack(side='left', padx=5)
        self.cli_search = ttk.Entry(search_frame, width=30)
        self.cli_search.pack(side='left', padx=5)
        ttk.Button(search_frame, text="Buscar",
                   command=self.buscar_cliente).pack(side='left', padx=5)
        ttk.Button(search_frame, text="Mostrar Todos",
                   command=self.cargar_clientes).pack(side='left', padx=5)

        columns = ('ID', 'Nombre', 'Teléfono', 'Correo', 'Dirección')
        self.tree_clientes = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)

        for col in columns:
            self.tree_clientes.heading(col, text=col)
            self.tree_clientes.column(col, width=150)

        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.tree_clientes.yview)
        self.tree_clientes.configure(yscrollcommand=scrollbar.set)

        self.tree_clientes.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        self.tree_clientes.bind('<Double-Button-1>', self.cargar_cliente_seleccionado)

        btn_actions = ttk.Frame(list_frame)
        btn_actions.pack(fill='x', pady=5)

        ttk.Button(btn_actions, text="Eliminar Cliente",
                   command=self.eliminar_cliente).pack(side='left', padx=5)

        self.cargar_clientes()

    def crear_tab_vehiculos(self):
        frame = ttk.Frame(self.tab_vehiculos, padding="20")
        frame.pack(fill='both', expand=True)

        form_frame = ttk.LabelFrame(frame, text="Datos del Vehículo", padding="10")
        form_frame.pack(fill='x', pady=10)

        ttk.Label(form_frame, text="Marca:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.veh_marca = ttk.Entry(form_frame, width=25)
        self.veh_marca.grid(row=0, column=1, pady=5, padx=5)

        ttk.Label(form_frame, text="Modelo:").grid(row=0, column=2, sticky=tk.W, pady=5)
        self.veh_modelo = ttk.Entry(form_frame, width=25)
        self.veh_modelo.grid(row=0, column=3, pady=5, padx=5)

        ttk.Label(form_frame, text="Placa:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.veh_placa = ttk.Entry(form_frame, width=25)
        self.veh_placa.grid(row=1, column=1, pady=5, padx=5)

        ttk.Label(form_frame, text="Año:").grid(row=1, column=2, sticky=tk.W, pady=5)
        self.veh_anio = ttk.Entry(form_frame, width=25)
        self.veh_anio.grid(row=1, column=3, pady=5, padx=5)

        ttk.Label(form_frame, text="Color:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.veh_color = ttk.Entry(form_frame, width=25)
        self.veh_color.grid(row=2, column=1, pady=5, padx=5)

        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=3, column=0, columnspan=4, pady=10)

        ttk.Button(btn_frame, text="Registrar Vehículo",
                   command=self.registrar_vehiculo).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Actualizar Vehículo",
                   command=self.actualizar_vehiculo).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Limpiar",
                   command=self.limpiar_form_vehiculo).pack(side='left', padx=5)

        list_frame = ttk.LabelFrame(frame, text="Vehículos Registrados", padding="10")
        list_frame.pack(fill='both', expand=True, pady=10)

        search_frame = ttk.Frame(list_frame)
        search_frame.pack(fill='x', pady=5)

        ttk.Label(search_frame, text="Buscar:").pack(side='left', padx=5)
        self.veh_search = ttk.Entry(search_frame, width=30)
        self.veh_search.pack(side='left', padx=5)
        ttk.Button(search_frame, text="Buscar",
                   command=self.buscar_vehiculo).pack(side='left', padx=5)
        ttk.Button(search_frame, text="Mostrar Todos",
                   command=self.cargar_vehiculos).pack(side='left', padx=5)

        columns = ('ID', 'Marca', 'Modelo', 'Placa', 'Año', 'Color')
        self.tree_vehiculos = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)

        for col in columns:
            self.tree_vehiculos.heading(col, text=col)
            self.tree_vehiculos.column(col, width=120)

        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.tree_vehiculos.yview)
        self.tree_vehiculos.configure(yscrollcommand=scrollbar.set)

        self.tree_vehiculos.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        self.tree_vehiculos.bind('<Double-Button-1>', self.cargar_vehiculo_seleccionado)

        btn_actions = ttk.Frame(list_frame)
        btn_actions.pack(fill='x', pady=5)

        ttk.Button(btn_actions, text="Eliminar Vehículo",
                   command=self.eliminar_vehiculo).pack(side='left', padx=5)

        self.cargar_vehiculos()

    def crear_tab_ingreso(self):
        """Crea la pestaña de registro de ingresos con layout optimizado"""

        # Frame principal
        main_frame = ttk.Frame(self.tab_ingreso, padding="15")
        main_frame.pack(fill='both', expand=True)

        # Título
        ttk.Label(main_frame, text="Registrar Ingreso de Vehículo al Taller",
                  font=('Arial', 14, 'bold')).pack(pady=10)

        # ========== FRAME PRINCIPAL CON 2 COLUMNAS ==========
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill='both', expand=True)

        # Columna IZQUIERDA (Clientes y Vehículos)
        left_column = ttk.Frame(content_frame)
        left_column.pack(side='left', fill='both', expand=True, padx=(0, 10))

        # Columna DERECHA (Motivo y Botón)
        right_column = ttk.Frame(content_frame)
        right_column.pack(side='right', fill='both', expand=True, padx=(10, 0))

        # ========== COLUMNA IZQUIERDA: CLIENTES Y VEHÍCULOS ==========

        # ===== SECCIÓN 1: CLIENTES =====
        cliente_frame = ttk.LabelFrame(left_column, text="1️⃣ Seleccionar Cliente (haz clic en una fila)",
                                       padding="10")
        cliente_frame.pack(fill='both', expand=True, pady=(0, 10))

        # Búsqueda de clientes
        search_cli_frame = ttk.Frame(cliente_frame)
        search_cli_frame.pack(fill='x', pady=(0, 5))

        ttk.Label(search_cli_frame, text="🔍").pack(side='left', padx=2)
        self.ing_cli_search = ttk.Entry(search_cli_frame, width=25)
        self.ing_cli_search.pack(side='left', padx=5, fill='x', expand=True)
        ttk.Button(search_cli_frame, text="Buscar",
                   command=self.buscar_cliente_ingreso, width=8).pack(side='left', padx=2)
        ttk.Button(search_cli_frame, text="Todos",
                   command=self.cargar_clientes_ingreso, width=8).pack(side='left', padx=2)

        # Tabla de clientes
        columns = ('ID', 'Nombre', 'Teléfono')
        self.tree_ing_cli = ttk.Treeview(cliente_frame, columns=columns, show='headings', height=6)

        col_widths = {'ID': 40, 'Nombre': 180, 'Teléfono': 100}
        for col in columns:
            self.tree_ing_cli.heading(col, text=col)
            self.tree_ing_cli.column(col, width=col_widths[col])

        scroll_cli = ttk.Scrollbar(cliente_frame, orient='vertical', command=self.tree_ing_cli.yview)
        self.tree_ing_cli.configure(yscrollcommand=scroll_cli.set)

        self.tree_ing_cli.pack(side='left', fill='both', expand=True)
        scroll_cli.pack(side='right', fill='y')

        # Indicador de selección de cliente
        self.label_cliente_seleccionado = ttk.Label(cliente_frame, text="❌ Cliente: Ninguno",
                                                    foreground="red", font=('Arial', 9, 'bold'))
        self.label_cliente_seleccionado.pack(pady=5)

        self.tree_ing_cli.bind('<<TreeviewSelect>>', self.actualizar_seleccion_cliente)

        # ===== SECCIÓN 2: VEHÍCULOS =====
        vehiculo_frame = ttk.LabelFrame(left_column, text="2️⃣ Seleccionar Vehículo (haz clic en una fila)",
                                        padding="10")
        vehiculo_frame.pack(fill='both', expand=True)

        # Búsqueda de vehículos
        search_veh_frame = ttk.Frame(vehiculo_frame)
        search_veh_frame.pack(fill='x', pady=(0, 5))

        ttk.Label(search_veh_frame, text="🔍").pack(side='left', padx=2)
        self.ing_veh_search = ttk.Entry(search_veh_frame, width=25)
        self.ing_veh_search.pack(side='left', padx=5, fill='x', expand=True)
        ttk.Button(search_veh_frame, text="Buscar",
                   command=self.buscar_vehiculo_ingreso, width=8).pack(side='left', padx=2)
        ttk.Button(search_veh_frame, text="Todos",
                   command=self.cargar_vehiculos_ingreso, width=8).pack(side='left', padx=2)

        # Tabla de vehículos
        columns = ('ID', 'Marca', 'Modelo', 'Placa')
        self.tree_ing_veh = ttk.Treeview(vehiculo_frame, columns=columns, show='headings', height=6)

        col_widths = {'ID': 40, 'Marca': 90, 'Modelo': 110, 'Placa': 80}
        for col in columns:
            self.tree_ing_veh.heading(col, text=col)
            self.tree_ing_veh.column(col, width=col_widths[col])

        scroll_veh = ttk.Scrollbar(vehiculo_frame, orient='vertical', command=self.tree_ing_veh.yview)
        self.tree_ing_veh.configure(yscrollcommand=scroll_veh.set)

        self.tree_ing_veh.pack(side='left', fill='both', expand=True)
        scroll_veh.pack(side='right', fill='y')

        # Indicador de selección de vehículo
        self.label_vehiculo_seleccionado = ttk.Label(vehiculo_frame, text="❌ Vehículo: Ninguno",
                                                     foreground="red", font=('Arial', 9, 'bold'))
        self.label_vehiculo_seleccionado.pack(pady=5)

        self.tree_ing_veh.bind('<<TreeviewSelect>>', self.actualizar_seleccion_vehiculo)

        # ========== COLUMNA DERECHA: MOTIVO Y BOTÓN ==========

        # ===== SECCIÓN 3: MOTIVO DEL INGRESO =====
        motivo_frame = ttk.LabelFrame(right_column, text="3️⃣ Motivo del Ingreso", padding="15")
        motivo_frame.pack(fill='both', expand=True)

        # Indicadores visuales de selección (resumen)
        resumen_frame = ttk.Frame(motivo_frame)
        resumen_frame.pack(fill='x', pady=(0, 10))

        ttk.Label(resumen_frame, text="📋 RESUMEN DE SELECCIÓN:",
                  font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))

        # Frame para los labels de resumen
        self.label_resumen_cliente = ttk.Label(resumen_frame, text="👤 Cliente: -",
                                               foreground="gray", font=('Arial', 9))
        self.label_resumen_cliente.pack(anchor='w', padx=10)

        self.label_resumen_vehiculo = ttk.Label(resumen_frame, text="🚗 Vehículo: -",
                                                foreground="gray", font=('Arial', 9))
        self.label_resumen_vehiculo.pack(anchor='w', padx=10, pady=2)

        ttk.Separator(motivo_frame, orient='horizontal').pack(fill='x', pady=10)

        # Instrucciones
        ttk.Label(motivo_frame, text="Describa el motivo del ingreso:",
                  font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))

        # Área de texto para el motivo
        self.ing_motivo = scrolledtext.ScrolledText(motivo_frame, width=45, height=15,
                                                    wrap=tk.WORD, font=('Arial', 10))
        self.ing_motivo.pack(fill='both', expand=True, pady=5)

        # Frame de información y ayuda
        info_frame = ttk.Frame(motivo_frame)
        info_frame.pack(fill='x', pady=10)

        ttk.Separator(motivo_frame, orient='horizontal').pack(fill='x', pady=10)

        # BOTÓN GRANDE DE REGISTRO
        btn_frame = ttk.Frame(motivo_frame)
        btn_frame.pack(fill='x', pady=5)

        self.btn_registrar = ttk.Button(btn_frame, text="✅ REGISTRAR INGRESO",
                                        command=self.registrar_ingreso_vehiculo)
        self.btn_registrar.pack(fill='x', ipady=10)

        # Mensaje informativo
        ttk.Label(btn_frame, text="El ingreso vinculará el cliente con el vehículo seleccionado",
                  foreground="blue", font=('Arial', 8, 'italic'),
                  wraplength=350).pack(pady=5)

        # Cargar datos iniciales
        self.cargar_clientes_ingreso()
        self.cargar_vehiculos_ingreso()

    # ========== MÉTODOS AUXILIARES ==========

    def actualizar_seleccion_cliente(self, event):
        """Actualiza los indicadores cuando se selecciona un cliente"""
        selected = self.tree_ing_cli.selection()
        if selected:
            values = self.tree_ing_cli.item(selected[0])['values']
            nombre_cliente = values[1]

            # Actualizar label inferior
            self.label_cliente_seleccionado.config(
                text=f"✅ Cliente: {nombre_cliente}",
                foreground="green"
            )

            # Actualizar resumen
            self.label_resumen_cliente.config(
                text=f"👤 Cliente: {nombre_cliente}",
                foreground="darkgreen",
                font=('Arial', 9, 'bold')
            )
        else:
            self.label_cliente_seleccionado.config(
                text="❌ Cliente: Ninguno",
                foreground="red"
            )
            self.label_resumen_cliente.config(
                text="👤 Cliente: -",
                foreground="gray",
                font=('Arial', 9)
            )

    def actualizar_seleccion_vehiculo(self, event):
        """Actualiza los indicadores cuando se selecciona un vehículo"""
        selected = self.tree_ing_veh.selection()
        if selected:
            values = self.tree_ing_veh.item(selected[0])['values']
            marca = values[1]
            modelo = values[2]
            placa = values[3]

            # Actualizar label inferior
            self.label_vehiculo_seleccionado.config(
                text=f"✅ Vehículo: {marca} {modelo} ({placa})",
                foreground="green"
            )

            # Actualizar resumen
            self.label_resumen_vehiculo.config(
                text=f"🚗 Vehículo: {marca} {modelo} - {placa}",
                foreground="darkgreen",
                font=('Arial', 9, 'bold')
            )
        else:
            self.label_vehiculo_seleccionado.config(
                text="❌ Vehículo: Ninguno",
                foreground="red"
            )
            self.label_resumen_vehiculo.config(
                text="🚗 Vehículo: -",
                foreground="gray",
                font=('Arial', 9)
            )

    def registrar_ingreso_vehiculo(self):
        """Registra el ingreso vinculando cliente con vehículo"""

        # 1. Validar cliente
        sel_cli = self.tree_ing_cli.selection()
        if not sel_cli:
            messagebox.showerror(
                "Error - Cliente no seleccionado",
                "❌ Debe seleccionar un CLIENTE\n\n"
                "Haz clic en una fila de la tabla de clientes"
            )
            return

        # 2. Validar vehículo
        sel_veh = self.tree_ing_veh.selection()
        if not sel_veh:
            messagebox.showerror(
                "Error - Vehículo no seleccionado",
                "❌ Debe seleccionar un VEHÍCULO\n\n"
                "Haz clic en una fila de la tabla de vehículos"
            )
            return

        # 3. Obtener IDs
        cliente_id = self.tree_ing_cli.item(sel_cli[0])['values'][0]
        vehiculo_id = self.tree_ing_veh.item(sel_veh[0])['values'][0]

        # 4. Validar motivo
        motivo = self.ing_motivo.get(1.0, tk.END).strip()
        if not motivo:
            messagebox.showerror(
                "Error - Motivo vacío",
                "❌ Debe escribir el MOTIVO del ingreso\n\n"
                "Describa el problema o servicio requerido"
            )
            return

        # 5. Obtener información para confirmación
        cliente_nombre = self.tree_ing_cli.item(sel_cli[0])['values'][1]
        vehiculo_info = self.tree_ing_veh.item(sel_veh[0])['values']
        vehiculo_texto = f"{vehiculo_info[1]} {vehiculo_info[2]} ({vehiculo_info[3]})"

        # 6. Confirmar
        confirmacion = messagebox.askyesno(
            "Confirmar Registro",
            f"¿Registrar el siguiente ingreso?\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 Cliente: {cliente_nombre}\n"
            f"🚗 Vehículo: {vehiculo_texto}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📝 Motivo:\n{motivo[:100]}{'...' if len(motivo) > 100 else ''}"
        )

        if not confirmacion:
            return

        # 7. Registrar
        try:
            self.db.cursor.execute(
                'INSERT INTO ingresos (cliente_id, vehiculo_id, motivo_ingreso) VALUES (?, ?, ?)',
                (cliente_id, vehiculo_id, motivo)
            )
            ingreso_id = self.db.cursor.lastrowid

            self.db.cursor.execute(
                'INSERT INTO servicios (ingreso_id, tipo_servicio, descripcion, realizado_por) VALUES (?, ?, ?, ?)',
                (ingreso_id, 'Ingreso', f'Vehículo ingresado al taller. Motivo: {motivo}', self.user_id)
            )

            self.db.conn.commit()

            messagebox.showinfo(
                "✅ ¡Ingreso Registrado!",
                f"El ingreso se registró correctamente\n\n"
                f"📋 Folio: #{ingreso_id}\n"
                f"👤 {cliente_nombre}\n"
                f"🚗 {vehiculo_texto}"
            )

            # 8. Limpiar formulario
            self.ing_motivo.delete(1.0, tk.END)
            self.tree_ing_cli.selection_remove(self.tree_ing_cli.selection())
            self.tree_ing_veh.selection_remove(self.tree_ing_veh.selection())

            # Actualizar labels
            self.label_cliente_seleccionado.config(text="❌ Cliente: Ninguno", foreground="red")
            self.label_vehiculo_seleccionado.config(text="❌ Vehículo: Ninguno", foreground="red")
            self.label_resumen_cliente.config(text="👤 Cliente: -", foreground="gray", font=('Arial', 9))
            self.label_resumen_vehiculo.config(text="🚗 Vehículo: -", foreground="gray", font=('Arial', 9))

            # Actualizar vista de ingresos
            self.cargar_ingresos()

        except Exception as e:
            messagebox.showerror("Error", f"❌ Error al registrar:\n\n{str(e)}")
            self.db.conn.rollback()


    def crear_tab_consulta(self):
        frame = ttk.Frame(self.tab_consulta, padding="20")
        frame.pack(fill='both', expand=True)

        search_frame = ttk.Frame(frame)
        search_frame.pack(fill='x', pady=10)

        ttk.Label(search_frame, text="Buscar:").pack(side='left', padx=5)
        self.cons_search = ttk.Entry(search_frame, width=30)
        self.cons_search.pack(side='left', padx=5)
        ttk.Button(search_frame, text="Buscar",
                   command=self.buscar_ingreso).pack(side='left', padx=5)
        ttk.Button(search_frame, text="Mostrar Todos",
                   command=self.cargar_ingresos).pack(side='left', padx=5)

        columns = ('ID', 'Cliente', 'Vehículo', 'Placa', 'Estado', 'Fecha Ingreso', 'Asignado')
        self.tree_ingresos = ttk.Treeview(frame, columns=columns, show='headings', height=12)

        for col in columns:
            self.tree_ingresos.heading(col, text=col)
            self.tree_ingresos.column(col, width=120)

        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=self.tree_ingresos.yview)
        self.tree_ingresos.configure(yscrollcommand=scrollbar.set)

        self.tree_ingresos.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill='x', pady=10)

        ttk.Label(btn_frame, text="Cambiar estado a:").pack(side='left', padx=5)
        self.cons_estado_combo = ttk.Combobox(btn_frame, values=[
            'Ingreso', 'Diagnóstico', 'Hojalatería', 'Pintura',
            'Ensamble', 'Listo', 'Entregado'
        ], width=15)
        self.cons_estado_combo.pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Actualizar Estado",
                   command=self.actualizar_estado_ingreso).pack(side='left', padx=5)

        self.cargar_ingresos()

    def crear_tab_historial(self):
        frame = ttk.Frame(self.tab_historial, padding="20")
        frame.pack(fill='both', expand=True)

        search_frame = ttk.Frame(frame)
        search_frame.pack(fill='x', pady=10)

        ttk.Label(search_frame, text="Buscar cliente o placa:").pack(side='left', padx=5)
        self.hist_search = ttk.Entry(search_frame, width=30)
        self.hist_search.pack(side='left', padx=5)
        ttk.Button(search_frame, text="Generar Historial",
                   command=self.generar_historial).pack(side='left', padx=5)

        self.hist_text = scrolledtext.ScrolledText(frame, width=90, height=30)
        self.hist_text.pack(fill='both', expand=True)

    # ========== MÉTODOS DE CLIENTES ==========
    def registrar_cliente(self):
        nombre = self.cli_nombre.get().strip()
        telefono = self.cli_telefono.get().strip()
        correo = self.cli_correo.get().strip()
        direccion = self.cli_direccion.get().strip()

        if not nombre or not telefono:
            messagebox.showerror("Error", "Nombre y teléfono son obligatorios")
            return

        try:
            self.db.cursor.execute(
                'INSERT INTO clientes (nombre, telefono, correo, direccion) VALUES (?, ?, ?, ?)',
                (nombre, telefono, correo, direccion)
            )
            self.db.conn.commit()
            messagebox.showinfo("Éxito", "Cliente registrado correctamente")
            self.limpiar_form_cliente()
            self.cargar_clientes()
        except Exception as e:
            messagebox.showerror("Error", f"Error al registrar: {str(e)}")

    def actualizar_cliente(self):
        selected = self.tree_clientes.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un cliente")
            return

        cliente_id = self.tree_clientes.item(selected[0])['values'][0]
        nombre = self.cli_nombre.get().strip()
        telefono = self.cli_telefono.get().strip()
        correo = self.cli_correo.get().strip()
        direccion = self.cli_direccion.get().strip()

        if not nombre or not telefono:
            messagebox.showerror("Error", "Nombre y teléfono son obligatorios")
            return

        self.db.cursor.execute(
            'UPDATE clientes SET nombre=?, telefono=?, correo=?, direccion=? WHERE id=?',
            (nombre, telefono, correo, direccion, cliente_id)
        )
        self.db.conn.commit()
        messagebox.showinfo("Éxito", "Cliente actualizado")
        self.limpiar_form_cliente()
        self.cargar_clientes()

    def eliminar_cliente(self):
        selected = self.tree_clientes.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un cliente")
            return

        if messagebox.askyesno("Confirmar", "¿Eliminar este cliente?"):
            cliente_id = self.tree_clientes.item(selected[0])['values'][0]
            self.db.cursor.execute('UPDATE clientes SET activo=0 WHERE id=?', (cliente_id,))
            self.db.conn.commit()
            messagebox.showinfo("Éxito", "Cliente eliminado")
            self.cargar_clientes()

    def cargar_clientes(self):
        for item in self.tree_clientes.get_children():
            self.tree_clientes.delete(item)

        self.db.cursor.execute('SELECT * FROM clientes WHERE activo=1 ORDER BY nombre')
        for row in self.db.cursor.fetchall():
            self.tree_clientes.insert('', 'end', values=row[:-1])

    def buscar_cliente(self):
        busqueda = self.cli_search.get().strip()
        for item in self.tree_clientes.get_children():
            self.tree_clientes.delete(item)

        self.db.cursor.execute(
            'SELECT * FROM clientes WHERE activo=1 AND (nombre LIKE ? OR telefono LIKE ?)',
            (f'%{busqueda}%', f'%{busqueda}%')
        )
        for row in self.db.cursor.fetchall():
            self.tree_clientes.insert('', 'end', values=row[:-1])

    def cargar_cliente_seleccionado(self, event):
        selected = self.tree_clientes.selection()
        if selected:
            values = self.tree_clientes.item(selected[0])['values']
            self.cli_nombre.delete(0, tk.END)
            self.cli_nombre.insert(0, values[1])
            self.cli_telefono.delete(0, tk.END)
            self.cli_telefono.insert(0, values[2])
            self.cli_correo.delete(0, tk.END)
            self.cli_correo.insert(0, values[3] if values[3] else '')
            self.cli_direccion.delete(0, tk.END)
            self.cli_direccion.insert(0, values[4] if values[4] else '')

    def limpiar_form_cliente(self):
        self.cli_nombre.delete(0, tk.END)
        self.cli_telefono.delete(0, tk.END)
        self.cli_correo.delete(0, tk.END)
        self.cli_direccion.delete(0, tk.END)

    # ========== MÉTODOS DE VEHÍCULOS ==========
    def registrar_vehiculo(self):
        marca = self.veh_marca.get().strip()
        modelo = self.veh_modelo.get().strip()
        placa = self.veh_placa.get().strip().upper()
        anio = self.veh_anio.get().strip()
        color = self.veh_color.get().strip()

        if not marca or not modelo or not placa:
            messagebox.showerror("Error", "Marca, modelo y placa son obligatorios")
            return

        try:
            self.db.cursor.execute(
                'INSERT INTO vehiculos (marca, modelo, placa, anio, color) VALUES (?, ?, ?, ?, ?)',
                (marca, modelo, placa, anio, color)
            )
            self.db.conn.commit()
            messagebox.showinfo("Éxito", "Vehículo registrado correctamente")
            self.limpiar_form_vehiculo()
            self.cargar_vehiculos()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "La placa ya está registrada")

    def actualizar_vehiculo(self):
        selected = self.tree_vehiculos.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un vehículo")
            return

        vehiculo_id = self.tree_vehiculos.item(selected[0])['values'][0]
        marca = self.veh_marca.get().strip()
        modelo = self.veh_modelo.get().strip()
        placa = self.veh_placa.get().strip().upper()
        anio = self.veh_anio.get().strip()
        color = self.veh_color.get().strip()

        if not marca or not modelo or not placa:
            messagebox.showerror("Error", "Marca, modelo y placa son obligatorios")
            return

        try:
            self.db.cursor.execute(
                'UPDATE vehiculos SET marca=?, modelo=?, placa=?, anio=?, color=? WHERE id=?',
                (marca, modelo, placa, anio, color, vehiculo_id)
            )
            self.db.conn.commit()
            messagebox.showinfo("Éxito", "Vehículo actualizado")
            self.limpiar_form_vehiculo()
            self.cargar_vehiculos()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "La placa ya está registrada")

    def eliminar_vehiculo(self):
        selected = self.tree_vehiculos.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un vehículo")
            return

        if messagebox.askyesno("Confirmar", "¿Eliminar este vehículo?"):
            vehiculo_id = self.tree_vehiculos.item(selected[0])['values'][0]
            self.db.cursor.execute('UPDATE vehiculos SET activo=0 WHERE id=?', (vehiculo_id,))
            self.db.conn.commit()
            messagebox.showinfo("Éxito", "Vehículo eliminado")
            self.cargar_vehiculos()

    def cargar_vehiculos(self):
        for item in self.tree_vehiculos.get_children():
            self.tree_vehiculos.delete(item)

        self.db.cursor.execute('SELECT * FROM vehiculos WHERE activo=1 ORDER BY marca, modelo')
        for row in self.db.cursor.fetchall():
            self.tree_vehiculos.insert('', 'end', values=row[:-1])

    def buscar_vehiculo(self):
        busqueda = self.veh_search.get().strip()
        for item in self.tree_vehiculos.get_children():
            self.tree_vehiculos.delete(item)

        self.db.cursor.execute(
            '''SELECT * FROM vehiculos WHERE activo=1 AND 
               (marca LIKE ? OR modelo LIKE ? OR placa LIKE ?)''',
            (f'%{busqueda}%', f'%{busqueda}%', f'%{busqueda}%')
        )
        for row in self.db.cursor.fetchall():
            self.tree_vehiculos.insert('', 'end', values=row[:-1])

    def cargar_vehiculo_seleccionado(self, event):
        selected = self.tree_vehiculos.selection()
        if selected:
            values = self.tree_vehiculos.item(selected[0])['values']
            self.veh_marca.delete(0, tk.END)
            self.veh_marca.insert(0, values[1])
            self.veh_modelo.delete(0, tk.END)
            self.veh_modelo.insert(0, values[2])
            self.veh_placa.delete(0, tk.END)
            self.veh_placa.insert(0, values[3])
            self.veh_anio.delete(0, tk.END)
            self.veh_anio.insert(0, values[4] if values[4] else '')
            self.veh_color.delete(0, tk.END)
            self.veh_color.insert(0, values[5] if values[5] else '')

    def limpiar_form_vehiculo(self):
        self.veh_marca.delete(0, tk.END)
        self.veh_modelo.delete(0, tk.END)
        self.veh_placa.delete(0, tk.END)
        self.veh_anio.delete(0, tk.END)
        self.veh_color.delete(0, tk.END)

    # ========== MÉTODOS DE INGRESO ==========
    def cargar_clientes_ingreso(self):
        for item in self.tree_ing_cli.get_children():
            self.tree_ing_cli.delete(item)

        self.db.cursor.execute('SELECT id, nombre, telefono FROM clientes WHERE activo=1')
        for row in self.db.cursor.fetchall():
            self.tree_ing_cli.insert('', 'end', values=row)

    def buscar_cliente_ingreso(self):
        busqueda = self.ing_cli_search.get().strip()
        for item in self.tree_ing_cli.get_children():
            self.tree_ing_cli.delete(item)

        self.db.cursor.execute(
            'SELECT id, nombre, telefono FROM clientes WHERE activo=1 AND (nombre LIKE ? OR telefono LIKE ?)',
            (f'%{busqueda}%', f'%{busqueda}%')
        )
        for row in self.db.cursor.fetchall():
            self.tree_ing_cli.insert('', 'end', values=row)

    def cargar_vehiculos_ingreso(self):
        for item in self.tree_ing_veh.get_children():
            self.tree_ing_veh.delete(item)

        self.db.cursor.execute('SELECT id, marca, modelo, placa FROM vehiculos WHERE activo=1')
        for row in self.db.cursor.fetchall():
            self.tree_ing_veh.insert('', 'end', values=row)

    def buscar_vehiculo_ingreso(self):
        busqueda = self.ing_veh_search.get().strip()
        for item in self.tree_ing_veh.get_children():
            self.tree_ing_veh.delete(item)

        self.db.cursor.execute(
            '''SELECT id, marca, modelo, placa FROM vehiculos WHERE activo=1 AND 
               (marca LIKE ? OR modelo LIKE ? OR placa LIKE ?)''',
            (f'%{busqueda}%', f'%{busqueda}%', f'%{busqueda}%')
        )
        for row in self.db.cursor.fetchall():
            self.tree_ing_veh.insert('', 'end', values=row)

    def registrar_ingreso_vehiculo(self):
        sel_cli = self.tree_ing_cli.selection()
        sel_veh = self.tree_ing_veh.selection()

        if not sel_cli or not sel_veh:
            messagebox.showerror("Error", "Seleccione un cliente y un vehículo")
            return

        cliente_id = self.tree_ing_cli.item(sel_cli[0])['values'][0]
        vehiculo_id = self.tree_ing_veh.item(sel_veh[0])['values'][0]
        motivo = self.ing_motivo.get(1.0, tk.END).strip()

        if not motivo:
            messagebox.showerror("Error", "Escriba el motivo del ingreso")
            return

        try:
            self.db.cursor.execute(
                'INSERT INTO ingresos (cliente_id, vehiculo_id, motivo_ingreso) VALUES (?, ?, ?)',
                (cliente_id, vehiculo_id, motivo)
            )
            ingreso_id = self.db.cursor.lastrowid

            self.db.cursor.execute(
                'INSERT INTO servicios (ingreso_id, tipo_servicio, descripcion, realizado_por) VALUES (?, ?, ?, ?)',
                (ingreso_id, 'Ingreso', f'Vehículo ingresado al taller. Motivo: {motivo}', self.user_id)
            )

            self.db.conn.commit()
            messagebox.showinfo("Éxito", "Ingreso registrado correctamente")
            self.ing_motivo.delete(1.0, tk.END)
            self.cargar_ingresos()
        except Exception as e:
            messagebox.showerror("Error", f"Error al registrar: {str(e)}")

    def cargar_ingresos(self):
        for item in self.tree_ingresos.get_children():
            self.tree_ingresos.delete(item)

        self.db.cursor.execute('''
            SELECT i.id, c.nombre, v.marca || ' ' || v.modelo, v.placa, i.estado, 
                   i.fecha_ingreso, COALESCE(u.nombre, 'Sin asignar')
            FROM ingresos i
            JOIN clientes c ON i.cliente_id = c.id
            JOIN vehiculos v ON i.vehiculo_id = v.id
            LEFT JOIN usuarios u ON i.asignado_a = u.id
            ORDER BY i.fecha_ingreso DESC
        ''')
        for row in self.db.cursor.fetchall():
            self.tree_ingresos.insert('', 'end', values=row)

    def buscar_ingreso(self):
        busqueda = self.cons_search.get().strip()
        for item in self.tree_ingresos.get_children():
            self.tree_ingresos.delete(item)

        self.db.cursor.execute('''
            SELECT i.id, c.nombre, v.marca || ' ' || v.modelo, v.placa, i.estado, 
                   i.fecha_ingreso, COALESCE(u.nombre, 'Sin asignar')
            FROM ingresos i
            JOIN clientes c ON i.cliente_id = c.id
            JOIN vehiculos v ON i.vehiculo_id = v.id
            LEFT JOIN usuarios u ON i.asignado_a = u.id
            WHERE c.nombre LIKE ? OR v.placa LIKE ?
            ORDER BY i.fecha_ingreso DESC
        ''', (f'%{busqueda}%', f'%{busqueda}%'))
        for row in self.db.cursor.fetchall():
            self.tree_ingresos.insert('', 'end', values=row)

    def actualizar_estado_ingreso(self):
        selected = self.tree_ingresos.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un ingreso")
            return

        nuevo_estado = self.cons_estado_combo.get()
        if not nuevo_estado:
            messagebox.showwarning("Advertencia", "Seleccione un estado")
            return

        ingreso_id = self.tree_ingresos.item(selected[0])['values'][0]

        self.db.cursor.execute('UPDATE ingresos SET estado=? WHERE id=?', (nuevo_estado, ingreso_id))
        self.db.cursor.execute(
            'INSERT INTO servicios (ingreso_id, tipo_servicio, descripcion, realizado_por) VALUES (?, ?, ?, ?)',
            (ingreso_id, 'Cambio de estado', f'Estado actualizado a: {nuevo_estado}', self.user_id)
        )

        if nuevo_estado == 'Entregado':
            self.db.cursor.execute('UPDATE ingresos SET fecha_entrega=CURRENT_TIMESTAMP WHERE id=?',
                                   (ingreso_id,))

        self.db.conn.commit()
        messagebox.showinfo("Éxito", "Estado actualizado")
        self.cargar_ingresos()

    def generar_historial(self):
        busqueda = self.hist_search.get().strip()
        if not busqueda:
            messagebox.showwarning("Advertencia", "Ingrese un nombre o placa")
            return

        self.hist_text.delete(1.0, tk.END)

        # Consulta mejorada: ordenar por última actividad
        self.db.cursor.execute('''
            SELECT i.id, c.nombre, c.telefono, c.correo, v.marca, v.modelo, v.placa, 
                   v.anio, v.color, i.estado, i.fecha_ingreso, i.fecha_entrega, i.motivo_ingreso,
                   (SELECT MAX(s.fecha) FROM servicios s WHERE s.ingreso_id = i.id) as ultima_actividad
            FROM ingresos i
            JOIN clientes c ON i.cliente_id = c.id
            JOIN vehiculos v ON i.vehiculo_id = v.id
            WHERE c.nombre LIKE ? OR v.placa LIKE ?
            ORDER BY ultima_actividad DESC, i.fecha_ingreso DESC
        ''', (f'%{busqueda}%', f'%{busqueda}%'))

        ingresos = self.db.cursor.fetchall()

        if not ingresos:
            self.hist_text.insert(tk.END, "No se encontraron registros\n")
            return

        # Encabezado
        self.hist_text.insert(tk.END, "╔" + "═" * 78 + "╗\n")
        self.hist_text.insert(tk.END, f"║  📋 HISTORIAL DE SERVICIOS - {len(ingresos)} resultado(s) encontrado(s)".ljust(
            79) + "║\n")
        self.hist_text.insert(tk.END, "║  Ordenado por: Última actividad (más reciente primero)".ljust(79) + "║\n")
        self.hist_text.insert(tk.END, "╚" + "═" * 78 + "╝\n\n")

        for idx, ingreso in enumerate(ingresos, 1):
            ing_id, cli_nom, cli_tel, cli_corr, v_marca, v_modelo, v_placa, v_anio, v_color, \
                estado, f_ing, f_ent, motivo, ultima_actividad = ingreso

            # Separador
            self.hist_text.insert(tk.END, "╔" + "═" * 78 + "╗\n")
            self.hist_text.insert(tk.END, f"║  SERVICIO #{idx} - FOLIO: {ing_id}".ljust(79) + "║\n")
            self.hist_text.insert(tk.END, "╚" + "═" * 78 + "╝\n\n")

            # CLIENTE
            self.hist_text.insert(tk.END, "👤 CLIENTE:\n")
            self.hist_text.insert(tk.END, "─" * 80 + "\n")
            self.hist_text.insert(tk.END, f"   Nombre:    {cli_nom}\n")
            self.hist_text.insert(tk.END, f"   Teléfono:  {cli_tel}\n")
            self.hist_text.insert(tk.END, f"   Correo:    {cli_corr if cli_corr else 'N/A'}\n\n")

            # VEHÍCULO
            self.hist_text.insert(tk.END, "🚗 VEHÍCULO:\n")
            self.hist_text.insert(tk.END, "─" * 80 + "\n")
            self.hist_text.insert(tk.END, f"   {v_marca} {v_modelo}\n")
            self.hist_text.insert(tk.END, f"   Placa:  {v_placa}\n")
            self.hist_text.insert(tk.END, f"   Año:    {v_anio if v_anio else 'N/A'}\n")
            self.hist_text.insert(tk.END, f"   Color:  {v_color if v_color else 'N/A'}\n\n")

            # SERVICIO
            self.hist_text.insert(tk.END, "📊 INFORMACIÓN DEL SERVICIO:\n")
            self.hist_text.insert(tk.END, "─" * 80 + "\n")
            self.hist_text.insert(tk.END, f"   Estado Actual:      {estado}\n")
            self.hist_text.insert(tk.END, f"   Fecha de Ingreso:   {f_ing}\n")
            self.hist_text.insert(tk.END, f"   Fecha de Entrega:   {f_ent if f_ent else 'Pendiente'}\n")
            self.hist_text.insert(tk.END, f"   Última Actividad:   {ultima_actividad if ultima_actividad else 'N/A'}\n")
            self.hist_text.insert(tk.END, f"   Motivo:             {motivo}\n\n")

            # ========== FACTURACIÓN Y PAGOS (CORREGIDO) ==========
            self.hist_text.insert(tk.END, "💰 FACTURACIÓN Y PAGOS:\n")
            self.hist_text.insert(tk.END, "─" * 80 + "\n")

            # 👇 CONSULTA CORREGIDA - usa tabla 'pagos' unificada
            self.db.cursor.execute('''
                SELECT id, monto_total, monto_pagado, estado_pago, fecha_creacion, historial_pagos
                FROM pagos
                WHERE ingreso_id = ?
            ''', (ing_id,))

            pago = self.db.cursor.fetchone()

            if pago:
                import json

                pago_id, monto_total, monto_pagado, estado_pago, fecha_pago, historial_str = pago
                pendiente = monto_total - monto_pagado

                # Símbolo según estado
                if estado_pago == 'Pagado':
                    simbolo = "✅"
                elif estado_pago == 'Parcial':
                    simbolo = "⏳"
                else:
                    simbolo = "⏰"

                self.hist_text.insert(tk.END, f"   {simbolo} Estado: {estado_pago}\n")
                self.hist_text.insert(tk.END, f"   💵 Monto Total:     ${monto_total:,.2f}\n")
                self.hist_text.insert(tk.END, f"   ✅ Monto Pagado:    ${monto_pagado:,.2f}\n")
                self.hist_text.insert(tk.END, f"   ⏳ Pendiente:       ${pendiente:,.2f}\n")
                self.hist_text.insert(tk.END, f"   📅 Fecha:           {fecha_pago}\n\n")

                # Mostrar historial de pagos
                historial_pagos = []
                if historial_str:
                    try:
                        historial_pagos = json.loads(historial_str)
                    except:
                        pass

                if historial_pagos:
                    self.hist_text.insert(tk.END, f"   💳 HISTORIAL ({len(historial_pagos)} pago(s)):\n")
                    self.hist_text.insert(tk.END, "   " + "·" * 76 + "\n")

                    for idx_pago, p in enumerate(historial_pagos, 1):
                        self.hist_text.insert(tk.END, f"\n   Pago #{idx_pago}:\n")
                        self.hist_text.insert(tk.END, f"      • Fecha:  {p.get('fecha', 'N/A')}\n")
                        self.hist_text.insert(tk.END, f"      • Monto:  ${p.get('monto', 0):.2f}\n")
                        self.hist_text.insert(tk.END, f"      • Método: {p.get('metodo', 'N/A')}\n")
                        if p.get('notas'):
                            self.hist_text.insert(tk.END, f"      • Notas:  {p['notas']}\n")
                    self.hist_text.insert(tk.END, "\n")
                else:
                    self.hist_text.insert(tk.END, "   📭 Sin pagos registrados\n\n")
            else:
                self.hist_text.insert(tk.END, "   ❌ SIN PRECIO ESTABLECIDO\n")
                self.hist_text.insert(tk.END, "   Este servicio aún no tiene un precio asignado.\n\n")

            # ========== HISTORIAL DE SERVICIOS ==========
            self.db.cursor.execute('''
                SELECT s.tipo_servicio, s.descripcion, s.fecha, u.nombre
                FROM servicios s
                LEFT JOIN usuarios u ON s.realizado_por = u.id
                WHERE s.ingreso_id = ?
                ORDER BY s.fecha DESC
            ''', (ing_id,))

            servicios = self.db.cursor.fetchall()

            self.hist_text.insert(tk.END, "🔧 HISTORIAL DE SERVICIOS:\n")
            self.hist_text.insert(tk.END, "─" * 80 + "\n")

            if servicios:
                for servicio in servicios:
                    tipo, desc, fecha, usuario = servicio
                    self.hist_text.insert(tk.END, f"   📅 [{fecha}] {tipo}\n")
                    self.hist_text.insert(tk.END, f"      {desc}\n")
                    self.hist_text.insert(tk.END, f"      👤 Por: {usuario if usuario else 'Sistema'}\n\n")
            else:
                self.hist_text.insert(tk.END, "   Sin actividad registrada\n\n")

            # ========== MENSAJES/REPORTES ==========
            self.db.cursor.execute('''
                SELECT m.mensaje, m.tipo, m.fecha, u1.nombre, u2.nombre
                FROM mensajes m
                JOIN usuarios u1 ON m.de_usuario = u1.id
                JOIN usuarios u2 ON m.para_usuario = u2.id
                WHERE m.ingreso_id = ?
                ORDER BY m.fecha DESC
            ''', (ing_id,))

            mensajes = self.db.cursor.fetchall()

            if mensajes:
                self.hist_text.insert(tk.END, "💬 REPORTES Y COMUNICACIONES:\n")
                self.hist_text.insert(tk.END, "─" * 80 + "\n")
                for msg in mensajes:
                    mensaje, tipo, fecha, de_user, para_user = msg
                    self.hist_text.insert(tk.END, f"   📅 [{fecha}] {tipo}\n")
                    self.hist_text.insert(tk.END, f"      De: {de_user} → Para: {para_user}\n")
                    self.hist_text.insert(tk.END, f"      💬 {mensaje}\n\n")

            # Separador final
            self.hist_text.insert(tk.END, "\n" + "═" * 80 + "\n\n")

        # Resumen final
        self.hist_text.insert(tk.END, "\n╔" + "═" * 78 + "╗\n")
        self.hist_text.insert(tk.END,
                              f"║  ✅ Fin del historial - {len(ingresos)} servicio(s) mostrado(s)".ljust(79) + "║\n")
        self.hist_text.insert(tk.END, "╚" + "═" * 78 + "╝\n")

        # Scroll al inicio
        self.hist_text.see("1.0")

    def crear_tab_facturacion(self):
        """Crea la pestaña de facturación y pagos"""

        # Frame principal con scroll
        main_frame = ttk.Frame(self.tab_facturacion)
        main_frame.pack(fill='both', expand=True)

        canvas = tk.Canvas(main_frame, bg='white')
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, padding="20")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # ========== SECCIÓN 1: RESUMEN FINANCIERO ==========
        resumen_frame = ttk.LabelFrame(scrollable_frame, text="📊 Resumen Financiero", padding="15")
        resumen_frame.pack(fill='x', pady=10)

        btn_actualizar_frame = ttk.Frame(resumen_frame)
        btn_actualizar_frame.pack(fill='x', pady=5)

        ttk.Button(btn_actualizar_frame, text="🔄 Actualizar Datos",
                   command=self.actualizar_resumen_financiero).pack(side='left', padx=5)

        # Labels para mostrar estadísticas
        stats_frame = ttk.Frame(resumen_frame)
        stats_frame.pack(fill='x', pady=10)

        # Columna 1: Ingresos del mes
        col1 = ttk.Frame(stats_frame)
        col1.pack(side='left', padx=20, fill='x', expand=True)

        ttk.Label(col1, text="💰 INGRESOS DEL MES",
                  font=('Arial', 11, 'bold')).pack(anchor='w')
        self.label_mes_total = ttk.Label(col1, text="$0.00",
                                         font=('Arial', 16, 'bold'), foreground='green')
        self.label_mes_total.pack(anchor='w')
        self.label_mes_pagado = ttk.Label(col1, text="Pagado: $0.00", foreground='darkgreen')
        self.label_mes_pagado.pack(anchor='w')
        self.label_mes_pendiente = ttk.Label(col1, text="Pendiente: $0.00", foreground='red')
        self.label_mes_pendiente.pack(anchor='w')

        # Columna 2: Ingresos del año
        col2 = ttk.Frame(stats_frame)
        col2.pack(side='left', padx=20, fill='x', expand=True)

        ttk.Label(col2, text="💎 INGRESOS DEL AÑO",
                  font=('Arial', 11, 'bold')).pack(anchor='w')
        self.label_anio_total = ttk.Label(col2, text="$0.00",
                                          font=('Arial', 16, 'bold'), foreground='blue')
        self.label_anio_total.pack(anchor='w')
        self.label_anio_pagado = ttk.Label(col2, text="Pagado: $0.00", foreground='darkblue')
        self.label_anio_pagado.pack(anchor='w')
        self.label_anio_pendiente = ttk.Label(col2, text="Pendiente: $0.00", foreground='red')
        self.label_anio_pendiente.pack(anchor='w')

        # Columna 3: Estadísticas generales
        col3 = ttk.Frame(stats_frame)
        col3.pack(side='left', padx=20, fill='x', expand=True)

        ttk.Label(col3, text="📈 ESTADÍSTICAS",
                  font=('Arial', 11, 'bold')).pack(anchor='w')
        self.label_total_servicios = ttk.Label(col3, text="Servicios: 0")
        self.label_total_servicios.pack(anchor='w')
        self.label_servicios_pagados = ttk.Label(col3, text="Pagados: 0", foreground='green')
        self.label_servicios_pagados.pack(anchor='w')
        self.label_servicios_pendientes = ttk.Label(col3, text="Pendientes: 0", foreground='red')
        self.label_servicios_pendientes.pack(anchor='w')

        # ========== SECCIÓN 2: GESTIONAR FACTURACIÓN ==========
        factura_frame = ttk.LabelFrame(scrollable_frame, text="💵 Gestionar Facturación de Servicios", padding="15")
        factura_frame.pack(fill='x', pady=10)

        # Búsqueda
        search_factura_frame = ttk.Frame(factura_frame)
        search_factura_frame.pack(fill='x', pady=5)

        ttk.Label(search_factura_frame, text="Buscar:").pack(side='left', padx=5)
        self.factura_search = ttk.Entry(search_factura_frame, width=30)
        self.factura_search.pack(side='left', padx=5)
        ttk.Button(search_factura_frame, text="🔍 Buscar",
                   command=self.buscar_facturacion).pack(side='left', padx=5)
        ttk.Button(search_factura_frame, text="Mostrar Todos",
                   command=self.cargar_facturacion).pack(side='left', padx=5)

        # Tabla de servicios facturables
        columns = ('ID', 'Folio', 'Cliente', 'Vehículo', 'Placa', 'Total', 'Pagado', 'Pendiente', 'Estado')
        self.tree_facturacion = ttk.Treeview(factura_frame, columns=columns, show='headings', height=8)

        anchos = [40, 50, 150, 150, 80, 90, 90, 90, 100]
        for col, ancho in zip(columns, anchos):
            self.tree_facturacion.heading(col, text=col)
            self.tree_facturacion.column(col, width=ancho, anchor='center')

        scroll_factura = ttk.Scrollbar(factura_frame, orient='vertical',
                                       command=self.tree_facturacion.yview)
        self.tree_facturacion.configure(yscrollcommand=scroll_factura.set)

        self.tree_facturacion.pack(side='left', fill='both', expand=True)
        scroll_factura.pack(side='right', fill='y')

        # Configurar colores
        self.tree_facturacion.tag_configure('pagado', background='#C8E6C9', foreground='#1B5E20')
        self.tree_facturacion.tag_configure('parcial', background='#FFF9C4', foreground='#F57F17')
        self.tree_facturacion.tag_configure('pendiente', background='#FFCDD2', foreground='#B71C1C')

        # Controles de facturación
        control_factura_frame = ttk.Frame(factura_frame)
        control_factura_frame.pack(fill='x', pady=10)

        ttk.Label(control_factura_frame, text="Monto Total del Servicio: $").pack(side='left', padx=5)
        self.entry_monto_total = ttk.Entry(control_factura_frame, width=12)
        self.entry_monto_total.pack(side='left', padx=5)

        ttk.Button(control_factura_frame, text="💰 Establecer/Actualizar Precio",
                   command=self.establecer_precio_servicio).pack(side='left', padx=10)

        ttk.Button(control_factura_frame, text="📋 Ver Detalle y Pagos",
                   command=self.ver_detalle_facturacion).pack(side='left', padx=5)

        # ========== SECCIÓN 3: REGISTRAR PAGOS ==========
        pago_frame = ttk.LabelFrame(scrollable_frame, text="💳 Registrar Pago", padding="15")
        pago_frame.pack(fill='x', pady=10)

        ttk.Label(pago_frame, text="Servicio seleccionado:").pack(anchor='w', pady=5)
        self.label_servicio_seleccionado = ttk.Label(pago_frame, text="Ninguno",
                                                     font=('Arial', 10, 'bold'), foreground='red')
        self.label_servicio_seleccionado.pack(anchor='w')

        form_pago_frame = ttk.Frame(pago_frame)
        form_pago_frame.pack(fill='x', pady=10)

        ttk.Label(form_pago_frame, text="Monto a pagar: $").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.entry_monto_pago = ttk.Entry(form_pago_frame, width=15)
        self.entry_monto_pago.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form_pago_frame, text="Método de pago:").grid(row=0, column=2, padx=5, pady=5, sticky='w')
        self.combo_metodo_pago = ttk.Combobox(form_pago_frame, width=15, values=[
            'Efectivo', 'Tarjeta', 'Transferencia', 'Cheque', 'Otro'
        ])
        self.combo_metodo_pago.grid(row=0, column=3, padx=5, pady=5)
        self.combo_metodo_pago.set('Efectivo')

        ttk.Label(form_pago_frame, text="Notas:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.entry_notas_pago = ttk.Entry(form_pago_frame, width=60)
        self.entry_notas_pago.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky='ew')

        ttk.Button(pago_frame, text="✅ REGISTRAR PAGO",
                   command=self.registrar_pago).pack(pady=10)

        # Bind para actualizar servicio seleccionado
        self.tree_facturacion.bind('<<TreeviewSelect>>', self.actualizar_servicio_seleccionado)

        # Cargar datos iniciales
        self.cargar_facturacion()
        self.actualizar_resumen_financiero()

    def actualizar_servicio_seleccionado(self, event):
        """Actualiza la etiqueta del servicio seleccionado para pago"""
        selected = self.tree_facturacion.selection()
        if selected:
            values = self.tree_facturacion.item(selected[0])['values']
            cliente = values[2]
            vehiculo = values[3]
            total = values[5]
            pendiente = values[7]

            self.label_servicio_seleccionado.config(
                text=f"✓ {cliente} - {vehiculo} | Total: {total} | Pendiente: {pendiente}",
                foreground="green"
            )
        else:
            self.label_servicio_seleccionado.config(
                text="Ninguno",
                foreground="red"
            )

    def cargar_facturacion(self):
        for item in self.tree_facturacion.get_children():
            self.tree_facturacion.delete(item)

        # Consulta simplificada - ya no necesita LEFT JOIN
        self.db.cursor.execute('''
            SELECT 
                p.id,
                i.id,
                c.nombre,
                v.marca || ' ' || v.modelo,
                v.placa,
                COALESCE(p.monto_total, 0),
                COALESCE(p.monto_pagado, 0),
                COALESCE(p.monto_total, 0) - COALESCE(p.monto_pagado, 0),
                COALESCE(p.estado_pago, 'Sin precio')
            FROM ingresos i
            JOIN clientes c ON i.cliente_id = c.id
            JOIN vehiculos v ON i.vehiculo_id = v.id
            LEFT JOIN pagos p ON i.id = p.ingreso_id
            ORDER BY i.fecha_ingreso DESC
        ''')

        for row in self.db.cursor.fetchall():
            pago_id, ingreso_id, cliente, vehiculo, placa, total, pagado, pendiente, estado = row

            if estado == 'Pagado':
                tag = 'pagado'
            elif estado == 'Parcial':
                tag = 'parcial'
            else:
                tag = 'pendiente'

            valores = (
                pago_id if pago_id else 'N/A',
                ingreso_id,
                cliente,
                vehiculo,
                placa,
                f'${total:.2f}',
                f'${pagado:.2f}',
                f'${pendiente:.2f}',
                estado
            )

            self.tree_facturacion.insert('', 'end', values=valores, tags=(tag,))

    def buscar_facturacion(self):
        """Busca en la facturación"""
        busqueda = self.factura_search.get().strip()

        for item in self.tree_facturacion.get_children():
            self.tree_facturacion.delete(item)

        self.db.cursor.execute('''
            SELECT 
                f.id,
                i.id,
                c.nombre,
                v.marca || ' ' || v.modelo,
                v.placa,
                COALESCE(f.monto_total, 0),
                COALESCE(f.monto_pagado, 0),
                COALESCE(f.monto_total, 0) - COALESCE(f.monto_pagado, 0),
                f.estado_pago
            FROM ingresos i
            JOIN clientes c ON i.cliente_id = c.id
            JOIN vehiculos v ON i.vehiculo_id = v.id
            LEFT JOIN pagos f ON i.id = f.ingreso_id
            WHERE c.nombre LIKE ? OR v.placa LIKE ?
            ORDER BY i.fecha_ingreso DESC
        ''', (f'%{busqueda}%', f'%{busqueda}%'))

        for row in self.db.cursor.fetchall():
            factura_id, ingreso_id, cliente, vehiculo, placa, total, pagado, pendiente, estado = row

            if not estado:
                estado = 'Sin precio'

            if estado == 'Pagado':
                tag = 'pagado'
            elif estado == 'Parcial':
                tag = 'parcial'
            else:
                tag = 'pendiente'

            valores = (
                factura_id if factura_id else 'N/A',
                ingreso_id,
                cliente,
                vehiculo,
                placa,
                f'${total:.2f}',
                f'${pagado:.2f}',
                f'${pendiente:.2f}',
                estado
            )

            self.tree_facturacion.insert('', 'end', values=valores, tags=(tag,))

    def establecer_precio_servicio(self):
        selected = self.tree_facturacion.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "⚠️ Seleccione un servicio de la tabla")
            return

        monto_str = self.entry_monto_total.get().strip()
        if not monto_str:
            messagebox.showwarning("Advertencia", "⚠️ Ingrese el monto total del servicio")
            return

        try:
            monto = float(monto_str)
            if monto < 0:
                raise ValueError("El monto no puede ser negativo")
        except ValueError:
            messagebox.showerror("Error", "❌ Ingrese un monto válido")
            return

        values = self.tree_facturacion.item(selected[0])['values']
        ingreso_id = values[1]

        # Verificar si ya existe registro de pago
        self.db.cursor.execute('SELECT id, monto_pagado FROM pagos WHERE ingreso_id = ?', (ingreso_id,))
        resultado = self.db.cursor.fetchone()

        try:
            if resultado:
                pago_id, monto_pagado = resultado

                # Recalcular estado
                if monto_pagado >= monto:
                    estado = 'Pagado'
                elif monto_pagado > 0:
                    estado = 'Parcial'
                else:
                    estado = 'Pendiente'

                self.db.cursor.execute('''
                    UPDATE pagos 
                    SET monto_total = ?, estado_pago = ?
                    WHERE id = ?
                ''', (monto, estado, pago_id))
            else:
                # Crear nuevo registro
                self.db.cursor.execute('''
                    INSERT INTO pagos (ingreso_id, monto_total, monto_pagado, estado_pago)
                    VALUES (?, ?, 0, 'Pendiente')
                ''', (ingreso_id, monto))

            self.db.conn.commit()
            messagebox.showinfo("✓ Precio Establecido", f"Se estableció el precio: ${monto:.2f}")

            self.entry_monto_total.delete(0, tk.END)
            self.cargar_facturacion()
            self.actualizar_resumen_financiero()

        except Exception as e:
            messagebox.showerror("Error", f"❌ Error: {str(e)}")
            self.db.conn.rollback()

    def registrar_pago(self):
        """Registra un nuevo pago para un servicio usando la interfaz existente"""

        # Verificar que hay un servicio seleccionado
        selection = self.tree_facturacion.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Selecciona un servicio primero")
            return

        # Obtener datos del formulario de la interfaz
        try:
            # Obtener el monto ingresado
            monto_str = self.entry_monto_pago.get().strip()

            # Limpiar el monto (eliminar símbolos de moneda, comas, espacios)
            monto_str = monto_str.replace('$', '').replace(',', '').replace(' ', '')

            # Validar que sea un número
            try:
                monto = float(monto_str)
            except ValueError:
                messagebox.showerror("Error",
                                     f"El monto debe ser un número válido.\nRecibido: '{self.entry_monto_pago.get()}'")
                return

            if monto <= 0:
                messagebox.showerror("Error", "El monto debe ser mayor a 0")
                return

            # Obtener método de pago
            metodo_pago = self.combo_metodo_pago.get()
            if not metodo_pago:
                messagebox.showerror("Error", "Selecciona un método de pago")
                return

            # Obtener notas (opcional)
            notas = self.entry_notas_pago.get().strip()

            # ⚠️ CORRECCIÓN CRÍTICA: Obtener el ingreso_id del servicio seleccionado
            item = self.tree_facturacion.item(selection[0])
            values = item['values']

            # El ingreso_id está en la posición [1], NO en [0]
            # Posición [0] = pago_id (o 'N/A')
            # Posición [1] = ingreso_id ✓
            ingreso_id = values[1]

            # Importar módulos necesarios
            import json
            from datetime import datetime

            # Obtener información actual del pago
            self.db.cursor.execute('''
                SELECT id, monto_total, monto_pagado, historial_pagos, estado_pago
                FROM pagos
                WHERE ingreso_id = ?
            ''', (ingreso_id,))

            pago_registro = self.db.cursor.fetchone()

            if not pago_registro:
                messagebox.showerror("Error", "No se encontró información de pago para este servicio")
                return

            pago_id, monto_total, monto_pagado_actual, historial_json, estado_actual = pago_registro

            # Calcular el monto pendiente
            monto_pendiente = monto_total - (monto_pagado_actual or 0)

            # Advertir si el pago es mayor al pendiente
            if monto > monto_pendiente:
                respuesta = messagebox.askyesno("Confirmar",
                                                f"El monto a pagar (${monto:.2f}) es mayor al pendiente (${monto_pendiente:.2f}).\n\n"
                                                "¿Deseas continuar de todas formas?")
                if not respuesta:
                    return

            # Calcular nuevo monto pagado
            nuevo_monto_pagado = (monto_pagado_actual or 0) + monto

            # Actualizar historial de pagos
            if historial_json:
                try:
                    historial = json.loads(historial_json)
                except:
                    historial = []
            else:
                historial = []

            # Agregar el nuevo pago al historial
            historial.append({
                'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'monto': monto,
                'metodo': metodo_pago,
                'registrado_por': self.user_id,
                'notas': notas if notas else None
            })

            # Determinar el nuevo estado del pago
            if nuevo_monto_pagado >= monto_total:
                nuevo_estado = 'Pagado'
            elif nuevo_monto_pagado > 0:
                nuevo_estado = 'Parcial'
            else:
                nuevo_estado = 'Pendiente'

            # Actualizar el registro en la base de datos
            self.db.cursor.execute('''
                UPDATE pagos
                SET monto_pagado = ?,
                    estado_pago = ?,
                    ultimo_pago = ?,
                    ultimo_metodo_pago = ?,
                    ultimo_fecha_pago = CURRENT_TIMESTAMP,
                    ultimo_registrado_por = ?,
                    historial_pagos = ?
                WHERE ingreso_id = ?
            ''', (nuevo_monto_pagado, nuevo_estado, monto, metodo_pago,
                  self.user_id, json.dumps(historial), ingreso_id))

            # Guardar cambios
            self.db.conn.commit()

            # Mostrar mensaje de éxito
            messagebox.showinfo("Éxito",
                                f"Pago registrado correctamente\n\n"
                                f"Monto: ${monto:.2f}\n"
                                f"Método: {metodo_pago}\n"
                                f"Nuevo estado: {nuevo_estado}\n"
                                f"Total pagado: ${nuevo_monto_pagado:.2f} de ${monto_total:.2f}")

            # Limpiar los campos del formulario
            self.entry_monto_pago.delete(0, tk.END)
            self.entry_notas_pago.delete(0, tk.END)
            self.combo_metodo_pago.current(0)

            # Recargar la tabla de facturación
            self.cargar_facturacion()

            # Actualizar resumen financiero
            self.actualizar_resumen_financiero()

        except Exception as e:
            messagebox.showerror("Error", f"Error al registrar el pago:\n{str(e)}")
            import traceback
            print("Error completo:")
            print(traceback.format_exc())

    def ver_detalle_facturacion(self):
        import json

        selected = self.tree_facturacion.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "⚠️ Seleccione un servicio")
            return

        values = self.tree_facturacion.item(selected[0])['values']
        pago_id = values[0]

        if pago_id == 'N/A':
            messagebox.showinfo("Sin Facturación", "Este servicio no tiene precio establecido")
            return

        # Obtener información completa
        self.db.cursor.execute('''
            SELECT p.monto_total, p.monto_pagado, p.estado_pago, p.fecha_creacion, 
                   p.historial_pagos, i.id, c.nombre, v.marca || ' ' || v.modelo, v.placa
            FROM pagos p
            JOIN ingresos i ON p.ingreso_id = i.id
            JOIN clientes c ON i.cliente_id = c.id
            JOIN vehiculos v ON i.vehiculo_id = v.id
            WHERE p.id = ?
        ''', (pago_id,))

        pago_info = self.db.cursor.fetchone()
        if not pago_info:
            messagebox.showerror("Error", "No se encontró información")
            return

        monto_total, monto_pagado, estado, fecha_creacion, historial_str, \
            ingreso_id, cliente, vehiculo, placa = pago_info

        pendiente = monto_total - monto_pagado

        # Parsear historial
        historial_pagos = []
        if historial_str:
            try:
                historial_pagos = json.loads(historial_str)
            except:
                historial_pagos = []

        # Crear ventana de detalle
        detalle_win = tk.Toplevel(self.root)
        detalle_win.title("Detalle de Facturación")
        detalle_win.geometry("700x600")

        frame = ttk.Frame(detalle_win, padding="20")
        frame.pack(fill='both', expand=True)

        ttk.Label(frame, text="DETALLE DE FACTURACIÓN",
                  font=('Arial', 14, 'bold')).pack(pady=10)

        info_text = scrolledtext.ScrolledText(frame, width=80, height=30, wrap=tk.WORD)
        info_text.pack(fill='both', expand=True)

        # Escribir información
        info_text.insert(tk.END, "═" * 70 + "\n")
        info_text.insert(tk.END, "  INFORMACIÓN DEL SERVICIO\n")
        info_text.insert(tk.END, "═" * 70 + "\n\n")

        info_text.insert(tk.END, f"📋 Folio: #{ingreso_id}\n")
        info_text.insert(tk.END, f"👤 Cliente: {cliente}\n")
        info_text.insert(tk.END, f"🚗 Vehículo: {vehiculo}\n")
        info_text.insert(tk.END, f"🔖 Placa: {placa}\n")
        info_text.insert(tk.END, f"📅 Fecha: {fecha_creacion}\n\n")

        info_text.insert(tk.END, "═" * 70 + "\n")
        info_text.insert(tk.END, "  RESUMEN FINANCIERO\n")
        info_text.insert(tk.END, "═" * 70 + "\n\n")

        info_text.insert(tk.END, f"💰 Monto Total:     ${monto_total:>12.2f}\n")
        info_text.insert(tk.END, f"✅ Monto Pagado:    ${monto_pagado:>12.2f}\n")
        info_text.insert(tk.END, f"⏳ Pendiente:       ${pendiente:>12.2f}\n")
        info_text.insert(tk.END, f"📊 Estado:          {estado}\n\n")

        if historial_pagos:
            info_text.insert(tk.END, "═" * 70 + "\n")
            info_text.insert(tk.END, f"  HISTORIAL DE PAGOS ({len(historial_pagos)} pago(s))\n")
            info_text.insert(tk.END, "═" * 70 + "\n\n")

            for idx, pago in enumerate(historial_pagos, 1):
                info_text.insert(tk.END, f"PAGO #{idx}\n")
                info_text.insert(tk.END, f"  📅 Fecha:   {pago.get('fecha', 'N/A')}\n")
                info_text.insert(tk.END, f"  💵 Monto:   ${pago.get('monto', 0):.2f}\n")
                info_text.insert(tk.END, f"  💳 Método:  {pago.get('metodo', 'N/A')}\n")

                # Obtener nombre del usuario
                usuario_id = pago.get('registrado_por')
                if usuario_id:
                    self.db.cursor.execute('SELECT nombre FROM usuarios WHERE id = ?', (usuario_id,))
                    usuario = self.db.cursor.fetchone()
                    info_text.insert(tk.END, f"  👤 Por:     {usuario[0] if usuario else 'N/A'}\n")

                if pago.get('notas'):
                    info_text.insert(tk.END, f"  📝 Notas:   {pago['notas']}\n")
                info_text.insert(tk.END, "\n")
        else:
            info_text.insert(tk.END, "═" * 70 + "\n")
            info_text.insert(tk.END, "  📭 Sin pagos registrados\n")
            info_text.insert(tk.END, "═" * 70 + "\n")

        info_text.config(state='disabled')

        ttk.Button(frame, text="Cerrar", command=detalle_win.destroy).pack(pady=10)

    def actualizar_resumen_financiero(self):
        import datetime

        fecha_actual = datetime.datetime.now()
        mes_actual = fecha_actual.month
        anio_actual = fecha_actual.year

        # Estadísticas del mes - tabla unificada
        self.db.cursor.execute('''
            SELECT 
                COUNT(*),
                COALESCE(SUM(monto_total), 0),
                COALESCE(SUM(monto_pagado), 0),
                COALESCE(SUM(monto_total - monto_pagado), 0),
                SUM(CASE WHEN estado_pago = 'Pagado' THEN 1 ELSE 0 END),
                SUM(CASE WHEN estado_pago != 'Pagado' THEN 1 ELSE 0 END)
            FROM pagos
            WHERE strftime('%m', fecha_creacion) = ? 
            AND strftime('%Y', fecha_creacion) = ?
        ''', (f'{mes_actual:02d}', str(anio_actual)))

        mes_data = self.db.cursor.fetchone()

        if mes_data:
            servicios_mes, total_mes, pagado_mes, pendiente_mes, pagados_mes, pendientes_mes = mes_data
            self.label_mes_total.config(text=f"${total_mes:,.2f}")
            self.label_mes_pagado.config(text=f"Pagado: ${pagado_mes:,.2f}")
            self.label_mes_pendiente.config(text=f"Pendiente: ${pendiente_mes:,.2f}")

        # Estadísticas del año
        self.db.cursor.execute('''
            SELECT 
                COUNT(*),
                COALESCE(SUM(monto_total), 0),
                COALESCE(SUM(monto_pagado), 0),
                COALESCE(SUM(monto_total - monto_pagado), 0),
                SUM(CASE WHEN estado_pago = 'Pagado' THEN 1 ELSE 0 END),
                SUM(CASE WHEN estado_pago != 'Pagado' THEN 1 ELSE 0 END)
            FROM pagos
            WHERE strftime('%Y', fecha_creacion) = ?
        ''', (str(anio_actual),))

        anio_data = self.db.cursor.fetchone()

        if anio_data:
            servicios_anio, total_anio, pagado_anio, pendiente_anio, pagados_anio, pendientes_anio = anio_data
            self.label_anio_total.config(text=f"${total_anio:,.2f}")
            self.label_anio_pagado.config(text=f"Pagado: ${pagado_anio:,.2f}")
            self.label_anio_pendiente.config(text=f"Pendiente: ${pendiente_anio:,.2f}")

        # Estadísticas generales
        self.db.cursor.execute('''
            SELECT 
                COUNT(*),
                SUM(CASE WHEN estado_pago = 'Pagado' THEN 1 ELSE 0 END),
                SUM(CASE WHEN estado_pago != 'Pagado' THEN 1 ELSE 0 END)
            FROM pagos
        ''')

        stats = self.db.cursor.fetchone()
        if stats:
            total, pagados, pendientes = stats
            self.label_total_servicios.config(text=f"Servicios: {total if total else 0}")
            self.label_servicios_pagados.config(text=f"Pagados: {pagados if pagados else 0}")
            self.label_servicios_pendientes.config(text=f"Pendientes: {pendientes if pendientes else 0}")

    def crear_tab_facturacion(self):
        """Crea la pestaña de facturación y pagos"""

        # Frame principal con scroll
        main_frame = ttk.Frame(self.tab_facturacion)
        main_frame.pack(fill='both', expand=True)

        canvas = tk.Canvas(main_frame, bg='white')
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, padding="20")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # ========== SECCIÓN 1: RESUMEN FINANCIERO ==========
        resumen_frame = ttk.LabelFrame(scrollable_frame, text="📊 Resumen Financiero", padding="15")
        resumen_frame.pack(fill='x', pady=10)

        btn_actualizar_frame = ttk.Frame(resumen_frame)
        btn_actualizar_frame.pack(fill='x', pady=5)

        ttk.Button(btn_actualizar_frame, text="🔄 Actualizar Datos",
                   command=self.actualizar_resumen_financiero).pack(side='left', padx=5)

        # Labels para mostrar estadísticas
        stats_frame = ttk.Frame(resumen_frame)
        stats_frame.pack(fill='x', pady=10)

        # Columna 1: Ingresos del mes
        col1 = ttk.Frame(stats_frame)
        col1.pack(side='left', padx=20, fill='x', expand=True)

        ttk.Label(col1, text="💰 INGRESOS DEL MES",
                  font=('Arial', 11, 'bold')).pack(anchor='w')
        self.label_mes_total = ttk.Label(col1, text="$0.00",
                                         font=('Arial', 16, 'bold'), foreground='green')
        self.label_mes_total.pack(anchor='w')
        self.label_mes_pagado = ttk.Label(col1, text="Pagado: $0.00", foreground='darkgreen')
        self.label_mes_pagado.pack(anchor='w')
        self.label_mes_pendiente = ttk.Label(col1, text="Pendiente: $0.00", foreground='red')
        self.label_mes_pendiente.pack(anchor='w')

        # Columna 2: Ingresos del año
        col2 = ttk.Frame(stats_frame)
        col2.pack(side='left', padx=20, fill='x', expand=True)

        ttk.Label(col2, text="💎 INGRESOS DEL AÑO",
                  font=('Arial', 11, 'bold')).pack(anchor='w')
        self.label_anio_total = ttk.Label(col2, text="$0.00",
                                          font=('Arial', 16, 'bold'), foreground='blue')
        self.label_anio_total.pack(anchor='w')
        self.label_anio_pagado = ttk.Label(col2, text="Pagado: $0.00", foreground='darkblue')
        self.label_anio_pagado.pack(anchor='w')
        self.label_anio_pendiente = ttk.Label(col2, text="Pendiente: $0.00", foreground='red')
        self.label_anio_pendiente.pack(anchor='w')

        # Columna 3: Estadísticas generales
        col3 = ttk.Frame(stats_frame)
        col3.pack(side='left', padx=20, fill='x', expand=True)

        ttk.Label(col3, text="📈 ESTADÍSTICAS",
                  font=('Arial', 11, 'bold')).pack(anchor='w')
        self.label_total_servicios = ttk.Label(col3, text="Servicios: 0")
        self.label_total_servicios.pack(anchor='w')
        self.label_servicios_pagados = ttk.Label(col3, text="Pagados: 0", foreground='green')
        self.label_servicios_pagados.pack(anchor='w')
        self.label_servicios_pendientes = ttk.Label(col3, text="Pendientes: 0", foreground='red')
        self.label_servicios_pendientes.pack(anchor='w')

        # ========== SECCIÓN 2: GESTIONAR FACTURACIÓN ==========
        factura_frame = ttk.LabelFrame(scrollable_frame, text="💵 Gestionar Facturación de Servicios", padding="15")
        factura_frame.pack(fill='x', pady=10)

        # Búsqueda
        search_factura_frame = ttk.Frame(factura_frame)
        search_factura_frame.pack(fill='x', pady=5)

        ttk.Label(search_factura_frame, text="Buscar:").pack(side='left', padx=5)
        self.factura_search = ttk.Entry(search_factura_frame, width=30)
        self.factura_search.pack(side='left', padx=5)
        ttk.Button(search_factura_frame, text="🔍 Buscar",
                   command=self.buscar_facturacion).pack(side='left', padx=5)
        ttk.Button(search_factura_frame, text="Mostrar Todos",
                   command=self.cargar_facturacion).pack(side='left', padx=5)

        # Tabla de servicios facturables
        columns = ('ID', 'Folio', 'Cliente', 'Vehículo', 'Placa', 'Total', 'Pagado', 'Pendiente', 'Estado')
        self.tree_facturacion = ttk.Treeview(factura_frame, columns=columns, show='headings', height=8)

        anchos = [40, 50, 150, 150, 80, 90, 90, 90, 100]
        for col, ancho in zip(columns, anchos):
            self.tree_facturacion.heading(col, text=col)
            self.tree_facturacion.column(col, width=ancho, anchor='center')

        scroll_factura = ttk.Scrollbar(factura_frame, orient='vertical',
                                       command=self.tree_facturacion.yview)
        self.tree_facturacion.configure(yscrollcommand=scroll_factura.set)

        self.tree_facturacion.pack(side='left', fill='both', expand=True)
        scroll_factura.pack(side='right', fill='y')

        # Configurar colores
        self.tree_facturacion.tag_configure('pagado', background='#C8E6C9', foreground='#1B5E20')
        self.tree_facturacion.tag_configure('parcial', background='#FFF9C4', foreground='#F57F17')
        self.tree_facturacion.tag_configure('pendiente', background='#FFCDD2', foreground='#B71C1C')

        # Controles de facturación
        control_factura_frame = ttk.Frame(factura_frame)
        control_factura_frame.pack(fill='x', pady=10)

        ttk.Label(control_factura_frame, text="Monto Total del Servicio: $").pack(side='left', padx=5)
        self.entry_monto_total = ttk.Entry(control_factura_frame, width=12)
        self.entry_monto_total.pack(side='left', padx=5)

        ttk.Button(control_factura_frame, text="💰 Establecer/Actualizar Precio",
                   command=self.establecer_precio_servicio).pack(side='left', padx=10)

        ttk.Button(control_factura_frame, text="📋 Ver Detalle y Pagos",
                   command=self.ver_detalle_facturacion).pack(side='left', padx=5)

        # ========== SECCIÓN 3: REGISTRAR PAGOS ==========
        pago_frame = ttk.LabelFrame(scrollable_frame, text="💳 Registrar Pago", padding="15")
        pago_frame.pack(fill='x', pady=10)

        ttk.Label(pago_frame, text="Servicio seleccionado:").pack(anchor='w', pady=5)
        self.label_servicio_seleccionado = ttk.Label(pago_frame, text="Ninguno",
                                                     font=('Arial', 10, 'bold'), foreground='red')
        self.label_servicio_seleccionado.pack(anchor='w')

        form_pago_frame = ttk.Frame(pago_frame)
        form_pago_frame.pack(fill='x', pady=10)

        ttk.Label(form_pago_frame, text="Monto a pagar: $").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.entry_monto_pago = ttk.Entry(form_pago_frame, width=15)
        self.entry_monto_pago.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form_pago_frame, text="Método de pago:").grid(row=0, column=2, padx=5, pady=5, sticky='w')
        self.combo_metodo_pago = ttk.Combobox(form_pago_frame, width=15, values=[
            'Efectivo', 'Tarjeta', 'Transferencia', 'Cheque', 'Otro'
        ])
        self.combo_metodo_pago.grid(row=0, column=3, padx=5, pady=5)
        self.combo_metodo_pago.set('Efectivo')

        ttk.Label(form_pago_frame, text="Notas:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.entry_notas_pago = ttk.Entry(form_pago_frame, width=60)
        self.entry_notas_pago.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky='ew')

        ttk.Button(pago_frame, text="✅ REGISTRAR PAGO",
                   command=self.registrar_pago).pack(pady=10)

        # Bind para actualizar servicio seleccionado
        self.tree_facturacion.bind('<<TreeviewSelect>>', self.actualizar_servicio_seleccionado)

        # Cargar datos iniciales
        self.cargar_facturacion()
        self.actualizar_resumen_financiero()

    def actualizar_servicio_seleccionado(self, event):
        """Actualiza la etiqueta del servicio seleccionado para pago"""
        selected = self.tree_facturacion.selection()
        if selected:
            values = self.tree_facturacion.item(selected[0])['values']
            cliente = values[2]
            vehiculo = values[3]
            total = values[5]
            pendiente = values[7]

            self.label_servicio_seleccionado.config(
                text=f"✓ {cliente} - {vehiculo} | Total: ${total} | Pendiente: ${pendiente}",
                foreground="green"
            )
        else:
            self.label_servicio_seleccionado.config(
                text="Ninguno",
                foreground="red"
            )

    def cargar_facturacion(self):
        """Carga todos los servicios con su información de facturación"""
        for item in self.tree_facturacion.get_children():
            self.tree_facturacion.delete(item)

        self.db.cursor.execute('''
                    SELECT 
                        f.id,
                        i.id,
                        c.nombre,
                        v.marca || ' ' || v.modelo,
                        v.placa,
                        COALESCE(f.monto_total, 0),
                        COALESCE(f.monto_pagado, 0),
                        COALESCE(f.monto_total, 0) - COALESCE(f.monto_pagado, 0),
                        f.estado_pago
                    FROM ingresos i
                    JOIN clientes c ON i.cliente_id = c.id
                    JOIN vehiculos v ON i.vehiculo_id = v.id
                    LEFT JOIN pagos f ON i.id = f.ingreso_id
                    ORDER BY i.fecha_ingreso DESC
                ''')

        for row in self.db.cursor.fetchall():
            factura_id, ingreso_id, cliente, vehiculo, placa, total, pagado, pendiente, estado = row

            # Si no tiene factura, crear una pendiente
            if not estado:
                estado = 'Sin precio'

            # Determinar tag de color
            if estado == 'Pagado':
                tag = 'pagado'
            elif estado == 'Parcial':
                tag = 'parcial'
            else:
                tag = 'pendiente'

            valores = (
                factura_id if factura_id else 'N/A',
                ingreso_id,
                cliente,
                vehiculo,
                placa,
                f'${total:.2f}',
                f'${pagado:.2f}',
                f'${pendiente:.2f}',
                estado
            )

            self.tree_facturacion.insert('', 'end', values=valores, tags=(tag,))

    def buscar_facturacion(self):
        """Busca en la facturación"""
        busqueda = self.factura_search.get().strip()

        for item in self.tree_facturacion.get_children():
            self.tree_facturacion.delete(item)

        self.db.cursor.execute('''
                    SELECT 
                        f.id,
                        i.id,
                        c.nombre,
                        v.marca || ' ' || v.modelo,
                        v.placa,
                        COALESCE(f.monto_total, 0),
                        COALESCE(f.monto_pagado, 0),
                        COALESCE(f.monto_total, 0) - COALESCE(f.monto_pagado, 0),
                        f.estado_pago
                    FROM ingresos i
                    JOIN clientes c ON i.cliente_id = c.id
                    JOIN vehiculos v ON i.vehiculo_id = v.id
                    LEFT JOIN pagos f ON i.id = f.ingreso_id
                    WHERE c.nombre LIKE ? OR v.placa LIKE ?
                    ORDER BY i.fecha_ingreso DESC
                ''', (f'%{busqueda}%', f'%{busqueda}%'))

        for row in self.db.cursor.fetchall():
            factura_id, ingreso_id, cliente, vehiculo, placa, total, pagado, pendiente, estado = row

            if not estado:
                estado = 'Sin precio'

            if estado == 'Pagado':
                tag = 'pagado'
            elif estado == 'Parcial':
                tag = 'parcial'
            else:
                tag = 'pendiente'

            valores = (
                factura_id if factura_id else 'N/A',
                ingreso_id,
                cliente,
                vehiculo,
                placa,
                f'${total:.2f}',
                f'${pagado:.2f}',
                f'${pendiente:.2f}',
                estado
            )

            self.tree_facturacion.insert('', 'end', values=valores, tags=(tag,))

    def establecer_precio_servicio(self):
        """Establece o actualiza el precio de un servicio"""
        selected = self.tree_facturacion.selection()
        if not selected:
            messagebox.showwarning(
                "Advertencia",
                "⚠️ Seleccione un servicio de la tabla"
            )
            return

        monto_str = self.entry_monto_total.get().strip()
        if not monto_str:
            messagebox.showwarning(
                "Advertencia",
                "⚠️ Ingrese el monto total del servicio"
            )
            return

        try:
            monto = float(monto_str)
            if monto < 0:
                raise ValueError("El monto no puede ser negativo")
        except ValueError:
            messagebox.showerror(
                "Error",
                "❌ Ingrese un monto válido"
            )
            return

        values = self.tree_facturacion.item(selected[0])['values']
        ingreso_id = values[1]
        cliente = values[2]
        vehiculo = values[3]

        # Verificar si ya existe facturación
        self.db.cursor.execute('SELECT id, monto_pagado FROM pagos WHERE ingreso_id = ?',
                               (ingreso_id,))
        resultado = self.db.cursor.fetchone()

        confirmacion = messagebox.askyesno(
            "Confirmar Precio",
            f"¿Establecer precio del servicio?\n\n"
            f"Cliente: {cliente}\n"
            f"Vehículo: {vehiculo}\n\n"
            f"💰 Monto Total: ${monto:.2f}"
        )

        if not confirmacion:
            return

        try:
            if resultado:
                # Actualizar precio existente
                factura_id, monto_pagado = resultado

                # Recalcular estado
                if monto_pagado >= monto:
                    estado = 'Pagado'
                elif monto_pagado > 0:
                    estado = 'Parcial'
                else:
                    estado = 'Pendiente'

                self.db.cursor.execute('''
                            UPDATE pagos 
                            SET monto_total = ?, estado_pago = ?
                            WHERE id = ?
                        ''', (monto, estado, factura_id))
            else:
                # Crear nueva facturación
                self.db.cursor.execute('''
                            INSERT INTO pagos (ingreso_id, monto_total, monto_pagado, estado_pago)
                            VALUES (?, ?, 0, 'Pendiente')
                        ''', (ingreso_id, monto))

            self.db.conn.commit()

            messagebox.showinfo(
                "✓ Precio Establecido",
                f"Se estableció el precio correctamente\n\n"
                f"💰 Monto: ${monto:.2f}"
            )

            self.entry_monto_total.delete(0, tk.END)
            self.cargar_facturacion()
            self.actualizar_resumen_financiero()

        except Exception as e:
            messagebox.showerror("Error", f"❌ Error al establecer precio:\n\n{str(e)}")
            self.db.conn.rollback()

    def registrar_pago(self):
        """Registra un nuevo pago usando los campos de la interfaz existente (sin ventana emergente)"""

        # Verificar que hay un servicio seleccionado
        selection = self.tree_facturacion.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "⚠️ Selecciona un servicio de la tabla primero")
            return

        try:
            # Obtener el monto ingresado del campo de la interfaz
            monto_str = self.entry_monto_pago.get().strip()

            if not monto_str:
                messagebox.showwarning("Advertencia", "⚠️ Ingresa el monto a pagar")
                return

            # Limpiar el monto (eliminar símbolos de moneda, comas, espacios)
            monto_str = monto_str.replace('$', '').replace(',', '').replace(' ', '')

            # Validar que sea un número
            try:
                monto = float(monto_str)
            except ValueError:
                messagebox.showerror("Error",
                                     f"❌ El monto debe ser un número válido\n\nRecibido: '{self.entry_monto_pago.get()}'")
                return

            if monto <= 0:
                messagebox.showerror("Error", "❌ El monto debe ser mayor a 0")
                return

            # Obtener método de pago del combobox de la interfaz
            metodo_pago = self.combo_metodo_pago.get()
            if not metodo_pago:
                messagebox.showerror("Error", "⚠️ Selecciona un método de pago")
                return

            # Obtener notas del campo de la interfaz
            notas = self.entry_notas_pago.get().strip()

            # Obtener el ingreso_id del servicio seleccionado
            item = self.tree_facturacion.item(selection[0])
            values = item['values']

            # IMPORTANTE: El ingreso_id está en la posición [1]
            ingreso_id = values[1]
            cliente = values[2]
            vehiculo = values[3]

            # Importar módulos necesarios
            import json
            from datetime import datetime

            # Obtener información actual del pago
            self.db.cursor.execute('''
                SELECT id, monto_total, monto_pagado, historial_pagos, estado_pago
                FROM pagos
                WHERE ingreso_id = ?
            ''', (ingreso_id,))

            pago_registro = self.db.cursor.fetchone()

            if not pago_registro:
                messagebox.showerror("Error",
                                     "❌ No se encontró información de pago\n\n"
                                     "Primero debes establecer un precio para este servicio")
                return

            pago_id, monto_total, monto_pagado_actual, historial_json, estado_actual = pago_registro

            # Calcular el monto pendiente
            monto_pendiente = monto_total - (monto_pagado_actual or 0)

            # Advertir si el pago es mayor al pendiente
            if monto > monto_pendiente:
                respuesta = messagebox.askyesno("Confirmar Pago",
                                                f"⚠️ El monto a pagar (${monto:.2f}) es MAYOR\n"
                                                f"al pendiente (${monto_pendiente:.2f})\n\n"
                                                f"¿Deseas continuar de todas formas?")
                if not respuesta:
                    return

            # Confirmar el pago
            confirmacion = messagebox.askyesno(
                "Confirmar Registro de Pago",
                f"¿Registrar el siguiente pago?\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 Cliente: {cliente}\n"
                f"🚗 Vehículo: {vehiculo}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"💵 Monto: ${monto:.2f}\n"
                f"💳 Método: {metodo_pago}\n"
                f"📝 Notas: {notas if notas else '(sin notas)'}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💰 Total del servicio: ${monto_total:.2f}\n"
                f"✅ Ya pagado: ${monto_pagado_actual or 0:.2f}\n"
                f"🔜 Nuevo total pagado: ${(monto_pagado_actual or 0) + monto:.2f}"
            )

            if not confirmacion:
                return

            # Calcular nuevo monto pagado
            nuevo_monto_pagado = (monto_pagado_actual or 0) + monto

            # Actualizar historial de pagos
            if historial_json:
                try:
                    historial = json.loads(historial_json)
                except:
                    historial = []
            else:
                historial = []

            # Agregar el nuevo pago al historial
            historial.append({
                'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'monto': monto,
                'metodo': metodo_pago,
                'registrado_por': self.user_id,
                'notas': notas if notas else None
            })

            # Determinar el nuevo estado del pago
            if nuevo_monto_pagado >= monto_total:
                nuevo_estado = 'Pagado'
            elif nuevo_monto_pagado > 0:
                nuevo_estado = 'Parcial'
            else:
                nuevo_estado = 'Pendiente'

            # Actualizar el registro en la base de datos
            self.db.cursor.execute('''
                UPDATE pagos
                SET monto_pagado = ?,
                    estado_pago = ?,
                    ultimo_pago = ?,
                    ultimo_metodo_pago = ?,
                    ultimo_fecha_pago = CURRENT_TIMESTAMP,
                    ultimo_registrado_por = ?,
                    historial_pagos = ?
                WHERE ingreso_id = ?
            ''', (nuevo_monto_pagado, nuevo_estado, monto, metodo_pago,
                  self.user_id, json.dumps(historial), ingreso_id))

            # Guardar cambios
            self.db.conn.commit()

            # Mostrar mensaje de éxito
            messagebox.showinfo("✅ Pago Registrado",
                                f"Pago registrado correctamente\n\n"
                                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                                f"💵 Monto pagado: ${monto:.2f}\n"
                                f"💳 Método: {metodo_pago}\n"
                                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                                f"📊 Nuevo estado: {nuevo_estado}\n"
                                f"💰 Total pagado: ${nuevo_monto_pagado:.2f} de ${monto_total:.2f}\n"
                                f"⏳ Pendiente: ${monto_total - nuevo_monto_pagado:.2f}")

            # Limpiar los campos del formulario
            self.entry_monto_pago.delete(0, tk.END)
            self.entry_notas_pago.delete(0, tk.END)
            self.combo_metodo_pago.current(0)

            # Recargar la tabla de facturación
            self.cargar_facturacion()

            # Actualizar resumen financiero
            self.actualizar_resumen_financiero()

        except Exception as e:
            messagebox.showerror("Error", f"❌ Error al registrar el pago:\n\n{str(e)}")
            import traceback
            print("Error completo:")
            print(traceback.format_exc())
    def ver_detalle_facturacion(self):
        """Muestra el detalle completo de facturación y pagos"""
        selected = self.tree_facturacion.selection()
        if not selected:
            messagebox.showwarning(
                "Advertencia",
                "⚠️ Seleccione un servicio"
            )
            return

        values = self.tree_facturacion.item(selected[0])['values']
        factura_id = values[0]

        if factura_id == 'N/A':
            messagebox.showinfo(
                "Sin Facturación",
                "Este servicio aún no tiene precio establecido"
            )
            return

        ingreso_id = values[1]
        cliente = values[2]
        vehiculo = values[3]
        placa = values[4]

        # Obtener información completa
        self.db.cursor.execute('''
            SELECT monto_total, monto_pagado, estado_pago, fecha_creacion
            FROM pagos
            WHERE id = ?
        ''', (factura_id,))

        factura_info = self.db.cursor.fetchone()
        if not factura_info:
            return

        monto_total, monto_pagado, estado, fecha_creacion = factura_info
        pendiente = monto_total - monto_pagado

        # Obtener historial de pagos
        self.db.cursor.execute('''
            SELECT p.fecha_pago, p.monto, p.metodo_pago, u.nombre, p.notas
            FROM pagos p
            LEFT JOIN usuarios u ON p.registrado_por = u.id
            WHERE p.facturacion_id = ?
            ORDER BY p.fecha_pago DESC
        ''', (factura_id,))

        pagos = self.db.cursor.fetchall()

        # Crear ventana de detalle
        detalle_win = tk.Toplevel(self.root)
        detalle_win.title("Detalle de Facturación")
        detalle_win.geometry("700x600")

        frame = ttk.Frame(detalle_win, padding="20")
        frame.pack(fill='both', expand=True)

        # Información del servicio
        ttk.Label(frame, text="DETALLE DE FACTURACIÓN",
                  font=('Arial', 14, 'bold')).pack(pady=10)

        info_text = scrolledtext.ScrolledText(frame, width=80, height=30, wrap=tk.WORD)
        info_text.pack(fill='both', expand=True)

        # Escribir información
        info_text.insert(tk.END, "═" * 70 + "\n")
        info_text.insert(tk.END, "  INFORMACIÓN DEL SERVICIO\n")
        info_text.insert(tk.END, "═" * 70 + "\n\n")

        info_text.insert(tk.END, f"📋 Folio de Ingreso: #{ingreso_id}\n")
        info_text.insert(tk.END, f"👤 Cliente: {cliente}\n")
        info_text.insert(tk.END, f"🚗 Vehículo: {vehiculo}\n")
        info_text.insert(tk.END, f"🔖 Placa: {placa}\n")
        info_text.insert(tk.END, f"📅 Fecha de facturación: {fecha_creacion}\n\n")

        info_text.insert(tk.END, "═" * 70 + "\n")
        info_text.insert(tk.END, "  RESUMEN FINANCIERO\n")
        info_text.insert(tk.END, "═" * 70 + "\n\n")

        info_text.insert(tk.END, f"💰 Monto Total:        ${monto_total:>12.2f}\n")
        info_text.insert(tk.END, f"✅ Monto Pagado:       ${monto_pagado:>12.2f}\n")
        info_text.insert(tk.END, f"⏳ Monto Pendiente:    ${pendiente:>12.2f}\n")
        info_text.insert(tk.END, f"📊 Estado:             {estado}\n\n")

        if pagos:
            info_text.insert(tk.END, "═" * 70 + "\n")
            info_text.insert(tk.END, f"  HISTORIAL DE PAGOS ({len(pagos)} pago(s) registrado(s))\n")
            info_text.insert(tk.END, "═" * 70 + "\n\n")

            for idx, pago in enumerate(pagos, 1):
                fecha_pago, monto, metodo, usuario, notas = pago

                info_text.insert(tk.END, f"PAGO #{idx}\n")
                info_text.insert(tk.END, f"  📅 Fecha: {fecha_pago}\n")
                info_text.insert(tk.END, f"  💵 Monto: ${monto:.2f}\n")
                info_text.insert(tk.END, f"  💳 Método: {metodo}\n")
                info_text.insert(tk.END, f"  👤 Registrado por: {usuario if usuario else 'N/A'}\n")
                if notas:
                    info_text.insert(tk.END, f"  📝 Notas: {notas}\n")
                info_text.insert(tk.END, "\n")
        else:
            info_text.insert(tk.END, "═" * 70 + "\n")
            info_text.insert(tk.END, "  📭 Sin pagos registrados\n")
            info_text.insert(tk.END, "═" * 70 + "\n")

        info_text.config(state='disabled')

        ttk.Button(frame, text="Cerrar",
                   command=detalle_win.destroy).pack(pady=10)

    def actualizar_resumen_financiero(self):
        """Actualiza las estadísticas financieras del mes y año"""
        import datetime

        fecha_actual = datetime.datetime.now()
        mes_actual = fecha_actual.month
        anio_actual = fecha_actual.year

        # Estadísticas del mes
        self.db.cursor.execute('''
            SELECT 
                COUNT(*),
                COALESCE(SUM(monto_total), 0),
                COALESCE(SUM(monto_pagado), 0),
                COALESCE(SUM(monto_total - monto_pagado), 0),
                SUM(CASE WHEN estado_pago = 'Pagado' THEN 1 ELSE 0 END),
                SUM(CASE WHEN estado_pago != 'Pagado' THEN 1 ELSE 0 END)
            FROM pagos
            WHERE strftime('%m', fecha_creacion) = ? 
            AND strftime('%Y', fecha_creacion) = ?
        ''', (f'{mes_actual:02d}', str(anio_actual)))

        mes_data = self.db.cursor.fetchone()

        if mes_data:
            servicios_mes, total_mes, pagado_mes, pendiente_mes, pagados_mes, pendientes_mes = mes_data

            self.label_mes_total.config(text=f"${total_mes:,.2f}")
            self.label_mes_pagado.config(text=f"Pagado: ${pagado_mes:,.2f}")
            self.label_mes_pendiente.config(text=f"Pendiente: ${pendiente_mes:,.2f}")

        # Estadísticas del año
        self.db.cursor.execute('''
            SELECT 
                COUNT(*),
                COALESCE(SUM(monto_total), 0),
                COALESCE(SUM(monto_pagado), 0),
                COALESCE(SUM(monto_total - monto_pagado), 0),
                SUM(CASE WHEN estado_pago = 'Pagado' THEN 1 ELSE 0 END),
                SUM(CASE WHEN estado_pago != 'Pagado' THEN 1 ELSE 0 END)
            FROM pagos
            WHERE strftime('%Y', fecha_creacion) = ?
        ''', (str(anio_actual),))

        anio_data = self.db.cursor.fetchone()

        if anio_data:
            servicios_anio, total_anio, pagado_anio, pendiente_anio, pagados_anio, pendientes_anio = anio_data

            self.label_anio_total.config(text=f"${total_anio:,.2f}")
            self.label_anio_pagado.config(text=f"Pagado: ${pagado_anio:,.2f}")
            self.label_anio_pendiente.config(text=f"Pendiente: ${pendiente_anio:,.2f}")

        # Estadísticas generales
        self.db.cursor.execute('''
            SELECT 
                COUNT(*),
                SUM(CASE WHEN estado_pago = 'Pagado' THEN 1 ELSE 0 END),
                SUM(CASE WHEN estado_pago != 'Pagado' THEN 1 ELSE 0 END)
            FROM pagos
        ''')

        stats = self.db.cursor.fetchone()
        if stats:
            total, pagados, pendientes = stats
            self.label_total_servicios.config(text=f"Servicios: {total if total else 0}")
            self.label_servicios_pagados.config(text=f"Pagados: {pagados if pagados else 0}")
            self.label_servicios_pendientes.config(text=f"Pendientes: {pendientes if pendientes else 0}")


# ======================== VENTANA GERENTE ========================
class GerenteWindow:
    def __init__(self, root, db, user_id, nombre):
        self.root = root
        self.db = db
        self.user_id = user_id
        self.nombre = nombre

        self.root.title(f"Alan Automotriz - {nombre}")
        self.root.geometry("1000x650")

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        self.tab_asignar = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_asignar, text="Asignar Servicios")
        self.crear_tab_asignar()

        self.tab_consulta = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_consulta, text="Consultar Vehículos")
        self.crear_tab_consulta()

        self.tab_mensajes = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_mensajes, text="Mensajes/Tareas")
        self.crear_tab_mensajes()

        self.tab_reportes = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_reportes, text="Reportes")
        self.crear_tab_reportes()

        self.tiempos_inicio = {}
        self.plazos = {}
        self.thread_activo = True

        self.root.title(f"Alan Automotriz - {nombre}")
        self.root.geometry("1000x650")


    def crear_tab_asignar(self):
        frame = ttk.Frame(self.tab_asignar, padding="20")
        frame.pack(fill='both', expand=True)

        ttk.Label(frame, text="Vehículos Pendientes de Asignación",
                  font=('Arial', 12, 'bold')).pack(pady=10)

        ttk.Button(frame, text="Actualizar Lista",
                   command=self.cargar_pendientes).pack(pady=5)

        columns = ('ID', 'Cliente', 'Vehículo', 'Placa', 'Estado', 'Fecha')
        self.tree_pendientes = ttk.Treeview(frame, columns=columns, show='headings', height=10)

        for col in columns:
            self.tree_pendientes.heading(col, text=col)
            self.tree_pendientes.column(col, width=130)

        self.tree_pendientes.pack(fill='both', expand=True, pady=10)

        asignar_frame = ttk.LabelFrame(frame, text="Asignar Servicio", padding="10")
        asignar_frame.pack(fill='x', pady=10)

        ttk.Label(asignar_frame, text="Asignar a:").grid(row=0, column=0, padx=5, pady=5)

        self.db.cursor.execute("SELECT id, nombre FROM usuarios WHERE rol='Tecnico' AND activo=1")
        tecnicos = self.db.cursor.fetchall()

        self.tecnico_combo = ttk.Combobox(asignar_frame,
                                          values=[f"{t[0]} - {t[1]}" for t in tecnicos],
                                          width=40)
        self.tecnico_combo.grid(row=0, column=1, padx=5, pady=5)

        ttk.Button(asignar_frame, text="Asignar",
                   command=self.asignar_servicio).grid(row=1, column=0, columnspan=2, pady=10)

        self.cargar_pendientes()

    def crear_tab_consulta(self):
        """Pestaña de consulta con sistema de tiempo y colores"""

        # Variables para control de tiempo
        self.tiempos_inicio = {}
        self.plazos = {}
        self.thread_activo = True

        frame = ttk.Frame(self.tab_consulta, padding="20")
        frame.pack(fill='both', expand=True)

        # Frame de controles superiores
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill='x', pady=10)

        ttk.Button(btn_frame, text="🔄 Actualizar Lista",
                   command=self.cargar_todos_vehiculos).pack(side='left', padx=5)

        ttk.Label(btn_frame, text="Cambiar estado a:").pack(side='left', padx=5)
        self.estado_combo = ttk.Combobox(btn_frame, values=[
            'Ingreso', 'Diagnóstico', 'Hojalatería', 'Pintura',
            'Ensamble', 'Listo', 'Entregado'
        ], width=15)
        self.estado_combo.pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Actualizar Estado",
                   command=self.actualizar_estado).pack(side='left', padx=5)

        # Frame para controles de plazo
        control_frame = ttk.LabelFrame(frame, text="⏱️ Asignar Plazo Personalizado a Vehículo Seleccionado",
                                       padding="10")
        control_frame.pack(fill='x', pady=10)

        ttk.Label(control_frame, text="Días:").pack(side='left', padx=5)
        self.entry_dias = ttk.Entry(control_frame, width=5)
        self.entry_dias.insert(0, "0")
        self.entry_dias.pack(side='left', padx=2)

        ttk.Label(control_frame, text="Horas:").pack(side='left', padx=5)
        self.entry_horas = ttk.Entry(control_frame, width=5)
        self.entry_horas.insert(0, "3")
        self.entry_horas.pack(side='left', padx=2)

        ttk.Label(control_frame, text="Minutos:").pack(side='left', padx=5)
        self.entry_minutos = ttk.Entry(control_frame, width=5)
        self.entry_minutos.insert(0, "0")
        self.entry_minutos.pack(side='left', padx=2)

        ttk.Button(control_frame, text="✓ Asignar y Activar",
                   command=self.asignar_plazo_vehiculo).pack(side='left', padx=10)

        ttk.Button(control_frame, text="⏸ Terminar",
                   command=self.pausar_plazo_vehiculo).pack(side='left', padx=5)

        # Leyenda de colores
        leyenda_frame = ttk.Frame(frame)
        leyenda_frame.pack(fill='x', pady=5)

        ttk.Label(leyenda_frame, text="📊 Leyenda:").pack(side='left', padx=5)
        ttk.Label(leyenda_frame, text="🟢 0-33% (Bien)",
                  foreground="green").pack(side='left', padx=5)
        ttk.Label(leyenda_frame, text="🟠 33-66% (Atención)",
                  foreground="orange").pack(side='left', padx=5)
        ttk.Label(leyenda_frame, text="🔴 66-100% (Urgente)",
                  foreground="red").pack(side='left', padx=5)
        ttk.Label(leyenda_frame, text="🟣 +100% (Retrasado)",
                  foreground="purple").pack(side='left', padx=5)

        # Tabla de vehículos
        columns = ('ID', 'Cliente', 'Vehículo', 'Placa', 'Estado', 'Asignado a', 'Plazo')
        self.tree_todos = ttk.Treeview(frame, columns=columns, show='headings', height=15)

        anchos = [50, 120, 150, 100, 100, 180, 120]
        for col, ancho in zip(columns, anchos):
            self.tree_todos.heading(col, text=col)
            self.tree_todos.column(col, width=ancho, anchor='center')

        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=self.tree_todos.yview)
        self.tree_todos.configure(yscrollcommand=scrollbar.set)

        self.tree_todos.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Configurar tags de colores
        self.tree_todos.tag_configure('verde', background='#4CAF50', foreground='white')
        self.tree_todos.tag_configure('naranja', background='#FF9800', foreground='white')
        self.tree_todos.tag_configure('rojo', background='#F44336', foreground='white')
        self.tree_todos.tag_configure('morado', background='#9C27B0', foreground='white')
        self.tree_todos.tag_configure('blanco', background='white', foreground='black')

        # Cargar datos y comenzar actualización
        self.cargar_todos_vehiculos()
        self.iniciar_actualizacion_tiempo()

    def asignar_plazo_vehiculo(self):
        """Asigna un plazo personalizado al vehículo seleccionado y lo guarda en BD"""
        from datetime import datetime, timedelta

        seleccion = self.tree_todos.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "⚠️ Seleccione un vehículo de la tabla")
            return

        item_id = seleccion[0]
        valores = self.tree_todos.item(item_id)['values']
        ingreso_id = valores[0]

        # Obtener valores de tiempo
        try:
            dias = int(self.entry_dias.get())
            horas = int(self.entry_horas.get())
            minutos = int(self.entry_minutos.get())
        except ValueError:
            messagebox.showerror("Error", "❌ Por favor ingrese números válidos")
            return

        # Validar plazo
        if dias == 0 and horas == 0 and minutos == 0:
            messagebox.showerror("Error", "❌ El plazo debe ser mayor a 0")
            return

        # Crear plazo
        plazo_personalizado = timedelta(days=dias, hours=horas, minutes=minutos)
        tiempo_inicio = datetime.now()

        # Asignar en memoria
        self.tiempos_inicio[item_id] = tiempo_inicio
        self.plazos[item_id] = plazo_personalizado

        # ===== GUARDAR EN BASE DE DATOS =====
        try:
            self.db.cursor.execute('''
                UPDATE ingresos 
                SET plazo_dias = ?, 
                    plazo_horas = ?, 
                    plazo_minutos = ?,
                    fecha_inicio_plazo = ?,
                    plazo_activo = 1
                WHERE id = ?
            ''', (dias, horas, minutos, tiempo_inicio.strftime('%Y-%m-%d %H:%M:%S'), ingreso_id))

            self.db.conn.commit()

            # Registrar en historial de servicios
            self.db.cursor.execute('''
                INSERT INTO servicios (ingreso_id, tipo_servicio, descripcion, realizado_por)
                VALUES (?, ?, ?, ?)
            ''', (ingreso_id, 'Plazo Asignado',
                  f'Plazo establecido: {dias} días, {horas} horas, {minutos} minutos',
                  self.user_id))

            self.db.conn.commit()

        except Exception as e:
            messagebox.showerror("Error", f"❌ Error al guardar plazo:\n{str(e)}")
            return

        # Actualizar vista
        segundos_totales = plazo_personalizado.total_seconds()
        dias_texto = int(segundos_totales // 86400)
        horas_texto = int((segundos_totales % 86400) // 3600)
        minutos_texto = int((segundos_totales % 3600) // 60)
        segundos_texto = int(segundos_totales % 60)

        if dias_texto > 0:
            plazo_texto = f"⏳ {dias_texto}d {horas_texto}h {minutos_texto}m {segundos_texto}s"
        elif horas_texto > 0:
            plazo_texto = f"⏳ {horas_texto}h {minutos_texto}m {segundos_texto}s"
        else:
            plazo_texto = f"⏳ {minutos_texto}m {segundos_texto}s"

        valores_actuales = list(valores)
        while len(valores_actuales) < 7:
            valores_actuales.append('')
        valores_actuales[6] = plazo_texto
        self.tree_todos.item(item_id, values=valores_actuales)

        messagebox.showinfo("✓ Plazo Asignado",
                            f"✅ Plazo guardado y cuenta regresiva iniciada\n\n"
                            f"⏱️ Tiempo asignado: {dias}d {horas}h {minutos}m\n\n"
                            f"💾 El plazo se mantendrá aunque cierres el programa")

    def pausar_plazo_vehiculo(self):
        """Pausa/finaliza el plazo y registra el resultado en historial"""
        from datetime import datetime

        seleccion = self.tree_todos.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "⚠️ Seleccione un vehículo")
            return

        item_id = seleccion[0]
        valores = self.tree_todos.item(item_id)['values']
        ingreso_id = valores[0]

        # Verificar si tiene plazo activo
        if item_id not in self.tiempos_inicio or item_id not in self.plazos:
            messagebox.showinfo("Información", "Este vehículo no tiene un plazo activo")
            return

        # Calcular resultado del plazo
        tiempo_transcurrido = datetime.now() - self.tiempos_inicio[item_id]
        plazo_total = self.plazos[item_id]
        porcentaje = (tiempo_transcurrido.total_seconds() / plazo_total.total_seconds()) * 100

        # Determinar categoría
        if porcentaje < 33:
            categoria = "TEMPRANO"
            emoji = "🟢"
            mensaje = "El trabajo se completó con tiempo de sobra"
        elif porcentaje < 66:
            categoria = "NORMAL"
            emoji = "🟡"
            mensaje = "El trabajo se completó en tiempo adecuado"
        elif porcentaje < 100:
            categoria = "URGENTE"
            emoji = "🟠"
            mensaje = "El trabajo se completó justo a tiempo"
        else:
            categoria = "ATRASADO"
            emoji = "🔴"
            retraso = tiempo_transcurrido - plazo_total
            mensaje = f"El trabajo se completó con retraso de {int(retraso.total_seconds() / 3600)} horas"

        # Confirmar finalización
        confirmacion = messagebox.askyesno(
            "Confirmar Finalización de Plazo",
            f"¿Marcar este plazo como finalizado?\n\n"
            f"{emoji} Categoría: {categoria}\n"
            f"Porcentaje usado: {porcentaje:.1f}%\n\n"
            f"{mensaje}\n\n"
            f"Esto se registrará en el historial del servicio."
        )

        if not confirmacion:
            return

        try:
            # Guardar en base de datos
            self.db.cursor.execute('''
                UPDATE ingresos 
                SET plazo_activo = 0
                WHERE id = ?
            ''', (ingreso_id,))

            # Registrar en historial
            descripcion = (f"Plazo finalizado - Categoría: {categoria} ({porcentaje:.1f}% del tiempo usado). "
                           f"{mensaje}")

            self.db.cursor.execute('''
                INSERT INTO servicios (ingreso_id, tipo_servicio, descripcion, realizado_por)
                VALUES (?, ?, ?, ?)
            ''', (ingreso_id, f'Plazo Finalizado - {categoria}', descripcion, self.user_id))

            self.db.conn.commit()

            # Eliminar de memoria
            if item_id in self.tiempos_inicio:
                del self.tiempos_inicio[item_id]
            if item_id in self.plazos:
                del self.plazos[item_id]

            # Actualizar vista
            self.tree_todos.item(item_id, tags=('blanco',))
            valores_actuales = list(valores)
            while len(valores_actuales) < 7:
                valores_actuales.append('')
            valores_actuales[6] = f'{emoji} Finalizado ({categoria})'
            self.tree_todos.item(item_id, values=valores_actuales)

            messagebox.showinfo("✓ Plazo Finalizado",
                                f"{emoji} Plazo marcado como: {categoria}\n\n"
                                f"Se registró en el historial del servicio")

        except Exception as e:
            messagebox.showerror("Error", f"❌ Error al finalizar plazo:\n{str(e)}")
            self.db.conn.rollback()

    def iniciar_actualizacion_tiempo(self):
        """Inicia el thread que actualiza los colores y tiempo restante"""
        import threading
        import time
        from datetime import datetime

        def actualizar():
            while self.thread_activo:
                try:
                    for item_id in self.tree_todos.get_children():
                        if item_id in self.tiempos_inicio and item_id in self.plazos:
                            tiempo_transcurrido = datetime.now() - self.tiempos_inicio[item_id]
                            plazo = self.plazos[item_id]

                            # Calcular tiempo restante o retraso
                            tiempo_restante = plazo - tiempo_transcurrido
                            segundos_restantes = tiempo_restante.total_seconds()

                            # Calcular porcentaje para el color
                            porcentaje = (tiempo_transcurrido.total_seconds() /
                                          plazo.total_seconds()) * 100

                            # Determinar color
                            if porcentaje < 33:
                                tag = 'verde'
                            elif porcentaje < 66:
                                tag = 'naranja'
                            elif porcentaje < 100:
                                tag = 'rojo'
                            else:
                                tag = 'morado'

                            # Aplicar color
                            self.tree_todos.item(item_id, tags=(tag,))

                            # Formatear el texto del tiempo
                            if segundos_restantes > 0:
                                # Tiempo restante (cuenta regresiva)
                                dias = int(segundos_restantes // 86400)
                                horas = int((segundos_restantes % 86400) // 3600)
                                minutos = int((segundos_restantes % 3600) // 60)
                                segundos = int(segundos_restantes % 60)

                                if dias > 0:
                                    texto_tiempo = f"⏳ {dias}d {horas}h {minutos}m {segundos}s"
                                elif horas > 0:
                                    texto_tiempo = f"⏳ {horas}h {minutos}m {segundos}s"
                                else:
                                    texto_tiempo = f"⏳ {minutos}m {segundos}s"
                            else:
                                # Tiempo de retraso (después de llegar a 0)
                                segundos_retraso = abs(segundos_restantes)
                                dias = int(segundos_retraso // 86400)
                                horas = int((segundos_retraso % 86400) // 3600)
                                minutos = int((segundos_retraso % 3600) // 60)
                                segundos = int(segundos_retraso % 60)

                                if dias > 0:
                                    texto_tiempo = f"🚨 RETRASO: {dias}d {horas}h {minutos}m {segundos}s"
                                elif horas > 0:
                                    texto_tiempo = f"🚨 RETRASO: {horas}h {minutos}m {segundos}s"
                                else:
                                    texto_tiempo = f"🚨 RETRASO: {minutos}m {segundos}s"

                            # Actualizar la columna de plazo
                            valores = list(self.tree_todos.item(item_id, 'values'))
                            if len(valores) >= 7:
                                valores[6] = texto_tiempo
                                self.tree_todos.item(item_id, values=valores)

                    time.sleep(1)  # Actualizar cada segundo
                except:
                    pass

        thread = threading.Thread(target=actualizar, daemon=True)
        thread.start()

    def cargar_todos_vehiculos(self):
        """Carga todos los vehículos CON sus plazos guardados en BD"""
        from datetime import datetime, timedelta

        # GUARDAR plazos actuales en memoria antes de limpiar
        plazos_guardados = {}
        for item_id in self.tree_todos.get_children():
            valores = self.tree_todos.item(item_id)['values']
            if valores:
                ingreso_id = valores[0]
                if item_id in self.tiempos_inicio and item_id in self.plazos:
                    plazos_guardados[ingreso_id] = {
                        'inicio': self.tiempos_inicio[item_id],
                        'plazo': self.plazos[item_id]
                    }

        # Limpiar vista
        for item in self.tree_todos.get_children():
            self.tree_todos.delete(item)

        # Limpiar memoria
        self.tiempos_inicio.clear()
        self.plazos.clear()

        # Cargar datos desde base de datos CON información de plazos
        self.db.cursor.execute('''
            SELECT i.id, c.nombre, v.marca || ' ' || v.modelo, v.placa, i.estado,
                   COALESCE(u.nombre, 'Sin asignar'),
                   i.plazo_dias, i.plazo_horas, i.plazo_minutos, 
                   i.fecha_inicio_plazo, i.plazo_activo
            FROM ingresos i
            JOIN clientes c ON i.cliente_id = c.id
            JOIN vehiculos v ON i.vehiculo_id = v.id
            LEFT JOIN usuarios u ON i.asignado_a = u.id
            ORDER BY i.fecha_ingreso DESC
        ''')

        # RESTAURAR plazos desde la memoria guardada o desde BD
        for row in self.db.cursor.fetchall():
            ingreso_id, cliente, vehiculo, placa, estado, asignado, \
                plazo_dias, plazo_horas, plazo_minutos, fecha_inicio_str, plazo_activo = row

            plazo_texto = 'Sin plazo'
            item_id = None

            # PRIORIDAD 1: Restaurar desde memoria (si existe)
            if ingreso_id in plazos_guardados:
                tiempo_inicio = plazos_guardados[ingreso_id]['inicio']
                plazo_total = plazos_guardados[ingreso_id]['plazo']

                tiempo_transcurrido = datetime.now() - tiempo_inicio
                tiempo_restante = plazo_total - tiempo_transcurrido
                segundos_restantes = tiempo_restante.total_seconds()

                # Formatear texto
                if segundos_restantes > 0:
                    dias = int(segundos_restantes // 86400)
                    horas = int((segundos_restantes % 86400) // 3600)
                    minutos = int((segundos_restantes % 3600) // 60)
                    segundos = int(segundos_restantes % 60)

                    if dias > 0:
                        plazo_texto = f"⏳ {dias}d {horas}h {minutos}m {segundos}s"
                    elif horas > 0:
                        plazo_texto = f"⏳ {horas}h {minutos}m {segundos}s"
                    else:
                        plazo_texto = f"⏳ {minutos}m {segundos}s"
                else:
                    segundos_retraso = abs(segundos_restantes)
                    dias = int(segundos_retraso // 86400)
                    horas = int((segundos_retraso % 86400) // 3600)
                    minutos = int((segundos_retraso % 3600) // 60)

                    if dias > 0:
                        plazo_texto = f"🚨 RETRASO: {dias}d {horas}h {minutos}m"
                    elif horas > 0:
                        plazo_texto = f"🚨 RETRASO: {horas}h {minutos}m"
                    else:
                        plazo_texto = f"🚨 RETRASO: {minutos}m"

                valores_completos = [ingreso_id, cliente, vehiculo, placa, estado, asignado, plazo_texto]
                item_id = self.tree_todos.insert('', 'end', values=valores_completos)

                # RESTAURAR en memoria
                self.tiempos_inicio[item_id] = tiempo_inicio
                self.plazos[item_id] = plazo_total

            # PRIORIDAD 2: Si tiene plazo activo en BD (nuevo ingreso o primera carga)
            elif plazo_activo and fecha_inicio_str:
                try:
                    plazo_total = timedelta(days=plazo_dias or 0,
                                            hours=plazo_horas or 0,
                                            minutes=plazo_minutos or 0)

                    fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d %H:%M:%S')

                    tiempo_transcurrido = datetime.now() - fecha_inicio
                    tiempo_restante = plazo_total - tiempo_transcurrido
                    segundos_restantes = tiempo_restante.total_seconds()

                    if segundos_restantes > 0:
                        dias = int(segundos_restantes // 86400)
                        horas = int((segundos_restantes % 86400) // 3600)
                        minutos = int((segundos_restantes % 3600) // 60)
                        segundos = int(segundos_restantes % 60)

                        if dias > 0:
                            plazo_texto = f"⏳ {dias}d {horas}h {minutos}m {segundos}s"
                        elif horas > 0:
                            plazo_texto = f"⏳ {horas}h {minutos}m {segundos}s"
                        else:
                            plazo_texto = f"⏳ {minutos}m {segundos}s"
                    else:
                        segundos_retraso = abs(segundos_restantes)
                        dias = int(segundos_retraso // 86400)
                        horas = int((segundos_retraso % 86400) // 3600)
                        minutos = int((segundos_retraso % 3600) // 60)

                        if dias > 0:
                            plazo_texto = f"🚨 RETRASO: {dias}d {horas}h {minutos}m"
                        elif horas > 0:
                            plazo_texto = f"🚨 RETRASO: {horas}h {minutos}m"
                        else:
                            plazo_texto = f"🚨 RETRASO: {minutos}m"

                    valores_completos = [ingreso_id, cliente, vehiculo, placa, estado, asignado, plazo_texto]
                    item_id = self.tree_todos.insert('', 'end', values=valores_completos)

                    self.tiempos_inicio[item_id] = fecha_inicio
                    self.plazos[item_id] = plazo_total

                except Exception as e:
                    valores_completos = [ingreso_id, cliente, vehiculo, placa, estado, asignado, 'Error en plazo']
                    self.tree_todos.insert('', 'end', values=valores_completos)

            # PRIORIDAD 3: Plazo finalizado
            elif plazo_dias is not None and not plazo_activo:
                plazo_texto = '✓ Finalizado'
                valores_completos = [ingreso_id, cliente, vehiculo, placa, estado, asignado, plazo_texto]
                self.tree_todos.insert('', 'end', values=valores_completos)

            # PRIORIDAD 4: Sin plazo
            else:
                valores_completos = [ingreso_id, cliente, vehiculo, placa, estado, asignado, plazo_texto]
                self.tree_todos.insert('', 'end', values=valores_completos)

    def crear_tab_mensajes(self):
        """Crea la pestaña de mensajes/tareas con mejor distribución de espacio"""

        # Frame principal con scroll
        main_frame = ttk.Frame(self.tab_mensajes)
        main_frame.pack(fill='both', expand=True)

        # Canvas para permitir scroll
        canvas = tk.Canvas(main_frame, bg='white')
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)

        # Frame scrollable
        scrollable_frame = ttk.Frame(canvas, padding="20")

        # Configurar scroll
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Empacar canvas y scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Scroll con rueda del mouse
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # ========== CONTENIDO ==========

        ttk.Label(scrollable_frame, text="Enviar Tarea/Mensaje a Técnico",
                  font=('Arial', 14, 'bold')).pack(pady=10)

        # ===== SECCIÓN 1: Seleccionar Vehículo =====
        ing_frame = ttk.LabelFrame(scrollable_frame, text="Seleccionar Vehículo", padding="10")
        ing_frame.pack(fill='x', pady=10)

        # Botón para actualizar lista de vehículos
        ttk.Button(ing_frame, text="🔄 Actualizar Lista de Vehículos",
                   command=self.cargar_vehiculos_mensajes).pack(pady=5)

        columns = ('ID', 'Cliente', 'Vehículo', 'Placa', 'Asignado')
        self.tree_msg_ing = ttk.Treeview(ing_frame, columns=columns, show='headings', height=4)

        for col in columns:
            self.tree_msg_ing.heading(col, text=col)
            if col == 'ID':
                self.tree_msg_ing.column(col, width=40)
            elif col == 'Asignado':
                self.tree_msg_ing.column(col, width=200)
            else:
                self.tree_msg_ing.column(col, width=130)

        self.tree_msg_ing.pack(fill='x', pady=5)

        # Indicador de selección
        self.label_vehiculo_msg = ttk.Label(ing_frame, text="Vehículo seleccionado: Ninguno",
                                            foreground="red", font=('Arial', 9, 'bold'))
        self.label_vehiculo_msg.pack(pady=5)

        self.tree_msg_ing.bind('<<TreeviewSelect>>', self.actualizar_seleccion_vehiculo_msg)

        # ===== SECCIÓN 2: Escribir Tarea/Mensaje =====
        msg_frame = ttk.LabelFrame(scrollable_frame, text="Escribir Tarea/Instrucciones", padding="10")
        msg_frame.pack(fill='x', pady=10)

        ttk.Label(msg_frame, text="Escribe las instrucciones detalladas para el técnico:").pack(anchor='w', pady=5)

        # Área de texto más grande
        self.msg_text = scrolledtext.ScrolledText(msg_frame, width=80, height=6)
        self.msg_text.pack(fill='x', pady=5)

        # Ejemplos
        ejemplos_frame = ttk.Frame(msg_frame)
        ejemplos_frame.pack(fill='x', pady=5)
        ttk.Label(ejemplos_frame, text="💡 Ejemplo: 'Revisar frenos delanteros y cambiar pastillas si es necesario'",
                  foreground="gray", font=('Arial', 8, 'italic')).pack(anchor='w')

        # Botón para enviar
        btn_enviar_frame = ttk.Frame(msg_frame)
        btn_enviar_frame.pack(pady=10)

        ttk.Button(btn_enviar_frame, text="📤 Enviar Tarea al Técnico",
                   command=self.enviar_tarea).pack()

        # ===== SECCIÓN 3: Reportes Recibidos =====
        rep_frame = ttk.LabelFrame(scrollable_frame, text="📨 Reportes Recibidos de Técnicos", padding="10")
        rep_frame.pack(fill='both', expand=True, pady=10)

        # Botones de acción
        btn_rep_frame = ttk.Frame(rep_frame)
        btn_rep_frame.pack(fill='x', pady=5)

        ttk.Button(btn_rep_frame, text="🔄 Actualizar Reportes",
                   command=self.cargar_reportes_recibidos).pack(side='left', padx=5)
        ttk.Button(btn_rep_frame, text="✓ Marcar Todos Como Leídos",
                   command=self.marcar_reportes_leidos).pack(side='left', padx=5)

        # Área de texto MUCHO MÁS GRANDE para reportes
        self.rep_text = scrolledtext.ScrolledText(rep_frame, width=80, height=20, wrap=tk.WORD)
        self.rep_text.pack(fill='both', expand=True, pady=5)

        # Configurar colores para mejor lectura
        self.rep_text.tag_configure("nuevo", foreground="red", font=('Arial', 10, 'bold'))
        self.rep_text.tag_configure("leido", foreground="green")
        self.rep_text.tag_configure("fecha", foreground="blue", font=('Arial', 9))
        self.rep_text.tag_configure("vehiculo", foreground="black", font=('Arial', 10, 'bold'))

        # Cargar datos iniciales
        self.cargar_vehiculos_mensajes()
        self.cargar_reportes_recibidos()

    # ========== MÉTODOS AUXILIARES ==========

    def actualizar_seleccion_vehiculo_msg(self, event):
        """Actualiza el indicador cuando se selecciona un vehículo para enviar mensaje"""
        selected = self.tree_msg_ing.selection()
        if selected:
            values = self.tree_msg_ing.item(selected[0])['values']
            cliente = values[1]
            vehiculo = values[2]
            placa = values[3]
            asignado = values[4]

            self.label_vehiculo_msg.config(
                text=f"✓ Vehículo: {vehiculo} ({placa}) - Cliente: {cliente} - Asignado a: {asignado}",
                foreground="green"
            )
        else:
            self.label_vehiculo_msg.config(
                text="Vehículo seleccionado: Ninguno",
                foreground="red"
            )

    def enviar_tarea(self):
        """Envía una tarea/mensaje al técnico asignado a un vehículo"""

        # 1. Validar selección de vehículo
        selected = self.tree_msg_ing.selection()
        if not selected:
            messagebox.showwarning(
                "Advertencia",
                "⚠️ Debe seleccionar un VEHÍCULO\n\n"
                "Haz clic en una fila de la tabla de vehículos"
            )
            return

        # 2. Validar mensaje
        mensaje = self.msg_text.get(1.0, tk.END).strip()
        if not mensaje:
            messagebox.showwarning(
                "Advertencia",
                "⚠️ Debe escribir un MENSAJE\n\n"
                "Escribe las instrucciones para el técnico"
            )
            return

        # 3. Obtener información del vehículo
        ingreso_id = self.tree_msg_ing.item(selected[0])['values'][0]
        vehiculo_info = self.tree_msg_ing.item(selected[0])['values']
        vehiculo_texto = f"{vehiculo_info[2]} ({vehiculo_info[3]})"
        tecnico_nombre = vehiculo_info[4] if vehiculo_info[4] else "Sin asignar"

        # 4. Verificar que tenga técnico asignado
        self.db.cursor.execute('SELECT asignado_a FROM ingresos WHERE id=?', (ingreso_id,))
        result = self.db.cursor.fetchone()

        if not result or not result[0]:
            messagebox.showwarning(
                "Advertencia",
                f"⚠️ Este vehículo NO tiene técnico asignado\n\n"
                f"Vehículo: {vehiculo_texto}\n\n"
                f"Debes asignar un técnico primero en la pestaña\n"
                f"'Asignar Servicios' antes de enviar tareas."
            )
            return

        para_usuario = result[0]

        # 5. Confirmar envío
        confirmacion = messagebox.askyesno(
            "Confirmar Envío de Tarea",
            f"¿Enviar la siguiente tarea?\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🚗 Vehículo: {vehiculo_texto}\n"
            f"👤 Para: {tecnico_nombre}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📝 Mensaje:\n{mensaje[:200]}{'...' if len(mensaje) > 200 else ''}"
        )

        if not confirmacion:
            return

        # 6. Insertar mensaje en base de datos
        try:
            self.db.cursor.execute(
                'INSERT INTO mensajes (ingreso_id, de_usuario, para_usuario, mensaje, tipo) VALUES (?, ?, ?, ?, ?)',
                (ingreso_id, self.user_id, para_usuario, mensaje, 'Tarea del Gerente')
            )
            self.db.conn.commit()

            messagebox.showinfo(
                "✓ Tarea Enviada",
                f"La tarea fue enviada correctamente\n\n"
                f"Para: {tecnico_nombre}\n"
                f"Vehículo: {vehiculo_texto}\n\n"
                f"El técnico verá esta tarea cuando\n"
                f"abra su pestaña 'Tareas del Gerente'"
            )

            # 7. Limpiar formulario
            self.msg_text.delete(1.0, tk.END)

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"❌ Error al enviar la tarea:\n\n{str(e)}"
            )

    def cargar_reportes_recibidos(self):
        """Carga los reportes enviados por los técnicos con mejor formato"""

        self.rep_text.delete(1.0, tk.END)

        self.db.cursor.execute('''
            SELECT m.id, m.fecha, v.placa, v.marca || ' ' || v.modelo, u.nombre, m.mensaje, m.leido, c.nombre
            FROM mensajes m
            JOIN ingresos i ON m.ingreso_id = i.id
            JOIN vehiculos v ON i.vehiculo_id = v.id
            JOIN clientes c ON i.cliente_id = c.id
            JOIN usuarios u ON m.de_usuario = u.id
            WHERE m.para_usuario = ? AND m.tipo = 'Reporte del Técnico'
            ORDER BY m.leido ASC, m.fecha DESC
        ''', (self.user_id,))

        reportes = self.db.cursor.fetchall()

        if not reportes:
            self.rep_text.insert(tk.END, "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
            self.rep_text.insert(tk.END, "  📭 No hay reportes recibidos de los técnicos\n")
            self.rep_text.insert(tk.END, "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n")
            self.rep_text.insert(tk.END, "Los técnicos pueden enviar reportes desde su\n")
            self.rep_text.insert(tk.END, "pestaña 'Enviar Reporte' cuando encuentren\n")
            self.rep_text.insert(tk.END, "problemas o necesiten comunicar algo importante.\n")
            return

        # Contar reportes nuevos
        nuevos = sum(1 for r in reportes if not r[6])

        if nuevos > 0:
            self.rep_text.insert(tk.END, "╔═══════════════════════════════════════════════════════╗\n", "nuevo")
            self.rep_text.insert(tk.END, f"║  🔴 TIENES {nuevos} REPORTE(S) NUEVO(S) SIN LEER  🔴         ║\n", "nuevo")
            self.rep_text.insert(tk.END, "╚═══════════════════════════════════════════════════════╝\n\n", "nuevo")

        # Mostrar cada reporte
        for idx, rep in enumerate(reportes, 1):
            msg_id, fecha, placa, vehiculo, tecnico, mensaje, leido, cliente = rep

            # Separador
            self.rep_text.insert(tk.END, "━" * 70 + "\n")

            # Estado y número
            if leido:
                estado = "✓ LEÍDO"
                tag = "leido"
            else:
                estado = "● NUEVO"
                tag = "nuevo"

            self.rep_text.insert(tk.END, f"#{idx} - {estado}  ", tag)
            self.rep_text.insert(tk.END, f"[{fecha}]\n", "fecha")

            # Información del vehículo
            self.rep_text.insert(tk.END, f"🚗 Vehículo: ", "vehiculo")
            self.rep_text.insert(tk.END, f"{vehiculo} - Placa: {placa}\n")

            self.rep_text.insert(tk.END, f"👤 Cliente: {cliente}\n")
            self.rep_text.insert(tk.END, f"🔧 Técnico: {tecnico}\n\n")

            # Mensaje del reporte
            self.rep_text.insert(tk.END, "📝 REPORTE:\n")
            self.rep_text.insert(tk.END, f"{mensaje}\n\n")

        self.rep_text.insert(tk.END, "━" * 70 + "\n")
        self.rep_text.insert(tk.END,
                             f"\n📊 Total de reportes: {len(reportes)} | Nuevos: {nuevos} | Leídos: {len(reportes) - nuevos}\n")

        # Scroll al inicio
        self.rep_text.see("1.0")

    def marcar_reportes_leidos(self):
        """Marca todos los reportes como leídos"""

        # Contar reportes no leídos
        self.db.cursor.execute('''
            SELECT COUNT(*) FROM mensajes 
            WHERE para_usuario = ? AND tipo = 'Reporte del Técnico' AND leido = 0
        ''', (self.user_id,))

        no_leidos = self.db.cursor.fetchone()[0]

        if no_leidos == 0:
            messagebox.showinfo(
                "Información",
                "✓ No hay reportes nuevos\n\nTodos los reportes ya están marcados como leídos"
            )
            return

        confirmacion = messagebox.askyesno(
            "Confirmar",
            f"¿Marcar {no_leidos} reporte(s) como leído(s)?\n\n"
            f"Esto indicará a los técnicos que ya\n"
            f"revisaste sus reportes."
        )

        if confirmacion:
            self.db.cursor.execute('''
                UPDATE mensajes SET leido = 1 
                WHERE para_usuario = ? AND tipo = 'Reporte del Técnico' AND leido = 0
            ''', (self.user_id,))

            self.db.conn.commit()

            messagebox.showinfo(
                "✓ Actualizado",
                f"Se marcaron {no_leidos} reporte(s) como leídos"
            )

            # Recargar reportes
            self.cargar_reportes_recibidos()

    def crear_tab_reportes(self):
        frame = ttk.Frame(self.tab_reportes, padding="20")
        frame.pack(fill='both', expand=True)

        ttk.Label(frame, text="Reportes del Taller",
                  font=('Arial', 12, 'bold')).pack(pady=10)

        ttk.Button(frame, text="Reporte General",
                   command=self.reporte_general).pack(pady=5)

        self.reporte_text = scrolledtext.ScrolledText(frame, width=80, height=25)
        self.reporte_text.pack(fill='both', expand=True, pady=10)

    def cargar_pendientes(self):
        for item in self.tree_pendientes.get_children():
            self.tree_pendientes.delete(item)

        self.db.cursor.execute('''
            SELECT i.id, c.nombre, v.marca || ' ' || v.modelo, v.placa, i.estado, i.fecha_ingreso
            FROM ingresos i
            JOIN clientes c ON i.cliente_id = c.id
            JOIN vehiculos v ON i.vehiculo_id = v.id
            WHERE i.asignado_a IS NULL AND i.estado != 'Entregado'
            ORDER BY i.fecha_ingreso
        ''')

        for row in self.db.cursor.fetchall():
            self.tree_pendientes.insert('', 'end', values=row)

    def cargar_todos_vehiculos(self):
        for item in self.tree_todos.get_children():
            self.tree_todos.delete(item)

        self.db.cursor.execute('''
            SELECT i.id, c.nombre, v.marca || ' ' || v.modelo, v.placa, i.estado,
                   COALESCE(u.nombre, 'Sin asignar')
            FROM ingresos i
            JOIN clientes c ON i.cliente_id = c.id
            JOIN vehiculos v ON i.vehiculo_id = v.id
            LEFT JOIN usuarios u ON i.asignado_a = u.id
            ORDER BY i.fecha_ingreso DESC
        ''')

        for row in self.db.cursor.fetchall():
            self.tree_todos.insert('', 'end', values=row)

    def asignar_servicio(self):
        selected = self.tree_pendientes.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un vehículo")
            return

        tecnico_str = self.tecnico_combo.get()
        if not tecnico_str:
            messagebox.showwarning("Advertencia", "Seleccione un técnico")
            return

        tecnico_id = int(tecnico_str.split(' - ')[0])
        ingreso_id = self.tree_pendientes.item(selected[0])['values'][0]

        self.db.cursor.execute('UPDATE ingresos SET asignado_a=? WHERE id=?', (tecnico_id, ingreso_id))
        self.db.cursor.execute(
            'INSERT INTO servicios (ingreso_id, tipo_servicio, descripcion, realizado_por) VALUES (?, ?, ?, ?)',
            (ingreso_id, 'Asignación', f'Servicio asignado a técnico ID:{tecnico_id}', self.user_id)
        )

        self.db.conn.commit()
        messagebox.showinfo("Éxito", "Servicio asignado correctamente")

        self.cargar_pendientes()
        self.cargar_todos_vehiculos()

    def actualizar_estado(self):
        """Actualiza el estado del vehículo seleccionado"""
        selected = self.tree_todos.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "⚠️ Seleccione un vehículo")
            return

        nuevo_estado = self.estado_combo.get()
        if not nuevo_estado:
            messagebox.showwarning("Advertencia", "⚠️ Seleccione un estado")
            return

        ingreso_id = self.tree_todos.item(selected[0])['values'][0]

        self.db.cursor.execute('UPDATE ingresos SET estado=? WHERE id=?', (nuevo_estado, ingreso_id))
        self.db.cursor.execute(
            'INSERT INTO servicios (ingreso_id, tipo_servicio, descripcion, realizado_por) VALUES (?, ?, ?, ?)',
            (ingreso_id, 'Cambio de estado', f'Estado actualizado a: {nuevo_estado}', self.user_id)
        )

        self.db.conn.commit()
        messagebox.showinfo("✓ Éxito", f"Estado actualizado a: {nuevo_estado}")
        self.cargar_todos_vehiculos()

    def cargar_vehiculos_mensajes(self):
        for item in self.tree_msg_ing.get_children():
            self.tree_msg_ing.delete(item)

        self.db.cursor.execute('''
            SELECT i.id, c.nombre, v.marca || ' ' || v.modelo, v.placa, u.nombre
            FROM ingresos i
            JOIN clientes c ON i.cliente_id = c.id
            JOIN vehiculos v ON i.vehiculo_id = v.id
            LEFT JOIN usuarios u ON i.asignado_a = u.id
            WHERE i.estado != 'Entregado'
            ORDER BY i.fecha_ingreso DESC
        ''')

        for row in self.db.cursor.fetchall():
            self.tree_msg_ing.insert('', 'end', values=row)

    def enviar_tarea(self):
        selected = self.tree_msg_ing.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un vehículo")
            return

        mensaje = self.msg_text.get(1.0, tk.END).strip()
        if not mensaje:
            messagebox.showwarning("Advertencia", "Escriba un mensaje")
            return

        ingreso_id = self.tree_msg_ing.item(selected[0])['values'][0]

        # Obtener técnico asignado
        self.db.cursor.execute('SELECT asignado_a FROM ingresos WHERE id=?', (ingreso_id,))
        result = self.db.cursor.fetchone()

        if not result or not result[0]:
            messagebox.showwarning("Advertencia", "Este vehículo no tiene técnico asignado")
            return

        para_usuario = result[0]

        self.db.cursor.execute(
            'INSERT INTO mensajes (ingreso_id, de_usuario, para_usuario, mensaje, tipo) VALUES (?, ?, ?, ?, ?)',
            (ingreso_id, self.user_id, para_usuario, mensaje, 'Tarea del Gerente')
        )

        self.db.conn.commit()
        messagebox.showinfo("Éxito", "Tarea enviada al técnico")
        self.msg_text.delete(1.0, tk.END)

    def cargar_reportes_recibidos(self):
        self.rep_text.delete(1.0, tk.END)

        self.db.cursor.execute('''
            SELECT m.fecha, v.placa, v.marca || ' ' || v.modelo, u.nombre, m.mensaje, m.leido
            FROM mensajes m
            JOIN ingresos i ON m.ingreso_id = i.id
            JOIN vehiculos v ON i.vehiculo_id = v.id
            JOIN usuarios u ON m.de_usuario = u.id
            WHERE m.para_usuario = ? AND m.tipo = 'Reporte del Técnico'
            ORDER BY m.fecha DESC
            LIMIT 20
        ''', (self.user_id,))

        reportes = self.db.cursor.fetchall()

        if not reportes:
            self.rep_text.insert(tk.END, "No hay reportes recibidos\n")
            return

        for rep in reportes:
            fecha, placa, vehiculo, tecnico, mensaje, leido = rep
            estado = "✓ Leído" if leido else "● NUEVO"
            self.rep_text.insert(tk.END, f"[{fecha}] {estado}\n")
            self.rep_text.insert(tk.END, f"Vehículo: {vehiculo} - Placa: {placa}\n")
            self.rep_text.insert(tk.END, f"Técnico: {tecnico}\n")
            self.rep_text.insert(tk.END, f"Reporte: {mensaje}\n")
            self.rep_text.insert(tk.END, "-" * 60 + "\n\n")

    def reporte_general(self):
        self.reporte_text.delete(1.0, tk.END)

        self.db.cursor.execute('SELECT COUNT(*) FROM ingresos')
        total = self.db.cursor.fetchone()[0]

        self.db.cursor.execute("SELECT COUNT(*) FROM ingresos WHERE estado='Entregado'")
        entregados = self.db.cursor.fetchone()[0]

        self.db.cursor.execute("SELECT COUNT(*) FROM ingresos WHERE estado!='Entregado'")
        en_proceso = self.db.cursor.fetchone()[0]

        self.reporte_text.insert(tk.END, "REPORTE GENERAL DEL TALLER\n")
        self.reporte_text.insert(tk.END, "=" * 60 + "\n\n")

        self.reporte_text.insert(tk.END, f"Total de vehículos ingresados: {total}\n")
        self.reporte_text.insert(tk.END, f"Vehículos entregados: {entregados}\n")
        self.reporte_text.insert(tk.END, f"Vehículos en proceso: {en_proceso}\n\n")

        self.reporte_text.insert(tk.END, "VEHÍCULOS POR ESTADO:\n")
        self.reporte_text.insert(tk.END, "-" * 60 + "\n")

        estados = ['Ingreso', 'Diagnóstico', 'Hojalatería', 'Pintura', 'Ensamble', 'Listo', 'Entregado']
        for estado in estados:
            self.db.cursor.execute('SELECT COUNT(*) FROM ingresos WHERE estado=?', (estado,))
            count = self.db.cursor.fetchone()[0]


# ======================== VENTANA TÉCNICO (LAMINADOR Y PINTOR) ========================
class TecnicoWindow:
    def __init__(self, root, db, user_id, nombre):
        self.root = root
        self.db = db
        self.user_id = user_id
        self.nombre = nombre

        self.root.title(f"Alan Automotriz - {nombre}")
        self.root.geometry("1000x650")

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        self.tab_servicios = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_servicios, text="Mis Servicios")
        self.crear_tab_servicios()

        self.tab_tareas = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_tareas, text="Tareas del Gerente")
        self.crear_tab_tareas()

        self.tab_reportes = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_reportes, text="Enviar Reporte")
        self.crear_tab_reportes()

    def crear_tab_servicios(self):
        frame = ttk.Frame(self.tab_servicios, padding="20")
        frame.pack(fill='both', expand=True)

        ttk.Label(frame, text="Vehículos Asignados a Mí",
                  font=('Arial', 12, 'bold')).pack(pady=10)

        ttk.Button(frame, text="Actualizar Lista",
                   command=self.cargar_mis_servicios).pack(pady=5)

        columns = ('ID', 'Cliente', 'Vehículo', 'Placa', 'Estado', 'Fecha Ingreso')
        self.tree_servicios = ttk.Treeview(frame, columns=columns, show='headings', height=10)

        for col in columns:
            self.tree_servicios.heading(col, text=col)
            self.tree_servicios.column(col, width=130)

        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=self.tree_servicios.yview)
        self.tree_servicios.configure(yscrollcommand=scrollbar.set)

        self.tree_servicios.pack(side='left', fill='both', expand=True, pady=10)
        scrollbar.pack(side='right', fill='y')

        accion_frame = ttk.LabelFrame(frame, text="Actualizar Estado del Vehículo", padding="10")
        accion_frame.pack(fill='x', pady=10)

        ttk.Label(accion_frame, text="Cambiar estado a:").grid(row=0, column=0, padx=5, pady=5)
        self.estado_combo = ttk.Combobox(accion_frame, values=[
            'Diagnóstico', 'Hojalatería', 'Pintura', 'Ensamble', 'Listo'
        ], width=20)
        self.estado_combo.grid(row=0, column=1, padx=5, pady=5)

        ttk.Button(accion_frame, text="Actualizar Estado",
                   command=self.actualizar_estado).grid(row=0, column=2, padx=5, pady=5)

        self.cargar_mis_servicios()

    def crear_tab_tareas(self):
        frame = ttk.Frame(self.tab_tareas, padding="20")
        frame.pack(fill='both', expand=True)

        ttk.Label(frame, text="Tareas e Instrucciones del Gerente",
                  font=('Arial', 12, 'bold')).pack(pady=10)

        ttk.Button(frame, text="Actualizar Tareas",
                   command=self.cargar_tareas).pack(pady=5)

        self.tareas_text = scrolledtext.ScrolledText(frame, width=80, height=25)
        self.tareas_text.pack(fill='both', expand=True)

        self.cargar_tareas()

    def crear_tab_reportes(self):
        frame = ttk.Frame(self.tab_reportes, padding="20")
        frame.pack(fill='both', expand=True)

        ttk.Label(frame, text="Enviar Reporte al Gerente",
                  font=('Arial', 12, 'bold')).pack(pady=10)

        # Selección de vehículo
        veh_frame = ttk.LabelFrame(frame, text="Seleccionar Vehículo", padding="10")
        veh_frame.pack(fill='x', pady=10)

        columns = ('ID', 'Cliente', 'Vehículo', 'Placa')
        self.tree_rep = ttk.Treeview(veh_frame, columns=columns, show='headings', height=5)

        for col in columns:
            self.tree_rep.heading(col, text=col)
            self.tree_rep.column(col, width=150)

        self.tree_rep.pack(fill='x', pady=5)

        # Área de reporte
        rep_frame = ttk.LabelFrame(frame, text="Escribir Reporte", padding="10")
        rep_frame.pack(fill='both', expand=True, pady=10)

        ttk.Label(rep_frame, text="Describa el problema, avance o cualquier situación:").pack(anchor='w', pady=5)
        self.rep_text = scrolledtext.ScrolledText(rep_frame, width=70, height=10)
        self.rep_text.pack(fill='both', expand=True)

        ttk.Button(rep_frame, text="Enviar Reporte al Gerente",
                   command=self.enviar_reporte).pack(pady=10)

        self.cargar_vehiculos_reporte()

    def cargar_mis_servicios(self):
        for item in self.tree_servicios.get_children():
            self.tree_servicios.delete(item)

        self.db.cursor.execute('''
            SELECT i.id, c.nombre, v.marca || ' ' || v.modelo, v.placa, i.estado, i.fecha_ingreso
            FROM ingresos i
            JOIN clientes c ON i.cliente_id = c.id
            JOIN vehiculos v ON i.vehiculo_id = v.id
            WHERE i.asignado_a = ? AND i.estado != 'Entregado'
            ORDER BY i.fecha_ingreso
        ''', (self.user_id,))

        for row in self.db.cursor.fetchall():
            self.tree_servicios.insert('', 'end', values=row)

    def actualizar_estado(self):
        selected = self.tree_servicios.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un vehículo")
            return

        nuevo_estado = self.estado_combo.get()
        if not nuevo_estado:
            messagebox.showwarning("Advertencia", "Seleccione un estado")
            return

        ingreso_id = self.tree_servicios.item(selected[0])['values'][0]

        self.db.cursor.execute('UPDATE ingresos SET estado=? WHERE id=?', (nuevo_estado, ingreso_id))
        self.db.cursor.execute(
            'INSERT INTO servicios (ingreso_id, tipo_servicio, descripcion, realizado_por) VALUES (?, ?, ?, ?)',
            (ingreso_id, 'Actualización de estado', f'Estado actualizado a: {nuevo_estado}', self.user_id)
        )

        self.db.conn.commit()
        messagebox.showinfo("Éxito", "Estado actualizado correctamente")
        self.cargar_mis_servicios()

    def cargar_tareas(self):
        self.tareas_text.delete(1.0, tk.END)

        self.db.cursor.execute('''
            SELECT m.fecha, v.placa, v.marca || ' ' || v.modelo, c.nombre, m.mensaje, m.leido
            FROM mensajes m
            JOIN ingresos i ON m.ingreso_id = i.id
            JOIN vehiculos v ON i.vehiculo_id = v.id
            JOIN clientes c ON i.cliente_id = c.id
            WHERE m.para_usuario = ? AND m.tipo = 'Tarea del Gerente'
            ORDER BY m.fecha DESC
        ''', (self.user_id,))

        tareas = self.db.cursor.fetchall()

        if not tareas:
            self.tareas_text.insert(tk.END, "No hay tareas asignadas\n")
            return

        nuevas = 0
        for tarea in tareas:
            fecha, placa, vehiculo, cliente, mensaje, leido = tarea

            if not leido:
                nuevas += 1
                estado = "● NUEVA TAREA"
            else:
                estado = "✓ Vista"

            self.tareas_text.insert(tk.END, f"[{fecha}] {estado}\n")
            self.tareas_text.insert(tk.END, f"Cliente: {cliente}\n")
            self.tareas_text.insert(tk.END, f"Vehículo: {vehiculo} - Placa: {placa}\n")
            self.tareas_text.insert(tk.END, f"TAREA/INSTRUCCIONES:\n{mensaje}\n")
            self.tareas_text.insert(tk.END, "=" * 70 + "\n\n")

        if nuevas > 0:
            self.tareas_text.insert(1.0, f"*** TIENES {nuevas} TAREA(S) NUEVA(S) ***\n\n")

            # Marcar como leídas
            self.db.cursor.execute(
                'UPDATE mensajes SET leido=1 WHERE para_usuario=? AND tipo="Tarea del Gerente" AND leido=0',
                (self.user_id,)
            )
            self.db.conn.commit()

    def cargar_vehiculos_reporte(self):
        for item in self.tree_rep.get_children():
            self.tree_rep.delete(item)

        self.db.cursor.execute('''
            SELECT i.id, c.nombre, v.marca || ' ' || v.modelo, v.placa
            FROM ingresos i
            JOIN clientes c ON i.cliente_id = c.id
            JOIN vehiculos v ON i.vehiculo_id = v.id
            WHERE i.asignado_a = ? AND i.estado != 'Entregado'
            ORDER BY i.fecha_ingreso
        ''', (self.user_id,))

        for row in self.db.cursor.fetchall():
            self.tree_rep.insert('', 'end', values=row)

    def enviar_reporte(self):
        selected = self.tree_rep.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un vehículo")
            return

        reporte = self.rep_text.get(1.0, tk.END).strip()
        if not reporte:
            messagebox.showwarning("Advertencia", "Escriba un reporte")
            return

        ingreso_id = self.tree_rep.item(selected[0])['values'][0]

        # Obtener el gerente
        self.db.cursor.execute("SELECT id FROM usuarios WHERE rol='Gerente' LIMIT 1")
        gerente = self.db.cursor.fetchone()

        if not gerente:
            messagebox.showerror("Error", "No se encontró un gerente en el sistema")
            return

        para_usuario = gerente[0]

        self.db.cursor.execute(
            'INSERT INTO mensajes (ingreso_id, de_usuario, para_usuario, mensaje, tipo) VALUES (?, ?, ?, ?, ?)',
            (ingreso_id, self.user_id, para_usuario, reporte, 'Reporte del Técnico')
        )

        self.db.conn.commit()
        messagebox.showinfo("Éxito", "Reporte enviado al gerente")
        self.rep_text.delete(1.0, tk.END)


# ======================== FUNCIÓN PRINCIPAL ========================
def main():
    db = Database()
    root = tk.Tk()
    LoginWindow(root, db)
    root.mainloop()
from datetime import datetime, timedelta


if __name__ == "__main__":
    main()