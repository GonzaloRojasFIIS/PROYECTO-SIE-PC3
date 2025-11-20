import main
import pandas as pd

def debug_chart():
    print("Running simulation...")
    res = main.run_simulation(7, 1500)
    
    df_productos = res['df_productos']
    print("\n--- df_productos head ---")
    print(df_productos.head())
    print(f"Index name: {df_productos.index.name}")
    
    print("\n--- Processing Daily Results ---")
    data_valor_diario = []
    
    for dia_data in res['resultados_diarios']:
        dia = dia_data['dia']
        df_snapshot = dia_data['estado_inventario']
        
        if dia == 1:
            print(f"\n--- Dia 1 Snapshot head ---")
            print(df_snapshot.head())
            print(f"Snapshot Index name: {df_snapshot.index.name}")
        
        valor_dia = 0
        for sku, row in df_snapshot.iterrows():
            stock = row['Stock_Fisico']
            
            # Debug lookup
            if sku not in df_productos.index:
                print(f"WARNING: SKU {sku} not found in df_productos")
                continue
                
            costo = df_productos.loc[sku, 'Costo_Unitario']
            valor_dia += stock * costo
        
        print(f"Dia {dia}: Valor Total = {valor_dia}")
        
        data_valor_diario.append({
            'Día': dia,
            'Valor_Total': valor_dia
        })

    df_costo = pd.DataFrame(data_valor_diario)
    print("\n--- Final DataFrame for Chart ---")
    print(df_costo)

if __name__ == "__main__":
    debug_chart()
