from pdf.pdf_base import (C_NAVY,C_MAGENTA,C_GRAY,C_WHITE,C_BORDER,)


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