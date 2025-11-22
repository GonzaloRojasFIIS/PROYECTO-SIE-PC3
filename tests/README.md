# Guía de Tests - Sistema Logística

Esta guía explica cómo ejecutar los tests del sistema y qué valida cada uno.

## Prerequisito: Activar el Entorno Virtual

```powershell
.venv\Scripts\Activate.ps1
```

## Tests Disponibles

### 1. test_stock_logic.py
**Qué valida:** Lógica de stock comprometido y prevención de stock negativo

**Ejecutar:**
```powershell
.venv\Scripts\python.exe tests\test_stock_logic.py
```

**Valida:**
- Stock nunca es negativo
- Stock comprometido se gestiona correctamente
- Despachos parciales en caso de quiebre
- Registro de backlog/ventas perdidas

---

### 2. test_modules.py
**Qué valida:** Importación correcta de todos los módulos del sistema

**Ejecutar:**
```powershell
.venv\Scripts\python.exe tests\test_modules.py
```

**Valida:**
- Todos los módulos se importan sin error
- Clases principales se pueden instanciar
- Funciones básicas funcionan correctamente

**Resultado esperado:**
```
✓ catalogos imported
✓ demanda imported
✓ inventario imported
✓ picking imported
✓ transporte imported
✓ indicadores imported
✓ alertas imported
✅ ALL MODULE TESTS PASSED
```

---

### 3. test_compras_kardex.py
**Qué valida:** Sistema de compras automáticas y registro en Kardex

**Ejecutar:**
```powershell
.venv\Scripts\python.exe tests\test_compras_kardex.py
```

**Valida:**
- Órdenes de compra se generan automáticamente
- Recepciones ocurren después del lead time
- Movimientos se registran correctamente en Kardex

**Resultado esperado:**
```
Total de órdenes de compra generadas: 12
Órdenes recibidas: 7

Movimientos de COMPRA_RECEPCION en kardex:
Total de recepciones registradas: 7
```

---

### 4. verify_changes.py
**Qué valida:** Integridad general del sistema completo

**Ejecutar:**
```powershell
.venv\Scripts\python.exe tests\verify_changes.py
```

**Valida:**
- Stock físico nunca negativo
- Backlog/ventas perdidas se registran
- Despachos respetan capacidad de vehículos
- KPIs se calculan en rangos válidos (0-100%)

**Resultado esperado:**
```
--- Test 1: Stock Non-Negative ---
✅ PASS: Stock Físico is non-negative.

--- Test 2: Backlog/Lost Sales Recording ---
✅ PASS: System records stockout situations.

--- Test 3: Transport Capacity ---
✅ PASS: All dispatches within vehicle capacity.

--- Test 4: KPIs Calculation ---
✅ PASS: KPIs in valid range.
```

---

### 5. debug_chart_data.py
**Qué valida:** Generación correcta de datos para gráficos

**Ejecutar:**
```powershell
.venv\Scripts\python.exe tests\debug_chart_data.py
```

**Valida:**
- Estructura de DataFrames es correcta
- Valores de inventario se calculan bien día a día
- Datos están listos para visualización

---

## Ejecutar Todos los Tests

Para ejecutar todos los tests en secuencia:

```powershell
.venv\Scripts\python.exe tests\test_modules.py
.venv\Scripts\python.exe tests\test_stock_logic.py
.venv\Scripts\python.exe tests\test_compras_kardex.py
.venv\Scripts\python.exe tests\verify_changes.py
.venv\Scripts\python.exe tests\debug_chart_data.py
```

## Tests en Jupyter Notebook

Los tests más importantes también están documentados en:
```
logistica_sim/simulador.ipynb
```

Este notebook incluye:
- Test 1: Lógica de Stock Comprometido
- Test 2: Sistema de Compras y Kardex
- Test 3: KPIs y Métricas del Sistema

Con explicaciones detalladas y resultados esperados.

---

## Solución de Problemas

### Error: "No module named 'pandas'"
Instalar dependencias:
```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Error: "No module named 'logistica_sim'"
Asegurarse de estar ejecutando desde la raíz del proyecto (PROYECTO SIE PC3)

---

**Última actualización:** 2025-11-21
