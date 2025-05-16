from game_manager import GameManager

def main():
    print("Initializing Risk Simulator...")
    
    # Define players as historical military leaders: (Name, Color)
    player_configurations = [
        ("Napoleon Bonaparte", "Red"),     # Aggressive strategy
        ("Genghis Khan", "Yellow"),        # Opportunistic strategy  
        ("Alexander the Great", "Purple"), # Aggressive strategy
        ("Sun Tzu", "Green"),              # Balanced strategy
        ("Hannibal Barca", "Blue"),        # Opportunistic strategy
        ("Queen Elizabeth I", "Orange")    # Defensive strategy
    ]

    if not 2 <= len(player_configurations) <= 6:
        print("Error: Number of players must be between 2 and 6.")
        return

    # Initialize the game manager with visualization enabled
    game = GameManager(player_configurations, use_visualization=True)
    
    # Start the main game loop
    game.start_main_game_loop()
    
    print("\nRisk Simulator main execution finished.")

if __name__ == "__main__":
    main()