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
        
    # 4. Resumen de Inventario
    pdf.chapter_title("4. Estado Final del Inventario (Top 10 Productos)")
    
    df_estado = resultados['df_productos'].join(resultados['df_kardex'].groupby('Producto').last()['Saldo_Final'], rsuffix='_Final')
    # Nota: df_kardex puede estar vacio o no tener todos los productos si no hubo movs.
    # Mejor usar df_estado_actual si está disponible en resultados, o reconstruirlo.
    # En main.py devolvemos 'df_productos' y 'df_kardex'.
    # Pero main.py NO devuelve 'df_estado_actual' explícitamente en el nivel superior del dict, 
    # pero sí está dentro de 'resultados_diarios'[-1]['estado_inventario']
    
    if resultados['resultados_diarios']:
        ultimo_dia = resultados['resultados_diarios'][-1]
        if 'estado_inventario' in ultimo_dia:
            # Join con df_productos para obtener Nombre_Producto
            df_final = ultimo_dia['estado_inventario'].join(
                resultados['df_productos'][['Nombre_Producto', 'Stock_Seguridad']]
            ).head(10)
            
            pdf.set_font('Arial', 'B', 8)
            # Encabezados
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
