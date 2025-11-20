import pandas as pd
from gestion_inventario import GestionInventario

def test_stock_logic():
    print("Iniciando prueba de lógica de Stock Comprometido...")
    gestion = GestionInventario()
    
    # Seleccionar un SKU para probar
    sku_prueba = gestion.df_inventario.index[0]
    stock_inicial = gestion.df_inventario.loc[sku_prueba, 'Stock_Fisico']
    print(f"SKU: {sku_prueba}, Stock Inicial: {stock_inicial}")
    
    # Caso 1: Pedido Normal (Suficiente Stock)
    print("\n--- Caso 1: Pedido Normal ---")
    pedido_normal = {
        'id_pedido': 'P001',
        'cliente_id': 'C001',
        'zona_id': 'Z01',
        'items': [{'sku': sku_prueba, 'cantidad': 10}]
    }
    
    # Comprometer
    gestion.comprometer_stock(pedido_normal)
    comprometido = gestion.df_inventario.loc[sku_prueba, 'Stock_Comprometido']
    print(f"Comprometido tras pedido normal (esperado 10): {comprometido}")
    
    # Despachar
    gestion.despachar_pedido(pedido_normal, 1)
    comprometido_final = gestion.df_inventario.loc[sku_prueba, 'Stock_Comprometido']
    fisico_final = gestion.df_inventario.loc[sku_prueba, 'Stock_Fisico']
    print(f"Comprometido tras despacho (esperado 0): {comprometido_final}")
    print(f"Stock Físico tras despacho (esperado {stock_inicial - 10}): {fisico_final}")
    
    # Caso 2: Pedido que excede Stock (Quiebre)
    print("\n--- Caso 2: Pedido Excesivo (Quiebre) ---")
    # Forzar stock bajo para prueba
    gestion.df_inventario.loc[sku_prueba, 'Stock_Fisico'] = 5
    gestion.df_inventario.loc[sku_prueba, 'Stock_Comprometido'] = 0
    gestion._calcular_campos_derivados()
    
    pedido_excesivo = {
        'id_pedido': 'P002',
        'cliente_id': 'C002',
        'zona_id': 'Z01',
        'items': [{'sku': sku_prueba, 'cantidad': 20}] # Pide 20, hay 5
    }
    
    # Comprometer
    gestion.comprometer_stock(pedido_excesivo)
    comprometido = gestion.df_inventario.loc[sku_prueba, 'Stock_Comprometido']
    print(f"Stock Físico actual: 5")
    print(f"Comprometido tras pedido excesivo (esperado 5, max disponible): {comprometido}")
    
    # Despachar
    gestion.despachar_pedido(pedido_excesivo, 1)
    comprometido_final = gestion.df_inventario.loc[sku_prueba, 'Stock_Comprometido']
    fisico_final = gestion.df_inventario.loc[sku_prueba, 'Stock_Fisico']
    print(f"Comprometido tras despacho parcial/fallido (esperado 0): {comprometido_final}")
    print(f"Stock Físico tras despacho (esperado 0): {fisico_final}")
    
    if comprometido_final == 0:
        print("\n[EXITO] PRUEBA EXITOSA: El stock comprometido se limpia correctamente.")
    else:
        print(f"\n[ERROR] ERROR: Quedo stock comprometido: {comprometido_final}")

if __name__ == "__main__":
    test_stock_logic()
