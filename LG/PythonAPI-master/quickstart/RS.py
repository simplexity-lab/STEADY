# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/5/23 17:42
# @Author  : Chengjie
# @File    : RS.py
import socket
from problem import LGSVLProblem
from jmetal.algorithm.multiobjective import NSGAII,RandomSearch
from jmetal.operator import SBXCrossover, PolynomialMutation
from jmetal.util.solution import print_function_values_to_file, print_variables_to_file
from jmetal.util.termination_criterion import StoppingByEvaluations
import dill as pickle
import lgsvl
from environs import Env

if __name__ == '__main__':
    env = Env()

    sim = lgsvl.Simulator(
        env.str("LGSVL__SIMULATOR_HOST", lgsvl.wise.SimulatorSettings.simulator_host),
        env.int("LGSVL__SIMULATOR_PORT", lgsvl.wise.SimulatorSettings.simulator_port)
    )
    HOST = '192.168.50.51'
    PORT = 6007
    ADDR = (HOST, PORT)
    ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ss.connect(ADDR)
    # ----------------------------------------------------------
    problem = LGSVLProblem(env, sim, ss)

    # --------------------
    max_evaluations = 3000
    #
    algorithm = RandomSearch(
        problem=problem,
        termination_criterion=StoppingByEvaluations(max_evaluations=max_evaluations)
    )

    try:
        algorithm.rerun()
        # algorithm.run()
    except Exception as e:
        print("error:", e.args)
        algorithm.getProblem().sim = None
        algorithm.getProblem().env = None
        algorithm.getProblem().ego = None
        algorithm.getProblem().npc = None
        algorithm.getProblem().ss = None

    finally:
        print("finally")
        algorithm.getProblem().sim = None
        algorithm.getProblem().env = None
        algorithm.getProblem().ego = None
        algorithm.getProblem().npc = None
        algorithm.getProblem().ss = None


    from jmetal.util.solution import get_non_dominated_solutions, print_function_values_to_file, \
        print_variables_to_file
    from jmetal.lab.visualization import Plot

    front = get_non_dominated_solutions(algorithm.get_result())

    # Save results to file
    print_function_values_to_file(front, 'FUN.' + algorithm.label)
    print_variables_to_file(front, 'VAR.' + algorithm.label)

    print(f'Algorithm: ${algorithm.get_name()}')
    print(f'Problem: ${algorithm.getProblem().get_name()}')
    print(f'Computing time: ${algorithm.total_computing_time}')

