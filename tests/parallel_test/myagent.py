from abce.agent import Agent
from random import shuffle
from numba import jit

class MyAgent(Agent):
    def init(self, simulation_parameters, agent_parameters):
        print("init", self.id)

    @jit(nogil=True)
    def compute(self):
        # print('here', self.idn)
        ll = list(range(1000))
        shuffle(ll)
        max(ll)
