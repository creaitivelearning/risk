import random
import math
from typing import Dict, List, Tuple, Set, Optional

class AIStrategy:
    """Base class for AI strategies with advanced decision-making capabilities"""
    
    def __init__(self, player_name: str, game_board):
        self.player_name = player_name
        self.game_board = game_board
        self.territory_values = {}  # Strategic value of each territory
        self.continent_priorities = {}  # Priority of each continent
        self.target_continent = None  # Current continent being targeted for conquest
        self.calculate_strategic_values()
    
    def calculate_strategic_values(self):
        """Calculate strategic values for territories and continents based on the current board state"""
        # Calculate continent priorities based on bonus and ease of defense
        for continent_name, continent in self.game_board.continents.items():
            # Calculate how many territories are needed to control the continent
            total_territories = len(continent.territories)
            territories_owned = sum(1 for terr_name in continent.territories 
                                   if self.game_board.get_territory(terr_name).owner == self.player_name)
            
            # Calculate number of entry points (borders with other continents)
            entry_points = self.count_continent_entry_points(continent_name)
            
            # Value = (bonus / entry_points) * (territories_owned / total_territories)^2
            # This favors continents with higher bonuses, fewer entry points, and where we already own territories
            if entry_points > 0:
                continent_value = (continent.bonus_armies / entry_points) * ((territories_owned / total_territories) ** 2 + 0.1)
            else:
                continent_value = 0  # Should not happen, but prevent division by zero
                
            # Adjust for continent size - smaller continents are easier to hold
            size_factor = 1.0 + (6 - total_territories) * 0.1  # Bonus for smaller continents
            continent_value *= size_factor
            
            self.continent_priorities[continent_name] = continent_value
        
        # Calculate territory strategic values
        for territory_name, territory in self.game_board.territories.items():
            # Base value calculation
            base_value = 1.0
            
            # Value increases for territories in valuable continents
            continent = self.get_continent_for_territory(territory_name)
            if continent:
                # Higher value if territory is in a high-priority continent
                continent_factor = self.continent_priorities.get(continent, 1.0) * 1.5
                base_value *= continent_factor
            
            # Value increases for territories that are continent entry/exit points
            if self.is_continent_gateway(territory_name):
                base_value *= 1.5  # Gateway territories are 50% more valuable
            
            # Value increases for territories with many connections (strategic positions)
            adj_count = len(self.game_board.adjacencies.get(territory_name, []))
            connectivity_factor = 1.0 + (adj_count - 3) * 0.1  # Base on average connectivity of ~3
            base_value *= max(0.8, connectivity_factor)  # Min factor of 0.8
            
            self.territory_values[territory_name] = base_value
    
    def count_continent_entry_points(self, continent_name: str) -> int:
        """Count how many territories in a continent border territories outside the continent"""
        continent = self.game_board.continents.get(continent_name)
        if not continent:
            return 0
            
        entry_points = 0
        for territory_name in continent.territories:
            adjacent_territories = self.game_board.adjacencies.get(territory_name, [])
            for adj_name in adjacent_territories:
                # Check if adjacent territory is outside this continent
                adj_continent = self.get_continent_for_territory(adj_name)
                if adj_continent != continent_name:
                    entry_points += 1
                    break  # Count each territory as at most one entry point
                    
        return max(1, entry_points)  # Minimum of 1 to avoid division by zero
    
    def is_continent_gateway(self, territory_name: str) -> bool:
        """Determine if a territory is a gateway to/from a continent"""
        territory_continent = self.get_continent_for_territory(territory_name)
        if not territory_continent:
            return False
            
        adjacent_territories = self.game_board.adjacencies.get(territory_name, [])
        for adj_name in adjacent_territories:
            adj_continent = self.get_continent_for_territory(adj_name)
            if adj_continent != territory_continent:
                return True
                
        return False
    
    def get_continent_for_territory(self, territory_name: str) -> Optional[str]:
        """Get the continent a territory belongs to"""
        for continent_name, continent in self.game_board.continents.items():
            if territory_name in continent.territories:
                return continent_name
        return None
    
    def get_player_continent_control(self, player_name: str) -> Dict[str, float]:
        """Calculate how much of each continent a player controls (0.0-1.0)"""
        control = {}
        for continent_name, continent in self.game_board.continents.items():
            total_territories = len(continent.territories)
            if total_territories == 0:
                control[continent_name] = 0
                continue
                
            owned_territories = sum(1 for terr_name in continent.territories
                                   if self.game_board.get_territory(terr_name).owner == player_name)
            control[continent_name] = owned_territories / total_territories
        return control
    
    def choose_target_continent(self, player_name: str):
        """Choose the best continent to focus on conquering"""
        continent_control = self.get_player_continent_control(player_name)
        weighted_priorities = {}
        
        for continent_name, priority in self.continent_priorities.items():
            # Weight by how close we are to controlling it
            # Higher weight for continents we already partially control
            control_level = continent_control.get(continent_name, 0)
            
            # Exponential scaling - strongly prefer continents we already partially control
            # but with a small random factor to occasionally try new continents
            weighted_priority = priority * ((control_level + 0.1) ** 2) * (0.8 + 0.4 * random.random())
            weighted_priorities[continent_name] = weighted_priority
        
        # Select continent with highest weighted priority
        if weighted_priorities:
            target_continent = max(weighted_priorities.items(), key=lambda x: x[1])[0]
            return target_continent
        return None
    
    def get_continent_completion_territories(self, continent_name: str, player_name: str) -> List[str]:
        """Get list of territories needed to complete a continent"""
        continent = self.game_board.continents.get(continent_name)
        if not continent:
            return []
            
        needed_territories = []
        for territory_name in continent.territories:
            territory = self.game_board.get_territory(territory_name)
            if territory.owner != player_name:
                needed_territories.append(territory_name)
                
        return needed_territories
    
    def get_best_reinforcement_territories(self, player_name: str, owned_territories: List[str]) -> List[str]:
        """Get prioritized list of territories for reinforcement"""
        # Update strategic values based on current game state
        self.calculate_strategic_values()
        
        # Choose a target continent if we don't have one or need to reconsider
        self.target_continent = self.choose_target_continent(player_name)
        
        # Identify front-line territories (border with enemy territory)
        front_line_territories = []
        for terr_name in owned_territories:
            if self.is_front_line_territory(terr_name, player_name):
                front_line_territories.append(terr_name)
                
        # If we have no front line territories, return any owned territories
        if not front_line_territories:
            return list(owned_territories)
        
        # Calculate prioritized scores for each front-line territory
        territory_scores = {}
        for terr_name in front_line_territories:
            territory = self.game_board.get_territory(terr_name)
            if not territory:
                continue
                
            # Base score is strategic value
            score = self.territory_values.get(terr_name, 1.0)
            
            # Bonus for territories with few armies (need defense)
            army_factor = 2.0 / (territory.armies + 1)
            score *= army_factor
            
            # Bonus for territories in target continent
            if self.target_continent and self.get_continent_for_territory(terr_name) == self.target_continent:
                score *= 2.0
                
            # Bonus for territories that could complete a continent
            continent = self.get_continent_for_territory(terr_name)
            if continent:
                continent_obj = self.game_board.continents.get(continent)
                if continent_obj:
                    needed_territories = self.get_continent_completion_territories(continent, player_name)
                    # If we're close to completing this continent
                    if 1 <= len(needed_territories) <= 3:
                        # Check if this territory borders enemies in the continent
                        borders_target = any(
                            adj_name in needed_territories and
                            self.game_board.get_territory(adj_name).owner != player_name
                            for adj_name in self.game_board.adjacencies.get(terr_name, [])
                        )
                        if borders_target:
                            score *= 1.5
            
            # Bonus for territories that border vulnerable enemy territories
            vulnerability_bonus = self.calculate_attack_opportunity_score(terr_name, player_name)
            score *= (1.0 + vulnerability_bonus)
            
            territory_scores[terr_name] = score
        
        # Sort territories by score
        sorted_territories = sorted(territory_scores.items(), key=lambda x: x[1], reverse=True)
        return [terr[0] for terr in sorted_territories]
    
    def is_front_line_territory(self, territory_name: str, player_name: str) -> bool:
        """Check if a territory borders enemy territory"""
        adjacent_territories = self.game_board.adjacencies.get(territory_name, [])
        for adj_name in adjacent_territories:
            adj_terr = self.game_board.get_territory(adj_name)
            if adj_terr and adj_terr.owner != player_name:
                return True
        return False
    
    def calculate_attack_opportunity_score(self, from_territory: str, player_name: str) -> float:
        """Calculate an opportunity score for attacks from this territory"""
        territory_obj = self.game_board.get_territory(from_territory)
        if not territory_obj or territory_obj.owner != player_name or territory_obj.armies <= 1:
            return 0.0
            
        opportunity_score = 0.0
        adjacent_territories = self.game_board.adjacencies.get(from_territory, [])
        
        for adj_name in adjacent_territories:
            adj_terr = self.game_board.get_territory(adj_name)
            if not adj_terr or adj_terr.owner == player_name:
                continue
                
            # Calculate advantage ratio
            if adj_terr.armies > 0:  # Avoid division by zero
                advantage = territory_obj.armies / adj_terr.armies
            else:
                advantage = territory_obj.armies
                
            # Territory is vulnerable if we have significant advantage
            if advantage >= 1.5:
                # Calculate value of capturing this territory
                capture_value = self.territory_values.get(adj_name, 1.0)
                
                # Extra value if it's in our target continent
                if self.target_continent and self.get_continent_for_territory(adj_name) == self.target_continent:
                    capture_value *= 2.0
                    
                # Extra value if it would complete a continent
                continent = self.get_continent_for_territory(adj_name)
                if continent:
                    needed_territories = self.get_continent_completion_territories(continent, player_name)
                    if len(needed_territories) == 1 and needed_territories[0] == adj_name:
                        capture_value *= 3.0
                
                # Factor in both advantage and capture value
                opportunity_score += (advantage - 1.0) * capture_value
        
        return min(3.0, opportunity_score)  # Cap at 3.0 to prevent extreme values
    
    def get_attack_targets(self, player_name: str, owned_territories: List[str]) -> List[Tuple[str, str, int]]:
        """Get prioritized list of attack targets as (from_territory, to_territory, attack_armies)"""
        attack_opportunities = []
        
        for from_terr_name in owned_territories:
            from_terr = self.game_board.get_territory(from_terr_name)
            if not from_terr or from_terr.armies <= 1:
                continue
                
            adjacent_territories = self.game_board.adjacencies.get(from_terr_name, [])
            for to_terr_name in adjacent_territories:
                to_terr = self.game_board.get_territory(to_terr_name)
                if not to_terr or to_terr.owner == player_name:
                    continue
                    
                # Calculate attack score
                attack_score = self.calculate_attack_score(from_terr_name, to_terr_name, player_name)
                
                # Calculate optimal attack armies (between 1 and min(3, from_terr.armies - 1))
                available_attack_armies = min(3, from_terr.armies - 1)
                if available_attack_armies > 0:
                    attack_opportunities.append((from_terr_name, to_terr_name, available_attack_armies, attack_score))
        
        # Sort by attack score
        attack_opportunities.sort(key=lambda x: x[3], reverse=True)
        return [(a[0], a[1], a[2]) for a in attack_opportunities]
    
    def calculate_attack_score(self, from_territory: str, to_territory: str, player_name: str) -> float:
        """Calculate a score for an attack from one territory to another"""
        from_terr = self.game_board.get_territory(from_territory)
        to_terr = self.game_board.get_territory(to_territory)
        
        if not from_terr or not to_terr or from_terr.owner != player_name or to_terr.owner == player_name:
            return 0.0
            
        # Base score from win probability calculation
        if to_terr.armies > 0:  # Prevent division by zero
            advantage_ratio = from_terr.armies / to_terr.armies
        else:
            advantage_ratio = from_terr.armies
            
        # Attack win probability - simplified formula based on empirical Risk odds
        # This is a simplified curve where higher advantage = higher win probability
        win_probability = min(0.9, max(0.1, 0.5 + (advantage_ratio - 1) * 0.2))
        
        # Strategic value of capturing this territory
        strategic_value = self.territory_values.get(to_territory, 1.0)
        
        # Bonuses for strategic situations
        
        # Bonus if territory is in target continent
        if self.target_continent and self.get_continent_for_territory(to_territory) == self.target_continent:
            strategic_value *= 2.0
        
        # Huge bonus if this would complete a continent
        continent = self.get_continent_for_territory(to_territory)
        if continent:
            needed_territories = self.get_continent_completion_territories(continent, player_name)
            if len(needed_territories) == 1 and needed_territories[0] == to_territory:
                strategic_value *= 3.0
        
        # Bonus if the territory is weakly defended
        if to_terr.armies <= 2:
            strategic_value *= 1.5
            
        # Final score combines win probability with strategic value
        return win_probability * strategic_value
    
    def get_best_fortification_move(self, player_name: str, owned_territories: List[str]) -> Optional[Tuple[str, str, int]]:
        """Find the best fortification move as (from_territory, to_territory, armies_to_move)"""
        # Build a graph of connected owned territories
        territory_graph = {}
        for terr_name in owned_territories:
            territory_graph[terr_name] = []
            for adj_name in self.game_board.adjacencies.get(terr_name, []):
                if adj_name in owned_territories:
                    territory_graph[terr_name].append(adj_name)
        
        # Classify territories: front-line vs. interior
        front_line_territories = []
        interior_territories = []
        
        for terr_name in owned_territories:
            if self.is_front_line_territory(terr_name, player_name):
                front_line_territories.append(terr_name)
            else:
                interior_territories.append(terr_name)
        
        # Best fortification moves come from interior to front-line
        best_fortifications = []
        
        # For each interior territory with excess armies, find accessible front-line territories
        for from_terr_name in interior_territories:
            from_terr = self.game_board.get_territory(from_terr_name)
            if not from_terr or from_terr.armies <= 1:
                continue
                
            # Find all accessible front-line territories using BFS
            accessible_front_lines = []
            visited = {from_terr_name}
            queue = [(from_terr_name, [])]  # (territory, path)
            
            while queue:
                current, path = queue.pop(0)
                
                if current != from_terr_name and current in front_line_territories:
                    accessible_front_lines.append((current, path + [current]))
                    continue  # No need to explore beyond a front-line territory
                
                for neighbor in territory_graph.get(current, []):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, path + [neighbor]))
            
            # For each accessible front-line, calculate fortification score
            for to_terr_name, path in accessible_front_lines:
                if len(path) < 1:  # Need at least one step
                    continue
                    
                to_terr = self.game_board.get_territory(to_terr_name)
                if not to_terr:
                    continue
                    
                # Calculate fortification score
                score = self.calculate_fortification_score(from_terr_name, to_terr_name, player_name)
                
                # Calculate armies to move (leave at least 1 behind)
                armies_to_move = max(1, from_terr.armies - 1)
                
                # Add to potential fortifications
                best_fortifications.append((from_terr_name, to_terr_name, armies_to_move, score))
        
        # If interior-to-front moves aren't available, look for front-to-front moves
        if not best_fortifications:
            for from_terr_name in front_line_territories:
                from_terr = self.game_board.get_territory(from_terr_name)
                if not from_terr or from_terr.armies <= 1:
                    continue
                    
                # Only consider front-line territories with low threat
                from_threat = self.calculate_territory_threat(from_terr_name, player_name)
                if from_threat > 0.5:  # Skip high-threat territories as sources
                    continue
                    
                # Find directly adjacent front-line territories
                for to_terr_name in territory_graph.get(from_terr_name, []):
                    if to_terr_name in front_line_territories:
                        to_terr = self.game_board.get_territory(to_terr_name)
                        if not to_terr:
                            continue
                            
                        # Calculate fortification score
                        score = self.calculate_fortification_score(from_terr_name, to_terr_name, player_name)
                        
                        # Only move armies if destination threat is higher
                        to_threat = self.calculate_territory_threat(to_terr_name, player_name)
                        if to_threat > from_threat:
                            # Calculate armies to move (leave at least 1 behind)
                            armies_to_move = max(1, from_terr.armies - 1)
                            best_fortifications.append((from_terr_name, to_terr_name, armies_to_move, score))
        
        # Sort by score and return best move
        best_fortifications.sort(key=lambda x: x[3], reverse=True)
        if best_fortifications:
            return best_fortifications[0][:3]  # Return (from, to, armies)
        return None
    
    def calculate_fortification_score(self, from_territory: str, to_territory: str, player_name: str) -> float:
        """Calculate a score for fortifying from one territory to another"""
        to_terr = self.game_board.get_territory(to_territory)
        if not to_terr or to_terr.owner != player_name:
            return 0.0
            
        # Base score: strategic value of the destination
        score = self.territory_values.get(to_territory, 1.0)
        
        # Increase score based on threat level to the destination
        threat = self.calculate_territory_threat(to_territory, player_name)
        score *= (1.0 + threat * 2.0)  # Higher threat means higher fortification priority
        
        # Bonus if the territory is in our target continent
        if self.target_continent and self.get_continent_for_territory(to_territory) == self.target_continent:
            score *= 1.5
            
        # Bonus if the territory contributes to continent control
        continent = self.get_continent_for_territory(to_territory)
        if continent:
            continent_control = self.get_player_continent_control(player_name).get(continent, 0)
            if continent_control > 0.5:  # If we control more than half the continent
                score *= 1.5
        
        return score
    
    def calculate_territory_threat(self, territory_name: str, player_name: str) -> float:
        """Calculate the threat level to a territory (0.0-1.0)"""
        territory = self.game_board.get_territory(territory_name)
        if not territory or territory.owner != player_name:
            return 0.0
            
        # Count enemy armies in adjacent territories
        adjacent_territories = self.game_board.adjacencies.get(territory_name, [])
        enemy_armies = 0
        for adj_name in adjacent_territories:
            adj_terr = self.game_board.get_territory(adj_name)
            if adj_terr and adj_terr.owner != player_name:
                enemy_armies += adj_terr.armies
        
        # Calculate threat ratio (enemy armies vs our armies)
        if territory.armies > 0:  # Prevent division by zero
            threat_ratio = enemy_armies / territory.armies
        else:
            threat_ratio = enemy_armies
            
        # Normalize to 0.0-1.0 range
        normalized_threat = min(1.0, threat_ratio / 3.0)
        return normalized_threat


