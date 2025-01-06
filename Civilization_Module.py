import random
import math
import numpy as np
import matplotlib.pyplot as plt

# Define global time as a global variable
global_time = 0

class Civilization:
    def __init__(self, seed, star_system):
        """
        Initializes the Civilization with a deterministic seed and a reference to the StarSystem.

        Parameters:
        - seed (int): Seed for deterministic random number generation.
        - star_system (StarSystem): Instance of the star system providing dynamic energy budgets and dangers.
        """
        self.seed = seed
        self.random_gen = random.Random(seed)  # Independent random generator for reproducibility

        # Star system reference
        self.star_system = star_system

        # Civilization parameters
        self.energy_consumption = 0
        self.growth_rate = 1
        self.kardashev_level = 0
        self.extinction_risk = 0.0
        self.germination_event = 0.0
    



    def _calculate_extinction_risk(self, total_energy_available):
        """
        Calculates the extinction risk based on rapid growth during scarcity
        and incorporating dangers from the star system.
        """
        scarcity_factor = max(0, self.energy_consumption/(total_energy_available if total_energy_available > 1 else 1))
                # Probability of triggering (e.g., 30% chance)
        self.extinction_risk_probability = 1e-6*scarcity_factor

        # Check if the event should trigger
        if self.random_gen.random() < self.extinction_risk_probability:
            self.extinction_risk = (
            total_energy_available * math.exp(-0.5*((((1 - abs(self.random_gen.gauss(0, (scarcity_factor +1) / 3))) - 0)/( 1 / 9)) ** 2)))
        else:
            self.extinction_risk = 0

        #(1 * math.exp(-(((1 - abs(self.random_gen.gauss(0, 1 / 3))) - 0) ** 2) /(2 * ((1 + 1.0001) / 3000) ** 2)))
        
    def _calculate_growth_rate(self, total_energy_available):
        """
        Calculates the growth rate of the civilization based on energy consumption
        and available energy budgets.
        """
        if self.energy_consumption <= total_energy_available:
            abundance_factor = 1 - (self.energy_consumption / (total_energy_available if total_energy_available > 1 else 1))
            self.growth_rate = 1 +  abundance_factor*0.0001
        else:
            self.growth_rate = 1
    def _update_energy_consumption(self, total_energy_available):
        """
        Updates the energy consumption based on the growth rate and available energy.
        Caps the energy consumption to the maximum available energy.
        """
        StarParameters = self.star_system.get_parameters()
        danger_impact = StarParameters['danger']
        self.energy_consumption = (((self.energy_consumption+1)**self.growth_rate)-1) + danger_impact - self.extinction_risk
        #print(self.energy_consumption,self.growth_rate,danger_impact,self.germination_event)
        self.energy_consumption = max(0, min(self.energy_consumption, (total_energy_available if total_energy_available > 1 else 1)))
        

    def _update_kardashev_level(self):
        """
        Updates the civilization's Kardashev level based on energy consumption.
        """
        energy_budget = self.star_system.get_parameters()
        if self.energy_consumption >= energy_budget['star_energy_power']+energy_budget['planets_power']+energy_budget['germination_planet_power']:
            self.kardashev_level = 4
        elif self.energy_consumption >= energy_budget['planets_power']+energy_budget['germination_planet_power']:
            self.kardashev_level = 3
        elif self.energy_consumption >= energy_budget['germination_planet_power']:
            self.kardashev_level = 2
        elif self.energy_consumption > 0 and self.energy_consumption < energy_budget['germination_planet_power']:
            self.kardashev_level = 1
        else:
            self.kardashev_level = 0

    def update(self):
        """
        Updates the civilization's parameters for the current time step.
        """
        #self.star_system.update(global_time)  # Update the star system for the current time step
        energy_budget = self.star_system.get_parameters()

        if self.kardashev_level >= 3:
            total_energy_available = (
                min(energy_budget['germination_planet_power'] +
                energy_budget['planets_power'],energy_budget['star_energy_power']) +
                energy_budget['star_energy_power']
            )
        elif self.kardashev_level == 2 :
            total_energy_available = (
                min(energy_budget['germination_planet_power'] +
                energy_budget['planets_power'],energy_budget['star_energy_power'])
            )
        elif self.kardashev_level < 2:
            total_energy_available = min(energy_budget['germination_planet_power'],energy_budget['star_energy_power'])
        else:
            total_energy_available = 1

        self._calculate_growth_rate(total_energy_available)
        self._update_energy_consumption(total_energy_available)
        self._calculate_extinction_risk(total_energy_available)
        self._update_kardashev_level()
        self.total_energy_available = total_energy_available

    def get_parameters(self):
        """
        Returns the current parameters of the civilization.
        """
        return {
            'energy_consumption': self.energy_consumption,
            'growth_rate': self.growth_rate,
            'kardashev_level': self.kardashev_level,
            'extinction_risk': self.extinction_risk,
            'energy_available': self.total_energy_available,
            'star_energy_power': self.star_system.get_parameters()['star_energy_power'],
            'planets_power': self.star_system.get_parameters()['planets_power'],
            'germination_planet_power': self.star_system.get_parameters()['germination_planet_power'],
            'Star_System_Danger': self.star_system.get_parameters()['danger']
        }

