#!/bin/env python
# coding: utf-8
"""
Hypervolume indicator.
"""
import json
import logging
from os import path

import click
from jsonschema import validate, ValidationError
import numpy as np
from pygmo import hypervolume, nadir, pareto_dominance
import yaml


_logger = logging.getLogger(__name__)


ref_point_jsonschema = """{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Reference point for Hypervolume",
  "OneOf": [
    {"type": "null"},
    {"type": "array", "minItems": 1, "items": {"type": "number"}}
  ]
}"""
solution_to_score_jsonschema = """{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Solution to score",
  "type": "object",
  "properties": {
    "objective": {
      "type": "array",
      "minItems": 1,
      "items": {"type": "number"}
    },
    "constraint": {
      "OneOf": [
        {"type": "number"},
        {"type": "array", "minItems": 1, "items": {"type": "number"}}
      ]
    }
  },
  "required": ["objective"]
}"""
solutions_scored_jsonschema = """{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Solutions scored",
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "objective": {
        "type": "array",
        "minItems": 1,
        "items": {
          "type": "number"
        }
      },
      "constraint": {
        "OneOf": [
          {"type": "number"},
          {"type": "array", "minItems": 1, "items": {"type": "number"}}
        ]
      }
    },
    "required": ["objective"]
  }
}"""


def load_config(ctx, value):
    """Load `ctx.default_map` from a file.

    :param ctx: Click context
    :param value: File name
    :return dict: Loaded config
    """
    if not path.exists(value):
        return {}
    with open(value) as f:
        ctx.default_map = yaml.safe_load(f)
    return ctx.default_map


def json_list(ctx, param, value):
    """Load a list from a JSON string.

    :param ctx: Click context
    :param param: Parameter info
    :param value: JSON string
    :return list: Loaded list
    """
    if type(value) is str:
        value = json.loads(value)
    if type(value) not in [list, type(None)]:
        ctx.fail("Invalid option: %s=%s, which must be list, str, or None." % (param.name, value))
    return value


def feasible(s):
    return not s.get('constraint') or np.all(np.array(s['constraint']) <= 0)


@click.command(help='Hypervolume indicator.')
@click.option('-r', '--ref-point', callback=json_list, default=None, help='Reference points.')
@click.option('-q', '--quiet', count=True, help='Be quieter.')
@click.option('-v', '--verbose', count=True, help='Be more verbose.')
@click.option('-c', '--config',
              type=click.Path(dir_okay=False), default='config.yml',
              is_eager=True, callback=load_config, help='Configuration file.')
@click.version_option('1.0.0')
@click.pass_context
def main(ctx, ref_point, quiet, verbose, config):
    verbosity = 10 * (quiet - verbose)
    log_level = logging.WARNING + verbosity
    logging.basicConfig(level=log_level)
    _logger.info('Log level is set to %d.', log_level)

    _logger.info('Validate ref_point...')
    validate(ref_point, json.loads(ref_point_jsonschema))
    _logger.debug('ref_point = %s', ref_point)
    _logger.info('...Validated')

    _logger.info('Recieve a solution to score...')
    x = input()
    _logger.debug('input_x = %s', x)
    _logger.info('...Recieved')

    _logger.info('Recieve solutions scored...')
    xs = input()
    _logger.debug('input_xs = %s', xs)
    _logger.info('...Recieved')

    _logger.info('Parse a solution to score...')
    solution_to_score = json.loads(x)
    _logger.debug('x = %s', solution_to_score)
    _logger.info('...Parsed')

    _logger.info('Validate a solution to score...')
    validate(solution_to_score, json.loads(solution_to_score_jsonschema))
    _logger.info('...Validated')

    _logger.info('Parse solutions scored...')
    solutions_scored = json.loads(xs)
    _logger.debug('xs = %s', solutions_scored)
    _logger.info('...Parsed')

    _logger.info('Validate solutions scored...')
    validate(solutions_scored, json.loads(solutions_scored_jsonschema))
    _logger.info('...Validated')

    _logger.info('Filter feasible solutions...')
    ys = [s['objective'] for s in solutions_scored if feasible(s)]
    if feasible(solution_to_score):
        ys.append(solution_to_score['objective'])
    else:
        _logger.warning('Current solution is not feasible.')
    _logger.debug('ys = %s', ys)
    _logger.info('%d / %d solutions are feasible.', len(ys), len(solutions_scored) + 1)
    _logger.info('...Filtered')

    if not ys:  # no feasible point
        _logger.warning('No feasible point. HV is zero.')
        print(json.dumps({'score': 0}))
        ctx.exit(0)

    if not ref_point:
        _logger.warning('HV_REF_POINT is not specified. Try to use the nadir point.')
        if len(ys) == 1:  # HV=0 since nadir() requires at least two feasible points
            _logger.warning('The nadir point requires at least two feasible points. HV is zero.')
            print(json.dumps({'score': 0}))
            ctx.exit(0)
        ref_point = nadir(ys)
        _logger.warning('The nadir point is set to %s.' % ref_point)
    _logger.debug('ref_point = %s', ref_point)

    _logger.info('Validate the reference point...')
    validate(ref_point, json.loads(ref_point_jsonschema))
    _logger.info('...Validated')

    _logger.info('Reference point is %s', ref_point)

    _logger.info('Filter solutions dominating the reference point...')
    ys = [y for y in ys if pareto_dominance(y, ref_point)]
    _logger.info('...Filtered')

    if ys:
          _logger.warning('No feasible point dominating the reference point. HV is zero.')
          print(json.dumps({'score': 0}))
          ctx.exit(0)

    _logger.info('Initialize a HV calculator...')
    hv = hypervolume(ys)
    _logger.info('...Initialized')

    _logger.info('Compute HV...')
    score = hv.compute(ref_point)
    _logger.debug('score = %s', score)
    _logger.info('...Computed')

    print(json.dumps({'score': score}))


if __name__ == '__main__':
    try:
        _logger.info('Start')
        main(auto_envvar_prefix="HV")  # pylint: disable=no-value-for-parameter,unexpected-keyword-arg
        _logger.info('Successfully finished')
    except Exception as e:
        _logger.error(e)
        print(json.dumps({'score': None, 'error': str(e)}))