class AggressiveStrategy(AIStrategy):
    """Aggressive AI strategy that prioritizes expansion and attack"""
    
    def calculate_strategic_values(self):
        super().calculate_strategic_values()
        # Increase value of territories with many connections (attack opportunities)
        for territory_name in self.territory_values:
            adj_count = len(self.game_board.adjacencies.get(territory_name, []))
            self.territory_values[territory_name] *= (1.0 + (adj_count - 3) * 0.15)
    
    def calculate_attack_score(self, from_territory: str, to_territory: str, player_name: str) -> float:
        # Start with base score from parent class
        score = super().calculate_attack_score(from_territory, to_territory, player_name)
        
        # Aggressive AI values attacks more highly
        score *= 1.3
        
        # Aggressive AI particularly favors attacks from strong positions
        from_terr = self.game_board.get_territory(from_territory)
        to_terr = self.game_board.get_territory(to_territory)
        
        if from_terr and to_terr:
            if from_terr.armies > to_terr.armies * 2:
                score *= 1.5  # Strongly favor overwhelming attacks
        
        return score


class DefensiveStrategy(AIStrategy):
    """Defensive AI strategy that prioritizes holding continents and fortifying borders"""
    
    def calculate_strategic_values(self):
        super().calculate_strategic_values()
        # Increase value of territories that are gateways (need to be defended)
        for territory_name in self.territory_values:
            if self.is_continent_gateway(territory_name):
                self.territory_values[territory_name] *= 1.5
    
    def get_best_reinforcement_territories(self, player_name: str, owned_territories: List[str]) -> List[str]:
        territories = super().get_best_reinforcement_territories(player_name, owned_territories)
        
        # Defensive AI prioritizes territories in continents it mostly controls
        continent_control = self.get_player_continent_control(player_name)
        
        # Reorder based on continent control
        def defensive_priority(territory_name):
            continent = self.get_continent_for_territory(territory_name)
            if continent:
                control_level = continent_control.get(continent, 0)
                # Strongly prioritize continents we mostly control
                if control_level > 0.6:
                    return control_level * 2.0
            return 0.0
        
        # Sort by defensive priority (high to low), then by original order
        territories.sort(key=lambda t: defensive_priority(t), reverse=True)
        
        return territories
    
    def calculate_attack_score(self, from_territory: str, to_territory: str, player_name: str) -> float:
        # Start with base score from parent class
        score = super().calculate_attack_score(from_territory, to_territory, player_name)
        
        # Defensive AI values attacks less highly, except for completing continents
        score *= 0.7
        
        # Check if this attack would complete a continent
        continent = self.get_continent_for_territory(to_territory)
        if continent:
            needed_territories = self.get_continent_completion_territories(continent, player_name)
            if len(needed_territories) == 1 and needed_territories[0] == to_territory:
                score *= 3.0  # Defensive AI really wants to complete continents
        
        return score