# # Example usage:
# if __name__ == "__main__":
#     from Star_System_Module import StarSystem  # Import the StarSystem class

#     star_system = StarSystem(seed=42, star_type="G-type")
#     civ = Civilization(seed=30, star_system=star_system)

#     time_steps = int(55e5)
#     energy_consumptions = []
#     growth_rates = []
#     kardashev_levels = []
#     extinction_risks = []
#     energy_available = []
#     star_energy_power = []
#     planets_power = []
#     germination_planet_power = []
#     Star_System_Danger=[]

#     for global_time in range(time_steps):
#         civ.update()
#         params = civ.get_parameters()
#         energy_consumptions.append(1+params['energy_consumption'])
#         growth_rates.append(params['growth_rate'])
#         kardashev_levels.append(params['kardashev_level'])
#         extinction_risks.append(np.sign(-params['extinction_risk']))
#         energy_available.append(1+params['energy_available'])
#         star_energy_power.append(1+params['star_energy_power'])
#         planets_power.append(1+params['planets_power'])
#         germination_planet_power.append(params['germination_planet_power'])
#         Star_System_Danger.append(np.sign(params['Star_System_Danger']))
#     # Plotting results
#     plt.figure(figsize=(12, 10))

#     plt.subplot(6, 1, 1)
#     plt.plot(range(time_steps), energy_consumptions, label='Energy Consumption', color='blue')
#     plt.ylabel('Energy Consumption')
#     plt.yscale('log')
#     plt.legend()

#     plt.subplot(6, 1, 2)
#     plt.plot(range(time_steps), growth_rates, label='Growth Rate', color='green')
#     plt.ylabel('Growth Rate')
#     plt.legend()

#     plt.subplot(6, 1, 3)
#     plt.plot(range(time_steps), extinction_risks, label='Extinction Risk', color='red')
#     plt.plot(range(time_steps), Star_System_Danger, label='Star Danger', color='purple')
#     plt.ylabel('Risk')
#     plt.legend()

#     plt.subplot(6, 1, 4)
#     plt.plot(range(time_steps), energy_available, label='Energy Available', color='yellow')
#     plt.ylabel('Energy Available')
#     plt.yscale('log')
#     plt.legend()

#     plt.subplot(6, 1, 5)
#     plt.plot(range(time_steps), star_energy_power, label='Star Energy Power', color='orange')
#     plt.plot(range(time_steps), planets_power, label='Planets Power', color='purple')
#     plt.plot(range(time_steps), germination_planet_power, label='Germination Power', color='pink')
#     plt.ylabel('Star & Planets Power')
#     plt.yscale('log')
#     plt.xlabel('Time Steps')
#     plt.legend()

#     plt.subplot(6, 1, 6)
#     plt.plot(range(time_steps), kardashev_levels, label='Level', color='yellow')
#     plt.ylabel('Level')
#     plt.legend()

#     plt.tight_layout()
#     plt.show()
