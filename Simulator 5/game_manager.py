import random
from game_board import GameBoard
from player import Player
from ai_strategy import create_ai_strategy  # Import the AI strategy system
from diplomacy import DiplomacyManager, TerritoryTreaty, Alliance, TreatyType  # Import diplomacy system
try:
    from game_visualization import GameVisualization
    VISUALIZATION_AVAILABLE = True
except ImportError:
    print("Pygame visualization not available. Running in text-only mode.")
    VISUALIZATION_AVAILABLE = False

# Card types
INFANTRY = "Infantry"
CAVALRY = "Cavalry"
ARTILLERY = "Artillery" 
WILD = "Wild"

class Card:
    def __init__(self, type_name, territory_name=None):
        self.type = type_name  # Infantry, Cavalry, Artillery, or Wild
        self.territory = territory_name  # Territory name or None for wild cards
        
    def __repr__(self):
        if self.territory:
            return f"{self.type} ({self.territory})"
        return f"{self.type} (Wild Card)"

class GameManager:
    def __init__(self, player_names_and_colors: list[tuple[str, str]], use_visualization=True):
        self.game_board = GameBoard()
        self.players = [Player(name, color) for name, color in player_names_and_colors]
        self.current_player_index = 0
        self.game_phase = "setup_territory_claim" # "setup_army_placement", "playing"
        
        # Initialize AI strategies for each player
        self.ai_strategies = {}
        for player in self.players:
            self.ai_strategies[player.name] = create_ai_strategy(player.name, self.game_board)
            
        # Initialize visualization if available
        self.use_visualization = use_visualization and VISUALIZATION_AVAILABLE
        self.visualization = None
        if self.use_visualization:
            self.visualization = GameVisualization(self.game_board)
        
        # Initialize Risk cards deck
        self.cards_deck = self._initialize_cards_deck()
        self.cards_trade_count = 0  # Track how many card sets have been traded in
        
        # Initialize diplomacy system
        self.diplomacy = DiplomacyManager()
            
        self._initialize_game_setup()

    def _initialize_cards_deck(self):
        """Create and shuffle the deck of Risk cards."""
        cards = []
        # Create territory cards - one card per territory
        territory_names = list(self.game_board.territories.keys())
        
        # Distribute card types evenly (except for wilds)
        card_types = [INFANTRY, CAVALRY, ARTILLERY]
        territory_index = 0
        
        for territory_name in territory_names:
            card_type = card_types[territory_index % len(card_types)]
            cards.append(Card(card_type, territory_name))
            territory_index += 1
        
        # Add some wild cards (standard Risk has 2)
        for _ in range(2):
            cards.append(Card(WILD))
            
        # Shuffle the deck
        random.shuffle(cards)
        print(f"Created a deck of {len(cards)} Risk cards.")
        return cards

    def draw_card(self):
        """Draw a card from the deck. If empty, reshuffle all cards except those in players' hands."""
        if not self.cards_deck:
            print("Reshuffling cards deck...")
            # In a real game, we'd collect all cards that aren't in players' hands
            # For now, just create a new deck
            self.cards_deck = self._initialize_cards_deck()
            
        if self.cards_deck:
            return self.cards_deck.pop(0)
        return None  # Should not happen, but just in case

    def _calculate_card_trade_bonus(self):
        """Calculate the bonus armies for trading in a set of cards."""
        # Standard Risk progression: 4, 6, 8, 10, 12, 15, then +5 each time
        if self.cards_trade_count < 6:
            bonus_values = [4, 6, 8, 10, 12, 15]
            return bonus_values[self.cards_trade_count]
        else:
            # After the 6th set, each set is worth 5 more than the previous
            return 15 + (self.cards_trade_count - 5) * 5

    def _check_for_card_set(self, cards):
        """Check if the given cards form a valid set."""
        if len(cards) < 3:
            return False
            
        # Count card types
        type_counts = {INFANTRY: 0, CAVALRY: 0, ARTILLERY: 0, WILD: 0}
        for card in cards:
            type_counts[card.type] += 1
            
        # Check for 3 of a kind
        if any(count >= 3 for card_type, count in type_counts.items() if card_type != WILD):
            return True
            
        # Check for one of each (Infantry, Cavalry, Artillery)
        if all(type_counts[card_type] >= 1 for card_type in [INFANTRY, CAVALRY, ARTILLERY]):
            return True
            
        # Check if wilds can complete a set
        wild_count = type_counts[WILD]
        if wild_count > 0:
            # Check if wilds can complete 3 of a kind
            for card_type in [INFANTRY, CAVALRY, ARTILLERY]:
                if type_counts[card_type] + wild_count >= 3:
                    return True
                    
            # Check if wilds can complete one of each
            missing_types = sum(1 for card_type in [INFANTRY, CAVALRY, ARTILLERY] if type_counts[card_type] == 0)
            if missing_types <= wild_count:
                return True
                
        return False

    def _handle_card_trading(self, player):
        """Handle card trading for reinforcements."""
        if len(player.cards) < 3:
            return 0  # Not enough cards to trade
            
        # Mandatory trading if player has 5+ cards
        must_trade = len(player.cards) >= 5
        if must_trade:
            print(f"{player.name} must trade in cards (has {len(player.cards)} cards).")
        
        # Try to find valid card sets
        valid_sets = []
        if len(player.cards) >= 3:
            # Simple approach: check all possible combinations of 3 cards
            from itertools import combinations
            for card_set in combinations(player.cards, 3):
                if self._check_for_card_set(card_set):
                    valid_sets.append(card_set)
        
        if not valid_sets:
            if must_trade:
                print(f"Warning: {player.name} must trade cards but no valid sets found. This should not happen.")
            return 0
            
        # Select a set to trade (for AI, choose the first valid set)
        selected_set = valid_sets[0]
        
        # Calculate bonus armies
        bonus_armies = self._calculate_card_trade_bonus()
        self.cards_trade_count += 1
        
        # Check for territory bonuses (if player owns territory shown on card)
        territory_bonus = 0
        for card in selected_set:
            if card.territory and card.territory in player.territories_owned:
                territory_bonus += 2
                print(f"{player.name} gets 2 bonus armies for owning {card.territory} shown on a traded card.")
        
        total_bonus = bonus_armies + territory_bonus
        print(f"{player.name} traded in cards for {bonus_armies} armies (plus {territory_bonus} territory bonus).")
        
        # Remove the cards from player's hand
        player.remove_cards(selected_set)
        
        # Add the cards back to the bottom of the deck
        self.cards_deck.extend(selected_set)
        
        return total_bonus

    def _initialize_game_setup(self):
        print("\n--- Initializing Game Setup ---")
        self._determine_starting_armies()
        self._distribute_territories()
        self._initial_army_placement_on_claimed_territories()
        self._setup_place_remaining_armies() # New method call

        self.game_phase = "playing" 
        print("\n--- All Initial Armies Placed. Game Starting! ---")
        self.game_board.display_board_state()
        for player in self.players:
            print(f"{player.name} ({player.color}) has {player.reinforcements} armies to place and owns: {player.territories_owned}")
        
        # Determine turn order (can be more sophisticated, e.g., rolling dice)
        random.shuffle(self.players)
        self.current_player_index = 0
        print(f"\nTurn order: {[p.name for p in self.players]}")
        print(f"It is now {self.players[self.current_player_index].name}\\\'s turn.") # Updated message

    def _determine_starting_armies(self):
        num_players = len(self.players)
        starting_armies = 0
        if num_players == 2: # Custom rule, standard Risk is 3-6
            starting_armies = 40
        elif num_players == 3:
            starting_armies = 35
        elif num_players == 4:
            starting_armies = 30
        elif num_players == 5:
            starting_armies = 25
        elif num_players == 6:
            starting_armies = 20
        else:
            raise ValueError(f"Unsupported number of players: {num_players}. Must be between 2 and 6.")

        for player in self.players:
            player.reinforcements = starting_armies
        print(f"Each of the {num_players} players starts with {starting_armies} armies.")

    def _distribute_territories(self):
        all_territory_names = list(self.game_board.territories.keys())
        random.shuffle(all_territory_names)
        
        player_index = 0
        for territory_name in all_territory_names:
            current_player = self.players[player_index]
            territory = self.game_board.get_territory(territory_name)
            if territory:
                territory.owner = current_player.name
                # territory.armies = 1 # Initial army placed in the next step
                current_player.add_territory(territory_name)
                # current_player.reinforcements -= 1 # Decrement from total starting armies
            
            player_index = (player_index + 1) % len(self.players)
        print("\nTerritories have been distributed.")

    def _initial_army_placement_on_claimed_territories(self):
        """Each player places one army on each territory they own."""
        for player in self.players:
            for territory_name in player.territories_owned:
                territory = self.game_board.get_territory(territory_name)
                if territory and territory.owner == player.name:
                    if player.reinforcements > 0:
                        territory.armies += 1
                        player.reinforcements -= 1
                    else:
                        # This case should ideally not be hit if starting armies are sufficient
                        # to place at least one on each claimed territory.
                        print(f"Warning: {player.name} ran out of armies to place 1 on each territory.")
        print("Initial 1 army placed on each claimed territory.")

    def _setup_place_remaining_armies(self):
        print("\n--- Placing Remaining Armies ---")
        for player in self.players: # Iterate in initial order for fairness before shuffling for turn order
            if not player.territories_owned:
                print(f"{player.name} has no territories to place armies on.")
                continue
            
            print(f"{player.name} ({player.color}) is placing {player.reinforcements} armies.")
            territories_list = list(player.territories_owned)
            while player.reinforcements > 0 and territories_list:
                # Basic AI: Distribute armies somewhat randomly
                chosen_territory_name = random.choice(territories_list)
                player.place_army(chosen_territory_name, self.game_board)
                # To prevent infinite loop if a territory somehow can't be placed on, though place_army handles it.
                # For very few territories and many armies, this will concentrate them, which is fine.
            if player.reinforcements > 0:
                # This might happen if a player has armies but somehow no valid territories (should not occur with current logic)
                print(f"Warning: {player.name} still has {player.reinforcements} armies left but couldn't place them.")
        print("All players have placed their initial armies.")

    def get_current_player(self) -> Player:
        return self.players[self.current_player_index]

    def next_turn(self):
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        print(f"\n--- {self.get_current_player().name}\\\'s Turn ({self.get_current_player().color}) ---")

    def _calculate_reinforcements(self, player: Player) -> int:
        """
        Calculate reinforcements according to official Risk rules:
        1. Count territories and divide by 3 (round down), with a minimum of 3
        2. Add continent bonuses if player controls entire continents
        3. Add card bonuses (handled separately in the card trading phase)
        """
        territories_owned_count = player.get_controlled_territories_count()
        reinforcements = max(3, territories_owned_count // 3)  # Official Risk rule: 1 per 3 territories, min 3

        # Add continent bonuses - if player controls all territories in a continent
        for continent_name, continent_obj in self.game_board.continents.items():
            is_owner_of_all = True
            if not continent_obj.territories:  # Skip if continent has no territories listed (should not happen)
                continue
            for territory_name in continent_obj.territories:
                territory = self.game_board.get_territory(territory_name)
                if not territory or territory.owner != player.name:
                    is_owner_of_all = False
                    break
            if is_owner_of_all:
                reinforcements += continent_obj.bonus_armies
                print(f"{player.name} gets {continent_obj.bonus_armies} bonus armies for controlling {continent_name}.")
        
        return reinforcements

    def _reinforcement_phase(self, player: Player):
        if self.use_visualization:
            self.visualization.draw_board(self.players, player, "Reinforcement")
            self.visualization.pause(0.5)
        
        num_reinforcements = self._calculate_reinforcements(player)
        player.add_reinforcements(num_reinforcements)
        print(f"{player.name} gets {num_reinforcements} reinforcements. Total: {player.reinforcements}")

        if not player.territories_owned:
            print(f"{player.name} has no territories to place reinforcements.")
            return

        print(f"{player.name} is placing {player.reinforcements} reinforcements.")
        
        # Use AI strategy to determine best reinforcement placements
        ai_strategy = self.ai_strategies.get(player.name)
        if ai_strategy:
            # Get prioritized territories for reinforcement
            prioritized_territories = ai_strategy.get_best_reinforcement_territories(
                player.name, list(player.territories_owned)
            )
            
            # Place armies according to the prioritization
            temp_reinforcements_to_place = player.reinforcements
            
            if prioritized_territories:
                print(f"{player.name} identified {len(prioritized_territories)} front-line territories: {prioritized_territories}")
                reinforcement_index = 0
                
                for _ in range(temp_reinforcements_to_place):
                    if player.reinforcements <= 0:
                        break
                        
                    # Cycle through the prioritized territories
                    territory_name = prioritized_territories[reinforcement_index % len(prioritized_territories)]
                    reinforcement_index += 1
                    
                    # Place the army
                    territory = self.game_board.get_territory(territory_name)
                    if territory:
                        prev_armies = territory.armies
                        player.place_army(territory_name, self.game_board)
                        print(f"Placed army on front-line: {territory_name} (now {territory.armies} armies)")
            else:
                print(f"{player.name} has no front-line territories. Placing randomly.")
                all_owned_territories = [self.game_board.get_territory(t) for t in player.territories_owned if self.game_board.get_territory(t)]
                if not all_owned_territories:
                    print(f"{player.name} has no territories at all to place armies.")
                    return
                    
                for _ in range(temp_reinforcements_to_place):
                    if player.reinforcements <= 0:
                        break
                    chosen_territory = random.choice(all_owned_territories)
                    player.place_army(chosen_territory.name, self.game_board)
                    print(f"Placed army randomly on: {chosen_territory.name} (now {chosen_territory.armies} armies)")
        else:
            # Fallback to the old method if no AI strategy is available
            # ...existing code for random placement...
            front_line_territories = []
            for terr_name in player.territories_owned:
                is_front_line = False
                adj_territories = self.game_board.get_adjacent_territories(terr_name)
                for adj_name in adj_territories:
                    adj_terr_obj = self.game_board.get_territory(adj_name)
                    if adj_terr_obj and adj_terr_obj.owner != player.name:
                        is_front_line = True
                        break
                if is_front_line:
                    front_line_territories.append(self.game_board.get_territory(terr_name))

            temp_reinforcements_to_place = player.reinforcements

            if front_line_territories:
                print(f"{player.name} identified {len(front_line_territories)} front-line territories: {[t.name for t in front_line_territories]}")
                for _ in range(temp_reinforcements_to_place):
                    if player.reinforcements == 0: break
                    if not front_line_territories: 
                        all_owned_territories = [self.game_board.get_territory(t) for t in player.territories_owned if self.game_board.get_territory(t)]
                        if not all_owned_territories: break
                        chosen_territory = random.choice(all_owned_territories)
                        player.place_army(chosen_territory.name, self.game_board)
                        print(f"Fallback: Placed army on {chosen_territory.name}")
                        continue

                    front_line_territories.sort(key=lambda t: t.armies)
                    min_armies = front_line_territories[0].armies
                    candidates = [t for t in front_line_territories if t.armies == min_armies]
                    chosen_territory = random.choice(candidates)
                    player.place_army(chosen_territory.name, self.game_board)
                    print(f"Placed army on front-line: {chosen_territory.name} (now {chosen_territory.armies} armies)")
            else:
                # No front-line territories, place randomly on any owned territory
                print(f"{player.name} has no front-line territories. Placing randomly.")
                all_owned_territories = [self.game_board.get_territory(t) for t in player.territories_owned if self.game_board.get_territory(t)]
                if not all_owned_territories:
                    print(f"{player.name} has no territories at all to place armies.")
                    return

                for _ in range(temp_reinforcements_to_place):
                    if player.reinforcements == 0: break
                    if not all_owned_territories: break
                    chosen_territory = random.choice(all_owned_territories)
                    player.place_army(chosen_territory.name, self.game_board)
                    print(f"Placed army randomly on: {chosen_territory.name} (now {chosen_territory.armies} armies)")

        print(f"{player.name} has finished placing reinforcements.")
        # Update visualization after reinforcement
        if self.use_visualization:
            self.visualization.draw_board(self.players, player, "Reinforcement Complete")
            self.visualization.pause(0.5)

    def _roll_dice(self, num_dice: int) -> list[int]:
        """Rolls a specified number of dice."""
        return sorted([random.randint(1, 6) for _ in range(num_dice)], reverse=True)

    def _resolve_attack(self, attacking_player: Player, defending_player: Player, 
                        attacking_territory: 'Territory', defending_territory: 'Territory', 
                        attacker_armies_for_attack: int):
        """
        Resolves a single attack round (one set of dice rolls).
        Modified to check for diplomatic treaties before allowing attacks.
        """
        # Check for diplomatic treaties before allowing attack
        if self.diplomacy.has_active_alliance(attacking_player.name, defending_player.name):
            print(f"{attacking_player.name} cannot attack {defending_player.name} due to an active alliance.")
            return False
            
        if self.diplomacy.has_territory_treaty(
            attacking_player.name, attacking_territory.name,
            defending_player.name, defending_territory.name
        ):
            # If there's a territory treaty, the attack is not allowed
            print(f"{attacking_player.name} cannot attack from {attacking_territory.name} to {defending_territory.name} due to a territory treaty.")
            return False
            
        # Original attack resolution logic continues from here
        if not attacking_territory or not defending_territory:
            return False

        # Determine number of dice
        # Attacker: 1 to 3 dice, must have more armies than dice rolled
        num_attacker_dice = 0
        if attacker_armies_for_attack >= 3 and attacking_territory.armies > 3: # Need >3 armies to roll 3 dice (3 attacking, 1 stays)
            num_attacker_dice = 3
        elif attacker_armies_for_attack >= 2 and attacking_territory.armies > 2: # Need >2 armies to roll 2 dice
            num_attacker_dice = 2
        elif attacker_armies_for_attack >= 1 and attacking_territory.armies > 1: # Need >1 army to roll 1 die
            num_attacker_dice = 1
        else:
            print(f"Attack cancelled: {attacking_player.name} does not have enough armies in {attacking_territory.name} to attack with {attacker_armies_for_attack} units.")
            return False # Not enough armies to attack as intended

        # Defender: 1 or 2 dice, based on armies in territory
        num_defender_dice = 0
        if defending_territory.armies >= 2:
            num_defender_dice = 2
        elif defending_territory.armies == 1:
            num_defender_dice = 1
        else: # Should not happen if territory still has owner
            print(f"Error: Defending territory {defending_territory.name} has no armies.")
            return False

        if num_attacker_dice == 0:
            return False

        attacker_rolls = self._roll_dice(num_attacker_dice)
        defender_rolls = self._roll_dice(num_defender_dice)

        print(f"{attacking_player.name} attacks {defending_territory.name} from {attacking_territory.name}!")
        print(f"Attacker ({attacking_territory.armies} armies, using {attacker_armies_for_attack} for this wave, rolling {num_attacker_dice} dice): {attacker_rolls}")
        print(f"Defender ({defending_territory.armies} armies, rolling {num_defender_dice} dice): {defender_rolls}")

        attacker_losses = 0
        defender_losses = 0

        # Compare dice
        for i in range(min(len(attacker_rolls), len(defender_rolls))):
            if attacker_rolls[i] > defender_rolls[i]:
                defender_losses += 1
            else:
                attacker_losses += 1
        
        attacking_territory.armies -= attacker_losses
        defending_territory.armies -= defender_losses

        print(f"Result: Attacker loses {attacker_losses} armies, Defender loses {defender_losses} armies.")
        print(f"{attacking_territory.name} now has {attacking_territory.armies} armies.")
        print(f"{defending_territory.name} now has {defending_territory.armies} armies.")

        # If territory is conquered, break any existing treaties
        if defending_territory.armies <= 0:
            print(f"{defending_territory.name} has been conquered by {attacking_player.name}!")
            
            # Break alliance if one exists
            if self.diplomacy.has_active_alliance(attacking_player.name, defending_player.name):
                # Find and break the alliance
                for treaty in self.diplomacy.get_player_treaties(attacking_player.name):
                    if (treaty.treaty_type == TreatyType.ALLIANCE and 
                        treaty.involves_player(defending_player.name)):
                        self.diplomacy.break_treaty(treaty)
                        print(f"Alliance between {attacking_player.name} and {defending_player.name} has been broken!")
                        break
            
            # Change territory ownership
            defending_territory.owner = attacking_player.name
            defending_player.remove_territory(defending_territory.name)
            attacking_player.add_territory(defending_territory.name)

            # Attacker must move at least num_attacker_dice armies, up to attacker_armies_for_attack
            # and leave at least 1 behind in the attacking_territory.
            min_move = num_attacker_dice 
            # Max armies to move is all but one from the original attacking stack,
            # but not more than what was committed to the attack wave that succeeded.
            armies_to_move = min(min_move, attacking_territory.armies - 1)  # Ensure at least 1 left
            armies_to_move = max(1, armies_to_move)  # Must move at least 1 if territory is taken

            if attacking_territory.armies > armies_to_move:  # if we have more than 1 army to move (after ensuring 1 is left)
                defending_territory.armies = armies_to_move
                attacking_territory.armies -= armies_to_move
                print(f"{attacking_player.name} moves {armies_to_move} armies into {defending_territory.name}.")
            else:  # Not enough armies to move the dice count and leave 1, so move all but 1
                armies_to_move = attacking_territory.armies - 1
                if armies_to_move > 0:
                    defending_territory.armies = armies_to_move
                    attacking_territory.armies -= armies_to_move
                    print(f"{attacking_player.name} moves {armies_to_move} armies into {defending_territory.name}.")
                else:  # This should not happen if attack was possible
                    defending_territory.armies = 1  # Must occupy with at least 1
                    attacking_territory.armies -= 1  # This might make it 0, which is an issue.
                    print(f"Error in army movement logic post-conquest for {defending_territory.name}")

            if defending_player.is_eliminated():
                print(f"!!!!!!!!!! {defending_player.name} has been eliminated! !!!!!!!!!!")
                # Break all treaties involving the eliminated player
                for treaty in list(self.diplomacy.get_player_treaties(defending_player.name)):
                    self.diplomacy.break_treaty(treaty)
                    print(f"Treaty broken due to player elimination: {treaty}")
                    
        return True

    def _attack_phase(self, player: Player):
        print(f"--- {player.name}'s Turn --- Phase: Attack ---")
        if self.use_visualization:
            self.visualization.draw_board(self.players, player, "Attack")
            self.visualization.pause(0.5)
            
        attack_count = 0
        max_attacks = 20  # Safety limit for very aggressive AIs
        
        # Get AI strategy for this player
        ai_strategy = self.ai_strategies.get(player.name)
        
        while attack_count < max_attacks:  # Loop for multiple attacks
            attack_count += 1
            
            # Use AI strategy to determine best attack targets
            best_attack = None
            
            if ai_strategy:
                # Get prioritized attack targets
                attack_targets = ai_strategy.get_attack_targets(
                    player.name, list(player.territories_owned)
                )
                
                # Filter out targets protected by treaties
                filtered_targets = []
                for from_terr_name, to_terr_name, armies_for_attack_wave in attack_targets:
                    from_terr_obj = self.game_board.get_territory(from_terr_name)
                    to_terr_obj = self.game_board.get_territory(to_terr_name)
                    
                    if from_terr_obj and to_terr_obj:
                        defending_player_name = to_terr_obj.owner
                        
                        # Skip if there's an alliance with the defending player
                        if self.diplomacy.has_active_alliance(player.name, defending_player_name):
                            continue
                            
                        # Skip if there's a territory treaty covering these territories
                        if self.diplomacy.has_territory_treaty(
                            player.name, from_terr_name,
                            defending_player_name, to_terr_name
                        ):
                            continue
                            
                        # If not protected by treaty, add to filtered targets
                        filtered_targets.append((from_terr_name, to_terr_name, armies_for_attack_wave))
                
                # Choose the best attack if any are available
                if filtered_targets:
                    from_terr_name, to_terr_name, armies_for_attack_wave = filtered_targets[0]
                    from_terr_obj = self.game_board.get_territory(from_terr_name)
                    to_terr_obj = self.game_board.get_territory(to_terr_name)
                    
                    if from_terr_obj and to_terr_obj and from_terr_obj.armies > 1:
                        best_attack = (from_terr_obj, to_terr_obj, armies_for_attack_wave)
            else:
                # Fallback to the old method if no AI strategy is available
                # Find attacks where attacker has significant advantage
                can_attack = False
                possible_attacks = []
                
                for terr_name in player.territories_owned:
                    terr_obj = self.game_board.get_territory(terr_name)
                    if terr_obj and terr_obj.armies > 1:
                        adj_territories = self.game_board.get_adjacent_territories(terr_name)
                        for adj_name in adj_territories:
                            adj_terr_obj = self.game_board.get_territory(adj_name)
                            if adj_terr_obj and adj_terr_obj.owner != player.name:
                                # Skip if protected by treaty
                                defending_player_name = adj_terr_obj.owner
                                
                                # Skip if there's an alliance with the defending player
                                if self.diplomacy.has_active_alliance(player.name, defending_player_name):
                                    continue
                                    
                                # Skip if there's a territory treaty covering these territories
                                if self.diplomacy.has_territory_treaty(
                                    player.name, terr_name,
                                    defending_player_name, adj_name
                                ):
                                    continue
                                
                                possible_attacks.append((terr_name, adj_name, terr_obj.armies - 1))
                                can_attack = True
                
                if can_attack and possible_attacks:
                    # Find best attack based on advantage ratio
                    best_advantage = 1.0
                    random.shuffle(possible_attacks)
                    
                    for from_terr_name, to_terr_name, available_attack_armies in possible_attacks:
                        from_terr_obj = self.game_board.get_territory(from_terr_name)
                        to_terr_obj = self.game_board.get_territory(to_terr_name)
                        
                        if from_terr_obj and to_terr_obj and to_terr_obj.armies > 0:
                            advantage_ratio = from_terr_obj.armies / to_terr_obj.armies
                            
                            if advantage_ratio > best_advantage:
                                best_advantage = advantage_ratio
                                best_attack = (from_terr_obj, to_terr_obj, min(available_attack_armies, 3))
                    
                    # If no good attacks found, consider opportunistic attacks
                    if not best_attack:
                        for from_terr_name, to_terr_name, available_attack_armies in possible_attacks:
                            from_terr_obj = self.game_board.get_territory(from_terr_name)
                            to_terr_obj = self.game_board.get_territory(to_terr_name)
                            
                            if from_terr_obj and to_terr_obj and from_terr_obj.armies > to_terr_obj.armies:
                                best_attack = (from_terr_obj, to_terr_obj, min(available_attack_armies, 3))
                                break
            
            # If no good attack found, end the attack phase
            if not best_attack:
                print(f"{player.name} evaluates options and chooses not to attack further this turn.")
                break
            
            # Execute the chosen attack
            attacking_territory, defending_territory, armies_for_attack_wave = best_attack
            defending_player_name = defending_territory.owner
            defending_player = next((p for p in self.players if p.name == defending_player_name), None)
            
            if not defending_player:
                print(f"Error: Could not find defending player object for {defending_player_name}")
                break
            
            # Get state before attack
            pre_attack_owner = defending_territory.owner
            
            # Resolve the attack
            attack_result = self._resolve_attack(player, defending_player, attacking_territory, defending_territory, armies_for_attack_wave)
            if not attack_result:
                print(f"{player.name} cannot attack {defending_player.name} due to diplomatic restrictions.")
                # Try another attack
                continue
            
            # Update visualization
            if self.use_visualization:
                self.visualization.draw_board(self.players, player, "Attack")
                self.visualization.pause(0.3)
            
            # Decide whether to continue attacking
            territory_captured = defending_territory.owner == player.name
            
            # Use AI strategy to decide whether to continue attacking
            should_continue = False
            
            if territory_captured:
                # After a conquest, more likely to continue
                should_continue = random.random() < 0.8
                if should_continue:
                    print(f"{player.name} is encouraged by the conquest and continues attacking!")
                else:
                    print(f"{player.name} decides to end the attack phase.")
                    break
            else:
                # After a failed attack, less likely to continue
                should_continue = random.random() < 0.5
                if should_continue:
                    print(f"{player.name} will try another attack despite the setback.")
                else:
                    print(f"{player.name} decides to end the attack phase.")
                    break
        
        # If we've reached the max number of attacks, print a message
        if attack_count >= max_attacks:
            print(f"{player.name} has reached the maximum number of attacks for this turn.")

    def _fortify_phase(self, player: Player):
        if self.use_visualization:
            self.visualization.draw_board(self.players, player, "Fortify")
            self.visualization.pause(0.5)
        
        print(f"--- {player.name}'s Turn ({player.color}) --- Phase: Fortify ---")
        if not player.territories_owned or len(player.territories_owned) <= 1:
            print(f"{player.name} has too few territories to fortify.")
            return
        
        # Use AI strategy to determine best fortification move
        ai_strategy = self.ai_strategies.get(player.name)
        best_move = None
        
        if ai_strategy:
            # Get the best fortification move
            best_move = ai_strategy.get_best_fortification_move(
                player.name, list(player.territories_owned)
            )
        else:
            # Fallback to the old method if no AI strategy is available
            # ...existing fortification logic...
            # Strategy: Find an owned territory with >1 army, and move some armies to an adjacent owned territory.
            # Prioritize moving from a territory with many armies to a weaker adjacent one, or towards a front.
            # Simple AI: Find any valid move and execute it.
            
            possible_fortifications = [] # List of (from_territory_obj, to_territory_obj, max_armies_to_move)

            for source_name in player.territories_owned:
                source_territory = self.game_board.get_territory(source_name)
                if source_territory and source_territory.armies > 1:
                    # Simple adjacent fortification for now:
                    q = [(source_territory, [source_territory.name])] # (current_territory, path_taken)
                    visited_for_path = {source_territory.name} # Territories visited in current BFS from source

                    # BFS to find all reachable owned territories from source_territory
                    reachable_owned_territories_from_source = []

                    head = 0
                    while head < len(q):
                        current_terr_obj, _ = q[head]
                        head += 1

                        for adj_name in self.game_board.get_adjacent_territories(current_terr_obj.name):
                            adj_terr_obj = self.game_board.get_territory(adj_name)
                            if adj_terr_obj and adj_terr_obj.owner == player.name and adj_name not in visited_for_path:
                                visited_for_path.add(adj_name)
                                # Add to reachable if it's not the source itself
                                if adj_name != source_name:
                                    reachable_owned_territories_from_source.append(adj_terr_obj)
                                # Continue BFS to find all connected territories
                                q.append((adj_terr_obj, [])) # Path not needed here, just reachability

                    for dest_territory in reachable_owned_territories_from_source:
                        # Can move source_territory.armies - 1
                        armies_available_to_move = source_territory.armies - 1
                        if armies_available_to_move > 0:
                            possible_fortifications.append((source_territory, dest_territory, armies_available_to_move))

            if possible_fortifications:
                # Sort by number of armies to move (which is based on source.armies -1)
                possible_fortifications.sort(key=lambda x: x[2], reverse=True) # Sort by armies_to_move desc
                
                # Pick the one that can move most armies, from a random selection if multiple have same max
                max_movable = possible_fortifications[0][2]
                top_options = [move for move in possible_fortifications if move[2] == max_movable]
                best_choice = random.choice(top_options)
                
                source, dest, armies_to_move = best_choice
                best_move = (source.name, dest.name, armies_to_move)
        
        # Execute the fortification move if one was found
        if best_move:
            source_name, dest_name, armies_to_move = best_move
            source = self.game_board.get_territory(source_name)
            dest = self.game_board.get_territory(dest_name)
            
            if source and dest and source.armies > armies_to_move:
                print(f"{player.name} chooses to fortify by moving {armies_to_move} armies from {source_name} to {dest_name}.")
                source.armies -= armies_to_move
                dest.armies += armies_to_move
                print(f"{source_name} now has {source.armies} armies. {dest_name} now has {dest.armies} armies.")
            else:
                print(f"Warning: Invalid fortification move from {source_name} to {dest_name}.")
        else:
            print(f"{player.name} chooses not to fortify (no beneficial move found by AI).")
        
        # Update visualization after fortification
        if self.use_visualization:
            self.visualization.draw_board(self.players, player, "Fortify Complete")
            self.visualization.pause(0.5)

    def play_turn(self):
        current_player = self.get_current_player()
        if current_player.is_eliminated():  # Check if player was eliminated before their turn starts
            print(f"{current_player.name} ({current_player.color}) is eliminated and skips their turn.")
            return False  # Game continues, but this player is out
            
        # Reset conquest flag at the beginning of the turn
        current_player.reset_conquest_flag()

        # Update diplomacy at the start of the turn
        expired_treaties = self.diplomacy.update_turn()
        if expired_treaties:
            for treaty in expired_treaties:
                player1, player2 = treaty.get_involved_players()
                print(f"Treaty between {player1} and {player2} has expired: {treaty}")
        
        # Diplomacy Phase - Added before Card Trading
        print(f"\n--- {current_player.name}'s Turn ({current_player.color}) --- Phase: Diplomacy ---")
        self._diplomacy_phase(current_player)
        
        # Card Trading Phase - Before Reinforcement
        card_bonus = 0
        if current_player.cards:
            print(f"\n--- {current_player.name}'s Turn ({current_player.color}) --- Phase: Card Trading ---")
            print(f"{current_player.name} has {len(current_player.cards)} cards: {current_player.cards}")
            
            # Handle card trading (mandatory if 5+ cards, optional otherwise)
            card_bonus = self._handle_card_trading(current_player)
            if card_bonus > 0:
                current_player.add_reinforcements(card_bonus)
                print(f"{current_player.name} received {card_bonus} reinforcements from card trading")

        # Reinforcement Phase
        print(f"\n--- {current_player.name}'s Turn ({current_player.color}) --- Phase: Reinforce ---")
        self._reinforcement_phase(current_player)
        
        # Check if player was eliminated
        if current_player.is_eliminated():
            print(f"{current_player.name} ({current_player.color}) was eliminated during the reinforcement phase.")
            return False  # Game continues, player is out

        # Attack Phase
        print(f"\n--- {current_player.name}'s Turn ({current_player.color}) --- Phase: Attack ---")
        self._attack_phase(current_player)

        # Award a Risk card if the player conquered at least one territory
        if current_player.conquered_territory_this_turn:
            card = self.draw_card()
            if card:
                current_player.add_card(card)
                print(f"{current_player.name} receives a Risk card for conquering a territory this turn: {card}")

        # Check for player elimination and card transfer after attack phase
        for other_player in self.players:
            if other_player != current_player and other_player.is_eliminated() and other_player.cards:
                # Transfer cards from eliminated player to the conquering player
                print(f"{current_player.name} receives {len(other_player.cards)} cards from eliminated player {other_player.name}")
                current_player.cards.extend(other_player.cards)
                other_player.cards = []
                
                # Check for mandatory card trading if player now has 5+ cards
                if len(current_player.cards) >= 5:
                    print(f"{current_player.name} must trade cards after eliminating {other_player.name} (now has {len(current_player.cards)} cards)")
                    while len(current_player.cards) >= 5:
                        card_bonus = self._handle_card_trading(current_player)
                        if card_bonus > 0:
                            # In official Risk, these armies can be placed immediately
                            # For simplicity, we'll add them to the player's next turn
                            current_player.add_reinforcements(card_bonus)
                            print(f"{current_player.name} received {card_bonus} reinforcements from mandatory card trading after elimination")

        if self.check_win_condition():  # Check win condition after attack
            return True
        
        # Check if player was eliminated during their attack phase (e.g. lost all territories)
        if current_player.is_eliminated():
            print(f"{current_player.name} ({current_player.color}) was eliminated during their attack phase.")
            return False  # Game continues, player is out

        # Fortify Phase
        print(f"\n--- {current_player.name}'s Turn ({current_player.color}) --- Phase: Fortify ---")
        self._fortify_phase(current_player)

        # Final win condition check for the turn
        if self.check_win_condition():
            return True
            
        return False  # Game continues
    
    def _diplomacy_phase(self, player):
        """Handle diplomatic actions for a player's turn"""
        # First, check for and respond to incoming treaty proposals
        incoming_proposals = self.diplomacy.get_player_proposals(player.name)
        if incoming_proposals:
            print(f"{player.name} has {len(incoming_proposals)} diplomatic proposals to consider:")
            for treaty, from_player in incoming_proposals:
                print(f"- From {from_player}: {treaty}")
                
                # AI decision making for accepting/rejecting treaties
                accept = False
                ai_strategy = self.ai_strategies.get(player.name)
                
                if ai_strategy:
                    # Use AI strategy to evaluate proposals
                    evaluation_score = self.diplomacy.evaluate_treaty_proposal(treaty, ai_strategy)
                    
                    # The higher the score, the more likely to accept
                    threshold = 0.6  # Accept if score > 0.6
                    accept = evaluation_score > threshold
                    
                    print(f"  {player.name} evaluates the proposal (score: {evaluation_score:.2f}) and ", end="")
                else:
                    # Simple random decision if no AI strategy
                    accept = random.random() > 0.4  # 60% chance to accept
                    print(f"  {player.name} ", end="")
                
                if accept:
                    self.diplomacy.accept_treaty(treaty)
                    print("accepts the treaty.")
                else:
                    self.diplomacy.reject_treaty(treaty)
                    print("rejects the treaty.")
        
        # Then, decide whether to propose new treaties
        if random.random() < 0.3:  # 30% chance to propose a treaty each turn
            # Determine which type of treaty to propose
            treaty_type = random.choice(["territory", "alliance"])
            
            # Find a potential treaty partner
            potential_partners = []
            for other_player in self.players:
                if other_player.name != player.name and not other_player.is_eliminated():
                    # Don't propose to players we already have an alliance with
                    if treaty_type == "alliance" and self.diplomacy.has_active_alliance(player.name, other_player.name):
                        continue
                    
                    # Add as potential partner
                    potential_partners.append(other_player)
            
            if potential_partners:
                # Choose a random partner
                partner = random.choice(potential_partners)
                
                if treaty_type == "territory":
                    # Find suitable territories for a territory treaty
                    player_territories = list(player.territories_owned)
                    partner_territories = list(partner.territories_owned)
                    
                    # Find adjacent territories
                    suitable_pairs = []
                    for p1_terr in player_territories:
                        for p2_terr in partner_territories:
                            # Check if territories are adjacent
                            if p2_terr in self.game_board.adjacencies.get(p1_terr, []):
                                suitable_pairs.append((p1_terr, p2_terr))
                    
                    if suitable_pairs:
                        # Choose a random pair
                        terr1, terr2 = random.choice(suitable_pairs)
                        
                        # Create and propose the treaty
                        treaty = TerritoryTreaty(player.name, partner.name, terr1, terr2, duration=3)
                        self.diplomacy.propose_treaty(treaty)
                        print(f"{player.name} proposes a territory treaty to {partner.name}: {treaty}")
                
                elif treaty_type == "alliance":
                    # Create and propose an alliance
                    treaty = Alliance(player.name, partner.name, duration=5)
                    self.diplomacy.propose_treaty(treaty)
                    print(f"{player.name} proposes an alliance to {partner.name}: {treaty}")

    def _resolve_attack(self, attacking_player: Player, defending_player: Player, 
                        attacking_territory: 'Territory', defending_territory: 'Territory', 
                        attacker_armies_for_attack: int):
        """
        Resolves a single attack round (one set of dice rolls).
        Modified to check for diplomatic treaties before allowing attacks.
        """
        # Check for diplomatic treaties before allowing attack
        if self.diplomacy.has_active_alliance(attacking_player.name, defending_player.name):
            print(f"{attacking_player.name} cannot attack {defending_player.name} due to an active alliance.")
            return False
            
        if self.diplomacy.has_territory_treaty(
            attacking_player.name, attacking_territory.name,
            defending_player.name, defending_territory.name
        ):
            # If there's a territory treaty, the attack is not allowed
            print(f"{attacking_player.name} cannot attack from {attacking_territory.name} to {defending_territory.name} due to a territory treaty.")
            return False
            
        # Original attack resolution logic continues from here
        if not attacking_territory or not defending_territory:
            return False

        # Determine number of dice
        # Attacker: 1 to 3 dice, must have more armies than dice rolled
        num_attacker_dice = 0
        if attacker_armies_for_attack >= 3 and attacking_territory.armies > 3: # Need >3 armies to roll 3 dice (3 attacking, 1 stays)
            num_attacker_dice = 3
        elif attacker_armies_for_attack >= 2 and attacking_territory.armies > 2: # Need >2 armies to roll 2 dice
            num_attacker_dice = 2
        elif attacker_armies_for_attack >= 1 and attacking_territory.armies > 1: # Need >1 army to roll 1 die
            num_attacker_dice = 1
        else:
            print(f"Attack cancelled: {attacking_player.name} does not have enough armies in {attacking_territory.name} to attack with {attacker_armies_for_attack} units.")
            return False # Not enough armies to attack as intended

        # Defender: 1 or 2 dice, based on armies in territory
        num_defender_dice = 0
        if defending_territory.armies >= 2:
            num_defender_dice = 2
        elif defending_territory.armies == 1:
            num_defender_dice = 1
        else: # Should not happen if territory still has owner
            print(f"Error: Defending territory {defending_territory.name} has no armies.")
            return False

        if num_attacker_dice == 0:
            return False

        attacker_rolls = self._roll_dice(num_attacker_dice)
        defender_rolls = self._roll_dice(num_defender_dice)

        print(f"{attacking_player.name} attacks {defending_territory.name} from {attacking_territory.name}!")
        print(f"Attacker ({attacking_territory.armies} armies, using {attacker_armies_for_attack} for this wave, rolling {num_attacker_dice} dice): {attacker_rolls}")
        print(f"Defender ({defending_territory.armies} armies, rolling {num_defender_dice} dice): {defender_rolls}")

        attacker_losses = 0
        defender_losses = 0

        # Compare dice
        for i in range(min(len(attacker_rolls), len(defender_rolls))):
            if attacker_rolls[i] > defender_rolls[i]:
                defender_losses += 1
            else:
                attacker_losses += 1
        
        attacking_territory.armies -= attacker_losses
        defending_territory.armies -= defender_losses

        print(f"Result: Attacker loses {attacker_losses} armies, Defender loses {defender_losses} armies.")
        print(f"{attacking_territory.name} now has {attacking_territory.armies} armies.")
        print(f"{defending_territory.name} now has {defending_territory.armies} armies.")

        # If territory is conquered, break any existing treaties
        if defending_territory.armies <= 0:
            print(f"{defending_territory.name} has been conquered by {attacking_player.name}!")
            
            # Break alliance if one exists
            if self.diplomacy.has_active_alliance(attacking_player.name, defending_player.name):
                # Find and break the alliance
                for treaty in self.diplomacy.get_player_treaties(attacking_player.name):
                    if (treaty.treaty_type == TreatyType.ALLIANCE and 
                        treaty.involves_player(defending_player.name)):
                        self.diplomacy.break_treaty(treaty)
                        print(f"Alliance between {attacking_player.name} and {defending_player.name} has been broken!")
                        break
            
            # Change territory ownership
            defending_territory.owner = attacking_player.name
            defending_player.remove_territory(defending_territory.name)
            attacking_player.add_territory(defending_territory.name)

            # Attacker must move at least num_attacker_dice armies, up to attacker_armies_for_attack
            # and leave at least 1 behind in the attacking_territory.
            min_move = num_attacker_dice 
            # Max armies to move is all but one from the original attacking stack,
            # but not more than what was committed to the attack wave that succeeded.
            armies_to_move = min(min_move, attacking_territory.armies - 1)  # Ensure at least 1 left
            armies_to_move = max(1, armies_to_move)  # Must move at least 1 if territory is taken

            if attacking_territory.armies > armies_to_move:  # if we have more than 1 army to move (after ensuring 1 is left)
                defending_territory.armies = armies_to_move
                attacking_territory.armies -= armies_to_move
                print(f"{attacking_player.name} moves {armies_to_move} armies into {defending_territory.name}.")
            else:  # Not enough armies to move the dice count and leave 1, so move all but 1
                armies_to_move = attacking_territory.armies - 1
                if armies_to_move > 0:
                    defending_territory.armies = armies_to_move
                    attacking_territory.armies -= armies_to_move
                    print(f"{attacking_player.name} moves {armies_to_move} armies into {defending_territory.name}.")
                else:  # This should not happen if attack was possible
                    defending_territory.armies = 1  # Must occupy with at least 1
                    attacking_territory.armies -= 1  # This might make it 0, which is an issue.
                    print(f"Error in army movement logic post-conquest for {defending_territory.name}")

            if defending_player.is_eliminated():
                print(f"!!!!!!!!!! {defending_player.name} has been eliminated! !!!!!!!!!!")
                # Break all treaties involving the eliminated player
                for treaty in list(self.diplomacy.get_player_treaties(defending_player.name)):
                    self.diplomacy.break_treaty(treaty)
                    print(f"Treaty broken due to player elimination: {treaty}")
                    
        return True

    def _attack_phase(self, player: Player):
        print(f"--- {player.name}'s Turn --- Phase: Attack ---")
        if self.use_visualization:
            self.visualization.draw_board(self.players, player, "Attack")
            self.visualization.pause(0.5)
            
        attack_count = 0
        max_attacks = 20  # Safety limit for very aggressive AIs
        
        # Get AI strategy for this player
        ai_strategy = self.ai_strategies.get(player.name)
        
        while attack_count < max_attacks:  # Loop for multiple attacks
            attack_count += 1
            
            # Use AI strategy to determine best attack targets
            best_attack = None
            
            if ai_strategy:
                # Get prioritized attack targets
                attack_targets = ai_strategy.get_attack_targets(
                    player.name, list(player.territories_owned)
                )
                
                # Filter out targets protected by treaties
                filtered_targets = []
                for from_terr_name, to_terr_name, armies_for_attack_wave in attack_targets:
                    from_terr_obj = self.game_board.get_territory(from_terr_name)
                    to_terr_obj = self.game_board.get_territory(to_terr_name)
                    
                    if from_terr_obj and to_terr_obj:
                        defending_player_name = to_terr_obj.owner
                        
                        # Skip if there's an alliance with the defending player
                        if self.diplomacy.has_active_alliance(player.name, defending_player_name):
                            continue
                            
                        # Skip if there's a territory treaty covering these territories
                        if self.diplomacy.has_territory_treaty(
                            player.name, from_terr_name,
                            defending_player_name, to_terr_name
                        ):
                            continue
                            
                        # If not protected by treaty, add to filtered targets
                        filtered_targets.append((from_terr_name, to_terr_name, armies_for_attack_wave))
                
                # Choose the best attack if any are available
                if filtered_targets:
                    from_terr_name, to_terr_name, armies_for_attack_wave = filtered_targets[0]
                    from_terr_obj = self.game_board.get_territory(from_terr_name)
                    to_terr_obj = self.game_board.get_territory(to_terr_name)
                    
                    if from_terr_obj and to_terr_obj and from_terr_obj.armies > 1:
                        best_attack = (from_terr_obj, to_terr_obj, armies_for_attack_wave)
            else:
                # Fallback to the old method if no AI strategy is available
                # Find attacks where attacker has significant advantage
                can_attack = False
                possible_attacks = []
                
                for terr_name in player.territories_owned:
                    terr_obj = self.game_board.get_territory(terr_name)
                    if terr_obj and terr_obj.armies > 1:
                        adj_territories = self.game_board.get_adjacent_territories(terr_name)
                        for adj_name in adj_territories:
                            adj_terr_obj = self.game_board.get_territory(adj_name)
                            if adj_terr_obj and adj_terr_obj.owner != player.name:
                                # Skip if protected by treaty
                                defending_player_name = adj_terr_obj.owner
                                
                                # Skip if there's an alliance with the defending player
                                if self.diplomacy.has_active_alliance(player.name, defending_player_name):
                                    continue
                                    
                                # Skip if there's a territory treaty covering these territories
                                if self.diplomacy.has_territory_treaty(
                                    player.name, terr_name,
                                    defending_player_name, adj_name
                                ):
                                    continue
                                
                                possible_attacks.append((terr_name, adj_name, terr_obj.armies - 1))
                                can_attack = True
                
                if can_attack and possible_attacks:
                    # Find best attack based on advantage ratio
                    best_advantage = 1.0
                    random.shuffle(possible_attacks)
                    
                    for from_terr_name, to_terr_name, available_attack_armies in possible_attacks:
                        from_terr_obj = self.game_board.get_territory(from_terr_name)
                        to_terr_obj = self.game_board.get_territory(to_terr_name)
                        
                        if from_terr_obj and to_terr_obj and to_terr_obj.armies > 0:
                            advantage_ratio = from_terr_obj.armies / to_terr_obj.armies
                            
                            if advantage_ratio > best_advantage:
                                best_advantage = advantage_ratio
                                best_attack = (from_terr_obj, to_terr_obj, min(available_attack_armies, 3))
                    
                    # If no good attacks found, consider opportunistic attacks
                    if not best_attack:
                        for from_terr_name, to_terr_name, available_attack_armies in possible_attacks:
                            from_terr_obj = self.game_board.get_territory(from_terr_name)
                            to_terr_obj = self.game_board.get_territory(to_terr_name)
                            
                            if from_terr_obj and to_terr_obj and from_terr_obj.armies > to_terr_obj.armies:
                                best_attack = (from_terr_obj, to_terr_obj, min(available_attack_armies, 3))
                                break
            
            # If no good attack found, end the attack phase
            if not best_attack:
                print(f"{player.name} evaluates options and chooses not to attack further this turn.")
                break
            
            # Execute the chosen attack
            attacking_territory, defending_territory, armies_for_attack_wave = best_attack
            defending_player_name = defending_territory.owner
            defending_player = next((p for p in self.players if p.name == defending_player_name), None)
            
            if not defending_player:
                print(f"Error: Could not find defending player object for {defending_player_name}")
                break
            
            # Get state before attack
            pre_attack_owner = defending_territory.owner
            
            # Resolve the attack
            attack_result = self._resolve_attack(player, defending_player, attacking_territory, defending_territory, armies_for_attack_wave)
            if not attack_result:
                print(f"{player.name} cannot attack {defending_player.name} due to diplomatic restrictions.")
                # Try another attack
                continue
            
            # Update visualization
            if self.use_visualization:
                self.visualization.draw_board(self.players, player, "Attack")
                self.visualization.pause(0.3)
            
            # Decide whether to continue attacking
            territory_captured = defending_territory.owner == player.name
            
            # Use AI strategy to decide whether to continue attacking
            should_continue = False
            
            if territory_captured:
                # After a conquest, more likely to continue
                should_continue = random.random() < 0.8
                if should_continue:
                    print(f"{player.name} is encouraged by the conquest and continues attacking!")
                else:
                    print(f"{player.name} decides to end the attack phase.")
                    break
            else:
                # After a failed attack, less likely to continue
                should_continue = random.random() < 0.5
                if should_continue:
                    print(f"{player.name} will try another attack despite the setback.")
                else:
                    print(f"{player.name} decides to end the attack phase.")
                    break
        
        # If we've reached the max number of attacks, print a message
        if attack_count >= max_attacks:
            print(f"{player.name} has reached the maximum number of attacks for this turn.")

    def _fortify_phase(self, player: Player):
        if self.use_visualization:
            self.visualization.draw_board(self.players, player, "Fortify")
            self.visualization.pause(0.5)
        
        print(f"--- {player.name}'s Turn ({player.color}) --- Phase: Fortify ---")
        if not player.territories_owned or len(player.territories_owned) <= 1:
            print(f"{player.name} has too few territories to fortify.")
            return
        
        # Use AI strategy to determine best fortification move
        ai_strategy = self.ai_strategies.get(player.name)
        best_move = None
        
        if ai_strategy:
            # Get the best fortification move
            best_move = ai_strategy.get_best_fortification_move(
                player.name, list(player.territories_owned)
            )
        else:
            # Fallback to the old method if no AI strategy is available
            # ...existing fortification logic...
            # Strategy: Find an owned territory with >1 army, and move some armies to an adjacent owned territory.
            # Prioritize moving from a territory with many armies to a weaker adjacent one, or towards a front.
            # Simple AI: Find any valid move and execute it.
            
            possible_fortifications = [] # List of (from_territory_obj, to_territory_obj, max_armies_to_move)

            for source_name in player.territories_owned:
                source_territory = self.game_board.get_territory(source_name)
                if source_territory and source_territory.armies > 1:
                    # Simple adjacent fortification for now:
                    q = [(source_territory, [source_territory.name])] # (current_territory, path_taken)
                    visited_for_path = {source_territory.name} # Territories visited in current BFS from source

                    # BFS to find all reachable owned territories from source_territory
                    reachable_owned_territories_from_source = []

                    head = 0
                    while head < len(q):
                        current_terr_obj, _ = q[head]
                        head += 1

                        for adj_name in self.game_board.get_adjacent_territories(current_terr_obj.name):
                            adj_terr_obj = self.game_board.get_territory(adj_name)
                            if adj_terr_obj and adj_terr_obj.owner == player.name and adj_name not in visited_for_path:
                                visited_for_path.add(adj_name)
                                # Add to reachable if it's not the source itself
                                if adj_name != source_name:
                                    reachable_owned_territories_from_source.append(adj_terr_obj)
                                # Continue BFS to find all connected territories
                                q.append((adj_terr_obj, [])) # Path not needed here, just reachability

                    for dest_territory in reachable_owned_territories_from_source:
                        # Can move source_territory.armies - 1
                        armies_available_to_move = source_territory.armies - 1
                        if armies_available_to_move > 0:
                            possible_fortifications.append((source_territory, dest_territory, armies_available_to_move))

            if possible_fortifications:
                # Sort by number of armies to move (which is based on source.armies -1)
                possible_fortifications.sort(key=lambda x: x[2], reverse=True) # Sort by armies_to_move desc
                
                # Pick the one that can move most armies, from a random selection if multiple have same max
                max_movable = possible_fortifications[0][2]
                top_options = [move for move in possible_fortifications if move[2] == max_movable]
                best_choice = random.choice(top_options)
                
                source, dest, armies_to_move = best_choice
                best_move = (source.name, dest.name, armies_to_move)
        
        # Execute the fortification move if one was found
        if best_move:
            source_name, dest_name, armies_to_move = best_move
            source = self.game_board.get_territory(source_name)
            dest = self.game_board.get_territory(dest_name)
            
            if source and dest and source.armies > armies_to_move:
                print(f"{player.name} chooses to fortify by moving {armies_to_move} armies from {source_name} to {dest_name}.")
                source.armies -= armies_to_move
                dest.armies += armies_to_move
                print(f"{source_name} now has {source.armies} armies. {dest_name} now has {dest.armies} armies.")
            else:
                print(f"Warning: Invalid fortification move from {source_name} to {dest_name}.")
        else:
            print(f"{player.name} chooses not to fortify (no beneficial move found by AI).")
        
        # Update visualization after fortification
        if self.use_visualization:
            self.visualization.draw_board(self.players, player, "Fortify Complete")
            self.visualization.pause(0.5)

    def play_turn(self):
        current_player = self.get_current_player()
        if current_player.is_eliminated():  # Check if player was eliminated before their turn starts
            print(f"{current_player.name} ({current_player.color}) is eliminated and skips their turn.")
            return False  # Game continues, but this player is out
            
        # Reset conquest flag at the beginning of the turn
        current_player.reset_conquest_flag()

        # Update diplomacy at the start of the turn
        expired_treaties = self.diplomacy.update_turn()
        if expired_treaties:
            for treaty in expired_treaties:
                player1, player2 = treaty.get_involved_players()
                print(f"Treaty between {player1} and {player2} has expired: {treaty}")
        
        # Diplomacy Phase - Added before Card Trading
        print(f"\n--- {current_player.name}'s Turn ({current_player.color}) --- Phase: Diplomacy ---")
        self._diplomacy_phase(current_player)
        
        # Card Trading Phase - Before Reinforcement
        card_bonus = 0
        if current_player.cards:
            print(f"\n--- {current_player.name}'s Turn ({current_player.color}) --- Phase: Card Trading ---")
            print(f"{current_player.name} has {len(current_player.cards)} cards: {current_player.cards}")
            
            # Handle card trading (mandatory if 5+ cards, optional otherwise)
            card_bonus = self._handle_card_trading(current_player)
            if card_bonus > 0:
                current_player.add_reinforcements(card_bonus)
                print(f"{current_player.name} received {card_bonus} reinforcements from card trading")

        # Reinforcement Phase
        print(f"\n--- {current_player.name}'s Turn ({current_player.color}) --- Phase: Reinforce ---")
        self._reinforcement_phase(current_player)
        
        # Check if player was eliminated
        if current_player.is_eliminated():
            print(f"{current_player.name} ({current_player.color}) was eliminated during the reinforcement phase.")
            return False  # Game continues, player is out

        # Attack Phase
        print(f"\n--- {current_player.name}'s Turn ({current_player.color}) --- Phase: Attack ---")
        self._attack_phase(current_player)

        # Award a Risk card if the player conquered at least one territory
        if current_player.conquered_territory_this_turn:
            card = self.draw_card()
            if card:
                current_player.add_card(card)
                print(f"{current_player.name} receives a Risk card for conquering a territory this turn: {card}")

        # Check for player elimination and card transfer after attack phase
        for other_player in self.players:
            if other_player != current_player and other_player.is_eliminated() and other_player.cards:
                # Transfer cards from eliminated player to the conquering player
                print(f"{current_player.name} receives {len(other_player.cards)} cards from eliminated player {other_player.name}")
                current_player.cards.extend(other_player.cards)
                other_player.cards = []
                
                # Check for mandatory card trading if player now has 5+ cards
                if len(current_player.cards) >= 5:
                    print(f"{current_player.name} must trade cards after eliminating {other_player.name} (now has {len(current_player.cards)} cards)")
                    while len(current_player.cards) >= 5:
                        card_bonus = self._handle_card_trading(current_player)
                        if card_bonus > 0:
                            # In official Risk, these armies can be placed immediately
                            # For simplicity, we'll add them to the player's next turn
                            current_player.add_reinforcements(card_bonus)
                            print(f"{current_player.name} received {card_bonus} reinforcements from mandatory card trading after elimination")

        if self.check_win_condition():  # Check win condition after attack
            return True
        
        # Check if player was eliminated during their attack phase (e.g. lost all territories)
        if current_player.is_eliminated():
            print(f"{current_player.name} ({current_player.color}) was eliminated during their attack phase.")
            return False  # Game continues, player is out

        # Fortify Phase
        print(f"\n--- {current_player.name}'s Turn ({current_player.color}) --- Phase: Fortify ---")
        self._fortify_phase(current_player)

        # Final win condition check for the turn
        if self.check_win_condition():
            return True
            
        return False  # Game continues

    def check_win_condition(self) -> bool: # Removed player argument
        active_players = [p for p in self.players if not p.is_eliminated()]
        
        if len(active_players) == 1:
            winner = active_players[0]
            print(f"\n!!!!!!!!!! {winner.name} HAS WON THE GAME! Only one player remains. !!!!!!!!!!")
            return True
        
        # Original condition: one player owns all territories (still valid)
        for player in active_players:
            if player.get_controlled_territories_count() == len(self.game_board.territories):
                print(f"\n!!!!!!!!!! {player.name} HAS CONQUERED THE WORLD! !!!!!!!!!!")
                return True
        return False

    def start_main_game_loop(self):
        print("\n=================================")
        print("   STARTING MAIN GAME LOOP     ")
        print("=================================")
        
        # Display initial board before first turn
        print("\n--- Board State Before First Turn ---")
        self.game_board.display_board_state()
        if self.use_visualization:
            self.visualization.draw_board(self.players, None, "Game Start")
            self.visualization.pause(1)  # Pause for 1 second to view initial board

        turn_count = 0
        max_turns = 200 # To prevent infinite loops during development

        try:
            while turn_count < max_turns and (not self.use_visualization or self.visualization.running):
                turn_count += 1
                current_player_for_turn = self.get_current_player()
                print(f"\n=== Turn {turn_count} - Player: {current_player_for_turn.name} ({current_player_for_turn.color}) ===")
                
                game_over = self.play_turn()
                if game_over:
                    print(f"\n--- Game Over After {current_player_for_turn.name}'s Turn ---")
                    if self.use_visualization:
                        winner = [p for p in self.players if not p.is_eliminated()][0]
                        self.visualization.draw_board(self.players, winner, "WINNER!")
                        self.visualization.pause(5)  # Show the final state for 5 seconds
                    break
                
                print(f"\n--- Board State After {current_player_for_turn.name}'s Turn ({current_player_for_turn.color}) ---")
                self.game_board.display_board_state() # Display board after each player's turn
                
                self.next_turn()
            
            if turn_count == max_turns:
                print(f"\nGame ended due to reaching max turns ({max_turns}).")
            
            print("\n--- Final Board State ---")
            self.game_board.display_board_state()
            for p in self.players:
                print(f"{p.name}: {p.get_controlled_territories_count()} territories")
                
        finally:
            # Make sure to close the visualization if it's open
            if self.use_visualization and self.visualization:
                self.visualization.close()

    def draw_board(self):
        """Draw the current game state using pygame visualization if available"""
        if self.use_visualization:
            player = self.players[self.current_player_index]
            phase = self.game_phase
            # Pass the diplomacy manager to the visualization
            self.visualization.draw_board(self.players, player, phase, self.diplomacy)
            return True
        return False

if __name__ == '__main__':
    # Example Usage
    player_configs = [("Player 1", "Red"), ("Player 2", "Blue"), ("Player 3", "Green")]
    game = GameManager(player_configs)
    # At this point, setup is done, players would take turns placing remaining armies.
    # Then the main game loop would begin.
    current_player = game.get_current_player()
    print(f"\n{current_player.name} should now place their remaining {current_player.reinforcements} armies.")
