"""
Módulo de Indicadores
Calcula los KPIs logísticos.
"""

from catalogos import dic_vehiculos

def calcular_kpis_diarios(pedidos_dia, pedidos_entregados, capacidad_picking, pedidos_dia_completos=None):
    """
    Calcula KPIs diarios.
    Nota: pedidos_entregados puede ser una lista de pedidos o estar vacío si se calcula fuera.
    pedidos_dia_completos: Lista de registros completos de pedidos para cálculo preciso de OTIF (opcional).
    """
    total_pedidos = len(pedidos_dia)
    
    # Si no se pasa lista de entregados, asumimos 0 para cálculos internos (se actualizarán fuera)
    total_entregados = len(pedidos_entregados)
    
    # OTIF se calculará en main.py con datos precisos
    # Aquí solo retornamos estructura base
    otif = 0.0
    
    return {
        "otif": round(otif, 2),
        "fill_rate": 0.0, # Se calcula fuera con precisión
        "backlog_rate": 0.0, # Se calcula fuera
        "productividad": 0.0,
        "utilizacion_flota": 0.0, # Se calcula en transporte
        "total_pedidos": total_pedidos
    }

def calcular_metricas_globales(resultados_diarios):
    """
    Calcula promedios globales de los KPIs diarios.
    """
    if not resultados_diarios:
        return {}
        
    df_res = pd.DataFrame([r['kpis'] for r in resultados_diarios])
    
    return {
        "otif_promedio": round(df_res['otif'].mean(), 2),
        "fill_rate_promedio": round(df_res['fill_rate'].mean(), 2),
        "total_pedidos": df_res['total_pedidos'].sum()
    }
    
import pandas as pd
