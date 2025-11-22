import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main
import pandas as pd

print("=" * 80)
print("TEST: VERIFICACIÓN BÁSICA DEL SISTEMA")
print("=" * 80)

try:
    print("\nEjecutando simulación de 5 días...")
    res = main.run_simulation(5, 1500, "normal")
    
    print("✓ Simulación completada exitosamente")
    
    print("\n" + "-" * 80)
    print("Componentes del resultado:")
    print("-" * 80)
    for key in res.keys():
        if isinstance(res[key], pd.DataFrame):
            print(f"✓ {key}: DataFrame ({len(res[key])} filas)")
        elif isinstance(res[key], list):
            print(f"✓ {key}: Lista ({len(res[key])} elementos)")
        elif isinstance(res[key], dict):
            print(f"✓ {key}: Diccionario ({len(res[key])} keys)")
        else:
            print(f"✓ {key}: {type(res[key]).__name__}")
    
    # Verificar componentes clave
    print("\n" + "-" * 80)
    print("Validaciones:")
    print("-" * 80)
    
    componentes_requeridos = [
        'df_productos', 'df_pedidos', 'df_kardex', 
        'df_compras', 'df_despachos', 'resultados_diarios',
        'metricas_globales'
    ]
    
    faltantes = []
    for comp in componentes_requeridos:
        if comp in res:
            print(f"✓ {comp} presente")
        else:
            print(f"✗ {comp} FALTANTE")
            faltantes.append(comp)
    
    print("\n" + "=" * 80)
    if not faltantes:
        print("✅ TEST EXITOSO: Sistema funciona correctamente")
    else:
        print(f"⚠️  TEST PARCIAL: Faltan {len(faltantes)} componentes")
    print("=" * 80)
    
except Exception as e:
    print(f"\n✗ Error durante la simulación: {e}")
    import traceback
    traceback.print_exc()
    print("\n" + "=" * 80)
    print("❌ TEST FALLIDO")
    print("=" * 80)
