# 🚛 Sistema de Simulación Logística ERP - LIA S.A.C.

Sistema avanzado de simulación de Supply Chain con estructura de datos profesional, gestión de inventario con prevención de stock negativo, y módulo de transporte basado en capacidad de peso.

## 📋 Descripción General

Este sistema simula operaciones logísticas completas incluyendo:

- **Gestión de Inventario**: Con control de stock físico, comprometido, en tránsito y Kardex completo
- **Gestión de Pedidos**: Procesamiento de demanda con tracking de ventas perdidas (backlog)
- **Gestión de Compras**: Reposición automática basada en puntos de reorden
- **Gestión de Transporte**: Asignación de vehículos por capacidad de peso con optimización
- **KPIs en Tiempo Real**: OTIF, Fill Rate, Backlog Rate, Utilización de Flota
- **Alertas Automáticas**: Notificaciones de stock bajo y problemas operacionales
- **Reportes PDF**: Generación automática de reportes ejecutivos

## 🎯 Características Principales

### ✅ Inventario Realista
- **Stock nunca negativo**: El sistema previene stock físico negativo
- **Tracking de backlog**: Registra todas las ventas perdidas por falta de stock
- **Kardex completo**: Registro detallado de todos los movimientos de inventario

### 🚚 Transporte Inteligente
- **Flota heterogénea**: Vehículos de diferentes capacidades (1Ton, 5Ton, 10Ton)
- **Optimización por peso**: Asignación basada en peso real de productos
- **Métricas de utilización**: % de ocupación por vehículo y viaje

### 📊 Análisis Avanzado
- **Múltiples escenarios**: Normal, Proveedor Lento, Demanda Estacional, Lote Económico
- **Visualizaciones interactivas**: Gráficos de evolución de stock, costos, utilización
- **Reportes diarios**: Vista detallada día por día con KPIs y estado de inventario

## 🛠️ Requisitos del Sistema

### Software Requerido
- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Librerías Python
```bash
streamlit
pandas
numpy
altair
fpdf
```

## 📦 Instalación

### Paso 1: Verificar Python
```bash
python --version
```
Debe mostrar Python 3.8 o superior.

### Paso 2: Clonar o Descargar el Proyecto
Si tienes el proyecto en tu escritorio, ve a la carpeta:
```bash
cd "C:\Users\Gonzalo\Desktop\PROYECTO SIE PC3"
```

### Paso 3: Instalar Dependencias
```bash
pip install streamlit pandas numpy altair fpdf
```

## 🚀 Ejecución del Sistema

### Método 1: Interfaz Web (Recomendado)

1. **Abrir terminal** en la carpeta del proyecto

2. **Ejecutar Streamlit**:
```bash
streamlit run app.py
```

3. **Abrir navegador**: El sistema abrirá automáticamente en `http://localhost:8501`

4. **Configurar simulación**:
   - Seleccionar escenario (Normal, Proveedor Lento, etc.)
   - Definir días a simular (7-60 días)
   - Ajustar capacidad de picking

