"""
Sistema de Simulación Logística - LIA S.A.C.
Script principal de ejecución con Gestión de Inventario Profesional (DataFrame).
"""
import pandas as pd
import numpy as np
from demanda import generar_demanda_diaria
from gestion_inventario import GestionInventario
from gestion_transporte import GestionTransporte
import indicadores
import alertas

def run_simulation(n_dias, capacidad_picking, escenario="normal"):
    """
    Ejecuta la simulación completa día a día.
    """
    # Inicializar módulos
    gestion = GestionInventario()
    transporte = GestionTransporte()
    
    resultados_diarios = []
    lista_pedidos_db = [] # Para construir df_pedidos
    
    # Loop de Simulación
    for dia in range(1, n_dias + 1):
        # 1. Generar Demanda (Pedidos)
        pedidos_dia = generar_demanda_diaria(dia, escenario)
        
        # 2. Recepción de Compras (Entradas de Stock)
        recepciones = gestion.recibir_ordenes_compra(dia)
        
        # 3. Procesamiento de Pedidos (Compromiso y Despacho)
        pedidos_procesados_dia = []
        pedidos_para_transporte = []
        
        for pedido in pedidos_dia:
            # Intentar comprometer stock
            exito, comprometidos, faltantes = gestion.comprometer_stock(pedido)
            
            # Despachar (Mueve de Físico a Cliente y registra Kardex)
            items_despachados = gestion.despachar_pedido(pedido, dia)
            
            # Calcular estado del pedido
            cant_solicitada = sum(i['cantidad'] for i in pedido['items'])
            cant_entregada = sum(i['cantidad'] for i in items_despachados)
            
            estado_pedido = 'Pendiente'
            if cant_entregada == cant_solicitada:
                estado_pedido = 'Entregado Total'
            elif cant_entregada > 0:
                estado_pedido = 'Entregado Parcial'
            else:
                estado_pedido = 'No Atendido'
            
            # Guardar registro para df_pedidos
            lista_pedidos_db.append({
                'ID_Pedido': pedido['id_pedido'],
                'Fecha': dia,
                'Cliente': pedido['cliente_id'],
                'Zona': pedido['zona_id'],
                'Producto': str([i['sku'] for i in pedido['items']]), # Simplificado para vista general
                'Cant_Solicitada': cant_solicitada,
                'Cant_Entregada': cant_entregada,
                'Estado': estado_pedido
            })
            
            # Preparar para transporte (solo lo que se despachó efectivamente)
            if cant_entregada > 0:
                # Reconstruir estructura para transporte con items despachados
                pedido_transporte = {
                    'id_pedido': pedido['id_pedido'],
                    'cliente': pedido['cliente_id'],
                    'zona': pedido['zona_id'],
                    'items': items_despachados # Solo lo que se mueve
                }
                pedidos_para_transporte.append(pedido_transporte)
        
        # 4. Planificación de Transporte
        despachos_dia, no_asignados = transporte.planificar_despachos(dia, pedidos_para_transporte, gestion.df_productos)
        
        # 5. Reposición (Compras a Proveedores)
        ordenes_generadas = gestion.verificar_reposicion(dia, escenario)
        
        # 6. Cálculo de KPIs y Alertas del Día
        kpis_dia = indicadores.calcular_kpis_diarios(
            pedidos_dia, 
            pedidos_procesados_dia, 
            capacidad_picking
        )
        
        # Recalcular KPIs precisos basados en lo procesado hoy
        total_solicitado_dia = sum(p['Cant_Solicitada'] for p in lista_pedidos_db if p['Fecha'] == dia)
        total_entregado_dia = sum(p['Cant_Entregada'] for p in lista_pedidos_db if p['Fecha'] == dia)
        fill_rate_dia = (total_entregado_dia / total_solicitado_dia * 100) if total_solicitado_dia > 0 else 100
        
        kpis_dia['fill_rate'] = round(fill_rate_dia, 2)
        
        # Calcular OTIF (On Time In Full) - Pedidos entregados 100% completos
        pedidos_hoy = [p for p in lista_pedidos_db if p['Fecha'] == dia]
        pedidos_perfectos = [p for p in pedidos_hoy if p['Cant_Solicitada'] == p['Cant_Entregada']]
        otif_dia = (len(pedidos_perfectos) / len(pedidos_hoy) * 100) if len(pedidos_hoy) > 0 else 0
        kpis_dia['otif'] = round(otif_dia, 2)
        
        # Calcular Backlog Rate (Unidades Perdidas / Total Solicitado)
        unidades_perdidas_dia = sum(vp.get('Cantidad_Perdida', 0) for vp in gestion.ventas_perdidas if vp.get('Fecha') == dia)
        backlog_rate_dia = (unidades_perdidas_dia / total_solicitado_dia * 100) if total_solicitado_dia > 0 else 0
        kpis_dia['backlog_rate'] = round(backlog_rate_dia, 2)
        
        # Calcular Utilización de Flota (Ocupación promedio de vehículos usados)
        if despachos_dia:
            ocupacion_promedio = sum(d['Porcentaje_Ocupacion'] for d in despachos_dia) / len(despachos_dia)
            kpis_dia['utilizacion_flota'] = round(ocupacion_promedio, 2)
        else:
            kpis_dia['utilizacion_flota'] = 0.0
        
        alertas_dia = alertas.generar_alertas(
            gestion.df_inventario, 
            gestion.df_productos,
            kpis_dia, 
            dia
        )
        
        # Guardar estado diario
        resultados_diarios.append({
            "dia": dia,
            "kpis": kpis_dia,
            "alertas": alertas_dia,
            "estado_inventario": gestion.df_inventario.copy() # Snapshot
        })

    # --- Generación de Resultados Finales ---
    tablas_inventario = gestion.obtener_tablas_finales()
    df_pedidos = pd.DataFrame(lista_pedidos_db)
    
    # Métricas Globales
    metricas_globales = indicadores.calcular_metricas_globales(resultados_diarios)
    metricas_globales['valor_total_inventario'] = (
        tablas_inventario['df_estado_actual']['Stock_Fisico'] * 
        tablas_inventario['df_estado_actual']['Costo_Unitario']
    ).sum()
    
    # Tablas de Transporte
    df_flota = transporte.obtener_flota_df()
    df_despachos = transporte.obtener_despachos_df()
    
    return {
        'config': {'n_dias': n_dias, 'escenario': escenario},
        'resultados_diarios': resultados_diarios,
        'metricas_globales': metricas_globales,
        'df_productos': tablas_inventario['df_productos'],
        'df_pedidos': df_pedidos,
        'df_compras': tablas_inventario['df_compras'],
        'df_kardex': tablas_inventario['df_kardex'],
        'df_flota': df_flota,
        'df_despachos': df_despachos,
        'ventas_perdidas': pd.DataFrame(gestion.ventas_perdidas)
    }

if __name__ == "__main__":
    # Test rápido
    res = run_simulation(7, 1500)
    print(f"Simulación completada. Pedidos: {len(res['df_pedidos'])}")
    print(f"Tablas generadas: {res.keys()}")
