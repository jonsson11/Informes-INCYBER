import os
import re
from datetime import datetime
from fpdf.enums import XPos, YPos
from config import (OUTPUT_DIR,logo_portada,pictogram_watermark,
    icon_windows,icon_linux,icon_macos,icon_server,
    icon_managed,icon_active,icon_shield,
    icon_physical,icon_virtual,)
from pdf.pdf_base import (PDF,C_NAVY,C_NAVY_LIGHT,C_MAGENTA,C_MAGENTA_DARK,C_MAGENTA_TINT,
    C_YELLOW,C_GREEN,C_GRAY,C_MUTED,C_BORDER,C_LIGHT,C_LIGHT_ROW,C_WHITE,C_TEXT,
    C_DARK,C_DARK2,C_RED,C_RED2,THREAT_COLORS,)
from pdf.components import (kpi_card,section_card,)


def _wrap_text(pdf, text, max_width):
    """Parte 'text' en lineas que encajen en 'max_width' (mm), segun la fuente actual."""
    lines = []
    current = ""
    for ch in text:
        if pdf.get_string_width(current + ch) <= max_width:
            current += ch
        else:
            lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines or [""]


def generate_pdf(company,stats,period_label,period_start=None,has_zabbix=False,zabbix_problems=None,):
    pdf = PDF()
    pdf.set_auto_page_break(auto=True,margin=15)
    period_str = period_label

    # ─────────────────────────────────────────────
    # PORTADA
    # ─────────────────────────────────────────────

    pdf.add_page()
    W, H = 210, 297

    # Desactivamos temporalmente el salto de pagina automatico: la
    # portada usa posicionamiento absoluto y no debe generar una
    # pagina en blanco extra si alguna celda roza el margen inferior.
    pdf.set_auto_page_break(auto=False)

    # Fondo solido azul marino (identidad Incyber), sin degradados ni
    # resplandores: portada "corporativa oscura" aprobada en las maquetas.
    pdf.set_fill_color(*C_NAVY)
    pdf.rect(0,0,W,H,style="F")

    # Pictograma del laberinto como marca de agua muy sutil, esquina
    # inferior derecha (recorta fuera del margen, igual que la maqueta).
    if os.path.exists(pictogram_watermark):
        wm_w = 150
        wm_x = W + 35 - wm_w
        wm_y = H + 35 - wm_w
        with pdf.local_context(fill_opacity=0.05):
            pdf.image(pictogram_watermark,x=wm_x,y=wm_y,w=wm_w)

    # Logo Incyber (version blanca de marca) arriba a la izquierda
    logo_w = 46
    margin_top = 16
    margin_left = 16
    if os.path.exists(logo_portada):
        pdf.image(logo_portada,x=margin_left,y=margin_top,w=logo_w)

    # Filete magenta + kicker + nombre de empresa, bloque de titulo
    block_x = margin_left
    block_w = W - 2 * margin_left
    pdf.set_fill_color(*C_MAGENTA)
    pdf.rect(block_x, 148, 17, 1.6, "F")

    pdf.set_xy(block_x, 154)
    pdf.set_font("helvetica","B",13.5)
    pdf.set_text_color(*C_MAGENTA)
    pdf.multi_cell(block_w,7,"INFORME MENSUAL DE CIBERSEGURIDAD",align="L",)

    pdf.set_x(block_x)
    pdf.set_font("helvetica","B",27)
    pdf.set_text_color(*C_WHITE)
    pdf.multi_cell(block_w,11,company.upper(),align="L",)

    pdf.ln(2)
    pdf.set_x(block_x)
    pdf.set_font("helvetica","",11.5)
    pdf.set_text_color(200,204,224)
    pdf.cell(block_w,7,f"Periodo del informe \u2014 {period_str}",align="L",)

    # Linea de pie + metadatos, igual que en la maqueta aprobada
    footer_y = H - 24
    pdf.set_draw_color(59,72,128)
    pdf.set_line_width(0.25)
    pdf.line(margin_left, footer_y, W - margin_left, footer_y)

    pdf.set_xy(margin_left, footer_y + 4)
    pdf.set_font("helvetica","",8.5)
    pdf.set_text_color(*C_MUTED)
    pdf.cell(block_w / 2,6,f"Generado automaticamente el {datetime.now().strftime('%d/%m/%Y')}",align="L",)

    pdf.set_xy(margin_left + block_w / 2, footer_y + 4)
    pdf.set_font("helvetica","B",8.5)
    pdf.set_text_color(*C_MUTED)
    pdf.cell(block_w / 2,6,"CONFIDENCIAL \u2014 USO INTERNO",align="R",)

    # ─────────────────────────────────────────────
    # PAGINA 2
    # ─────────────────────────────────────────────
    pdf.set_auto_page_break(auto=True,margin=15)
    pdf.add_page()
    pdf.set_text_color(*C_DARK)
    pdf.set_font("helvetica","B",18)
    pdf.cell(0,12,"Estado Global de Seguridad",new_x=XPos.LMARGIN,new_y=YPos.NEXT,)
    pdf.set_font("helvetica","",8)
    pdf.set_text_color(*C_GRAY)
    pdf.cell(0,5,f"Periodo de informe: {period_str}",new_x=XPos.LMARGIN,new_y=YPos.NEXT,)
    pdf.ln(3)

    kpi_card(pdf,15,45,56,26,
        "Endpoints Gestionados",stats["total_managed"],icon=icon_managed,)
    kpi_card(pdf,76,45,56,26,
        "Endpoints Activos",stats["total_online"],"(Con conexión en los últimos 30 días)",icon=icon_active,)
    kpi_card(pdf,137,45,56,26,
        "Amenazas Bloqueadas",stats["blocked_total"],icon=icon_shield,)
    section_card(pdf,15,80,180,34,
        "Detalle de Inventario",)

    inv_cols = [
        (str(stats["ws_count"]), "Windows", icon_windows),
        (str(stats["sv_count"]), "Windows Server", icon_server),
        (str(stats["macos_count"]), "macOS", icon_macos),
        (str(stats["linux_count"]), "Linux", icon_linux),
        (str(stats["phys_count"]), "Fisicos", icon_physical),
        (str(stats["virt_count"]), "Virtuales", icon_virtual),
    ]

    x_pos = 24

    for i, (num, lbl, icon) in enumerate(inv_cols):
        # Separador fino entre el grupo de SO (WS/SRV/macOS/Linux)
        # y el grupo Fisico/Virtual, antes de la 5a columna
        if i == 4:
            sep_x = x_pos - 10
            pdf.set_draw_color(*C_RED)
            pdf.set_line_width(0.4)
            pdf.line(sep_x, 86, sep_x, 110)

        if icon:
            icon_size = 7
            pdf.image(icon, x=x_pos, y=96.5, w=icon_size, h=icon_size)

        pdf.set_xy(x_pos + (10 if icon else 0), 97)
        pdf.set_font("helvetica","B",13)
        pdf.set_text_color(*C_DARK)
        pdf.cell(22,6,num)
        pdf.set_xy(x_pos,104)
        pdf.set_font("helvetica","",7)
        pdf.set_text_color(*C_GRAY)
        pdf.cell(22,4,lbl)
        x_pos += 30

    section_card(pdf,15,124,88,65,
        "Distribución por Tipos de Amenaza",)

    total_v = (sum(stats["top5_threats"].values())if stats["top5_threats"] else 1)

    for i, (threat, count) in enumerate(stats["top5_threats"].items()):
        color = THREAT_COLORS[i % len(THREAT_COLORS)]
        bar_y = 138 + i * 10
        pdf.set_xy(22,bar_y)
        pdf.set_font("helvetica","",7)
        pdf.set_text_color(*C_TEXT)
        pdf.cell(33,5, threat[:20])
        pdf.set_fill_color(226,232,240)
        pdf.rect(57,bar_y + 1.5,33,3.5,"F")
        pdf.set_fill_color(*color)
        pdf.rect(57,bar_y + 1.5,(count / total_v) * 33, 3.5,"F")
        pdf.set_xy(92,bar_y )
        pdf.set_font("helvetica","B",7)
        pdf.cell(8,5,str(int(count)))

    if not stats["top5_threats"]:
        pdf.set_xy(22,148)
        pdf.set_font("helvetica","I",8)
        pdf.set_text_color(*C_GRAY)
        pdf.cell(75,5,
            "Sin amenazas en el periodo")

    section_card(pdf,107,124,88,65,
        "Distribución por Tipo de Endpoint",)

    ws_v = stats["breakdown_ws"]
    sv_v = stats["breakdown_sv"]

    if ws_v + sv_v == 0:
        pdf.set_xy(116,148)
        pdf.set_font("helvetica","I",8)
        pdf.set_text_color(*C_GRAY)
        pdf.cell(75,5,
            "Sin datos en el periodo")
    else:
        total_ep = max(1,ws_v + sv_v)
        ws_w = (ws_v / total_ep) * 72
        sv_w = 72 - ws_w
        bx = 116
        by = 148
        pdf.set_fill_color(*C_RED)
        pdf.rect(bx,by, ws_w, 12,"F")
        pdf.set_fill_color(*C_NAVY)
        pdf.rect(bx + ws_w, by,sv_w, 12,"F")
        pdf.set_xy(bx,by + 1)
        pdf.set_font("helvetica","B", 9)
        pdf.set_text_color(*C_WHITE)
        pdf.cell(72,10, str(ws_v + sv_v), align="C")
        pdf.set_fill_color(*C_RED)
        pdf.rect(bx,by + 16, 3, 3,"F")
        pdf.set_xy(bx + 5,by + 15)
        pdf.set_font("helvetica","",7)
        pdf.set_text_color(*C_TEXT)
        pdf.cell( 30,5,
            f"En Workstations: {ws_v}")
        pdf.set_fill_color(*C_NAVY)
        pdf.rect(bx,by + 23,3, 3,"F")
        pdf.set_xy(bx + 5,by + 22)
        pdf.cell(30,5,
            f"En Servidores: {sv_v}")
    
    section_card(pdf,15, 199,180, 44,
        "Acciones de Remediacion",)
    pcts = stats["action_pcts"]
    # Los 4 segmentos usan integramente la paleta de marca: magenta y
    # navy como primarios, amarillo como acento puntual (tal y como
    # indica el manual: "CTAs, alertas, detalles clave") y gris neutro.
    colors = [
        C_MAGENTA,
        C_NAVY,
        C_YELLOW,
        C_MUTED,
    ]
    # Texto oscuro sobre el segmento amarillo (regla de marca: nunca
    # texto blanco/negro generico sobre un fondo de color, usar el tono
    # mas oscuro de la misma familia -> aqui, navy).
    text_colors = [C_WHITE, C_WHITE, C_NAVY, C_WHITE]
    labels = ["Bloqueado","Eliminado","Cuarentena","Desinfectado",]
    keys = ["blocked","deleted","quarantine","disinfected",]
    bx3 = 25
    by3 = 215
    bw3 = 162
    bh3 = 9

    if sum(pcts.get(k, 0) for k in keys) == 0:
        pdf.set_xy(25,217)
        pdf.set_font("helvetica","I",8)
        pdf.set_text_color(*C_GRAY)
        pdf.cell(162,5,
            "Sin acciones de remediacion en el periodo",align="C")
    else:
        cx3 = bx3
        pdf.set_font("helvetica","B",8)
        for key, color, txt_color in zip(keys,colors,text_colors):
            pct_val = pcts.get(key, 0)
            seg_w = (pct_val / 100) * bw3
            pdf.set_fill_color(*color)
            pdf.rect(cx3,by3,seg_w,bh3,"F")

            # Solo dibujamos el porcentaje DENTRO del segmento si cabe.
            # Asi evitamos que el texto se desborde sobre otros segmentos.
            label_txt = f"{pct_val:.1f}%"
            text_w = pdf.get_string_width(label_txt)
            if pct_val > 0 and text_w + 4 <= seg_w:
                pdf.set_xy(cx3, by3)
                pdf.set_text_color(*txt_color)
                pdf.cell(seg_w, bh3, label_txt, align="C")

            cx3 += seg_w

        lx = 25
        for lbl, key, color in zip(labels,keys,colors):
            pdf.set_fill_color(*color)
            pdf.rect(lx, 229, 3, 3,"F")
            pdf.set_xy(lx + 5,227)
            pdf.set_font("helvetica","",6)
            pdf.set_text_color(*C_TEXT)
            pdf.cell(30,5,f"{lbl}: {pcts.get(key, 0):.1f}%")
            lx += 34

    # ─────────────────────────────────────────────
    # PAGINA 3: CUARENTENA & TOP10
    # ─────────────────────────────────────────────
    pdf.add_page()

    pdf.set_font("helvetica","B",7.5)
    pdf.set_text_color(*C_MAGENTA)
    pdf.cell(0,5,"FUENTE \u00b7 BITDEFENDER GRAVITYZONE",new_x=XPos.LMARGIN,new_y=YPos.NEXT,)
    pdf.ln(1)
    pdf.set_text_color(*C_NAVY)
    pdf.set_font("helvetica", "B", 18)

    pdf.cell(0,12,
        "Elementos en Cuarentena",new_x=XPos.LMARGIN,new_y=YPos.NEXT,)

    quarantine = stats["quarantine_table"]
    pdf.ln(3)

    start_x = pdf.get_x()

    def _draw_quarantine_header():
        pdf.set_x(start_x)
        y0 = pdf.get_y()
        pdf.set_text_color(*C_GRAY)
        pdf.set_font("helvetica", "B", 8)
        pdf.cell(15, 8, "#", border=0, align="C")
        pdf.cell(38, 8, "ENDPOINT", border=0)
        pdf.cell(48, 8, "MALWARE", border=0)
        pdf.cell(60, 8, "RUTA", border=0)
        pdf.cell(4,8,"",border=0)
        pdf.cell(25,8,"FECHA",border=0,new_x=XPos.LMARGIN,new_y=YPos.NEXT,)
        pdf.set_draw_color(*C_NAVY)
        pdf.set_line_width(0.5)
        pdf.line(start_x, y0 + 8, start_x + 190, y0 + 8)
        pdf.ln(2)

    _draw_quarantine_header()

    if quarantine.empty:

        row_h = 11
        y0 = pdf.get_y()

        pdf.set_fill_color(*C_WHITE)
        pdf.rect(start_x, y0, 190, row_h, "F")

        pdf.set_text_color(*C_GRAY)
        pdf.set_font("helvetica", "I", 9)
        pdf.set_xy(start_x, y0 + 3)
        pdf.cell(190,5,"No se han añadido elementos a la cuarentena.",align="C",)
        pdf.set_draw_color(*C_BORDER)
        pdf.set_line_width(0.4)
        pdf.line(start_x, y0 + row_h, start_x + 190, y0 + row_h)
        pdf.ln(row_h)

    else:
        alt = False
        sep_ys = []
        col_endpoint_x = start_x + 15
        col_malware_x = col_endpoint_x + 38
        col_ruta_x = col_malware_x + 48
        col_fecha_x = col_ruta_x + 60 + 4
        ruta_w = 58
        line_h = 4.2

        def _flush_q_seps():
            pdf.set_draw_color(*C_BORDER)
            pdf.set_line_width(0.2)
            for sy in sep_ys:
                pdf.line(start_x, sy, start_x + 190, sy)
            sep_ys.clear()

        for pos, (_, row) in enumerate(quarantine.iterrows(), start=1):

            pdf.set_font("helvetica", "", 8)
            ruta_lines = _wrap_text(pdf, str(row["Ruta"]), ruta_w)
            row_h = max(11, line_h * len(ruta_lines) + 6)

            if pdf.get_y() + row_h > pdf.page_break_trigger:
                # Dibujar separadores pendientes ANTES de saltar de página,
                # mientras no hay ningún rect posterior que los tape.
                _flush_q_seps()
                pdf.add_page()
                _draw_quarantine_header()
                alt = False

            y0 = pdf.get_y()
            pdf.set_fill_color(*(C_LIGHT_ROW if alt else C_WHITE))
            pdf.rect(start_x, y0, 190, row_h, "F")

            pdf.set_text_color(*C_TEXT)
            pdf.set_font("helvetica", "", 8)

            badge_cx = start_x + 7.5
            badge_cy = y0 + row_h / 2
            badge_r = 3.6
            pdf.set_fill_color(*C_MAGENTA_TINT)
            pdf.ellipse(badge_cx - badge_r, badge_cy - badge_r, badge_r * 2, badge_r * 2, "F")
            pdf.set_text_color(*C_MAGENTA)
            pdf.set_font("helvetica", "B", 8)

            pdf.set_xy(start_x, badge_cy - 2.3)
            pdf.cell(15, 4.6, str(pos), align="C")

            text_y = y0 + (row_h - 5) / 2
            pdf.set_text_color(*C_TEXT)
            pdf.set_font("helvetica", "", 8)
            pdf.set_xy(col_endpoint_x, text_y)
            pdf.cell(38, 5, str(row["Endpoint"])[:25])
            pdf.set_xy(col_malware_x, text_y)
            pdf.cell(48, 5, str(row["Malware"])[:30])
            pdf.set_xy(col_fecha_x, text_y)
            pdf.cell(20, 5, str(row["Fecha"])[:10])

            ruta_y0 = y0 + (row_h - line_h * len(ruta_lines)) / 2
            for i, line in enumerate(ruta_lines):
                pdf.set_xy(col_ruta_x, ruta_y0 + i * line_h)
                pdf.cell(60, line_h, line)

            # NO dibujar la línea aquí: la siguiente iteración pintaría
            # su rect justo encima tapándola. Se acumula y se dibuja en
            # _flush_q_seps(), que se llama antes de cada salto de
            # página (o al final, cuando ya no hay más rects que la tapen).
            sep_ys.append(y0 + row_h)
            pdf.set_xy(start_x, y0 + row_h)
            alt = not alt

        _flush_q_seps()
        pdf.set_y(pdf.get_y())

    pdf.set_draw_color(*C_BORDER)
    pdf.set_line_width(0.2)
    pdf.line(start_x, pdf.get_y(), start_x + 190, pdf.get_y())
    pdf.ln(2.5)
    pdf.set_font("helvetica", "", 8)
    pdf.set_text_color(*C_GRAY)
    pdf.cell(95, 5, f"Elementos en cuarentena: {len(quarantine)}")
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(*C_NAVY)
    pdf.cell(95, 5, f"Periodo: {period_str}", align="R",
        new_x=XPos.LMARGIN, new_y=YPos.NEXT,)

    pdf.set_text_color(*C_GRAY)
    pdf.set_font("helvetica", "I", 8)

    pdf.ln(3)

    pdf.multi_cell(190,4,
        "Los archivos en cuarentena se consideran potencialmente maliciosos y han sido aislados de forma segura para impedir su ejecución y proteger los equipos de la organización. Se recomienda eliminar estos archivos manualmente por precaución si no son estrictamente necesarios. Si detecta que algún archivo ha sido puesto en cuarentena incorrectamente, por favor, contáctanos para su revisión."
    )

    pdf.ln(4)
    top10 = stats["top10_table"]
    row_h = 11
    title_h = 15
    space_h = 3
    header_h = 11
    rows_h = row_h if top10.empty else len(top10) * row_h

    required_h = title_h + space_h + header_h + rows_h

    if pdf.get_y() + required_h > pdf.page_break_trigger:
        pdf.add_page()

    pdf.set_font("helvetica","B",7.5)
    pdf.set_text_color(*C_MAGENTA)
    pdf.cell(0,5,"FUENTE \u00b7 BITDEFENDER GRAVITYZONE",new_x=XPos.LMARGIN,new_y=YPos.NEXT,)
    pdf.ln(1)
    pdf.set_text_color(*C_NAVY)
    pdf.set_font("helvetica","B",18)
    pdf.cell(0,12,
        "Top 10 Endpoints Afectados",new_x=XPos.LMARGIN,new_y=YPos.NEXT,)

    pdf.ln(3)
    start_x = pdf.get_x()

    def _draw_top10_header():
        pdf.set_x(start_x)
        y0 = pdf.get_y()
        pdf.set_text_color(*C_GRAY)
        pdf.set_font("helvetica","B",8)
        pdf.cell(20,8,"#",border=0,align="C")
        pdf.cell(120,8,
            "  NOMBRE DEL ENDPOINT",border=0)
        pdf.cell(50,8,
            "DETECCIONES",border=0,align="C",new_x=XPos.LMARGIN,new_y=YPos.NEXT,)
        pdf.set_draw_color(*C_NAVY)
        pdf.set_line_width(0.5)
        pdf.line(start_x, y0 + 8, start_x + 190, y0 + 8)
        pdf.ln(2)

    _draw_top10_header()

    alt = False
    row_h = 11

    if top10.empty:
        row_h = 11
        y0 = pdf.get_y()

        pdf.set_fill_color(*C_WHITE)
        pdf.rect(start_x, y0, 190, row_h, "F")

        pdf.set_text_color(*C_GRAY)
        pdf.set_font("helvetica", "I", 9)
        pdf.set_xy(start_x, y0 + 3)
        pdf.cell(190,5,"Sin detecciones en el periodo.",align="C",)
        pdf.set_draw_color(*C_BORDER)
        pdf.set_line_width(0.4)
        pdf.line(start_x, y0 + row_h, start_x + 190, y0 + row_h)
        pdf.ln(row_h)

    else:
        sep_ys = []
        total_detecciones = int(top10["Detecciones"].sum())

        def _flush_t10_seps():
            pdf.set_draw_color(*C_BORDER)
            pdf.set_line_width(0.2)
            for sy in sep_ys:
                pdf.line(start_x, sy, start_x + 190, sy)
            sep_ys.clear()

        for i, (_, row) in enumerate(top10.iterrows()):
            pos = i + 1

            if pdf.get_y() + row_h > pdf.page_break_trigger:
                _flush_t10_seps()
                pdf.add_page()
                _draw_top10_header()
                alt = False

            is_podium = pos <= 3
            y0 = pdf.get_y()
            pdf.set_fill_color(*(C_MAGENTA_TINT if is_podium else (C_LIGHT_ROW if alt else C_WHITE)))
            pdf.rect(start_x, y0, 190, row_h, "F")

            badge_cx = start_x + 10
            badge_cy = y0 + row_h / 2
            badge_r = 4.2 if is_podium else 3.6

            pdf.set_fill_color(*C_MAGENTA_TINT)
            pdf.ellipse(badge_cx - badge_r, badge_cy - badge_r, badge_r * 2, badge_r * 2, "F")
            pdf.set_text_color(*C_MAGENTA)
            pdf.set_font("helvetica", "B", 9 if is_podium else 8)

            pdf.set_xy(start_x, badge_cy - 2.3)
            pdf.cell(20, 4.6, str(pos), align="C")

            pdf.set_xy(start_x + 20, y0 + (row_h - 5) / 2)
            pdf.set_text_color(*C_MAGENTA if is_podium else C_TEXT)
            pdf.set_font("helvetica", "B" if is_podium else "", 9)
            pdf.cell(120, 5, f"  {row['Endpoint']}")

            pdf.set_xy(start_x + 140, y0 + (row_h - 5) / 2)
            pdf.set_text_color(*C_MAGENTA if is_podium else C_NAVY)
            pdf.set_font("helvetica", "B", 9)
            pdf.cell(50, 5, str(int(row["Detecciones"])), align="C")

            sep_ys.append(y0 + row_h)
            pdf.set_xy(start_x, y0 + row_h)
            alt = not alt

        _flush_t10_seps()
        pdf.set_y(pdf.get_y())
        pdf.set_draw_color(*C_BORDER)
        pdf.set_line_width(0.2)
        pdf.line(start_x, pdf.get_y(), start_x + 190, pdf.get_y())
        pdf.ln(2.5)
        pdf.set_font("helvetica", "", 8)
        pdf.set_text_color(*C_GRAY)
        pdf.cell(95, 5, f"Endpoints en el ranking: {len(top10)}")
        pdf.set_font("helvetica", "B", 8)
        pdf.set_text_color(*C_NAVY)
        pdf.cell(95, 5, f"Total detecciones: {total_detecciones}", align="R",
            new_x=XPos.LMARGIN, new_y=YPos.NEXT,)
        pdf.ln(2)

    # ─────────────────────────────────────────────
    # SECCION: INCIDENCIAS ZABBIX (solo si la empresa tiene Zabbix)
    # ─────────────────────────────────────────────
    if has_zabbix:
        zabbix_problems = zabbix_problems or []

        title_h_z = 15
        header_h_z = 11
        problema_w_z = 51  # ancho util de la columna "Problema" para el wrap
        line_h_z = 4.2

        pdf.set_font("helvetica", "", 8)
        _z_lines_cache = [
            _wrap_text(pdf, str(p["name"]), problema_w_z) for p in zabbix_problems
        ]
        _z_row_heights = [
            max(11, line_h_z * len(lines) + 6) for lines in _z_lines_cache
        ]
        rows_h_z = sum(_z_row_heights) if _z_row_heights else 11
        required_h_z = title_h_z + header_h_z + rows_h_z

        if pdf.get_y() + required_h_z > pdf.page_break_trigger:
            pdf.add_page()

        pdf.set_font("helvetica","B",7.5)
        pdf.set_text_color(*C_MAGENTA)
        pdf.cell(0,5,"FUENTE \u00b7 ZABBIX MONITORING",new_x=XPos.LMARGIN,new_y=YPos.NEXT,)
        pdf.ln(1)
        pdf.set_text_color(*C_NAVY)
        pdf.set_font("helvetica", "B", 18)
        pdf.cell(0, 12,
            "Incidencias en Resolucion (Zabbix)", new_x=XPos.LMARGIN, new_y=YPos.NEXT,)

        pdf.ln(3)
        start_x = pdf.get_x()

        def _draw_zabbix_header():
            pdf.set_x(start_x)
            y0 = pdf.get_y()
            pdf.set_text_color(*C_GRAY)
            pdf.set_font("helvetica", "B", 8)
            pdf.cell(12, 8, "#", border=0, align="C")
            pdf.cell(33, 8, "HOST", border=0)
            pdf.cell(53, 8, "PROBLEMA", border=0)
            pdf.cell(16, 8, "OCURR.", border=0, align="C")
            pdf.cell(23, 8, "SEVERIDAD", border=0, align="C")
            pdf.cell(23, 8, "ESTADO", border=0, align="C")
            pdf.cell(30, 8, "ULTIMA DETECCION", border=0, align="C",
                new_x=XPos.LMARGIN, new_y=YPos.NEXT,)
            pdf.set_draw_color(*C_NAVY)
            pdf.set_line_width(0.5)
            pdf.line(start_x, y0 + 8, start_x + 190, y0 + 8)
            pdf.ln(2)

        _draw_zabbix_header()

        if not zabbix_problems:
            row_h_e = 11
            y0 = pdf.get_y()
            pdf.set_fill_color(*C_WHITE)
            pdf.rect(start_x, y0, 190, row_h_e, "F")
            pdf.set_text_color(*C_GRAY)
            pdf.set_font("helvetica", "I", 9)
            pdf.set_xy(start_x, y0 + 3)
            pdf.cell(190, 5, "Sin incidencias suprimidas/reconocidas en el periodo.", align="C",)
            pdf.set_draw_color(*C_BORDER)
            pdf.set_line_width(0.4)
            pdf.line(start_x, y0 + row_h_e, start_x + 190, y0 + row_h_e)
            pdf.ln(row_h_e)
        else:
            alt = False
            sep_ys = []
            col_host_x = start_x + 12
            col_problema_x = col_host_x + 33
            col_ocurr_x = col_problema_x + 53
            col_sev_x = col_ocurr_x + 16
            col_estado_x = col_sev_x + 23
            col_fecha_x = col_estado_x + 23

            def _flush_z_seps():
                pdf.set_draw_color(*C_BORDER)
                pdf.set_line_width(0.2)
                for sy in sep_ys:
                    pdf.line(start_x, sy, start_x + 190, sy)
                sep_ys.clear()

            for i, p in enumerate(zabbix_problems):
                pos = i + 1
                name_lines = _z_lines_cache[i]
                row_h_z = _z_row_heights[i]

                if pdf.get_y() + row_h_z > pdf.page_break_trigger:
                    _flush_z_seps()
                    pdf.add_page()
                    _draw_zabbix_header()
                    alt = False

                y0 = pdf.get_y()
                pdf.set_fill_color(*(C_LIGHT_ROW if alt else C_WHITE))
                pdf.rect(start_x, y0, 190, row_h_z, "F")

                # Badge redondo con el numero de fila, igual que en Cuarentena/Top10
                badge_cx = start_x + 6
                badge_cy = y0 + row_h_z / 2
                badge_r = 3.4
                pdf.set_fill_color(*C_MAGENTA_TINT)
                pdf.ellipse(badge_cx - badge_r, badge_cy - badge_r, badge_r * 2, badge_r * 2, "F")

                pdf.set_text_color(*C_MAGENTA)
                pdf.set_font("helvetica", "B", 8)
                pdf.set_xy(start_x, badge_cy - 2.3)
                pdf.cell(12, 4.6, str(pos), align="C")

                text_y = y0 + (row_h_z - 5) / 2

                pdf.set_text_color(*C_TEXT)
                pdf.set_font("helvetica", "", 8)
                pdf.set_xy(col_host_x, text_y)
                pdf.cell(33, 5, str(p["host"])[:20])

                # "Problema" en varias lineas, centrado verticalmente segun
                # cuantas lineas ocupe (igual que la columna "Ruta" en Cuarentena)
                name_y0 = y0 + (row_h_z - line_h_z * len(name_lines)) / 2
                for li, line in enumerate(name_lines):
                    pdf.set_xy(col_problema_x, name_y0 + li * line_h_z)
                    pdf.cell(53, line_h_z, line)

                pdf.set_font("helvetica", "B", 8)
                pdf.set_xy(col_ocurr_x, text_y)
                pdf.cell(16, 5, str(p["occurrences"]), align="C")

                pdf.set_font("helvetica", "", 8)
                pdf.set_xy(col_sev_x, text_y)
                pdf.cell(23, 5, str(p["severity"]), align="C")

                resolved = p.get("resolved", False)
                estado_str = "RESUELTO" if resolved else "ACTIVO"
                pdf.set_text_color(*C_GREEN if resolved else C_RED)
                pdf.set_font("helvetica", "B", 7.5)
                pdf.set_xy(col_estado_x, text_y)
                pdf.cell(23, 5, estado_str, align="C")

                pdf.set_text_color(*C_TEXT)
                pdf.set_font("helvetica", "", 8)
                fecha_str = p["date"].strftime("%d/%m/%y") if p.get("date") else "N/D"
                pdf.set_xy(col_fecha_x, text_y)
                pdf.cell(30, 5, fecha_str, align="C")

                sep_ys.append(y0 + row_h_z)
                pdf.set_xy(start_x, y0 + row_h_z)
                alt = not alt

            _flush_z_seps()
            pdf.set_y(pdf.get_y())
            pdf.set_draw_color(*C_BORDER)
            pdf.set_line_width(0.2)
            pdf.line(start_x, pdf.get_y(), start_x + 190, pdf.get_y())
            pdf.ln(2.5)
            total_ocurr_z = sum(p.get("occurrences", 0) for p in zabbix_problems)
            pdf.set_font("helvetica", "", 8)
            pdf.set_text_color(*C_GRAY)
            pdf.cell(95, 5, f"Incidencias con seguimiento activo: {len(zabbix_problems)}")
            pdf.set_font("helvetica", "B", 8)
            pdf.set_text_color(*C_NAVY)
            pdf.cell(95, 5, f"Total ocurrencias: {total_ocurr_z}", align="R",
                new_x=XPos.LMARGIN, new_y=YPos.NEXT,)

    if period_start:
        mmaa = period_start.strftime("%m%y")
    else:
        mmaa = datetime.now().strftime("%m%y")
    out_name = ("Informe_"f"{re.sub(r'[^A-Za-z0-9_-]', '_', company)}_{mmaa}.pdf")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR,out_name)
    pdf.output(out_path)
    return out_path