
from st_aggrid import JsCode

AG_GRID_PERCENT_FORMATTER = JsCode(
    """
    function customPercentFormatter(params) {
        let n = Number.parseFloat(params.value) * 100;
        let precision = params.column.colDef.precision ?? 0;

        if (!Number.isNaN(n)) {
          return n.toFixed(precision).replace(/\B(?=(\d{3})+(?!\d))/g, ',')+'%';
        } else {
          return '-';
        }
    }
    """
)

def get_format_value(format=""):
    if format=="%":
        return JsCode(
        """
        function customPercentFormatter(params) {
            let n = Number.parseFloat(params.value) * 100;
            let precision = params.column.colDef.precision ?? 0;

            if (!Number.isNaN(n)) {
            return n.toFixed(precision).replace(/\B(?=(\d{3})+(?!\d))/g, ',')+'%';
            } else {
            return '-';
            }
        }
        """
        )
    
    elif format=="S/.":
        return JsCode(
        """
        function customPercentFormatter2(params) {
        
            let n = Number.parseFloat(params.value);
    
            if (!Number.isNaN(n)) {
            return 'S/. ' + params.value;
            } else {
            return '-';
            }
        }
        """
        )
    else:
        return ""
    
def get_name_model(sigla):
    if sigla=="VC":
        return "Variance-covariance VaR"
    elif sigla=="ES":
        return "Expected Shortfall"
    elif sigla=="HS":
        return "Historical Simulation VaR"
    elif sigla=="MC":
        return "Monte Carlo VaR"
    else:
        return "Ninguno"
        

def get_grid_options(tipo_valueFormatter):

    grid_options = {
    "rowSelection": "single",
    "columnDefs": [
        

        {
        "headerName": "Variance-covariance VaR (VC)" ,
        "children": [
            {
            "field": "vc_95" ,"headerName": "95%" ,  "valueFormatter":get_format_value(tipo_valueFormatter),"precision":2,
            },
        
            {
            "field": "vc_99" ,"headerName": "99%" , "valueFormatter":get_format_value(tipo_valueFormatter),"precision":2,
            }
        ]
        },

        {
        "headerName": "Expected Shortfall (ES)",
        "children": [
            {
            "field": "es_95", "headerName": "95%" ,"valueFormatter":get_format_value(tipo_valueFormatter),"precision":2,
            },

            {
            "field": "es_99" ,"headerName": "99%" , "valueFormatter":get_format_value(tipo_valueFormatter),"precision":2,
            }
        ]
        }
        ,

        {
        "headerName": "Historical Simulation VaR (HS)",
        "children": [
            {
            "field": "hs_95", "headerName": "95%" ,"valueFormatter":get_format_value(tipo_valueFormatter),"precision":2,
            },
        
            {
            "field": "hs_99" ,"headerName": "99%" , "valueFormatter":get_format_value(tipo_valueFormatter),"precision":2,
            }
        ]
        }
    ,

        {
        "headerName": "Monte Carlo VaR (MC)",
        "children": [
            {
            "field": "mc_95", "headerName": "95%" ,"valueFormatter":get_format_value(tipo_valueFormatter),"precision":2,
            },
        
            {
            "field": "mc_99" ,"headerName": "99%" , "valueFormatter":get_format_value(tipo_valueFormatter),"precision":2,
            }
        ]
        }

        

    ],

    "defaultColDef" : {
        "flex": 1,
    },
    
    "autoGroupColumnDef" : {
        "field": "Activo",  
        "headerName": 'País / Sector / Asset',
        "minWidth": 400,
        "cellRendererParams": {
        "suppressCount": False,
        },
    },
    "treeData" :True, 
    "animateRows" :True, 
    #"groupDefaultExpanded" :-1, 

    "getDataPath": JsCode(""" function(data){
        return data.Activo.split("/");
        }""").js_code

    }

    return grid_options