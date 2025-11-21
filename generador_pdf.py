from fpdf import FPDF
import pandas as pd
import tempfile

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Reporte de Simulacion Logistica ERP', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 10, title, 0, 1, 'L', 1)
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 10, body)
        self.ln()

    def add_kpi_table(self, kpis):
        self.set_font('Arial', 'B', 10)
        self.cell(90, 10, 'Indicador', 1)
        self.cell(90, 10, 'Valor', 1)
        self.ln()
        self.set_font('Arial', '', 10)
        for key, value in kpis.items():
            self.cell(90, 10, key, 1)
            self.cell(90, 10, str(value), 1)
            self.ln()
        self.ln()

def generar_pdf(resultados):
    pdf = PDFReport()
    pdf.add_page()
    
    # 1. Configuración
    pdf.chapter_title("1. Configuracion de la Simulacion")
    config_text = (
        f"Escenario: {resultados['config']['escenario']}\n"
        f"Dias Simulados: {resultados['config']['n_dias']}\n"
    )
    pdf.chapter_body(config_text)
    
    # 2. Métricas Globales
    pdf.chapter_title("2. Indicadores Clave de Desempeno (KPIs)")
    
    # Calcular KPIs globales (mismo método que Tablero de Control)
    df_pedidos = resultados['df_pedidos']
    
    # OTIF y Fill Rate globales
    total_pedidos = len(df_pedidos['ID_Pedido'].unique())
    total_unidades = df_pedidos['Cant_Solicitada'].sum()
    fill_rate_global = (df_pedidos['Cant_Entregada'].sum() / total_unidades * 100) if total_unidades > 0 else 0
    
    pedidos_agrupados = df_pedidos.groupby('ID_Pedido').agg({
        'Cant_Solicitada': 'sum',
        'Cant_Entregada': 'sum'
    })
    pedidos_perfectos = pedidos_agrupados[pedidos_agrupados['Cant_Solicitada'] == pedidos_agrupados['Cant_Entregada']]
    otif_global = (len(pedidos_perfectos) / total_pedidos * 100) if total_pedidos > 0 else 0
    
    # Backlog y Utilización Flota (promedios diarios están bien para estos)
    kpis_diarios = pd.DataFrame([d['kpis'] for d in resultados['resultados_diarios']]).fillna(0)
    
    metricas = {
        "OTIF (Pedidos Perfectos)": f"{otif_global:.1f}%",
        "Fill Rate (Volumen)": f"{fill_rate_global:.1f}%",
        "Backlog Rate Promedio": f"{kpis_diarios['backlog_rate'].mean():.1f}%",
        "Utilizacion Flota Promedio": f"{kpis_diarios['utilizacion_flota'].mean():.1f}%",
        "Valor Inventario Final": f"S/ {resultados['metricas_globales']['valor_total_inventario']:,.2f}"
    }
    pdf.add_kpi_table(metricas)
    
    # 3. Alertas
    pdf.chapter_title("3. Resumen de Alertas")
    hay_alertas = False
    for d in resultados['resultados_diarios']:
        if d['alertas']:
            hay_alertas = True
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 10, f"Dia {d['dia']}:", 0, 1)
            pdf.set_font('Arial', '', 10)
            for alerta in d['alertas']:
                pdf.cell(10) # Indent
                # Manejar alertas como dict o string
                if isinstance(alerta, dict):
                    mensaje = alerta.get('Mensaje', str(alerta))
                else:
                    mensaje = str(alerta)
                pdf.multi_cell(0, 10, f"- {mensaje}")
    
    if not hay_alertas:
        pdf.chapter_body("No se registraron alertas durante la simulacion.")
        
    # 4. Resumen de Operaciones
    pdf.chapter_title("4. Resumen de Operaciones")
    
    # Cálculos para el resumen
    total_pedidos_cnt = len(df_pedidos['ID_Pedido'].unique())
    total_solicitado = df_pedidos['Cant_Solicitada'].sum()
    total_entregado = df_pedidos['Cant_Entregada'].sum()
    
    total_perdido = 0
    if 'ventas_perdidas' in resultados and not resultados['ventas_perdidas'].empty:
        total_perdido = resultados['ventas_perdidas']['Cantidad_Perdida'].sum()
        
    backlog_total_unidades = total_solicitado - total_entregado - total_perdido
    if backlog_total_unidades < 0: backlog_total_unidades = 0
        
    porcentaje_backlog = (backlog_total_unidades / total_solicitado * 100) if total_solicitado > 0 else 0
    
    resumen_texto = (
        f"Total pedidos recibidos: {total_pedidos_cnt}\n"
        f"Total unidades solicitadas: {total_solicitado:,.0f}\n"
        f"Total unidades entregadas: {total_entregado:,.0f}\n"
        f"Backlog total: {backlog_total_unidades:,.0f} unidades ({porcentaje_backlog:.1f}%)"
    )
    pdf.chapter_body(resumen_texto)

    # 5. Recomendaciones (Dinámicas basadas en resultados)
    pdf.chapter_title("5. Recomendaciones")
    
    recomendaciones = []
    
    # Análisis de Backlog
    if porcentaje_backlog > 10:
        recomendaciones.append(f"- CRITICO: Backlog elevado ({porcentaje_backlog:.1f}%). Aumentar Stock Objetivo o reducir Lead Time de proveedores.")
    elif porcentaje_backlog > 5:
        recomendaciones.append(f"- Backlog moderado ({porcentaje_backlog:.1f}%). Revisar puntos de reorden para productos criticos.")
    
    # Análisis de Ventas Perdidas
    if total_perdido > 0:
        tasa_perdida = (total_perdido / total_solicitado * 100) if total_solicitado > 0 else 0
        if tasa_perdida > 5:
            recomendaciones.append(f"- Alta tasa de ventas perdidas ({tasa_perdida:.1f}%). Mejorar disponibilidad de stock inicial.")
        elif tasa_perdida > 2:
            recomendaciones.append(f"- Ventas perdidas detectadas ({tasa_perdida:.1f}%). Monitorear cobertura de inventario.")
    
    # Análisis de OTIF
    otif_promedio = kpis_diarios['otif'].mean() if 'otif' in kpis_diarios.columns else 0
    if otif_promedio < 80:
        recomendaciones.append(f"- OTIF bajo ({otif_promedio:.1f}%). Incrementar capacidad de picking o mejorar gestion de inventario.")
    elif otif_promedio < 90:
        recomendaciones.append(f"- OTIF moderado ({otif_promedio:.1f}%). Revisar procesos de alistamiento.")
    
    # Análisis de Utilización de Flota
    utilizacion_flota = kpis_diarios['utilizacion_flota'].mean() if 'utilizacion_flota' in kpis_diarios.columns else 0
    if utilizacion_flota < 60:
        recomendaciones.append(f"- Baja utilizacion de flota ({utilizacion_flota:.1f}%). Consolidar rutas o reasignar pedidos entre zonas.")
    elif utilizacion_flota > 90:
        recomendaciones.append(f"- Flota cerca del limite ({utilizacion_flota:.1f}%). Considerar ampliar capacidad de transporte.")
    
    # Análisis de Días Pico (Peak Days)
    demanda_por_dia = df_pedidos.groupby('Fecha')['Cant_Solicitada'].sum().sort_values(ascending=False)
    if len(demanda_por_dia) > 0:
        top_3_dias = demanda_por_dia.head(3)
        if len(top_3_dias) > 0:
            dias_pico_str = ", ".join([f"Dia {int(dia)}" for dia in top_3_dias.index])
            recomendaciones.append(f"- Dias de mayor demanda: {dias_pico_str}. Reforzar personal de picking en estos dias.")
    
    # Análisis de Productos Críticos
    if 'historial_backlog' in resultados and not resultados['historial_backlog'].empty:
        productos_backlog = resultados['historial_backlog'].groupby('Producto')['Cantidad_Pendiente'].sum().sort_values(ascending=False).head(3)
        if len(productos_backlog) > 0:
            productos_str = ", ".join(productos_backlog.index)
            recomendaciones.append(f"- Productos con mayor backlog: {productos_str}. Priorizar reaprovisionamiento.")
    
    # Recomendación general sobre política FIFO
    recomendaciones.append("- Sistema utiliza politica FIFO estricta para backlog (atencion equitativa por orden de llegada).")
    
    if len(recomendaciones) == 1:  # Solo la recomendación FIFO
        recomendaciones.insert(0, "- Operacion estable. Mantener parametros actuales y monitorear tendencias.")
    
    pdf.chapter_body("\n".join(recomendaciones))

    # 6. Resumen de Inventario
    pdf.chapter_title("6. Estado Final del Inventario")
    
    if resultados['resultados_diarios']:
        ultimo_dia = resultados['resultados_diarios'][-1]
        if 'estado_inventario' in ultimo_dia:
            df_final = ultimo_dia['estado_inventario'].join(
                resultados['df_productos'][['Nombre_Producto', 'Stock_Seguridad']]
            ).head(10)
            
            pdf.set_font('Arial', 'B', 8)
            cols = ['Producto', 'Nombre', 'Stock_Fisico', 'Stock_Disponible']
            anchos = [40, 60, 30, 30]
            
            for i, col in enumerate(cols):
                pdf.cell(anchos[i], 8, col, 1)
            pdf.ln()
            
            pdf.set_font('Arial', '', 8)
            for index, row in df_final.iterrows():
                pdf.cell(anchos[0], 8, str(index)[:30], 1)
                pdf.cell(anchos[1], 8, str(row.get('Nombre_Producto', 'N/A'))[:30], 1)
                pdf.cell(anchos[2], 8, str(int(row['Stock_Fisico'])), 1)
                pdf.cell(anchos[3], 8, str(int(row['Stock_Disponible'])), 1)
                pdf.ln()
    
    return pdf.output(dest='S').encode('latin-1')
