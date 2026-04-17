import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
import io
import csv
import os

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Dashboard El Tejar", layout="wide", page_icon="🏭")

# --- ESTILOS PERSONALIZADOS (CSS) - SLATE LIGHT THEME ---
st.markdown("""
<style>
    /* Fondo gris claro para no fatigar la vista */
    .stApp { background-color: #f1f5f9; }
    
    /* Tarjetas de Noticias */
    .news-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 12px;
        border-left: 4px solid #eab308;
        margin-bottom: 15px;
        color: #0f172a;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        border: 1px solid #e2e8f0;
    }
    .news-title { font-size: 1.1rem; font-weight: bold; color: #d97706; margin-bottom: 5px; }
    .news-source { font-size: 0.8rem; color: #64748b; margin-bottom: 10px; }
    .news-snippet { font-size: 0.9rem; line-height: 1.4; color: #334155; }
    .read-more { color: #0284c7; text-decoration: none; font-size: 0.85rem; font-weight: bold;}
    .stDataFrame [data-testid="stTable"] { font-variant-numeric: tabular-nums; }
    
    /* Tarjetas KPI Principales */
    .kpi-card {
        background-color: #ffffff;
        padding: 20px 10px 15px 10px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        border: 1px solid #e2e8f0;
        border-top: 4px solid #65a30d; 
        margin-bottom: 20px;
        color: #0f172a;
    }
    .kpi-card.blue { border-top-color: #3b82f6; }
    .kpi-card.yellow { border-top-color: #eab308; }
    .kpi-card.orange { border-top-color: #f97316; }
    
    .kpi-icon { font-size: 32px; margin-bottom: 10px; }
    .kpi-title { color: #64748b; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 5px; }
    .kpi-value { color: #0f172a; font-size: 2.2rem; font-weight: 800; line-height: 1.1; }
    .kpi-unit { font-size: 1rem; color: #94a3b8; font-weight: 500; }
    
    .kpi-delta { font-size: 0.95rem; font-weight: 600; margin-top: 12px; padding-top: 10px; border-top: 1px solid #f1f5f9; }
    .delta-positive { color: #16a34a; } 
    .delta-negative { color: #dc2626; } 
    .delta-neutral { color: #64748b; font-weight: 400; } 
    
    /* Tarjetas Acumulado Mensual - Estilo Apilado */
    .monthly-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 18px 10px;
        text-align: center;
        border-top: 4px solid #94a3b8;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 15px;
        border-left: 1px solid #e2e8f0;
        border-right: 1px solid #e2e8f0;
        border-bottom: 1px solid #e2e8f0;
    }
    .monthly-card.blue { border-top-color: #3b82f6; }
    .monthly-card.yellow { border-top-color: #eab308; }
    .monthly-card.orange { border-top-color: #f97316; }
    
    .m-title { color: #64748b; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; margin-bottom: 8px; display: block; }
    .m-icon { font-size: 20px; margin-bottom: 5px; display: block; }
    .m-value { color: #0f172a; font-size: 1.8rem; font-weight: 800; line-height: 1.1; }
    .m-unit { font-size: 0.9rem; color: #94a3b8; font-weight: 500; }
</style>
""", unsafe_allow_html=True)

# --- SISTEMA DE DOBLE LOGIN ---
def check_password():
    if "login_ok" not in st.session_state:
        st.session_state["login_ok"] = False
        st.session_state["role"] = None
        
    if not st.session_state["login_ok"]:
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            if os.path.exists("Logo.png"):
                st.image("Logo.png", width=250)
            else:
                st.markdown("<div style='text-align: center; font-size: 4rem;'>🏭</div>", unsafe_allow_html=True)
            st.markdown("### 🔐 Acceso Privado - Oleícola El Tejar")
            usuario = st.text_input("Usuario (oficina / presidente)")
            password = st.text_input("Contraseña", type="password")
            if st.button("Entrar", use_container_width=True):
                if usuario == "presidente" and password == "Tejar2026":
                    st.session_state["login_ok"] = True
                    st.session_state["role"] = "presidente"
                    st.rerun()
                elif usuario == "oficina" and password == "Tejar2026":
                    st.session_state["login_ok"] = True
                    st.session_state["role"] = "oficina"
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")
        return False
    return True

# --- FUNCIONES DE MEMORIA ---
def save_file_to_disk(uploaded_file, date_obj):
    date_str = date_obj.isoformat()
    with open(f"parte_{date_str}.dat", "wb") as f:
        f.write(uploaded_file.getvalue())
    with open(f"parte_{date_str}_name.txt", "w") as f:
        f.write(uploaded_file.name)
    with open("ultima_fecha.txt", "w") as f:
        f.write(date_str)

def load_file_from_disk(date_obj):
    date_str = date_obj.isoformat()
    dat_path = f"parte_{date_str}.dat"
    name_path = f"parte_{date_str}_name.txt"
    if os.path.exists(dat_path) and os.path.exists(name_path):
        with open(name_path, "r") as f:
            name = f.read().strip()
        with open(dat_path, "rb") as f:
            content = f.read()
        file_obj = io.BytesIO(content)
        file_obj.name = name
        return file_obj
    return None

def load_last_date():
    if os.path.exists("ultima_fecha.txt"):
        try:
            with open("ultima_fecha.txt", "r") as f:
                return date.fromisoformat(f.read().strip())
        except: pass
    return date.today()

# --- MAPEO DE JERARQUÍAS ---
def format_names(series):
    return series.astype(str).str.strip().str.title().str.replace('Mw', 'MW', regex=False)

def get_centro_from_planta(planta_name):
    """Asigna instalaciones específicas a su Centro Matriz"""
    p_upper = str(planta_name).upper()
    if "BAENA" in p_upper: return "Baena"
    # Autogeneración, Vetejar y Algodonales pertenecen al complejo Palenciana
    if "VETEJAR" in p_upper or "ALGODONALES" in p_upper or "AUTOGENERACI" in p_upper: return "Palenciana"
    if "TEJAR" in p_upper: return "El Tejar"
    return format_names(pd.Series([planta_name])).iloc[0]

# --- SISTEMA DE OBJETIVOS ---
def load_objectives():
    if os.path.exists("objetivos_tejar.csv"):
        df = pd.read_csv("objetivos_tejar.csv")
        # Asegurar que el CSV antiguo hereda la nueva columna Centro para el Smart Filter
        if "Centro" not in df.columns:
            df["Centro"] = df["Planta"].apply(get_centro_from_planta)
        return df
    else:
        return pd.DataFrame({
            "Area": ["Centrifugacion", "Centrifugacion", "Centrifugacion", "Secado", "Secado", "Secado", "Secado", "Secado", "Extraccion", "Extraccion", "Electricidad", "Electricidad", "Electricidad", "Electricidad"],
            "Planta": ["Marchena", "Cabra", "Baena", "Palenciana", "Marchena", "Cabra", "Baena", "Espejo", "El Tejar", "Baena", "Vetejar 12.6 MW", "Baena 25 MW", "Algodonales 5.3 MW", "Autogeneración 5.7 MW"],
            "Centro": ["Marchena", "Cabra", "Baena", "Palenciana", "Marchena", "Cabra", "Baena", "Espejo", "El Tejar", "Baena", "Palenciana", "Baena", "Palenciana", "Palenciana"],
            "Metrica": ["Aceite (kg)", "Aceite (kg)", "Aceite (kg)", "OGS (kg)", "OGS (kg)", "OGS (kg)", "OGS (kg)", "OGS (kg)", "Aceite (kg)", "Aceite (kg)", "Energia (kWh)", "Energia (kWh)", "Energia (kWh)", "Energia (kWh)"],
            "Objetivo_Diario": [5251, 442, 1906, 148900, 272720, 288560, 313160, 181020, 43400, 18900, 190270, 358330, 91400, 60000]
        })

def save_objectives(df):
    df.to_csv("objetivos_tejar.csv", index=False)

