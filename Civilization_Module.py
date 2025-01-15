import random
import math
import numpy as np
import matplotlib.pyplot as plt



class Civilization:
    def __init__(self, seed, star_system,civ_id,group_id,star_map):
        """
        Initializes the Civilization with a deterministic seed and a reference to the StarSystem.

        Parameters:
        - seed (int): Seed for deterministic random number generation.
        - star_system (StarSystem): Instance of the star system providing dynamic energy budgets and dangers.
        """
        self.seed = seed
        self.star_map=star_map
        self.random_gen = random.Random(seed)  # Independent random generator for reproducibility
        self.civ_id = civ_id
        self.group_id = group_id
        # Star system reference
        self.star_system = star_system

        # Civilization parameters
        self.energy_consumption = 0
        self.growth_rate = 1
        self.kardashev_level = 0
        self.extinction_risk = 0.0
        self.germination_event = 0.0
        self.colonization_attack=None
        # Initialize awareness map
        self.awareness_map=self._initialize_awareness_map()

    def _initialize_awareness_map(self):
        """
        Generates the initial awareness map from the star map.
        Includes indexes, types, positions, and relative distances.
        """
        awareness_map = {}
        for star_index, star_data in self.star_map.items():
            position = star_data["position"]
            star_type = star_data["type"]
            distance = self._calculate_distance(position, self.star_system.position)
            awareness_map[star_index] = {
                "type": star_type,
                "position": position,
                "distance": distance,
                "civilization_id": None,  # Initially unknown
                "group_id": None,  # Initially unknown
                "relationship": None,  # Initially unknown
                "last_update_time": -1,  # No updates yet
                "Known_energy": None, # No updates yet

            }
            if star_index==self.star_system.index:
                awareness_map[star_index]["civilization_id"] = self.civ_id
                awareness_map[star_index]["group_id"] = self.group_id
                awareness_map[star_index]["relationship"] = "self"
        return awareness_map

    def _calculate_distance(self, pos1, pos2):
        """
        Calculates the Euclidean distance between two positions in 3D space.
        """
        return sum((pos1[i] - pos2[i]) ** 2 for i in range(3)) ** 0.5

    def _calculate_extinction_risk(self, total_energy_available):
        """
        Calculates the extinction risk based on rapid growth during scarcity
        and incorporating dangers from the star system.
        """
        scarcity_factor = max(0, self.energy_consumption/(total_energy_available if total_energy_available > 1 else 1))
                # Probability of triggering (e.g., 30% chance)
        self.extinction_risk_probability = 1e-8*scarcity_factor

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
        if self.attack_energy > 0:
            self.energy_consumption = max(0, min(self.energy_consumption, (total_energy_available if total_energy_available > 1 else 1)))
            self.energy_consumption +=self.attack_energy
            
        if self.attack_energy < 0:
            self.energy_consumption +=self.attack_energy
            self.energy_consumption = max(0, min(self.energy_consumption, (total_energy_available if total_energy_available > 1 else 1)))
        else:
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

    def update(self,global_time,attack_energy,communications_list):
        """
        Updates the civilization's parameters for the current time step.
        """
        if global_time == 900000:
            print(f" Civ {self.civ_id}-{self.group_id} year {global_time} : {communications_list}")
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

        self.attack_energy = attack_energy
        self._calculate_growth_rate(total_energy_available)
        self._calculate_extinction_risk(total_energy_available)
        self._update_energy_consumption(total_energy_available)
        self.total_energy_available = total_energy_available
        self.prevKL=self.kardashev_level
        self._update_kardashev_level()
        if self.prevKL != self.kardashev_level:
            print(f"Civ {self.civ_id}-{self.group_id} reached level: {self.kardashev_level} on Year: {global_time} with energy: {self.energy_consumption}")
        self.comms=self._comms_updates(global_time,communications_list)
        self.colonization_attack=self._attack_planner(global_time)

    def _comms_updates(self, global_time, communications_list):
        """
        Updates the awareness map based on received communications and generates messages for allies when updates occur.
        """
        communications = []  # List of new communications to be sent
        pre_awareness_map = self.awareness_map  # Preserve the previous state of the awareness map
        
        if communications_list:
            print("Hurrey")
            for communication in communications_list:
                # Check if the communication is directed at this civilization's star system
                if (communication['mssg_arrival'] == global_time and 
                    communication['destinatary'] == self.star_system.index):
                    # Check if the awareness map needs to be updated
                    origin = communication['Origin']
                    if (self.awareness_map[origin]['civilization_id'] != communication['Sender_id'] or
                        self.awareness_map[origin]['group_id'] != communication['sender_group']):
                        print(f"making updates on map {self.awareness_map[origin]}")
                        # Update awareness map
                        self.awareness_map[origin]['civilization_id'] = communication['Sender_id']
                        self.awareness_map[origin]['group_id'] = communication['sender_group']
                        self.awareness_map[origin]["last_update_time"] = global_time
                        
                        if self.group_id != communication['sender_group']:
                            self.awareness_map[origin]["relationship"] = "Enemy"
                        elif ( self.group_id == communication['sender_group'] and self.civ_id != communication['Sender_id']):
                            self.awareness_map[origin]["relationship"] = "Ally"
                            print(f"New Ally {self.awareness_map[origin]} before {pre_awareness_map[origin]}")


        for star_index_, data in self.awareness_map.items():
            if data["relationship"] == "Ally":    
                for star_index, current_data in self.awareness_map.items():
                    prev_data = pre_awareness_map.get(star_index, {})

                    fields_to_check = ["civilization_id", "group_id"]

                    # Compare only the relevant fields
                    if any(current_data.get(field) != prev_data.get(field) for field in fields_to_check):
                        outgoing_message={
                            "destinatary": star_index_,  # Send to this ally star
                            "Origin": star_index,  # Message reveals target star
                            "Sender_id": current_data.get("civilization_id"),  # Message reveals target civiization
                            "sender_group": current_data.get("group_id"), # Message reveals target civilization group
                            "mssg_distance": self.awareness_map[star_index_]["distance"],  # Distance to the ally star
                            "mssg_arrival": int(global_time + self.awareness_map[star_index_]["distance"]),  # Arrival time
                            "mssg_send_time": global_time,
                        }
                        communications.append(outgoing_message)
                        print(f"sending message {communications}")
        # Set communications to None if no messages were generated
        if not communications:
            communications = None

        return communications

    def _attack_planner(self,global_time):
        """
        Plans an attack based on the current awareness map and Kardashev level.
        """
        colonization_attack=None
        if self.kardashev_level == 4:
            min_distance = float('inf')
            target_star_index = None

            for star_index, star_data in self.awareness_map.items():
                if star_data["relationship"] in ["Enemy"]: # Relationships that must be target
                    if star_data["distance"] < min_distance:
                        min_distance = star_data["distance"]
                        target_star_index = star_index
                elif star_data["relationship"] in [None]: # Relationships that must be target
                    if star_data["distance"] < min_distance:
                        min_distance = star_data["distance"]
                        target_star_index = star_index

            if target_star_index is not None:
                self.awareness_map[target_star_index]["relationship"] = "Colonizing"
                self.awareness_map[target_star_index]["last_update_time"] = global_time

                #print(f"Targeting star index {target_star_index} with minimum distance {min_distance}")
                colonization_attack= {
                    "destinatary": target_star_index,
                    "Origin":self.star_system.index,
                    "Sender_id": self.civ_id,
                    "sender_group": self.group_id,
                    "attack_cost": self.energy_consumption*0.1,  # 10% of civilization energy
                    "attack_energy": self.energy_consumption*0.05,  # 50% of the attack is energy
                    "attack_speed": 0.05,  # Arbritary 5% of light speed. The speed and the two energies could be dynamic between eachother.
                    "attack_distance": int(min_distance),
                    "attack_arrival": global_time+int(min_distance/0.05),  # Time the attack will arrive at 0.05 light speed
                    "attack_send_time": global_time,
                }
        return colonization_attack
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
            'Star_System_Danger': self.star_system.get_parameters()['danger'],
            'colonization_attack': self.colonization_attack,
            'communications': self.comms,
        }

# # Example usage:
# if __name__ == "__main__":
#     from Star_System_Module import StarSystem  # Import the StarSystem class
# # Define global time as a global variable
#     global_time = 0
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
