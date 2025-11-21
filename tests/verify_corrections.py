"""
Script de verificación para probar las correcciones:
1. OTIF diario calculado correctamente
2. Detalle de productos en pedidos
3. Referencias en kardex
"""
import main

print("=" * 60)
print("VERIFICACIÓN DE CORRECCIONES")
print("=" * 60)

# Ejecutar simulación corta
print("\n1. Ejecutando simulación de 3 días...")
resultados = main.run_simulation(n_dias=3, capacidad_picking=1500, escenario="normal")

print("✓ Simulación completada")

# Verificar OTIF
print("\n2. Verificando cálculo de OTIF...")
for dia_data in resultados['resultados_diarios'][:3]:
    dia = dia_data['dia']
    otif = dia_data['kpis']['otif']
    total_pedidos = dia_data['kpis']['total_pedidos']
    print(f"   Día {dia}: OTIF = {otif}% (Total pedidos: {total_pedidos})")

# Verificar detalle de productos en pedidos
print("\n3. Verificando detalle de productos en pedidos...")
df_pedidos = resultados['df_pedidos']
primer_pedido = df_pedidos.iloc[0]

if 'Items_Detalle' in primer_pedido:
    print(f"✓ Campo 'Items_Detalle' encontrado en pedidos")
    print(f"   Ejemplo - Pedido {primer_pedido['ID_Pedido']}:")
    items = primer_pedido['Items_Detalle']
    if isinstance(items, list):
        for item in items:
            print(f"     - SKU: {item['SKU']}, Solicitado: {item['Cant_Solicitada']}, Entregado: {item['Cant_Entregada']}")
else:
    print("✗ Campo 'Items_Detalle' NO encontrado")

# Verificar referencias en kardex
print("\n4. Verificando referencias en kardex...")
df_kardex = resultados['df_kardex']

if 'ID_Referencia' in df_kardex.columns and 'Tipo_Referencia' in df_kardex.columns:
    print("✓ Columnas 'ID_Referencia' y 'Tipo_Referencia' encontradas")
    
    # Mostrar ejemplos de ventas
    ventas = df_kardex[df_kardex['Tipo_Movimiento'] == 'VENTA_DESPACHO'].head(3)
    if not ventas.empty:
        print("\n   Ejemplos de movimientos de venta:")
        for idx, row in ventas.iterrows():
            print(f"     - Día {row['Fecha']}, Producto: {row['Producto']}, Cant: {row['Cantidad']}, ID_Pedido: {row['ID_Referencia']}")
    
    # Mostrar ejemplos de compras
    compras = df_kardex[df_kardex['Tipo_Movimiento'] == 'COMPRA_RECEPCION'].head(3)
    if not compras.empty:
        print("\n   Ejemplos de movimientos de compra:")
        for idx, row in compras.iterrows():
            print(f"     - Día {row['Fecha']}, Producto: {row['Producto']}, Cant: {row['Cantidad']}, ID_Compra: {row['ID_Referencia']}")
else:
    print("✗ Columnas de referencia NO encontradas en kardex")

print("\n" + "=" * 60)
print("VERIFICACIÓN COMPLETADA")
print("=" * 60)
