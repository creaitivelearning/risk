"""
Diplomacy module for Risk game.
Handles territory treaties and alliances between players.
"""
import random
from enum import Enum
from typing import Dict, List, Tuple, Optional, Set

class TreatyType(Enum):
    TERRITORY = "Territory Treaty"
    ALLIANCE = "Alliance"

class TreatyStatus(Enum):
    ACTIVE = "Active"
    BROKEN = "Broken"
    EXPIRED = "Expired"

class Treaty:
    """Base class for all diplomatic treaties"""
    def __init__(self, treaty_type: TreatyType, player1: str, player2: str, duration: int = 3):
        self.treaty_type = treaty_type
        self.player1 = player1
        self.player2 = player2
        self.duration = duration  # Duration in turns
        self.turns_remaining = duration
        self.status = TreatyStatus.ACTIVE
        self.creation_turn = 0  # Will be set when added to DiplomacyManager
    
    def is_active(self) -> bool:
        """Check if the treaty is still active"""
        return self.status == TreatyStatus.ACTIVE
    
    def involves_player(self, player_name: str) -> bool:
        """Check if a player is involved in this treaty"""
        return player_name == self.player1 or player_name == self.player2
    
    def get_involved_players(self) -> Tuple[str, str]:
        """Get the players involved in this treaty"""
        return (self.player1, self.player2)
    
    def decrement_duration(self) -> bool:
        """Decrement the treaty duration. Returns True if expired."""
        if not self.is_active():
            return True
            
        self.turns_remaining -= 1
        if self.turns_remaining <= 0:
            self.status = TreatyStatus.EXPIRED
            return True
        return False
    
    def break_treaty(self):
        """Mark the treaty as broken"""
        if self.is_active():
            self.status = TreatyStatus.BROKEN
    
    def __repr__(self):
        return f"{self.treaty_type.value} between {self.player1} and {self.player2} ({self.status.value}, {self.turns_remaining} turns remaining)"

class TerritoryTreaty(Treaty):
    """A treaty between two players regarding specific territories"""
    def __init__(self, player1: str, player2: str, territory1: str, territory2: str, duration: int = 3):
        super().__init__(TreatyType.TERRITORY, player1, player2, duration)
        self.territory1 = territory1  # Territory owned by player1
        self.territory2 = territory2  # Territory owned by player2
    
    def covers_territories(self, terr1: str, terr2: str) -> bool:
        """Check if this treaty covers the two territories"""
        return ((self.territory1 == terr1 and self.territory2 == terr2) or
                (self.territory1 == terr2 and self.territory2 == terr1))
    
    def __repr__(self):
        return f"Territory Treaty: {self.player1} ({self.territory1}) and {self.player2} ({self.territory2}) - {self.status.value}, {self.turns_remaining} turns remaining"

class Alliance(Treaty):
    """An alliance treaty between two players"""
    def __init__(self, player1: str, player2: str, duration: int = 5):
        super().__init__(TreatyType.ALLIANCE, player1, player2, duration)
    
    def __repr__(self):
        return f"Alliance between {self.player1} and {self.player2} - {self.status.value}, {self.turns_remaining} turns remaining"

