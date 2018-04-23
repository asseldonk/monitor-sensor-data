import time
from influxdb import InfluxDBClient
import os.path



def check_if_db_exists(client, db_name):
    db_list = client.query('show databases')
    for item in db_list.get_points():
        if item['name'] == db_name:
            return True
    return False


def create_database(client, db_name):
    client.create_database(db_name)


def create_downsampling(client, db_name):
    # create retention policies: delete raw data after one hour, collect other data forever
    client.query('create retention policy rp_1h on ' + db_name + ' duration 1h replication 1 default')
    # create continuous queries
    client.query('create continuous query cq_60s on ' + db_name + ' begin select mean(temperature) as temperature into autogen.mean_60s from data_raw group by time(60s) end')
    client.query('create continuous query cq_1h on ' + db_name + ' begin select mean(temperature) as temperature into autogen.mean_1h from autogen.mean_60s group by time(1h) end')
    client.query('create continuous query cq_1d on ' + db_name + ' begin select mean(temperature) as temperature into autogen.mean_1d from autogen.mean_1h group by time(1d) end')


def read_temperature():
    # open sensor file and read content
    path = '/sys/bus/w1/devices/28-000004e06f2c/w1_slave'
    # check if sensor exixts
    if os.path.isfile(path):
        file    = open(path)
        content = file.readlines()
        file.close()
        # get value
        stringvalue = content[1].split(" ")[9]
        # get temperature
        temperature = float(stringvalue[2:]) / 1000
    else:
        temperature = 'inf'
    return temperature


# main
def main():
    db_name     = 'sensor_data'
    measurement = 'data_raw'
    # connect to database
    client = InfluxDBClient(host='localhost', port=8086)
    # if database does not exist
    if not check_if_db_exists(client, db_name):
        create_database(client, db_name)
        create_downsampling(client, db_name)
    # use database, note: client.query('use database') does not work...
    client.switch_database(db_name)
    # start measurement
    starttime   = time.time()
    while True:
        temperature = read_temperature()
        # if sensor exixts
        if temperature != 'inf':
            # create measurement json
            json_insert = [
                {
                    'measurement' : measurement,
                    'fields'      : {
                        'temperature' : temperature,
                    },
                }
            ]
            # write temperature to db
            client.write_points(json_insert)
            # take measurement every five seconds
            time.sleep(5.0 - ((time.time() - starttime) % 5.0))



if __name__ == '__main__':
    main()