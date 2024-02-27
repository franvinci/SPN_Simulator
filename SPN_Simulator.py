import random
from tqdm import tqdm
import pandas as pd
import pm4py
from pm4py.algo.conformance.alignments.petri_net import algorithm as alignments
from pm4py.objects.petri_net.obj import PetriNet
import os


class StochasticPetriNetSimulator:

    def __init__(self, net, initial_marking, final_marking, transition_weights='frequency', log=[]):

        self.net = net
        self.initial_marking = initial_marking
        self.final_marking = final_marking
        self.add_start_end_transitions()
        
        if transition_weights == 'equal':
            self.transition_weights = {t: 1 for t in list(self.net.transitions)}
            print('\n', self.transition_weights, '\n')
        if transition_weights == 'frequency':
            if log == []:
                print('Error: Empty event-log.')
            else:
                self.log = log
                self.transition_weights = self.return_transitions_frequency()
                # print('\n', self.transition_weights, '\n')
        if transition_weights == 'manually':
            self.transition_weights = dict()
            print('Insert weight for each transition...')
            for t in list(self.net.transitions):
                t_w = float(input(str(t) + ": "))
                self.transition_weights[t] = t_w
            print('\n', self.transition_weights, '\n')


    def add_start_end_transitions(self):
        
        N = len(self.net.transitions) + len(self.net.places) + 1
        t_start = PetriNet.Transition(name = 'n'+str(N), label='<START>')
        self.net.transitions.add(t_start)

        N = len(self.net.transitions) + len(self.net.places) + 1
        t_end = PetriNet.Transition(name = 'n'+str(N), label='<END>')
        self.net.transitions.add(t_end)

        N = len(self.net.transitions) + len(self.net.places) + 1
        new_place_start = PetriNet.Place(name = 'n'+str(N))
        self.net.places.add(new_place_start)

        N = len(self.net.transitions) + len(self.net.places) + 1
        new_place_end = PetriNet.Place(name = 'n'+str(N))
        self.net.places.add(new_place_end)

        places_from = list(self.initial_marking)
        places_to = list(self.final_marking)

        t_after_start = []
        for p in places_from:
            for arc in p.out_arcs:
                t_after_start.append(arc.target)
                self.net.arcs.remove(arc)
            p.out_arcs.clear()

        t_before_end = []
        for p in places_to:
            for arc in p.in_arcs:
                t_before_end.append(arc.source)
                self.net.arcs.remove(arc)
            p.in_arcs.clear()

        new_arcs = []

        for p in places_from:
            new_arcs.append(PetriNet.Arc(p, t_start))
            
        for p in places_to:
            new_arcs.append(PetriNet.Arc(t_end, p))

        new_arcs.append(PetriNet.Arc(t_start, new_place_start))
        new_arcs.append(PetriNet.Arc(new_place_end, t_end))

        for t in t_after_start:
            new_arcs.append(PetriNet.Arc(new_place_start, t))

        for t in t_before_end:
            new_arcs.append(PetriNet.Arc(t, new_place_end))

        for arc in new_arcs:
            self.net.arcs.add(arc)

        pm4py.write_pnml(self.net, self.initial_marking, self.final_marking, 'net_startEnd.pnml')
        self.net, self.initial_marking, self.final_marking = pm4py.read_pnml('net_startEnd.pnml')
        os.remove('net_startEnd.pnml')


    def return_transitions_frequency(self):
        alignments_ = alignments.apply_log(self.log, self.net, self.initial_marking, self.final_marking, parameters={"ret_tuple_as_trans_desc": True})
        aligned_traces = [[y[0] for y in x['alignment'] if y[0][1]!='>>'] for x in alignments_]

        frequency_t = {t: 0 for t in self.net.transitions}

        for trace in aligned_traces:
            for align in trace:
                name_t = align[1]
                for t in list(self.net.transitions):
                    if t.name == name_t:
                        frequency_t[t] += 1
                        break

        return frequency_t


    def return_enabled_transitions(self, tkns):
        enabled_t = set()
        for t in list(self.net.transitions):
            if {a.source for a in t.in_arcs}.issubset(tkns):
                enabled_t.add(t)
        return enabled_t


    def return_fired_transition(self, enabled_transitions):

        total_weight = sum(self.transition_weights[s] for s in enabled_transitions)
        random_value = random.uniform(0, total_weight)
        
        cumulative_weight = 0
        for s in enabled_transitions:
            cumulative_weight += self.transition_weights[s]
            if random_value <= cumulative_weight:
                return s


    def update_markings(self, tkns, t_fired):

        for a_in in list(t_fired.in_arcs):
            tkns.remove(a_in.source)

        for a_out in list(t_fired.out_arcs):
            tkns.extend([a_out.target])
            
        return tkns


    def simulate_one_istance(self):
        trace_sim = []
        tkns = list(self.initial_marking)
        enabled_transitions = self.return_enabled_transitions(tkns)
        t_fired = self.return_fired_transition(enabled_transitions)
        if t_fired.label and (t_fired.label not in ['<START>', '<END>']):
            trace_sim.append(t_fired.label)
        tkns = self.update_markings(tkns, t_fired)
        while set(tkns) != set(self.final_marking):
            enabled_transitions = self.return_enabled_transitions(tkns)
            t_fired = self.return_fired_transition(enabled_transitions)
            if t_fired.label and (t_fired.label not in ['<START>', '<END>']):
                trace_sim.append(t_fired.label)
            tkns = self.update_markings(tkns, t_fired)
        return trace_sim
    

    def simulate(self, n_istances):
        simulated_traces = []
        for i in tqdm(range(n_istances)):
            trace = self.simulate_one_istance()
            simulated_traces.extend([(str(i + 1), e) for e in trace])

        log_data = pd.DataFrame(simulated_traces, columns=['case:concept:name', 'concept:name'])
        log_data['time:timestamp'] = range(len(log_data))
        log_data['time:timestamp'] = pd.to_datetime(log_data['time:timestamp'])
        log_sim = pm4py.convert_to_event_log(log_data)

        return log_sim 