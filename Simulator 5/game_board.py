class Territory:
    def __init__(self, name: str, continent: str):
        self.name = name
        self.continent = continent
        self.owner = None
        self.armies = 0

    def __repr__(self):
        return f"{self.name} (Owner: {self.owner}, Armies: {self.armies})"

class Continent:
    def __init__(self, name: str, territories: list[str], bonus_armies: int):
        self.name = name
        self.territories = territories  # List of territory names
        self.bonus_armies = bonus_armies

    def __repr__(self):
        return f"{self.name} (Bonus: {self.bonus_armies})"

class GameBoard:
    def __init__(self):
        self.territories: dict[str, Territory] = {}
        self.continents: dict[str, Continent] = {}
        self.adjacencies: dict[str, list[str]] = {} # To store adjacencies
        self._initialize_board()

    def _initialize_board(self):
        # Define Continents
        # Continent(name, list_of_territory_names, bonus_armies)
        self.continents = {
            "NorthAmerica": Continent("North America", [], 5),
            "SouthAmerica": Continent("South America", [], 2),
            "Europe": Continent("Europe", [], 5),
            "Africa": Continent("Africa", [], 3),
            "Asia": Continent("Asia", [], 7),
            "Australia": Continent("Australia", [], 2),
        }

        # Define Territories
        # Territory(name, continent_name)
        na_territories = {
            "Alaska": Territory("Alaska", "NorthAmerica"),
            "NorthwestTerritory": Territory("Northwest Territory", "NorthAmerica"),
            "Greenland": Territory("Greenland", "NorthAmerica"),
            "Alberta": Territory("Alberta", "NorthAmerica"),
            "Ontario": Territory("Ontario", "NorthAmerica"),
            "Quebec": Territory("Quebec", "NorthAmerica"),
            "WesternUS": Territory("Western US", "NorthAmerica"),
            "EasternUS": Territory("Eastern US", "NorthAmerica"),
            "CentralAmerica": Territory("Central America", "NorthAmerica"),
        }
        sa_territories = {
            "Venezuela": Territory("Venezuela", "SouthAmerica"),
            "Peru": Territory("Peru", "SouthAmerica"),
            "Brazil": Territory("Brazil", "SouthAmerica"),
            "Argentina": Territory("Argentina", "SouthAmerica"),
        }
        eu_territories = {
            "Iceland": Territory("Iceland", "Europe"),
            "Scandinavia": Territory("Scandinavia", "Europe"),
            "GreatBritain": Territory("Great Britain", "Europe"),
            "NorthernEurope": Territory("Northern Europe", "Europe"),
            "Ukraine": Territory("Ukraine", "Europe"),
            "WesternEurope": Territory("Western Europe", "Europe"),
            "SouthernEurope": Territory("Southern Europe", "Europe"),
        }
        af_territories = {
            "NorthAfrica": Territory("North Africa", "Africa"),
            "Egypt": Territory("Egypt", "Africa"),
            "EastAfrica": Territory("East Africa", "Africa"),
            "Congo": Territory("Congo", "Africa"),
            "SouthAfrica": Territory("South Africa", "Africa"),
            "Madagascar": Territory("Madagascar", "Africa"),
        }
        as_territories = {
            "Ural": Territory("Ural", "Asia"),
            "Siberia": Territory("Siberia", "Asia"),
            "Yakutsk": Territory("Yakutsk", "Asia"),
            "Kamchatka": Territory("Kamchatka", "Asia"),
            "Irkutsk": Territory("Irkutsk", "Asia"),
            "Mongolia": Territory("Mongolia", "Asia"),
            "Japan": Territory("Japan", "Asia"),
            "Afghanistan": Territory("Afghanistan", "Asia"),
            "China": Territory("China", "Asia"),
            "MiddleEast": Territory("Middle East", "Asia"),
            "India": Territory("India", "Asia"),
            "Siam": Territory("Siam", "Asia"), # Southeast Asia
        }
        au_territories = {
            "Indonesia": Territory("Indonesia", "Australia"),
            "NewGuinea": Territory("New Guinea", "Australia"),
            "WesternAustralia": Territory("Western Australia", "Australia"),
            "EasternAustralia": Territory("Eastern Australia", "Australia"),
        }

        self.territories = {
            **na_territories, **sa_territories, **eu_territories,
            **af_territories, **as_territories, **au_territories
        }

        # Assign territory names to continents
        for terr_name, terr_obj in self.territories.items():
            if terr_obj.continent in self.continents:
                self.continents[terr_obj.continent].territories.append(terr_name)

        # Define Adjacencies
        # (Territory: [Adjacent Territories])
        self.adjacencies = {
            # North America
            "Alaska": ["NorthwestTerritory", "Alberta", "Kamchatka"],
            "NorthwestTerritory": ["Alaska", "Greenland", "Alberta", "Ontario"],
            "Greenland": ["NorthwestTerritory", "Ontario", "Quebec", "Iceland"],
            "Alberta": ["Alaska", "NorthwestTerritory", "Ontario", "WesternUS"],
            "Ontario": ["NorthwestTerritory", "Greenland", "Alberta", "Quebec", "WesternUS", "EasternUS"],
            "Quebec": ["Greenland", "Ontario", "EasternUS"],
            "WesternUS": ["Alberta", "Ontario", "EasternUS", "CentralAmerica"],
            "EasternUS": ["Ontario", "Quebec", "WesternUS", "CentralAmerica"],
            "CentralAmerica": ["WesternUS", "EasternUS", "Venezuela"],

            # South America
            "Venezuela": ["CentralAmerica", "Peru", "Brazil"],
            "Peru": ["Venezuela", "Brazil", "Argentina"],
            "Brazil": ["Venezuela", "Peru", "Argentina", "NorthAfrica"],
            "Argentina": ["Peru", "Brazil"],

            # Europe
            "Iceland": ["Greenland", "Scandinavia", "GreatBritain"],
            "Scandinavia": ["Iceland", "GreatBritain", "NorthernEurope", "Ukraine"],
            "GreatBritain": ["Iceland", "Scandinavia", "NorthernEurope", "WesternEurope"],
            "NorthernEurope": ["Scandinavia", "GreatBritain", "Ukraine", "WesternEurope", "SouthernEurope"],
            "Ukraine": ["Scandinavia", "NorthernEurope", "SouthernEurope", "Ural", "Afghanistan", "MiddleEast"],
            "WesternEurope": ["GreatBritain", "NorthernEurope", "SouthernEurope", "NorthAfrica"],
            "SouthernEurope": ["NorthernEurope", "Ukraine", "WesternEurope", "NorthAfrica", "Egypt", "MiddleEast"],

            # Africa
            "NorthAfrica": ["Brazil", "WesternEurope", "SouthernEurope", "Egypt", "EastAfrica", "Congo"],
            "Egypt": ["SouthernEurope", "NorthAfrica", "EastAfrica", "MiddleEast"],
            "EastAfrica": ["NorthAfrica", "Egypt", "Congo", "SouthAfrica", "Madagascar", "MiddleEast"],
            "Congo": ["NorthAfrica", "EastAfrica", "SouthAfrica"],
            "SouthAfrica": ["EastAfrica", "Congo", "Madagascar"],
            "Madagascar": ["EastAfrica", "SouthAfrica"],

            # Asia
            "Ural": ["Ukraine", "Siberia", "China", "Afghanistan"],
            "Siberia": ["Ural", "Yakutsk", "Irkutsk", "Mongolia", "China"],
            "Yakutsk": ["Siberia", "Kamchatka", "Irkutsk"],
            "Kamchatka": ["Alaska", "Yakutsk", "Irkutsk", "Mongolia", "Japan"],
            "Irkutsk": ["Siberia", "Yakutsk", "Kamchatka", "Mongolia"],
            "Mongolia": ["Siberia", "Irkutsk", "Kamchatka", "Japan", "China"],
            "Japan": ["Kamchatka", "Mongolia"],
            "Afghanistan": ["Ukraine", "Ural", "China", "MiddleEast", "India"],
            "China": ["Ural", "Siberia", "Mongolia", "Afghanistan", "India", "Siam"],
            "MiddleEast": ["Ukraine", "SouthernEurope", "Egypt", "EastAfrica", "Afghanistan", "India"],
            "India": ["Afghanistan", "China", "MiddleEast", "Siam"],
            "Siam": ["China", "India", "Indonesia"],

            # Australia
            "Indonesia": ["Siam", "NewGuinea", "WesternAustralia"],
            "NewGuinea": ["Indonesia", "WesternAustralia", "EasternAustralia"],
            "WesternAustralia": ["Indonesia", "NewGuinea", "EasternAustralia"],
            "EasternAustralia": ["NewGuinea", "WesternAustralia"],
        }

    def get_territory(self, name: str) -> Territory | None:
        return self.territories.get(name)

    def get_continent(self, name: str) -> Continent | None:
        return self.continents.get(name)

    def display_board_state(self):
        print("\n================== BOARD STATE ==================")
        for continent_name, continent_obj in self.continents.items():
            print(f"\n--- {continent_obj.name.upper()} (Bonus: {continent_obj.bonus_armies}) ---")
            if not continent_obj.territories:
                print("    (No territories listed for this continent)")
                continue
            
            # Prepare data for sorted output by territory name
            territory_details = []
            for terr_name in continent_obj.territories:
                terr_obj = self.get_territory(terr_name)
                if terr_obj:
                    owner_display = terr_obj.owner if terr_obj.owner else "Unowned"
                    territory_details.append((terr_obj.name, owner_display, terr_obj.armies))
                else:
                    territory_details.append((terr_name, "ERROR: Not Found", 0))
            
            # Sort territories alphabetically by name for consistent display
            territory_details.sort(key=lambda x: x[0])
            
            # Determine column widths for alignment
            max_name_len = 0
            max_owner_len = 0
            for name, owner, armies in territory_details:
                if len(name) > max_name_len:
                    max_name_len = len(name)
                if len(owner) > max_owner_len:
                    max_owner_len = len(owner)
            
            # Add a little padding
            max_name_len += 2
            max_owner_len += 2

            print(f"    {'Territory'.ljust(max_name_len)} {'Owner'.ljust(max_owner_len)} Armies")
            print(f"    {'-'*max_name_len} {'-'*max_owner_len} ------")
            for name, owner, armies in territory_details:
                print(f"    {name.ljust(max_name_len)} {owner.ljust(max_owner_len)} {str(armies).rjust(6)}")
        print("===============================================")

    def get_adjacent_territories(self, territory_name: str) -> list[str]:
        return self.adjacencies.get(territory_name, [])

# Example Usage (can be removed or moved to main.py later)
if __name__ == "__main__":
    board = GameBoard()
    board.display_board_state()
