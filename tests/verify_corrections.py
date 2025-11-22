"""
Script de verificación para validar funcionalidades clave del sistema:
1. Cálculo de KPIs (OTIF, Fill Rate, Backlog Rate)
2. Detalle de items en pedidos
3. Referencias correctas en Kardex
4. Coherencia de datos
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main

print("=" * 80)
print("VERIFICACIÓN DE FUNCIONALIDADES DEL SISTEMA")
print("=" * 80)

# Ejecutar simulación
print("\n1. Ejecutando simulación de 5 días...")
resultados = main.run_simulation(n_dias=5, capacidad_picking=1500, escenario="normal")
print("✓ Simulación completada")

# Verificar cálculo de KPIs
print("\n" + "-" * 80)
print("2. Verificando cálculo de KPIs diarios...")
print("-" * 80)
for dia_data in resultados['resultados_diarios'][:5]:
    dia = dia_data['dia']
    kpis = dia_data['kpis']
    print(f"\nDía {dia}:")
    print(f"  OTIF: {kpis['otif']:.1f}%")
    print(f"  Fill Rate: {kpis['fill_rate']:.1f}%")
    print(f"  Backlog Rate: {kpis['backlog_rate']:.1f}%")
    print(f"  Total Pedidos: {kpis['total_pedidos']}")

# Verificar KPIs globales
print("\n" + "-" * 80)
print("3. Verificando KPIs globales...")
print("-" * 80)
metricas = resultados['metricas_globales']
print(f"OTIF Global: {metricas.get('otif_global', 0):.1f}%")
print(f"Fill Rate Global: {metricas.get('fill_rate_global', 0):.1f}%")
print(f"Total Pedidos: {metricas.get('total_pedidos', 0)}")
print(f"Valor Inventario Final: S/ {metricas.get('valor_total_inventario', 0):,.2f}")

# Verificar estructura de pedidos
print("\n" + "-" * 80)
print("4. Verificando estructura de pedidos...")
print("-" * 80)
df_pedidos = resultados['df_pedidos']
print(f"Total registros de pedidos: {len(df_pedidos)}")
print(f"Columnas disponibles: {', '.join(df_pedidos.columns)}")

if 'Cant_Solicitada' in df_pedidos.columns and 'Cant_Entregada' in df_pedidos.columns:
    print("✓ Columnas de cantidad presentes")
    total_sol = df_pedidos['Cant_Solicitada'].sum()
    total_ent = df_pedidos['Cant_Entregada'].sum()
    print(f"  Total Solicitado: {total_sol:,.0f}")
    print(f"  Total Entregado: {total_ent:,.0f}")
else:
    print("✗ Columnas de cantidad faltantes")

# Verificar Kardex
print("\n" + "-" * 80)
print("5. Verificando Kardex...")
print("-" * 80)
df_kardex = resultados['df_kardex']
print(f"Total movimientos en Kardex: {len(df_kardex)}")

if 'Tipo_Movimiento' in df_kardex.columns:
    tipos = df_kardex['Tipo_Movimiento'].value_counts()
    print("\nMovimientos por tipo:")
    for tipo, count in tipos.items():
        print(f"  {tipo}: {count}")
else:
    print("✗ Columna 'Tipo_Movimiento' faltante")

# Verificar referencias en Kardex
if 'ID_Referencia' in df_kardex.columns and 'Tipo_Referencia' in df_kardex.columns:
    print("\n✓ Referencias en Kardex presentes")
    
    # Ejemplos de ventas
    ventas = df_kardex[df_kardex['Tipo_Movimiento'] == 'VENTA_DESPACHO'].head(3)
    if not ventas.empty:
        print("\nEjemplos de movimientos de venta:")
        for idx, row in ventas.iterrows():
            print(f"  Día {row['Fecha']}, {row['Producto']}, "
                  f"Cantidad: {row['Cantidad']}, Pedido: {row['ID_Referencia']}")
    
    # Ejemplos de compras
    compras = df_kardex[df_kardex['Tipo_Movimiento'] == 'COMPRA_RECEPCION'].head(3)
    if not compras.empty:
        print("\nEjemplos de movimientos de compra:")
        for idx, row in compras.iterrows():
            print(f"  Día {row['Fecha']}, {row['Producto']}, "
                  f"Cantidad: {row['Cantidad']}, Compra: {row['ID_Referencia']}")
else:
    print("✗ Referencias en Kardex faltantes")

# Resumen de validación
print("\n" + "=" * 80)
validaciones_exitosas = 0
total_validaciones = 5

if metricas.get('otif_global', 0) >= 0 and metricas.get('otif_global', 0) <= 100:
    validaciones_exitosas += 1
if metricas.get('fill_rate_global', 0) >= 0 and metricas.get('fill_rate_global', 0) <= 100:
    validaciones_exitosas += 1
if 'Cant_Solicitada' in df_pedidos.columns:
    validaciones_exitosas += 1
if 'Tipo_Movimiento' in df_kardex.columns:
    validaciones_exitosas += 1
if 'ID_Referencia' in df_kardex.columns:
    validaciones_exitosas += 1

print(f"✅ VERIFICACIÓN COMPLETADA: {validaciones_exitosas}/{total_validaciones} validaciones exitosas")
print("=" * 80)
