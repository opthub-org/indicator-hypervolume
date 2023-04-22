#!/bin/env python
"""
Hypervolume indicator.
"""
import json
import logging
from os import path
from traceback import format_exc

import click
import numpy as np
import yaml
from jsonschema import validate
from pygmo import (  # pylint: disable=no-name-in-module
    hypervolume,
    nadir,
    pareto_dominance,
)


LOGGER = logging.getLogger(__name__)


REF_POINT_JSONSCHEMA = """{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Reference point for Hypervolume",
  "OneOf": [
    {"type": "null"},
    {"type": "array", "minItems": 1, "items": {"type": "number"}}
  ]
}"""

SOLUTION_TO_SCORE_JSONSCHEMA = """{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Solution to score",
  "type": "object",
  "properties": {
    "objective": {
      "OneOf": [
        {"type": "null"},
        {"type": "array", "minItems": 1, "items": {"type": "number"}}
      ]
    },
    "constraint": {
      "OneOf": [
        {"type": ["number", "null"]},
        {"type": "array", "minItems": 1, "items": {"type": "number"}}
      ]
    }
  }
}"""

SOLUTIONS_SCORED_JSONSCHEMA = """{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Solutions scored",
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "objective": {
        "OneOf": [
          {"type": "null"},
          {"type": "array", "minItems": 1, "items": {"type": "number"}}
        ]
      },
      "constraint": {
        "OneOf": [
          {"type": ["number", "null"]},
          {"type": "array", "minItems": 1, "items": {"type": "number"}}
        ]
      }
    }
  }
}"""


def load_config(ctx, _, value):
    """Load `ctx.default_map` from a file.

    :param ctx: Click context
    :param value: File name
    :return dict: Loaded config
    """
    if not path.exists(value):
        return {}
    with open(value, encoding="utf-8") as file:
        ctx.default_map = yaml.safe_load(file)
        if not isinstance(ctx.default_map, dict):
            raise TypeError(
                f"The content of `{value}` must be dict, but {type(ctx.default_map)}."
            )
    return ctx.default_map


def json_list(ctx, param, value):
    """Load a list from a JSON string.

    :param ctx: Click context
    :param param: Parameter info
    :param value: JSON string
    :return list: Loaded list
    """
    if isinstance(value, str):
        value = json.loads(value)
    if not isinstance(value, (list, type(None))):
        ctx.fail(
            "Invalid option: %s=%s, which must be list, str, or None."
            % (param.name, value)
        )
    return value


def feasible(solution):
    """Check if a given solution is feasible or not.
    :param solution: A solution
    :return: boolean
    """
    objective = solution.get("objective")
    constraint = solution.get("constraint")
    return (None not in np.array(objective)) and (
        constraint is None or np.all(np.array(constraint) <= 0.0)
    )


def is_pareto_efficient(costs):
    """
    Find the pareto-efficient points
    :param costs: An (n_points, n_costs) array
    :return: A (n_points, ) boolean array, indicating whether each point is Pareto efficient
    """
    is_efficient = np.ones(costs.shape[0], dtype=bool)
    for i, cost in enumerate(costs):
        if is_efficient[i]:
            is_efficient[is_efficient] = np.any(
                costs[is_efficient] < cost, axis=1
            )  # Keep any point with a lower cost
            is_efficient[i] = True  # And keep self
    return is_efficient


