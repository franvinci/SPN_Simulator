# SPN_Simulator
Stochastic Petri Net Simulator

### How to use:

<pre>
```python
import pm4py
from SPN_Simulator import StochasticPetriNetSimulator

net, initial_marking, final_marking = pm4py.read_pnml('example_data/purchasing.pnml')
log = pm4py.read_xes('example_data/PurchasingExample.xes.gz')
log = pm4py.filter_event_attribute_values(log, 'lifecycle:transition', ['complete'], level="event", retain=True)   

simulator = StochasticPetriNetSimulator(net, initial_marking, final_marking, log=log)

n_traces = 10000
log = simulator.simulate(n_traces)

pm4py.write_xes(log, 'example_outputs/purchasing_sim.xes')
```
</pre>