import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main
import pandas as pd

def verify():
    print("=" * 60)
    print("VERIFICATION: Running simulation for system validation")
    print("=" * 60)
    
    # Run a 10-day simulation with normal capacity
    res = main.run_simulation(n_dias=10, capacidad_picking=1500, escenario="normal")
    
    print("\n--- Test 1: Stock Non-Negative ---")
    # Verify Stock Non-Negative
    df_inv_final = res['resultados_diarios'][-1]['estado_inventario']
    min_stock = df_inv_final['Stock_Fisico'].min()
    print(f"Minimum Stock Físico across all products: {min_stock}")
    if min_stock < 0:
        print("❌ FAIL: Stock Físico cannot be negative.")
    else:
        print("✅ PASS: Stock Físico is non-negative.")
        
    print("\n--- Test 2: Backlog/Lost Sales Recording ---")
    # Verify Backlog or Lost Sales
    backlog = res.get('backlog', pd.DataFrame())
    ventas_perdidas = res.get('ventas_perdidas', pd.DataFrame())
    
    total_backlog = len(backlog) if not backlog.empty else 0
    total_perdidas = len(ventas_perdidas) if not ventas_perdidas.empty else 0
    
    print(f"Backlog items: {total_backlog}")
    print(f"Ventas Perdidas: {total_perdidas}")
    
    if total_backlog > 0 or total_perdidas > 0:
        print("✅ PASS: System records stockout situations.")
    else:
        print("⚠️  INFO: No stockouts in this simulation (good inventory management).")
        
    print("\n--- Test 3: Transport Capacity ---")
    # Verify Transport
    df_despachos = res['df_despachos']
    print(f"Total dispatches: {len(df_despachos)}")
    if not df_despachos.empty:
        overloaded = df_despachos[df_despachos['Peso_Total_Carga_kg'] > df_despachos['Capacidad_Max_kg']]
        if overloaded.empty:
            print("✅ PASS: All dispatches within vehicle capacity.")
        else:
            print(f"❌ FAIL: {len(overloaded)} dispatches exceeded capacity.")
    else:
        print("⚠️  WARNING: No dispatches generated.")
        
    print("\n--- Test 4: KPIs Calculation ---")
    metricas = res['metricas_globales']
    print(f"Global OTIF: {metricas.get('otif_global', 0):.1f}%")
    print(f"Global Fill Rate: {metricas.get('fill_rate_global', 0):.1f}%")
    
    if 0 <= metricas.get('otif_global', 0) <= 100:
        print("✅ PASS: KPIs in valid range.")
    else:
        print("❌ FAIL: KPIs out of range.")
    
    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    verify()
