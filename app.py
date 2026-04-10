import streamlit as st
import cv2
import numpy as np
import pytesseract
from pokemontcgsdk import Card
import re

# --- CONFIGURACIÓN ---
TIPO_CAMBIO = 18.20
st.set_page_config(page_title="PokéVane Gold ✨", page_icon="⚡", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #000000; color: #ffcb05; }
    [data-testid="stMetricValue"] { color: #000000 !important; font-family: 'Arial Black'; font-size: 35px; }
    div[data-testid="stMetric"] { background-color: #ffcb05; padding: 20px; border-radius: 20px; border: 3px solid #3b4cca; }
    h1 { color: #ffcb05; text-shadow: 2px 2px #3b4cca; font-family: 'Arial Black'; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ PokéVane Gold Edition")

# --- BIENVENIDA ---
col_j, col_t = st.columns([1, 4])
with col_j:
    st.image("https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/135.png", width=80)
with col_t:
    st.write("### ✨ ¡Hola Vane! \nEstamos ajustando la puntería para leer tus cartas.")

st.divider()

# --- PESTAÑAS ---
tab_gal, tab_manual = st.tabs(["📁 Subir de Galería", "⌨️ Búsqueda Manual"])
foto_vane = None
manual_ready = False

with tab_gal:
    galeria = st.file_uploader("Selecciona la foto de tu iPhone", type=['jpg', 'jpeg', 'png'])
    if galeria: foto_vane = galeria

with tab_manual:
    m_nom = st.text_input("Nombre")
    m_num = st.text_input("Número")
    if st.button("Buscar ahora 🔍"): manual_ready = True

# --- MOTOR DE PROCESAMIENTO REPARADO ---
if foto_vane or manual_ready:
    try:
        nombre_l, numero_l, total_l = "", "", ""

        if manual_ready:
            nombre_l, numero_l = m_nom, m_num
        else:
            file_bytes = np.asarray(bytearray(foto_vane.read()), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, 1)
            img_redim = cv2.resize(img, (1000, 1400))
            gris = cv2.cvtColor(img_redim, cv2.COLOR_BGR2GRAY)

            # --- NUEVA LÓGICA DE FILTRADO ---
            # Nombre: Recorte + Aumento de tamaño + Umbral
            rec_nom = gris[35:160, 150:850]
            rec_nom = cv2.resize(rec_nom, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
            _, bin_nom = cv2.threshold(rec_nom, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Número: Recorte + Inversión de color (Muy importante para letras blancas)
            rec_num = gris[1300:1375, 50:600]
            rec_num = cv2.resize(rec_num, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
            # Invertimos para que el número blanco se vuelva negro
            inv_num = cv2.bitwise_not(rec_num)
            # Usamos umbral adaptativo para no perder detalles finos
            bin_num = cv2.adaptiveThreshold(inv_num, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

            # Lectura Tesseract
            nombre_l = pytesseract.image_to_string(bin_nom, config='--psm 7').strip()
            num_raw = pytesseract.image_to_string(bin_num, config='--psm 7').strip()

            # Limpieza de texto
            nombre_l = "".join(filter(str.isalpha, nombre_l.split()[0] if nombre_l else ""))
            if "krok" in nombre_l.lower(): nombre_l = "Krokorok"
            if "cacne" in nombre_l.lower(): nombre_l = "Cacnea"

            # Limpieza de números
            nums = re.findall(r'\d+', num_raw)
            if len(nums) >= 2:
                numero_l, total_l = nums[0].lstrip('0'), nums[1]
            elif len(nums) == 1:
                numero_l = nums[0].lstrip('0')

            with st.expander("🛠️ Detalles Técnicos"):
                st.image(bin_nom, caption=f"Leído: {nombre_l}")
                st.image(bin_num, caption=f"Leído: {numero_l} de {total_l}")

        # --- BÚSQUEDA ---
        if len(nombre_l) >= 2:
            with st.spinner('🌟 Buscando...'):
                # Intento 1: Nombre + Número + Total
                q = f'name:"{nombre_l}" number:"{numero_l}"'
                if total_l: q += f' set.printedTotal:{total_l}'
                res = Card.where(q=q)
                
                # Intento 2: Nombre + Número (Flexible)
                if not res:
                    res = Card.where(q=f'name:"{nombre_l}" number:"{numero_l}"')

                if res:
                    c = res[0]
                    st.success(f"### 🔴 ¡LOCALIZADA! 🔴")
                    col1, col2 = st.columns([1, 1.2])
                    with col1:
                        st.image(c.images.large)
                    with col2:
                        st.write(f"### {c.name}")
                        st.write(f"**Set:** {c.set.name}")
                        st.write(f"**Serie:** #{c.number}/{c.set.printedTotal}")
                        st.write(f"**💎 Rareza:** {c.rarity}")
                    
                    st.divider()
                    # Precios
                    p = None
                    if c.tcgplayer and c.tcgplayer.prices:
                        pr = c.tcgplayer.prices
                        p = getattr(pr, 'holofoil', None) or getattr(pr, 'normal', None) or getattr(pr, 'reverseHolofoil', None)
                    
                    if p and hasattr(p, 'market'):
                        v_usd = p.market
                        m1, m2 = st.columns(2)
                        m1.metric("PRECIO MXN", f"${v_usd * TIPO_CAMBIO:.2f}")
                        m2.metric("PRECIO USD", f"${v_usd:.2f}")
                else:
                    st.error(f"No encontré a {nombre_l} #{numero_l}. Prueba el buscador manual.")
    except Exception as e:
        st.error(f"Error: {e}")
