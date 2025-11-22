import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main
import pandas as pd

print("=" * 80)
print("TEST: VERIFICAR ESTADO DE STOCK COMPROMETIDO")
print("=" * 80)

# Run simulation
print("\nEjecutando simulación de 15 días...")
res = main.run_simulation(15, 1500, "normal")

# Check last day inventory status
df_estado = res['resultados_diarios'][-1]['estado_inventario']
print("\n" + "-" * 80)
print("Estado de Inventario al Día 15 (Primeros 5 productos):")
print("-" * 80)
print(df_estado[['Stock_Fisico', 'Stock_Comprometido', 'Stock_Disponible']].head())

# Check if any Committed Stock > 0
comprometido_total = df_estado['Stock_Comprometido'].sum()
stock_fisico_total = df_estado['Stock_Fisico'].sum()
stock_disponible_total = df_estado['Stock_Disponible'].sum()

print("\n" + "-" * 80)
print("RESUMEN DE STOCK AL FINAL DE LA SIMULACIÓN")
print("-" * 80)
print(f"Stock Físico Total: {stock_fisico_total:.0f}")
print(f"Stock Comprometido Total: {comprometido_total:.0f}")
print(f"Stock Disponible Total: {stock_disponible_total:.0f}")

# Validaciones
print("\n" + "-" * 80)
print("VALIDACIONES")
print("-" * 80)

if comprometido_total >= 0:
    print("✓ PASS: Stock comprometido no es negativo")
else:
    print("✗ FAIL: Stock comprometido es negativo")

if stock_fisico_total >= 0:
    print("✓ PASS: Stock físico no es negativo")
else:
    print("✗ FAIL: Stock físico es negativo")

# Verificar coherencia: Stock_Disponible = Stock_Fisico - Stock_Comprometido
esperado_disponible = stock_fisico_total - comprometido_total
if abs(stock_disponible_total - esperado_disponible) < 0.01:
    print("✓ PASS: Coherencia entre stock físico, comprometido y disponible")
else:
    print(f"✗ FAIL: Incoherencia detectada. Esperado disponible: {esperado_disponible}, Real: {stock_disponible_total}")

print("\n" + "=" * 80)
print("✅ VERIFICACIÓN COMPLETADA")
print("=" * 80)
