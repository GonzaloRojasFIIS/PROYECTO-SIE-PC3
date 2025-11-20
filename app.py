import streamlit as st
import pandas as pd
import main
import catalogos
import altair as alt

st.set_page_config(page_title="Simulación Logística ERP", layout="wide")

st.title("🚛 Sistema de Simulación Logística ERP")
st.markdown("Simulación avanzada de Supply Chain con estructura de datos profesional.")

# Sidebar - Configuración
st.sidebar.header("⚙️ Configuración")

escenario = st.sidebar.selectbox(
    "📋 Escenario",
    ["normal", "proveedor_lento", "demanda_estacional", "lote_economico"],
    format_func=lambda x: {
        "normal": "Normal - Estándar",
        "proveedor_lento": "Proveedor Lento (Lead Time 10 días)",
        "demanda_estacional": "Demanda Estacional (Pico días 15-20)",
        "lote_economico": "Lote Económico (EOQ)"
    }[x]
)

n_dias = st.sidebar.number_input("Días a simular", min_value=7, max_value=60, value=15)
capacidad_picking = st.sidebar.number_input("Capacidad Picking (u/día)", value=1500)

if st.sidebar.button("▶️ Ejecutar Simulación"):
    with st.spinner("Procesando simulación..."):
        resultados = main.run_simulation(n_dias, capacidad_picking, escenario)
        st.session_state['resultados'] = resultados
        st.success("¡Simulación completada con éxito!")