def apply_objectives(df_cent, df_secado, df_ext, df_elec, df_obj):
    def merge_obj(df, join_col, area_name, obj_col_name):
        if df.empty or join_col not in df.columns: return df
        sub_obj = df_obj[df_obj["Area"] == area_name][["Planta", "Objetivo_Diario"]]
        sub_obj = sub_obj.rename(columns={"Planta": join_col, "Objetivo_Diario": obj_col_name})
        if obj_col_name in df.columns:
            df = df.drop(columns=[obj_col_name])
        return pd.merge(df, sub_obj, on=join_col, how="left")

    df_cent = merge_obj(df_cent, "Centro", "Centrifugacion", "Optimo")
    df_secado = merge_obj(df_secado, "Centro", "Secado", "Obj_OGS")
    df_ext = merge_obj(df_ext, "Extractora", "Extraccion", "Obj_Aceite")
    df_elec = merge_obj(df_elec, "Planta", "Electricidad", "Optimo_kWh")
    return df_cent, df_secado, df_ext, df_elec

# --- FUNCIONES DE LIMPIEZA Y HTML ---
def format_kpi_number(num):
    try:
        val = float(num)
        if val >= 1_000_000: return f"{val/1_000_000:.2f}M"
        elif val >= 1_000: return f"{val/1_000:.1f}k"
        else: return f"{val:,.0f}"
    except: return "0"

def get_delta_html(real, target):
    if not target or target == 0 or pd.isna(target):
        return "<div class='kpi-delta delta-neutral'>Sin objetivo definido</div>"
    diff = real - target
    pct = (diff / target) * 100
    if diff > 0: return f"<div class='kpi-delta delta-positive'>▲ +{format_kpi_number(diff)} (+{pct:.1f}%)</div>"
    elif diff < 0: return f"<div class='kpi-delta delta-negative'>▼ {format_kpi_number(diff)} ({pct:.1f}%)</div>"
    else: return "<div class='kpi-delta delta-neutral'>▬ Objetivo exacto</div>"

def get_kpi_card_html(title, icon, val, unit, delta_html, css_class=""):
    return f"""
    <div class="kpi-card {css_class}">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{format_kpi_number(val)}<span class="kpi-unit"> {unit}</span></div>
        {delta_html}
    </div>
    """

def get_monthly_card_html(title, icon, val, unit, css_class=""):
    return f"""
    <div class="monthly-card {css_class}">
        <span class="m-icon">{icon}</span>
        <span class="m-title">{title}</span>
        <div class="m-value">{format_kpi_number(val)}<span class="m-unit"> {unit}</span></div>
    </div>
    """

@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')

def display_styled_table(df, area="", download_name="datos.csv"):
    if df.empty: return
    df_clean = df.dropna(axis=1, how='all')
    if area == "Centrifugacion":
        def highlight(row):
            styles = [''] * len(row)
            if 'Acidez' in df_clean.columns:
                val = row['Acidez']
                if pd.notnull(val) and isinstance(val, (int, float)) and val > 3:
                    styles[df_clean.columns.get_loc('Acidez')] = 'background-color: rgba(239, 68, 68, 0.4); color: white;'
            return styles
        st.dataframe(df_clean.style.apply(highlight, axis=1).format(thousands=","), hide_index=True, use_container_width=True)
    else:
        st.dataframe(df_clean.style.format(thousands=","), hide_index=True, use_container_width=True)
    csv_data = convert_df(df_clean)
    st.download_button(label="📥 Descargar CSV", data=csv_data, file_name=download_name, mime='text/csv')

def fix_number(x):
    if pd.isna(x): return x
    if isinstance(x, str):
        x = x.strip()
        test_str = x.replace('-', '').replace(',', '').replace('.', '')
        if test_str.isdigit() and len(test_str) > 0:
            if x.count(',') > 1: x = x.replace(',', '')
            elif x.count('.') > 1: x = x.replace('.', '')
            elif ',' in x and '.' in x:
                if x.rfind(',') > x.rfind('.'): x = x.replace('.', '').replace(',', '.')
                else: x = x.replace(',', '')
            elif ',' in x: x = x.replace(',', '.')
    return x

