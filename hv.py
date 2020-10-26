# coding: utf-8
"""
Hypervolume indicator.
"""
import json
import os
import sys

from pygmo import hypervolume


def main():
    with open(sys.argv[1]) as f, open(sys.argv[2]) as g:
        solution_to_score = json.load(f)
        solutions_scored = json.load(g)

    ys = [s['objective'] for s in solutions_scored]
    ys.append(solution_to_score['objective'])
    hv = hypervolume(ys)
    ref_point = json.loads(os.getenv('HV_REF_POINT', 'null'))
    score = hv.compute(ref_point)
    print(json.dumps({'score': score}))


if __name__ == '__main__':
    main()
