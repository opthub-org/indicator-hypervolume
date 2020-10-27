# coding: utf-8
"""
Hypervolume indicator.
"""
import json
import logging
import os
import sys

from pygmo import hypervolume


_logger = logging.getLogger(__name__)


def main():
    try:
        verbosity = 0
        if len(sys.argv) > 1:
            for c in sys.argv[1]:
                verbosity += -10 if c == 'v' else 10 if c == 'q' else 0
        log_level = logging.WARNING + verbosity
        logging.basicConfig(level=log_level)
        _logger.info('Log level is set to %d.', log_level)

        env = os.getenv('HV_REF_POINT', 'null')
        _logger.debug('env_ref = %s', env)

        ref_point = json.loads(env)
        _logger.debug('ref = %s', ref_point)

        x = input()
        _logger.debug('input_x = %s', x)

        xs = input()
        _logger.debug('input_xs = %s', xs)

        solution_to_score = json.loads(x)
        _logger.debug('x = %s', solution_to_score)

        solutions_scored = json.loads(xs)
        _logger.debug('xs = %s', solutions_scored)

        ys = [s['objective'] for s in solutions_scored]
        ys.append(solution_to_score['objective'])
        hv = hypervolume(ys)

        score = hv.compute(ref_point)
        _logger.debug('score = %s', score)

    except Exception as e:
        _logger.error(e)
        score = float('inf')
    print(json.dumps({'score': score}))


if __name__ == '__main__':
    main()
