from fpdf.enums import XPos, YPos
from pdf.pdf_base import (C_NAVY,C_MAGENTA,C_MAGENTA_TINT,C_GRAY,C_TEXT,C_WHITE,C_BORDER,C_LIGHT,)


def kpi_card(pdf,x,y,w,h,title,value, subtitle = None, icon = None):

    # Tarjeta blanca con borde fino y esquinas redondeadas (mismo
    # lenguaje visual que las tarjetas del informe/manual de marca),
    # con un filete magenta superior en vez de la barra lateral roja.
    pdf.set_draw_color(*C_BORDER)
    pdf.set_line_width(0.25)
    pdf.set_fill_color(*C_WHITE)
    pdf.rect(x, y, w, h, "FD", round_corners=True, corner_radius=2.2)
    pdf.set_fill_color(*C_MAGENTA)
    pdf.rect(x, y, w, 1.1, "F")

    pdf.set_xy(x + 5,y + 4)
    pdf.set_font("helvetica","B",7)
    pdf.set_text_color(*C_GRAY)
    pdf.cell(w - 10, 5, title.upper())
    pdf.set_xy(x + 5,y + 10)
    pdf.set_font("helvetica","B",18)
    pdf.set_text_color(*C_NAVY)
    pdf.cell(w - 10, 10, str(value))
    if icon:
        icon_size = 6
        value_w = pdf.get_string_width(str(value))
        icon_x = x + 5 + value_w + 4
        icon_y = y + 10 + (10 - icon_size) / 2
        pdf.image(icon, x=icon_x, y=icon_y, w=icon_size, h=icon_size)
    if subtitle:
        pdf.set_xy(x + 5, y + 19)
        pdf.set_font("helvetica", "", 7)
        pdf.set_text_color(*C_GRAY)
        pdf.cell(w - 10, 5, str(subtitle))


def section_card(pdf, x, y, w, h,title):

    pdf.set_draw_color(*C_BORDER)
    pdf.set_line_width(0.25)
    pdf.set_fill_color(*C_WHITE)
    pdf.rect(x, y, w, h, "FD", round_corners=True, corner_radius=2.2)
    pdf.set_fill_color(*C_MAGENTA)
    pdf.rect(x, y, w, 1.1, "F")
    pdf.set_xy(x + 6, y + 5)
    pdf.set_font("helvetica", "B",8)
    pdf.set_text_color(*C_GRAY)
    pdf.cell(w - 10,5,title.upper())


def upsell_card(pdf, x, y, w, h, service_name, description, benefits):
    """
    Tarjeta de "venta cruzada" que se muestra en lugar de una seccion de
    datos (BitDefender o Zabbix) cuando la empresa no tiene ese servicio
    contratado. Usa el mismo lenguaje visual que el resto del informe
    (tarjeta blanca, filete magenta superior, radios de esquina) pero con
    un borde discontinuo para marcar visualmente que es contenido
    informativo/comercial y no un bloque de datos reales.
    """
    pdf.set_dash_pattern(dash=1.5, gap=1.2)
    pdf.set_draw_color(*C_BORDER)
    pdf.set_line_width(0.35)
    pdf.set_fill_color(*C_LIGHT)
    pdf.rect(x, y, w, h, "FD", round_corners=True, corner_radius=3)
    pdf.set_dash_pattern(dash=0, gap=0)

    pdf.set_fill_color(*C_MAGENTA)
    pdf.rect(x, y, w, 1.4, "F")

    pad = 11
    inner_w = w - 2 * pad
    cy = y + 14

    # Badge "SERVICIO NO CONTRATADO"
    pdf.set_xy(x + pad, cy)
    pdf.set_font("helvetica", "B", 7.5)
    pdf.set_text_color(*C_MAGENTA)
    pdf.cell(inner_w, 5, "SERVICIO NO CONTRATADO")
    cy += 9

    pdf.set_xy(x + pad, cy)
    pdf.set_font("helvetica", "B", 16)
    pdf.set_text_color(*C_NAVY)
    pdf.cell(inner_w, 8, service_name)
    cy += 12

    pdf.set_xy(x + pad, cy)
    pdf.set_font("helvetica", "", 9.5)
    pdf.set_text_color(*C_TEXT)
    pdf.multi_cell(inner_w, 5.2, description)
    cy = pdf.get_y() + 5

    for benefit in benefits:
        pdf.set_fill_color(*C_MAGENTA)
        pdf.rect(x + pad, cy + 1.6, 2, 2, "F")
        pdf.set_xy(x + pad + 5, cy)
        pdf.set_font("helvetica", "", 9)
        pdf.set_text_color(*C_TEXT)
        pdf.multi_cell(inner_w - 5, 5, benefit)
        cy = pdf.get_y() + 2.5

    # CTA final, siempre anclado a la parte baja de la tarjeta
    cta_h = 16
    cta_y = y + h - cta_h - 9
    pdf.set_fill_color(*C_NAVY)
    pdf.rect(x + pad, cta_y, inner_w, cta_h, "F", round_corners=True, corner_radius=2)
    pdf.set_xy(x + pad + 4, cta_y)
    pdf.set_font("helvetica", "B", 9)
    pdf.set_text_color(*C_WHITE)
    pdf.multi_cell(
        inner_w - 8, 4.6,
        "Si quieres disponer de esta informacion en tus proximos informes, "
        "contacta con tu responsable de cuenta en INCYBER Technologies.",
        align="C",
    )