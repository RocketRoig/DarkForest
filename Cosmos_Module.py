import random
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

        self._create_star_systems_and_civilizations()

    def _create_star_systems_and_civilizations(self):
        """
        Creates star systems and civilizations that coexist in the cosmos.
        """
        star_types = ['G-type', 'K-type', 'M-type']
        for _ in range(self.num_star_systems):
            # Create Star System
            star_seed = self.random_gen.randint(0, int(1e9))
            star_type = self.random_gen.choice(star_types)
            star_system = StarSystem(seed=star_seed, star_type=star_type)
            self.star_systems.append(star_system)

            # Create Civilization associated with this Star System
            civ_seed = self.random_gen.randint(0, int(1e9))
            civilization = Civilization(seed=civ_seed, star_system=star_system)
            self.civilizations.append(civilization)

    def update(self, global_time):
        """
        Updates all star systems and civilizations for the current global time step.

        Parameters:
        - global_time (int): Current global time step.
        """
        for star_system in self.star_systems:
            star_system.update(global_time)

        for civilization in self.civilizations:
            civilization.update()

    def get_status(self):
        """
        Returns the current status of the cosmos, including star system and civilization data.
        """
        status = {
            "star_systems": [star_system.get_parameters() for star_system in self.star_systems],
            "civilizations": [civilization.get_parameters() for civilization in self.civilizations]
        }
        return status

# Example usage
if __name__ == "__main__":
    num_star_systems = 5
    cosmos = Cosmos(seed=12345, num_star_systems=num_star_systems)

    time_steps = 100
    for global_time in range(time_steps):
        cosmos.update(global_time)

    # Retrieve and print status of the cosmos
    cosmos_status = cosmos.get_status()
    print("Star Systems:")
    for i, star_system in enumerate(cosmos_status["star_systems"]):
        print(f"Star System {i + 1}: {star_system}")

    print("\nCivilizations:")
    for i, civilization in enumerate(cosmos_status["civilizations"]):
        print(f"Civilization {i + 1}: {civilization}")
