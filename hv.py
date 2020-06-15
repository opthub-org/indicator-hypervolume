# coding: utf-8
"""
Hypervolume indicator.
"""
import json
import os
import sys

from pygmo import hypervolume


def main():
    solution_to_score = json.loads(sys.argv[1])
    solutions_scored = json.loads(sys.argv[2])

    ys = [s['objective'] for s in solutions_scored]
    ys.append(solution_to_score['objective'])
    hv = hypervolume(ys)
    ref_point = json.loads(os.getenv('HV_REF_POINT', 'null'))
    score = hv.compute(ref_point)
    print(json.dumps({'score': score}))


if __name__ == '__main__':
    main()
