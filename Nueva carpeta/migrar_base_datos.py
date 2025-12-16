"""
SCRIPT DE MIGRACIÓN DE BASE DE DATOS
=====================================
Este script actualiza la estructura de tu base de datos para usar
la tabla unificada 'pagos' en lugar de 'facturacion' + 'pagos' separadas.

IMPORTANTE: 
- Este script hace una copia de seguridad antes de modificar
- Migra todos los datos existentes
"""

import sqlite3
import shutil
from datetime import datetime

def crear_backup():
    """Crea una copia de seguridad de la base de datos"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f'alan_automotriz_backup_{timestamp}.db'
    
    try:
        shutil.copy2('alan_automotriz.db', backup_name)
        print(f"✅ Backup creado: {backup_name}")
        return True
    except Exception as e:
        print(f"❌ Error al crear backup: {e}")
        return False

def verificar_estructura_actual(cursor):
    """Verifica qué tablas y columnas existen actualmente"""
    print("\n" + "="*60)
    print("VERIFICANDO ESTRUCTURA ACTUAL")
    print("="*60)
    
    # Verificar tablas existentes
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('pagos', 'facturacion');")
    tablas = cursor.fetchall()
    
    tiene_pagos = False
    tiene_facturacion = False
    
    for tabla in tablas:
        if tabla[0] == 'pagos':
            tiene_pagos = True
            print("\n📊 Tabla 'pagos' encontrada")
            cursor.execute("PRAGMA table_info(pagos);")
            columnas = cursor.fetchall()
            print("Columnas actuales:")
            for col in columnas:
                print(f"  - {col[1]} ({col[2]})")
        
        if tabla[0] == 'facturacion':
            tiene_facturacion = True
            print("\n📊 Tabla 'facturacion' encontrada")
            cursor.execute("PRAGMA table_info(facturacion);")
            columnas = cursor.fetchall()
            print("Columnas actuales:")
            for col in columnas:
                print(f"  - {col[1]} ({col[2]})")
    
    return tiene_pagos, tiene_facturacion

def migrar_base_datos():
    """Realiza la migración de la base de datos"""
    
    print("="*60)
    print("INICIANDO MIGRACIÓN DE BASE DE DATOS")
    print("="*60)
    
    # Crear backup
    if not crear_backup():
        print("\n❌ No se pudo crear el backup. Abortando migración.")
        return False
    
    # Conectar a la base de datos
    conn = sqlite3.connect('alan_automotriz.db')
    cursor = conn.cursor()
    
    # Verificar estructura actual
    tiene_pagos, tiene_facturacion = verificar_estructura_actual(cursor)
    
    print("\n" + "="*60)
    print("ESTRATEGIA DE MIGRACIÓN")
    print("="*60)
    
    if tiene_facturacion and tiene_pagos:
        print("\n⚠️  SITUACIÓN: Tienes AMBAS tablas (facturacion y pagos)")
        print("Se procederá a:")
        print("  1. Renombrar tabla 'pagos' antigua a 'pagos_old'")
        print("  2. Crear nueva tabla 'pagos' unificada")
        print("  3. Migrar datos de 'facturacion' y 'pagos_old'")
        print("  4. Eliminar tablas antiguas")
        
        respuesta = input("\n¿Continuar? (s/n): ")
        if respuesta.lower() != 's':
            print("Migración cancelada.")
            conn.close()
            return False
        
        # Renombrar tabla pagos antigua
        cursor.execute("ALTER TABLE pagos RENAME TO pagos_old;")
        
        # Crear nueva tabla pagos unificada
        cursor.execute('''
            CREATE TABLE pagos (
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
        
        # Migrar datos de facturacion
        print("\n📦 Migrando datos de 'facturacion'...")
        cursor.execute('''
            INSERT INTO pagos (ingreso_id, monto_total, monto_pagado, estado_pago, fecha_creacion)
            SELECT ingreso_id, monto_total, monto_pagado, estado_pago, fecha_creacion
            FROM facturacion
        ''')
        
        # Migrar historial de pagos antiguos
        print("📦 Consolidando historial de pagos...")
        cursor.execute('''
            SELECT p.facturacion_id, p.monto, p.metodo_pago, p.fecha_pago, p.registrado_por, p.notas
            FROM pagos_old p
        ''')
        
        import json
        pagos_antiguos = cursor.fetchall()
        
        # Agrupar pagos por facturacion_id
        historial_por_factura = {}
        for pago in pagos_antiguos:
            factura_id, monto, metodo, fecha, usuario, notas = pago
            if factura_id not in historial_por_factura:
                historial_por_factura[factura_id] = []
            
            historial_por_factura[factura_id].append({
                'fecha': fecha,
                'monto': monto,
                'metodo': metodo,
                'registrado_por': usuario,
                'notas': notas
            })
        
        # Actualizar la nueva tabla pagos con el historial
        for factura_id, historial in historial_por_factura.items():
            # Obtener el ingreso_id correspondiente
            cursor.execute('SELECT ingreso_id FROM facturacion WHERE id = ?', (factura_id,))
            result = cursor.fetchone()
            if result:
                ingreso_id = result[0]
                historial_json = json.dumps(historial)
                
                # Actualizar con el último pago
                if historial:
                    ultimo = historial[-1]  # El más reciente
                    cursor.execute('''
                        UPDATE pagos 
                        SET historial_pagos = ?,
                            ultimo_pago = ?,
                            ultimo_metodo_pago = ?,
                            ultimo_fecha_pago = ?,
                            ultimo_registrado_por = ?
                        WHERE ingreso_id = ?
                    ''', (historial_json, ultimo['monto'], ultimo['metodo'], 
                          ultimo['fecha'], ultimo['registrado_por'], ingreso_id))
        
        # Eliminar tablas antiguas
        print("🗑️  Eliminando tablas antiguas...")
        cursor.execute("DROP TABLE IF EXISTS facturacion;")
        cursor.execute("DROP TABLE IF EXISTS pagos_old;")
        
    elif tiene_pagos and not tiene_facturacion:
        print("\n⚠️  SITUACIÓN: Solo tienes tabla 'pagos'")
        print("Se verificarán las columnas...")
        
        cursor.execute("PRAGMA table_info(pagos);")
        columnas = [col[1] for col in cursor.fetchall()]
        
        columnas_necesarias = ['monto_total', 'monto_pagado', 'estado_pago', 'historial_pagos']
        faltan = [col for col in columnas_necesarias if col not in columnas]
        
        if faltan:
            print(f"\n❌ Faltan columnas: {', '.join(faltan)}")
            print("Se agregará las columnas faltantes...")
            
            for columna in faltan:
                if columna == 'monto_total':
                    cursor.execute("ALTER TABLE pagos ADD COLUMN monto_total REAL DEFAULT 0;")
                elif columna == 'monto_pagado':
                    cursor.execute("ALTER TABLE pagos ADD COLUMN monto_pagado REAL DEFAULT 0;")
                elif columna == 'estado_pago':
                    cursor.execute("ALTER TABLE pagos ADD COLUMN estado_pago TEXT DEFAULT 'Pendiente';")
                elif columna == 'historial_pagos':
                    cursor.execute("ALTER TABLE pagos ADD COLUMN historial_pagos TEXT;")
            
            print("✅ Columnas agregadas correctamente")
        else:
            print("✅ La tabla 'pagos' ya tiene todas las columnas necesarias")
    
    elif tiene_facturacion and not tiene_pagos:
        print("\n⚠️  SITUACIÓN: Solo tienes tabla 'facturacion'")
        print("Se renombrará 'facturacion' a 'pagos' y se agregarán columnas...")
        
        # Renombrar facturacion a pagos
        cursor.execute("ALTER TABLE facturacion RENAME TO pagos;")
        
        # Agregar columnas faltantes
        cursor.execute("ALTER TABLE pagos ADD COLUMN ultimo_pago REAL DEFAULT 0;")
        cursor.execute("ALTER TABLE pagos ADD COLUMN ultimo_metodo_pago TEXT;")
        cursor.execute("ALTER TABLE pagos ADD COLUMN ultimo_fecha_pago TIMESTAMP;")
        cursor.execute("ALTER TABLE pagos ADD COLUMN ultimo_registrado_por INTEGER;")
        cursor.execute("ALTER TABLE pagos ADD COLUMN historial_pagos TEXT;")
        cursor.execute("ALTER TABLE pagos ADD COLUMN notas TEXT;")
        
        print("✅ Tabla renombrada y columnas agregadas")
    
    else:
        print("\n✅ No hay tablas de facturación/pagos. Se creará la estructura correcta.")
        
        cursor.execute('''
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
    
    # Confirmar cambios
    conn.commit()
    
    print("\n" + "="*60)
    print("VERIFICANDO RESULTADO")
    print("="*60)
    
    cursor.execute("PRAGMA table_info(pagos);")
    columnas = cursor.fetchall()
    print("\n✅ Estructura final de la tabla 'pagos':")
    for col in columnas:
        print(f"  - {col[1]:30} {col[2]:15}")
    
    conn.close()
    
    print("\n" + "="*60)
    print("✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
    print("="*60)
    print("\nAhora puedes ejecutar tu aplicación normalmente.")
    
    return True

if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════╗
║        SCRIPT DE MIGRACIÓN - ALAN AUTOMOTRIZ               ║
║                                                             ║
║  Este script actualizará la estructura de tu base de       ║
║  datos para usar la nueva tabla 'pagos' unificada.         ║
║                                                             ║
║  ⚠️  IMPORTANTE:                                            ║
║  - Se creará un backup automático                          ║
║  - Todos tus datos se preservarán                          ║
║  - El proceso es reversible con el backup                  ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    respuesta = input("¿Deseas continuar con la migración? (s/n): ")
    
    if respuesta.lower() == 's':
        if migrar_base_datos():
            print("\n✅ Todo listo! Puedes cerrar esta ventana y ejecutar tu aplicación.")
        else:
            print("\n❌ La migración no se completó. Verifica los errores anteriores.")
    else:
        print("\nMigración cancelada por el usuario.")
