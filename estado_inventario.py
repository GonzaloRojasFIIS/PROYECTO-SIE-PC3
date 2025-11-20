"""
Módulo de Estado de Inventario
Mantiene el estado acumulativo del inventario y órdenes de proveedor en tránsito.
"""
from catalogos import dic_sku
from datetime import datetime, timedelta

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
