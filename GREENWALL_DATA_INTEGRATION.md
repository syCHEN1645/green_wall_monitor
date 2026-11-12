# GreenWall Data Integration Guide

## Overview

GreenWall sensor data is stored in InfluxDB 2.x and queried using Flux.

Official documentation:

- [Query data with Flux](https://docs.influxdata.com/influxdb/v2/query-data/flux/)
- [Query data from InfluxDB](https://docs.influxdata.com/influxdb/v2/query-data/get-started/query-influxdb/)
- [InfluxDB Python client library](https://docs.influxdata.com/influxdb/cloud/api-guide/client-libraries/python/)
- [InfluxDB HTTP query API](https://docs.influxdata.com/influxdb/v2/api/v2/)

## Database connection

| Setting | Value |
|---|---|
| Database | InfluxDB 2.x |
| Query endpoint | `http://<database-host>:8086/api/v2/query` |
| Organization | `greenwall` |
| Bucket | `test-data` |
| Query language | Flux |
| Authentication | InfluxDB API token |

Use a read-only API token for database access.

Install the official Python client:

~~~bash
pip install influxdb-client
~~~

Create a connection:

~~~python
from influxdb_client import InfluxDBClient

url = "http://<database-host>:8086"
token = "<read-only-api-token>"
org = "greenwall"

client = InfluxDBClient(
    url=url,
    token=token,
    org=org,
)
~~~

## Data series

Available sensor series:

~~~text
1-air-temp-out/air-temp
1-air-temp-in/air-temp
1-water-temp/wall-temp
1-wall-temp/wall-temp
1-soil-moisture/soil-moisture

2-air-temp-out/air-temp
2-air-temp-in/air-temp
2-water-temp/wall-temp
2-wall-temp/wall-temp
2-soil-moisture/soil-moisture
~~~

Use the series identifier as the value of the `sensor` column when filtering data.

## InfluxDB record schema

| Column | Meaning |
|---|---|
| `_time` | Reading timestamp in UTC |
| `_value` | Numeric sensor value |
| `_field` | InfluxDB field name, normally `value` |
| `_measurement` | InfluxDB measurement name, normally `Box-1` |
| `sensor` | Sensor series identifier |

## Flux queries

Flux requires a bounded time range. Use `range()` with explicit start and stop times.

~~~flux
from(bucket: "test-data")
  |> range(
      start: 2026-11-01T00:00:00Z,
      stop: 2026-11-02T00:00:00Z
  )
  |> filter(fn: (r) =>
      r.sensor == "2-air-temp-out/air-temp"
  )
  |> aggregateWindow(every: 1m, fn: last, createEmpty: false)
  |> keep(columns: ["_time", "_value", "_field", "_measurement", "sensor"])
~~~

Official Flux references:

- [Flux query basics](https://docs.influxdata.com/influxdb/v2/query-data/get-started/query-influxdb/)
- [range()](https://docs.influxdata.com/influxdb/v2/reference/flux/stdlib/built-in/transformations/range/)
- [filter()](https://docs.influxdata.com/influxdb/v2/reference/flux/stdlib/built-in/transformations/filter/)
- [aggregateWindow()](https://docs.influxdata.com/influxdb/v2/reference/flux/stdlib/built-in/transformations/aggregates/aggregatewindow/)
- [keep()](https://docs.influxdata.com/flux/v0/stdlib/universe/keep/)

## Python query example

~~~python
from influxdb_client import InfluxDBClient

url = "http://<database-host>:8086"
token = "<read-only-api-token>"
org = "greenwall"
bucket = "test-data"

query = f'''
from(bucket: "{bucket}")
  |> range(start: 2026-11-01T00:00:00Z, stop: 2026-11-02T00:00:00Z)
  |> filter(fn: (r) => r.sensor == "2-air-temp-out/air-temp")
  |> aggregateWindow(every: 1m, fn: last, createEmpty: false)
  |> keep(columns: ["_time", "_value", "_field", "_measurement", "sensor"])
'''

with InfluxDBClient(url=url, token=token, org=org) as client:
    tables = client.query_api().query(org=org, query=query)
    for table in tables:
        for record in table.records:
            print({
                "time": record.get_time().isoformat(),
                "value": record.get_value(),
                "field": record.get_field(),
                "measurement": record.get_measurement(),
                "sensor": record.values.get("sensor"),
            })
~~~

Example result:

~~~python
{
    "time": "2026-11-01T00:01:00+00:00",
    "value": 23.45,
    "field": "value",
    "measurement": "Box-1",
    "sensor": "2-air-temp-out/air-temp",
}
~~~

InfluxDB timestamps are UTC. Use ISO 8601 UTC timestamps such as `2026-11-01T00:00:00Z`.

