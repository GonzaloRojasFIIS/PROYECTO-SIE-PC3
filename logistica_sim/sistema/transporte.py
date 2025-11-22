"""
Módulo de Transporte Consolidado
Administra la flota de vehículos, asignación de despachos y cálculo de ocupación por peso.
Consolida: transporte.py + gestion_transporte.py
"""
import pandas as pd
import numpy as np
from .catalogos import dic_zonas


# ============================================================================
# FUNCIONES BÁSICAS DE TRANSPORTE (de transporte.py original)
# ============================================================================

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


# ============================================================================
# CLASE DE GESTIÓN DE TRANSPORTE (de gestion_transporte.py)
# ============================================================================

class GestionTransporte:
    def __init__(self):
        """Inicializa la gestión de transporte."""
        self.flota = []
        self.despachos = []
        self.contador_despachos = 1
        
        self._inicializar_flota()
        
    def _inicializar_flota(self):
        """
        Crea la flota inicial de vehículos.
        """
        # Definición de flota estándar
        self.flota = [
            {'ID_Vehiculo': 'V-001', 'Tipo': 'Camión 5Ton', 'Capacidad_Max_kg': 5000, 'Costo_Por_Viaje': 150, 'Estado': 'Disponible'},
            {'ID_Vehiculo': 'V-002', 'Tipo': 'Camión 5Ton', 'Capacidad_Max_kg': 5000, 'Costo_Por_Viaje': 150, 'Estado': 'Disponible'},
            {'ID_Vehiculo': 'V-003', 'Tipo': 'Camión 10Ton', 'Capacidad_Max_kg': 10000, 'Costo_Por_Viaje': 280, 'Estado': 'Disponible'},
            {'ID_Vehiculo': 'V-004', 'Tipo': 'Furgoneta 1Ton', 'Capacidad_Max_kg': 1000, 'Costo_Por_Viaje': 80, 'Estado': 'Disponible'},
            {'ID_Vehiculo': 'V-005', 'Tipo': 'Camión 5Ton', 'Capacidad_Max_kg': 5000, 'Costo_Por_Viaje': 150, 'Estado': 'Disponible'}
        ]
        
    def obtener_flota_df(self):
        return pd.DataFrame(self.flota)
    
    def obtener_despachos_df(self):
        return pd.DataFrame(self.despachos)
        
    def planificar_despachos(self, dia_actual, pedidos_para_despacho, df_productos):
        """
        Asigna pedidos a vehículos basándose en el peso y la ZONA (Destino).
        Se intenta usar vehículos distintos para zonas distintas.
        
        Args:
            dia_actual: Día de la simulación.
            pedidos_para_despacho: Lista de pedidos listos (con items despachados).
            df_productos: DataFrame de productos para consultar pesos.
        """
        from .catalogos import dic_zonas

        if not pedidos_para_despacho:
            return [], []  # despachos_dia, pedidos_sin_asignar
            
        # 1. Calcular peso total por pedido y agrupar por ZONA
        pedidos_con_peso = []
        for pedido in pedidos_para_despacho:
            peso_total = 0
            items_validos = []
            
            for item in pedido['items']:
                sku = item['sku']
                cantidad = item['cantidad']
                peso_unitario = df_productos.loc[sku, 'Peso_Unitario_kg']
                peso_total += cantidad * peso_unitario
                items_validos.append(item)
            
            if peso_total > 0:
                pedidos_con_peso.append({
                    'id_pedido': pedido['id_pedido'],
                    'peso_kg': peso_total,
                    'cliente': pedido.get('cliente', 'Desconocido'),
                    'zona': pedido.get('zona', 'General')
                })
        
        # Agrupar pedidos por Zona
        pedidos_por_zona = {}
        for p in pedidos_con_peso:
            z = p['zona']
            if z not in pedidos_por_zona:
                pedidos_por_zona[z] = []
            pedidos_por_zona[z].append(p)

        # 2. Asignar a vehículos (Algoritmo Greedy por Zona)
        # Reiniciar estado de flota para el día
        vehiculos_disponibles = [v for v in self.flota if v['Estado'] == 'Disponible']
        # Ordenar vehículos por capacidad (usar los grandes primero)
        vehiculos_disponibles.sort(key=lambda x: x['Capacidad_Max_kg'], reverse=True)
        
        # Control de uso de vehículos en el día (para no reutilizar el mismo camión en zonas lejanas el mismo día)
        vehiculos_usados_hoy = set()
        
        despachos_dia = []
        pedidos_sin_asignar = []

        # Procesar cada zona
        for zona_id, pedidos_zona in pedidos_por_zona.items():
            nombre_zona = dic_zonas.get(zona_id, zona_id)
            
            # Ordenar pedidos de la zona por peso descendente
            pedidos_zona.sort(key=lambda x: x['peso_kg'], reverse=True)
            
            # Filtrar vehículos que NO han sido usados hoy todavía
            # (Si se acaban los libres, podríamos reusar, pero la regla pide "más de una flota")
            vehiculos_libres = [v for v in vehiculos_disponibles if v['ID_Vehiculo'] not in vehiculos_usados_hoy]
            
            # Si no hay libres, ¿reusamos? 
            # Para cumplir "si son destinos distintos deberían ir más de una flota", intentamos forzar distintos.
            # Si no hay suficientes camiones, quedarán pendientes o se reusan.
            # Vamos a intentar usar libres primero. Si no hay, usamos los ya usados (segunda vuelta).
            if not vehiculos_libres and vehiculos_disponibles:
                 vehiculos_libres = vehiculos_disponibles # Fallback: reusar si es absolutamente necesario
            
            # Ordenar libres por capacidad
            vehiculos_libres.sort(key=lambda x: x['Capacidad_Max_kg'], reverse=True)
            
            carga_vehiculos_zona = {v['ID_Vehiculo']: 0 for v in vehiculos_libres}
            pedidos_vehiculos_zona = {v['ID_Vehiculo']: [] for v in vehiculos_libres}
            
            pedidos_no_asignados_zona = []

            for pedido in pedidos_zona:
                asignado = False
                for vehiculo in vehiculos_libres:
                    vid = vehiculo['ID_Vehiculo']
                    capacidad = vehiculo['Capacidad_Max_kg']
                    carga_actual = carga_vehiculos_zona[vid]
                    
                    if carga_actual + pedido['peso_kg'] <= capacidad:
                        # Asignar
                        carga_vehiculos_zona[vid] += pedido['peso_kg']
                        pedidos_vehiculos_zona[vid].append(pedido['id_pedido'])
                        asignado = True
                        vehiculos_usados_hoy.add(vid) # Marcar como usado
                        break
                
                if not asignado:
                    pedidos_no_asignados_zona.append(pedido['id_pedido'])
            
            pedidos_sin_asignar.extend(pedidos_no_asignados_zona)

            # Generar despachos para esta zona
            for vehiculo in vehiculos_libres:
                vid = vehiculo['ID_Vehiculo']
                carga = carga_vehiculos_zona[vid]
                
                if carga > 0:
                    ocupacion = (carga / vehiculo['Capacidad_Max_kg']) * 100
                    
                    despacho = {
                        'ID_Despacho': f"D-{self.contador_despachos:04d}",
                        'Fecha_Salida': dia_actual,
                        'Destino': nombre_zona, # Nuevo campo solicitado
                        'ID_Vehiculo': vid,
                        'Tipo_Vehiculo': vehiculo['Tipo'],
                        'Peso_Total_Carga_kg': round(carga, 2),
                        'Capacidad_Max_kg': vehiculo['Capacidad_Max_kg'],
                        'Porcentaje_Ocupacion': round(ocupacion, 1),
                        'Costo_Viaje': vehiculo['Costo_Por_Viaje'],
                        'Pedidos_Asociados': ", ".join(pedidos_vehiculos_zona[vid]),
                        'Cant_Pedidos': len(pedidos_vehiculos_zona[vid])
                    }
                    
                    self.despachos.append(despacho)
                    despachos_dia.append(despacho)
                    self.contador_despachos += 1

        return despachos_dia, pedidos_sin_asignar
