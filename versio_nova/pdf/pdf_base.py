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
            if os.path.exists(logo_encabezado):
                self.image(logo_encabezado,x=160,y=8,w=35)
            self.set_font("helvetica","B",10)
            self.set_text_color(150,150,150)
            self.set_y(15)
            self.cell(0,10,"Informe de Seguridad de Endpoints",align="L")
            self.ln(10)

    def footer(self):
        if self.page_no() == 1: return
        self.set_y(-15)
        self.set_font("helvetica","I",8)
        self.set_text_color(128,128,128)
        self.cell(0,10,f"Página {self.page_no()}", align="C")


C_DARK = (15,23,42)
C_DARK2 = (24,35,61)
C_RED = (225,29,72)
C_RED2 = (190,18,60)
C_GRAY = (100,116,139)
C_LIGHT = (248,250,252)
C_WHITE = (255,255,255)
C_TEXT = (30,41,59)
C_MUTED = (148,163,184)
# Azul marino de acento para graficos: misma familia que C_DARK2 (portada)
# pero mas claro y saturado, para que no se lea como negro en superficies
# pequeñas (barras, chips de leyenda, etc.)
C_NAVY = (41,64,120)

THREAT_COLORS = [
    C_RED,    # rojo primario (igual que la portada)
    C_NAVY,   # azul marino (variante clara, para graficos)
    C_RED2,   # rojo oscuro
    C_MUTED,  # azul-gris claro
    C_GRAY,   # azul-gris medio
]