class BalancedStrategy(AIStrategy):
    """Balanced AI strategy with a mix of aggressive and defensive traits"""
    
    def __init__(self, player_name: str, game_board):
        super().__init__(player_name, game_board)
        # Randomly lean slightly more aggressive or defensive each game
        self.aggression_factor = random.uniform(0.9, 1.1)
    
    def calculate_attack_score(self, from_territory: str, to_territory: str, player_name: str) -> float:
        # Start with base score from parent class
        score = super().calculate_attack_score(from_territory, to_territory, player_name)
        
        # Apply the aggression factor
        score *= self.aggression_factor
        
        # Balanced AI particularly values breaking up opponent continents
        to_continent = self.get_continent_for_territory(to_territory)
        if to_continent:
            # Check who controls this continent
            for other_player in self._get_other_players(player_name):
                other_control = self.get_player_continent_control(other_player).get(to_continent, 0)
                if other_control > 0.6:  # If opponent controls most of the continent
                    score *= 1.5  # Prioritize breaking it up
                    break
        
        return score
    
    def _get_other_players(self, player_name: str) -> List[str]:
        """Get list of other players in the game"""
        # Note: This is a simplified version, the actual implementation
        # would need to access the full list of players from the game state
        other_players = []
        for territory in self.game_board.territories.values():
            if territory.owner and territory.owner != player_name and territory.owner not in other_players:
                other_players.append(territory.owner)
        return other_players


