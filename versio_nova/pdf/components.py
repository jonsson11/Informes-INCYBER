from pdf.pdf_base import (C_DARK,C_RED,C_GRAY,C_LIGHT,)


def kpi_card(pdf,x,y,w,h,title,value, subtitle = None, icon = None):

    pdf.set_fill_color(*C_LIGHT)
    pdf.rect(x, y, w, h, "F")
    pdf.set_fill_color(*C_RED)
    pdf.rect(x, y, 2, h, "F")
    pdf.set_xy(x + 5,y + 3)
    pdf.set_font("helvetica","B",7)
    pdf.set_text_color(*C_GRAY)
    pdf.cell(w - 10, 5, title.upper())
    pdf.set_xy(x + 5,y + 9)
    pdf.set_font("helvetica","B",18)
    pdf.set_text_color(*C_DARK)
    pdf.cell(w - 10, 10, str(value))
    if icon:
        icon_size = 6
        value_w = pdf.get_string_width(str(value))
        icon_x = x + 5 + value_w + 4
        icon_y = y + 9 + (10 - icon_size) / 2
        pdf.image(icon, x=icon_x, y=icon_y, w=icon_size, h=icon_size)
    if subtitle:
        pdf.set_xy(x + 5, y + 18) 
        pdf.set_font("helvetica", "", 7)
        pdf.set_text_color(*C_GRAY) 
        pdf.cell(w - 10, 5, str(subtitle))
    

def section_card(pdf, x, y, w, h,title):

    pdf.set_fill_color(*C_LIGHT)
    pdf.rect(x, y, w, h, "F")
    pdf.set_fill_color(*C_RED)
    pdf.rect(x, y, 2, h, "F")
    pdf.set_xy(x + 6, y + 4)
    pdf.set_font("helvetica", "B",8)
    pdf.set_text_color(*C_GRAY)
    pdf.cell(w - 10,5,title.upper())