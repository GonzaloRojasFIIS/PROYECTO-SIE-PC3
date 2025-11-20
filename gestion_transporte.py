"""
Módulo de Gestión de Transporte
Administra la flota de vehículos, asignación de despachos y cálculo de ocupación por peso.
"""
import pandas as pd
import numpy as np

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
        Asigna pedidos a vehículos basándose en el peso.
        
        Args:
            dia_actual: Día de la simulación.
            pedidos_para_despacho: Lista de pedidos listos (con items despachados).
            df_productos: DataFrame de productos para consultar pesos.
        """
        if not pedidos_para_despacho:
            return [], []  # despachos_dia, pedidos_sin_asignar
            
        # 1. Calcular peso total por pedido
        pedidos_con_peso = []
        for pedido in pedidos_para_despacho:
            peso_total = 0
            items_validos = []
            
            # Nota: Los pedidos vienen de gestion_inventario.despachar_pedido (items_despachados)
            # Pero necesitamos la estructura completa del pedido para saber el ID.
            # Asumimos que 'pedidos_para_despacho' es una lista de dicts con {'id_pedido': ..., 'items': [...]}
            
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
        
        # Ordenar pedidos por peso descendente (Estrategia First Fit Decreasing simple)
        pedidos_con_peso.sort(key=lambda x: x['peso_kg'], reverse=True)
        
        # 2. Asignar a vehículos (Algoritmo Greedy simple)
        # Reiniciar estado de flota para el día (asumimos viajes diarios)
        vehiculos_disponibles = [v for v in self.flota if v['Estado'] == 'Disponible']
        # Ordenar vehículos por capacidad (usar los grandes primero o según estrategia)
        vehiculos_disponibles.sort(key=lambda x: x['Capacidad_Max_kg'], reverse=True)
        
        despachos_dia = []
        
        # Control de carga actual por vehículo
        carga_vehiculos = {v['ID_Vehiculo']: 0 for v in vehiculos_disponibles}
        pedidos_vehiculos = {v['ID_Vehiculo']: [] for v in vehiculos_disponibles}
        
        pedidos_sin_asignar = []
        
        for pedido in pedidos_con_peso:
            asignado = False
            for vehiculo in vehiculos_disponibles:
                vid = vehiculo['ID_Vehiculo']
                capacidad = vehiculo['Capacidad_Max_kg']
                carga_actual = carga_vehiculos[vid]
                
                if carga_actual + pedido['peso_kg'] <= capacidad:
                    # Asignar
                    carga_vehiculos[vid] += pedido['peso_kg']
                    pedidos_vehiculos[vid].append(pedido['id_pedido'])
                    asignado = True
                    break
            
            if not asignado:
                pedidos_sin_asignar.append(pedido['id_pedido'])
        
        # 3. Generar registros de despacho
        for vehiculo in vehiculos_disponibles:
            vid = vehiculo['ID_Vehiculo']
            carga = carga_vehiculos[vid]
            
            if carga > 0:
                ocupacion = (carga / vehiculo['Capacidad_Max_kg']) * 100
                
                despacho = {
                    'ID_Despacho': f"D-{self.contador_despachos:04d}",
                    'Fecha_Salida': dia_actual,
                    'ID_Vehiculo': vid,
                    'Tipo_Vehiculo': vehiculo['Tipo'],
                    'Peso_Total_Carga_kg': round(carga, 2),
                    'Capacidad_Max_kg': vehiculo['Capacidad_Max_kg'],
                    'Porcentaje_Ocupacion': round(ocupacion, 1),
                    'Costo_Viaje': vehiculo['Costo_Por_Viaje'],
                    'Pedidos_Asociados': ", ".join(pedidos_vehiculos[vid]),
                    'Cant_Pedidos': len(pedidos_vehiculos[vid])
                }
                
                self.despachos.append(despacho)
                despachos_dia.append(despacho)
                self.contador_despachos += 1
                
        return despachos_dia, pedidos_sin_asignar
