\
class Player:
    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color
        self.territories_owned = set() # Set of Territory objects or names
        self.cards = [] # For Risk cards
        self.reinforcements = 0
        self.conquered_territory_this_turn = False  # Track if player conquered a territory this turn

    def __repr__(self):
        return f"Player {self.name} ({self.color})"

    def add_territory(self, territory_name: str):
        self.territories_owned.add(territory_name)
        self.conquered_territory_this_turn = True  # Set flag when territory is conquered

    def remove_territory(self, territory_name: str):
        if territory_name in self.territories_owned:
            self.territories_owned.remove(territory_name)

    def get_controlled_territories_count(self) -> int:
        return len(self.territories_owned)

    def add_reinforcements(self, count: int):
        self.reinforcements += count

    def place_army(self, territory_name: str, board: 'GameBoard'):
        """Places one army on a territory, decrementing reinforcements."""
        if territory_name in self.territories_owned and self.reinforcements > 0:
            territory = board.get_territory(territory_name)
            if territory and territory.owner == self.name:
                territory.armies += 1
                self.reinforcements -= 1
                return True
        return False

    def is_eliminated(self) -> bool:
        return not self.territories_owned and self.reinforcements == 0
        
    def add_card(self, card):
        """Add a Risk card to the player's hand."""
        self.cards.append(card)
        
    def get_cards(self):
        """Return the player's hand of Risk cards."""
        return self.cards
        
    def remove_cards(self, cards_to_remove):
        """Remove specific cards from the player's hand."""
        for card in cards_to_remove:
            if card in self.cards:
                self.cards.remove(card)
    
    def reset_conquest_flag(self):
        """Reset the conquered territory flag at the start of a turn."""
        self.conquered_territory_this_turn = False

# Example Usage (can be removed or moved to main.py later)
if __name__ == "__main__":
    player1 = Player(name="Player 1", color="Red")
    player1.add_territory("Alaska")
    player1.add_territory("Northwest Territory")
    print(player1)
    print(f"Territories: {player1.territories_owned}")
    print(f"Reinforcements: {player1.reinforcements}")
