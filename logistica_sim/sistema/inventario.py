"""
Módulo de Inventario Consolidado
Gestiona el stock, reposición automática y sistema completo de inventario ERP.
Consolida: inventario.py + gestion_inventario.py + estado_inventario.py
"""
import pandas as pd
import numpy as np
from .catalogos import dic_sku


# ============================================================================
# FUNCIONES BÁSICAS DE INVENTARIO (de inventario.py original)
# ============================================================================

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


# ============================================================================
# CLASE PRINCIPAL DE GESTIÓN DE INVENTARIO (de gestion_inventario.py)
# ============================================================================

class GestionInventario:
    """
    Clase que gestiona el inventario con estructura DataFrame profesional.
    Incluye Kardex, Maestro de Productos y Gestión de Órdenes.
    """
    
    def __init__(self):
        """Inicializa el sistema de inventario con datos maestros."""
        # Tablas Transaccionales - Inicializar antes de llamar a métodos que las usen
        self.ordenes_compra = []  # Lista de diccionarios para df_compras
        self.kardex = []          # Lista de diccionarios para df_kardex
        self.ventas_perdidas = [] # Registro de demanda insatisfecha
        self.backlog = []         # Registro de pedidos pendientes por falta de stock (Clientes que esperan)
        self.historial_backlog = [] # Registro histórico de todos los ingresos a backlog
        
        # Contadores de IDs
        self.contador_compras = 1
        
        self._inicializar_datos_maestros()
        self._inicializar_estado_dinamico()
        
    def _inicializar_datos_maestros(self):
        """
        Crea el DataFrame de datos maestros (df_productos).
        Campos: ID, Nombre, Stock_Inicial, Stock_Seguridad, Punto_Reorden, Lead_Time, Costo, Q_Lote_Optimo
        """
        datos_maestros = []
        
        for sku, info in dic_sku.items():
            # Calcular EOQ (Economic Order Quantity) simplificado
            # Aumentado de 60% a 80% para asegurar mejor reposición
            q_lote = int(info['stock_objetivo'] * 0.8)
            
            datos_maestros.append({
                'ID_Producto': sku,
                'Nombre_Producto': info['nombre'],
                'Categoria': info.get('categoria', 'General'),
                'Stock_Seguridad': info['stock_minimo'],
                'Punto_Reorden': int(info['stock_minimo'] * 2.0),  # Aumentado de 1.5 a 2.0
                'Stock_Objetivo': info['stock_objetivo'], # Agregado para cálculo de reposición inteligente
                'Lead_Time': info['lead_time_dias'],
                'Q_Lote_Optimo': q_lote,
                'Costo_Unitario': info['costo_unitario'],
                'Precio_Venta': info['precio_venta'],
                'Peso_Unitario_kg': info.get('peso_kg', 1.0) # Default 1kg si no existe
            })
        
        self.df_productos = pd.DataFrame(datos_maestros)
        self.df_productos.set_index('ID_Producto', inplace=True)
    
    def _inicializar_estado_dinamico(self):
        """
        Crea el DataFrame de estado dinámico (variables diarias).
        """
        index = self.df_productos.index
        
        self.df_inventario = pd.DataFrame({
            'Stock_Fisico': [self.df_productos.loc[sku, 'Q_Lote_Optimo'] * 2 for sku in index], # Stock inicial arbitrario pero saludable
            'Stock_Comprometido': [0 for _ in index],
            'Stock_En_Transito': [0 for _ in index],
        }, index=index)
        
        # Registrar saldo inicial en Kardex
        for sku in index:
            self._registrar_kardex(0, sku, 'SALDO_INICIAL', self.df_inventario.loc[sku, 'Stock_Fisico'], self.df_inventario.loc[sku, 'Stock_Fisico'])
            
        self._calcular_campos_derivados()
    
    def _calcular_campos_derivados(self):
        """Calcula los campos que se derivan de otros."""
        self.df_inventario['Stock_Disponible'] = (
            self.df_inventario['Stock_Fisico'] - 
            self.df_inventario['Stock_Comprometido']
        )
        
        self.df_inventario['Posicion_Inventario'] = (
            self.df_inventario['Stock_Disponible'] + 
            self.df_inventario['Stock_En_Transito']
        )
        
    def _registrar_kardex(self, dia, sku, tipo_movimiento, cantidad, saldo_final, id_referencia=None, tipo_referencia=None):
        """Registra un movimiento en el Kardex con referencia opcional a pedido/compra."""
        registro = {
            'Fecha': dia,
            'Producto': sku,
            'Tipo_Movimiento': tipo_movimiento,
            'Cantidad': cantidad,
            'Saldo_Final': saldo_final,
            'ID_Referencia': id_referencia if id_referencia else '',
            'Tipo_Referencia': tipo_referencia if tipo_referencia else ''
        }
        self.kardex.append(registro)

    def recibir_ordenes_compra(self, dia_actual):
        """
        Procesa las órdenes de compra que llegan en el día actual.
        Actualiza Stock_Fisico, Stock_En_Transito y Kardex.
        """
        recepciones = []
        
        # Filtrar órdenes que llegan hoy
        for orden in self.ordenes_compra:
            if orden['Estado'] == 'En Transito' and orden['Fecha_Arribo'] <= dia_actual:
                sku = orden['Producto']
                cantidad = orden['Cantidad']
                
                # Actualizar Inventario
                self.df_inventario.loc[sku, 'Stock_Fisico'] += cantidad
                self.df_inventario.loc[sku, 'Stock_En_Transito'] -= cantidad
                
                # Actualizar Estado de la Orden
                orden['Estado'] = 'Recibido'
                
                # Registrar en Kardex
                self._registrar_kardex(
                    dia_actual, sku, 'COMPRA_RECEPCION', cantidad, 
                    self.df_inventario.loc[sku, 'Stock_Fisico'],
                    id_referencia=orden['ID_Compra'],
                    tipo_referencia='compra'
                )
                
                recepciones.append(orden)
        
        self._calcular_campos_derivados()
        return recepciones
    
    def comprometer_stock(self, pedido):
        """
        Compromete el stock para un pedido.
        Retorna (Exito, ListaComprometidos, ListaFaltantes)
        """
        exito_total = True
        items_comprometidos = []
        items_faltantes = []
        
        for item in pedido['items']:
            sku = item['sku']
            cantidad_solicitada = item['cantidad']
            
            disponible = self.df_inventario.loc[sku, 'Stock_Disponible']
            
            if disponible >= cantidad_solicitada:
                self.df_inventario.loc[sku, 'Stock_Comprometido'] += cantidad_solicitada
                items_comprometidos.append({'sku': sku, 'cantidad': cantidad_solicitada})
            else:
                exito_total = False
                cantidad_faltante = cantidad_solicitada - disponible
                
                if disponible > 0:
                    self.df_inventario.loc[sku, 'Stock_Comprometido'] += disponible
                    items_comprometidos.append({'sku': sku, 'cantidad': disponible})
                
                items_faltantes.append({'sku': sku, 'cantidad_faltante': cantidad_faltante})
        
        self._calcular_campos_derivados()
        return exito_total, items_comprometidos, items_faltantes
    
    def despachar_pedido(self, pedido, dia_actual):
        """
        Despacha un pedido.
        Lógica Profesional:
        - Si hay stock suficiente: Despacha todo.
        - Si NO hay stock suficiente: 
            - Evalúa si el cliente espera (Backlog) o se va (Venta Perdida) según su probabilidad.
        - NUNCA deja Stock_Fisico en negativo.
        """
        from .catalogos import dic_clientes # Importar aquí para acceder a probabilidad
        import random

        items_despachados = []
        cliente_id = pedido.get('cliente_id')
        prob_espera = 0.5 # Default
        
        if cliente_id and cliente_id in dic_clientes:
            prob_espera = dic_clientes[cliente_id].get('probabilidad_espera', 0.5)

        for item in pedido['items']:
            sku = item['sku']
            cantidad_solicitada = item['cantidad']
            
            stock_actual = self.df_inventario.loc[sku, 'Stock_Fisico']
            comprometido_actual = self.df_inventario.loc[sku, 'Stock_Comprometido']
            
            # Determinar cuánto podemos despachar realmente
            cantidad_a_despachar = min(cantidad_solicitada, stock_actual)
            
            # Actualizar Stock Físico
            if cantidad_a_despachar > 0:
                self.df_inventario.loc[sku, 'Stock_Fisico'] -= cantidad_a_despachar
                
                # Reducir el comprometido asociado
                reducir_compromiso = min(cantidad_solicitada, comprometido_actual)
                self.df_inventario.loc[sku, 'Stock_Comprometido'] -= reducir_compromiso
                
                items_despachados.append({
                    'sku': sku,
                    'cantidad': cantidad_a_despachar
                })
                
                # Registrar en Kardex (Salida)
                self._registrar_kardex(
                    dia_actual, sku, 'VENTA_DESPACHO', -cantidad_a_despachar,
                    self.df_inventario.loc[sku, 'Stock_Fisico'],
                    id_referencia=pedido['id_pedido'],
                    tipo_referencia='pedido'
                )
            
            # Manejo de Faltantes: Backlog o Venta Perdida
            if cantidad_a_despachar < cantidad_solicitada:
                cantidad_faltante = cantidad_solicitada - cantidad_a_despachar
                
                # Decisión del Cliente: ¿Espera o se va?
                decision_espera = random.random() < prob_espera
                
                if decision_espera:
                    # BACKLOG: El cliente espera
                    # IMPORTANTE: Asegurar que el Stock Comprometido refleje este pendiente
                    self.df_inventario.loc[sku, 'Stock_Comprometido'] += cantidad_faltante
                    
                    self.backlog.append({
                        'Fecha_Pedido': dia_actual,
                        'ID_Pedido': pedido['id_pedido'],
                        'Cliente': cliente_id,
                        'Producto': sku,
                        'Cantidad_Pendiente': cantidad_faltante,
                        'Prioridad': prob_espera # Usar prob como proxy de prioridad/importancia
                    })
                    
                    # Registrar en histórico de backlog (para reportes)
                    self.historial_backlog.append({
                        'Fecha_Ingreso': dia_actual,
                        'Cliente': cliente_id,
                        'ID_Pedido': pedido['id_pedido'],
                        'Producto': sku,
                        'Cantidad_Pendiente': cantidad_faltante,
                        'Probabilidad_Espera': prob_espera,
                        'Estado': 'Ingresado a Backlog'
                    })
                    
                else:
                    # VENTA PERDIDA: El cliente se va
                    self.df_inventario.loc[sku, 'Stock_Comprometido'] -= cantidad_faltante
                    
                    # Asegurar no negativos (por si acaso hubo desincronización)
                    if self.df_inventario.loc[sku, 'Stock_Comprometido'] < 0:
                         self.df_inventario.loc[sku, 'Stock_Comprometido'] = 0

                    self.ventas_perdidas.append({
                        'Fecha': dia_actual,
                        'Pedido_ID': pedido['id_pedido'],
                        'Producto': sku,
                        'Cantidad_Solicitada': cantidad_solicitada,
                        'Cantidad_Atendida': cantidad_a_despachar,
                        'Cantidad_Perdida': cantidad_faltante,
                        'Motivo': 'Cliente no espera (Stockout)'
                    })
        
        # Failsafe
        self.df_inventario['Stock_Fisico'] = self.df_inventario['Stock_Fisico'].clip(lower=0)
        self.df_inventario['Stock_Comprometido'] = self.df_inventario['Stock_Comprometido'].clip(lower=0)
        
        self._calcular_campos_derivados()
        return items_despachados

    def atender_backlog(self, dia_actual):
        """
        Intenta despachar pedidos pendientes en el Backlog con el stock disponible.
        Se debe llamar al inicio del día después de recibir compras.
        """
        items_recuperados = [] # Lista de items despachados desde backlog
        
        # Ordenar backlog por FIFO puro (orden de llegada)
        # Sort in-place: Fecha asc (más antiguo primero)
        self.backlog.sort(key=lambda x: x['Fecha_Pedido'])
        
        pendientes_restantes = []
        
        for pendiente in self.backlog:
            sku = pendiente['Producto']
            cantidad_pendiente = pendiente['Cantidad_Pendiente']
            
            stock_disponible = self.df_inventario.loc[sku, 'Stock_Fisico']
            
            if stock_disponible > 0:
                cantidad_a_despachar = min(cantidad_pendiente, stock_disponible)
                
                # Despachar
                self.df_inventario.loc[sku, 'Stock_Fisico'] -= cantidad_a_despachar
                
                # Ajustar compromiso: Al atender backlog, liberamos la reserva que tenían.
                if self.df_inventario.loc[sku, 'Stock_Comprometido'] > 0:
                    self.df_inventario.loc[sku, 'Stock_Comprometido'] -= min(cantidad_a_despachar, self.df_inventario.loc[sku, 'Stock_Comprometido'])
                
                # Registrar Kardex
                self._registrar_kardex(
                    dia_actual, sku, 'VENTA_BACKLOG', -cantidad_a_despachar,
                    self.df_inventario.loc[sku, 'Stock_Fisico'],
                    id_referencia=pendiente['ID_Pedido'],
                    tipo_referencia='pedido'
                )
                
                # Agregar a items recuperados para transporte
                items_recuperados.append({
                    'id_pedido': pendiente['ID_Pedido'], # Mismo ID original
                    'cliente': pendiente['Cliente'],
                    'sku': sku,
                    'cantidad': cantidad_a_despachar,
                    'es_backlog': True
                })
                
                # Si queda saldo pendiente, se mantiene en backlog
                if cantidad_a_despachar < cantidad_pendiente:
                    pendiente['Cantidad_Pendiente'] -= cantidad_a_despachar
                    pendientes_restantes.append(pendiente)
            else:
                pendientes_restantes.append(pendiente)
                
        self.backlog = pendientes_restantes
        self._calcular_campos_derivados()
        
        return items_recuperados
    
    def verificar_reposicion(self, dia_actual, escenario="normal"):
        """
        Verifica Puntos de Reorden y genera Órdenes de Compra.
        """
        ordenes_creadas = []
        
        for sku in self.df_inventario.index:
            posicion = self.df_inventario.loc[sku, 'Posicion_Inventario']
            punto_reorden = self.df_productos.loc[sku, 'Punto_Reorden']
            
            if posicion < punto_reorden:
                q_lote = self.df_productos.loc[sku, 'Q_Lote_Optimo']
                stock_objetivo = self.df_productos.loc[sku, 'Stock_Objetivo']
                lead_time = self.df_productos.loc[sku, 'Lead_Time']
                
                if escenario == "lote_economico":
                    # Lógica específica si se requiere, por ahora usa Q_Lote_Optimo
                    pass
                
                # Lógica Inteligente:
                # Pedimos el Q_Lote_Optimo (monto fijo), PERO si el déficit es muy grande (ej. Backlog alto),
                # pedimos lo necesario para llegar al Stock Objetivo.
                # Cantidad = Max(Q_Lote, Stock_Objetivo - Posicion_Actual)
                deficit_para_objetivo = stock_objetivo - posicion
                cantidad_pedir = max(q_lote, deficit_para_objetivo)
                
                # Crear Orden de Compra (df_compras row)
                orden = {
                    'ID_Compra': f"OC-{self.contador_compras:05d}",
                    'Fecha_Creacion': dia_actual,
                    'Producto': sku,
                    'Cantidad': cantidad_pedir,
                    'Fecha_Arribo': dia_actual + lead_time,
                    'Estado': 'En Transito',
                    'Lead_Time_Aplicado': lead_time
                }
                
                self.ordenes_compra.append(orden)
                ordenes_creadas.append(orden)
                self.contador_compras += 1
                
                # Actualizar Stock En Tránsito
                self.df_inventario.loc[sku, 'Stock_En_Transito'] += cantidad_pedir
        
        self._calcular_campos_derivados()
        return ordenes_creadas
    
    def obtener_tablas_finales(self):
        """Retorna los DataFrames finales para reportes."""
        df_compras = pd.DataFrame(self.ordenes_compra)
        df_kardex = pd.DataFrame(self.kardex)
        
        # Estado actual completo
        df_estado = self.df_inventario.join(self.df_productos)
        
        return {
            'df_productos': self.df_productos,
            'df_compras': df_compras,
            'df_kardex': df_kardex,
            'df_estado_actual': df_estado
        }