5. **Ejecutar**: Hacer clic en "▶️ Ejecutar Simulación"
├── logistica_sim/                # Paquete principal
│   ├── simulador.ipynb          # Notebook demostrativo Jupyter
│   ├── README.md                # Documentación del paquete
│   └── sistema/                 # Módulos del sistema
│       ├── __init__.py          # Exports del paquete
│       ├── catalogos.py         # Datos maestros (productos, clientes)
│       ├── demanda.py           # Generación de demanda/pedidos
│       ├── inventario.py        # Gestión de inventario, Kardex y backlog
│       ├── picking.py           # Asignación de picking
│       ├── transporte.py        # Gestión de flota y despachos
│       ├── indicadores.py       # Cálculo de KPIs
│       ├── alertas.py           # Sistema de alertas
│       └── reporte.py           # Generación de reportes y PDF
│
├── tests/                        # Archivos de testing
│   ├── test_stock_logic.py
│   ├── test_compras_kardex.py
│   └── verify_*.py
│
├── app.py                        # Interfaz web Streamlit
├── main.py                       # Motor principal de simulación
└── README.md                     # Esta documentación
```

### Importación de Módulos

Para usar el sistema programáticamente:

```python
# Importar clases principales
from logistica_sim.sistema import GestionInventario, GestionTransporte
from logistica_sim.sistema.demanda import generar_demanda_diaria
from logistica_sim.sistema import catalogos, indicadores, alertas
```


## 🎮 Uso de la Interfaz Web

### Tablero de Control
Muestra KPIs globales:
- Total de Pedidos procesados
- Fill Rate (% de unidades entregadas)
- OTIF (% de pedidos perfectos)
- Valor del inventario final

### Pestañas Principales

1. **📦 Productos (Maestro)**
   - Catálogo de productos con costos, precios, pesos
   - Parámetros de reposición (Stock Seguridad, Punto Reorden, Lote Óptimo)

2. **🛒 Pedidos (Ventas)**
   - Registro completo de pedidos
   - Tabla de ventas perdidas (backlog) si aplica

3. **🚚 Compras (Reposición)**
   - Órdenes de compra generadas automáticamente
   - Fechas de emisión y arribo

4. **🚛 Transporte (Flota)**
   - Estado de la flota de vehículos
   - Despachos realizados con % de ocupación y costos

5. **📜 Kardex (Movimientos)**
   - Historia completa de movimientos de inventario
   - Saldos finales por operación

6. **📈 Análisis Gráfico**
   - Evolución de stock por producto
   - Valor del inventario en el tiempo

7. **📊 Reporte Diario**
   - Selector de día
   - KPIs del día seleccionado
   - Estado del inventario al cierre
   - Alertas específicas del día

## 🔧 Configuración de Escenarios

### Normal
Configuración estándar:
- Lead time: 3-7 días según producto
- Demanda: Aleatoria con distribución normal
- Capacidad picking: 1500 u/día

### Proveedor Lento
Simula problemas de suministro:
- Lead time: 10 días para todos los productos
- Mayor probabilidad de stockouts

### Demanda Estacional
Picos de demanda en días específicos:
- Días 15-20: Demanda aumentada +50%
- Probar capacidad del sistema en alta demanda

### Lote Económico
Usa lotes económicos de compra (EOQ):
- Optimización de costos de pedido vs almacenamiento

## 📊 KPIs Calculados

### OTIF (On-Time In-Full)
Porcentaje de pedidos entregados **completos** (100% de unidades):
```
OTIF = (Pedidos Perfectos / Total Pedidos) × 100
```

### Fill Rate
Porcentaje de unidades entregadas del total solicitado:
```
Fill Rate = (Unidades Entregadas / Unidades Solicitadas) × 100
```

### Backlog Rate
Porcentaje de unidades perdidas (no entregadas):
```
Backlog Rate = (Unidades Perdidas / Unidades Solicitadas) × 100
```

### Utilización de Flota
Promedio de ocupación de los vehículos utilizados:
```
Utilización = Promedio(% Ocupación de cada Despacho)
```

## 📄 Generación de Reportes PDF

1. Ejecutar la simulación completa
2. Scroll hasta la sección "📄 Exportar Resultados"
3. Click en "Generar Reporte PDF"
4. Click en "⬇️ Descargar Reporte PDF"

El PDF incluye:
- Configuración de la simulación
- KPIs consolidados
- Resumen de alertas por día
- Estado final del inventario

## 🐛 Solución de Problemas

### Error: "Module not found"
```bash
pip install <nombre_del_modulo>
```

### Error: "Port 8501 is already in use"
Cerrar la instancia anterior de Streamlit o usar otro puerto:
```bash
streamlit run app.py --server.port 8502
```

### Stock llega a 0 muy rápido
Ajustar parámetros en `catalogos.py`:
- Aumentar `stock_objetivo`
- Aumentar `stock_minimo`
- Reducir `lead_time_dias`

### PDF no se genera
Verificar instalación de fpdf:
```bash
pip install fpdf
```

## 📈 Recomendaciones de Uso

### Para Pruebas Rápidas
- Simular 7-10 días
- Usar escenario "Normal"
- Capacidad picking: 1500

### Para Análisis Completo
- Simular 30-60 días
- Probar diferentes escenarios
- Comparar KPIs entre escenarios
- Generar reportes PDF para cada escenario

### Para Stress Testing
- Usar escenario "Demanda Estacional"
- Reducir capacidad de picking a 1000
- Simular 30 días
- Analizar ventas perdidas y utilización de flota

## 👥 Soporte Técnico

Para reportar problemas o sugerencias:
- Revisar los logs en la terminal donde corre Streamlit
- Verificar que todos los archivos `.py` estén presentes
- Asegurar que las dependencias estén instaladas

## 📝 Notas Importantes

- **Stock Físico**: Nunca puede ser negativo (garantizado por el sistema)
- **Ventas Perdidas**: Se registran automáticamente cuando no hay stock
- **Transporte**: Solo se despacha lo que hay en stock físico
- **Reposición**: Automática cuando se alcanza el punto de reorden

---

**Desarrollado para**: LIA S.A.C.  
**Versión**: 2.0  
**Última actualización**: 2025-11-21

