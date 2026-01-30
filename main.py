import random
from city import City
from person import Person
from simulation import Simulation

def generate_people(city):
    people=[]
    for home in city.home_nodes:
        if random.random()<0.2:
            p=Person(home,None,city)
        else:
            work=random.choice(city.work_nodes)
            p=Person(home,work,city)
        people.append(p)
    return people

if __name__=='__main__':
    city=City();people=generate_people(city)
    print(f"Homes:{len(city.home_nodes)} Work:{len(city.work_nodes)} People:{len(people)}")
    sim=Simulation(city,people);sim.run()