# --- TRADUCTOR MÁGICO DE SUBIFOR ---
def parse_subifor_csv(df_raw):
    df_raw.columns = [str(c).lower().strip() for c in df_raw.columns]
    
    name_col = None
    for col in ['nombre_c', 'nombre', 'centro', 'planta', 'descripción', 'descripcion']:
        if col in df_raw.columns:
            name_col = col
            break
    if not name_col:
        if len(df_raw.columns) >= 5:
            name_col = df_raw.columns[4]
        else:
            raise ValueError("No se pudo encontrar la columna de nombre de la planta.")

    for col in ['actividad', 'actividad1', 'centro'] + [f'a{i}' for i in range(1, 14)]:
        if col in df_raw.columns:
            df_raw[col] = pd.to_numeric(df_raw[col], errors='coerce').fillna(0)
            
    # Aportaciones
    df_aport = df_raw[df_raw['actividad'] == 1][[name_col, 'a1', 'a2']].copy() if 'a1' in df_raw.columns else pd.DataFrame(columns=[name_col, 'a1', 'a2'])
    df_aport.rename(columns={name_col: 'Planta', 'a1': 'Hoy (kg)', 'a2': 'Acum. Mensual'}, inplace=True)
    df_aport['Planta'] = format_names(df_aport['Planta'])
    if not df_aport.empty:
        df_aport['Centro'] = df_aport['Planta'].apply(get_centro_from_planta)
        df_aport = df_aport[(df_aport['Hoy (kg)'] > 0) | (df_aport['Acum. Mensual'] > 0)]
    
    # Existencias
    df_ex = df_raw[df_raw['actividad'] == 0]
    hueso = df_ex['a1'].sum() if 'a1' in df_ex.columns else 0
    orujillo = df_ex['a2'].sum() if 'a2' in df_ex.columns else 0
    hoja = df_ex['a3'].sum() if 'a3' in df_ex.columns else 0
    df_existencias = pd.DataFrame({"Material": ["Hueso de Aceituna", "Orujillo", "Hoja de Olivo"], "Total Kilos": [hueso, orujillo, hoja]})
    
    # Centrifugación
    cond_in_cent = (df_raw['actividad'] == 2) | ((df_raw['actividad'] == 4) & (df_raw.get('actividad1', 0) == 1))
    df_c2 = df_raw[cond_in_cent][[name_col, 'a1']].rename(columns={name_col: 'Centro', 'a1': 'Entrada_Alperujo'}) if 'a1' in df_raw.columns else pd.DataFrame(columns=['Centro', 'Entrada_Alperujo'])
    
    cols_out_cent = [name_col]
    rename_cent = {name_col: 'Centro'}
    if 'a1' in df_raw.columns: cols_out_cent.append('a1'); rename_cent['a1'] = 'Aceite_Prod'
    if 'a2' in df_raw.columns: cols_out_cent.append('a2'); rename_cent['a2'] = 'Acum. Mensual'
    if 'a4' in df_raw.columns: cols_out_cent.append('a4'); rename_cent['a4'] = 'Acidez'
    if 'a5' in df_raw.columns: cols_out_cent.append('a5'); rename_cent['a5'] = 'Acidez_Mensual'
    if 'a6' in df_raw.columns: cols_out_cent.append('a6'); rename_cent['a6'] = 'Acidez_Campana'
    if 'a7' in df_raw.columns: cols_out_cent.append('a7'); rename_cent['a7'] = 'Rdto_Obtenido'
    if 'a8' in df_raw.columns: cols_out_cent.append('a8'); rename_cent['a8'] = 'Media_Mensual'
    if 'a9' in df_raw.columns: cols_out_cent.append('a9'); rename_cent['a9'] = 'Rdto_Campana'
    
    df_c3_cent = df_raw[df_raw['actividad'] == 3][cols_out_cent].rename(columns=rename_cent)
    
    cols_out_desh = [name_col]
    rename_desh = {name_col: 'Centro'}
    if 'a7' in df_raw.columns: cols_out_desh.append('a7'); rename_desh['a7'] = 'Aceite_Prod'
    if 'a8' in df_raw.columns: cols_out_desh.append('a8'); rename_desh['a8'] = 'Acum. Mensual'
    
    df_c3_desh = df_raw[(df_raw['actividad'] == 5) & (df_raw.get('actividad1', 0) == 1)][cols_out_desh].rename(columns=rename_desh)
    df_c3 = pd.concat([df_c3_cent, df_c3_desh], ignore_index=True) if not df_c3_cent.empty or not df_c3_desh.empty else pd.DataFrame(columns=['Centro', 'Aceite_Prod', 'Acum. Mensual'])
    
    if not df_c2.empty or not df_c3.empty:
        df_cent = pd.merge(df_c2, df_c3, on='Centro', how='outer').fillna(0)
    else:
        df_cent = pd.DataFrame(columns=['Centro', 'Entrada_Alperujo', 'Aceite_Prod', 'Acum. Mensual', 'Acidez', 'Acidez_Mensual', 'Acidez_Campana', 'Rdto_Obtenido', 'Media_Mensual', 'Rdto_Campana'])
        
    df_cent['Centro'] = format_names(df_cent['Centro'])
    df_cent = df_cent.groupby('Centro', as_index=False).sum()
    
    if 'Rdto_Obtenido' not in df_cent.columns: df_cent['Rdto_Obtenido'] = 0.0
    if 'Entrada_Alperujo' in df_cent.columns and 'Aceite_Prod' in df_cent.columns:
        mask_rdto = (df_cent['Rdto_Obtenido'] == 0) & (df_cent['Entrada_Alperujo'] > 0)
        if mask_rdto.any():
            df_cent.loc[mask_rdto, 'Rdto_Obtenido'] = (df_cent.loc[mask_rdto, 'Aceite_Prod'] / df_cent.loc[mask_rdto, 'Entrada_Alperujo'] * 100).round(2)
            
    for col in ['Acidez', 'Acidez_Mensual', 'Acidez_Campana', 'Media_Mensual', 'Rdto_Campana']:
        if col not in df_cent.columns: df_cent[col] = pd.NA
        else: df_cent[col] = df_cent[col].replace(0, pd.NA)
    
    # Secado
    cond_secado = (df_raw['actividad'] == 5) & (df_raw.get('actividad1', 0) != 1)
    df_secado_out = df_raw[cond_secado][[name_col, 'a1', 'a2']].copy() if 'a1' in df_raw.columns else pd.DataFrame(columns=[name_col, 'a1', 'a2'])
    df_secado_out.rename(columns={name_col: 'Centro', 'a1': 'OGS_Salida', 'a2': 'Acum. Mensual'}, inplace=True)
    
    cond_sec_in = (df_raw['actividad'] == 4) & (df_raw.get('actividad1', 0) != 1)
    df_sec_in = df_raw[cond_sec_in][[name_col, 'a1']].rename(columns={name_col: 'Centro', 'a1': 'Entrada_Alperujo'}) if 'a1' in df_raw.columns else pd.DataFrame(columns=['Centro', 'Entrada_Alperujo'])
    
    df_secado = pd.merge(df_sec_in, df_secado_out, on='Centro', how='outer').fillna(0)
    if 'Centro' in df_secado.columns:
        df_secado['Centro'] = format_names(df_secado['Centro'])
    
    # Extracción (Producción y Entrada)
    cond_ext = df_raw['actividad'].isin([6, 7, 9])
    df_ext_raw = df_raw[cond_ext].copy()
    
    ext_in, ext_prod, ext_ventas = [], [], []
    
    if not df_ext_raw.empty:
        for idx, row in df_ext_raw.iterrows():
            act = row.get('actividad')
            act1 = row.get('actividad1', 0)
            centro_code = row.get('centro', -1)
            desc = str(row.get(name_col, '')).upper()
            
            planta = 'Desconocida'
            if act == 6: planta = 'El Tejar'
            elif act == 7 and act1 == 0: planta = 'Baena'
            elif act == 7 and act1 == 1: planta = 'Espejo'
            elif act == 7 and act1 == 3: planta = 'Pedro Abad'
            elif act == 9:
                if "PEDRO ABAD" in desc or centro_code == 17: planta = 'Pedro Abad'
                elif "BAENA" in desc or centro_code == 9: planta = 'Baena'
                elif "TEJAR" in desc or centro_code == 1: planta = 'El Tejar'
                else: planta = format_names(pd.Series([desc])).iloc[0]
            
            v1 = pd.to_numeric(row.get('a1', 0), errors='coerce')
            v2 = pd.to_numeric(row.get('a2', 0), errors='coerce')
            v3 = pd.to_numeric(row.get('a3', 0), errors='coerce')
            v12 = pd.to_numeric(row.get('a12', 0), errors='coerce')
            if pd.isna(v1): v1 = 0
            if pd.isna(v2): v2 = 0
            if pd.isna(v3): v3 = 0
            if pd.isna(v12): v12 = 0
            
            if act == 9:
                ext_ventas.append({'Extractora': planta, 'Salida_Aceite': v1, 'Salida_Mes': v2})
            elif "ACEITE" in desc or "PROD" in desc:
                ext_prod.append({'Extractora': planta, 'Aceite_Prod': v1, 'Acum. Mensual': v2, 'Acum_Campana': v3, 'Optimo_Subifor': v12})
            else:
                ext_in.append({'Extractora': planta, 'OGS_Procesado': v1, 'OGS_Acum': v2})
                
    df_in = pd.DataFrame(ext_in).groupby('Extractora', as_index=False).sum() if ext_in else pd.DataFrame(columns=['Extractora'])
    df_prod = pd.DataFrame(ext_prod).groupby('Extractora', as_index=False).sum() if ext_prod else pd.DataFrame(columns=['Extractora'])
    df_ventas = pd.DataFrame(ext_ventas).groupby('Extractora', as_index=False).sum() if ext_ventas else pd.DataFrame(columns=['Extractora'])
    
    df_ext = pd.DataFrame({'Extractora': ['El Tejar', 'Baena', 'Pedro Abad', 'Espejo']})
    if not df_in.empty: df_ext = pd.merge(df_ext, df_in, on='Extractora', how='outer')
    if not df_prod.empty: df_ext = pd.merge(df_ext, df_prod, on='Extractora', how='outer')
    if not df_ventas.empty: df_ext = pd.merge(df_ext, df_ventas, on='Extractora', how='outer')
    df_ext = df_ext.fillna(0)
    df_ext['Centro'] = df_ext['Extractora'].apply(get_centro_from_planta)
    
    # Electricidad
    df_elec = df_raw[df_raw['actividad'] == 8][[name_col, 'a1', 'a2']].copy() if 'a1' in df_raw.columns else pd.DataFrame(columns=[name_col, 'a1', 'a2'])
    df_elec.rename(columns={name_col: 'Planta', 'a1': 'Generada_kWh', 'a2': 'Acum. Mensual'}, inplace=True)
    df_elec['Planta'] = format_names(df_elec['Planta'])
    if not df_elec.empty:
        df_elec['Centro'] = df_elec['Planta'].apply(get_centro_from_planta)
    
    # Consumo Secado
    cols_to_extract = [name_col]
    for c in ['a1', 'a2', 'a3', 'a4']:
        if c in df_raw.columns: cols_to_extract.append(c)
    df_cons_secado = df_raw[df_raw['actividad'] == 19][cols_to_extract].copy()
    if not df_cons_secado.empty:
        rename_dict = {name_col: 'Centro', 'a1': 'Consumo_Hueso', 'a2': 'Consumo_Orujillo', 'a3': 'Consumo_Poda', 'a4': 'Consumo_Hoja'}
        df_cons_secado.rename(columns=rename_dict, inplace=True)
        if 'Centro' in df_cons_secado.columns:
            df_cons_secado['Centro'] = format_names(df_cons_secado['Centro'])
    else:
        df_cons_secado = pd.DataFrame(columns=['Centro', 'Consumo_Hueso', 'Consumo_Orujillo', 'Consumo_Poda', 'Consumo_Hoja'])

    # Consumo Extracción
    df_cons_ext_raw = df_raw[df_raw['actividad'] == 20][cols_to_extract].copy()
    if not df_cons_ext_raw.empty:
        rename_dict = {name_col: 'Extractora', 'a1': 'Consumo_Hueso', 'a2': 'Consumo_Orujillo', 'a3': 'Consumo_Poda', 'a4': 'Consumo_Hoja'}
        df_cons_ext_raw.rename(columns=rename_dict, inplace=True)
        
        def map_cons_ext(desc, centro):
            desc = str(desc).upper()
            if "PEDRO ABAD" in desc or centro == 17: return "Pedro Abad"
            if "TEJAR" in desc or centro == 1: return "El Tejar"
            return format_names(pd.Series([desc])).iloc[0]
            
        df_cons_ext_raw['Extractora'] = [map_cons_ext(row.get('Extractora', ''), df_raw.loc[idx, 'centro'] if 'centro' in df_raw.columns else -1) for idx, row in df_cons_ext_raw.iterrows()]
        df_cons_ext = df_cons_ext_raw.groupby('Extractora', as_index=False).sum()
        df_cons_ext['Centro'] = df_cons_ext['Extractora'].apply(get_centro_from_planta)
    else:
        df_cons_ext = pd.DataFrame(columns=['Extractora', 'Consumo_Hueso', 'Consumo_Orujillo', 'Consumo_Poda', 'Consumo_Hoja', 'Centro'])

    df_full = pd.DataFrame()
    return df_aport, df_existencias, df_cent, df_secado, df_ext, df_elec, df_cons_secado, df_cons_ext, df_full

