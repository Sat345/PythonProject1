"""
SCRIPT DE DIAGNÓSTICO RÁPIDO
=============================
Ejecuta este script primero para ver qué estructura tiene tu base de datos actual
"""

import sqlite3

print("="*70)
print("DIAGNÓSTICO DE BASE DE DATOS - ALAN AUTOMOTRIZ")
print("="*70)

try:
    conn = sqlite3.connect('alan_automotriz.db')
    cursor = conn.cursor()
    
    # Verificar tabla pagos
    print("\n1️⃣  VERIFICANDO TABLA 'pagos':")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pagos';")
    if cursor.fetchone():
        print("   ✅ La tabla 'pagos' existe")
        
        cursor.execute("PRAGMA table_info(pagos);")
        columnas = cursor.fetchall()
        print("\n   📊 Columnas actuales:")
        for col in columnas:
            print(f"      - {col[1]:30} ({col[2]})")
        
        # Verificar columnas críticas
        nombres_columnas = [col[1] for col in columnas]
        columnas_necesarias = ['monto_total', 'monto_pagado', 'estado_pago', 'historial_pagos']
        
        print("\n   🔍 Verificación de columnas necesarias:")
        for col_necesaria in columnas_necesarias:
            if col_necesaria in nombres_columnas:
                print(f"      ✅ {col_necesaria}")
            else:
                print(f"      ❌ {col_necesaria} - FALTA")
    else:
        print("   ❌ La tabla 'pagos' NO existe")
    
    # Verificar tabla facturacion
    print("\n2️⃣  VERIFICANDO TABLA 'facturacion':")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='facturacion';")
    if cursor.fetchone():
        print("   ⚠️  La tabla 'facturacion' TODAVÍA existe (debería eliminarse)")
        
        cursor.execute("PRAGMA table_info(facturacion);")
        columnas = cursor.fetchall()
        print("\n   📊 Columnas:")
        for col in columnas:
            print(f"      - {col[1]:30} ({col[2]})")
    else:
        print("   ✅ La tabla 'facturacion' no existe (correcto)")
    
    # Contar registros
    print("\n3️⃣  CONTANDO REGISTROS:")
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pagos';")
    if cursor.fetchone():
        cursor.execute("SELECT COUNT(*) FROM pagos;")
        count = cursor.fetchone()[0]
        print(f"   📦 Registros en 'pagos': {count}")
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='facturacion';")
    if cursor.fetchone():
        cursor.execute("SELECT COUNT(*) FROM facturacion;")
        count = cursor.fetchone()[0]
        print(f"   📦 Registros en 'facturacion': {count}")
    
    conn.close()
    
    print("\n" + "="*70)
    print("RECOMENDACIÓN:")
    print("="*70)
    
    # Dar recomendación
    cursor = sqlite3.connect('alan_automotriz.db').cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pagos';")
    tiene_pagos = cursor.fetchone() is not None
    
    if tiene_pagos:
        cursor.execute("PRAGMA table_info(pagos);")
        columnas = [col[1] for col in cursor.fetchall()]
        
        if 'monto_total' not in columnas:
            print("\n❌ PROBLEMA: Tu tabla 'pagos' no tiene las columnas correctas")
            print("\n📋 SOLUCIÓN:")
            print("   1. Ejecuta el script: python migrar_base_datos.py")
            print("   2. Esto agregará las columnas faltantes automáticamente")
            print("   3. Se creará un backup antes de modificar")
        else:
            print("\n✅ Tu base de datos parece estar correcta")
    else:
        print("\n❌ PROBLEMA: No existe la tabla 'pagos'")
        print("\n📋 SOLUCIÓN:")
        print("   1. Ejecuta el script: python migrar_base_datos.py")
        print("   2. Esto creará la estructura correcta")
    
except FileNotFoundError:
    print("\n❌ ERROR: No se encontró el archivo 'alan_automotriz.db'")
    print("   Asegúrate de ejecutar este script en el mismo directorio")
    print("   donde está tu base de datos.")
except Exception as e:
    print(f"\n❌ ERROR: {e}")

print("\n" + "="*70)
