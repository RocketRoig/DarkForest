import random
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from Star_System_Module import StarSystem
from Civilization_Module import Civilization

class Cosmos:
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
        self.star_systems = []
        self.civilizations = []
        self.positions = []  # Stores the positions of star systems
        self.civilization_groups = {}  # Groups of civilizations by origin

        self._create_star_systems()

    def _create_star_systems(self):
        """
        Creates star systems and assigns each a random position.
        """
        star_types = ['G-type', 'K-type', 'M-type']
        for i in range(self.num_star_systems):
            # Create Star System
            star_seed = self.random_gen.randint(0, int(1e9))
            star_type = self.random_gen.choice(star_types)
            star_system = StarSystem(seed=star_seed, star_type=star_type)
            star_system.index = i  # Assign an index to the star system
            star_system.type = star_type  # Store star type
            self.star_systems.append(star_system)

            # Assign a random position in 3D space
            position = (
                self.random_gen.uniform(-1e6, 1e6),  # X-axis position
                self.random_gen.uniform(-1e6, 1e6),  # Y-axis position
                self.random_gen.uniform(-1e6, 1e6)   # Z-axis position
            )
            self.positions.append(position)

    def germination_events(self):
        """
        Monitors the danger parameter of each star system and initiates civilizations
        on stars where germination events occur (positive danger).
        """
        for star_system in self.star_systems:
            params = star_system.get_parameters()
            if params['danger'] > 0:  # Germination event detected
                # Check if a civilization already exists in this star system
                existing_civilization = next((civ for civ in self.civilizations if civ.star_system == star_system), None)
                if not existing_civilization:
                    # Create a new civilization
                    civ_seed = self.random_gen.randint(0, int(1e9))
                    new_civilization = Civilization(seed=civ_seed, star_system=star_system)
                    new_civilization.index = len(self.civilizations)  # Assign a unique index

                    # Create a new group for the civilization
                    group_id = len(self.civilization_groups)
                    self.civilization_groups[group_id] = [new_civilization]
                    new_civilization.group_id = group_id
                    print("Created civilization:" + str(new_civilization.index)+"-"+str(new_civilization.group_id)+". On Year: "+str(global_time)+". On Star: "+str(star_system.index))
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
                    print(f"Civilization {civilization.index} in Star System {civilization.star_system.index} has died on Year: {global_time}")
                    civilization.star_system = None  # Set the star system to None
                    #self.civilizations.remove(civilization)

    def update(self, global_time):
        """
        Updates all star systems, monitors germination events, and checks civilization energy.

        Parameters:
        - global_time (int): Current global time step.
        """
        for star_system in self.star_systems:
            star_system.update(global_time)

        self.germination_events()

        for civilization in self.civilizations:
            if civilization.star_system is not None:  # Only update active civilizations
                civilization.update()
                
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

    def plot_star_systems(self):
        """
        Generates a 3D plot of the star systems, coloring the stars based on their type.
        """
        fig = plt.figure(figsize=(10, 7))
        ax = fig.add_subplot(111, projection='3d')

        # Map star types to colors
        color_map = {
            'G-type': 'yellow',
            'K-type': 'orange',
            'M-type': 'red'
        }

        for i, position in enumerate(self.positions):
            star_type = self.star_systems[i].type
            color = color_map.get(star_type, 'white')
            ax.scatter(position[0], position[1], position[2], c=color, label=star_type if i == 0 else "")

        ax.set_title("3D Star System Positions")
        ax.set_xlabel("X-axis")
        ax.set_ylabel("Y-axis")
        ax.set_zlabel("Z-axis")
        ax.legend()
        plt.show()

# Example usage
if __name__ == "__main__":
    num_star_systems = 20
    cosmos = Cosmos(seed=12345, num_star_systems=num_star_systems)

    time_steps = int(25e5)
    for global_time in range(time_steps):
        cosmos.update(global_time)

    # # Plot the star systems
    # cosmos.plot_star_systems()

    # #Retrieve and print status of the cosmos
    # cosmos_status = cosmos.get_status()
    # print("Star Systems:")
    # for star_system in cosmos_status["star_systems"]:
    #     print(f"Star System {star_system['index']}: {star_system}")

    # print("\nCivilizations:")
    # for civilization in cosmos_status["civilizations"]:
    #     print(f"Civilization {civilization['index']}: {civilization}")

    # print("\nCivilization Groups:")
    # for group_id, group in cosmos_status["civilization_groups"].items():
    #     print(f"Group {group_id}: {group}")
