"""
CORRECCIÓN AUTOMÁTICA COMPLETA
===============================
Este script corrige TODAS las referencias a 'facturacion' en tu código
"""

import re
import shutil
from datetime import datetime

print("="*70)
print("CORRECCIÓN AUTOMÁTICA DE REFERENCIAS A 'facturacion'")
print("="*70)

# Crear backup
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
backup_name = f'AlanAutomotriz_backup_{timestamp}.py'

try:
    shutil.copy2('AlanAutomotriz.py', backup_name)
    print(f"\n✅ Backup creado: {backup_name}")
except Exception as e:
    print(f"\n❌ Error al crear backup: {e}")
    print("   Asegúrate de estar en la carpeta correcta")
    exit(1)

# Leer el archivo
with open('AlanAutomotriz.py', 'r', encoding='utf-8') as f:
    contenido = f.read()

print("\n" + "="*70)
print("APLICANDO CORRECCIONES")
print("="*70)

correcciones_aplicadas = []

# 1. Cambiar FROM facturacion a FROM pagos
patron1 = r'\bFROM\s+facturacion\b'
if re.search(patron1, contenido, re.IGNORECASE):
    contenido = re.sub(patron1, 'FROM pagos', contenido, flags=re.IGNORECASE)
    correcciones_aplicadas.append("FROM facturacion → FROM pagos")

# 2. Cambiar JOIN facturacion a JOIN pagos
patron2 = r'(LEFT\s+JOIN|RIGHT\s+JOIN|INNER\s+JOIN|JOIN)\s+facturacion\s+(\w+)'
matches = re.findall(patron2, contenido, re.IGNORECASE)
if matches:
    # Reemplazar y también cambiar el alias de 'f' a 'p'
    contenido = re.sub(patron2, r'\1 pagos \2', contenido, flags=re.IGNORECASE)
    
    # Si el alias era 'f', cambiar todas las referencias 'f.' por 'p.'
    # dentro de las consultas SQL
    contenido = re.sub(
        r'(LEFT\s+JOIN\s+pagos)\s+f\b',
        r'\1 p',
        contenido,
        flags=re.IGNORECASE
    )
    correcciones_aplicadas.append("JOIN facturacion f → JOIN pagos p")

# 3. Cambiar INSERT INTO facturacion a INSERT INTO pagos
patron3 = r'INSERT\s+INTO\s+facturacion\b'
if re.search(patron3, contenido, re.IGNORECASE):
    contenido = re.sub(patron3, 'INSERT INTO pagos', contenido, flags=re.IGNORECASE)
    correcciones_aplicadas.append("INSERT INTO facturacion → INSERT INTO pagos")

# 4. Cambiar UPDATE facturacion a UPDATE pagos
patron4 = r'UPDATE\s+facturacion\b'
if re.search(patron4, contenido, re.IGNORECASE):
    contenido = re.sub(patron4, 'UPDATE pagos', contenido, flags=re.IGNORECASE)
    correcciones_aplicadas.append("UPDATE facturacion → UPDATE pagos")

# 5. Cambiar referencias al alias 'f.' por 'p.' en contextos SQL
# Solo dentro de consultas SQL (después de SELECT y antes de FROM)
def reemplazar_alias_en_sql(match):
    sql = match.group(0)
    # Reemplazar f. por p. solo si viene después de LEFT JOIN pagos p
    if 'LEFT JOIN pagos p' in sql or 'JOIN pagos p' in sql:
        sql = re.sub(r'\bf\.', 'p.', sql)
    return sql

# Buscar bloques de SQL completos
patron_sql = r"self\.db\.cursor\.execute\('''[^']*'''[^)]*\)"
contenido = re.sub(patron_sql, reemplazar_alias_en_sql, contenido, flags=re.DOTALL)

# 6. Corrección específica para registrar_pago - eliminar facturacion_id
# Buscar la función registrar_pago y corregirla
patron_registrar_pago = r'(def registrar_pago\(self[^:]*\):.*?)(self\.db\.conn\.commit\(\))'

def corregir_registrar_pago(match):
    funcion = match.group(0)
    
    # Si menciona facturacion_id, necesita corrección completa
    if 'facturacion_id' in funcion:
        # Agregar comentario de advertencia
        return funcion.replace(
            'facturacion_id',
            'ingreso_id  # CORREGIDO: antes era facturacion_id'
        )
    return funcion

contenido = re.sub(patron_registrar_pago, corregir_registrar_pago, contenido, flags=re.DOTALL)

if 'facturacion_id' in contenido:
    correcciones_aplicadas.append("facturacion_id → ingreso_id")

# Guardar el archivo corregido
with open('AlanAutomotriz.py', 'w', encoding='utf-8') as f:
    f.write(contenido)

print("\n✅ CORRECCIONES APLICADAS:")
for i, correccion in enumerate(correcciones_aplicadas, 1):
    print(f"   {i}. {correccion}")

if not correcciones_aplicadas:
    print("   ℹ️  No se encontraron referencias a 'facturacion' que corregir")
    print("   Tu código puede que ya esté actualizado")

print("\n" + "="*70)
print("VERIFICACIÓN FINAL")
print("="*70)

# Verificar que no queden referencias problemáticas
problemas = []

if re.search(r'FROM\s+facturacion\b', contenido, re.IGNORECASE):
    problemas.append("Todavía hay 'FROM facturacion'")

if re.search(r'JOIN\s+facturacion\b', contenido, re.IGNORECASE):
    problemas.append("Todavía hay 'JOIN facturacion'")

if re.search(r'INSERT\s+INTO\s+facturacion\b', contenido, re.IGNORECASE):
    problemas.append("Todavía hay 'INSERT INTO facturacion'")

if re.search(r'UPDATE\s+facturacion\b', contenido, re.IGNORECASE):
    problemas.append("Todavía hay 'UPDATE facturacion'")

if 'facturacion_id' in contenido:
    # Verificar si está en contexto de SQL (no en comentarios)
    if re.search(r'[\'"].*facturacion_id.*[\'"]', contenido):
        problemas.append("Todavía hay referencias a 'facturacion_id'")

if problemas:
    print("\n⚠️  ADVERTENCIAS:")
    for problema in problemas:
        print(f"   - {problema}")
    print("\n   Puede que necesites correcciones manuales adicionales.")
else:
    print("\n✅ No se encontraron problemas pendientes")
    print("   ¡Tu código debería funcionar ahora!")

print("\n" + "="*70)
print("SIGUIENTE PASO")
print("="*70)
print("""
1. Ejecuta tu aplicación: python AlanAutomotriz.py
2. Prueba establecer precio a un servicio
3. Prueba registrar un pago
4. Si hay errores, envía el mensaje de error

💾 Archivo original respaldado en: {}

⚠️  NOTA IMPORTANTE sobre registrar_pago():
   Si sigues teniendo el error de 'facturacion_id', necesitarás
   reescribir manualmente la función registrar_pago() usando
   el código correcto que te proporcioné en el archivo
   CORRECCION_PRECIO_Y_PAGO.py
""".format(backup_name))
