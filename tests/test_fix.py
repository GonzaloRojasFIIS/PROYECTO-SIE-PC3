
import main
import pandas as pd
import sys

try:
    print("Testing simulation run...")
    res = main.run_simulation(2, 1500, "normal")
    print("Simulation run successful!")
    print("Keys in result:", res.keys())
    if 'historial_inventario' in res:
        print("Historial inventario shape:", res['historial_inventario'].shape)
    else:
        print("Historial inventario missing")
except Exception as e:
    print(f"Error during simulation: {e}")
    import traceback
    traceback.print_exc()
