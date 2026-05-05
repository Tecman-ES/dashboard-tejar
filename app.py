import re
import pandas as pd
import sys
import pdfplumber

print("=====================================================")
print("🤖 CLONADOR SUBIFOR DESDE PDF - VERSIÓN V26 (HÍBRIDO)")
print("=====================================================")

MAP_CENTROS = {
    'EL TEJAR': 1, 'PALENCIANA': 3, 'MARCHENA': 4, 'CABRA': 5, 
    'PEDRO ABAD': 7, 'BAENA': 9, 'BOGARRE': 13, 'MANCHA REAL': 14, 
    'ESPEJO': 16, 'EXTRACTORA PEDRO ABAD': 17, 'M.REAL': 17, 
    'VETEJAR 12,6 MW': 20, 'AUTOGENERACIÓN 5,7 MW': 21, 'AUTOGENERACION 5,7 MW': 21,
    'BAENA 25 MW': 22, 'ALGODONALES 5,3 MW': 23,
    # Nombres cortos del NUEVO FORMATO
    '12,6 MW': 20, '5,7 MW': 21, '25 MW': 22, '5,3 MW': 23
}

def limpiar_numero(texto):
    if not texto: return 0.0
    t = str(texto).strip().replace('"', '')
    t = re.sub(r'[^\d\.,]', '', t)
    if not t: return 0.0
    if t[-1] in '.,': t = t[:-1]
    if ',' in t and '.' in t:
        if t.rfind(',') > t.rfind('.'): t = t.replace('.', '').replace(',', '.')
        else: t = t.replace(',', '')
    elif ',' in t:
        partes = t.split(',')
        if len(partes[-1]) == 3 and len(partes) > 1: t = t.replace(',', '')
        else: t = t.replace(',', '.')
    elif '.' in t:
        partes = t.split('.')
        if len(partes[-1]) == 3 and len(partes) > 1: t = t.replace('.', '')
    try: return float(t)
    except: return 0.0

def atrapar_lista_nums(planta, texto_bloque):
    if not texto_bloque: return []
    planta_regex = planta.replace(',', r'[,\.]').replace('.', r'[,\.]').replace('N', '[NΝ]').replace('Ó', '[OÓ]').replace(' ', r'\s+')
    for linea in texto_bloque.split('\n'):
        linea_cl = linea.replace('"', '')
        match = re.search(rf'\b{planta_regex}\b', linea_cl, re.IGNORECASE)
        if match:
            resto = linea_cl[match.end():]
            
            # V26: Detección del nuevo formato tabular con Pipes (|)
            if '|' in resto:
                return [limpiar_numero(tok) for tok in resto.split('|') if tok.strip()]
                
            if resto.strip().startswith(','): resto = '0' + resto
            return [limpiar_numero(tok) for tok in re.findall(r'[\d\.,]+', resto)]
    return []

def atrapar_espacial(planta, texto_bloque):
    if not texto_bloque: return {}
    planta_regex = planta.replace(',', r'[,\.]').replace('.', r'[,\.]').replace('N', '[NΝ]').replace('Ó', '[OÓ]').replace(' ', r'\s+')
    for linea in texto_bloque.split('\n'):
        match_planta = re.search(rf'\b{planta_regex}\b', linea, re.IGNORECASE)
        if match_planta:
            r = {f'a{i}':0.0 for i in range(1,14)}
            resto = linea[match_planta.end():]
            
            # V26: Nuevo formato
            if '|' in resto:
                nums = [limpiar_numero(x) for x in resto.split('|') if x.strip()]
                if len(nums) >= 1: r['a1'] = nums[0]
                if len(nums) >= 2: r['a2'] = nums[1]
                if len(nums) >= 3: r['a3'] = nums[2]
                if len(nums) >= 4: r['a4'] = nums[3]
                return r
                
            # Viejo formato
            nums = []
            for m in re.finditer(r'[\d\.,]+', resto):
                nums.append((m.start(), limpiar_numero(m.group())))
            if not nums: return r
            for pos, val in nums:
                if pos < 25: r['a1'] = val
                elif pos < 35: r['a2'] = val
                elif pos < 45: r['a3'] = val
                elif pos < 60: r['a4'] = val
                elif pos > 65: r['a10'], r['a11'], r['a12'] = val, val, val
            return r
    return {}

