"""
Módulo de Gestión de Inventario
Sistema completo de inventario con DataFrame para simulación ERP Supply Chain
"""
import pandas as pd
import numpy as np
from catalogos import dic_sku

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
        
    def _registrar_kardex(self, dia, sku, tipo_movimiento, cantidad, saldo_final):
        """Registra un movimiento en el Kardex."""
        self.kardex.append({
            'Fecha': dia,
            'Producto': sku,
            'Tipo_Movimiento': tipo_movimiento,
            'Cantidad': cantidad,
            'Saldo_Final': saldo_final
        })

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
                    self.df_inventario.loc[sku, 'Stock_Fisico']
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
        from catalogos import dic_clientes # Importar aquí para acceder a probabilidad
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
                    self.df_inventario.loc[sku, 'Stock_Fisico']
                )
            
            # Manejo de Faltantes: Backlog o Venta Perdida
            if cantidad_a_despachar < cantidad_solicitada:
                cantidad_faltante = cantidad_solicitada - cantidad_a_despachar
                
                # Decisión del Cliente: ¿Espera o se va?
                decision_espera = random.random() < prob_espera
                
                if decision_espera:
                    # BACKLOG: El cliente espera
                    # Mantenemos el compromiso de stock si existía (o lo creamos si no, pero aquí ya debería estar comprometido en teoría)
                    # En este modelo simple, el compromiso se libera al despachar. Si queda pendiente, 
                    # deberíamos mantener el compromiso lógico para que no se venda a otro.
                    # Ajuste: Si espera, nos aseguramos que el stock futuro se reserve.
                    
                    # Si ya había compromiso y no se despachó, se mantiene solo.
                    # Si no había (ej. venta directa sin reserva previa), se debería crear.
                    # Asumimos que 'comprometer_stock' ya corrió antes.
                    
                    # IMPORTANTE: Asegurar que el Stock Comprometido refleje este pendiente
                    # Como comprometer_stock solo comprometió lo disponible, la parte faltante NO está en Stock_Comprometido.
                    # Al moverlo a Backlog, debemos "comprometer" ese stock futuro (Backorder).
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
                    # Si no despachamos nada o parcial, y el cliente se va, liberamos el compromiso restante.
                    # El compromiso actual en el DF sigue teniendo la parte no despachada.
                    
                    # Liberamos lo que falta porque el cliente canceló.
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
            # Nota: Para backlog usamos Stock Físico. El Comprometido ya debería incluir estos pendientes si se gestionó bien,
            # pero para simplificar, asumimos que el backlog tiene prioridad absoluta sobre nuevos pedidos del día.
            
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
                    self.df_inventario.loc[sku, 'Stock_Fisico']
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
