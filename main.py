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
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode , AgGridTheme , ColumnsAutoSizeMode
import datetime
from  grid_option import get_grid_options , get_name_model
from sqlalchemy import create_engine, inspect
import io

# buffer to use for excel writer
buffer = io.BytesIO()



def get_data_from_table(table="",engine=None, index_col=None,parse_dates=None):
    engine = engine
    query = f"SELECT * FROM {table} "
    df = pd.read_sql_query(query, engine,index_col=index_col,parse_dates=parse_dates)

    # Cierra la conexión a la base de datos
    engine.dispose()
    return df


st.set_page_config(layout="wide")

st.title('Monitoreo del VaR en Economías Emergentes de América Latina')
st.subheader('Riesgo por países')

if "engine" not in st.session_state:
    engine_str = st.secrets["engine"]
    engine = create_engine(engine_str)

    df = get_data_from_table(table="portafolios",engine=engine)
    st.session_state.df_portafolios_origen = df

    cod_portfolio_list = ["arg","bra","chl","col","mex","pe"]

    list_rt = []
    list_bt = []

    for cod_portfolio in cod_portfolio_list:

        returns_name = f"returns_{cod_portfolio}"
        returns = get_data_from_table(table=returns_name,engine=engine)
        returns["cod_portfolio"]=cod_portfolio

        backtesting_name = f"backtesting_{cod_portfolio}"
        df_backtesting = get_data_from_table(table=backtesting_name,engine=engine)
        df_backtesting["cod_portfolio"]=cod_portfolio

        list_rt.append(returns)
        list_bt.append(df_backtesting)
    

    st.session_state.returns = pd.concat(list_rt)
    st.session_state.df_backtesting = pd.concat(list_bt)


   

if "engine" not in st.session_state:

    engine = create_engine('postgresql://fl0user:MLYK9dmVOB4T@ep-super-field-51954597.us-east-2.aws.neon.fl0.io/dw-market-risk')
    st.session_state.engine = engine

if "tipo_formato_tabla" not in st.session_state:
    st.session_state.tipo_formato_tabla = "%"


    

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
    df[columnas_a_multiplicar] = df[columnas_a_multiplicar].round(2)


    if  st.session_state.formato_presentacion  == 'Porcentaje (%)':
        st.session_state.tipo_formato_tabla = "%"
        st.session_state.df_portafolios = st.session_state.df_portafolios_origen.copy()
    else:        
        st.session_state.tipo_formato_tabla = "S/."
        st.session_state.df_portafolios = df.copy()


#st.write(st.session_state.tipo_formato_tabla)




#with st.form("my_form"):

if "formato_presentacion" not in st.session_state:
    st.session_state.visibility = "visible"
    st.session_state.disabled = False
    st.session_state.horizontal = False

col1_fp, col2_fp, col3_fp, col4_fp = st.columns(4)

with col1_fp:
    formato_press = st.radio(
        "Formato de presentación",
        ["Porcentaje (%)", "Inversión (S/.)"], 
        
    
        horizontal=True, key="formato_presentacion"
    )

    if formato_press == 'Porcentaje (%)':
        formato_percen = True 
        
    else:
        formato_percen = False

        

with col2_fp:


    number = st.number_input('Monto de Inversión (S/.)' ,key="monto_inversion", disabled=formato_percen , value=100)
        
        # Every form must have a submit button.
        
    #with col3_fp:
    #    st.write('')
    #    st.write('')
    #    submitted = st.form_submit_button("Actualizar",on_click=actualizar_df_portafolio, type="primary")

    

#    vc: Variance-covariance VaR
#    es: Expected Shortfall
#    hs: Historical Simulation VaR
#    mc: Monte Carlo VaR    
    

if 'clicked' not in st.session_state:
    st.session_state.clicked = False

def click_button():
    st.session_state.clicked = True

with col3_fp:
    st.write('')
    st.write('')
    st.button('Actualizar', on_click=click_button)

    if st.session_state.clicked:
        
        
        # The message and nested widget will remain on the page
        actualizar_df_portafolio()


