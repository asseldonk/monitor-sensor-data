# Monitor Sensor Data with influxDB and Dash

This repository provides two python files for read, store and visualize sensor data.

* influx\_insert.py reads out sensor data - here exemplary shown for the temperature sensor ds18b20 connected to a raspberry pi - and stores data into influxDB. For downsampling, mean values are stored every minute, hour and day via continuous queries (cq\_1m, cq\_1h, cq\_1d). Further more, raw data is deleted after one hour (retention policy rp\_1h).

* app.py visualises data from influxDB with Dash by plotly.

## License

See the [LICENSE](LICENSE.md) file for license rights and limitations (MIT).