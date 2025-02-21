import random
import math
import numpy as np
import sys
#import matplotlib.pyplot as plt



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
                "time_stamp": -1,  # No updates yet
                "known_energy": None, # No updates yet

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
            k=0.0015
            self.growth_rate = np.exp(k) - 1   #1 + 0.0002 #abundance_factor*0.0001
        else:
            self.growth_rate = 1
    def _update_energy_consumption(self, total_energy_available):
        """
        Updates the energy consumption based on the growth rate and available energy.
        Caps the energy consumption to the maximum available energy.
        """
        StarParameters = self.star_system.get_parameters()
        danger_impact = StarParameters['danger']
        self.energy_consumption = self.energy_consumption+self.energy_consumption*self.growth_rate + danger_impact - self.extinction_risk
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
        #self.star_system.update(global_time)  # Update the star system for the current time step
        energy_budget = self.star_system.get_parameters()
        self.limit_KL_2=energy_budget['germination_planet_power']
        self.limit_KL_3=energy_budget['germination_planet_power']+energy_budget['planets_power']
        self.limit_KL_4=energy_budget['germination_planet_power']+energy_budget['planets_power']+energy_budget['star_energy_power']

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
            sys.stdout.write("\033[J")  # Clear everything below the current cursor position
            print(f"Civ {self.civ_id}-{self.group_id} reached level: {self.kardashev_level} on Year: {global_time} with energy: {self.energy_consumption}\n")
        self.comms=self._comms_updates(global_time,communications_list)
        self.colonization_attack=self._attack_planner(global_time)

    def _comms_updates(self, global_time, communications_list):
        """
        Updates the awareness map based on received communications and generates messages for allies when updates occur.
        """
        communications = []  # List of new communications to be sent
        pre_awareness_map = {key: value.copy() for key, value in self.awareness_map.items()}  # Preserve the previous state of the awareness map
        
        if communications_list:
               
            for communication in communications_list:
                
                # Check if the communication is directed at this civilization's star system
                if (communication['mssg_arrival'] == global_time and 
                    communication['destinatary'] == self.star_system.index):
                    # Check if the awareness map needs to be updated
                    
                    position = communication['Position']
                    if ((self.awareness_map[position]['civilization_id'] != communication['target_id'] or
                        self.awareness_map[position]['group_id'] != communication['target_group'] or
                        (self.awareness_map[position]['known_energy'] != communication['target_energy'] and
                         communication['target_energy'] != None )) and
                         self.awareness_map[position]['time_stamp'] < communication['time_stamp']):
                        #when time stam is newer and there is a unpdate on energy consumption or civilization Id, then:
                        # Update awareness map
                        self.awareness_map[position]['civilization_id'] = communication['target_id']
                        self.awareness_map[position]['group_id'] = communication['target_group']
                        self.awareness_map[position]["known_energy"] = communication['target_energy']
                        self.awareness_map[position]["time_stamp"] = communication['time_stamp']
                        
                        if self.group_id != communication['target_group']:
                            
                            self.awareness_map[position]["relationship"] = "Enemy"
                            
                        if ( self.group_id == communication['target_group'] and self.civ_id != communication['target_id']):
                            self.awareness_map[position]["relationship"] = "Ally"


        for star_index_, data in self.awareness_map.items():
            if data["relationship"] == "Ally":    
                for star_index, current_data in self.awareness_map.items():
                    prev_data = pre_awareness_map.get(star_index, {})

                    fields_to_check = ["civilization_id", "group_id","known_energy"]

                    # Compare only the relevant fields
                    if any(current_data.get(field) != prev_data.get(field) for field in fields_to_check):
                        outgoing_message={
                            "destinatary": star_index_,  # Send to this ally star
                            "Origin": self.star_system.index,  # Message reveals the message origin
                            "Position": star_index, # Message reveals the target position
                            "target_id": current_data.get("civilization_id"),  # Message reveals target civiization
                            "target_group": current_data.get("group_id"), # Message reveals target civilization group
                            "target_energy":current_data.get("Known_energy"), # Message reveals target energy consumption
                            "time_stamp":current_data.get("time_stamp"), #time stamp to track updated intelligence.
                            "mssg_distance": self.awareness_map[star_index_]["distance"],  # Distance to the ally star
                            "mssg_arrival": int(global_time + self.awareness_map[star_index_]["distance"]),  # Arrival time
                            "mssg_send_time": global_time,
                        }
                        communications.append(outgoing_message)
                        
        # Set communications to None if no messages were generated
        if not communications:
            communications = None

        return communications

    def _attack_planner(self,global_time):
        """
        Plans an attack based on the current awareness map and Kardashev level.
        """
        colonization_attack=None
        max_danger=0
        target_star_index = None
        for E_star_index,E_star_data in self.awareness_map.items():
                if E_star_data["relationship"] =="Enemy" and E_star_data["known_energy"] is not None:
                    max_danger=max(max_danger,E_star_data["known_energy"])
        
        if (max_danger==0 and self.energy_consumption > 2*self.limit_KL_3):
            min_distance = float('inf')
            for star_index, star_data in self.awareness_map.items():
                if star_data["relationship"] =="Enemy": # Relationships that must be target
                    if star_data["distance"] < min_distance:
                        min_distance = star_data["distance"]
                        target_star_index = star_index
                elif star_data["relationship"] ==None: #  Potential empty Star to colonize
                    if star_data["distance"] < min_distance:
                        min_distance = star_data["distance"]
                        target_star_index = star_index
                        self.awareness_map[target_star_index]["relationship"] = "Colonizing"
                        self.awareness_map[target_star_index]["time_stamp"] = global_time
        if max_danger>0 and self.energy_consumption>max_danger*10:
            for star_index, star_data in self.awareness_map.items():
                if star_data["known_energy"] ==max_danger:
                    target_star_index = star_index
                    min_distance = star_data["distance"]

        #print(f"Targeting star index {target_star_index} with minimum distance {min_distance}")
        if target_star_index is not None:
            colonization_attack= {
                "destinatary": target_star_index,
                "Origin":self.star_system.index,
                "Sender_id": self.civ_id,
                "sender_group": self.group_id,
                "attack_cost": self.energy_consumption*0.5,  # 50% of civilization energy
                "attack_energy": self.energy_consumption*0.5*0.1,  # 10% of the attack is destrutive power
                "attack_speed": 0.01,  # Arbritary 5% of light speed. The speed and the two energies could be dynamic between eachother.
                "attack_distance": int(min_distance),
                "attack_arrival": global_time+int(min_distance/0.01),  # Time the attack will arrive at 0.01 light speed
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

