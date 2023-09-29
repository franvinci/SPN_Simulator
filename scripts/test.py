import sys
sys.path.append('./')

import pm4py
from SPN_Simulator import StochasticPetriNetSimulator

import argparse
parser = argparse.ArgumentParser()

parser.add_argument('--pnml_path', type=str, default='example_data/purchasing.pnml')
parser.add_argument('--n_traces', type=int, default=10000)
parser.add_argument('--input_log', type=str, default='example_data/PurchasingExample.xes.gz')
parser.add_argument('--transition_weights', type=str, default='frequency')
parser.add_argument('--output_path', type=str, default='example_outputs/purchasing_sim.xes')


args = parser.parse_args()
pnml_path = args.pnml_path
n_traces = args.n_traces
input_log = args.input_log
transition_weights = args.transition_weights
output_path = args.output_path

net, initial_marking, final_marking = pm4py.read_pnml(pnml_path)
pm4py.view_petri_net(net, initial_marking, final_marking)

simulator = StochasticPetriNetSimulator(net, initial_marking, final_marking, transition_weights, log_path=input_log)

log = simulator.simulate(n_traces)
pm4py.write_xes(log, output_path)