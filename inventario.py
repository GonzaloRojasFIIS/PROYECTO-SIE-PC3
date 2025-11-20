"""
Módulo de Inventario
Gestiona el stock y la reposición automática.
"""

def reservar_y_actualizar(stock, pedido):
    """
    Reserva stock para un pedido y actualiza el inventario.
    Retorna una lista de items despachados y pendientes (si no hay stock).
    """
    despachado = []
    pendiente = []
    
    for item in pedido["items"]:
        sku = item["sku"]
        cantidad = item["cantidad"]
        
        if sku in stock:
            disponible = stock[sku]
            if disponible >= cantidad:
                stock[sku] -= cantidad
                despachado.append({
                    "sku": sku,
                    "cantidad": cantidad
                })
            else:
                # Despacho parcial si hay algo de stock
                if disponible > 0:
                    stock[sku] = 0
                    despachado.append({
                        "sku": sku,
                        "cantidad": disponible
                    })
                    pendiente.append({
                        "sku": sku,
                        "cantidad": cantidad - disponible
                    })
                else:
                    pendiente.append({
                        "sku": sku,
                        "cantidad": cantidad
                    })
        else:
            # SKU no existe en inventario (caso borde)
            pendiente.append({
                "sku": sku,
                "cantidad": cantidad
            })
            
    return despachado, pendiente

from catalogos import dic_sku

def reponer_por_demanda(stock, stock_inicial_dia, demanda_dia_por_sku):
    """
    Calcula la reposición basada en la demanda diaria comparada con el stock inicial.
    Si la demanda supera el stock inicial (quiebre de stock), calcula la cantidad necesaria
    para cubrir la demanda insatisfecha y restablecer el inventario al stock objetivo.
    
    Retorna un registro de las reposiciones realizadas.
    """
    reposiciones = []
    
    for sku, cantidad_actual in stock.items():
        # Obtener stock objetivo del catálogo
        info_sku = dic_sku.get(sku)
        if not info_sku:
            continue
            
        stock_objetivo = info_sku["stock_objetivo"]
        stock_inicial = stock_inicial_dia.get(sku, 0)
        demanda_total = demanda_dia_por_sku.get(sku, 0)
        
        # Verificar si hubo quiebre de stock (demanda > stock inicial)
        if demanda_total > stock_inicial:
            # Hay quiebre de stock: la demanda superó el inventario disponible
            demanda_insatisfecha = demanda_total - stock_inicial
            
            # Calcular la reposición necesaria para:
            # 1. Cubrir la demanda insatisfecha
            # 2. Restablecer el stock al nivel objetivo
            # Reposición = (demanda_insatisfecha) + (stock_objetivo - cantidad_actual)
            
            cantidad_a_reponer = stock_objetivo - cantidad_actual
            
            if cantidad_a_reponer > 0:
                stock[sku] += cantidad_a_reponer
                
                reposiciones.append({
                    "sku": sku,
                    "cantidad_agregada": cantidad_a_reponer,
                    "nuevo_stock": stock[sku],
                    "stock_objetivo": stock_objetivo,
                    "quiebre_stock": True,
                    "demanda_insatisfecha": demanda_insatisfecha
                })
        else:
            # No hubo quiebre, pero verificamos si el stock está bajo el objetivo
            if cantidad_actual < stock_objetivo:
                cantidad_a_reponer = stock_objetivo - cantidad_actual
                stock[sku] += cantidad_a_reponer
                
                reposiciones.append({
                    "sku": sku,
                    "cantidad_agregada": cantidad_a_reponer,
                    "nuevo_stock": stock[sku],
                    "stock_objetivo": stock_objetivo,
                    "quiebre_stock": False,
                    "demanda_insatisfecha": 0
                })
            
    return reposiciones
