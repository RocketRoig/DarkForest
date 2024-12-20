import random
import math
import matplotlib.pyplot as plt

class StarSystem:
    def __init__(self, seed, star_type):
        """
        Initializes the Star System with a deterministic seed and a star type.

        Parameters:
        - seed (int): Seed for deterministic random number generation.
        - star_type (str): Type of the star (e.g., 'G-type', 'K-type').
        """
        self.seed = seed
        self.random_gen = random.Random(seed)  # Independent random generator for reproducibility
        self.star_type = star_type
        self.SSb = {
            'germination_planet_power': 0,
            'planets_power': 0,
            'star_energy_budget': 0
        }

        # Star cycle and danger configuration
        self.cycle_length = self._calculate_cycle_length()
        self.brightness_factor = self._get_brightness_factor()
        self.danger_cycle_params = self._calculate_danger_params()
        self.SSb['planets_power'] = self._initialize_planets_power()
        self.SSb['germination_planet_power'] = self._initialize_germination_power()

    def _calculate_cycle_length(self):
        """
        Determines the length of the star's energy cycle based on its type,
        generating a random value within the range for the star type.
        """
        star_type_cycle_map = {
            'G-type': (8e6, 12e6),
            'K-type': (15e5, 25e6),
            'M-type': (25e6, 35e6)
        }
        cycle_range = star_type_cycle_map.get(self.star_type, (10e6, 20e6))
        return self.random_gen.uniform(*cycle_range)

    def _get_brightness_factor(self):
        """
        Determines the brightness factor for the star type.
        This acts as a multiplier for the star's energy budget.
        """
        star_type_brightness_map = {
            'G-type': 1.0e6,  # Base brightness
            'K-type': 0.8e6,  # Slightly dimmer
            'M-type': 0.5e6   # Much dimmer
        }
        return star_type_brightness_map.get(self.star_type, 1.0)  # Default to 1.0

    def _initialize_planets_power(self):
        """
        Initializes the power available from planets in the star system.
        """
        return self.random_gen.uniform(500, 10000)

    def _initialize_germination_power(self):
        """
        Initializes the power available from the germination planet in the star system.
        """
        return self.random_gen.uniform(10, 500)

    def _calculate_star_power(self, global_time):
        """
        Calculates the star's energy budget at a given global time based on its cycle.
        """
        phase = (2 * math.pi * global_time) / self.cycle_length
        return max(0, min(10 * math.sin(phase) * self.brightness_factor, self.brightness_factor))  # Brightness modulates the energy

    def _calculate_danger_params(self):
        """
        Generates danger parameters: frequencies and amplitudes of sub-cycles.
        Includes both periodic and event-based dangers.
        """
        num_cycles = 1  # Simplified for clarity
        danger_params = []

        for cycle in range(num_cycles):
            period = 5e6
            amplitude = period * self.random_gen.uniform(1.0, 3.0)
            is_eventual = True

            danger_params.append({
                'period': period,
                'amplitude': amplitude,
                'is_eventual': is_eventual
            })

        return danger_params

    def _calculate_danger(self, global_time):
        """
        Calculates the danger level (resistance to progress) at a given global time.
        Combines periodic and event-based dangers.
        """
        danger = 0
        for cycle in self.danger_cycle_params:
            phase = (2 * math.pi * global_time) / cycle['period']
            if cycle['is_eventual']:
                # Event-based danger: higher chance of occurrence at peaks
                danger += cycle['amplitude'] * 1000 * math.exp(-(((1-abs(self.random_gen.gauss(0, 1/3))) - 0) ** 2) / (2 * ((math.cos(phase) + 1.00001) / 3000) ** 2))
            else:
                danger += cycle['amplitude'] * math.sin(phase) + cycle['amplitude']
        return danger

    def update(self, global_time):
        """
        Updates the star system's parameters for the given global time step.

        Parameters:
        - global_time (int): The current global time step in the simulation.
        """
        # Update energy budgets
        self.SSb['star_energy_power'] = self._calculate_star_power(global_time)

        # Update resistance to progress (danger)
        self.SSb['danger'] = self._calculate_danger(global_time)

    def get_parameters(self):
        """
        Returns the current parameters of the star system.
        """
        return self.SSb

# Example usage:
# if __name__ == "__main__":
#     system = StarSystem(seed=42, star_type="G-type")

#     global_times = range(int(5e6))  # Simulate for X time steps
#     star_brightness = []
#     danger_levels = []
#     Level_history = []  
#     Level=2
#     for global_time in global_times:
#         system.update(global_time)
#         params = system.get_parameters()
#         Level=min(max(2,Level**1.01-params['danger']),params['star_energy_power']+params['planets_power']+params['germination_planet_power'])
#         Level_history.append(Level-2)
#         star_brightness.append(params['star_energy_power'])
#         danger_levels.append(params['danger'])

# # Plotting the results with dual y-axes
# plt.figure(figsize=(10, 6))

# # Create the first axis for star brightness
# fig, ax1 = plt.subplots()

# ax1.set_xlabel("Global Time")
# ax1.set_ylabel("Civilization level", color="Blue")
# ax1.plot(global_times, Level_history, label="Civilization Level", color="Blue")
# ax1.tick_params(axis='y', labelcolor="Blue")


# # Create the second axis for danger levels
# ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
# ax2.set_ylabel("Danger Levels", color="red")  
# ax2.plot(global_times, danger_levels, label="Danger Levels", color="red")
# ax2.tick_params(axis='y', labelcolor="red")

# # Add titles and grid
# plt.title("Star Brightness and Danger Levels Over Time")
# fig.tight_layout()  # adjust spacing to prevent overlap
# plt.grid()
# plt.show()
