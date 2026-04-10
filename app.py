import streamlit as st
import cv2
import numpy as np
import pytesseract
from pokemontcgsdk import Card
import re # Para limpieza extra

# --- CONFIGURACIÓN ESTÉTICA Y DE TEMA ---
TIPO_CAMBIO = 18.20

# Ponemos la página en modo ancho y con un título divertido
st.set_page_config(page_title="PokéVane Gold ✨", page_icon="⚡", layout="centered")

# CSS personalizado para un tema oscuro y eléctrico
st.markdown("""
    <style>
    /* Fondo negro para toda la app */
    .main { background-color: #000000; color: #ffcb05; }
    
    /* Estilo para las métricas (precios) */
    [data-testid="stMetricValue"] { color: #000000 !important; font-family: 'Arial Black'; font-size: 35px; }
    [data-testid="stMetricLabel"] { color: #555555 !important; font-weight: bold; }
    div[data-testid="stMetric"] { 
        background-color: #ffcb05; 
        padding: 20px; 
        border-radius: 20px; 
        box-shadow: 0px 5px 15px rgba(255, 203, 5, 0.3);
        border: 2px solid #3b4cca;
    }

    /* Títulos y textos */
    h1 { color: #ffcb05; text-shadow: 2px 2px #3b4cca; font-family: 'Arial Black'; text-align: center; }
    h3 { color: #ffcb05; }
    .stAlert { border-radius: 20px; border: 2px solid #ffcb05; background-color: #111111; color: #ffcb05; }
    
    /* Pestañas */
    .stTabs [data-baseweb="tab-list"] { background-color: #111111; border-radius: 10px; }
    .stTabs [data-baseweb="tab"] { color: #ffcb05; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { background-color: #3b4cca; border-radius: 10px; }

    /* Divisores */
    hr { border: 1px solid #3b4cca; }
    
    /* Imagen de Jolteon celebrando */
    .jolteon-celebra {
        text-align: center;
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# Título y Bienvenida
st.title("⚡ PokéVane Gold Edition")

# --- MINI COMPAÑERO DE ENTRADA (Solo Jolteon) ---
col_jolteon_mini, col_text_mini = st.columns([1, 10]) # Jolteon es el principal
with col_jolteon_mini:
    st.image("https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/135.png", width=50) # Jolteon
with col_text_mini:
    st.write("### ✨ ¡Hola Vane! Listos para valuar tus cartas.")

st.divider()

# --- MENÚ DE ENTRADA ---
tab_galeria, tab_camara = st.tabs(["📁 Subir de Galería", "📸 Usar Cámara"])

foto_vane = None

with tab_galeria:
    galeria = st.file_uploader("Elige la foto más nítida de tu iPhone", type=['jpg', 'jpeg', 'png'])
    if galeria: foto_vane = galeria

with tab_camara:
    st.info("💡 Consejo: Para mejor enfoque, toma la foto primero con tu cámara normal y súbela en la otra pestaña.")
    camara = st.camera_input("Escanear")
    if camara: foto_vane = camara

# --- LÓGICA DE PROCESAMIENTO ---
if foto_vane:
    try:
        # Procesamiento de imagen
        file_bytes = np.asarray(bytearray(foto_vane.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, 1)
        img_redim = cv2.resize(img, (1000, 1400))
        
        # Recortes (Los que funcionaron perfecto)
        rec_nombre = img_redim[40:160, 150:800]
        rec_numero = img_redim[1305:1345, 100:450] 

        def filtro_vane(crop):
            gris = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            return cv2.convertScaleAbs(gris, alpha=1.5, beta=10)

        nom_f = filtro_vane(rec_nombre)
        num_f = filtro_vane(rec_numero)

        # Lectura
        nombre_txt = pytesseract.image_to_string(nom_f, config='--psm 3').strip()
        numero_txt = pytesseract.image_to_string(num_f, config='--psm 3').strip()

        # Limpieza
        nombre_limpio = "".join(filter(str.isalpha, nombre_txt))
        if any(x in nombre_txt.lower() for x in ["krok", "rokor", "korok"]):
            nombre_limpio = "Krokorok"
        
        solo_num = "".join(filter(str.isdigit, numero_txt.split('/')[0] if '/' in numero_txt else numero_txt))
        if len(solo_num) > 3: solo_num = solo_num[:3]
        solo_num = solo_num.lstrip('0')

        if len(nombre_limpio) > 2:
            with st.spinner('🌟 ¡Consultando la Pokédex de precios...!'):
                res = Card.where(q=f'name:"{nombre_limpio}" number:"{solo_num}"')
                
                if not res:
                    res = Card.where(q=f'name:"{nombre_limpio}"')
                
                if res:
                    c = res[0]
                    
                    st.success(f"### 🔴 ¡CARTA LOCALIZADA! 🔴") # Usamos 🔴 como Pokébola
                    st.divider()
                    
                    # --- MOSTRAR IMAGEN DE LA CARTA ---
                    st.markdown("### ✨ ¡Tus amigos están celebrando! ✨")
                    col_carta, col_info = st.columns([1, 2])
                    with col_carta:
                        # Imagen oficial de la carta
                        st.image(c.images.large, caption=c.name, use_column_width=True)
                    with col_info:
                        st.write(f"**Nombre:** {c.name}")
                        st.write(f"**Expansión:** {c.set.name} (#{c.number}/{c.set.printedTotal})")
                    st.divider()
                    
                    # Precios
                    precios = c.tcgplayer.prices if c.tcgplayer else None
                    p = None
                    if precios:
                        p = getattr(precios, 'normal', None) or getattr(precios, 'holofoil', None) or getattr(precios, 'reverseHolofoil', None)
                    
                    if p and hasattr(p, 'market'):
                        val_usd = p.market
                        val_mxn = val_usd * TIPO_CAMBIO
                        
                        # --- JOLTEON CELEBRANDO ---
                        # Jolteon de PokeAPI celebrando con una Pokébola
                        st.markdown("<div class='jolteon-celebra'>", unsafe_allow_html=True)
                        st.image("https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/135.png", width=200)
                        st.caption("¡Jolteon usó Trueno en los precios!")
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        # --- MÉTRICAS BONITAS (AMARILLAS CON TEXTO NEGRO) ---
                        m1, m2 = st.columns(2)
                        m1.metric("PRECIO MXN", f"${val_mxn:.2f}")
                        m2.metric("PRECIO USD", f"${val_usd:.2f}")
                        st.caption("✨ Precios de mercado actuales (TCGPlayer)")
                    else:
                        st.warning("💎 Carta identificada, pero no tiene precio de mercado hoy.")
                else:
                    st.error("❌ No encontré esa carta. Intenta con una foto más clara.")
        
        # Detalles técnicos (Escondidos por default)
        with st.expander("🛠️ Ver ajustes técnicos"):
            st.image(nom_f, caption=f"Lectura Nombre: {nombre_limpio}")
            st.image(num_f, caption=f"Lectura Número: {solo_num}")

    except Exception as e:
        st.error(f"¡Ups! Algo falló: {str(e)}")
