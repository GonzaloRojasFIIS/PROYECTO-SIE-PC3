# Logística Sim - Sistema de Simulación Logística

Paquete de simulación logística para análisis de operaciones de Supply Chain.

## Estructura del Paquete

```
logistica_sim/
├─ simulador.ipynb          # Notebook demostrativo
└─ sistema/                 # Paquete principal
   ├─ __init__.py          # Exporta clases y funciones principales
   ├─ catalogos.py         # Datos maestros (productos, clientes, zonas)
   ├─ demanda.py           # Generación de demanda diaria
   ├─ inventario.py        # Sistema de gestión de inventario
   ├─ picking.py           # Asignación de picking
   ├─ transporte.py        # Gestión de flota y despachos
   ├─ indicadores.py       # Cálculo de KPIs
   ├─ alertas.py           # Generación de alertas
   └─ reporte.py           # Generación de reportes
```

## Uso

### Importar el paquete

```python
from logistica_sim.sistema import GestionInventario, GestionTransporte
from logistica_sim.sistema.demanda import generar_demanda_diaria
from logistica_sim.sistema import catalogos
```

### Ejecutar simulación completa

```python
import main

resultados = main.run_simulation(
    n_dias=15, 
    capacidad_picking=1500, 
    escenario="normal"
)
```

### Ejecutar aplicación Streamlit

```bash
streamlit run app.py
```

## Módulos Principales

### `inventario.py`
Consolidación de gestión de inventario:
- `GestionInventario`: Sistema ERP con DataFrame, Kardex y backlog
- `EstadoInventario`: Estado acumulativo del inventario
- Funciones: `reservar_y_actualizar`, `reponer_por_demanda`

### `transporte.py`
Consolidación de gestión de transporte:
- `GestionTransporte`: Administración de flota y despachos
- Función: `planificar_rutas`

### `reporte.py`
Consolidación de reportes:
- `generar_pdf`: Genera reporte PDF con análisis dinámico
- `reporte_logistica`: Imprime reporte de consola
- `PDFReport`: Clase FPDF personalizada

## Tests

Los archivos de test se encuentran en la carpeta `tests/`:
```
tests/
├─ test_stock_logic.py
├─ test_compras_kardex.py
├─ verify_corrections.py
└─ ...
```

## Escenarios Disponibles

- **normal**: Operación estándar
- **proveedor_lento**: Lead time aumentado (10 días)
- **demanda_estacional**: Pico de demanda en días 15-20
- **lote_economico**: Reposición por lotes EOQ

## KPIs Calculados

- **OTIF** (On Time In Full): Pedidos perfectos entregados a tiempo
- **Fill Rate**: Porcentaje de unidades entregadas vs solicitadas
- **Backlog Rate**: Porcentaje de pedidos pendientes
- **Utilización de Flota**: Ocupación promedio de vehículos

## Notebook Demostrativo

Ver `simulador.ipynb` para ejemplos de uso del paquete.