def atrapar_elec_espacial(planta, texto_bloque):
    if not texto_bloque: return {}
    base_regex = planta.replace(',', r'[,\.]').replace('.', r'[,\.]').replace(' ', r'\s+')
    
    IMANES = {'a1': 24, 'a2': 31, 'a3': 39, 'a4': 50, 'a10': 71}
    
    for linea in texto_bloque.split('\n'):
        match_planta = re.search(rf'\b{base_regex}\b', linea, re.IGNORECASE)
        if match_planta:
            r = {f'a{i}':0.0 for i in range(1,14)}
            resto = linea[match_planta.end():]
            
            # V26: Nuevo formato con pipes
            if '|' in resto:
                nums = [limpiar_numero(x) for x in resto.split('|') if x.strip()]
                if len(nums) >= 1: r['a1'] = nums[0]
                if len(nums) >= 2: r['a2'] = nums[1]
                if len(nums) >= 3: r['a4'] = nums[2] # En el nuevo, el 3º es AÑO (a4)
                return r

            # Viejo formato
            resto_limpio = re.sub(r'^[\s\d\.,]*(?:MW|M\.W\.)', '', resto, flags=re.IGNORECASE)
            offset_absoluto = match_planta.end() + (len(resto) - len(resto_limpio))
            nums_encontrados = []
            for m in re.finditer(r'[\d\.,]+', resto_limpio):
                nums_encontrados.append((offset_absoluto + m.start(), limpiar_numero(m.group())))
            if not nums_encontrados: return r
            for pos, val in nums_encontrados:
                mejor_iman = min(IMANES.keys(), key=lambda k: abs(IMANES[k] - pos))
                if mejor_iman == 'a10': r['a10'], r['a11'], r['a12'] = val, val, val
                else: r[mejor_iman] = val
            return r
    return {}

# --- MAPEOS ESTÁNDAR ---
def map_act1(nums):
    r = {f'a{i}':0.0 for i in range(1,14)}
    if len(nums) == 3: r['a1'], r['a2'], r['a3'] = nums
    elif len(nums) == 2: r['a2'], r['a3'] = nums
    elif len(nums) == 1: r['a3'] = nums[0]
    return r

def map_act2_4(planta, nums, is_deshid=False):
    r = {f'a{i}':0.0 for i in range(1,14)}
    L = len(nums)
    if L >= 5: r['a1'], r['a2'], r['a3'], r['a10'], r['a12'] = nums[:5]
    elif L == 4:
        if planta == 'ESPEJO' and is_deshid: r['a1'], r['a2'], r['a3'], r['a12'] = nums
        elif planta == 'ESPEJO': r['a1'], r['a2'], r['a3'], r['a10'] = nums
        else: r['a2'], r['a3'], r['a10'], r['a12'] = nums
    elif L == 3:
        if planta == 'ESPEJO': r['a2'], r['a3'], r['a10'] = nums
        else: r['a1'], r['a2'], r['a3'] = nums # Nuevo formato
    elif L == 2:
        if planta == 'ESPEJO': r['a3'], r['a10'] = nums
    return r

def map_act3(nums):
    r = {f'a{i}':0.0 for i in range(1,14)}
    if len(nums) >= 10: 
        r['a1'],r['a2'],r['a3'],r['a4'],r['a5'],r['a6'],r['a7'],r['a8'],r['a9'],r['a10'] = nums[:10]
    elif len(nums) == 3: 
        r['a1'], r['a2'], r['a3'] = nums # Nuevo formato
    return r

def map_act5(planta, nums):
    r = {f'a{i}':0.0 for i in range(1,14)}
    if len(nums) == 4: r['a1'], r['a2'], r['a3'], r['a12'] = nums
    elif len(nums) == 3: r['a1'], r['a2'], r['a3'] = nums # Nuevo formato
    return r

def map_deshid_out(nums):
    r = {f'a{i}':0.0 for i in range(1,14)}
    if len(nums) == 9: 
        for i in range(9): r[f'a{i+1}'] = nums[i]
    elif len(nums) == 3: r['a1'],r['a2'],r['a3'] = nums # Nuevo formato
    return r

def map_extraccion(nums, is_aceite):
    r = {f'a{i}':0.0 for i in range(1,14)}
    if len(nums) >= 4: r['a1'], r['a2'], r['a3'], r['a10'] = nums[:4]
    elif len(nums) == 3: r['a1'], r['a2'], r['a3'] = nums
    return r

