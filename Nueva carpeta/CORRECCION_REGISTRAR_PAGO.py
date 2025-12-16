"""
CORRECCIÓN EXACTA PARA registrar_pago()
========================================

PROBLEMA IDENTIFICADO:
La línea 2466 de tu código tiene un error:
    ingreso_id = item['values'][0]

Esto está obteniendo el pago_id (o 'N/A'), no el ingreso_id.
El ingreso_id está en la posición [1].

SOLUCIÓN:
"""

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


"""
RESUMEN DE LA CORRECCIÓN:
=========================

ANTES (línea 2466 - INCORRECTO):
    ingreso_id = item['values'][0]  # ❌ Esto obtiene el pago_id

DESPUÉS (CORRECTO):
    ingreso_id = values[1]  # ✅ Esto obtiene el ingreso_id

EXPLICACIÓN:
Los valores en self.tree_facturacion son:
    [0] = pago_id (o 'N/A')
    [1] = ingreso_id ← ESTE ES EL QUE NECESITAMOS
    [2] = cliente
    [3] = vehiculo
    [4] = placa
    [5] = total
    [6] = pagado
    [7] = pendiente
    [8] = estado

Por eso el error decía "no such column named facturacion_id" - 
porque estaba usando el pago_id donde debía usar el ingreso_id.
"""
