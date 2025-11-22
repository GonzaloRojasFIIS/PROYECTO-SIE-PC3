import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main
import pandas as pd

def debug_chart():
    print("=" * 60)
    print("DEBUG: Testing chart data generation")
    print("=" * 60)
    
    print("\nRunning 7-day simulation...")
    res = main.run_simulation(7, 1500, "normal")
    
    df_productos = res['df_productos']
    print("\n--- df_productos structure ---")
    print(f"Shape: {df_productos.shape}")
    print(f"Index name: {df_productos.index.name}")
    print(f"Columns: {list(df_productos.columns)}")
    print("\nFirst 3 products:")
    print(df_productos.head(3))
    
    print("\n--- Processing Daily Inventory Values ---")
    data_valor_diario = []
    
    for dia_data in res['resultados_diarios']:
        dia = dia_data['dia']
        df_snapshot = dia_data['estado_inventario']
        
        if dia == 1:
            print(f"\n--- Day 1 Snapshot ---")
            print(f"Shape: {df_snapshot.shape}")
            print(f"Index name: {df_snapshot.index.name}")
            print("First 3 items:")
            print(df_snapshot.head(3))
        
        valor_dia = 0
        skus_not_found = []
        
        for sku, row in df_snapshot.iterrows():
            stock = row['Stock_Fisico']
            
            if sku not in df_productos.index:
                skus_not_found.append(sku)
                continue
                
            costo = df_productos.loc[sku, 'Costo_Unitario']
            valor_dia += stock * costo
        
        if skus_not_found:
            print(f"⚠️  Day {dia}: {len(skus_not_found)} SKUs not found in df_productos")
        
        print(f"Day {dia}: Total Inventory Value = S/ {valor_dia:,.2f}")
        
        data_valor_diario.append({
            'Día': dia,
            'Valor_Total': valor_dia
        })

    df_costo = pd.DataFrame(data_valor_diario)
    print("\n--- Final DataFrame for Chart ---")
    print(df_costo)
    
    print("\n" + "=" * 60)
    print("✅ DEBUG COMPLETE: Data ready for charting")
    print("=" * 60)

if __name__ == "__main__":
    debug_chart()