class OpportunisticStrategy(AIStrategy):
    """Opportunistic AI that targets the weakest opponents and best opportunities"""
    
    def calculate_attack_score(self, from_territory: str, to_territory: str, player_name: str) -> float:
        # Start with base score from parent class
        score = super().calculate_attack_score(from_territory, to_territory, player_name)
        
        # Get territory owner
        to_terr = self.game_board.get_territory(to_territory)
        if not to_terr or not to_terr.owner:
            return score
            
        # Check if the target player is weak (has few territories)
        target_player = to_terr.owner
        target_strength = self._get_player_strength(target_player)
        player_strength = self._get_player_strength(player_name)
        
        # Favor attacking weaker players
        if target_strength < player_strength * 0.7:
            score *= 1.5
            
        # Check if territory is poorly defended relative to surrounding territories
        from_terr = self.game_board.get_territory(from_territory)
        if from_terr and to_terr:
            if from_terr.armies > to_terr.armies * 2:
                score *= 1.3  # Opportunistic AI loves easy picks
        
        return score
    
    def _get_player_strength(self, player_name: str) -> float:
        """Calculate a player's overall strength"""
        territory_count = 0
        army_count = 0
        
        for territory in self.game_board.territories.values():
            if territory.owner == player_name:
                territory_count += 1
                army_count += territory.armies
        
        return territory_count * 2 + army_count


