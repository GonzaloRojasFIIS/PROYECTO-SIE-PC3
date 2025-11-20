
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

try:
    import catalogos
    print("catalogos imported")
    import demanda
    print("demanda imported")
    import inventario
    print("inventario imported")
    import picking
    print("picking imported")
    import transporte
    print("transporte imported")
    import indicadores
    print("indicadores imported")
    import alertas
    print("alertas imported")

    # Test Data
    print("Testing functions...")
    
    # Demanda
    pedidos = demanda.simular_demanda(1, catalogos.dic_clientes, catalogos.dic_sku)
    print(f"Demanda generated: {len(pedidos[1])} pedidos")
    
    # Inventario
    stock = {sku: 200 for sku in catalogos.dic_sku}
    pedido = pedidos[1][0]
    despachado, pendiente = inventario.reservar_y_actualizar(stock, pedido)
    print("Inventario updated")
    
    # Picking
    preparados, pendientes_picking, procesados = picking.asignar_picking(1, pedidos[1], 1500)
    print(f"Picking assigned: {len(preparados)} preparados")
    
    # Transporte
    rutas, costo = transporte.planificar_rutas(1, preparados, catalogos.dic_vehiculos)
    print(f"Transporte planned: {len(rutas)} rutas")
    
    # Indicadores
    kpis = indicadores.calcular_indicadores(pedidos[1], preparados, pendientes_picking, rutas, 1500)
    print("KPIs calculated")
    print(kpis)
    
    # Alertas
    msgs = alertas.generar_alertas(kpis, {})
    print("Alertas generated")
    
    print("ALL TESTS PASSED")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
