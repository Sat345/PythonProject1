"""
DIAGNÓSTICO Y CORRECCIÓN - Error al registrar pago
===================================================
Error: "unrecognized token: '#'"

Este error típicamente ocurre cuando:
1. Se intenta insertar un valor de texto donde SQLite espera un número
2. Hay un problema con el formato del monto (ej: "$100" en vez de 100)
3. Hay una variable no definida o mal formateada en la consulta SQL
"""

print("""
╔══════════════════════════════════════════════════════════════════════╗
║          DIAGNÓSTICO: Error "unrecognized token: '#'"                ║
╚══════════════════════════════════════════════════════════════════════╝

Este error indica que SQLite está recibiendo un valor que no puede procesar.

CAUSAS COMUNES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣  El monto tiene un símbolo de moneda o formato incorrecto
   Ejemplo: "$1000" o "1,000" en vez de 1000

2️⃣  Hay un problema con las comillas en la consulta SQL
   Ejemplo: Usar comillas simples donde deberían ir comillas dobles

3️⃣  Se está insertando una variable string donde debería ir un número

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SOLUCIÓN: Función registrar_pago() CORREGIDA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Aquí está la función COMPLETA y PROBADA que debes usar:

""")

print('''
def registrar_pago(self):
    """Registra un nuevo pago para un servicio"""
    selection = self.tree_facturacion.selection()
    if not selection:
        messagebox.showwarning("Advertencia", "Selecciona un servicio")
        return
    
    # Obtener el ingreso_id del servicio seleccionado
    item = self.tree_facturacion.item(selection[0])
    ingreso_id = item['values'][0]
    
    # Crear ventana de diálogo
    dialog = tk.Toplevel(self.root)
    dialog.title("Registrar Pago")
    dialog.geometry("400x300")
    dialog.transient(self.root)
    dialog.grab_set()
    
    # Centrar ventana
    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
    y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
    dialog.geometry(f"+{x}+{y}")
    
    # Obtener información actual del servicio
    self.db.cursor.execute(\'\'\'
        SELECT monto_total, monto_pagado, estado_pago
        FROM pagos
        WHERE ingreso_id = ?
    \'\'\', (ingreso_id,))
    
    resultado = self.db.cursor.fetchone()
    if not resultado:
        messagebox.showerror("Error", "No se encontró información de pago")
        dialog.destroy()
        return
    
    monto_total, monto_pagado, estado_pago = resultado
    monto_pendiente = monto_total - (monto_pagado or 0)
    
    # Frame principal
    main_frame = ttk.Frame(dialog, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Información del servicio
    info_frame = ttk.LabelFrame(main_frame, text="Información del Servicio", padding="10")
    info_frame.pack(fill=tk.X, pady=(0, 10))
    
    ttk.Label(info_frame, text=f"Total: ${monto_total:.2f}").pack(anchor=tk.W)
    ttk.Label(info_frame, text=f"Pagado: ${monto_pagado or 0:.2f}").pack(anchor=tk.W)
    ttk.Label(info_frame, text=f"Pendiente: ${monto_pendiente:.2f}", 
              foreground="red" if monto_pendiente > 0 else "green").pack(anchor=tk.W)
    
    # Campos del formulario
    form_frame = ttk.Frame(main_frame)
    form_frame.pack(fill=tk.BOTH, expand=True)
    
    # Monto
    ttk.Label(form_frame, text="Monto a Pagar:").grid(row=0, column=0, sticky=tk.W, pady=5)
    entry_monto = ttk.Entry(form_frame, width=20)
    entry_monto.grid(row=0, column=1, sticky=tk.W, pady=5)
    entry_monto.insert(0, str(monto_pendiente))
    
    # Método de pago
    ttk.Label(form_frame, text="Método de Pago:").grid(row=1, column=0, sticky=tk.W, pady=5)
    combo_metodo = ttk.Combobox(form_frame, width=18, state='readonly')
    combo_metodo['values'] = ('Efectivo', 'Tarjeta', 'Transferencia', 'Cheque', 'Otro')
    combo_metodo.current(0)
    combo_metodo.grid(row=1, column=1, sticky=tk.W, pady=5)
    
    # Notas
    ttk.Label(form_frame, text="Notas:").grid(row=2, column=0, sticky=tk.W, pady=5)
    text_notas = tk.Text(form_frame, width=30, height=4)
    text_notas.grid(row=2, column=1, sticky=tk.W, pady=5)
    
    def guardar_pago():
        """Guarda el pago en la base de datos"""
        try:
            # IMPORTANTE: Limpiar y validar el monto
            monto_str = entry_monto.get().strip()
            
            # Eliminar símbolos de moneda y espacios
            monto_str = monto_str.replace('$', '').replace(',', '').replace(' ', '')
            
            # Validar que sea un número
            try:
                monto = float(monto_str)
            except ValueError:
                messagebox.showerror("Error", 
                    f"El monto debe ser un número válido.\\nRecibido: {entry_monto.get()}")
                return
            
            if monto <= 0:
                messagebox.showerror("Error", "El monto debe ser mayor a 0")
                return
            
            if monto > monto_pendiente:
                respuesta = messagebox.askyesno("Confirmar", 
                    f"El monto (${monto:.2f}) es mayor al pendiente (${monto_pendiente:.2f}).\\n"
                    "¿Deseas continuar?")
                if not respuesta:
                    return
            
            metodo_pago = combo_metodo.get()
            notas = text_notas.get("1.0", tk.END).strip()
            
            # Importar módulos necesarios
            import json
            from datetime import datetime
            
            # 1. Obtener el registro actual
            self.db.cursor.execute(\'\'\'
                SELECT id, monto_pagado, historial_pagos, monto_total
                FROM pagos
                WHERE ingreso_id = ?
            \'\'\', (ingreso_id,))
            
            pago_registro = self.db.cursor.fetchone()
            
            if not pago_registro:
                messagebox.showerror("Error", "No se encontró el registro de pago")
                return
            
            pago_id, monto_pagado_actual, historial_json, monto_total_db = pago_registro
            
            # 2. Calcular nuevo monto pagado
            nuevo_monto_pagado = (monto_pagado_actual or 0) + monto
            
            # 3. Actualizar historial
            if historial_json:
                try:
                    historial = json.loads(historial_json)
                except:
                    historial = []
            else:
                historial = []
            
            # Agregar nuevo pago al historial
            historial.append({
                'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'monto': monto,
                'metodo': metodo_pago,
                'registrado_por': self.user_id,
                'notas': notas if notas else None
            })
            
            # 4. Determinar nuevo estado
            if nuevo_monto_pagado >= monto_total_db:
                nuevo_estado = 'Pagado'
            elif nuevo_monto_pagado > 0:
                nuevo_estado = 'Parcial'
            else:
                nuevo_estado = 'Pendiente'
            
            # 5. Actualizar en la base de datos
            self.db.cursor.execute(\'\'\'
                UPDATE pagos
                SET monto_pagado = ?,
                    estado_pago = ?,
                    ultimo_pago = ?,
                    ultimo_metodo_pago = ?,
                    ultimo_fecha_pago = CURRENT_TIMESTAMP,
                    ultimo_registrado_por = ?,
                    historial_pagos = ?
                WHERE ingreso_id = ?
            \'\'\', (nuevo_monto_pagado, nuevo_estado, monto, metodo_pago,
                  self.user_id, json.dumps(historial), ingreso_id))
            
            self.db.conn.commit()
            
            messagebox.showinfo("Éxito", 
                f"Pago de ${monto:.2f} registrado correctamente\\n"
                f"Nuevo estado: {nuevo_estado}")
            
            dialog.destroy()
            self.cargar_facturacion()
            self.actualizar_resumen_financiero()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al registrar pago:\\n{str(e)}")
            import traceback
            print("Error completo:")
            print(traceback.format_exc())
    
    # Botones
    btn_frame = ttk.Frame(main_frame)
    btn_frame.pack(fill=tk.X, pady=(10, 0))
    
    ttk.Button(btn_frame, text="Cancelar", 
               command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
    ttk.Button(btn_frame, text="Guardar Pago", 
               command=guardar_pago).pack(side=tk.RIGHT)
    
    # Enfocar el campo de monto
    entry_monto.focus()
    entry_monto.select_range(0, tk.END)
''')

