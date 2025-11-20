"""
Módulo de Transporte
Planifica las rutas y asigna vehículos.
"""
from catalogos import dic_zonas

def planificar_rutas(dia, pedidos_preparados, vehiculos):
    """
    Asigna pedidos a vehículos y planifica rutas.
    Retorna la planificación de rutas y el costo total.
    """
    rutas = []
    costo_total = 0
    
    # Agrupar pedidos por ZONA (no por cliente)
    pedidos_por_zona = {}
    for pedido in pedidos_preparados:
        zona_id = pedido["zona_id"]
        if zona_id not in pedidos_por_zona:
            pedidos_por_zona[zona_id] = 0
        
        # Sumar unidades
        total_unidades = sum(item["cantidad"] for item in pedido["items"])
        pedidos_por_zona[zona_id] += total_unidades
        
    # Asignar vehículos a zonas (simplificado: 1 vehículo por zona si alcanza capacidad)
    # En un caso real esto sería un problema de optimización (VRP)
    
    vehiculos_disponibles = list(vehiculos.keys())
    idx_vehiculo = 0
    
    for zona_id, cantidad_total in pedidos_por_zona.items():
        nombre_zona = dic_zonas[zona_id]
        
        # Asignar vehículo disponible (round-robin simple para el ejemplo)
        vehiculo_id = vehiculos_disponibles[idx_vehiculo % len(vehiculos_disponibles)]
        info_vehiculo = vehiculos[vehiculo_id]
        capacidad = info_vehiculo["capacidad"]
        costo_km = info_vehiculo["costo_km"]
        
        # Calcular utilización
        # Si la cantidad excede la capacidad, se necesitarían más viajes o vehículos
        # Para simplificar, asumimos que se hace el viaje con lo que cabe o múltiples viajes
        # pero calculamos utilización sobre la capacidad de UN viaje para el reporte
        
        utilizacion = min(cantidad_total, capacidad) / capacidad * 100
        
        # Costo estimado (asumimos distancia fija promedio por zona para el ejemplo, ej. 50km)
        distancia_promedio = 50 
        costo_viaje = distancia_promedio * costo_km
        
        rutas.append({
            "vehiculo": vehiculo_id,
            "zona": nombre_zona,
            "cantidad": cantidad_total,
            "utilizacion": utilizacion,
            "costo": costo_viaje
        })
        
        costo_total += costo_viaje
        idx_vehiculo += 1
        
    return rutas, costo_total
