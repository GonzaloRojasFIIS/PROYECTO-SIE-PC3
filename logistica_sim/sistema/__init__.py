"""
Paquete Sistema - logistica_sim.sistema
Sistema de simulación logística con módulos de inventario, transporte, y reportes.
"""

# Exponer clases principales para facilitar los imports
from .inventario import GestionInventario, EstadoInventario, reservar_y_actualizar, reponer_por_demanda
from .transporte import GestionTransporte, planificar_rutas
from .reporte import generar_pdf, reporte_logistica, PDFReport

# Exponer módulos completos para acceso directo
from . import catalogos
from . import demanda
from . import picking
from . import indicadores
from . import alertas

__all__ = [
    # Clases de Inventario
    'GestionInventario',
    'EstadoInventario',
    'reservar_y_actualizar',
    'reponer_por_demanda',
    
    # Clases de Transporte
    'GestionTransporte',
    'planificar_rutas',
    
    # Funciones de Reporte
    'generar_pdf',
    'reporte_logistica',
    'PDFReport',
    
    # Módulos
    'catalogos',
    'demanda',
    'picking',
    'indicadores',
    'alertas',
]
