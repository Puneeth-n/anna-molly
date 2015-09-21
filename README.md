# What is Anna-Molly? ![](https://travis-ci.org/trademob/anna-molly.svg?branch=master)

[![Join the chat at https://gitter.im/trademob/anna-molly](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/trademob/anna-molly?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

Anna-Molly is a scalable system to collect metric data for dynamic monitoring.

* It can:
    - Receive metrics from Carbon and store the relevant metrics.
    - Analyze them with one of the available plugin algorithms.
    - Push the analysis to graphite.
    - Trigger Events based on the results of the algorithm.


Anna-Molly has two components:

1. **Collector**
    * The collector is responsible for receiving the Metrics from a Spout (Metric-Source) and pushing it to a Sink.
2. **Task Runner**
    * The Task-Runner is a celery encapsulated task, that invokes algorithm plugins that then work with
      the data from the Sink. The plugins can be algorithms, supporting tasks, event handlers or others.

> **A word of Caution:** This is a work in progress. There are a number of moving parts in Anna-Molly.
> which makes configuration and setup slightly tricky. You can follow the setup guide below. In case you
> run into issues in setting it up, write to us.


# What do I need?

Python (2.6, 2.7)

## Dependencies

```bash
sudo apt-get install -y build-essential python-pip r-base redis-server \
                        automake
sudo pip install -r /opt/anna-molly/requirements.txt
```


# Getting Started.

## First Steps

**Assumption:** You have a carbon relaying pickled metrics to a destination *(host:port)*.

### Bring up the Vagrant Box

* `vagrant up`

### Setup the Collector

* Configure a `collector.json` at `/opt/anna-molly/config`. You can use the
  `/opt/anna-molly/config/collector.json.example` as a template. Instructions on setting-up the collector config
  can be found in the sections below.
* Start the Collector `python /opt/anna-molly/bin/collector.py --config /opt/anna-molly/config/collector.json`

We should now have metrics being pushed to RedisSink. Verify this issuing `redis-cli -p 6379 monitor`

### Setup Task-Runner/Celery

* Configure a `analyzer.json` at `/opt/anna-molly/config`. You can use the
  `/opt/anna-molly/config/analyzer.json.example` as a template. Instructions on setting-up the analyzer config
  can be found in the sections below.
* Start Task-Runner/Celery `celery -A lib.app worker -l info` from `/opt/anna-molly`
* Start Scheduler `celery --beat --config=scheduler --workdir=./bin` from `/opt/anna-molly`


# Terminology

## Spout

Metric data source. It is exclusively used by the Collector Daemon to receive the data and push it to the Sink.

### Implementations

1. **CarbonAsyncTcpSpout** - Carbon Asynchronous TCP Pickle Spout

## Sink

A duplex interface to read and write data.
- Collector writes the data to the sink.
- Tasks read data from the sink.
- Tasks can also write to sink.

### Implementations

1. **RedisSink**
2. **GraphiteSink** (Write Only)

## Models

Class definitions that dictate how Time Series data is stored in the Sink or used by the tasks.

### Implementations

1. **TimeSeriesTuple** - For simplicity, data is stored and processed around as TimeSeriesTuple.
2. **RedisTimeStamped**
3. **RedisIntervalTimeStamped**
4. **RedisGeneric**

## Base Task

Base Task module is an abstract class that all plugins inherit from. It can setup the necessary
resources/connections for the plugin and exposes a `run` method which is implemented by the plugins.

## Collector Daemon

Collector Daemon receives data from a Spout and pushes it to a Sink. Metrics of interest can be
configured in `config/collector.json`. See configuration section below for details.

* Collector uses Spouts to listen/receive data.
* The data received if in whitelist is then instantiated to the configured model and pushed into the Sink.

## Task Runner

The task runner is an encapsulated Celery Task. Any Plugin in the `lib/plugins` folder can be invoked
by the task-runner as a task.

### Poll Tasks

Poll tasks are special tasks that are invoked by the scheduler to identify and trigger the actual Algorithm Task.

## Plugins

Plugins inherit from the BaseTask module and are responsible for setting up resources required for the Plugin to
run. It also implements the run method which is invoked by the task-runner.


# Configuration

There are three configuration files:

1. collector.json: Used by the `Collector`.
2. analyzer.json: Used by `Celery/BaseTask`.
3. services.json: Used by Plugins for algorithm specific configuration (see [wiki](https://github.com/trademob/anna-molly/wiki))

Note: The configuration needs to be simplified and will be worked on shortly.

## collector.json

```json
{
  "router": {
    "blacklist": [
      "MX",
      "osys.*"
    ],
    "whitelist": {
      ".*": [
        {
          "RedisTimeStamped": {
            "ttl": 10000
          }
        }
      ]
    }
  },
  "writer": {
    "RedisSink": {
      "host": "127.0.0.1",
      "port": 6379,
      "db": 3,
      "pipeline_size": 50
    }
  },
  "listener": {
    "CarbonAsyncTcpSpout": {
      "host": "0.0.0.0",
      "port": 2014
    }
  }
}
```

### Router

Config for routing/modeling the metrics.

  - Blacklist (Array) - Metrics matching one of the blacklist are rejected.
  - Whitelist (Object) - Metrics that match a whitelist are instantiated as the model specified in the config.
    Other metrics are ignored. Metrics that have N models configured, will have N objects stored in the Sink.

### Writer

Needs Sink

### Listener

Needs Spout

## analyzer.json

```json
{
  "celery": {
    "broker": {
      "host": "redis://127.0.0.1:6379/0"
    },
    "backend": {
      "host": "redis://127.0.0.1:6379/2"
    },
    "time_limit": "120"
  },
  "metric_sink": {
    "RedisSink": {
      "host": "127.0.0.1",
      "port": 6379
    }
  },
  "output_sink": {
    "GraphiteSink": {
      "host": "storage.metrics.foo.com",
      "port": 2003,
      "url": "graphite.foo.com"
    }
  }
}
```

### Celery

Basic Celery configuration. Can be used with a broker/backend of your choice. Refer Celery Docs for more information.

### MetricSink

Sink configuration. This is the input from which the plugins will fetch the Metric data for analysis. It must provide
configuration specific to the Sink implementation.

### OutputSink

Plugins push the result data into the OutputSink.

## services.json

```json
{
  "TukeysFilter": {
    "scheduler_options": {
      "interval_secs": 30,
      "plugin_args": {
        "name": "TukeysFilter"
      }
    },
    "service_options": {
      "service1": {}
    }
  }
}
```

### Algorithm Configuration

Each key in the `services.json` file defines an algorithm that will run (here `TukeysFilter`).

- **scheduler_options** - celery config
    - **interval_secs** - how often the tasks should run
    - **plugin_args** - arguments for the Poll Task
      - name - Mandatory plugin name.
- **service_options** - options for the each Task Runner

## Algorithms

* [Seasonal Trend Decomposition](https://github.com/trademob/anna-molly/wiki/Seasonal-Trend-Decomposition)
* [Tukeys Outlier Filter](https://github.com/trademob/anna-molly/wiki/Tukey's-Outlier-Filter)
* [Seasonal Trend Decomposition Ensemble](https://github.com/trademob/anna-molly/wiki/Seasonal-Trend-Decomposition-Ensemble)
* [Flow Difference](https://github.com/trademob/anna-molly/wiki/Flow-Difference)