class DiplomacyManager:
    """Manages all diplomatic relations in the game"""
    def __init__(self):
        self.treaties: List[Treaty] = []
        self.current_turn = 0
        self.treaty_proposals: Dict[Tuple[str, str], List[Treaty]] = {}  # (from_player, to_player) -> list of proposals
        self.trust_levels: Dict[Tuple[str, str], float] = {}  # (player1, player2) -> trust level (0.0-1.0)
    
    def update_turn(self):
        """Update treaties at the start of a new turn"""
        self.current_turn += 1
        expired_treaties = []
        
        for treaty in self.treaties:
            if treaty.is_active() and treaty.decrement_duration():
                expired_treaties.append(treaty)
        
        return expired_treaties
    
    def propose_treaty(self, treaty: Treaty):
        """Register a treaty proposal between players"""
        from_player, to_player = treaty.get_involved_players()
        if (from_player, to_player) not in self.treaty_proposals:
            self.treaty_proposals[(from_player, to_player)] = []
        
        self.treaty_proposals[(from_player, to_player)].append(treaty)
    
    def accept_treaty(self, treaty: Treaty) -> bool:
        """Accept a treaty proposal"""
        from_player, to_player = treaty.get_involved_players()
        
        # Check if proposal exists
        if (from_player, to_player) in self.treaty_proposals and treaty in self.treaty_proposals[(from_player, to_player)]:
            # Remove from proposals
            self.treaty_proposals[(from_player, to_player)].remove(treaty)
            
            # Set creation turn
            treaty.creation_turn = self.current_turn
            
            # Add to active treaties
            self.treaties.append(treaty)
            return True
        
        return False
    
    def reject_treaty(self, treaty: Treaty) -> bool:
        """Reject a treaty proposal"""
        from_player, to_player = treaty.get_involved_players()
        
        # Check if proposal exists
        if (from_player, to_player) in self.treaty_proposals and treaty in self.treaty_proposals[(from_player, to_player)]:
            # Remove from proposals
            self.treaty_proposals[(from_player, to_player)].remove(treaty)
            return True
        
        return False
    
    def break_treaty(self, treaty: Treaty):
        """Break an active treaty"""
        if treaty in self.treaties and treaty.is_active():
            treaty.break_treaty()
            
            # Decrease trust between the players
            from_player, to_player = treaty.get_involved_players()
            self._decrease_trust(from_player, to_player)
    
    def has_active_alliance(self, player1: str, player2: str) -> bool:
        """Check if two players have an active alliance"""
        for treaty in self.treaties:
            if (treaty.treaty_type == TreatyType.ALLIANCE and 
                treaty.is_active() and 
                ((treaty.player1 == player1 and treaty.player2 == player2) or
                 (treaty.player1 == player2 and treaty.player2 == player1))):
                return True
        return False
    
    def has_territory_treaty(self, player1: str, territory1: str, player2: str, territory2: str) -> bool:
        """Check if there's an active territory treaty covering these territories"""
        for treaty in self.treaties:
            if (isinstance(treaty, TerritoryTreaty) and 
                treaty.is_active() and 
                ((treaty.player1 == player1 and treaty.player2 == player2) or
                 (treaty.player1 == player2 and treaty.player2 == player1)) and
                treaty.covers_territories(territory1, territory2)):
                return True
        return False
    
    def get_player_treaties(self, player_name: str) -> List[Treaty]:
        """Get all active treaties involving a player"""
        return [treaty for treaty in self.treaties 
                if treaty.is_active() and treaty.involves_player(player_name)]
    
    def get_player_proposals(self, to_player: str) -> List[Tuple[Treaty, str]]:
        """Get all treaty proposals to a player"""
        proposals = []
        for (from_player, to), treaty_list in self.treaty_proposals.items():
            if to == to_player:
                for treaty in treaty_list:
                    proposals.append((treaty, from_player))
        return proposals
    
    def get_trust_level(self, player1: str, player2: str) -> float:
        """Get the trust level between two players (0.0-1.0)"""
        key = tuple(sorted([player1, player2]))
        return self.trust_levels.get(key, 0.5)  # Default to neutral trust
    
    def _increase_trust(self, player1: str, player2: str, amount: float = 0.1):
        """Increase trust between two players"""
        key = tuple(sorted([player1, player2]))
        current = self.trust_levels.get(key, 0.5)
        self.trust_levels[key] = min(1.0, current + amount)
    
    def _decrease_trust(self, player1: str, player2: str, amount: float = 0.2):
        """Decrease trust between two players"""
        key = tuple(sorted([player1, player2]))
        current = self.trust_levels.get(key, 0.5)
        self.trust_levels[key] = max(0.0, current - amount)
    
    def evaluate_treaty_proposal(self, treaty: Treaty, ai_strategy=None) -> float:
        """AI helper function to evaluate the value of a treaty proposal"""
        # Base assessment score (0.0-1.0)
        score = 0.5
        
        player1, player2 = treaty.get_involved_players()
        
        # Factor in trust level
        trust = self.get_trust_level(player1, player2)
        score += (trust - 0.5) * 0.3  # Trust impacts score by ±0.15
        
        # Check treaty type specific factors
        if isinstance(treaty, TerritoryTreaty):
            # For territory treaties, we'd need to evaluate the strategic importance
            if ai_strategy:
                # If we have an AI strategy, use it to evaluate the territory values
                # This is a stub - the real implementation would depend on your AI strategy
                # Might compare the relative values of the territories
                pass
            else:
                # Default behavior without AI strategy
                score += 0.1  # Slightly favor territory treaties
        
        elif isinstance(treaty, Alliance):
            # Alliances are generally more valuable but riskier
            score += 0.2  # More valuable than territory treaties
            
            # Maybe reduce score if the other player is much stronger
            if ai_strategy:
                pass  # Would evaluate relative player strengths
        
        return min(max(0.0, score), 1.0)  # Ensure score is in 0.0-1.0 range

# Example usage
if __name__ == "__main__":
    diplomacy = DiplomacyManager()
    
    # Create a territory treaty
    territory_treaty = TerritoryTreaty("Player 1", "Player 2", "Alaska", "Alberta", duration=3)
    print(territory_treaty)
    
    # Create an alliance
    alliance = Alliance("Player 1", "Player 3", duration=5)
    print(alliance)
    
    # Propose treaties
    diplomacy.propose_treaty(territory_treaty)
    diplomacy.propose_treaty(alliance)
    
    # Accept treaties
    diplomacy.accept_treaty(territory_treaty)
    diplomacy.accept_treaty(alliance)
    
    # Check active treaties
    print("\nActive treaties for Player 1:", diplomacy.get_player_treaties("Player 1"))
    
    # Update turn and check again
    expired = diplomacy.update_turn()
    print("\nExpired treaties after turn update:", expired)
    print("Active treaties after turn update:", diplomacy.get_player_treaties("Player 1"))
    
    # Check alliance
    print("\nAlliance between Player 1 and Player 3:", 
          diplomacy.has_active_alliance("Player 1", "Player 3"))
    
    # Check territory treaty
    print("Territory treaty for Alaska-Alberta:", 
          diplomacy.has_territory_treaty("Player 1", "Alaska", "Player 2", "Alberta"))