"""
Script para verificar movimientos de compra con periodo más largo
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main

print("Ejecutando simulación de 15 días...")
resultados = main.run_simulation(n_dias=15, capacidad_picking=1500, escenario="normal")

df_kardex = resultados['df_kardex']
df_compras = resultados['df_compras']

print(f"\nTotal de órdenes de compra generadas: {len(df_compras)}")
print(f"Órdenes recibidas: {len(df_compras[df_compras['Estado'] == 'Recibido'])}")

print("\nPrimeras 5 órdenes de compra:")
print("=" * 100)
for idx, row in df_compras.head(5).iterrows():
    print(f"ID: {row['ID_Compra']} | Creación: Día {row['Fecha_Creacion']} | Arribo: Día {row['Fecha_Arribo']} | Producto: {row['Producto']} | Estado: {row['Estado']}")

print("\nMovimientos de COMPRA_RECEPCION en kardex:")
print("=" * 100)

compras = df_kardex[df_kardex['Tipo_Movimiento'] == 'COMPRA_RECEPCION']

if not compras.empty:
    print(f"Total de recepciones registradas: {len(compras)}\n")
    for idx, row in compras.head(10).iterrows():
        print(f"Día {row['Fecha']:>2} | Producto: {row['Producto']} | Cantidad: {row['Cantidad']:>4} | ID_Compra: {row['ID_Referencia']} | Tipo: {row['Tipo_Referencia']}")
else:
    print("No se encontraron movimientos de compra")

print("\n" + "=" * 100)
