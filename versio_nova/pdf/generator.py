import os
import re
from datetime import datetime
from PIL import Image
from fpdf.enums import XPos, YPos
from fpdf.pattern import LinearGradient, RadialGradient
from config import (BASE_PATH,OUTPUT_DIR,logo_portada,icon_portada,
    icon_windows,icon_linux,icon_macos,icon_server,
    icon_managed,icon_active,icon_shield,
    icon_physical,icon_virtual,)
from pdf.pdf_base import (PDF,C_DARK,C_DARK2,C_RED,C_RED2,C_GRAY,C_LIGHT,C_WHITE,C_TEXT,C_MUTED,C_NAVY,THREAT_COLORS,)
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

    # Fondo con degradado diagonal sutil
    grad_bg = LinearGradient(0,0,W,H,colors=[C_DARK,C_DARK2])
    with pdf.use_pattern(grad_bg):
        pdf.rect(0,0,W,H,style="F")

    # Patron de fondo: lineas diagonales finas, muy sutiles
    pdf.set_draw_color(255,255,255)
    with pdf.local_context(stroke_opacity=0.035):
        pdf.set_line_width(0.3)
        step = 14
        for i in range(-int(H / step),int(W / step) + 1):
            x0 = i * step
            pdf.line(x0,0,x0 + H,H)

    # Resplandor radial rojo centrado en el bloque de titulo
    glow = RadialGradient(W / 2,100,0,W / 2,100,75,colors=[C_RED,C_DARK])
    with pdf.local_context(fill_opacity=0.35):
        with pdf.use_pattern(glow):
            pdf.rect(0,20,W,170,style="F")

    # Segundo resplandor, mas tenue, centrado en el area de la etiqueta de periodo
    glow2 = RadialGradient(W / 2,145,0,W / 2,145,75,colors=[C_RED,C_DARK])
    with pdf.local_context(fill_opacity=0.15):
        with pdf.use_pattern(glow2):
            pdf.rect(0,20,W,170,style="F")

    # Barra superior e inferior con degradado
    grad_top = LinearGradient(0,0,W,0,colors=[C_RED2,C_RED,C_RED2])
    with pdf.use_pattern(grad_top):
        pdf.rect(0,0,W,4,style="F")
    with pdf.use_pattern(grad_top):
        pdf.rect(0,H - 3,W,3,style="F")

    # Cunas triangulares decorativas en las esquinas
    pdf.set_fill_color(*C_RED)
    with pdf.local_context(fill_opacity=0.55):
        pdf.polygon([(0,4),(55,4),(0,45)],style="F")
    with pdf.local_context(fill_opacity=0.45):
        pdf.polygon([(W,H - 3),(W - 70,H - 3),(W,H - 50)],style="F")

    # Detalles tipo "circuito" (linea + nodo) en las esquinas
    pdf.set_draw_color(*C_RED)
    with pdf.local_context(stroke_opacity=0.5):
        pdf.set_line_width(0.4)
        pdf.line(20,30,20,8)
        pdf.line(20,8,45,8)
    with pdf.local_context(fill_opacity=0.8):
        pdf.set_fill_color(*C_RED)
        pdf.circle(45,8,1.2,style="F")

    pdf.set_draw_color(*C_RED)
    with pdf.local_context(stroke_opacity=0.8):
        pdf.line(190,261,190,289)
        pdf.line(190,289,165,289)
    with pdf.local_context(fill_opacity=0.8):
        pdf.set_fill_color(*C_RED)
        pdf.circle(165,289,1.2,style="F")

    # Logo arriba a la derecha, con pequenos margenes
    logo_w = 50
    margin_top = 10
    margin_right = 6
    logo_x = W - margin_right - logo_w
    if os.path.exists(logo_portada):
        pdf.image(logo_portada,x=logo_x,y=margin_top,w=logo_w)

    # Icono decorativo a la izquierda del logo, con la misma altura
    if os.path.exists(logo_portada):
        with Image.open(logo_portada) as _im:
            logo_h_mm = logo_w * (_im.height / _im.width)
    else:
        logo_h_mm = logo_w * (332 / 1200)
    icon_gap = 4
    icon_w = logo_h_mm
    if os.path.exists(icon_portada):
        pdf.image(icon_portada,x=logo_x - icon_gap - icon_w,y=margin_top,w=icon_w,h=logo_h_mm)

    # Titulo de dos pesos: "INFORME DE" fino + "CIBERSEGURIDAD" grueso
    pdf.set_y(95)
    pdf.set_font("helvetica","",20)
    pdf.set_text_color(*C_MUTED)
    pdf.cell(0,10,"INFORME DE",align="C",new_x=XPos.LMARGIN,new_y=YPos.NEXT,)

    pdf.set_font("helvetica","B",34)
    pdf.set_text_color(*C_WHITE)
    pdf.cell(0,14,"CIBERSEGURIDAD",align="C",new_x=XPos.LMARGIN,new_y=YPos.NEXT,)

    # Linea corta con degradado bajo el titulo
    grad_line = LinearGradient(75,0,135,0,colors=[C_DARK,C_RED,C_DARK])
    with pdf.use_pattern(grad_line):
        pdf.rect(75,125,60,0.6,style="F")

    pdf.set_y(132)
    pdf.set_font("helvetica","",11.5)
    pdf.set_text_color(*C_MUTED)
    pdf.cell(0,9,"Resumen ejecutivo y detalle de infecciones",align="C",new_x=XPos.LMARGIN,new_y=YPos.NEXT,)

    # Etiqueta "pill" con el periodo del informe, justo debajo del subtitulo
    pill_text = f"PERIODO: {period_str}"
    pdf.set_font("helvetica","B",8.5)
    pill_w = pdf.get_string_width(pill_text) + 14
    pill_x = (W - pill_w) / 2
    pill_y = 146
    pdf.set_draw_color(*C_RED)
    with pdf.local_context(stroke_opacity=0.7):
        pdf.set_line_width(0.4)
        pdf.rect(pill_x,pill_y,pill_w,7,style="D",round_corners=True,corner_radius=3.5)
    pdf.set_text_color(*C_RED)
    pdf.set_xy(pill_x,pill_y + 1.3)
    pdf.cell(pill_w,4.5,pill_text,align="C")

    # Tarjeta de datos con degradado propio y filo superior rojo
    card_x,card_y,card_w,card_h = 50,215,110,40
    grad_card = LinearGradient(card_x,card_y,card_x,card_y + card_h,colors=[(26,38,66),(18,27,48)])
    with pdf.use_pattern(grad_card):
        pdf.rect(card_x,card_y,card_w,card_h,style="F",round_corners=True,corner_radius=2)
    pdf.set_fill_color(*C_RED)
    pdf.rect(card_x,card_y,card_w,1.2,style="F")

    pdf.set_y(card_y + 6)
    for bold_txt, val_txt in [
        ("EMPRESA:", company),(
            "FECHA INFORME:",datetime.now().strftime("%d/%m/%Y")),(
            "PREPARADO POR:","INCYBER TECHNOLOGIES S.L."),
    ]:

        pdf.set_x(card_x + 10)
        pdf.set_font("helvetica","B",9)
        pdf.set_text_color(*C_WHITE)
        pdf.cell(42,9,bold_txt)
        pdf.set_font("helvetica","",9)
        pdf.set_text_color(*C_MUTED)
        pdf.cell(50,9,val_txt,new_x=XPos.LMARGIN,new_y=YPos.NEXT,)

    # ─────────────────────────────────────────────
    # PAGINA 2
    # ─────────────────────────────────────────────
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
    colors = [
        C_RED,
        C_RED2,
        C_NAVY,
        C_MUTED,
    ]
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
        for key, color in zip(keys,colors):
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
                pdf.set_text_color(*C_WHITE)
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

    pdf.set_text_color(*C_DARK)
    pdf.set_font("helvetica", "B", 18)

    pdf.cell(0,15,
        "Elementos en Cuarentena",new_x=XPos.LMARGIN,new_y=YPos.NEXT,)

    quarantine = stats["quarantine_table"]
    pdf.ln(3)

    start_x = pdf.get_x()

    def _draw_quarantine_header():
        pdf.set_x(start_x)
        pdf.set_fill_color(*C_RED)
        pdf.set_text_color(*C_WHITE)
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(15, 11, "#", border=0, fill=True, align="C")
        pdf.cell(38, 11, "Endpoint", border=0, fill=True)
        pdf.cell(48, 11, "Malware", border=0, fill=True)
        pdf.cell(60, 11, "Ruta", border=0, fill=True)
        pdf.cell(4,11,"",border=0,fill=True)
        pdf.cell(25,11,"Fecha",border=0,fill=True,new_x=XPos.LMARGIN,new_y=YPos.NEXT,)

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
        pdf.set_draw_color(226, 232, 240)
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
            pdf.set_draw_color(0, 0, 0)
            pdf.set_line_width(0.1)
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
            pdf.set_fill_color((241, 245, 249) if alt else C_WHITE)
            pdf.rect(start_x, y0, 190, row_h, "F")

            pdf.set_text_color(*C_TEXT)
            pdf.set_font("helvetica", "", 8)

            badge_cx = start_x + 7.5
            badge_cy = y0 + row_h / 2
            badge_r = 3.6
            pdf.set_draw_color(203, 213, 225)
            pdf.set_line_width(0.25)
            pdf.ellipse(badge_cx - badge_r, badge_cy - badge_r, badge_r * 2, badge_r * 2, "D")

            pdf.set_xy(start_x, badge_cy - 2.3)
            pdf.cell(15, 4.6, str(pos), align="C")

            text_y = y0 + (row_h - 5) / 2
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

    pdf.set_text_color(*C_DARK)
    pdf.set_font("helvetica","B",18)
    pdf.cell(0,15,
        "TOP 10 Endpoints Afectados",new_x=XPos.LMARGIN,new_y=YPos.NEXT,)

    pdf.ln(3)
    start_x = pdf.get_x()

    def _draw_top10_header():
        pdf.set_x(start_x)
        pdf.set_fill_color(*C_RED)
        pdf.set_text_color(*C_WHITE)
        pdf.set_font("helvetica","B",10)
        pdf.cell(20,11,"#",border=0,fill=True,align="C")
        pdf.cell(120,11,
            "  Nombre del Endpoint",border=0,fill=True)
        pdf.cell(50,11,
            "Detecciones",border=0,fill=True,align="C",new_x=XPos.LMARGIN,new_y=YPos.NEXT,)

    _draw_top10_header()

    pdf.set_draw_color(226,232,240)
    pdf.set_line_width(0.1)
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
        pdf.set_draw_color(226, 232, 240)
        pdf.set_line_width(0.4)
        pdf.line(start_x, y0 + row_h, start_x + 190, y0 + row_h)
        pdf.ln(row_h)

    else:
        sep_ys = []

        def _flush_t10_seps():
            pdf.set_draw_color(0, 0, 0)
            pdf.set_line_width(0.1)
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
            pdf.set_fill_color((253,232,238) if is_podium else ((241,245,249) if alt else C_WHITE))
            pdf.rect(start_x, y0, 190, row_h, "F")

            badge_cx = start_x + 10
            badge_cy = y0 + row_h / 2
            badge_r = 4.2 if is_podium else 3.6

            if is_podium:
                pdf.set_fill_color(*C_RED)
                pdf.ellipse(badge_cx - badge_r, badge_cy - badge_r, badge_r * 2, badge_r * 2, "F")
                pdf.set_text_color(*C_WHITE)
                pdf.set_font("helvetica", "B", 9)
            else:
                pdf.set_draw_color(203, 213, 225)
                pdf.set_line_width(0.25)
                pdf.ellipse(badge_cx - badge_r, badge_cy - badge_r, badge_r * 2, badge_r * 2, "D")
                pdf.set_text_color(*C_GRAY)
                pdf.set_font("helvetica", "B", 8)

            pdf.set_xy(start_x, badge_cy - 2.3)
            pdf.cell(20, 4.6, str(pos), align="C")

            pdf.set_xy(start_x + 20, y0 + (row_h - 5) / 2)
            pdf.set_text_color(*C_RED if is_podium else C_TEXT)
            pdf.set_font("helvetica", "B" if is_podium else "", 9)
            pdf.cell(120, 5, f"  {row['Endpoint']}")

            pdf.set_xy(start_x + 140, y0 + (row_h - 5) / 2)
            pdf.set_text_color(*C_RED if is_podium else C_DARK)
            pdf.set_font("helvetica", "B", 9)
            pdf.cell(50, 5, str(int(row["Detecciones"])), align="C")

            sep_ys.append(y0 + row_h)
            pdf.set_xy(start_x, y0 + row_h)
            alt = not alt

        _flush_t10_seps()
        pdf.set_y(pdf.get_y())

    # ─────────────────────────────────────────────
    # SECCION: INCIDENCIAS ZABBIX (solo si la empresa tiene Zabbix)
    # ─────────────────────────────────────────────
    if has_zabbix:
        zabbix_problems = zabbix_problems or []

        title_h_z = 15
        header_h_z = 11
        row_h_z = 11
        rows_h_z = row_h_z if not zabbix_problems else len(zabbix_problems) * row_h_z
        required_h_z = title_h_z + header_h_z + rows_h_z

        if pdf.get_y() + required_h_z > pdf.page_break_trigger:
            pdf.add_page()

        pdf.set_text_color(*C_DARK)
        pdf.set_font("helvetica", "B", 18)
        pdf.cell(0, 15,
            "Incidencias Zabbix (En Tratamiento)", new_x=XPos.LMARGIN, new_y=YPos.NEXT,)

        pdf.ln(3)
        start_x = pdf.get_x()

        def _draw_zabbix_header():
            pdf.set_x(start_x)
            pdf.set_fill_color(*C_RED)
            pdf.set_text_color(*C_WHITE)
            pdf.set_font("helvetica", "B", 10)
            pdf.cell(15, 11, "#", border=0, fill=True, align="C")
            pdf.cell(40, 11, "Host", border=0, fill=True)
            pdf.cell(65, 11, "Problema", border=0, fill=True)
            pdf.cell(20, 11, "Ocurr.", border=0, fill=True, align="C")
            pdf.cell(25, 11, "Severidad", border=0, fill=True, align="C")
            pdf.cell(25, 11, "Última detección", border=0, fill=True, align="C",
                new_x=XPos.LMARGIN, new_y=YPos.NEXT,)

        _draw_zabbix_header()

        pdf.set_draw_color(226, 232, 240)
        pdf.set_line_width(0.1)

        if not zabbix_problems:
            row_h_e = 11
            y0 = pdf.get_y()
            pdf.set_fill_color(*C_WHITE)
            pdf.rect(start_x, y0, 190, row_h_e, "F")
            pdf.set_text_color(*C_GRAY)
            pdf.set_font("helvetica", "I", 9)
            pdf.set_xy(start_x, y0 + 3)
            pdf.cell(190, 5, "Sin incidencias suprimidas/reconocidas en el periodo.", align="C",)
            pdf.set_draw_color(226, 232, 240)
            pdf.set_line_width(0.4)
            pdf.line(start_x, y0 + row_h_e, start_x + 190, y0 + row_h_e)
            pdf.ln(row_h_e)
        else:
            alt = False
            sep_ys = []

            def _flush_z_seps():
                pdf.set_draw_color(0, 0, 0)
                pdf.set_line_width(0.1)
                for sy in sep_ys:
                    pdf.line(start_x, sy, start_x + 190, sy)
                sep_ys.clear()

            for i, p in enumerate(zabbix_problems):
                pos = i + 1

                if pdf.get_y() + row_h_z > pdf.page_break_trigger:
                    _flush_z_seps()
                    pdf.add_page()
                    _draw_zabbix_header()
                    alt = False

                y0 = pdf.get_y()
                pdf.set_fill_color((241, 245, 249) if alt else C_WHITE)
                pdf.rect(start_x, y0, 190, row_h_z, "F")

                # Badge redondo con el numero de fila, igual que en Cuarentena/Top10
                badge_cx = start_x + 7.5
                badge_cy = y0 + row_h_z / 2
                badge_r = 3.6
                pdf.set_draw_color(203, 213, 225)
                pdf.set_line_width(0.25)
                pdf.ellipse(badge_cx - badge_r, badge_cy - badge_r, badge_r * 2, badge_r * 2, "D")

                pdf.set_text_color(*C_GRAY)
                pdf.set_font("helvetica", "B", 8)
                pdf.set_xy(start_x, badge_cy - 2.3)
                pdf.cell(15, 4.6, str(pos), align="C")

                pdf.set_text_color(*C_TEXT)
                pdf.set_font("helvetica", "", 8)
                text_y = y0 + (row_h_z - 5) / 2

                pdf.set_xy(start_x + 15, text_y)
                pdf.cell(40, 5, str(p["host"])[:24])

                pdf.set_xy(start_x + 55, text_y)
                pdf.cell(65, 5, str(p["name"])[:44])

                pdf.set_font("helvetica", "B", 8)
                pdf.set_xy(start_x + 120, text_y)
                pdf.cell(20, 5, str(p["occurrences"]), align="C")

                pdf.set_font("helvetica", "", 8)
                pdf.set_xy(start_x + 140, text_y)
                pdf.cell(25, 5, str(p["severity"]), align="C")

                fecha_str = p["date"].strftime("%d/%m/%y") if p.get("date") else "N/D"
                pdf.set_xy(start_x + 165, text_y)
                pdf.cell(25, 5, fecha_str, align="C")

                sep_ys.append(y0 + row_h_z)
                pdf.set_xy(start_x, y0 + row_h_z)
                alt = not alt

            _flush_z_seps()
            pdf.set_y(pdf.get_y())

    if period_start:
        mmaa = period_start.strftime("%m%y")
    else:
        mmaa = datetime.now().strftime("%m%y")
    out_name = ("Informe_"f"{re.sub(r'[^A-Za-z0-9_-]', '_', company)}_{mmaa}.pdf")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR,out_name)
    pdf.output(out_path)
    return out_path