class NapoleonStrategy(AggressiveStrategy):
    """Napoleon Bonaparte: Master of aggressive tactics with focus on artillery and rapid maneuvers"""
    
    def __init__(self, player_name: str, game_board):
        super().__init__(player_name, game_board)
        print(f"{player_name} employs the aggressive tactics of Napoleon Bonaparte!")
        # Napoleon favored concentration of force and rapid attacks
        self.aggression_bonus = 1.4
        
    def calculate_strategic_values(self):
        super().calculate_strategic_values()
        # Napoleon valued central territories (for rapid movement in any direction)
        # Increase value for territories with many connections
        for territory_name in self.territory_values:
            adj_count = len(self.game_board.adjacencies.get(territory_name, []))
            if adj_count > 4:  # Heavily value well-connected territories
                self.territory_values[territory_name] *= 1.5
    
    def calculate_attack_score(self, from_territory: str, to_territory: str, player_name: str) -> float:
        # Napoleon was known for overwhelming force
        score = super().calculate_attack_score(from_territory, to_territory, player_name)
        score *= self.aggression_bonus
        
        # Napoleon focused on breaking enemy strong points
        to_terr = self.game_board.get_territory(to_territory)
        if to_terr and to_terr.armies > 3:  # Target enemy concentrations
            score *= 1.2
            
        return score
    
    def get_best_reinforcement_territories(self, player_name: str, owned_territories: List[str]) -> List[str]:
        # Napoleon prioritized concentration of force
        territories = super().get_best_reinforcement_territories(player_name, owned_territories)
        
        # Find territories with the most adjacent enemy territories
        def count_adjacent_enemies(terr_name):
            adjacent_territories = self.game_board.adjacencies.get(terr_name, [])
            enemy_count = 0
            for adj_name in adjacent_territories:
                adj_terr = self.game_board.get_territory(adj_name)
                if adj_terr and adj_terr.owner != player_name:
                    enemy_count += 1
            return enemy_count
        
        # Prioritize territories with many adjacent enemies
        territories.sort(key=count_adjacent_enemies, reverse=True)
        return territories


