"""
Sistema de Simulación Logística - LIA S.A.C.
Script principal de ejecución con Gestión de Inventario Profesional (DataFrame).
"""
import pandas as pd
import numpy as np
from logistica_sim.sistema.demanda import generar_demanda_diaria
from logistica_sim.sistema.inventario import GestionInventario
from logistica_sim.sistema.transporte import GestionTransporte
from logistica_sim.sistema import indicadores, alertas
from logistica_sim.sistema.catalogos import dic_zonas

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
        
        # 2.1. Atender Backlog (Prioridad antes de nuevos pedidos)
        items_backlog_despachados = gestion.atender_backlog(dia)
        
        # 3. Procesamiento de Pedidos (Compromiso y Despacho)
        pedidos_procesados_dia = []
        pedidos_para_transporte = []
        
        # Agregar items de backlog a transporte
        # Agrupar por pedido para reconstruir estructura de transporte
        backlog_por_pedido = {}
        for item in items_backlog_despachados:
            pid = item['id_pedido']
            if pid not in backlog_por_pedido:
                backlog_por_pedido[pid] = {'id_pedido': pid, 'cliente': item['cliente'], 'items': [], 'zona': 'General'}
            
            backlog_por_pedido[pid]['items'].append({'sku': item['sku'], 'cantidad': item['cantidad']})
            
        # Añadir backlog procesado a la lista de transporte
        for pid, p_data in backlog_por_pedido.items():
            # Buscar zona en lista_pedidos_db (histórico)
            # Esto es un poco ineficiente pero funcional para simulación pequeña
            zona_id_found = 'General'
            for p_hist in lista_pedidos_db:
                if p_hist['ID_Pedido'] == pid:
                    zona_id_found = p_hist['Zona_ID']  # Usar ID, no nombre
                    break
            p_data['zona'] = zona_id_found
            pedidos_para_transporte.append(p_data)

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
                estado_pedido = 'Pendiente' 
            
            # Determinar el día de entrega efectiva (hoy si se entregó algo, sino se marca como pendiente)
            dia_entrega = dia if cant_entregada > 0 else None
            
            # Crear detalle de items con cantidades
            items_detalle = []
            for item in pedido['items']:
                items_detalle.append({
                    'SKU': item['sku'],
                    'Cant_Solicitada': item['cantidad'],
                    'Cant_Entregada': sum(d['cantidad'] for d in items_despachados if d['sku'] == item['sku'])
                })
            
            # Guardar registro para df_pedidos
            lista_pedidos_db.append({
                'ID_Pedido': pedido['id_pedido'],
                'Fecha': dia,
                'Fecha_Entrega': dia_entrega,
                'Cliente': pedido['cliente_id'],
                'Zona_ID': pedido['zona_id'],  # ID para lógica interna
                'Zona': dic_zonas.get(pedido['zona_id'], pedido['zona_id']),  # Nombre para display
                'Producto': str([i['sku'] for i in pedido['items']]), # Simplificado para vista general
                'Items_Detalle': items_detalle,  # Detalle completo de productos
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
        # Primero calcular los KPIs base
        pedidos_dia_completos = [p for p in lista_pedidos_db if p['Fecha'] == dia]
        
        kpis_dia = indicadores.calcular_kpis_diarios(
            pedidos_dia, 
            pedidos_procesados_dia, 
            capacidad_picking,
            pedidos_dia_completos  # Pasar registros completos para cálculo correcto de OTIF
        )
        
        # Recalcular KPIs precisos basados en lo procesado hoy
        total_solicitado_dia = sum(p['Cant_Solicitada'] for p in lista_pedidos_db if p['Fecha'] == dia)
        total_entregado_dia = sum(p['Cant_Entregada'] for p in lista_pedidos_db if p['Fecha'] == dia)
        fill_rate_dia = (total_entregado_dia / total_solicitado_dia * 100) if total_solicitado_dia > 0 else 100
        kpis_dia['fill_rate'] = round(fill_rate_dia, 2)
        
        # OTIF: Pedidos completos entregados EL MISMO DÍA
        pedidos_otif = [
            p for p in pedidos_dia_completos 
            if p['Cant_Solicitada'] == p['Cant_Entregada']  # Completo
            and p['Fecha_Entrega'] == dia  # Entregado el mismo día
        ]
        otif_dia = (len(pedidos_otif) / len(pedidos_dia_completos) * 100) if len(pedidos_dia_completos) > 0 else 0
        kpis_dia['otif'] = round(otif_dia, 2)

        # Calcular Backlog Rate correcto (Unidades pendientes, NO perdidas)
        # Backlog = Total No Entregado - Ventas Perdidas
        unidades_no_entregadas = total_solicitado_dia - total_entregado_dia
        unidades_perdidas_dia = sum(vp.get('Cantidad_Perdida', 0) for vp in gestion.ventas_perdidas if vp.get('Fecha') == dia)
        unidades_backlog_dia = unidades_no_entregadas - unidades_perdidas_dia
        if unidades_backlog_dia < 0: unidades_backlog_dia = 0  # Failsafe
        
        backlog_rate_dia = (unidades_backlog_dia / total_solicitado_dia * 100) if total_solicitado_dia > 0 else 0
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
        'ventas_perdidas': pd.DataFrame(gestion.ventas_perdidas),
        'historial_backlog': pd.DataFrame(gestion.historial_backlog)
    }

if __name__ == "__main__":
    # Test rápido
    res = run_simulation(7, 1500)
    print(f"Simulación completada. Pedidos: {len(res['df_pedidos'])}")
    print(f"Tablas generadas: {res.keys()}")
