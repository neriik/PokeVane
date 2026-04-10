import streamlit as st
import cv2
import numpy as np
import pytesseract
from pokemontcgsdk import Card
from PIL import Image
import re 
import traceback # Para ver el error real

# --- CONFIGURACIÓN ESTÉTICA Y DE TEMA ---
TIPO_CAMBIO = 18.20

st.set_page_config(page_title="PokéVane Gold ✨", page_icon="⚡", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #000000; color: #ffcb05; }
    [data-testid="stMetricValue"] { color: #000000 !important; font-family: 'Arial Black'; font-size: 35px; }
    [data-testid="stMetricLabel"] { color: #555555 !important; font-weight: bold; }
    div[data-testid="stMetric"] { 
        background-color: #ffcb05; 
        padding: 20px; 
        border-radius: 20px; 
        box-shadow: 0px 5px 15px rgba(255, 203, 5, 0.3);
        border: 2px solid #3b4cca;
    }
    h1 { color: #ffcb05; text-shadow: 2px 2px #3b4cca; font-family: 'Arial Black'; text-align: center; }
    h3 { color: #ffcb05; }
    .stAlert { border-radius: 20px; border: 2px solid #ffcb05; background-color: #111111; color: #ffcb05; }
    .stTabs [data-baseweb="tab-list"] { background-color: #111111; border-radius: 10px; }
    .stTabs [data-baseweb="tab"] { color: #ffcb05; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { background-color: #3b4cca; border-radius: 10px; }
    hr { border: 1px solid #3b4cca; }
    .jolteon-celebra { text-align: center; margin-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ PokéVane Gold Edition")

col_j, col_t = st.columns([1, 4])
with col_j:
    st.image("https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/135.png", width=50)
with col_t:
    st.write("### ✨ ¡Hola Vane! Listos para valuar tus cartas.")

st.divider()

tab_galeria, tab_manual = st.tabs(["📁 Subir de Galería", "⌨️ Búsqueda Manual"])

foto_vane = None
manual_ready = False

with tab_galeria:
    galeria = st.file_uploader("Elige la foto más nítida de tu iPhone", type=['jpg', 'jpeg', 'png'])
    if galeria: foto_vane = galeria

with tab_manual:
    m_nom = st.text_input("Nombre de la carta")
    m_num = st.text_input("Número")
    m_tot = st.text_input("Total del set")
    if st.button("Buscar manualmente 🔍"): manual_ready = True

# --- LÓGICA DE PROCESAMIENTO ---
if foto_vane or manual_ready:
    try:
        nombre_l, numero_l, total_l = "", "", ""

        if manual_ready:
            nombre_l, numero_l, total_l = m_nom, m_num, m_tot
        else:
            # --- NUEVO MOTOR DE LECTURA DE IMAGEN (PIL) ---
            imagen_pil = Image.open(foto_vane)
            img_array = np.array(imagen_pil)
            
            # Convertimos a escala de grises de forma segura
            if len(img_array.shape) == 3: # Si tiene color
                if img_array.shape[2] == 4: # Si tiene canal alpha (transparencia de iPhone)
                    img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
                gris = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gris = img_array
                
            img_redim = cv2.resize(gris, (1000, 1400))
            
            # --- PROCESAMIENTO QUIRÚRGICO DE DANTE ---
            # Nombre: Letras negras
            rec_nom_gris = img_redim[35:160, 150:850]
            _, bin_nom = cv2.threshold(rec_nom_gris, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Número: INVERSIÓN (Para letras blancas)
            rec_num_gris = img_redim[1300:1375, 50:600]
            inv_num = cv2.bitwise_not(rec_num_gris)
            _, bin_num = cv2.threshold(inv_num, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Lectura
            n_txt = pytesseract.image_to_string(bin_nom, config='--psm 7').strip()
            u_txt = pytesseract.image_to_string(bin_num, config='--psm 7').strip()

            nombre_l = "".join(filter(str.isalpha, n_txt.split()[0] if n_txt else ""))
            if "krok" in n_txt.lower(): nombre_l = "Krokorok"
            if "cacne" in n_txt.lower(): nombre_l = "Cacnea"
            if "arcan" in n_txt.lower(): nombre_l = "Arcanine"

            # Extraer números
            nums = re.findall(r'\d+', u_txt)
            if len(nums) >= 2:
                numero_l = nums[0].lstrip('0')
                total_l = nums[1]
                if not numero_l and nums[0]: numero_l = nums[0][-1]
            elif len(nums) == 1:
                numero_l = nums[0].lstrip('0')

            with st.expander("🛠️ Ver ajustes técnicos"):
                st.image(bin_nom, caption=f"Leído: {nombre_l}")
                st.image(bin_num, caption=f"Leído: {numero_l} / {total_l}")

        # --- BÚSQUEDA ---
        if len(nombre_l) >= 2:
            with st.spinner('🌟 ¡Consultando la Pokédex de precios...!'):
                q = f'name:"{nombre_l}" number:"{numero_l}"'
                if total_l: q += f' set.printedTotal:{total_l}'
                res = Card.where(q=q)
                
                if not res: res = Card.where(q=f'name:"{nombre_l}" number:"{numero_l}"')
                if not res: res = Card.where(q=f'name:"{nombre_l}"')
                
                if res:
                    c = res[0]
                    st.success(f"### 🔴 ¡CARTA LOCALIZADA! 🔴")
                    st.divider()
                    
                    st.markdown("### ✨ ¡Tus amigos están celebrando! ✨")
                    col_carta, col_info = st.columns([1, 2])
                    with col_carta:
                        st.image(c.images.large, caption=c.name, use_column_width=True)
                    with col_info:
                        st.write(f"**Nombre:** {c.name}")
                        st.write(f"**Expansión:** {c.set.name} (#{c.number}/{c.set.printedTotal})")
                        st.write(f"**💎 Rareza:** {c.rarity if c.rarity else 'Común'}")
                    st.divider()
                    
                    precios = c.tcgplayer.prices if c.tcgplayer else None
                    p = None
                    if precios:
                        p = getattr(precios, 'normal', None) or getattr(precios, 'holofoil', None) or getattr(precios, 'reverseHolofoil', None)
                    
                    if p and hasattr(p, 'market'):
                        val_usd = p.market
                        val_mxn = val_usd * TIPO_CAMBIO
                        
                        st.markdown("<div class='jolteon-celebra'>", unsafe_allow_html=True)
                        st.image("https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/135.png", width=200)
                        st.caption("¡Jolteon usó Trueno en los precios!")
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        m1, m2 = st.columns(2)
                        m1.metric("PRECIO MXN", f"${val_mxn:.2f}")
                        m2.metric("PRECIO USD", f"${val_usd:.2f}")
                        st.caption("✨ Precios de mercado actuales (TCGPlayer)")
                    else:
                        st.warning("💎 Carta identificada, pero no tiene precio de mercado hoy.")
                else:
                    st.error("❌ No encontré esa carta. Intenta la búsqueda manual.")
        else:
            if foto_vane: st.warning("⚠️ No pude leer el nombre. Asegúrate de enfocar bien.")

    except Exception as e:
        st.error("❌ Ocurrió un error técnico al procesar la imagen.")
        with st.expander("🛠️ Detalles del error para Neri (Desarrollador)"):
            st.code(traceback.format_exc())
