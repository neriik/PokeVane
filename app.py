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

col_j, col_t = st.columns([1, 4])
with col_j:
    st.image("https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/135.png", width=80)
with col_t:
    st.write("### ✨ ¡Hola Vane! \nSubre tu foto y deja que Jolteon haga su magia.")

st.divider()

tab_gal, tab_manual = st.tabs(["📁 Subir de Galería", "⌨️ Búsqueda Manual"])
foto_vane = None
manual_ready = False

with tab_gal:
    galeria = st.file_uploader("Selecciona la mejor foto", type=['jpg', 'jpeg', 'png'])
    if galeria: foto_vane = galeria

with tab_manual:
    m_nom = st.text_input("Nombre")
    m_num = st.text_input("Número")
    m_tot = st.text_input("Total del set")
    if st.button("Buscar ahora 🔍"): manual_ready = True

if foto_vane or manual_ready:
    try:
        nombre_l, numero_l, total_l = "", "", ""

        if manual_ready:
            nombre_l, numero_l, total_l = m_nom, m_num, m_tot
        else:
            file_bytes = np.asarray(bytearray(foto_vane.read()), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, 1)
            img_redim = cv2.resize(img, (1000, 1400))
            
            # --- FILTRO SUTIL Y NATURAL ---
            gris = cv2.cvtColor(img_redim, cv2.COLOR_BGR2GRAY)
            # Solo aumentamos el brillo ligeramente sin quemar el contraste
            # Antes alpha=1.7, ahora alpha=1.2 (suave)
            final_img = cv2.convertScaleAbs(gris, alpha=1.2, beta=15)

            # Recortes
            rec_nom = final_img[35:160, 150:850]
            rec_num = final_img[1300:1375, 50:600]
            
            n_txt = pytesseract.image_to_string(rec_nom, config='--psm 3').strip()
            # PSM 7 es mejor para una sola línea de texto
            u_txt = pytesseract.image_to_string(rec_num, config='--psm 7').strip()

            # Limpieza básica
            nombre_l = "".join(filter(str.isalpha, n_txt.split()[0] if n_txt else ""))
            if "krok" in n_txt.lower(): nombre_l = "Krokorok"
            if "cacne" in n_txt.lower(): nombre_l = "Cacnea"

            # --- CORRECCIÓN DE NÚMEROS MEJORADA ---
            nums = re.findall(r'\d+', u_txt)
            if len(nums) >= 2:
                numero_l = nums[0].lstrip('0')
                total_l = nums[1]
                # Si el número quedó vacío porque era '000', le ponemos el último dígito
                if not numero_l and nums[0]: numero_l = nums[0][-1] 
            elif len(nums) == 1:
                # Si solo detectó un bloque de números, intentamos separarlo
                # Esto es útil si leyó algo como '005198'
                n = nums[0]
                if len(n) > 3:
                    numero_l = n[:len(n)-3].lstrip('0')
                    total_l = n[len(n)-3:]
                else:
                    numero_l = n.lstrip('0')

            with st.expander("🛠️ Detalles Técnicos"):
                st.image(rec_nom, caption=f"Leído: {nombre_l}")
                st.image(rec_num, caption=f"Leído: {numero_l} de {total_l}")

        if len(nombre_l) >= 2:
            with st.spinner('Buscando...'):
                # Intento 1: Exacto (Nombre + Número + Total del set)
                q = f'name:"{nombre_l}" number:"{numero_l}"'
                if total_l: q += f' set.printedTotal:{total_l}'
                res = Card.where(q=q)
                
                if not res:
                    # Intento 2: Solo nombre y numero (Flexible)
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
                        st.write(f"**ID:** #{c.number}/{c.set.printedTotal}")
                        st.write(f"**💎 Rareza:** {c.rarity if c.rarity else 'Común'}")
                    
                    st.divider()
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
                        st.warning("Sin precio disponible.")
                else:
                    st.error("No se encontró la carta exacta.")
    except Exception as e:
        st.error(f"Error: {e}")
