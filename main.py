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

st.set_page_config(layout="wide")


df = pd.DataFrame({"Desk_Book_Asset": [ "Fixed Income", "Fixed Income/bonos gubernamentales" , "Fixed Income/bonos corporativos de alto rendimiento"  ], 
                    "V_s_90": [1, 2, 3], "V_s_95": [3, 4, 5], "V_s_99": [4, 5, 6],"V_h_90": [9, 9, 9], "V_h_95": [10, 10, 10], "V_h_99": [11, 11, 11]})

grid_options = {
  "rowSelection": "single",
  "columnDefs": [
    

    {
      "headerName": "VaR Estresado Histórico" ,
      "children": [
        {
          "field": "V_s_90" ,"headerName": "90%" , 
        },
        {
          "field": "V_s_95" ,"headerName": "95%" , 
        },
        {
          "field": "V_s_99" ,"headerName": "99%" , 
        }
      ]
    },

    {
      "headerName": "VaR Histórico",
      "children": [
        {
          "field": "V_h_90", "headerName": "90%" ,
        },
        {
          "field": "V_h_95","headerName": "95%" , 
        },
        {
          "field": "V_h_99" ,"headerName": "99%" , 
        }
      ]
    }

  ],

  "defaultColDef" : {
      "flex": 1,
  },
  
  "autoGroupColumnDef" : {
    "field": "Desk_Book_Asset",  
    "headerName": 'Desk / Book / Asset',
    "minWidth": 400,
    "cellRendererParams": {
      "suppressCount": False,
    },
  },
  "treeData" :True, 
  "animateRows" :True, 
  "groupDefaultExpanded" :-1, 

  "getDataPath": JsCode(""" function(data){
      return data.Desk_Book_Asset.split("/");
    }""").js_code

}

custom_css = {
   ".ag-theme-alpine .ag-row-odd": {"background": "rgba(243, 247, 249, 0.3) !important","border": "1px solid #eee !important"},
    }


grid_return = AgGrid(df, gridOptions=grid_options, 
                     allow_unsafe_jscode=True,   
                     enable_enterprise_modules=True, 
                     filter=True,
                     custom_css=custom_css,
                     theme=AgGridTheme.ALPINE,   
                     update_mode=GridUpdateMode.SELECTION_CHANGED, 
                     tree_data=True)

selected = grid_return["selected_rows"] 
st.write(selected)

# Mostrar la tabla en Streamlit


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

tab1, tab2, tab3 = st.tabs(["Cat", "Dog", "Owl"])

with tab1:
   st.header("A cat")
   ''' 
   df_data = getFileListFromGDrive()

   grid_response = AgGrid(
        df_data, 
        height=500, 
        width='100%',        

   )
   '''


with tab2:
   st.header("A dog")
   st.image("https://static.streamlit.io/examples/dog.jpg", width=200)


with tab3:
   st.header("An owl")
   st.image("https://static.streamlit.io/examples/owl.jpg", width=200)



col1, col2 = st.columns(2)

with col1:
   st.header("A cat")

   np.random.seed(42)
   data = np.random.normal(0, 10000, 1000)  # Generar 1000 valores con media 0 y desviación estándar 10000

   percentil_deseado = 1  # Cambia este valor al percentil que necesitas
   valor_percentil = np.percentile(data, percentil_deseado)

   print("valor_percentil : ",valor_percentil)
   print("min : ",np.min(data))

   # Crear un histograma con Plotly
   fig = px.histogram(data, nbins=20, title="Histograma de Valores", labels={"count": "Frecuencia", "value": "Valor (k)"})

   # Cambiar etiquetas en el eje x para indicar miles (posfijo "k")
   fig.update_xaxes(tickvals=[-50000, -40000, -30000, -20000, -10000, 0, 10000, 20000, 30000, 40000, 50000],
                    ticktext=["-50k", "-40k", "-30k", "-20k", "-10k", "0", "10k", "20k", "30k", "40k", "50k"])
   
   fig.add_vrect(x0=np.min(data), x1=valor_percentil, 
              annotation_text="decline", annotation_position="top left",
              fillcolor="red", opacity=0.25, line_width=0)


   st.plotly_chart(fig, theme="streamlit", use_container_width=True)

with col2:
    st.header("A dog")


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







