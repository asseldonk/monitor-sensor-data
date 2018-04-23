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
    # plotly tries to use utc time first, so remove timezone information:
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
db_name     = 'sensor_data'
measurement = 'autogen.mean_60s'
period      = '1d'
data        = read_db(db_name, measurement, period)
# dash
app  = dash.Dash()
app.layout = html.Div(
    [
        html.Link(
            rel  = 'stylesheet',
            href = '/static/css/main.css'
        ),
        html.H1('Sensor Data'),
        html.Div([
            html.Div([
                # dropdown for selecting measurement
                html.Label('Select measurement:'),
                dcc.Dropdown(
                    id        = 'dropdown-measurement',
                    options   = [
                        {'label': 'raw data',               'value': 'data_raw'},
                        {'label': 'averaged over 1 minute', 'value': 'autogen.mean_60s'},
                        {'label': 'averaged over 1 hour',   'value': 'autogen.mean_1h'},
                        {'label': 'averaged over 1 day',    'value': 'autogen.mean_1d'}
                    ],
                    value     = 'autogen.mean_60s',
                    clearable = False
                ),
            ]),
            html.Div([
                # dropdown for selecting period
                html.Label('Select Period:'),
                dcc.Dropdown(
                    id        = 'dropdown-period',
                    options   = [
                        {'label': '1 min',   'value': '1m'},
                        {'label': '10 min',  'value': '10m'},
                        {'label': '1 hour',  'value': '1h'},
                        {'label': '1 day',   'value': '1d'},
                        {'label': '1 week',  'value': '1w'},
                        {'label': '1 month', 'value': '4w'}
                    ],
                    value     = '1d',
                    clearable = False
                )
            ]),
            html.Div([
                # dropdown for selecting update interval
                # since infinity or no interval is not posible,
                # use maximum permitted time: 2147483647 (about 24.86 days)
                html.Label('Select update interval:'),
                dcc.Dropdown(
                    id        = 'dropdown-interval',
                    options   = [
                        {'label': 'every 5 seconds',  'value': 5*1000},
                        {'label': 'every 10 seconds', 'value': 10*1000},
                        {'label': 'every minute',     'value': 60*1000},
                        {'label': 'every hour',       'value': 60*60*1000},
                        {'label': 'every day',        'value': 24*60*60*1000},
                        {'label': 'never',            'value': 2147483647}
                    ],
                    value     = 60*1000,
                    clearable = False
                )
            ])
        ],
        className = 'dropdowns'
        ),
        # temperatur graph
        dcc.Graph(id      = 'graph-temperature',
                  figure  = {
                        'data'   : [get_data(data, 'temperature', 'rgb(224,72,66)')],
                        'layout' : get_layout(data, 'temperature', 'temperature &deg;C')
                  }
        ),
        dcc.Interval(id          = 'interval-component',
                     n_intervals = 0
        ),
    ]
)


# css file
@app.server.route('/static/<path:path>')
def static_file(path):
    static_folder = os.path.join(os.getcwd(), 'static')
    return send_from_directory(static_folder, path)

# update interval
@app.callback(Output('interval-component', 'interval'),
              [Input('dropdown-interval', 'value')
              ])
def update_interval(value):
    return value


# update temperature graph
@app.callback(Output('graph-temperature', 'figure'),
              [Input('interval-component', 'n_intervals'),
               Input('dropdown-measurement', 'value'),
               Input('dropdown-period', 'value')
              ])
def update_graph(n, dropdown_measurement, dropdown_period):
    # read database
    measurement = dropdown_measurement
    period      = dropdown_period
    data        = read_db(db_name, measurement, period)
    # return data and layout
    return {
        'data'   : [get_data(data,'temperature', 'rgb(224,72,66)')],
        'layout' : get_layout(data, 'temperature', 'temperature &deg;C')
    }



if __name__ == '__main__':
    app.run_server(debug=False, host='192.168.2.103', port=8050)