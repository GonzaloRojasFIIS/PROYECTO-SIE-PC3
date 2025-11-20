"""
Módulo de Alertas
Genera alertas basadas en los indicadores y umbrales definidos.
"""

def generar_alertas(df_inventario, df_productos, indicadores, dia):
    """
    Genera alertas basadas en el estado del inventario y los KPIs del día.
    """
    alertas = []
    
    # 1. Alertas de Inventario (Stock Crítico)
    # Unir con df_productos para obtener Stock_Seguridad
    # Asumimos que ambos tienen el mismo índice (ID_Producto)
    df_full = df_inventario.join(df_productos[['Stock_Seguridad']])
    
    criticos = df_full[df_full['Stock_Fisico'] <= df_full['Stock_Seguridad']]
    
    for sku, row in criticos.iterrows():
        alertas.append({
            'Fecha': dia,
            'Tipo': 'Inventario Crítico',
            'Mensaje': f"Producto {sku} con stock bajo ({row['Stock_Fisico']} < {row['Stock_Seguridad']}).",
            'Nivel': 'Alto'
        })
        
    # 2. Alertas de KPIs
    if indicadores['otif'] < 90:
        alertas.append({
            'Fecha': dia,
            'Tipo': 'KPI Bajo',
            'Mensaje': f"OTIF del día bajo: {indicadores['otif']}% (Meta: 90%)",
            'Nivel': 'Medio'
        })
        
    if indicadores.get('fill_rate', 100) < 95:
        alertas.append({
            'Fecha': dia,
            'Tipo': 'KPI Bajo',
            'Mensaje': f"Fill Rate bajo: {indicadores['fill_rate']}% (Meta: 95%)",
            'Nivel': 'Medio'
        })

    return alertas