with col4_fp:
    st.write('')
    st.write('')
    # download button 2 to download dataframe as xlsx

        



custom_css = {
   ".ag-theme-alpine .ag-row-odd": {"background": "rgba(243, 247, 249, 0.3) !important","border": "1px solid #eee !important"},
    }



grid_return = AgGrid(st.session_state.df_portafolios, gridOptions=get_grid_options(st.session_state.tipo_formato_tabla), 
                     allow_unsafe_jscode=True,   
                     enable_enterprise_modules=True, 
                     filter=True,
                     #fit_columns_on_grid_load=True,
                     custom_css=custom_css,
                     theme=AgGridTheme.ALPINE,   
                     update_mode=GridUpdateMode.SELECTION_CHANGED, 
                     columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
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


#with st.sidebar:
    
#    today = datetime.datetime.now()
#    next_year = today.year + 1
#    jan_1 = datetime.date(next_year, 1, 1)
#    dec_31 = datetime.date(next_year, 12, 31)

#    d = st.date_input(
#        "Rango de fechas",
#        (jan_1, datetime.date(next_year, 1, 7)),
#        jan_1,
#        dec_31,
#        format="MM.DD.YYYY",
#    )
  



if not selected_df.empty :
    st.session_state.clicked = False
    #st.write(selected[0]["Activo"])
    if "cod_portfolio" in selected[0]:
        cod_portfolio = selected[0]["cod_portfolio"]
        name_portfolio = selected[0]["name_portfolio"]
        activo = selected[0]["Activo"]

        activo_parts = activo.split("/")
        if len(activo_parts)>1:
            activo_name = activo_parts[1] +"/"+ activo_parts[2]
        else:
            activo_name = activo_parts[0]

        col1, col2 = st.columns(2)

        with col1:

            st.subheader('Distribución')

            tipo_var = st.radio("Tipo de modelo de riesgo", ["VC", "ES", "HS","MC"],horizontal=True)
            nombre_tipo_var = get_name_model(tipo_var)

            tipo_var_lower = tipo_var.lower()

            nivel_95 = selected[0][f"{tipo_var_lower}_95"]
            nivel_99 = selected[0][f"{tipo_var_lower}_99"]



            #returns = pd.read_csv(f"returns_{cod_portfolio}.csv")
            #returns_name = f"returns_{cod_portfolio}"
            #returns = get_data_from_table(table=returns_name)

            returns = st.session_state.returns.copy()
            returns = returns[returns["cod_portfolio"]==cod_portfolio].copy() 
            returns.drop('cod_portfolio', axis=1, inplace=True)

   
            if  st.session_state.formato_presentacion  == 'Porcentaje (%)':
              
                data = returns[activo_name]     

                annotation_text_95 = f"95% : {nivel_95:.2%}"
                annotation_text_99 = f"99% : {nivel_99:.2%}"

            else:        
        
                data = returns[activo_name]*st.session_state.monto_inversion 
                #nivel_95 = nivel_95*st.session_state.monto_inversion 
                #nivel_99 = nivel_99*st.session_state.monto_inversion 

                annotation_text_95 = f"95% : {nivel_95:.2f}"
                annotation_text_99 = f"99% : {nivel_99:.2f}"


            nombre_portafolio = ""
            nombre_activo = ""
            # Crear un histograma con Plotly
            fig = px.histogram(data, nbins=50, title=f" {activo}  - {nombre_tipo_var}", text_auto=True,  
                            labels={"count": "Frecuencia", "value": "Valor (k)"})
            

            fig.add_vrect(x0=nivel_99, x1=nivel_95, 
                annotation_text=annotation_text_95, annotation_position="top right",
                fillcolor="red", opacity=0.1, line_width=1,annotation_textangle = 90, annotation_font=dict(size=16, color="black"))

            fig.add_vrect(x0=np.min(data), x1=nivel_99, 
                        annotation_text=annotation_text_99, annotation_position="top right",
                        fillcolor="red", opacity=0.3, line_width=1,annotation_textangle = 90, annotation_font=dict(size=16, color="black"))


            tipo_formato_tabla = st.session_state.tipo_formato_tabla

            fig.update_layout(
                xaxis_title_text = f'P&L ({tipo_formato_tabla})', 
                yaxis_title_text = 'Frecuencia'
                )

            fig.update_layout(showlegend=False)




            st.plotly_chart(fig, theme="streamlit", use_container_width=True)

        with col2:

            st.subheader('Backtesting')
            
            checks = st.columns(3)
            with checks[0]:
                st.write("Nivel de Significancia: ")
            with checks[1]:
                z95 = st.checkbox('95%', value=True)
            with checks[2]:
                z99 =st.checkbox('99%', value=False)

            #df_backtesting = pd.read_csv(f"backtesting_{cod_portfolio}.csv")

            #backtesting_name = f"backtesting_{cod_portfolio}"
            #df_backtesting = get_data_from_table(table=backtesting_name)
            #st.session_state.df_backtesting = pd.concat(list_bt)
            
            df_backtesting = st.session_state.df_backtesting.copy()
            df_backtesting = df_backtesting[df_backtesting["cod_portfolio"]==cod_portfolio].copy() 
            df_backtesting.drop('cod_portfolio', axis=1, inplace=True)

            df_backtesting.datetime = pd.to_datetime(df_backtesting.datetime)
            

            df_backtesting_sel = df_backtesting[df_backtesting["Activo"]==activo].copy()
            df_backtesting_sel.set_index('datetime', inplace=True)

            config_bacttest =[

            {"name":'PnL',     "color":'#229954', "values": df_backtesting_sel["PnL"] },
            {"name":'VC 95%',  "color":'#EC7063', "values": df_backtesting_sel["vc_95"] },
            {"name":'HS 95%',  "color":'#9B59B6', "values": df_backtesting_sel["hs_95"] },
            {"name":'MC 95%',  "color":'#2980B9', "values": df_backtesting_sel["mc_95"] },
            {"name":'ES 95%',  "color":'#D4AC0D', "values": df_backtesting_sel["es_95"] },
            {"name":'VC 99%',  "color":'#7B241C', "values": df_backtesting_sel["vc_99"] },
            {"name":'HS 99%',  "color":'#76448A', "values": df_backtesting_sel["hs_99"] },
            {"name":'MC 99%',  "color":'#4A235A ', "values": df_backtesting_sel["mc_99"] },
            {"name":'ES 99%',  "color":'#784212 ', "values": df_backtesting_sel["es_99"] },


            ]


            config_bacttest = [item for item in config_bacttest if
                  item['name'] == 'PnL' or ((z95 and '95%' in item['name']) or (z99 and '99%' in item['name']))]


            ######## generando data de bacttesting ####################

            fig = go.Figure()
            fechas_df_backtesting_sel = df_backtesting_sel.index

            fechas_formateadas = fechas_df_backtesting_sel.strftime('%d/%m/%y')

            tipo_formato_tabla = st.session_state.tipo_formato_tabla

            
            
            
            for item in config_bacttest:

                if  tipo_formato_tabla=="S/.":
                    values_bt = item["values"]*st.session_state.monto_inversion      
                else:
                    values_bt = item["values"]      


                # Agregar curvas al gráfico
                fig.add_trace(go.Scatter(x=fechas_formateadas, y=values_bt, mode='lines+markers', name=item["name"], line=dict(color=item["color"]), marker=dict(size=5, color='black', line=dict(width=2))   ))

            # Personalización de ejes y diseño
            fig.update_layout(
            
                yaxis=dict(title=f"{tipo_formato_tabla}"),
                legend=dict(yanchor="top", y=1.02, xanchor="right", x=1.1),
                margin=dict(l=1, r=1, t=1, b=1)  

            )


            fig.update_xaxes(
                title_text='Fechas',
                tickangle=-45,  # Ángulo de inclinación de las fechas
                showline=True,
                showgrid=False,
                #range=[fechas_formateadas[0], fechas_formateadas[-1]],  # Ajusta el rango de fechas
                zeroline=False,
            
            )

            # Mostrar gráfico
            st.plotly_chart(fig, theme="streamlit", use_container_width=True)
            #streamlit run main.py