if 'resultados' in st.session_state:
    res = st.session_state['resultados']
    
    # Extraer DataFrames
    df_productos = res['df_productos']
    df_pedidos = res['df_pedidos']
    df_compras = res['df_compras']
    df_kardex = res['df_kardex']
    
    # --- KPIs Globales ---
    st.header("📊 Tablero de Control")
    
    # Calcular KPIs desde df_pedidos
    total_pedidos = len(df_pedidos['ID_Pedido'].unique())
    total_unidades = df_pedidos['Cant_Solicitada'].sum()
    fill_rate = (df_pedidos['Cant_Entregada'].sum() / total_unidades) * 100 if total_unidades > 0 else 0
    
    # OTIF (Aproximado: Entregado completo el mismo día)
    pedidos_agrupados = df_pedidos.groupby('ID_Pedido').agg({
        'Cant_Solicitada': 'sum',
        'Cant_Entregada': 'sum'
    })
    pedidos_perfectos = pedidos_agrupados[pedidos_agrupados['Cant_Solicitada'] == pedidos_agrupados['Cant_Entregada']]
    otif = (len(pedidos_perfectos) / total_pedidos) * 100 if total_pedidos > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Pedidos", total_pedidos)
    col2.metric("Fill Rate (Volumen)", f"{fill_rate:.1f}%")
    col3.metric("OTIF (Pedidos)", f"{otif:.1f}%")
    col4.metric("Valor Inventario Final", f"S/ {res['metricas_globales']['valor_total_inventario']:,.2f}")

    # --- Pestañas de Datos ---
    st.markdown("---")
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📦 Productos (Maestro)", 
        "🛒 Pedidos (Ventas)", 
        "🚚 Compras (Reposición)", 
        "🚛 Transporte (Flota)",
        "📜 Kardex (Movimientos)",
        "📈 Análisis Gráfico",
        "📊 Reporte Diario"
    ])
    
    with tab1:
        st.subheader("Maestro de Productos")
        st.dataframe(df_productos.style.format({
            'Costo_Unitario': 'S/ {:.2f}', 
            'Precio_Venta': 'S/ {:.2f}',
            'Peso_Unitario_kg': '{:.2f} kg'
        }), use_container_width=True)
        
    with tab2:
        st.subheader("Registro de Pedidos (Ventas)")
        st.dataframe(df_pedidos, use_container_width=True)
        
        if 'ventas_perdidas' in res and not res['ventas_perdidas'].empty:
            st.error("⚠️ Registro de Ventas Perdidas (Backlog)")
            st.dataframe(res['ventas_perdidas'], use_container_width=True)
        
    with tab3:
        st.subheader("Gestión de Compras (Reposición)")
        if not df_compras.empty:
            st.dataframe(df_compras, use_container_width=True)
        else:
            st.info("No se generaron órdenes de compra en este periodo.")
            
    with tab4:
        st.subheader("Gestión de Transporte")
        col_t1, col_t2 = st.columns(2)
        
        with col_t1:
            st.markdown("### 🚛 Flota Disponible")
            st.dataframe(res['df_flota'], use_container_width=True)
            
        with col_t2:
            st.markdown("### 📦 Despachos Realizados")
            if not res['df_despachos'].empty:
                st.dataframe(res['df_despachos'].style.format({
                    'Peso_Total_Carga_kg': '{:.2f} kg',
                    'Porcentaje_Ocupacion': '{:.1f}%',
                    'Costo_Viaje': 'S/ {:.2f}'
                }), use_container_width=True)
            else:
                st.info("No se han generado despachos.")
        
    with tab5:
        st.subheader("Kardex de Inventario")
        st.dataframe(df_kardex, use_container_width=True)
        
    with tab6:
        st.subheader("Evolución de Inventario")
        
        if not df_kardex.empty:
            # Crear un rango de días completo
            dias = range(1, n_dias + 1)
            skus = df_productos.index.unique()
            
            data_evolucion = []
            
            for sku in skus:
                movs = df_kardex[df_kardex['Producto'] == sku].sort_values('Fecha')
                
                # Obtener saldo final de cada día
                for d in dias:
                    movs_dia = movs[movs['Fecha'] <= d]
                    if not movs_dia.empty:
                        saldo = movs_dia.iloc[-1]['Saldo_Final']
                    else:
                        # Si no hay movimientos previos, asumimos el stock inicial (Q_Lote * 2 según inicialización)
                        # O mejor, buscamos el valor inicial en df_productos si pudiéramos, pero aquí usaremos una lógica segura
                        saldo = df_productos.loc[sku, 'Q_Lote_Optimo'] * 2
                    
                    data_evolucion.append({
                        'Dia': d,
                        'Producto': sku,
                        'Stock': saldo
                    })
            
            df_grafico = pd.DataFrame(data_evolucion)
            
            # Gráfico de Stock (Restaurado)
            chart_stock = alt.Chart(df_grafico).mark_line(point=True).encode(
                x=alt.X('Dia:O', title='Día'),
                y='Stock:Q',
                color='Producto:N',
                tooltip=['Dia', 'Producto', 'Stock']
            ).properties(title="Niveles de Stock por Producto").interactive()
            
            st.altair_chart(chart_stock, use_container_width=True)
            
        else:
            st.info("No hay movimientos en el Kardex para graficar el stock.")

        # Nueva Gráfica Complementaria: Evolución del Fill Rate (Nivel de Servicio)
        st.markdown("### 📈 Evolución del Nivel de Servicio (Fill Rate)")
        
        data_fill_rate = []
        for dia_data in res['resultados_diarios']:
            data_fill_rate.append({
                'Dia': dia_data['dia'],
                'Fill_Rate': dia_data['kpis'].get('fill_rate', 0)
            })
            
        df_fill = pd.DataFrame(data_fill_rate)
        
        if not df_fill.empty:
            chart_fill = alt.Chart(df_fill).mark_area(
                line={'color':'#2196F3'},
                color=alt.Gradient(
                    gradient='linear',
                    stops=[alt.GradientStop(color='white', offset=0),
                           alt.GradientStop(color='#2196F3', offset=1)],
                    x1=1, x2=1, y1=1, y2=0
                )
            ).encode(
                x=alt.X('Dia:O', title='Día'),
                y=alt.Y('Fill_Rate:Q', title='Fill Rate (%)', scale=alt.Scale(domain=[0, 100])),
                tooltip=[alt.Tooltip('Dia', title='Día'), alt.Tooltip('Fill_Rate:Q', format='.1f')]
            ).properties(title="Fill Rate Diario (%)").interactive()
            
            st.altair_chart(chart_fill, use_container_width=True)

        # Gráfico de Ventas Perdidas / No Atendidas
        st.markdown("### 📉 Unidades No Atendidas (Quiebres de Stock)")
        
        if 'ventas_perdidas' in res and not res['ventas_perdidas'].empty:
            df_perdidas = res['ventas_perdidas']
            # Agrupar por día
            df_perdidas_dia = df_perdidas.groupby('Fecha')['Cantidad_Perdida'].sum().reset_index()
            df_perdidas_dia.rename(columns={'Fecha': 'Dia'}, inplace=True)
            
            chart_perdidas = alt.Chart(df_perdidas_dia).mark_bar(color='#ef5350').encode(
                x=alt.X('Dia:O', title='Día'),
                y=alt.Y('Cantidad_Perdida:Q', title='Unidades Perdidas'),
                tooltip=[alt.Tooltip('Dia', title='Día'), alt.Tooltip('Cantidad_Perdida:Q', title='Cant. Perdida')]
            ).properties(title="Total Unidades No Despachadas por Día").interactive()
            
            st.altair_chart(chart_perdidas, use_container_width=True)
        else:
            st.success("✅ ¡Excelente! No hubo ventas perdidas en este periodo.")

    with tab7:
        st.subheader("📊 Reporte Diario Detallado")
        
        # Usar n_dias de la configuración guardada para consistencia
        n_dias_sim = res['config']['n_dias']
        dia_seleccionado = st.slider("Seleccionar Día", 1, n_dias_sim, 1, key="slider_dia_reporte")
        
        # Obtener datos del día
        datos_dia = res['resultados_diarios'][dia_seleccionado - 1]
        kpis_dia = datos_dia['kpis']
        estado_inv_dia = datos_dia['estado_inventario']
        
        # Métricas del Día
        col_d1, col_d2, col_d3, col_d4 = st.columns(4)
        col_d1.metric("Pedidos Día", kpis_dia['total_pedidos'])
        col_d2.metric("OTIF Día", f"{kpis_dia['otif']}%")
        col_d3.metric("Fill Rate Día", f"{kpis_dia.get('fill_rate', 0)}%")
        col_d4.metric("Backlog Rate", f"{kpis_dia.get('backlog_rate', 0)}%")
        
        st.markdown("### 📦 Estado del Inventario (Cierre del Día)")
        
        # Enriquecer tabla con datos maestros
        df_view = estado_inv_dia.join(df_productos[['Nombre_Producto', 'Stock_Seguridad', 'Costo_Unitario']])
        df_view['Valor_Stock'] = df_view['Stock_Fisico'] * df_view['Costo_Unitario']
        df_view['Cobertura (Días)'] = (df_view['Stock_Fisico'] / (df_view['Stock_Seguridad'] / 3)).round(1)
        
        st.dataframe(df_view.style.format({
            'Valor_Stock': 'S/ {:.2f}',
            'Costo_Unitario': 'S/ {:.2f}',
            'Stock_Fisico': '{:.0f}',
            'Stock_Comprometido': '{:.0f}'
        }).applymap(lambda x: 'background-color: #ffcdd2' if x < 0 else '', subset=['Stock_Fisico']), use_container_width=True)
        
        # Alertas del día
        if datos_dia['alertas']:
            for a in datos_dia['alertas']:
                if isinstance(a, dict):
                    st.error(f"⚠️ {a['Mensaje']}")
                else:
                    st.error(f"⚠️ {a}")
        else:
            st.success("✅ Sin alertas este día.")


    # Recomendaciones
    st.subheader("Recomendaciones")
    
    kpis_consolidados = pd.DataFrame([d['kpis'] for d in res['resultados_diarios']])
    otif_promedio = kpis_consolidados['otif'].mean()
    utilizacion_promedio = kpis_consolidados['utilizacion_flota'].mean()
    backlog_promedio = kpis_consolidados['backlog_rate'].mean()
    
    if otif_promedio < 95:
        st.info("📌 Verificar tiempos de preparación y capacidad de picking.")
    if utilizacion_promedio > 85:
        st.info("📌 Considerar ampliar la flota o renegociar horarios de entrega.")
    if backlog_promedio > 5:
        st.info("📌 Incrementar personal de picking los días de alta demanda.")
    if utilizacion_promedio < 50:
        st.info("📌 Optimizar rutas para consolidar carga.")
    
    hay_alertas_global = any(d['alertas'] for d in res['resultados_diarios'])
    if not hay_alertas_global and otif_promedio >= 95:
        st.success("📌 Operación estable. Mantener monitoreo.")

    # --- Descarga de Reporte PDF ---
    st.markdown("---")
    st.subheader("📄 Exportar Resultados")
    
    try:
        import generador_pdf
        
        if st.button("Generar Reporte PDF"):
            with st.spinner("Generando PDF..."):
                pdf_bytes = generador_pdf.generar_pdf(res)
                
                st.download_button(
                    label="⬇️ Descargar Reporte PDF",
                    data=pdf_bytes,
                    file_name="reporte_logistica_erp.pdf",
                    mime="application/pdf"
                )
    except ImportError:
        st.error("La librería 'fpdf' no está instalada. Por favor instálela para generar reportes (pip install fpdf).")
    except Exception as e:
        st.error(f"Error al generar el PDF: {e}")

else:
    st.info("👈 Configure los parámetros y ejecute la simulación.")
