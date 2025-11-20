"""
Módulo de Reporte
Genera el reporte final consolidado.
"""

def reporte_logistica(pedidos, indicadores, alertas):
    """
    Imprime el reporte consolidado de la simulación.
    """
    print("\n===== REPORTE LOGÍSTICO SEMANAL - LIA S.A.C. =====")
    print("Resumen de operaciones:")
    print(f"Total pedidos recibidos: {indicadores['total_pedidos']}")
    print(f"Total unidades solicitadas: {indicadores['total_unidades']:,}")
    print(f"Total unidades entregadas: {indicadores['unidades_entregadas']:,}")
    print(f"Backlog total: {indicadores['backlog_unidades']:,} unidades ({indicadores['backlog_rate']}%)")
    
    print("\nIndicadores globales:")
    print(f"OTIF: {indicadores['otif']} %")
    print(f"Fill Rate: {indicadores['fill_rate']} %")
    print(f"Backlog Rate: {indicadores['backlog_rate']} %")
    print(f"Productividad de Picking: {indicadores['productividad']} unid/h")
    print(f"Utilización de flota: {indicadores['utilizacion_flota']} %")
    
    print("\nAlertas activas:")
    if alertas:
        for alerta in alertas:
            print(f" - {alerta}")
    else:
        print(" - Ninguna alerta detectada.")
        
    print("\nRecomendaciones:")
    if indicadores['otif'] < 95:
        print("- Verificar tiempos de preparación y capacidad de picking.")
    if indicadores['utilizacion_flota'] > 85:
        print("- Considerar ampliar la flota o renegociar horarios de entrega.")
    if indicadores['backlog_rate'] > 5:
        print("- Incrementar personal de picking los días de alta demanda.")
    if indicadores['utilizacion_flota'] < 50:
        print("- Optimizar rutas para consolidar carga.")
    if not alertas and indicadores['otif'] >= 95:
        print("- Operación estable. Mantener monitoreo.")