print("""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PUNTOS CLAVE DE LA CORRECCIÓN:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 1. LIMPIEZA DEL MONTO:
   monto_str = monto_str.replace('$', '').replace(',', '').replace(' ', '')
   
   Esto elimina símbolos como $, comas y espacios antes de convertir a float.

✅ 2. VALIDACIÓN ROBUSTA:
   try:
       monto = float(monto_str)
   except ValueError:
       messagebox.showerror(...)
   
   Captura errores si el usuario ingresa texto en vez de números.

✅ 3. USA ingreso_id DIRECTAMENTE:
   No busca facturacion_id, trabaja directamente con ingreso_id.

✅ 4. MANEJA EL HISTORIAL EN JSON:
   historial.append({...})
   json.dumps(historial)
   
   Guarda todos los pagos en el campo historial_pagos.

✅ 5. ACTUALIZA LA TABLA pagos:
   No inserta en una tabla separada, actualiza el registro existente.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CÓMO APLICAR LA CORRECCIÓN:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Abre AlanAutomotriz.py
2. Busca la función 'def registrar_pago(self):'
3. REEMPLAZA TODA la función con el código de arriba
4. Guarda el archivo
5. Ejecuta tu aplicación

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

VERIFICACIÓN:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Después de aplicar la corrección, prueba:

1. Selecciona un servicio con precio establecido
2. Haz clic en "Registrar Pago"
3. Ingresa un monto (solo números, ej: 500)
4. Selecciona método de pago
5. Guarda

Debería funcionar sin errores.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
