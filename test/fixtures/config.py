sink = {
    'RedisSink': {
        'host': '127.0.0.1',
        'port': 6379,
        'pipeline_size': 100,
        'db': 0
    }
}

spout = {
    'CarbonTcpSpout': {
        'host': '127.0.0.1',
        'port': 2004,
        'model': 'pickle'
    }
}

analyzer = {
    'metric_sink': {
        'RedisSink': {
            'host': '127.0.0.1',
            'port': 6379,
            'pipeline_size': 100,
            'db': 0
        }
    },
    'output_sink': {
        'GraphiteSink': {
            'host': '127.0.0.1',
            'port': 2003,
            'url': 'graphite.foo.com',
            'prefix': 'AnnaMolly'
        }
    },
    'celery': {
        'broker': {
            'host': 'someHost'
        },
        'backend': {
            'host': 'someHost'
        }
    },
}

services = {
    'TukeysFilter': {
        'scheduler_options': {
            'interval_secs': 60,
            'plugin_args': {
                'name': 'TukeysFilter'
            }
        },
        'service_options': {
            'service1': {
                'metric': 'cpu',
                'quantile_25': 'service.quartil_25',
                "model": [
                    {
                        "RedisTimeStamped": {
                            "ttl": 10000
                        }
                    }
                ]
            }
        }
    },
    'SeasonalDecomposition': {
        'scheduler_options': {
            'interval_secs': 300,
            'plugin_args': {
                'name': 'SeasonalDecomposition'
            }
        },
        'service_options': {
            'stl_service1': {
                'metric': 'cpu',
                'period_length': 3,
                'seasons': 2,
                'interval': 1,
                'error_params': {},
                "model": [
                    {
                        "RedisIntervalTimeStamped": {
                            "ttl": 10000,
                            "interval": 300
                        }
                    }
                ]
            }
        }
    },
    'SeasonalDecompositionEnsemble': {
        'scheduler_options': {
            'interval_secs': 180,
            'plugin_args': {
                'name': 'SeasonalDecompositionEnsemble'
            }
        },
        'service_options': {
            'stle_service1': {
                'metric': 'cpu',
                'period_length': 3,
                'seasons': 2,
                'interval': 1,
                'error_params': {},
                "model": [
                    {
                        "RedisIntervalTimeStamped": {
                            "ttl": 10000,
                            "interval": 300
                        }
                    }
                ]
            }
        }
    },
    'FlowDifference': {
        'scheduler_options': {
            'interval_secs': 600,
            'plugin_args': {
                'name': 'FlowDifference'
            }
        },
        'service_options': {
            'flow_service1': {
                'in_metric': 'service1.out',
                'out_metric': 'service2.in',
                'stale': 10,
                'error_params': {},
                "model": [
                    {
                        "RedisIntervalTimeStamped": {
                            "ttl": 10000,
                            "interval": 300
                        }
                    }
                ]
            }
        }
    }
}

collector = {
    'router': {
        'blacklist': ['.*_crit.*']
    }
}