# ============================================================================
# CLASE DE ESTADO DE INVENTARIO (de estado_inventario.py)
# ============================================================================

class EstadoInventario:
    """
    Clase para mantener el estado acumulativo del inventario a través de los días.
    Simula un sistema ERP real donde el estado persiste día a día.
    """
    
    def __init__(self):
        """Inicializa el estado del inventario con los valores objetivo."""
        # Stock actual por SKU
        self.stock = {sku: info["stock_objetivo"] for sku, info in dic_sku.items()}
        
        # Órdenes de compra a proveedores en tránsito
        # Estructura: [(fecha_llegada, sku, cantidad), ...]
        self.ordenes_en_transito = []
        
        # Historial de snapshots diarios
        # Estructura: {dia: {snapshots...}, ...}
        self.historial_diario = {}
        
        # Contador de órdenes de compra
        self.orden_counter = 1
        
        # Registro de quiebres de stock
        # Estructura: [(dia, sku, demanda_insatisfecha), ...]
        self.quiebres_stock = []
        
    def snapshot_diario(self, dia):
        """Captura un snapshot del estado actual del inventario."""
        return {
            "stock": self.stock.copy(),
            "ordenes_en_transito": len(self.ordenes_en_transito),
            "cantidad_en_transito": sum(orden[2] for orden in self.ordenes_en_transito)
        }
    
    def recibir_ordenes(self, dia_actual):
        """
        Procesa las órdenes de proveedor que llegan en el día actual.
        Retorna lista de recepciones.
        """
        recepciones = []
        ordenes_restantes = []
        
        for fecha_llegada, sku, cantidad in self.ordenes_en_transito:
            if fecha_llegada <= dia_actual:
                # La orden llegó
                self.stock[sku] += cantidad
                recepciones.append({
                    "sku": sku,
                    "cantidad": cantidad,
                    "fecha_llegada": fecha_llegada
                })
            else:
                # Aún en tránsito
                ordenes_restantes.append((fecha_llegada, sku, cantidad))
        
        self.ordenes_en_transito = ordenes_restantes
        return recepciones
    
    def procesar_demanda(self, pedido):
        """
        Procesa un pedido contra el stock actual.
        Retorna: (items_despachados, items_pendientes, hubo_quiebre)
        """
        despachado = []
        pendiente = []
        hubo_quiebre = False
        
        for item in pedido["items"]:
            sku = item["sku"]
            cantidad_solicitada = item["cantidad"]
            
            if sku in self.stock:
                disponible = self.stock[sku]
                
                if disponible >= cantidad_solicitada:
                    # Hay suficiente stock
                    self.stock[sku] -= cantidad_solicitada
                    despachado.append({
                        "sku": sku,
                        "cantidad": cantidad_solicitada
                    })
                else:
                    # Quiebre de stock
                    hubo_quiebre = True
                    if disponible > 0:
                        # Despacho parcial
                        self.stock[sku] = 0
                        despachado.append({
                            "sku": sku,
                            "cantidad": disponible
                        })
                        pendiente.append({
                            "sku": sku,
                            "cantidad": cantidad_solicitada - disponible
                        })
                    else:
                        # No hay nada
                        pendiente.append({
                            "sku": sku,
                            "cantidad": cantidad_solicitada
                        })
        
        return despachado, pendiente, hubo_quiebre
    
    def crear_orden_proveedor(self, dia_actual, sku, cantidad, motivo="REPOSICION"):
        """
        Crea una orden de compra al proveedor.
        La orden llegará después de lead_time días.
        """
        info_sku = dic_sku[sku]
        lead_time = info_sku["lead_time_dias"]
        fecha_llegada = dia_actual + lead_time
        
        self.ordenes_en_transito.append((fecha_llegada, sku, cantidad))
        
        orden_id = f"OC-{self.orden_counter:04d}"
        self.orden_counter += 1
        
        return {
            "orden_id": orden_id,
            "sku": sku,
            "cantidad": cantidad,
            "dia_orden": dia_actual,
            "dia_llegada_estimado": fecha_llegada,
            "lead_time": lead_time,
            "motivo": motivo
        }
    
    def verificar_reposicion(self, dia_actual, demanda_dia_por_sku, escenario="normal"):
        """
        Verifica si es necesario reponer stock y crea órdenes al proveedor.
        Retorna lista de órdenes creadas.
        """
        ordenes_creadas = []
        
        for sku, info in dic_sku.items():
            stock_actual = self.stock.get(sku, 0)
            stock_objetivo = info["stock_objetivo"]
            stock_minimo = info["stock_minimo"]
            demanda_hoy = demanda_dia_por_sku.get(sku, 0)
            
            # Aplicar lógica según escenario
            if escenario == "lote_economico":
                # Solo reponer en lotes de 50 unidades
                if stock_actual < stock_minimo:
                    # Calcular cuántos lotes de 50 se necesitan
                    deficit = stock_objetivo - stock_actual
                    lotes_necesarios = (deficit + 49) // 50  # Redondeo hacia arriba
                    cantidad_reponer = lotes_necesarios * 50
                    
                    orden = self.crear_orden_proveedor(
                        dia_actual, sku, cantidad_reponer, 
                        motivo="LOTE_ECONOMICO"
                    )
                    ordenes_creadas.append(orden)
                    
            else:
                # Lógica normal de reposición
                # Verificar si hubo quiebre (demanda > stock inicial del día)
                if demanda_hoy > stock_actual or stock_actual < stock_minimo:
                    cantidad_reponer = stock_objetivo - stock_actual
                    
                    if cantidad_reponer > 0:
                        orden = self.crear_orden_proveedor(
                            dia_actual, sku, cantidad_reponer,
                            motivo="QUIEBRE_STOCK" if demanda_hoy > stock_actual else "BAJO_MINIMO"
                        )
                        ordenes_creadas.append(orden)
        
        return ordenes_creadas
    
    def registrar_quiebre(self, dia, sku, demanda_insatisfecha):
        """Registra un evento de quiebre de stock."""
        self.quiebres_stock.append({
            "dia": dia,
            "sku": sku,
            "demanda_insatisfecha": demanda_insatisfecha
        })
    
    def obtener_costo_inventario(self):
        """Calcula el costo total del inventario actual."""
        costo_total = 0
        for sku, cantidad in self.stock.items():
            info = dic_sku[sku]
            costo_total += cantidad * info["costo_unitario"]
        return costo_total
    
    def obtener_nivel_servicio(self):
        """Calcula el nivel de servicio (% de días sin quiebre)."""
        if not self.historial_diario:
            return 100.0
        
        dias_con_quiebre = len(set(q["dia"] for q in self.quiebres_stock))
        total_dias = len(self.historial_diario)
        
        if total_dias == 0:
            return 100.0
        
        return ((total_dias - dias_con_quiebre) / total_dias) * 100
