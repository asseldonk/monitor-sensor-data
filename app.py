import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input
from flask import send_from_directory
import os
from influxdb import DataFrameClient
import pandas as pd
from pytz import timezone



# read database
def read_db(db_name, measurement, period):
    # read  from database and fill data into pandas dataframe
    client = DataFrameClient(host     = 'localhost',
                             port     = 8086,
                             database = db_name)
    result = client.query('select * from ' + measurement + ' where time > now()-' + period, chunked=True)
    column = next(iter(result))
    data   = result[column]
    # convert utc time to local time
    data.index = data.index.tz_convert('Europe/Berlin')
    # hack due to (plotly tries to use utc time first):
    # https://github.com/plotly/plotly.py/blob/6f9621a611da36f10678c9d9c8c784f55e472429/plotly/utils.py#L263
    data.index = data.index.tz_localize(None)
    return data


# create layout object
def get_layout(data, item, yaxis_title):
    min_x = data.index[0] if (data is not None and not data.empty) else -1
    max_x = data.index[-1] if (data is not None and not data.empty) else 1
    min_y = data[item].min()-4. if (data is not None and not data.empty) else -1
    max_y = data[item].max()+4. if (data is not None and not data.empty) else 1
    return {
            'font'          : {'color' : 'rgb(240,240,240)'},
            'title'         : item,
            'plot_bgcolor'  : '#242424',
            'paper_bgcolor' : '#242424',
            'line'          : {'color' : 'rgb(224,72,66)'},
            'marker'        : {'color' : 'rgb(224,72,66)'},
            'xaxis'         : {
                              'title'     : 'time',
                              'range'     : [min_x, max_x],
                              'tickcolor' : 'rgb(80,80,80)',
                              'gridcolor' : 'rgb(80,80,80)',
                              'linecolor' : 'rgb(80,80,80)'
            },
            'yaxis'         : {
                              'title'     : yaxis_title,
                              'range'     : [min_y, max_y],
                              'tickcolor' : 'rgb(80,80,80)',
                              'gridcolor' : 'rgb(80,80,80)',
                              'linecolor' : 'rgb(80,80,80)'
            }
    }


# create data object
def get_data(data, item, color):
    return {
          'x'      : data.index,
          'y'      : data[item],
          'name'   : 'lines+markers',
          'mode'   : 'lines+markers',
          'marker' : {
                     'color' : color,
                     'line'  : {'color' : color}
          },
          'line'   : {
                      'color' : color,
          }
    }



# default data
data = read_db('sensor_data', 'autogen.mean_60s', '1d')
# dash
app  = dash.Dash()
app.layout = html.Div(
    [
        html.Link(
            rel  = 'stylesheet',
            href = '/static/css/main.css'
        ),
        html.H1('Sensor Data'),
        # temperatur graph
        dcc.Graph(id      = 'graph-temperature',
                  figure  = {
                        'data'   : [get_data(data, 'temperature', 'rgb(224,72,66)')],
                        'layout' : get_layout(data, 'temperature', 'temperature &deg;C')
                  }
        ),
        dcc.Interval(id          = 'interval-component',
                     interval    = 1*60000,
                     n_intervals = 0
        ),
    ]
)


# css file
@app.server.route('/static/<path:path>')
def static_file(path):
    static_folder = os.path.join(os.getcwd(), 'static')
    return send_from_directory(static_folder, path)


# update temperature graph
@app.callback(Output('graph-temperature', 'figure'),
              [Input('interval-component', 'n_intervals')])
def update_graph_scatter(n):
    db_name     = 'sensor_data'
    measurement = 'autogen.mean_60s' # 'data_raw', 'autogen.mean_60s', 'autogen.mean_1h', 'autogen.mean_1d'
    period      = '1d' # '1d' '30d' '52w'
    # read database
    data        = read_db(db_name, measurement, period)
    # return data and layout
    return {
        'data'   : [get_data(data,'temperature', 'rgb(224,72,66)')],
        'layout' : get_layout(data, 'temperature', 'temperature &deg;C')
    }



if __name__ == '__main__':
    app.run_server(debug=False, host='192.168.2.103', port=8050)