@click.command(help="Hypervolume indicator.")
@click.option(
    "-r", "--ref-point", callback=json_list, default=None, help="Reference points."
)
@click.option("-q", "--quiet", count=True, help="Be quieter.")
@click.option("-v", "--verbose", count=True, help="Be more verbose.")
@click.option(
    "-c",
    "--config",
    type=click.Path(dir_okay=False),
    default="config.yml",
    is_eager=True,
    callback=load_config,
    help="Configuration file.",
)
@click.version_option("1.0.0")
@click.pass_context
def main(ctx, ref_point, quiet, verbose, config):  # pylint: disable=unused-argument
    """Calculate hypervolume indicator."""
    verbosity = 10 * (quiet - verbose)
    log_level = logging.WARNING + verbosity
    logging.basicConfig(level=log_level)
    LOGGER.info("Log level is set to %d.", log_level)

    LOGGER.info("Recieve a solution to score...")
    json_solution_to_score = input()
    LOGGER.debug("json_solution_to_score = %s", json_solution_to_score)
    LOGGER.info("...Recieved")

    LOGGER.info("Recieve solutions scored...")
    json_solutions_scored = input()
    LOGGER.debug("json_solutions_scored = %s", json_solutions_scored)
    LOGGER.info("...Recieved")

    LOGGER.info("Parse a solution to score...")
    solution_to_score = json.loads(json_solution_to_score)
    LOGGER.debug("solution_to_score = %s", solution_to_score)
    LOGGER.info("...Parsed")

    LOGGER.info("Validate a solution to score...")
    validate(solution_to_score, json.loads(SOLUTION_TO_SCORE_JSONSCHEMA))
    LOGGER.info("...Validated")

    LOGGER.info("Parse solutions scored...")
    solutions_scored = json.loads(json_solutions_scored)
    LOGGER.debug("solutions_scored = %s", solutions_scored)
    LOGGER.info("...Parsed")

    LOGGER.info("Validate solutions scored...")
    validate(solutions_scored, json.loads(SOLUTIONS_SCORED_JSONSCHEMA))
    LOGGER.info("...Validated")

    LOGGER.info("Filter feasible solutions...")
    feasible_objectives = [s["objective"] for s in solutions_scored if feasible(s)]
    if feasible(solution_to_score):
        feasible_objectives.append(solution_to_score["objective"])
    else:
        LOGGER.warning("Current solution is not feasible.")
    LOGGER.debug("feasible_objectives = %s", feasible_objectives)
    LOGGER.info("...Filtered")

    LOGGER.info(
        "%d / %d solutions are feasible.",
        len(feasible_objectives),
        len(solutions_scored) + 1,
    )

    if not feasible_objectives:  # no feasible point
        LOGGER.warning("No feasible point. HV is zero.")
        print(json.dumps({"score": 0}))
        ctx.exit(0)

    if not ref_point:
        LOGGER.warning("HV_REF_POINT is not specified. Try to use the nadir point.")
        if (
            len(feasible_objectives) == 1
        ):  # HV=0 since nadir() requires at least two feasible points
            LOGGER.warning(
                "The nadir point requires at least two feasible points. HV is zero."
            )
            print(json.dumps({"score": 0}))
            ctx.exit(0)
        ref_point = nadir(feasible_objectives)
        LOGGER.warning("The nadir point is set to %s.", ref_point)
    LOGGER.debug("ref_point = %s", ref_point)

    LOGGER.info("Validate the reference point...")
    validate(ref_point, json.loads(REF_POINT_JSONSCHEMA))
    LOGGER.info("...Validated")

    LOGGER.info("Reference point is %s", ref_point)

    # PyGMO's HV algorithm (WFG-algorithm) has time complexity between
    # Omega(n^{d/2} log n) and O(n^{d-1}) for n points of d dimensions.
    # To accelerate HV computation, points with no HV contribution are excluded.

    # 1. Remove points that do not dominates the reference point in O(dn) time
    LOGGER.info("Filter points not dominating the reference point...")
    hv_objectives = np.array(
        [y for y in feasible_objectives if pareto_dominance(y, ref_point)]
    )
    LOGGER.debug("hv_objectives = %s", hv_objectives)
    LOGGER.info("...Filtered")

    # 2. Remove duplicate points in O(dn) time
    LOGGER.info("Uniquify points...")
    unique_hv_objectives = np.unique(hv_objectives, axis=0)
    LOGGER.debug("unique_hv_objectives = %s", unique_hv_objectives)
    LOGGER.info("...Uniquified")

    # 3. Remove dominated points in O(dn^2) time
    LOGGER.info("Compute nondominated front...")
    efficient_objectives = unique_hv_objectives[
        is_pareto_efficient(unique_hv_objectives)
    ]
    LOGGER.debug("efficient_objectives = %s", efficient_objectives)
    LOGGER.info("...Computed")

    if len(efficient_objectives) == 0:
        LOGGER.warning("No point dominates the reference point. HV is zero.")
        print(json.dumps({"score": 0}))
        ctx.exit(0)

    LOGGER.info("Initialize a HV calculator...")
    hvi = hypervolume(efficient_objectives)
    LOGGER.info("...Initialized")

    LOGGER.info("Compute HV...")
    score = hvi.compute(ref_point)
    LOGGER.debug("score = %s", score)
    LOGGER.info("...Computed")

    print(json.dumps({"score": score}))


if __name__ == "__main__":
    try:
        LOGGER.info("Start")
        main(  # pylint: disable=no-value-for-parameter,unexpected-keyword-arg
            auto_envvar_prefix="HV"
        )
        LOGGER.info("Successfully finished")
    except Exception as e:  # pylint: disable=broad-exception-caught
        LOGGER.error(format_exc())
        print(json.dumps({"score": None, "error": str(e)}))