class GenghisKhanStrategy(OpportunisticStrategy):
    """Genghis Khan: Master of rapid conquest and overwhelming force"""
    
    def __init__(self, player_name: str, game_board):
        super().__init__(player_name, game_board)
        print(f"{player_name} employs the swift conquest tactics of Genghis Khan!")
        
    def calculate_strategic_values(self):
        super().calculate_strategic_values()
        # Genghis valued mobility - territories with many connections
        for territory_name in self.territory_values:
            adj_count = len(self.game_board.adjacencies.get(territory_name, []))
            self.territory_values[territory_name] *= (1.0 + (adj_count / 10.0))
    
    def calculate_attack_score(self, from_territory: str, to_territory: str, player_name: str) -> float:
        # Genghis Khan was known for rapid expansion
        score = super().calculate_attack_score(from_territory, to_territory, player_name)
        
        # Strong preference for attacking weaker territories
        from_terr = self.game_board.get_territory(from_territory)
        to_terr = self.game_board.get_territory(to_territory)
        
        if from_terr and to_terr and to_terr.armies > 0:
            advantage = from_terr.armies / to_terr.armies
            if advantage > 2.0:  # Heavily favor overwhelming advantage
                score *= 1.7
        
        return score
    
    def get_best_fortification_move(self, player_name: str, owned_territories: List[str]) -> Optional[Tuple[str, str, int]]:
        # Genghis Khan would prioritize fortifying frontline territories for further expansion
        best_move = super().get_best_fortification_move(player_name, owned_territories)
        
        # Additional mobility check - prefer fortifying territories with many connections
        if not best_move:
            return None
            
        source_name, dest_name, armies_to_move = best_move
        dest_terr = self.game_board.get_territory(dest_name)
        
        if dest_terr:
            # Check if this territory has many connections
            adj_count = len(self.game_board.adjacencies.get(dest_name, []))
            if adj_count < 3:  # Not many connections, seek a better territory
                # Find a better-connected territory if possible
                for terr_name in owned_territories:
                    if self.is_front_line_territory(terr_name, player_name):
                        new_adj_count = len(self.game_board.adjacencies.get(terr_name, []))
                        if new_adj_count > adj_count:
                            # Found a better-connected territory
                            new_terr = self.game_board.get_territory(terr_name)
                            if new_terr and source_name != terr_name:
                                return (source_name, terr_name, armies_to_move)
        
        return best_move


class AlexanderStrategy(AggressiveStrategy):
    """Alexander the Great: Bold conqueror focused on rapid expansion"""
    
    def __init__(self, player_name: str, game_board):
        super().__init__(player_name, game_board)
        print(f"{player_name} channels the bold conquests of Alexander the Great!")
        # Alexander was known for personal leadership in battle
        self.bold_attack_threshold = 0.4  # Lower threshold for attacks
        
    def calculate_strategic_values(self):
        super().calculate_strategic_values()
        # Alexander valued capturing key territories and capitals
        # For simplicity, we'll treat higher-value territories as "capitals"
        top_territories = sorted(self.territory_values.items(), key=lambda x: x[1], reverse=True)[:5]
        for terr_name, _ in top_territories:
            self.territory_values[terr_name] *= 1.8  # Major bonus for "capitals"
    
    def calculate_attack_score(self, from_territory: str, to_territory: str, player_name: str) -> float:
        # Alexander was known for bold, decisive attacks
        score = super().calculate_attack_score(from_territory, to_territory, player_name)
        
        # Alexander would continue his momentum after a victory
        ongoing_conquest = False
        for adj_name in self.game_board.adjacencies.get(to_territory, []):
            adj_terr = self.game_board.get_territory(adj_name)
            if adj_terr and adj_terr.owner == player_name:
                # There's already an adjacent territory we own - part of ongoing conquest
                ongoing_conquest = True
                break
        
        if ongoing_conquest:
            score *= 1.4  # Bonus for continuing conquest in same region
            
        return score
    
    def get_best_reinforcement_territories(self, player_name: str, owned_territories: List[str]) -> List[str]:
        territories = super().get_best_reinforcement_territories(player_name, owned_territories)
        
        # Alexander focused forces at his front lines rather than defending
        front_line_territories = [t for t in territories if self.is_front_line_territory(t, player_name)]
        if front_line_territories:
            return front_line_territories
        return territories


