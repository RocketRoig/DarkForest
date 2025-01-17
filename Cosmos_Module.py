import random
from Star_System_Module import StarSystem
from Civilization_Module import Civilization
from vpython import sphere, vector, color, arrow, canvas,helix,rate
import math
import sys
import time
import threading
from flask_app import app, simulation_data  # Import the Flask app and shared data

class Cosmos:
    star_map = {} # Global star map: {index: {"position": position, "type": star_type, "seed": star_seed}}
    def __init__(self, seed, num_star_systems):
        """
        Initializes the Cosmos with a deterministic seed and a number of star systems and civilizations.

        Parameters:
        - seed (int): Seed for deterministic random number generation.
        - num_star_systems (int): Number of star systems to create.
        """
        self.seed = seed
        self.random_gen = random.Random(seed)
        self.num_star_systems = num_star_systems
        self.stars_density=0.0008 # Solay system region ~0.004 stars with habitable planets per cubic light year
        self.star_systems = []
        self.civilizations = []
        self.civilization_groups = {}  # Groups of civilizations by origin
        self.colonization_list = []  # List of ongoing colonizations
        self.communications_list = []  # List of ongoing comms
        self._create_star_systems()


    def _create_star_systems(self):
        """
        Creates star systems and assigns each a random position.
        """
        star_types = ['G-type', 'K-type', 'M-type','F-type','A-type','B-type','O-type']
        for i in range(self.num_star_systems):
            # Create Star System
            star_seed = self.random_gen.randint(0, int(1e9))
            star_type = self.random_gen.choice(star_types)
            star_system = StarSystem(seed=star_seed, star_type=star_type)
            star_system.index = i  # Assign an index to the star system
            star_system.type = star_type  # Store star type
            

            # Assign a random position in 3D space
            Volume_simulation=self.num_star_systems/self.stars_density
            Length_simulation=Volume_simulation**(1/3)
            position = (
                self.random_gen.uniform(-Length_simulation/2, Length_simulation/2),  # X-axis position
                self.random_gen.uniform(-Length_simulation/2, Length_simulation/2),  # Y-axis position
                self.random_gen.uniform(-Length_simulation/2, Length_simulation/2)   # Z-axis position
            )
            star_system.position = position
            Cosmos.star_map[i] = {"position": position, "type": star_type, "seed": star_seed}
            self.star_systems.append(star_system)
    def germination_events(self):
        """
        Monitors the danger parameter of each star system and initiates civilizations
        on stars where germination events occur (positive danger).
        """
        for star_system in self.star_systems:
            params = star_system.get_parameters()
            if star_system.index in [0,19] and global_time == 1:
                params['danger'] = 10e-5
            if params['danger'] > 0:  # Germination event detected
                # Check if a civilization already exists in this star system
                existing_civilization = next((civ for civ in self.civilizations if civ.star_system == star_system), None)
                if not existing_civilization:
                    # Create a new civilization and a new group for the civilization
                    civ_seed = self.random_gen.randint(0, int(1e9))
                    civ_id=len(self.civilizations) # Assign a unique index

                    group_id = len(self.civilization_groups) # Assign a new group index
                    new_civilization = Civilization(seed=civ_seed, star_system=star_system,civ_id=civ_id,group_id=group_id,star_map=Cosmos.star_map)
                    new_civilization.index = civ_id  
                    self.civilization_groups[group_id] = [new_civilization]
                    new_civilization.group_id = group_id
                    sys.stdout.write("\033[J")  # Clear everything below the current cursor position
                    print("Created civilization:" + str(new_civilization.index)+"-"+str(new_civilization.group_id)+". On Year: "+str(global_time)+". On Star: "+str(star_system.index)+"\n")
                    self.civilizations.append(new_civilization)

    def monitor_civilization_energy(self):
        """
        Checks the energy of all civilizations, and if a civilization's energy reaches zero,
        declares it dead, makes its star system available for germination, and sets its star system to None.
        """
        for civilization in self.civilizations[:]:  # Copy list to avoid modification during iteration
            if civilization.star_system is not None:  # Only update active civilizations
                params = civilization.get_parameters()
                if params['energy_consumption'] <= 0:
                    sys.stdout.write("\033[J")  # Clear everything below the current cursor position
                    print(f"Civilization {civilization.index} in Star System {civilization.star_system.index} has died on Year: {global_time}\n")
                    civilization.star_system = None  # Set the star system to None
                    #self.civilizations.remove(civilization)
    def update_colonizations(self):
        """
        Updates ongoing attacks.
        """
        for civilization in self.civilizations[:]:  # Copy list to avoid modification during iteration
            if civilization.star_system is not None:  # Only update active civilizations
                params = civilization.get_parameters()
                if params['colonization_attack'] != None:
                    sys.stdout.write("\033[J")  # Clear everything below the current cursor position
                    print(f"Civilization {civilization.index}-{civilization.group_id} from Star System {civilization.star_system.index} is attacking Star System {params['colonization_attack']['destinatary']} on Year: {global_time}. The attack will arrive on Year: {params['colonization_attack']['attack_arrival']} .\n")
                    colonization={
                    "destinatary": params['colonization_attack']['destinatary'],
                    "Origin":params['colonization_attack']['Origin'],
                    "Sender_id": params['colonization_attack']['Sender_id'],
                    "sender_group": params['colonization_attack']['sender_group'],
                    "attack_cost": params['colonization_attack']['attack_energy'],
                    "attack_energy": params['colonization_attack']['attack_energy'],
                    "attack_speed": params['colonization_attack']['attack_speed'],
                    "attack_distance": params['colonization_attack']['attack_distance'],
                    "attack_arrival": params['colonization_attack']['attack_arrival'],
                    "attack_send_time":params['colonization_attack']['attack_send_time'],
                    }
                    self.colonization_list.append(colonization)
    def update_communications(self):
        """
        Updates ongoing communications from each civilization and appends them to the communications list.
        """
        for civilization in self.civilizations[:]:  # Copy list to avoid modification during iteration
            if civilization.star_system is not None:  # Only update active civilizations
                params = civilization.get_parameters()
                if params['communications']:  # Check if the civilization has communications
                    for communication in params['communications']:  # Loop through all communications
                        self.communications_list.append(communication)  # Append each communication
                        #print(f"Communication sent from Civ {civilization.civ_id}: {communication}")

    def _civilizations_clash(self, global_time):  
        """
        Updates the interaction between civilizations and StarSystems and creates the communications resulting from those comms.
        """
        self.attack_list = []  # Aligns with star_system indices
        self.comms_recieved_list = []  # Aligns with star_system indices

        for star_system in self.star_systems:
            self.new_attack = 0  # Initialize new_attack for this star_system
            self.new_comms = []  # Collect communications for this star_system

            for colonization in self.colonization_list:
                # Remove colonization cost from the original civilization's energy
                if (colonization['attack_send_time'] == global_time - 1 and 
                    colonization['Origin'] == star_system.index):
                    self.new_attack += -colonization['attack_cost']
                    sys.stdout.write("\033[J")  # Clear everything below the current cursor position
                    print(f"{colonization['Sender_id']} from star {colonization['Origin']} must Pay attack of: {self.new_attack}")

                # Handle receiving attacks
                elif (colonization['attack_arrival'] == global_time and colonization['destinatary'] == star_system.index):
                    # Find the civilization belonging to this star_system
                    civilization = next(
                        (civ for civ in self.civilizations 
                        if civ.star_system is not None and civ.star_system.index == star_system.index), 
                        None
                    )

                    if civilization:
                        params = civilization.get_parameters()
                        if civilization.group_id == colonization['sender_group']:  # Allied colonization
                            self.new_attack += colonization['attack_energy']
                            sys.stdout.write("\033[J")  # Clear everything below the current cursor position
                            print(f"Allied colonization, energy added: {colonization['attack_energy']}\n")

                            # Create communications for allies
                            self.new_comms.append({
                                "destinatary": star_system.index,
                                "Origin": colonization['Origin'],
                                "Sender_id": colonization['Sender_id'],
                                "sender_group": colonization['sender_group'],
                                "mssg_distance": 0,
                                "mssg_arrival": global_time,
                                "mssg_send_time": global_time,
                            })
                        elif params['energy_consumption'] > colonization['attack_energy']:  # Resisted attack
                            self.new_attack += -colonization['attack_energy']
                            sys.stdout.write("\033[J")  # Clear everything below the current cursor position
                            print(f"ATTACKED: Civilization {civilization.civ_id}-{civilization.group_id} resisted attack from {colonization['Sender_id']}-{colonization['sender_group']}.\n")
                            # revealed position attacker
                            self.communications_list.append({
                                "destinatary": star_system.index,
                                "Origin": colonization['Origin'],
                                "Sender_id": colonization['Sender_id'],
                                "sender_group": colonization['sender_group'],
                                "mssg_distance": 0,
                                "mssg_arrival": global_time,
                                "mssg_send_time": global_time,
                            })
                            # revelad survival civilization
                            self.communications_list.append({
                                "destinatary": colonization['Origin'],
                                "Origin": star_system.index,
                                "Sender_id": civilization.index,
                                "sender_group": civilization.group_id,
                                "mssg_distance": colonization['attack_distance'],
                                "mssg_arrival": int(global_time+colonization['attack_distance']),
                                "mssg_send_time": global_time,
                            })
                        elif params['energy_consumption'] < colonization['attack_energy']:  # Destroyed in attack
                            self.new_attack += -colonization['attack_energy']
                            sys.stdout.write("\033[J")  # Clear everything below the current cursor position
                            print(f"ATTACKED: Civilization {civilization.civ_id}-{civilization.group_id} perished in attack from {colonization['Sender_id']}-{colonization['sender_group']}.\n")

                            # Remaining energy becomes new colonization attempt
                            self.colonization_list.append({
                                "destinatary": colonization['destinatary'],
                                "Origin": colonization['Origin'],
                                "Sender_id": colonization['Sender_id'],
                                "sender_group": colonization['sender_group'],
                                "attack_cost": 0,
                                "attack_energy": colonization['attack_energy'] - params['energy_consumption'],
                                "attack_speed": 1,
                                "attack_distance": colonization['attack_distance'],
                                "attack_arrival": global_time + 1,
                                "attack_send_time": global_time,
                            })

                    elif civilization is None:  # Star system is uninhabited
                        self.panspermia_energy = colonization['attack_energy']
                        new_civ,new_group=self.panspermia(self.panspermia_energy, star_system, colonization['sender_group'])
                        self.communications_list.append({
                                "destinatary": colonization['Origin'],
                                "Origin": star_system.index,
                                "Sender_id": new_civ,
                                "sender_group": new_group,
                                "mssg_distance": colonization['attack_distance'],
                                "mssg_arrival": int(global_time+colonization['attack_distance']),
                                "mssg_send_time": global_time,
                            })
                        self.communications_list.append({
                                "destinatary": star_system.index,
                                "Origin": colonization['Origin'],
                                "Sender_id": colonization['Sender_id'],
                                "sender_group": colonization['sender_group'],
                                "mssg_distance": colonization['attack_distance'],
                                "mssg_arrival": global_time+1,
                                "mssg_send_time": global_time,
                            })
                        self.new_attack += self.panspermia_energy

            # Append communications received by the star system
            for communication in self.communications_list:
                if (communication['mssg_arrival'] == global_time and communication['destinatary'] == star_system.index):
                    self.new_comms.append(communication)


            self.attack_list.append(self.new_attack)  # Append attack aligned with star_system index
            self.comms_recieved_list.append(self.new_comms)  # Append comms aligned with star_system index
  


        return self.attack_list, self.comms_recieved_list

    
    def panspermia(self,pansnpermia_energy,star_system,group_id):
        """
        Initiates civilizations
        from a colonization attempt.
        """
        if pansnpermia_energy > 0:  # Germination event detected
            # Create a new civilization with same group as the colonizer
            civ_seed = self.random_gen.randint(0, int(1e9))
            new_civ_id=len(self.civilizations) # Assign a unique index

            new_civilization = Civilization(seed=civ_seed, star_system=star_system,civ_id=new_civ_id,group_id=group_id,star_map=Cosmos.star_map)
            new_civilization.index = new_civ_id  
            self.civilization_groups[group_id] = [new_civilization]
            new_civilization.group_id = group_id
            sys.stdout.write("\033[J")  # Clear everything below the current cursor position
            print("Colonized civilization:" + str(new_civilization.index)+"-"+str(new_civilization.group_id)+". On Year: "+str(global_time)+". On Star: "+str(star_system.index)+" with energy: "+str(pansnpermia_energy)+"\n")
            self.civilizations.append(new_civilization)
            return new_civ_id,group_id
    def update(self, global_time):
        """
        Updates all star systems, monitors germination events, and checks civilization energy.

        Parameters:
        - global_time (int): Current global time step.
        """  

        for star_system in self.star_systems:
            star_system.update(global_time)

        self.germination_events()
        self.attack_list,self.comms_recieved_list=self._civilizations_clash(global_time)
        for civilization in self.civilizations:
            if civilization.star_system is not None:  # Only update active civilizations
                civilization.update(global_time,attack_energy=self.attack_list[civilization.star_system.index],communications_list=self.comms_recieved_list[civilization.star_system.index])
        self.update_colonizations()
        self.update_communications()    
        self.monitor_civilization_energy()
    def get_status(self):
        """
        Returns the current status of the cosmos, including star system and civilization data.
        """
        status = {
            "star_systems": [
                {
                    "index": star_system.index,
                    "parameters": star_system.get_parameters(),
                    "position": self.positions[i],
                    "type": star_system.type
                } for i, star_system in enumerate(self.star_systems)
            ],
            "civilizations": [
                {
                    "index": civilization.index,
                    "parameters": civilization.get_parameters(),
                    "group_id": civilization.group_id,
                    "star_system": civilization.star_system.index if civilization.star_system else None
                } for civilization in self.civilizations
            ],
            "civilization_groups": {
                group_id: [civ.index for civ in group]
                for group_id, group in self.civilization_groups.items()
            }
        }
        return status
    def display_data(self, global_time, star_systems, civilizations):
        """
        Refreshes the console with a table of stars, civilizations, and their relationships,
        and ensures proper cursor positioning.

        Parameters:
        - global_time: The current simulation year.
        - star_systems: List of star system objects.
        - civilizations: List of civilization objects.
        """
                # Update simulation data
        simulation_data["global_time"] = global_time
        # Iterate over all stars and civilizations
        simulation_data["star_systems"] =[]
        simulation_data["communications_list"]=[]
        for star in star_systems:
            civ = next((c for c in civilizations if c.star_system and c.star_system.index == star.index), None)
            if civ:
                colonizing = [f"{k}" for k, v in civ.awareness_map.items() if v.get("relationship") == "Colonizing"]
                enemies = [f"{v['civilization_id']}-{v['group_id']}" for k, v in civ.awareness_map.items() if v.get("relationship") == "Enemy"]
                allies = [f"{v['civilization_id']}-{v['group_id']}" for k, v in civ.awareness_map.items() if v.get("relationship") == "Ally"]

                colonizing_str = ','.join(colonizing)
                if len(colonizing_str) > 20:
                    colonizing_str = colonizing_str[:20 - 3] + '...'

                simulation_data["star_systems"].append(
                {"index": star.index, 
                 "type": "-", 
                 "civilization": f'{civ.civ_id}-{civ.group_id}', 
                "colonizing": f"{colonizing_str:<25}", 
                "enemies": f"{','.join(enemies):<25}", 
                "allies": f"{','.join(allies):<25}",
                "kardashev_level": f"{civ.kardashev_level}",
                "energy_consumption": f"{civ.energy_consumption}"})
       
            else:
                simulation_data["star_systems"].append(
                {"index": star.index, "type": "-", "civilization": f'-', 
                "colonizing": f"-", "enemies": f"-", "allies": f"-","kardashev_level": f"-",
                "energy_consumption": f"-"})
        for comms in self.communications_list:
            simulation_data["communications_list"].append(
            {"destinatary": f"{comms['destinatary']}", "origin": f"{comms['Origin']}", "civ": f"{comms['Sender_id']}-{comms['Sender_id']}", 
            "send_time": f"{comms['mssg_send_time']}", "arrival_time": f"{comms['mssg_arrival']}", "mssg_distance": f"{comms['mssg_distance']}"})
 


    def run_simulation(self,visualization, steps, step_delay, visualization_interval):
        """
        Visualizes the simulation with optional skipping of visualization steps.

        Parameters:
        - steps (int): Number of simulation steps to run.
        - step_delay (float): Optional delay between steps (None for max speed).
        - visualization_interval (int): Number of steps to skip between visual updates.
        """
        print(f"______Starting simulation_____\n\n\n\n")
        global global_time
        if visualization:
            # Map star types to shapes and colors
            shape_map = {
                'G-type': sphere,
                'K-type': sphere,
                'M-type': sphere,
                'F-type': sphere,
                'A-type': sphere,
                'B-type': sphere,
                'O-type': sphere
            }
            ['G-type', 'K-type', 'M-type','F-type','A-type','B-type','O-type']
            color_map = {None: vector(1, 1, 1)}  # Default to white
            color_map.update(self.generate_color_map(20))  # Add dynamic colors

            # Determine the maximum coordinate value in each axis
            max_coords = [max(abs(star_system.position[i]) for star_system in self.star_systems) for i in range(3)]

            # Define the desired maximum range (max position + 100)
            max_position = 100 + 1  # Adjust for sphere radius (default is 1)

            # Scaling factors for each axis
            scaling_factors = [max_position / max_coord if max_coord != 0 else 1 for max_coord in max_coords]

            # Create VPython objects for all stars with scaled positions
            star_objects = {}
            for star_system in self.star_systems:
                # Scale each position component
                scaled_position = [
                    star_system.position[i] * scaling_factors[i] for i in range(3)
                ]
                star_pos = vector(*scaled_position)  # Convert to VPython vector
                star_objects[star_system.index] = shape_map[star_system.type](
                    pos=star_pos, radius=1, color=color_map[None],emmisive=True
                )
            # Dictionary to store active arrows and moving spheres
            active_arrows = {}
            moving_spheres = {}
            # Dictionary to store active communication arrows and moving spirals
            active_communications = {}
            moving_spirals = {}

        # Main simulation loop
        for global_time in range(steps):
            # Update simulation state every step
            self.update(global_time) 
            time.sleep(0.0001)           
            # Only visualize on specified intervals
            if global_time % visualization_interval == 0:
                self.display_data(global_time, cosmos.star_systems, cosmos.civilizations)
                if visualization:
                    if step_delay is not None:
                        rate(1 / step_delay)  # Apply delay if provided

                    # Update visualization for civilizations
                    for civilization in self.civilizations:
                        if civilization.star_system:
                            star_index = civilization.star_system.index
                            star_color = color_map.get(civilization.group_id, vector(1, 1, 1))
                            energy_ratio = civilization.energy_consumption / (
                                civilization.star_system.get_parameters()['star_energy_power'] +
                                civilization.star_system.get_parameters()['planets_power'] +
                                civilization.star_system.get_parameters()['germination_planet_power']
                            )
                            star_objects[star_index].color = star_color
                            star_objects[star_index].radius = 1 + energy_ratio * 5

                    # Draw and manage colonization vectors
                    for colonization in self.colonization_list:
                        start_star = self.star_systems[colonization["Origin"]]
                        end_star = self.star_systems[colonization["destinatary"]]

                        # Calculate colonization progress
                        total_time = colonization["attack_arrival"] - colonization["attack_send_time"]
                        elapsed_time = global_time - colonization["attack_send_time"]
                        progress = elapsed_time / total_time if total_time > 0 else 1

                        # Check if colonization is ongoing
                        if colonization["attack_arrival"] > global_time:
                            # Create or update colonization arrow
                            if colonization["destinatary"] not in active_arrows:
                                active_arrows[colonization["destinatary"]] = arrow(
                                    pos=vector(*(start_star.position[i] * scaling_factors[i] for i in range(3))),
                                    axis=vector(*(end_star.position[i] * scaling_factors[i] - start_star.position[i] * scaling_factors[i] for i in range(3))),
                                    shaftwidth=1,
                                    headwidth=3,
                                    headlength=5,
                                    color=vector(1, 1, 0),  # Yellow
                                    opacity=0.5
                                )

                            # Create or update moving sphere
                            if colonization["destinatary"] not in moving_spheres:
                                moving_spheres[colonization["destinatary"]] = sphere(
                                    pos=vector(*(start_star.position[i] * scaling_factors[i] for i in range(3))),
                                    radius=2,
                                    color=vector(0, 1, 1),  # Cyan
                                    opacity=1
                                )

                            # Update moving sphere position
                            moving_spheres[colonization["destinatary"]].pos = vector(
                                *(
                                    start_star.position[i] * scaling_factors[i] +
                                    progress * (end_star.position[i] * scaling_factors[i] - start_star.position[i] * scaling_factors[i])
                                    for i in range(3)
                                )
                            )
                        else:
                            # Remove colonization arrow and sphere when colonization ends
                            if colonization["destinatary"] in active_arrows:
                                active_arrows[colonization["destinatary"]].visible = False
                                del active_arrows[colonization["destinatary"]]

                            if colonization["destinatary"] in moving_spheres:
                                moving_spheres[colonization["destinatary"]].visible = False
                                del moving_spheres[colonization["destinatary"]]

                    # Draw and manage communication vectors
                    for communication in self.communications_list:
                        start_star = self.star_systems[communication["Origin"]]
                        end_star = self.star_systems[communication["destinatary"]]

                        # Calculate communication progress
                        total_time = communication["mssg_arrival"] - communication["mssg_send_time"]
                        elapsed_time = global_time - communication["mssg_send_time"]
                        progress = elapsed_time / total_time if total_time > 0 else 1

                        # Check if communication is ongoing
                        if communication["mssg_arrival"] > global_time:
                            # Create or update communication arrow (thin with no head)
                            if communication["destinatary"] not in active_communications:
                                active_communications[communication["destinatary"]] = arrow(
                                    pos=vector(*(start_star.position[i] * scaling_factors[i] for i in range(3))),
                                    axis=vector(*(end_star.position[i] * scaling_factors[i] - start_star.position[i] * scaling_factors[i] for i in range(3))),
                                    shaftwidth=0.2,  # Thin arrow
                                    headwidth=1,    # No head
                                    headlength=1,   # No head
                                    color=vector(0, 1, 0),  # Green
                                    opacity=0.5
                                )

                            # Create or update moving helix
                            if communication["destinatary"] not in moving_spirals:
                                moving_spirals[communication["destinatary"]] = helix(
                                    pos=vector(*(start_star.position[i] * scaling_factors[i] for i in range(3))),
                                    axis=vector(1, 0, 0),  # Temporary axis, will be updated
                                    radius=1,              # Radius of the helix
                                    thickness=1,           # Thickness of the helix
                                    length=1,              # Length of the helix
                                    coils=2,               # Number of coils
                                    color=vector(1, 0, 1), # Magenta
                                )

                            # Update helix position and axis
                            moving_spirals[communication["destinatary"]].pos = vector(
                                *(start_star.position[i] * scaling_factors[i] +
                                progress * (end_star.position[i] * scaling_factors[i] - start_star.position[i] * scaling_factors[i])
                                for i in range(3))
                            )
                            # Compute the raw vector
                            raw_axis = vector(
                                *(end_star.position[i] * scaling_factors[i] - start_star.position[i] * scaling_factors[i]
                                for i in range(3))
                            )

                            # Normalize the vector and scale it by a fixed scalar
                            axis_length = raw_axis.mag  # Magnitude of the raw axis
                            scalar = 10  # Fixed scalar for the spiral's axis length
                            normalized_axis = raw_axis.norm() * scalar if axis_length > 0 else vector(0, 0, 0)

                            # Update the helix axis
                            moving_spirals[communication["destinatary"]].axis = normalized_axis
                        else:
                            # Remove communication arrow and helix when communication ends
                            if communication["destinatary"] in active_communications:
                                active_communications[communication["destinatary"]].visible = False
                                del active_communications[communication["destinatary"]]

                            if communication["destinatary"] in moving_spirals:
                                moving_spirals[communication["destinatary"]].visible = False
                                del moving_spirals[communication["destinatary"]]




        print("Visualization complete.")



    def generate_color_map(self,num_colors):
        """
        Generates a color map with `num_colors` distinct colors.

        Parameters:
        - num_colors (int): Number of distinct colors to generate.

        Returns:
        - color_map (dict): Dictionary mapping group IDs to VPython colors.
        """
        import colorsys

        color_map = {None: color.white}  # Default for no civilization
        for i in range(num_colors):
            # Evenly spaced hues
            hue = i / num_colors
            rgb = colorsys.hsv_to_rgb(hue, 1, 1)  # Saturation and Value set to 1 for vivid colors
            color_map[i] = vector(rgb[0], rgb[1], rgb[2])  # Convert to VPython color

        return color_map
    def start_flask():
        app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)


# Example usage

if __name__ == "__main__":
    scene = canvas(resizable=True,width=1200, height=600, title="Simulation Canvas")
    num_star_systems = 20
    # Start the Flask app in a separate thread
    flask_thread = threading.Thread(target=Cosmos.start_flask)
    flask_thread.daemon = True
    flask_thread.start()


    cosmos = Cosmos(seed=12345, num_star_systems=num_star_systems)
    time_steps = int(25e6)
    cosmos.run_simulation(visualization=True,steps=time_steps, step_delay=None,visualization_interval=10)