# --- MOTOR DE EXTRACCIÓN MANUAL / PLANTILLAS ---
def load_data(uploaded_file):
    if uploaded_file is not None:
        try:
            uploaded_file.seek(0)
            filename = uploaded_file.name.lower()
            
            if filename.endswith('.csv') or filename.endswith('.txt'):
                content = uploaded_file.getvalue().decode('latin1', errors='ignore')
                sep = ';' if content.count(';') > content.count(',') else ','
                df_raw = pd.read_csv(io.StringIO(content), delimiter=sep)
                
                cols = [str(c).lower().strip() for c in df_raw.columns]
                if 'actividad' in cols:
                    return parse_subifor_csv(df_raw)
                    
                reader = csv.reader(io.StringIO(content), delimiter=sep)
                df_dict = {"Sheet1": pd.DataFrame(list(reader)).fillna('')}
                
            else:
                raw_dict = pd.read_excel(uploaded_file, sheet_name=None)
                first_sheet = list(raw_dict.keys())[0]
                first_df = raw_dict[first_sheet]
                cols = [str(c).lower().strip() for c in first_df.columns]
                if 'actividad' in cols:
                    return parse_subifor_csv(first_df)
                
                df_dict = {name: df.fillna('').astype(str) for name, df in raw_dict.items()}
                
            def extract_table(df_d, marker):
                for sheet_name, df_r in df_d.items():
                    if df_r.empty: continue
                    col0 = df_r.iloc[:, 0].astype(str).str.strip()
                    idx = df_r[col0 == marker].index
                    if len(idx) > 0:
                        start_idx = idx[0]
                        end_idx = len(df_r)
                        for i in range(start_idx + 1, len(df_r)):
                            val = str(df_r.iloc[i, 0]).strip()
                            if val.startswith('#') and val != marker:
                                end_idx = i
                                break
                        df_sub = df_r.iloc[start_idx+1:end_idx].copy()
                        df_sub = df_sub.replace(r'^\s*$', pd.NA, regex=True).dropna(how='all').reset_index(drop=True)
                        if df_sub.empty: return pd.DataFrame()
                        headers = df_sub.iloc[0].fillna('').astype(str).str.strip()
                        df_sub.columns = headers
                        df_sub = df_sub.iloc[1:].reset_index(drop=True)
                        valid_cols = [c for c in df_sub.columns if c != '']
                        if not valid_cols: return pd.DataFrame()
                        df_sub = df_sub[valid_cols]
                        for col in df_sub.columns:
                            df_sub[col] = df_sub[col].apply(fix_number)
                            s_num = pd.to_numeric(df_sub[col], errors='coerce')
                            if s_num.isna().sum() <= df_sub[col].isna().sum():
                                df_sub[col] = s_num
                        return df_sub
                return pd.DataFrame()
                
            df_aport = extract_table(df_dict, "# APORTACIONES")
            df_existencias = extract_table(df_dict, "# EXISTENCIAS")
            df_cent = extract_table(df_dict, "# CENTRIFUGACION")
            df_secado = extract_table(df_dict, "# SECADO")
            df_ext = extract_table(df_dict, "# EXTRACCION")
            df_elec = extract_table(df_dict, "# ELECTRICIDAD")
            
            if not df_aport.empty and 'Planta' in df_aport.columns: df_aport['Centro'] = df_aport['Planta'].apply(get_centro_from_planta)
            if not df_ext.empty and 'Extractora' in df_ext.columns: df_ext['Centro'] = df_ext['Extractora'].apply(get_centro_from_planta)
            if not df_elec.empty and 'Planta' in df_elec.columns: df_elec['Centro'] = df_elec['Planta'].apply(get_centro_from_planta)
            
            return df_aport, df_existencias, df_cent, df_secado, df_ext, df_elec, pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
            
        except Exception as e:
            st.error(f"Error procesando archivo: {str(e)}")
            pass
            
    # --- DATOS POR DEFECTO ---
    df_aport = pd.DataFrame({"Planta": ["Palenciana", "Marchena", "Cabra", "Pedro Abad", "Baena", "Bogarre", "Mancha Real", "Espejo"], "Centro": ["Palenciana", "Marchena", "Cabra", "Pedro Abad", "Baena", "Bogarre", "Mancha Real", "Espejo"], "Hoy (kg)": [925240, 76600, 1000940, 173220, 114380, 152180, 54160, 113180], "Acum. Mensual": [11287480, 249122145, 10153600, 203101510, 3693860, 3070720, 87145800, 2395120]})
    df_existencias = pd.DataFrame({"Material": ["Hueso de Aceituna", "Orujillo", "Hoja de Olivo"], "Total Kilos": [27694950, 17150820, 57655131]})
    df_cent = pd.DataFrame({"Centro": ["Palenciana", "Marchena", "Cabra", "Baena"], "Entrada_Alperujo": [260545, 461201, 67426, 631151], "Aceite_Prod": [0, 1870, 632, 771], "Rdto_Obtenido": [0.0, 0.41, 0.94, 0.12], "Acidez": [3.44, 2.92, 11.15, 7.81], "Acidez_Mensual": [3.50, 3.00, 10.00, 8.00], "Acidez_Campana": [3.40, 2.80, 9.50, 8.50], "Media_Mensual": [0.0, 0.46, 0.40, 0.30], "Rdto_Campana": [0.0, 0.46, 0.41, 0.41], "Acum. Mensual": [181512, 28296, 8850, 22616]})
    df_secado = pd.DataFrame({"Centro": ["Palenciana", "Marchena", "Cabra", "Pedro Abad", "Baena", "Bogarre", "Mancha Real", "Espejo"], "Entrada_Alperujo": [444668, 904664, 595175, 621928, 457958, 527979, 163116, 157546], "OGS_Salida": [134400, 221140, 161380, 0, 110000, 0, 0, 22298], "Acum. Mensual": [4241823, 10687000, 2426560, 3388880, 16195500, 2918540, 1183521, 2281940]})
    df_ext = pd.DataFrame({"Extractora": ["El Tejar", "Baena", "Pedro Abad", "Espejo"], "Centro": ["El Tejar", "Baena", "Pedro Abad", "Espejo"], "OGS_Procesado": [570400, 110000, 329510, 29100], "Aceite_Prod": [31800, 8300, 0, 0], "Acum. Mensual": [255100, 151900, 171100, 192398], "Optimo_Subifor": [43400, 18900, 0, 0], "Salida_Aceite": [12500, 5000, 0, 0]})
    df_elec = pd.DataFrame({"Planta": ["Vetejar 12.6 MW", "Autogeneración 5.7 MW", "Baena 25 MW", "Algodonales 5.3 MW"], "Centro": ["Palenciana", "Palenciana", "Baena", "Palenciana"], "Generada_kWh": [226344, 67876, 450634, 119229], "Acum. Mensual": [2868493, 833355, 6653469, 1507278]})
    
    df_cons_secado = pd.DataFrame({"Centro": ["Palenciana", "Marchena", "Cabra", "Pedro Abad", "Baena", "Bogarre", "Mancha Real", "Espejo"], "Consumo_Hueso": [1016300, 490000, 206280, 240000, 1072840, 368100, 398603, 449700], "Consumo_Orujillo": [0, 233540, 0, 18800, 0, 0, 26820, 0], "Consumo_Poda": [0, 0, 0, 898800, 19380, 231700, 0, 2239000], "Consumo_Hoja": [0, 0, 0, 0, 0, 0, 0, 0]})
    df_cons_ext = pd.DataFrame({"Extractora": ["El Tejar", "Pedro Abad"], "Centro": ["El Tejar", "Pedro Abad"], "Consumo_Hueso": [595000, 240000], "Consumo_Poda": [0, 898800], "Consumo_Orujillo": [0, 0], "Consumo_Hoja": [0, 0]})
    df_full = pd.DataFrame()
    
    return df_aport, df_existencias, df_cent, df_secado, df_ext, df_elec, df_cons_secado, df_cons_ext, df_full