class SunTzuStrategy(BalancedStrategy):
    """Sun Tzu: Master of deception, positioning and strategic warfare"""
    
    def __init__(self, player_name: str, game_board):
        super().__init__(player_name, game_board)
        print(f"{player_name} employs the ancient wisdom of Sun Tzu!")
        # Sun Tzu valued knowledge of the battlefield
        self.analyzed_territories = {}
        
    def calculate_strategic_values(self):
        super().calculate_strategic_values()
        # Sun Tzu valued controlling key terrain
        for territory_name in self.territory_values:
            # Value territories that control access to others
            adj_count = len(self.game_board.adjacencies.get(territory_name, []))
            gateway_bonus = 1.0
            if self.is_continent_gateway(territory_name):
                gateway_bonus = 1.6  # Significant bonus for controlling gateways
            self.territory_values[territory_name] *= gateway_bonus * (1 + (adj_count - 3) * 0.1)
    
    def calculate_attack_score(self, from_territory: str, to_territory: str, player_name: str) -> float:
        # Sun Tzu focused on attacking when victory was certain
        score = super().calculate_attack_score(from_territory, to_territory, player_name)
        
        from_terr = self.game_board.get_territory(from_territory)
        to_terr = self.game_board.get_territory(to_territory)
        
        if from_terr and to_terr and to_terr.armies > 0:
            # Sun Tzu cautious about attacking unless advantage is clear
            advantage = from_terr.armies / to_terr.armies
            if advantage < 1.5:  # Reduce score for battles without clear advantage
                score *= 0.7
            elif advantage > 2.5:  # Increase score for battles with overwhelming advantage
                score *= 1.5
            
        # Sun Tzu valued strategic position over brute force
        if self.is_continent_gateway(to_territory):
            score *= 1.8  # Heavy bonus for attacking gateway territories
            
        return score
    
    def get_best_fortification_move(self, player_name: str, owned_territories: List[str]) -> Optional[Tuple[str, str, int]]:
        # Sun Tzu valued positioning troops optimally
        best_move = super().get_best_fortification_move(player_name, owned_territories)
        
        # Additional analysis to fortify gateway territories
        gateway_territories = [t for t in owned_territories if self.is_continent_gateway(t) and 
                               self.is_front_line_territory(t, player_name)]
        
        if gateway_territories and best_move:
            source_name, dest_name, armies_to_move = best_move
            
            # If destination isn't a gateway but we have some, prefer fortifying gateways
            if dest_name not in gateway_territories:
                # Find gateway territories that need reinforcement
                for gateway in gateway_territories:
                    gateway_terr = self.game_board.get_territory(gateway)
                    if gateway_terr and self.calculate_territory_threat(gateway, player_name) > 0.3:
                        return (source_name, gateway, armies_to_move)
        
        return best_move


class HannibalStrategy(OpportunisticStrategy):
    """Hannibal Barca: Master tactician known for surprise and unconventional strategies"""
    
    def __init__(self, player_name: str, game_board):
        super().__init__(player_name, game_board)
        print(f"{player_name} adopts the cunning tactics of Hannibal Barca!")
        # Hannibal was known for surprise attacks through unexpected routes
        
    def calculate_strategic_values(self):
        super().calculate_strategic_values()
        # Hannibal valued surprise and unexpected approaches
        # Value territories that allow surprise movements
        for territory_name in self.territory_values:
            if self.is_continent_gateway(territory_name):
                self.territory_values[territory_name] *= 1.3  # Bonus for territories that allow unexpected movements
    
    def calculate_attack_score(self, from_territory: str, to_territory: str, player_name: str) -> float:
        # Hannibal was known for unexpected attacks
        score = super().calculate_attack_score(from_territory, to_territory, player_name)
        
        # Hannibal favored attacking where enemies least expected
        # For simplicity, this means attacking from territories that border multiple enemy territories
        from_terr_obj = self.game_board.get_territory(from_territory)
        if from_terr_obj:
            enemy_borders = 0
            adjacent_territories = self.game_board.adjacencies.get(from_territory, [])
            for adj_name in adjacent_territories:
                adj_terr = self.game_board.get_territory(adj_name)
                if adj_terr and adj_terr.owner != player_name:
                    enemy_borders += 1
            
            if enemy_borders >= 2:  # Territory borders multiple enemies - good for surprise attacks
                score *= 1.3
        
        return score
    
    def get_best_reinforcement_territories(self, player_name: str, owned_territories: List[str]) -> List[str]:
        territories = super().get_best_reinforcement_territories(player_name, owned_territories)
        
        # Hannibal often used terrain to his advantage
        # Prioritize territories that border multiple enemy territories
        def multi_border_value(terr_name):
            enemy_borders = 0
            adjacent_territories = self.game_board.adjacencies.get(terr_name, [])
            for adj_name in adjacent_territories:
                adj_terr = self.game_board.get_territory(adj_name)
                if adj_terr and adj_terr.owner != player_name:
                    enemy_borders += 1
            return enemy_borders
        
        # Prioritize territories that can attack multiple enemies
        return sorted(territories, key=multi_border_value, reverse=True)


