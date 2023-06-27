
from LifeSimulator import Simulator 

initial_character_count=20

env = Simulator(initial_character_count=initial_character_count)

for time in range(10000):
    for avatar_index in range(0, initial_character_count):
        action = env.get_random_action_set(parse=True)
        details = env.step(avatar_index, action)
    if time%500 == 0:
        print (f"action: {action}, details: {details}")
    env.render()

