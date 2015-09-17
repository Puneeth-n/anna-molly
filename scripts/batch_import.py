#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:et:sw=4 ts=4

# python imports
import argparse
import json
import logging
import os, sys
import urllib2

from collections import namedtuple

ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(ROOT)

log = logging.getLogger(os.path.basename(__file__))

from lib.modules import config as config_loader
from lib.modules.sink import RedisSink
from lib.modules.models import TimeSeriesTuple, RedisTimeStamped

# argparse
def parse_options():
    '''
    Parse user arguments
    '''
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description='Populate redis db from graphite.')
    parser.add_argument('-a', '--analyzer', default='config/analyzer.json', type=str, help='filepath and name to analyzer config')
    parser.add_argument('-s', '--services', default='config/services.json', type=str, help='filepath and name to services config')
    parser.add_argument('--ttl', default=1250000, type=str, help='TTL')
    parser.add_argument('--log_level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help="Set the logging level", default='INFO')

    return parser.parse_args()

# logging
def set_log_level(args):
    '''
    Set loglevel
    '''
    logging.basicConfig(level=args.log_level)

def read_metrics(config, metrics, args):
    '''
    Read metric from metric sink
    '''
    data = namedtuple('data', 'name values')
    for metric in metrics:
        graphite_config = config['output_sink']['GraphiteSink']
        host = graphite_config['host']
        port = graphite_config['port']
        url = 'http://{0}/render/?width=586&height=308&_salt=1422452261.817&target={1}&from=-{2}hours&format=json'.format(host, metric.name, metric.seasons*24)
        log.debug('Graphite host: %s port: %d, url: %s', host, port, url)
        try:
            yield data(metric.name, json.loads(urllib2.urlopen(url).read())[0]['datapoints'])
        except Exception as _e:
            log.error('Could not process metric: %s Exception: %s', metric[0], _e)
            exit(1)

def transform_metrics(data, args):
    '''
    Transform previous data read from metric sink
    '''
    for d in data:
        for datapoint in d.values:
            value = datapoint[0]
            if 'count.sum' in d.name:
                try:
                    value = datapoint[0] / 30.0
                except:
                    value = datapoint[0]
            tst = TimeSeriesTuple(d.name, datapoint[1], value)
            rts = RedisTimeStamped({'ttl': args.ttl}, tst)
            yield rts

def write_metrics(config, tuples):
    '''
    write data to redis sink
    '''
    redis_config = config['metric_sink']['RedisSink']
    log.debug('Redis host: %s port: %d db: %d', redis_config['host'], redis_config['port'], redis_config['db'])
    sink = RedisSink(redis_config)
    log.info('Writing to redis sink')

    try:
        sink.write(tuples)
        sink.redis_pipeline.execute()
        log.info('Data written successfully')
    except Exception as _e:
        log.error('Could not write to database. Exception: %s', _e)

def load_metrics(plugins, args):
    '''
    This function returns a namedtuple of metric's and its seasons
    '''
    metrics = namedtuple('metrics', 'name seasons')
    for plugin in plugins:
        if plugin not in ['SeasonalDecompositionEnsemble', 'SeasonalDecomposition']:
            continue
        for metric in plugins[plugin]['worker_options']:
            log.info('Processing metric: %s for plugin: %s', metric, plugin)
            seasons = plugins[plugin]['worker_options'][metric]['seasons']
            name = plugins[plugin]['worker_options'][metric]['metric'].split('*', 1)[0]
            yield metrics(name, seasons)

def main():
    '''
    main
    '''
    args = parse_options()
    set_log_level(args)

    try:
        plugins = config_loader.load(args.services)
        config = config_loader.load(args.analyzer)
    except IOError as _e:
        log.error('Could not open file: %s', _e.filename)
        exit(1)

    metrics = load_metrics(plugins, args)
    data = read_metrics(config, metrics, args)
    tuples = transform_metrics(data, args)
    write_metrics(config, tuples)

if __name__ == "__main__":
    main()