def extraer_y_clonar_subifor(ruta_pdf):
    with pdfplumber.open(ruta_pdf) as pdf:
        texto_limpio = "\n".join([p.extract_text(layout=True) for p in pdf.pages if p.extract_text(layout=True)]).replace(',,', ',0,')
    
    match_fecha = re.search(r'(\d{2}/\d{2}/\d{4})', texto_limpio)
    fecha_pdf = match_fecha.group(1) if match_fecha else "01/01/2026"
    
    b_ex = re.search(r'EXISTENCIAS(.*?)APORT\. DE ORUJO', texto_limpio, re.S)
    b_ap = re.search(r'APORT\. DE ORUJO(.*?)ENTRADA CENTRIFUG', texto_limpio, re.S)
    b_c_in = re.search(r'ENTRADA CENTRIFUG.*?(?:ALPERUJO)(.*?)(?:SALIDA CENTRIFUG|ENTRADA SECADO)', texto_limpio, re.S)
    b_c_out = re.search(r'SALIDA CENTRIFUG.*?ACEITE(.*?)(?:ENTRADA SECADO|ENTRADA DESHIDRA|EXISTENCIAS)', texto_limpio, re.S)
    b_s_in = re.search(r'ENTRADA SECADO(.*?)(?:ENTRADA DESHIDRA|SECADO SALIDA)', texto_limpio, re.S)
    b_s_out = re.search(r'SECADO SALIDA(.*?)(?:DESHIDRATACION SALIDA|EXTRACTORA TEJAR|PRODUCCIÓN ENERGÍA)', texto_limpio, re.S)
    b_e_tej = re.search(r'EXTRACTORA TEJAR(.*?)EXTRACTORA BAE', texto_limpio, re.S)
    b_e_bae = re.search(r'EXTRACTORA BAE(.*?)(?:EXTRACTORA ESP|EXTRACTORA P\.ABAD|ELECTRICIDAD)', texto_limpio, re.S)
    b_elec = re.search(r'(?:ELECTRICIDAD|PRODUCCIÓN ENERGÍA)(.*?)(?:SALIDA DE ACEITE|EXTRACTORA|CONSUMO DIARIO|$)', texto_limpio, re.S)
    
    bloques = {
        "EX": b_ex.group(1) if b_ex else "", "AP": b_ap.group(1) if b_ap else "",
        "C_IN": b_c_in.group(1) if b_c_in else "", "C_OUT": b_c_out.group(1) if b_c_out else "",
        "S_IN": b_s_in.group(1) if b_s_in else "", "S_OUT": b_s_out.group(1) if b_s_out else "",
        "ELEC": b_elec.group(1) if b_elec else "",
    }

    filas = []
    def add_row(act, act1, centro_code, nombre, dict_data):
        f = {'fecha': f"{fecha_pdf} 0:00", 'actividad': act, 'actividad1': act1, 'centro': centro_code, 'nombre_c': str(nombre).upper()}
        for i in range(1, 14): f[f'a{i}'] = dict_data.get(f'a{i}', 0.0)
        filas.append(f)

    for p in ['EL TEJAR','PALENCIANA','MARCHENA','CABRA','PEDRO ABAD','BAENA','MANCHA REAL','ESPEJO']:
        nx = atrapar_espacial(p, bloques['EX']); add_row(0, 0, MAP_CENTROS[p], p, nx) if sum(nx.values())>0 else None
    for p in ['PALENCIANA','MARCHENA','CABRA','PEDRO ABAD','BAENA','BOGARRE','MANCHA REAL','ESPEJO']:
        nx = map_act1(atrapar_lista_nums(p, bloques['AP'])); add_row(1, 0, MAP_CENTROS[p], p, nx) if sum(nx.values())>0 else None
    for p in ['PALENCIANA','MARCHENA','CABRA','BAENA']:
        n_in = map_act2_4(p, atrapar_lista_nums(p, bloques['C_IN'])); add_row(2, 0, MAP_CENTROS[p], p, n_in) if sum(n_in.values())>0 else None
        n_ou = map_act3(atrapar_lista_nums(p, bloques['C_OUT'])); add_row(3, 0, MAP_CENTROS[p], p, n_ou) if sum(n_ou.values())>0 else None
    
    # ELECTRICIDAD V26: Busca los nombres cortos, pero los inyecta con el nombre largo oficial
    for p in ['12,6 MW', '5,7 MW', '25 MW', '5,3 MW']:
        nx = atrapar_elec_espacial(p, bloques['ELEC'])
        if sum(nx.values()) > 0:
            nombre_oficial = {'12,6 MW':'VETEJAR 12,6 MW', '5,7 MW':'AUTOGENERACION 5,7 MW', '25 MW':'BAENA 25 MW', '5,3 MW':'ALGODONALES 5,3 MW'}[p]
            add_row(8, 0, MAP_CENTROS[p], nombre_oficial, nx)

    return pd.DataFrame(filas) if filas else pd.DataFrame()

def generar_clon_subifor(df_subifor, ruta_salida):
    cols = ['fecha', 'actividad', 'actividad1', 'centro', 'nombre_c', 'a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 'a8', 'a9', 'a10', 'a11', 'a12', 'a13', 'marca']
    
    # 🛡️ PARACAÍDAS ANTI-CRASH
    if df_subifor.empty:
        print("⚠️ AVISO: El PDF está vacío o la fuente está corrupta. Se genera CSV en blanco.")
        pd.DataFrame(columns=cols).to_csv(ruta_salida, index=False, sep=';')
        return

    for c in cols:
        if c not in df_subifor.columns: df_subifor[c] = 0.0
            
    df_out = df_subifor[cols].copy()
    
    def fmt(x):
        try:
            if pd.isna(x): return "0"
            s = f"{float(x):.6f}".rstrip('0').rstrip('.')
            return s.replace('.', ',') if s else "0"
        except: return "0"
        
    for c in cols[5:18]: 
        df_out[c] = df_out[c].apply(fmt)
        
    df_out.to_csv(ruta_salida, index=False, sep=';')

if __name__ == "__main__":
    if len(sys.argv) > 1:
        df = extraer_y_clonar_subifor(sys.argv[1])
        generar_clon_subifor(df, sys.argv[1].lower().replace(".pdf", ".csv"))
