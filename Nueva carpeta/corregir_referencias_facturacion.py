"""
SCRIPT PARA CORREGIR REFERENCIAS A 'facturacion'
=================================================
Este script busca y corrige automáticamente todas las consultas SQL
que todavía usan la tabla 'facturacion' en lugar de 'pagos'
"""

import re
import shutil
from datetime import datetime

# Crear backup del archivo Python
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
backup_name = f'AlanAutomotriz_backup_{timestamp}.py'

try:
    shutil.copy2('AlanAutomotriz.py', backup_name)
    print(f"✅ Backup creado: {backup_name}")
except Exception as e:
    print(f"❌ Error al crear backup: {e}")
    exit(1)

# Leer el archivo
with open('AlanAutomotriz.py', 'r', encoding='utf-8') as f:
    contenido = f.read()

print("\n" + "="*70)
print("BUSCANDO REFERENCIAS A 'facturacion' EN CONSULTAS SQL")
print("="*70)

# Buscar todas las ocurrencias de 'facturacion' en consultas SQL
# Patrón para encontrar consultas SQL que usen la tabla facturacion
patron_from = r'FROM\s+facturacion'
patron_join = r'(LEFT\s+JOIN|RIGHT\s+JOIN|INNER\s+JOIN|JOIN)\s+facturacion'

ocurrencias_from = list(re.finditer(patron_from, contenido, re.IGNORECASE))
ocurrencias_join = list(re.finditer(patron_join, contenido, re.IGNORECASE))

total_ocurrencias = len(ocurrencias_from) + len(ocurrencias_join)

print(f"\n🔍 Encontradas {total_ocurrencias} referencias a la tabla 'facturacion':")
print(f"   - {len(ocurrencias_from)} en cláusulas FROM")
print(f"   - {len(ocurrencias_join)} en cláusulas JOIN")

if total_ocurrencias == 0:
    print("\n✅ No se encontraron referencias a 'facturacion' en consultas SQL")
    print("   Tu código ya está actualizado correctamente.")
    exit(0)

# Mostrar las líneas donde aparecen
print("\n📍 Ubicaciones encontradas:")
lineas = contenido.split('\n')
for match in ocurrencias_from + ocurrencias_join:
    # Encontrar el número de línea
    pos = match.start()
    num_linea = contenido[:pos].count('\n') + 1
    
    # Mostrar contexto
    if 0 <= num_linea - 1 < len(lineas):
        print(f"\n   Línea {num_linea}: {lineas[num_linea-1].strip()}")

# Preguntar si desea continuar
print("\n" + "="*70)
respuesta = input("¿Deseas reemplazar 'facturacion' por 'pagos' automáticamente? (s/n): ")

if respuesta.lower() != 's':
    print("\nOperación cancelada.")
    exit(0)

# Realizar los reemplazos
contenido_corregido = contenido

# Reemplazar en cláusulas FROM
contenido_corregido = re.sub(
    r'FROM\s+facturacion\b',
    'FROM pagos',
    contenido_corregido,
    flags=re.IGNORECASE
)

# Reemplazar en cláusulas JOIN
contenido_corregido = re.sub(
    r'(LEFT\s+JOIN|RIGHT\s+JOIN|INNER\s+JOIN|JOIN)\s+facturacion\b',
    r'\1 pagos',
    contenido_corregido,
    flags=re.IGNORECASE
)

# Guardar el archivo corregido
with open('AlanAutomotriz.py', 'w', encoding='utf-8') as f:
    f.write(contenido_corregido)

print("\n" + "="*70)
print("✅ CORRECCIONES APLICADAS")
print("="*70)
print(f"\n📝 Se reemplazaron {total_ocurrencias} ocurrencias")
print(f"💾 Archivo original respaldado en: {backup_name}")
print("\n✅ Ahora puedes ejecutar tu aplicación")

print("\n" + "="*70)
print("VERIFICACIÓN FINAL")
print("="*70)

# Verificar que no queden referencias
patron_verificacion = r'\bfacturacion\b'
ocurrencias_restantes = list(re.finditer(patron_verificacion, contenido_corregido, re.IGNORECASE))

# Filtrar solo las que están en consultas SQL (ignorar comentarios y strings de UI)
ocurrencias_en_sql = []
for match in ocurrencias_restantes:
    pos = match.start()
    # Buscar hacia atrás para ver si está en una consulta SQL
    contexto_previo = contenido_corregido[max(0, pos-200):pos]
    if 'SELECT' in contexto_previo or 'FROM' in contexto_previo or 'JOIN' in contexto_previo:
        ocurrencias_en_sql.append(match)

if ocurrencias_en_sql:
    print(f"\n⚠️  Todavía hay {len(ocurrencias_en_sql)} posibles referencias a 'facturacion'")
    print("   Puede que estén en comentarios o nombres de variables (esto es normal)")
else:
    print("\n✅ No se encontraron más referencias a 'facturacion' en consultas SQL")
    print("   ¡Todo correcto!")
