"""
Módulo de Demanda
Simula la llegada de pedidos diarios usando clientes fijos con frecuencias de compra.
"""
import random
from .catalogos import dic_clientes, FRECUENCIA_PESOS

def generar_demanda_diaria(dia, escenario="normal"):
    """
    Genera la lista de pedidos para un día específico.
    """
    from .catalogos import dic_sku, dic_zonas # Importar aquí para evitar ciclos si fuera necesario
    
    # Preparar lista de clientes ponderada por frecuencia
    clientes_ponderados = []
    for cliente_id, info in dic_clientes.items():
        frecuencia = info["frecuencia_compra"]
        peso = FRECUENCIA_PESOS.get(frecuencia, 1)
        clientes_ponderados.extend([cliente_id] * peso)
        
    # Aplicar multiplicador según escenario
    multiplicador_demanda = 1.0
    if escenario == "demanda_estacional" and 15 <= dia <= 20:
        multiplicador_demanda = 2.0  # Black Friday effect
    
    # Base de pedidos por día (ajustado por escenario)
    n_pedidos_base = random.randint(10, 15)
    n_pedidos = int(n_pedidos_base * multiplicador_demanda)
    
    pedidos_dia = []
    
    for i in range(n_pedidos):
        # Seleccionar cliente usando la lista ponderada
        cliente_id = random.choice(clientes_ponderados)
        zona_id = random.choice(list(dic_zonas.keys()))
        
        # Generar líneas de pedido (1 a 3 productos por pedido para variedad)
        n_lineas = random.randint(1, 3)
        items = []
        skus_disponibles = list(dic_sku.keys())
        
        # Evitar repetir SKU en el mismo pedido
        skus_seleccionados = random.sample(skus_disponibles, min(n_lineas, len(skus_disponibles)))
        
        for sku in skus_seleccionados:
            # Cantidad base ajustada por escenario
            cantidad_base = random.randint(5, 50)
            cantidad = int(cantidad_base * multiplicador_demanda)
            
            items.append({
                "sku": sku,
                "cantidad": cantidad
            })
        
        pedido = {
            "id_pedido": f"P{dia:02d}-{i+1:03d}",
            "cliente_id": cliente_id,
            "zona_id": zona_id,
            "items": items
        }
        pedidos_dia.append(pedido)
        
    return pedidos_dia

def simular_demanda(n_dias, dic_sku, escenario="normal"):
    """
    Simula la demanda para un número de días usando clientes fijos.
    Retorna un diccionario con los pedidos por día.
    """
    demanda_diaria = {}
    for dia in range(1, n_dias + 1):
        demanda_diaria[dia] = generar_demanda_diaria(dia, escenario)
    return demanda_diaria