# --- SMART FILTER MULTI-COLUMNA ---
def filter_dataframe(df, column_names, planta_seleccionada):
    if df.empty or planta_seleccionada == "Todas":
        return df
    if isinstance(column_names, str):
        column_names = [column_names]
    mask = pd.Series(False, index=df.index)
    for col in column_names:
        if col in df.columns:
            mask = mask | df[col].astype(str).str.contains(planta_seleccionada, case=False, na=False)
    return df[mask].reset_index(drop=True)

# --- APLICACIÓN PRINCIPAL ---
if check_password():
    role = st.session_state["role"]
    
    col_logo, col_titulo, col_logout = st.columns([1, 8, 1])
    with col_logo:
        if os.path.exists("Logo.png"):
            st.image("Logo.png", use_container_width=True)
        else:
            st.markdown("<div style='font-size: 3rem; text-align: center;'>🏭</div>", unsafe_allow_html=True)
    with col_titulo:
        st.title("Panel Operativo - Oleícola El Tejar SCA")
    with col_logout:
        st.write("<br>", unsafe_allow_html=True)
        if st.button("🚪 Salir"):
            st.session_state["login_ok"] = False
            st.session_state["role"] = None
            st.rerun()
            
    st.markdown("---")
    
    col_date, col_filter = st.columns([1, 2])
    with col_date:
        fecha_activa = st.date_input("📅 Selecciona la Fecha del Reporte:", load_last_date())
        if fecha_activa != load_last_date():
            with open("ultima_fecha.txt", "w") as f:
                f.write(fecha_activa.isoformat())
    
    with col_filter:
        plantas_disponibles = ["Todas", "Baena", "Cabra", "Marchena", "Palenciana", "Pedro Abad", "Espejo", "Bogarre", "Mancha Real", "Algodonales", "Vetejar", "El Tejar"]
        planta_activa = st.selectbox("📍 Filtro Global por Planta/Centro:", plantas_disponibles)

    if role == "oficina":
        st.info(f"👋 **Modo Oficina:** Sube el archivo CSV exportado de Subifor para el día **{fecha_activa.strftime('%d/%m/%Y')}**.")
        with st.container():
            archivo_subido = st.file_uploader("📂 Sube tu Archivo (CSV de Subifor)", type=["csv", "xlsx", "xls"], label_visibility="visible")
            if archivo_subido is not None:
                save_file_to_disk(archivo_subido, fecha_activa)
                st.success(f"✅ Archivo guardado correctamente en la base de datos histórica para el {fecha_activa.strftime('%d/%m/%Y')}.")
    
    archivo_compartido = load_file_from_disk(fecha_activa)
    if archivo_compartido is None:
        st.warning(f"⚠️ Aún no hay ningún parte subido para el día **{fecha_activa.strftime('%d/%m/%Y')}**. Por favor, contacte con oficina o seleccione otra fecha.")
        df_aport, df_existencias, df_cent, df_secado, df_ext, df_elec, df_cons_secado, df_cons_ext, df_full = pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    else:
        df_aport, df_existencias, df_cent, df_secado, df_ext, df_elec, df_cons_secado, df_cons_ext, df_full = load_data(archivo_compartido)
        
    df_obj = load_objectives()
    df_cent, df_secado, df_ext, df_elec = apply_objectives(df_cent, df_secado, df_ext, df_elec, df_obj)
    
    df_aport = filter_dataframe(df_aport, ["Planta", "Centro"], planta_activa)
    df_cent = filter_dataframe(df_cent, ["Centro", "Planta"], planta_activa)
    df_secado = filter_dataframe(df_secado, ["Centro", "Planta"], planta_activa)
    df_ext = filter_dataframe(df_ext, ["Extractora", "Centro"], planta_activa)
    df_elec = filter_dataframe(df_elec, ["Centro", "Planta"], planta_activa)
    df_obj_filtered = filter_dataframe(df_obj, ["Centro", "Planta"], planta_activa)

    tabs = st.tabs(["👁️ Visión General", "📦 Aportaciones", "🌀 Centrifugación", "🔥 Secado", "⚗️ Extracción", "⚡ Electricidad", "🎯 Mis Objetivos"])

    # --- PESTAÑA 1: VISIÓN GENERAL ---
    with tabs[0]:
        if not df_aport.empty or not df_elec.empty:
            col_resumen, col_noticias = st.columns([2, 1])
            with col_resumen:
                st.subheader(f"Resumen Ejecutivo - {planta_activa.upper()}")
                
                total_orujo = df_aport['Hoy (kg)'].sum() if not df_aport.empty and 'Hoy (kg)' in df_aport.columns else 0
                total_elec = df_elec['Generada_kWh'].sum() if not df_elec.empty and 'Generada_kWh' in df_elec.columns else 0
                total_aceite_cent = df_cent['Aceite_Prod'].sum() if not df_cent.empty and 'Aceite_Prod' in df_cent.columns else 0
                total_aceite_ext = df_ext['Aceite_Prod'].sum() if not df_ext.empty and 'Aceite_Prod' in df_ext.columns else 0
                
                total_orujo_mes = df_aport['Acum. Mensual'].sum() if not df_aport.empty and 'Acum. Mensual' in df_aport.columns else 0
                total_elec_mes = df_elec['Acum. Mensual'].sum() if not df_elec.empty and 'Acum. Mensual' in df_elec.columns else 0
                total_aceite_cent_mes = df_cent['Acum. Mensual'].sum() if not df_cent.empty and 'Acum. Mensual' in df_cent.columns else 0
                total_aceite_ext_mes = df_ext['Acum. Mensual'].sum() if not df_ext.empty and 'Acum. Mensual' in df_ext.columns else 0
                
                target_elec = df_obj_filtered[df_obj_filtered['Area']=='Electricidad']['Objetivo_Diario'].sum()
                target_cent = df_obj_filtered[df_obj_filtered['Area']=='Centrifugacion']['Objetivo_Diario'].sum()
                target_ext = df_obj_filtered[df_obj_filtered['Area']=='Extraccion']['Objetivo_Diario'].sum()
                
                st.markdown("#### 📅 Producción Diaria (Hoy)")
                c1, c2, c3, c4 = st.columns(4)
                with c1: st.markdown(get_kpi_card_html("Orujo Recibido", "📦", total_orujo, "kg", "<div class='kpi-delta delta-neutral'>Materia prima de entrada</div>", ""), unsafe_allow_html=True)
                with c2: st.markdown(get_kpi_card_html("Electricidad", "⚡", total_elec, "kWh", get_delta_html(total_elec, target_elec), "blue"), unsafe_allow_html=True)
                with c3: st.markdown(get_kpi_card_html("Aceite Centrif.", "💧", total_aceite_cent, "kg", get_delta_html(total_aceite_cent, target_cent), "yellow"), unsafe_allow_html=True)
                with c4: st.markdown(get_kpi_card_html("Aceite Extrac.", "⚗️", total_aceite_ext, "kg", get_delta_html(total_aceite_ext, target_ext), "orange"), unsafe_allow_html=True)
                
                st.write("<br>", unsafe_allow_html=True)
                
                st.markdown("#### 📊 Producción Acumulada Mensual")
                m1, m2, m3, m4 = st.columns(4)
                with m1: st.markdown(get_monthly_card_html("Orujo Recibido", "📦", total_orujo_mes, "kg", ""), unsafe_allow_html=True)
                with m2: st.markdown(get_monthly_card_html("Electricidad", "⚡", total_elec_mes, "kWh", "blue"), unsafe_allow_html=True)
                with m3: st.markdown(get_monthly_card_html("Aceite Centrif.", "💧", total_aceite_cent_mes, "kg", "yellow"), unsafe_allow_html=True)
                with m4: st.markdown(get_monthly_card_html("Aceite Extrac.", "⚗️", total_aceite_ext_mes, "kg", "orange"), unsafe_allow_html=True)
                
                st.write("<br>", unsafe_allow_html=True)
                st.write("### 🤖 Análisis Operativo IA")
                
                alertas = []
                if not df_cent.empty and 'Acidez' in df_cent.columns:
                    for _, row in df_cent.iterrows():
                        val_acidez = row.get('Acidez', pd.NA)
                        if pd.notnull(val_acidez) and isinstance(val_acidez, (int, float)) and val_acidez > 3:
                            alertas.append(f"⚠️ **Centrifugación {row.get('Centro', '')}:** Acidez crítica detectada ({val_acidez}%)")
                
                if not df_elec.empty and 'Generada_kWh' in df_elec.columns and 'Optimo_kWh' in df_elec.columns:
                    for _, row in df_elec.iterrows():
                        val_gen, val_opt = row['Generada_kWh'], row['Optimo_kWh']
                        if pd.notnull(val_gen) and pd.notnull(val_opt) and val_gen > val_opt:
                            alertas.append(f"✅ **Electricidad {row.get('Planta', '')}:** Rendimiento supera el objetivo estratégico.")

                if not alertas:
                    st.success(f"✅ **Operaciones Normales en {planta_activa}:** Todos los parámetros monitorizados están dentro de la normalidad.")
                else:
                    for a in alertas:
                        if "⚠️" in a: st.error(a)
                        else: st.success(a)

            with col_noticias:
                st.subheader("📰 Actualidad del Sector")
                st.markdown("""
                <div class="news-card">
                    <div class="news-title">El precio del AOVE se estabiliza en origen</div>
                    <div class="news-source">Fuente: OleoMerca | Abril 2026</div>
                    <div class="news-snippet">Las operaciones en picual de alta calidad se cierran en torno a los 4,20€/kg, marcando un freno a las caídas de las últimas tres semanas...</div>
                    <a href="https://www.olimerca.com/" target="_blank" class="read-more" style="display: inline-block; margin-top: 8px;">Leer completa →</a>
                </div>
                <div class="news-card">
                    <div class="news-title">Nuevo marco normativo para la cogeneración</div>
                    <div class="news-source">Fuente: Revista Alcuza | Abril 2026</div>
                    <div class="news-snippet">El Ministerio de Transición Ecológica ha publicado el borrador que bonificará a las plantas extractoras que demuestren una alta eficiencia...</div>
                    <a href="https://www.mercacei.com/" target="_blank" class="read-more" style="display: inline-block; margin-top: 8px;">Leer completa →</a>
                </div>
                """, unsafe_allow_html=True)

    # --- PESTAÑA 2: APORTACIONES Y EXISTENCIAS ---
    with tabs[1]:
        col_hoy, col_mes = st.columns(2)
        with col_hoy:
            st.subheader("Orujo Aportado Hoy (kg)")
            if not df_aport.empty and 'Planta' in df_aport.columns and 'Hoy (kg)' in df_aport.columns:
                fig_aport = px.bar(df_aport, x="Planta", y="Hoy (kg)")
                fig_aport.update_traces(texttemplate='%{y:,.0f}', textposition='outside', marker_color='#8d6e63')
                fig_aport.update_layout(yaxis=dict(tickformat=","), margin=dict(t=30))
                st.plotly_chart(fig_aport, use_container_width=True)
            else: st.info("Faltan datos de Aportaciones diarias.")
            
        with col_mes:
            st.subheader("Acumulado Mensual (kg)")
            if not df_aport.empty and 'Planta' in df_aport.columns and 'Acum. Mensual' in df_aport.columns:
                fig_aport_mes = px.bar(df_aport, x="Planta", y="Acum. Mensual")
                fig_aport_mes.update_traces(texttemplate='%{y:,.0f}', textposition='outside', marker_color='#60a5fa')
                fig_aport_mes.update_layout(yaxis=dict(tickformat=","), margin=dict(t=30))
                st.plotly_chart(fig_aport_mes, use_container_width=True)
            else: st.info("Faltan datos de Acumulado Mensual.")
            
        if planta_activa == "Todas":
            st.markdown("---")
            st.subheader("📦 Estado General de Existencias")
            if not df_existencias.empty:
                cols_ex = st.columns(len(df_existencias))
                for i, row in df_existencias.iterrows():
                    with cols_ex[i]:
                        mat_name = row['Material']
                        icon = "📦"
                        if "Hueso" in mat_name: icon = "🫒"
                        elif "Orujillo" in mat_name: icon = "🤎"
                        elif "Hoja" in mat_name: icon = "🍃"
                        
                        st.markdown(get_kpi_card_html(mat_name, icon, row['Total Kilos'], "kg", "", "blue"), unsafe_allow_html=True)
            else:
                st.info("Sin datos de existencias.")
                
        with st.expander("📊 Ver tabla de datos detallada (Aportaciones)"):
            display_styled_table(df_aport, download_name="aportaciones_tejar.csv")

    # --- PESTAÑA 3: CENTRIFUGACIÓN ---
    with tabs[2]:
        st.subheader("🌀 Análisis Detallado de Centrifugación")
        
        col1, col2 = st.columns(2)
        with col1:
            if not df_cent.empty and 'Centro' in df_cent.columns and 'Entrada_Alperujo' in df_cent.columns:
                fig_entrada_cent = px.bar(df_cent, x="Centro", y="Entrada_Alperujo", title="Entrada de Alperujo (kg)")
                fig_entrada_cent.update_traces(texttemplate='%{y:,.0f}', textposition='outside', marker_color='#4ade80')
                fig_entrada_cent.update_layout(yaxis=dict(tickformat=","), margin=dict(t=40))
                st.plotly_chart(fig_entrada_cent, use_container_width=True)
            else: st.info("Faltan datos de Entrada de Alperujo.")
            
        with col2:
            if not df_cent.empty and 'Centro' in df_cent.columns and 'Aceite_Prod' in df_cent.columns:
                fig_cent_comp = go.Figure()
                fig_cent_comp.add_trace(go.Bar(x=df_cent['Centro'], y=df_cent['Aceite_Prod'], name='Producido', marker_color='#fbbf24', text=df_cent['Aceite_Prod'], texttemplate='%{text:,.0f}'))
                if 'Optimo' in df_cent.columns:
                    fig_cent_comp.add_trace(go.Bar(x=df_cent['Centro'], y=df_cent['Optimo'], name='Óptimo', marker_color='#94a3b8', text=df_cent['Optimo'], texttemplate='%{text:,.0f}'))
                fig_cent_comp.update_layout(title="Aceite Producido vs Óptimo Industrial (kg)", barmode='group', yaxis=dict(tickformat=","), margin=dict(t=40))
                st.plotly_chart(fig_cent_comp, use_container_width=True)
            else: st.info("Faltan datos de Aceite Producido.")
            
        col3, col4 = st.columns(2)
        with col3:
            if not df_cent.empty and 'Rdto_Obtenido' in df_cent.columns:
                fig_rdto = go.Figure()
                
                if 'Media_Mensual' in df_cent.columns and df_cent['Media_Mensual'].notna().any():
                    colors = ['#22c55e' if r >= m else '#ef4444' for r, m in zip(df_cent['Rdto_Obtenido'], df_cent['Media_Mensual'].fillna(0))]
                else:
                    colors = ['#3b82f6'] * len(df_cent)
                    
                fig_rdto.add_trace(go.Bar(x=df_cent['Centro'], y=df_cent['Rdto_Obtenido'], name='Rdto. Diario (%)', marker_color=colors, text=df_cent['Rdto_Obtenido'], texttemplate='%{text:.2f}%', textposition='auto'))
                
                if 'Media_Mensual' in df_cent.columns and df_cent['Media_Mensual'].notna().any():
                    fig_rdto.add_trace(go.Scatter(x=df_cent['Centro'], y=df_cent['Media_Mensual'], mode='markers+text', name='Media Mensual (%)', text=df_cent['Media_Mensual'], texttemplate='%{text:.2f}%', textposition='top center', textfont=dict(color='#0f172a', size=14, weight='bold'), marker=dict(symbol='line-ew', size=45, color='#0f172a', line=dict(width=3))))
                    
                fig_rdto.update_layout(title="Rendimiento Diario vs Media Mensual (%)<br><sup><span style='color:#22c55e'>Verde</span>: Supera media | <span style='color:#ef4444'>Rojo</span>: Por debajo de media</sup>", yaxis_title="Rendimiento (%)", margin=dict(t=60))
                st.plotly_chart(fig_rdto, use_container_width=True)
                
        with col4:
            if not df_cent.empty and 'Acidez' in df_cent.columns and df_cent['Acidez'].notna().any():
                df_acidez = df_cent.dropna(subset=['Acidez']).copy()
                if not df_acidez.empty:
                    colors = ['#ef4444' if val > 3 else '#22c55e' for val in df_acidez['Acidez']]
                    fig_acidez = go.Figure(data=[go.Bar(x=df_acidez['Centro'], y=df_acidez['Acidez'], marker_color=colors, text=df_acidez['Acidez'], texttemplate='%{text:.2f}%', textposition='auto')])
                    fig_acidez.add_hline(y=3, line_dash="dash", line_color="#ef4444", annotation_text="Límite (3%)", annotation_position="top right")
                    fig_acidez.update_layout(title="Control de Calidad: Acidez del Aceite (%)", yaxis_title="Acidez (%)", margin=dict(t=40))
                    st.plotly_chart(fig_acidez, use_container_width=True)
            else:
                st.info("No hay datos de acidez registrados para graficar.")
                
        st.markdown("#### 📈 Producción Acumulada")
        if not df_cent.empty and 'Acum. Mensual' in df_cent.columns:
            fig_acum = px.bar(df_cent, x="Centro", y="Acum. Mensual", title="Aceite Acumulado Mensual (kg)")
            fig_acum.update_traces(texttemplate='%{y:,.0f}', textposition='outside', marker_color='#8b5cf6')
            fig_acum.update_layout(yaxis=dict(tickformat=","), margin=dict(t=40))
            st.plotly_chart(fig_acum, use_container_width=True)

        with st.expander("📊 Ver tabla de datos detallada (Centrifugación)"):
            display_styled_table(df_cent, "Centrifugacion", download_name="centrifugacion_tejar.csv")

    # --- PESTAÑA 4: SECADO ---
    with tabs[3]:
        total_ogs = df_secado['OGS_Salida'].sum() if not df_secado.empty and 'OGS_Salida' in df_secado.columns else 0
        st.markdown(f"### 🏭 Total Orujo Graso Seco (OGS) Generado: **{total_ogs:,.0f} kg**")
        st.write("<hr>", unsafe_allow_html=True)
        
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.subheader("Entrada Alperujo Procesado (kg)")
            if not df_secado.empty and 'Entrada_Alperujo' in df_secado.columns and df_secado['Entrada_Alperujo'].sum() > 0:
                fig_alperujo_sec = px.bar(df_secado, x="Centro", y="Entrada_Alperujo")
                fig_alperujo_sec.update_traces(marker_color='#4ade80', texttemplate='%{y:,.0f}', textposition='outside')
                fig_alperujo_sec.update_layout(yaxis=dict(tickformat=","), margin=dict(t=30))
                st.plotly_chart(fig_alperujo_sec, use_container_width=True)
            else:
                st.info("Sin datos de entrada de alperujo.")
                
        with col_s2:
            st.subheader("OGS Salida vs Objetivo (kg)")
            if not df_secado.empty and 'Centro' in df_secado.columns and 'OGS_Salida' in df_secado.columns:
                fig_ogs = px.bar(df_secado, x="Centro", y=["OGS_Salida", "Obj_OGS"] if 'Obj_OGS' in df_secado.columns else "OGS_Salida", barmode="group", color_discrete_sequence=['#d97706', '#fcd34d'])
                fig_ogs.update_layout(yaxis=dict(tickformat=","), margin=dict(t=30))
                st.plotly_chart(fig_ogs, use_container_width=True)
            else: st.info(f"Sin datos de Secado para: {planta_activa}")

        st.markdown("#### 📊 Acumulado Mensual (OGS)")
        if not df_secado.empty and 'Acum. Mensual' in df_secado.columns and df_secado['Acum. Mensual'].sum() > 0:
            fig_ogs_mes = px.bar(df_secado, x="Centro", y="Acum. Mensual")
            fig_ogs_mes.update_traces(marker_color='#f59e0b', texttemplate='%{y:,.0f}', textposition='outside')
            fig_ogs_mes.update_layout(yaxis=dict(tickformat=","), margin=dict(t=30))
            st.plotly_chart(fig_ogs_mes, use_container_width=True)
    
        if not df_cons_secado.empty:
            df_cons_secado_filt = filter_dataframe(df_cons_secado, ["Centro", "Planta"], planta_activa)
            if not df_cons_secado_filt.empty:
                st.markdown("#### 🔥 Consumo Térmico Mensual en Secaderos")
                df_melted = df_cons_secado_filt.melt(id_vars=["Centro"], value_vars=["Consumo_Hueso", "Consumo_Orujillo", "Consumo_Poda", "Consumo_Hoja"], var_name="Material", value_name="Kilos")
                df_melted = df_melted[df_melted["Kilos"] > 0]
                
                if not df_melted.empty:
                    df_melted['Material'] = df_melted['Material'].str.replace('Consumo_', '')
                    fig_cons = px.bar(df_melted, x="Centro", y="Kilos", color="Material", 
                                      title="Acumulado Mensual de Biomasa (kg)", 
                                      color_discrete_map={"Hueso": "#78350f", "Orujillo": "#475569", "Poda": "#4d7c0f", "Hoja": "#84cc16"})
                    st.plotly_chart(fig_cons, use_container_width=True)
                else:
                    st.info("Sin consumos térmicos mensuales registrados.")

        with st.expander("📊 Ver tabla de datos detallada"):
            display_styled_table(df_secado, download_name="secado_tejar.csv")

    # --- PESTAÑA 5: EXTRACCIÓN ---
    with tabs[4]:
        col_ext1, col_ext2 = st.columns(2)
        with col_ext1:
            st.subheader("Entrada de Orujo a Extractora (kg)")
            if not df_ext.empty and 'OGS_Procesado' in df_ext.columns and df_ext['OGS_Procesado'].sum() > 0:
                fig_ogs_ext = px.bar(df_ext, x="Extractora", y="OGS_Procesado")
                fig_ogs_ext.update_traces(marker_color='#8d6e63', texttemplate='%{y:,.0f}', textposition='outside')
                fig_ogs_ext.update_layout(yaxis=dict(tickformat=","), margin=dict(t=30))
                st.plotly_chart(fig_ogs_ext, use_container_width=True)
            else:
                st.info("No hay datos de entrada de orujo registrados.")
                
        with col_ext2:
            st.subheader("Producción de Aceite vs Objetivo (kg)")
            if not df_ext.empty and 'Aceite_Prod' in df_ext.columns:
                opt_col = "Optimo_Subifor" if "Optimo_Subifor" in df_ext.columns and df_ext["Optimo_Subifor"].sum() > 0 else "Obj_Aceite"
                fig_aceite = px.bar(df_ext, x="Extractora", y=["Aceite_Prod", opt_col] if opt_col in df_ext.columns else "Aceite_Prod", barmode="group", color_discrete_sequence=['#eab308', '#fef08a'])
                fig_aceite.update_layout(yaxis=dict(tickformat=","), margin=dict(t=30))
                st.plotly_chart(fig_aceite, use_container_width=True)
                
        if not df_ext.empty and 'Salida_Aceite' in df_ext.columns and df_ext['Salida_Aceite'].sum() > 0:
            st.markdown("#### 🚢 Ventas y Salidas de Aceite (kg)")
            fig_ventas = px.bar(df_ext, x="Extractora", y="Salida_Aceite")
            fig_ventas.update_traces(marker_color='#0ea5e9', texttemplate='%{y:,.0f}', textposition='outside')
            fig_ventas.update_layout(yaxis=dict(tickformat=","), margin=dict(t=30))
            st.plotly_chart(fig_ventas, use_container_width=True)
            
        if not df_cons_ext.empty:
            df_cons_ext_filt = filter_dataframe(df_cons_ext, ["Extractora", "Centro"], planta_activa)
            if not df_cons_ext_filt.empty:
                st.markdown("#### 🔥 Consumo Térmico Mensual en Extracción")
                df_melted_ext = df_cons_ext_filt.melt(id_vars=["Extractora"], value_vars=["Consumo_Hueso", "Consumo_Orujillo", "Consumo_Poda", "Consumo_Hoja"], var_name="Material", value_name="Kilos")
                df_melted_ext = df_melted_ext[df_melted_ext["Kilos"] > 0]
                
                if not df_melted_ext.empty:
                    df_melted_ext['Material'] = df_melted_ext['Material'].str.replace('Consumo_', '')
                    fig_cons_ext = px.bar(df_melted_ext, x="Extractora", y="Kilos", color="Material", 
                                      title="Acumulado Mensual de Biomasa (kg)", 
                                      color_discrete_map={"Hueso": "#78350f", "Orujillo": "#475569", "Poda": "#4d7c0f", "Hoja": "#84cc16"})
                    st.plotly_chart(fig_cons_ext, use_container_width=True)
                else:
                    st.info("Sin consumos térmicos mensuales registrados en Extracción.")
                
        with st.expander("📊 Ver tabla de datos detallada"):
            display_styled_table(df_ext, download_name="extraccion_tejar.csv")

    # --- PESTAÑA 6: ELECTRICIDAD ---
    with tabs[5]:
        total_elec = df_elec['Generada_kWh'].sum() if not df_elec.empty and 'Generada_kWh' in df_elec.columns else 0
        st.markdown(f"### ⚡ Total Generado Hoy: **{total_elec:,.0f} kWh**")
        st.write("<hr>", unsafe_allow_html=True)
        
        st.subheader("Rendimiento Eléctrico Diario")
        
        def_opts = {'BAENA': 358330, 'VETEJAR': 190270, 'ALGODONALES': 91400, 'AUTOGENERACIÓN': 60000, 'AUTOGENERACION': 60000}
        
        if not df_elec.empty and 'Planta' in df_elec.columns and 'Generada_kWh' in df_elec.columns:
            st.write("*(Los velocímetros muestran la producción en azul y la línea oscura marca el objetivo estratégico)*")
            
            plantas_records = df_elec.to_dict('records')
            # Cambiado de a saltos de 3, a saltos de 4, para que quepan todos en una línea
            for i in range(0, len(plantas_records), 4):
                cols_velocimetros = st.columns(4)
                for j in range(4):
                    if i + j < len(plantas_records):
                        row = plantas_records[i + j]
                        gen = row['Generada_kWh'] if pd.notnull(row['Generada_kWh']) else 0
                        
                        opt = row.get('Optimo_kWh', 0)
                        if pd.isna(opt) or opt == 0:
                            planta_str = str(row['Planta']).upper()
                            for k, v in def_opts.items():
                                if k in planta_str:
                                    opt = v
                                    break
                        if opt == 0: opt = 1
                        
                        fig_gauge = go.Figure(go.Indicator(
                            mode = "gauge+number+delta",
                            value = gen,
                            domain = {'x': [0, 1], 'y': [0, 1]},
                            title = {'text': str(row['Planta']), 'font': {'size': 20, 'color': '#0f172a'}},
                            delta = {'reference': opt, 'increasing': {'color': "#16a34a"}, 'decreasing': {'color': "#dc2626"}, 'valueformat': ",.0f"},
                            number = {'font': {'size': 28, 'color': '#0f172a'}, 'valueformat': ",.0f"},
                            gauge = {
                                'axis': {'range': [None, max(opt, gen) * 1.2], 'tickwidth': 1, 'tickcolor': "#0f172a", 'tickfont': {'color': '#0f172a'}},
                                'bar': {'color': "#3b82f6", 'thickness': 0.7}, 
                                'bgcolor': "rgba(0,0,0,0)",
                                'borderwidth': 1,
                                'bordercolor': "#cbd5e1",
                                'steps': [
                                    {'range': [0, opt*0.8], 'color': '#fee2e2'},      
                                    {'range': [opt*0.8, opt], 'color': '#fef08a'},    
                                    {'range': [opt, max(opt, gen)*1.2], 'color': '#dcfce3'} 
                                ],
                                'threshold': {'line': {'color': "#0f172a", 'width': 4}, 'thickness': 0.85, 'value': opt}
                            }
                        ))
                        fig_gauge.update_layout(margin=dict(t=60, b=20, l=20, r=20), height=320, paper_bgcolor="rgba(0,0,0,0)")
                        
                        with cols_velocimetros[j]:
                            st.plotly_chart(fig_gauge, use_container_width=True)
                
        else: st.info(f"Faltan datos eléctricos para la planta: {planta_activa}")
        
        with st.expander("📊 Ver tabla de datos detallada"):
            display_styled_table(df_elec, download_name="electricidad_tejar.csv")

    # --- PESTAÑA 7: OBJETIVOS ---
    with tabs[6]:
        st.subheader("🎯 Configuración Estratégica de Objetivos")
        st.info("Estos objetivos se inyectan automáticamente en los gráficos para medir el rendimiento.")
        
        if role == "presidente":
            st.write("Doble clic en la columna **'Objetivo_Diario'** para modificarlos.")
            edited_obj = st.data_editor(df_obj, num_rows="dynamic", use_container_width=True, hide_index=True)
            
            if st.button("💾 Guardar y Aplicar Cambios", type="primary"):
                save_objectives(edited_obj)
                st.success("¡Objetivos actualizados! Recargando...")
                st.rerun()
        else:
            st.write("*(Modo solo lectura. Solo Presidencia puede editar).*")
            st.dataframe(df_obj.style.format(thousands=","), hide_index=True, use_container_width=True)
