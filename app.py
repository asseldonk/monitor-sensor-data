import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input
from flask import send_from_directory
import os
from influxdb import InfluxDBClient
from datetime import datetime
from pytz import timezone



# read database
def read_db(db_name, measurement, period):
    client = InfluxDBClient(host     = 'localhost',
                            port     = 8086,
                            database = db_name)
    result = client.query('select * from ' + measurement + ' where time > now()-' + period)
    return result


# create layout object
def get_layout(time, item, title, yaxis_title):
    min_x  = time[0] if (time and len(time)>0) else -1
    max_x  = time[-1] if (time and len(time)>0) else 1
    min_y  = float(min(item))-4. if (item and len(item)>0) else -1
    max_y  = float(max(item))+4. if (item and len(item)>0) else 1
    return {
            'font'          : {'color' : 'rgb(240,240,240)'},
            'title'         : title,
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
def get_data(time, item, color):
  return {
          'x'      : time,
          'y'      : item,
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


# convert utc to local
def utc_to_local(time):
  fmt   = '%Y-%m-%dT%H:%M:%S'
  local = []
  for item in time:
    # shorten time (accuracy: seconds), otherwise fmt = '%Y-%m-%dT%H:%M:%S.%f'
    item     = item[:19]
    dt       = datetime.strptime(item, fmt)
    dt_utc   = dt.replace(tzinfo=timezone('UTC'))
    dt_local = dt_utc.astimezone(timezone('Europe/Berlin'))
    dt_local = str(dt_local)[:-6]
    local.append(str(dt_local))
  return local



# dash
app = dash.Dash()
app.layout = html.Div(
    [
        html.Link(
            rel  = 'stylesheet',
            href = '/static/css/main.css'
        ),
        html.H1('Sensor Data'),
        # temperatur
        dcc.Graph(id      = 'graph-temperature',
                  figure  = {
                        'data'   : [get_data(None, None, 'rgb(224,72,66)')],
                        'layout' : get_layout([], [], 'Temperature', 'temperature &deg;C')
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
    period      = '12h' # '1d' '30d' '52w'
    # read database
    db_data     = read_db(db_name, measurement, period)
    temp        = map(lambda x: x['temperature'], db_data.get_points())
    time        = map(lambda x: x['time'], db_data.get_points())
    # convert to local
    time        = utc_to_local(time)
    # return data and layout
    return {
        'data'   : [get_data(time, temp, 'rgb(224,72,66)')],
        'layout' : get_layout(time, temp, 'Temperature', 'temperature &deg;C')
    }



if __name__ == '__main__':
    app.run_server(debug=False, host='192.168.2.103', port=8050)