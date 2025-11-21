"""
Módulo de Picking
Gestiona la preparación de pedidos y la capacidad diaria.
"""

def asignar_picking(dia, pedidos, capacidad):
    """
    Asigna pedidos para picking considerando la capacidad diaria.
    Retorna los pedidos preparados y los pendientes (backlog).
    """
    preparados = []
    pendientes = []
    unidades_procesadas = 0
    
    for pedido in pedidos:
        # Calcular total de unidades del pedido
        total_unidades = sum(item["cantidad"] for item in pedido["items"])
        
        if unidades_procesadas + total_unidades <= capacidad:
            preparados.append(pedido)
            unidades_procesadas += total_unidades
        else:
            pendientes.append(pedido)
            
    return preparados, pendientes, unidades_procesadas
