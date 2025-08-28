import streamlit as st
import pandas as pd
import math
import json
import io
import os
import streamlit.components.v1 as components

# --- CSS personalizado ---
st.markdown("""
<style>
/* Fondo oscuro general */
.stApp {
    background-color: ##323052;
    color: #e0e0e0;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
/* Título principal centrado y estilizado */
.title-bar {
    background-color: #F6E51C;
    color: #2a2a2a !important;
    padding: 20px 25px;
    font-size: 36px;
    font-weight: 800;
    text-align: center;
    margin-bottom: 30px;
    border-radius: 12px;
    box-shadow: 0 0 15px #d4c514;
}
/* Barra lateral */
.css-1d391kg, .css-1v3fvcr .stSidebar {
    background-color: #3c3c3c;
    padding: 15px;
    border-radius: 8px;
}
/* Botones */
.stButton > button {
    background-color: #F6E51C;
    color: #2a2a2a;
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-weight: 700;
    width: 100%;
    box-shadow: 0 2px 5px rgba(246, 229, 28, 0.6);
    transition: all 0.3s ease;
}
.stButton > button:hover {
    background-color: #d4c514;
    color: #1a1a1a;
}
/* Inputs y textareas */
.stTextInput input, .stNumberInput input, .stTextArea textarea {
    background-color: #3c3c3c !important;
    color: #ffffff !important;
    border: 2px solid transparent !important;
    border-radius: 6px;
    padding: 6px;
}
.stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
    border-color: #F6E51C !important;
    box-shadow: 0 0 8px #F6E51C !important;
    background-color: #3c3c3c !important;
}
/* Labels importantes */
label, .input-label {
    color: #F6E51C;
    font-weight: 600;
}
/* Tablas y áreas de texto */
.stDataFrame, .stTextArea {
    background-color: ##323052;
    color: #e0e0e0;
}
/* Encabezados secundarios */
h2, h3, h4 {
    color: #F6E51C;
}
</style>
""", unsafe_allow_html=True)

# Carpeta donde se guardarán los datos para persistencia
SAVE_DIR = "datos_guardados"
os.makedirs(SAVE_DIR, exist_ok=True)

