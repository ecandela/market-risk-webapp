import streamlit as st
import pandas as pd
import numpy as np
import os
import json
import time
from io import BytesIO
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.http import MediaIoBaseDownload
from io import StringIO
import requests
import plotly.express as px
import plotly.graph_objects as go
from st_aggrid import AgGrid , JsCode
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode , AgGridTheme
import datetime
from  grid_option import get_grid_options , get_name_model

a = "avc".split("/")
print(a)

st.set_page_config(layout="wide")

st.title('Seguimiento del Valor en Riesgo (VaR) en Economías Emergentes de América Latina')
st.subheader('This is a subheader with a divider')



if "tipo_formato_tabla" not in st.session_state:
    st.session_state.tipo_formato_tabla = "%"

if "df_portafolios_origen" not in st.session_state:

    df = pd.read_csv("portafolios.csv")
    st.session_state.df_portafolios_origen = df

if "df_portafolios" not in st.session_state:

    st.session_state.df_portafolios = st.session_state.df_portafolios_origen.copy() 



def actualizar_df_portafolio():

    monto_inversion = st.session_state.monto_inversion 
    df = st.session_state.df_portafolios_origen.copy()

    excluir_columnas = ['Activo', 'cod_portfolio', 'name_portfolio']

    # Valor específico por el que multiplicar las columnas
    
    # Realizar la multiplicación excluyendo las columnas especificadas
    columnas_a_multiplicar = [col for col in df.columns if col not in excluir_columnas]

    df[columnas_a_multiplicar] = df[columnas_a_multiplicar] * monto_inversion



    if  st.session_state.formato_presentacion  == 'Porcentaje (%)':
        st.session_state.tipo_formato_tabla = "%"
        st.session_state.df_portafolios = st.session_state.df_portafolios_origen.copy()
    else:        
        st.session_state.tipo_formato_tabla = "S/."
        st.session_state.df_portafolios = df.copy()


#st.write(st.session_state.tipo_formato_tabla)




with st.form("my_form"):

    col1_fp, col2_fp, col3_fp = st.columns(3)

    with col1_fp:
        formato_press = st.radio(
            "Formato de presentación",
            ["Porcentaje (%)", "Inversión (S/.)"], 
            
        
            horizontal=True, key="formato_presentacion"
        )
    
        if formato_press == 'Porcentaje (%)':
            st.session_state.form_disabled = True
            
        else:
            st.session_state.form_disabled = False
     
            

    with col2_fp:

        number = st.number_input('Monto de Inversión (S/.)' ,key="monto_inversion")
        
        # Every form must have a submit button.
        
    with col3_fp:
        submitted = st.form_submit_button("Aplicar",on_click=actualizar_df_portafolio)

    

#    vc: Variance-covariance VaR
#    es: Expected Shortfall
#    hs: Historical Simulation VaR
#    mc: Monte Carlo VaR    
    





custom_css = {
   ".ag-theme-alpine .ag-row-odd": {"background": "rgba(243, 247, 249, 0.3) !important","border": "1px solid #eee !important"},
    }



grid_return = AgGrid(st.session_state.df_portafolios, gridOptions=get_grid_options(st.session_state.tipo_formato_tabla), 
                     allow_unsafe_jscode=True,   
                     enable_enterprise_modules=True, 
                     filter=True,
                     fit_columns_on_grid_load=False,
                     custom_css=custom_css,
                     theme=AgGridTheme.ALPINE,   
                     update_mode=GridUpdateMode.SELECTION_CHANGED, 
                     tree_data=True)

selected = grid_return["selected_rows"] 
selected_df = pd.DataFrame(selected).apply(pd.to_numeric, errors='coerce')
#st.write(selected)



class GoogleDriveService:
    def __init__(self):
        self._SCOPES=['https://www.googleapis.com/auth/drive']

    def build(self):

        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["GOOGLE_APPLICATION_CREDENTIALS"], self._SCOPES)
        
        service = build('drive', 'v3', credentials=creds)

        return service 

def getFileListFromGDrive():
    selected_fields="files(id,name,webViewLink)"
    service  =GoogleDriveService().build()
    list_file=service.files().list(fields=selected_fields).execute()
    print({"files":list_file.get("files")})


    file_id = "1g-BC4wL9mSq68XZ31RkVl9ItabP6O1sd"  # Please set the file ID of the CSV file.

    # Descarga el archivo en un objeto de BytesIO
    request = service.files().get_media(fileId=file_id)
    fh = BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()

    # Convierte los datos en un DataFrame
    fh.seek(0)  # Reinicia el puntero del archivo
    data = fh.read().decode('utf-8')  # Decodifica los datos en texto (si es necesario)
    df = pd.read_csv(StringIO(data))  # Crea un DataFrame desde los datos


    return df


