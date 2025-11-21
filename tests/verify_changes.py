import main
import pandas as pd

def verify():
    print("Running simulation for verification...")
    # Run a 10-day simulation with high demand to force stockouts
    res = main.run_simulation(n_dias=10, capacidad_picking=1000, escenario="normal")
    
    # 1. Verify Stock Non-Negative
    df_inv = res['df_productos'].join(res['resultados_diarios'][-1]['estado_inventario'][['Stock_Fisico']])
    min_stock = df_inv['Stock_Fisico'].min()
    print(f"Min Stock Físico: {min_stock}")
    if min_stock < 0:
        print("FAIL: Stock Físico cannot be negative.")
    else:
        print("PASS: Stock Físico is non-negative.")
        
    # 2. Verify Lost Sales
    ventas_perdidas = res['ventas_perdidas']
    print(f"Ventas Perdidas: {len(ventas_perdidas)}")
    if not ventas_perdidas.empty:
        print("PASS: Lost sales recorded.")
    else:
        print("WARNING: No lost sales recorded (might be due to sufficient stock).")
        
    # 3. Verify Transport
    df_despachos = res['df_despachos']
    print(f"Despachos: {len(df_despachos)}")
    if not df_despachos.empty:
        overloaded = df_despachos[df_despachos['Peso_Total_Carga_kg'] > df_despachos['Capacidad_Max_kg']]
        if overloaded.empty:
            print("PASS: All dispatches within capacity.")
        else:
            print(f"FAIL: {len(overloaded)} dispatches overloaded.")
    else:
        print("WARNING: No dispatches generated.")

if __name__ == "__main__":
    verify()
