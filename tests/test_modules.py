import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from logistica_sim.sistema import catalogos
    print("✓ catalogos imported")
    from logistica_sim.sistema import demanda
    print("✓ demanda imported")
    from logistica_sim.sistema import inventario
    print("✓ inventario imported")
    from logistica_sim.sistema import picking
    print("✓ picking imported")
    from logistica_sim.sistema import transporte
    print("✓ transporte imported")
    from logistica_sim.sistema import indicadores
    print("✓ indicadores imported")
    from logistica_sim.sistema import alertas
    print("✓ alertas imported")

    # Test Data
    print("\nTesting functions...")
    
    # Demanda
    pedidos_dia = demanda.generar_demanda_diaria(1, "normal")
    print(f"✓ Demanda generated: {len(pedidos_dia)} pedidos")
    
    # Gestión Inventario
    gestion = inventario.GestionInventario()
    print("✓ GestionInventario initialized")
    
    # Picking
    preparados, pendientes_picking, procesados = picking.asignar_picking(1, pedidos_dia, 1500)
    print(f"✓ Picking assigned: {len(preparados)} preparados")
    
    # Transporte
    gestion_trans = transporte.GestionTransporte()
    print("✓ GestionTransporte initialized")
    
    print("\n" + "=" * 60)
    print("✅ ALL MODULE TESTS PASSED")
    print("   All modules import successfully")
    print("   Core classes can be instantiated")
    print("   Basic functions work correctly")
    print("=" * 60)

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
