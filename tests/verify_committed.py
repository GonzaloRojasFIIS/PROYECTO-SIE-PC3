import main
import pandas as pd

# Run simulation
print("Running simulation...")
res = main.run_simulation(15, 1500)

# Check last day inventory status
df_estado = res['resultados_diarios'][-1]['estado_inventario']
print("\nLast Day Inventory Status (Sample):")
print(df_estado[['Stock_Fisico', 'Stock_Comprometido', 'Stock_Disponible']].head())

# Check if any Committed Stock > 0
comprometido_total = df_estado['Stock_Comprometido'].sum()
print(f"\nTotal Committed Stock on Last Day: {comprometido_total}")

if comprometido_total > 0:
    print("SUCCESS: Committed Stock is being maintained for backlog items.")
else:
    print("WARNING: Committed Stock is 0. Check if there is any backlog remaining.")