class ElizabethStrategy(DefensiveStrategy):
    """Queen Elizabeth I: Master of defensive strategy and resource management"""
    
    def __init__(self, player_name: str, game_board):
        super().__init__(player_name, game_board)
        print(f"{player_name} employs the shrewd defensive strategy of Queen Elizabeth I!")
        # Elizabeth was known for defensive positioning and diplomacy
        
    def calculate_strategic_values(self):
        super().calculate_strategic_values()
        # Elizabeth valued consolidating territory
        # Increase value of territories surrounded by friendly territories
        for territory_name in self.territory_values:
            secure_factor = self._calculate_security_factor(territory_name, self.player_name)
            self.territory_values[territory_name] *= (1.0 + secure_factor * 0.5)
    
    def _calculate_security_factor(self, territory_name: str, player_name: str) -> float:
        """Calculate how secure a territory is (surrounded by friendlies)"""
        adjacent_territories = self.game_board.adjacencies.get(territory_name, [])
        if not adjacent_territories:
            return 0.0
            
        friendly_count = 0
        for adj_name in adjacent_territories:
            adj_terr = self.game_board.get_territory(adj_name)
            if adj_terr and adj_terr.owner == player_name:
                friendly_count += 1
                
        return friendly_count / len(adjacent_territories)  # 0.0-1.0 security factor
    
    def calculate_attack_score(self, from_territory: str, to_territory: str, player_name: str) -> float:
        # Elizabeth was cautious about attacks, preferring consolidation
        score = super().calculate_attack_score(from_territory, to_territory, player_name)
        
        # Elizabeth was more likely to attack if it consolidated territory
        consolidation_factor = 0.0
        adjacent_territories = self.game_board.adjacencies.get(to_territory, [])
        for adj_name in adjacent_territories:
            if adj_name == from_territory:
                continue  # Skip the attacking territory
                
            adj_terr = self.game_board.get_territory(adj_name)
            if adj_terr and adj_terr.owner == player_name:
                consolidation_factor += 0.2  # Each adjacent owned territory increases attack value
        
        score *= (1.0 + consolidation_factor)
        
        # Elizabeth was very cautious about overextending
        from_terr = self.game_board.get_territory(from_territory)
        to_terr = self.game_board.get_territory(to_territory)
        
        if from_terr and to_terr and to_terr.armies > 0:
            if from_terr.armies < to_terr.armies * 1.3:  # Reduce score for attacks without clear advantage
                score *= 0.6
        
        return score
    
    def get_best_fortification_move(self, player_name: str, owned_territories: List[str]) -> Optional[Tuple[str, str, int]]:
        # Elizabeth prioritized strengthening border defenses
        best_move = super().get_best_fortification_move(player_name, owned_territories)
        
        if best_move:
            # If the destination isn't a border territory, look for one
            _, dest_name, _ = best_move
            if not self.is_front_line_territory(dest_name, player_name):
                front_line_territories = [t for t in owned_territories if self.is_front_line_territory(t, player_name)]
                if front_line_territories:
                    # Find the most threatened border territory
                    most_threatened = max(front_line_territories, 
                                        key=lambda t: self.calculate_territory_threat(t, player_name))
                    # Update destination to the threatened territory
                    source_name, _, armies_to_move = best_move
                    return (source_name, most_threatened, armies_to_move)
        
        return best_move


# Factory function to create AI strategy based on player name or preferences
def create_ai_strategy(player_name: str, game_board, strategy_type=None):
    """Create an AI strategy object based on player name or specified type"""
    
    # Historical leader-based strategies
    if "Napoleon" in player_name:
        return NapoleonStrategy(player_name, game_board)
    elif "Genghis Khan" in player_name:
        return GenghisKhanStrategy(player_name, game_board)
    elif "Alexander" in player_name:
        return AlexanderStrategy(player_name, game_board)
    elif "Sun Tzu" in player_name:
        return SunTzuStrategy(player_name, game_board)
    elif "Hannibal" in player_name:
        return HannibalStrategy(player_name, game_board)
    elif "Elizabeth" in player_name:
        return ElizabethStrategy(player_name, game_board)
    
    # Original strategies as fallback
    elif strategy_type is None:
        # Assign strategy based on player name
        if "Alpha" in player_name:
            return AggressiveStrategy(player_name, game_board)
        elif "Beta" in player_name:
            return DefensiveStrategy(player_name, game_board)
        elif "Gamma" in player_name:
            return BalancedStrategy(player_name, game_board)
        elif "Delta" in player_name:
            return OpportunisticStrategy(player_name, game_board)
        else:
            # Default to balanced
            return BalancedStrategy(player_name, game_board)
    else:
        # Create strategy based on specified type
        if strategy_type == "aggressive":
            return AggressiveStrategy(player_name, game_board)
        elif strategy_type == "defensive":
            return DefensiveStrategy(player_name, game_board)
        elif strategy_type == "balanced":
            return BalancedStrategy(player_name, game_board)
        elif strategy_type == "opportunistic":
            return OpportunisticStrategy(player_name, game_board)
        else:
            return AIStrategy(player_name, game_board)