# Funciones de persistencia
def guardar_respuesta(grupo_id, data):
    path = os.path.join(SAVE_DIR, f"grupo_{grupo_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def cargar_respuesta(grupo_id):
    path = os.path.join(SAVE_DIR, f"grupo_{grupo_id}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return ""

def limpiar_todo():
    for filename in os.listdir(SAVE_DIR):
        file_path = os.path.join(SAVE_DIR, filename)
        os.remove(file_path)
    st.session_state.clear()

# Configuración de la página
st.set_page_config(page_title="Procesador de comparables", layout="wide")
st.markdown('<div class="title-bar">Procesador de Comparables</div>', unsafe_allow_html=True)

# Botón limpiar todo en sidebar
if st.sidebar.button("🗑️ Limpiar todo"):
    limpiar_todo()
    st.experimental_rerun()

# Subida de archivo Excel
uploaded_file = st.file_uploader(
    "Sube un archivo Excel con columnas: Activo, Descripción y Marca", 
    type=["xlsx", "xls"]
)

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    expected_cols = {"Activo", "Descripción", "Marca"}
    
    if not expected_cols.issubset(set(df.columns)):
        st.error(f"El archivo debe contener las columnas: {expected_cols}")
    else:
        df['Combinado'] = df['Activo'].astype(str) + "///" + df['Descripción'].astype(str) + "///" + df['Marca'].astype(str)
        st.subheader("Vista previa de datos combinados")
        st.dataframe(df[['Combinado']].head(10))

        # Selección de tamaño de grupo
        group_size = st.number_input("Selecciona cuántos productos por grupo", min_value=1, value=3)
        num_groups = math.ceil(len(df) / group_size)
        st.write(f"Se generarán {num_groups} grupo(s).")
        st.markdown("---")

        st.subheader("Grupos generados y texto listo para copiar y analizar respuestas")

        # Inicializamos lista en session_state para almacenar DataFrames
        if 'all_groups_dfs' not in st.session_state:
            st.session_state['all_groups_dfs'] = []

        # Sidebar: índice de grupos
        grupos = [f"Grupo {i+1}" for i in range(num_groups)]
        selected_group = st.sidebar.selectbox("Ir a un grupo", ["Todos los grupos"] + grupos)

        for g in range(num_groups):
            group_name = f"Grupo {g+1}"
            
            if selected_group != "Todos los grupos" and selected_group != group_name:
                continue

            start_idx = g * group_size
            end_idx = min((g + 1) * group_size, len(df))
            group_df = df.iloc[start_idx:end_idx]

            enumerated_rows = [f"{i}) {row}" for i, row in enumerate(group_df['Combinado'], start=1)]
            group_text = "\n".join(enumerated_rows)

            # Plantilla del prompt
            final_text = f"""Eres un avaluador experto y estas en el proceso de buscar equipos y estructuras que sean comparables a las características de los siguientes equipos que te describo con nombre, descripción y marcas separados por /// y enumerados que te doy después de los asterísticos*** 
{group_text}
***. con estos datos tendrás la siguiente tarea: 
- Para cada uno de los productos enumerados en este grupo, busca **exactamente 3 productos similares en internet** (de cualquier marca). 
- Entrega **solo 3 resultados por producto**, ni más ni menos.
- Cada resultado debe incluir:
    - Precio del producto y moneda
    - Link donde encontraste la información

Formato de entrega:

{{ "Producto": "Nombre del producto original", 
"Descripción": "Descripción del producto original",
 "Marca": "Marca del producto original",
  "Resultados": {{
     "Comparable 1 en US": "Precio en USD del primer producto comparable",
     "Comparable 2 en US": "Precio en USD del segundo producto comparable",
     "Comparable 3 en US": "Precio en USD del tercer producto comparable",
     "Fuente comparable 1": "NACIONAL o INTERNACIONAL",
     "Fuente comparable 2": "NACIONAL o INTERNACIONAL", 
     "Fuente comparable 3": "NACIONAL o INTERNACIONAL",
     "Link de comparable 1": "URL del producto comparable 1",
     "Link de comparable 2": "URL del producto comparable 2", 
     "Link de comparable 3": "URL del producto comparable 3" 
     }} 
}}

Consideraciones:
- Prioriza productos que tengan precio visible. Si no hay precio, deja el campo vacío.
- El objetivo principal es obtener un rango de precios entre equipos similares.
- Los productos deben ser del mismo tipo y capacidad.
- Asegúrate de que los links estén activos y que funcionen correctamente.
- Usa el formato JSON proporcionado sin cambios.
- No agregues nada fuera del formato solicitado.
- La extracción debe ser precisa y coherente.
- Realiza una búsqueda rigurosa por internet.
- Verifica que las páginas estén activas y que los links no den error 404.
- Entrega solo el formato JSON
"""

            st.markdown(f"### {group_name}")

            col1, col2 = st.columns([1, 1])

            with col1:
                st.markdown("#### Prompt para LLM")
                st.text_area(f"Texto {group_name}", value=final_text, height=350, key=f"text_area_{g}")

                # Botón copiar prompt
                safe_text = final_text.replace("`", "'")
                components.html(f"""
                    <script>
                    function copyToClipboard{g}() {{
                        navigator.clipboard.writeText(`{safe_text}`).then(() => {{
                            var btn = document.getElementById("btn{g}");
                            btn.innerText = "✅ Copiado!";
                            btn.style.backgroundColor = "#4CAF50";
                            setTimeout(() => {{
                                btn.innerText = "Copiar {group_name}";
                                btn.style.backgroundColor = "#F6E51C";
                            }}, 2000);
                        }});
                    }}
                    </script>
                    <button id="btn{g}" onclick="copyToClipboard{g}()" style="
                        margin-top:5px; padding:10px 15px; 
                        background-color:#F6E51C; color:#2a2a2a; 
                        border:none; border-radius:5px;
                        font-weight:bold;">Copiar {group_name}</button>
                """, height=50)

            with col2:
                st.markdown("#### Pegar Respuesta del LLM")
                
                saved_response = cargar_respuesta(g)
                
                response_text = st.text_area(
                    f"Respuesta LLM {group_name}",
                    height=350,
                    key=f"llm_response_{g}",
                    value=saved_response,
                    placeholder="Pega aquí la respuesta JSON del LLM"
                )

                if response_text.strip():
                    guardar_respuesta(g, response_text)
                    try:
                        response_data = json.loads(response_text)
                        if isinstance(response_data, dict):
                            response_data = [response_data]
                        
                        rows = []
                        for item in response_data:
                            fila = {
                                "Producto": item.get("Producto", ""),
                                "Descripción": item.get("Descripción", ""),
                                "Marca": item.get("Marca", "")
                            }
                            resultados = item.get("Resultados", {})
                            fila.update(resultados)
                            rows.append(fila)
                        
                        df_resultados = pd.DataFrame(rows)
                        st.dataframe(df_resultados)

                        towrite = io.BytesIO()
                        df_resultados.to_excel(towrite, index=False, engine='xlsxwriter')
                        towrite.seek(0)
                        st.download_button(
                            label=f"📥 Descargar Excel {group_name}",
                            data=towrite,
                            file_name=f"{group_name}_Resultados.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )

                        st.session_state['all_groups_dfs'].append((group_name, df_resultados))

                    except Exception as e:
                        st.error(f"Error al procesar la respuesta: {e}")

            st.markdown("---")

        if st.session_state['all_groups_dfs']:
            towrite_all = io.BytesIO()
            with pd.ExcelWriter(towrite_all, engine='xlsxwriter') as writer:
                for nombre, df_grp in st.session_state['all_groups_dfs']:
                    df_grp.to_excel(writer, sheet_name=nombre, index=False)
            towrite_all.seek(0)
            st.download_button(
                label="📥 Descargar Excel Todos los Grupos",
                data=towrite_all,
                file_name="Todos_Grupos_Resultados.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

