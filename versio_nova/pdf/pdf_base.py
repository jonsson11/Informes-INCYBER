import os
import unicodedata
from fpdf import FPDF
from config import logo_encabezado


def _sanitize_text(text):
    """
    Los datos que llegan de BitDefender (nombres de malware, rutas de
    archivos, nombres de equipo, etc.) a veces traen caracteres Unicode
    (comillas tipográficas, guiones largos, emojis, texto en otros
    alfabetos...) que la fuente "helvetica" (fuente core del PDF, solo
    soporta Latin-1) no puede representar. Sin esto, fpdf2 lanza
    FPDFUnicodeEncodingException y se cae la generación del informe.

    Esta función normaliza los caracteres "tipográficos" habituales a su
    equivalente ASCII y, para cualquier otro caracter que siga sin caber
    en Latin-1, lo sustituye por "?" en lugar de reventar el informe.
    """
    if text is None:
        return text
    if not isinstance(text, str):
        text = str(text)

    replacements = {
        "\u2018": "'", "\u2019": "'",   # comillas simples tipográficas
        "\u201c": '"', "\u201d": '"',   # comillas dobles tipográficas
        "\u2013": "-", "\u2014": "-",   # en dash / em dash
        "\u2026": "...",                # puntos suspensivos
        "\u00a0": " ",                   # espacio de no separación
        "\u2022": "-",                   # bullet
        "\ufeff": "",                    # BOM
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)

    # Intenta descomponer acentos/diacriticos "raros" (ej. alfabetos con
    # combining marks) a su forma mas simple antes del fallback final.
    text = unicodedata.normalize("NFKC", text)

    # Cualquier caracter que aun asi no quepa en Latin-1 (emojis, CJK,
    # cirilico, etc.) se sustituye por "?" en vez de romper el PDF.
    return text.encode("latin-1", errors="replace").decode("latin-1")


class PDF(FPDF):
    def cell(self, w=None, h=None, text="", *args, **kwargs):
        return super().cell(w, h, _sanitize_text(text), *args, **kwargs)

    def multi_cell(self, w, h=None, text="", *args, **kwargs):
        return super().multi_cell(w, h, _sanitize_text(text), *args, **kwargs)

    def get_string_width(self, text, *args, **kwargs):
        return super().get_string_width(_sanitize_text(text), *args, **kwargs)

    def header(self):
        if self.page_no() > 1:
            # Fondo de pagina en gris muy claro (igual que las tarjetas
            # blancas de contenido resalten con un borde/sombra sutil,
            # tal y como se aprobo en las maquetas de estilo).
            self.set_fill_color(*C_PAGE_BG)
            self.rect(0, 0, 210, 297, "F")

            if os.path.exists(logo_encabezado):
                self.image(logo_encabezado,x=15,y=8,w=26)
            self.set_font("helvetica","B",8)
            self.set_text_color(*C_MUTED)
            self.set_xy(0,11)
            self.cell(195,6,"INFORME MENSUAL DE CIBERSEGURIDAD",align="R")
            # Filete magenta bajo la cabecera (acento de marca)
            self.set_draw_color(*C_MAGENTA)
            self.set_line_width(0.6)
            self.line(15,21,195,21)
            self.set_y(25)

    def footer(self):
        if self.page_no() == 1: return
        self.set_draw_color(*C_BORDER)
        self.set_line_width(0.2)
        self.line(15,282,195,282)
        self.set_y(-15)
        self.set_font("helvetica","",8)
        self.set_text_color(*C_MUTED)
        self.set_x(15)
        self.cell(90,10,"INCYBER \u00b7 Ciberseguridad Industrial",align="L")
        self.set_x(105)
        self.cell(90,10,f"Pagina {self.page_no()}",align="R")


# --------------------------------------------------
# PALETA DE MARCA INCYBER (Manual d'identitat corporativa)
# --------------------------------------------------
# Los nombres historicos (C_DARK, C_RED, ...) se conservan para no romper
# el resto del codigo, pero ahora apuntan a los colores oficiales de marca
# en vez de al rojo/negro de la version anterior.

C_NAVY = (33,44,84)          # #212C54 - Pantone 2757, color primario
C_NAVY_LIGHT = (59,72,128)   # variante clara del navy, para acentos/graficos
C_MAGENTA = (229,0,124)      # #E5007C - Pantone 226, color primario (acento)
C_MAGENTA_DARK = (153,0,84)  # variante oscura del magenta (texto sobre tinta)
C_MAGENTA_TINT = (251,234,243)  # magenta muy claro, fondo de badges/podio
C_YELLOW = (255,208,10)      # #FFD00A - Pantone 109, color de acento (usar poco)
C_GREEN = (22,163,74)        # verde semantico (solo para estado "resuelto")

C_GRAY = (90,97,120)         # texto secundario
C_MUTED = (154,160,180)      # texto terciario / hints
C_BORDER = (231,232,238)     # bordes finos de tarjetas y tablas
C_LIGHT = (246,247,251)      # fondo de tarjeta clara
C_LIGHT_ROW = (241,242,247)  # fila alterna (zebra) de tablas
C_PAGE_BG = (246,247,251)    # fondo de pagina en paginas de contenido
C_WHITE = (255,255,255)
C_TEXT = (59,66,88)          # texto de cuerpo

# Alias retrocompatibles (mismo nombre, valor de marca nuevo)
C_DARK = C_NAVY
C_DARK2 = C_NAVY_LIGHT
C_RED = C_MAGENTA
C_RED2 = C_MAGENTA_DARK

THREAT_COLORS = [
    C_MAGENTA,      # magenta primario (igual que la portada)
    C_NAVY,         # azul marino
    C_MUTED,        # gris azulado claro
    C_NAVY_LIGHT,   # azul marino claro
    C_GRAY,         # gris azulado medio
]