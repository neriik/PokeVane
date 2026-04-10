import streamlit as st
import cv2
import numpy as np
import pytesseract
from pokemontcgsdk import Card
import re

# --- CONFIGURACIÓN ---
TIPO_CAMBIO = 18.20
st.set_page_config(page_title="PokéVane Gold ✨", page_icon="⚡", layout="centered")

# --- CSS LOOK ELÉCTRICO ---
st.markdown("""
    <style>
    .main { background-color: #000000; color: #ffcb05; }
    [data-testid="stMetricValue"] { color: #000000 !important; font-family: 'Arial Black'; font-size: 35px; }
    div[data-testid="stMetric"] { 
        background-color: #ffcb05; 
        padding: 20px; 
        border-radius: 20px; 
        border: 3px solid #3b4cca;
        box-shadow: 0px 5px 15px rgba(255, 203, 5, 0.4);
    }
    h1 { color: #ffcb05; text-shadow: 2px 2px #3b4cca; font-family: 'Arial Black'; text-align: center; }
    .stAlert { border-radius: 20px; border: 2px solid #ffcb05; background-color: #111111; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ PokéVane Gold Edition")

# --- BIENVENIDA ---
col_j, col_t = st.columns([1, 4])
with col_j:
    st.image("https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/135.png", width=80)
with col_t:
    st.write("### ✨ ¡Hola Vane! \nSube una foto de tu galería o busca tu carta manualmente.")

st.divider()

# --- PESTAÑAS ---
tab_gal, tab_manual = st.tabs(["📁 Subir de Galería", "⌨️ Búsqueda Manual"])
foto_vane = None
manual_ready = False

with tab_gal:
    galeria = st.file_uploader("Selecciona la mejor foto de tu iPhone", type=['jpg', 'jpeg', 'png'])
    if galeria: foto_vane = galeria

with tab_manual:
    st.write("### ⌨️ Datos de la carta")
    m_nom = st.text_input("Nombre del Pokémon", placeholder="Ej: Arcanine")
    m_num = st.text_input("Número de carta", placeholder="Ej: 32")
    m_tot = st.text_input("Total del set (Opcional)", placeholder="Ej: 198")
    if st.button("Buscar ahora 🔍"):
        manual_ready