with st.sidebar:
    

    

    with st.echo():
        st.write("This code will be printed to the sidebar.")

    today = datetime.datetime.now()
    next_year = today.year + 1
    jan_1 = datetime.date(next_year, 1, 1)
    dec_31 = datetime.date(next_year, 12, 31)

    d = st.date_input(
        "Select your vacation for next year",
        (jan_1, datetime.date(next_year, 1, 7)),
        jan_1,
        dec_31,
        format="MM.DD.YYYY",
    )
  





col1, col2 = st.columns(2)

with col1:

  tipo_var = st.radio("Tipo de modelo de riesgo", ["VC", "ES", "HS","MC"],horizontal=True)
  nombre_tipo_var = get_name_model(tipo_var)

  if not selected_df.empty :
      #st.write(selected[0]["Activo"])
      if "cod_portfolio" in selected[0]:
        cod_portfolio = selected[0]["cod_portfolio"]
        name_portfolio = selected[0]["name_portfolio"]
        activo = selected[0]["Activo"]

        tipo_var_lower = tipo_var.lower()

        nivel_95 = selected[0][f"{tipo_var_lower}_95"]
        nivel_99 = selected[0][f"{tipo_var_lower}_99"]

        activo_parts = activo.split("/")
        if len(activo_parts)>1:
            activo_name = activo_parts[1] +"/"+ activo_parts[2]
        else:
            activo_name = activo_parts[0]

        returns = pd.read_csv(f"returns_{cod_portfolio}.csv")
        data = returns[activo_name]


        nombre_portafolio = ""
        nombre_activo = ""
        # Crear un histograma con Plotly
        fig = px.histogram(data, nbins=50, title=f" {activo}  - {nombre_tipo_var}", text_auto=True,  
                          labels={"count": "Frecuencia", "value": "Valor (k)"})
        

        fig.add_vrect(x0=nivel_99, x1=nivel_95, 
            annotation_text=f"95% : {nivel_95:.4f} ", annotation_position="top right",
            fillcolor="red", opacity=0.1, line_width=1,annotation_textangle = 90, annotation_font=dict(size=16, color="black"))

        fig.add_vrect(x0=np.min(data), x1=nivel_99, 
                    annotation_text=f"99% : {nivel_99:.4f} ", annotation_position="top right",
                    fillcolor="red", opacity=0.3, line_width=1,annotation_textangle = 90, annotation_font=dict(size=16, color="black"))




        fig.update_layout(
            xaxis_title_text = f'P&L (S/.)', 
            yaxis_title_text = 'Frecuencia'
            )

        fig.update_layout(showlegend=False)




        st.plotly_chart(fig, theme="streamlit", use_container_width=True)

with col2:
    
    checks = st.columns(3)
    with checks[0]:
        st.checkbox('95%')
    with checks[1]:
        st.checkbox('97.5%')
    with checks[2]:
        st.checkbox('99%')


    # Datos de ejemplo
    fechas = ['Oct 2019', 'Nov 2019', 'Dic 2019', 'Ene 2020', 'Feb 2020', 'Mar 2020', 'Abr 2020', 'May 2020']
    valores_95 = [100, 150, 120, 200, 180, 220, 250, 240]
    valores_97_5 = [110, 160, 130, 210, 190, 230, 260, 250]
    valores_99 = [120, 170, 140, 220, 200, 240, 270, 260]

    # Crear figura
    fig = go.Figure()

    # Agregar curvas al gráfico
    fig.add_trace(go.Scatter(x=fechas, y=valores_95, mode='lines', name='95%', line=dict(color='black')))
    fig.add_trace(go.Scatter(x=fechas, y=valores_97_5, mode='lines', name='97.5%', line=dict(color='yellow')))
    fig.add_trace(go.Scatter(x=fechas, y=valores_99, mode='lines', name='99%', line=dict(color='blue')))

    # Personalización de ejes y diseño
    fig.update_layout(
        title='Curvas de Valor',
        xaxis=dict(tickvals=list(range(0, len(fechas), len(fechas)//8)), ticktext=fechas[::len(fechas)//8]),
        yaxis=dict(title='value (USD)'),
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    )

    # Mostrar gráfico
    st.plotly_chart(fig, theme="streamlit", use_container_width=True)
    #streamlit run main.py







