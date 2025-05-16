import pygame
import sys
import time
import math
from game_board import GameBoard
from diplomacy import TreatyType, TreatyStatus

# Constants
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 768
BACKGROUND_COLOR = (245, 245, 245)  # Off-white, changed from dark blue
TERRITORY_COLORS = {
    None: (200, 200, 200),  # Gray for unowned
    "Napoleon Bonaparte": (220, 60, 60),     # Red
    "Genghis Khan": (220, 220, 60),          # Yellow
    "Alexander the Great": (190, 60, 190),   # Purple
    "Sun Tzu": (60, 190, 60),                # Green
    "Hannibal Barca": (60, 120, 220),        # Blue
    "Queen Elizabeth I": (255, 165, 0),      # Orange
    # Keep old mappings for backward compatibility
    "AI Alpha": (220, 60, 60),   # Red
    "AI Beta": (60, 120, 220),   # Blue
    "AI Gamma": (60, 190, 60),   # Green
    "AI Delta": (220, 220, 60),  # Yellow
    "AI Epsilon": (190, 60, 190), # Purple
    "AI Zeta": (60, 190, 190),   # Teal
}
# Card colors
CARD_COLORS = {
    "Infantry": (150, 200, 150),  # Light green
    "Cavalry": (200, 150, 150),   # Light red
    "Artillery": (150, 150, 200), # Light blue
    "Wild": (200, 200, 100)       # Light yellow
}
CONTINENT_COLORS = {
    "NorthAmerica": (255, 210, 80, 100),     # Yellow (from the image)
    "SouthAmerica": (255, 160, 130, 100),    # Salmon/orange (from the image)
    "Europe": (160, 180, 230, 100),          # Blue (from the image)
    "Africa": (240, 210, 150, 100),          # Yellow/brown (from the image)
    "Asia": (180, 220, 180, 100),            # Green (from the image)
    "Australia": (255, 180, 210, 100),       # Pink (from the image)
}
HIGHLIGHT_COLOR = (255, 255, 255, 180)
TEXT_COLOR = (20, 20, 20)
BORDER_COLOR = (0, 0, 0)          # Black, changed from dark gray/blue
CONNECTION_COLOR = (0, 0, 0)      # Black, changed from gray/blue
WATER_COLOR = (245, 245, 245)     # Off-white, same as BACKGROUND_COLOR (was (61, 89, 124))
FONT_SIZE = 14
LARGE_FONT_SIZE = 24
TERRITORY_RADIUS = 22
LINE_WIDTH = 2

# New colors for continent styling
CONTINENT_OUTLINE_COLOR = (0, 0, 0, 220)  # Black outline, fairly opaque
CONTINENT_FILL_COLOR = (230, 230, 230, 40) # Very light gray, very transparent fill

# Treaty visualization colors
ALLIANCE_COLOR = (255, 215, 0, 150)  # Gold with transparency
TERRITORY_TREATY_COLOR = (0, 191, 255, 150)  # Deep Sky Blue with transparency
TREATY_LINE_WIDTH = 4

# Territory coordinates - accurate to official Risk board layout
TERRITORY_COORDS = {
    # North America
    "Alaska": (85, 135),
    "NorthwestTerritory": (175, 125),
    "Greenland": (335, 95),
    "Alberta": (155, 165),
    "Ontario": (215, 175),
    "Quebec": (265, 165),
    "WesternUS": (155, 220),
    "EasternUS": (220, 235),
    "CentralAmerica": (170, 290),
    
    # South America
    "Venezuela": (225, 330),
    "Peru": (225, 390),
    "Brazil": (285, 380),
    "Argentina": (240, 455),
    
    # Europe
    "Iceland": (405, 120),
    "Scandinavia": (465, 110),
    "GreatBritain": (415, 165),
    "NorthernEurope": (470, 175),
    "Ukraine": (530, 155),
    "WesternEurope": (425, 215),
    "SouthernEurope": (485, 220),
    
    # Africa
    "NorthAfrica": (435, 310),
    "Egypt": (490, 280),
    "EastAfrica": (530, 340),
    "Congo": (480, 380),
    "SouthAfrica": (490, 450),
    "Madagascar": (560, 435),
    
    # Asia
    "Ural": (600, 135),
    "Siberia": (660, 105),
    "Yakutsk": (725, 85),
    "Kamchatka": (810, 105),
    "Irkutsk": (710, 145),
    "Mongolia": (750, 180),
    "Japan": (840, 195),
    "Afghanistan": (590, 200),
    "China": (700, 230),
    "MiddleEast": (550, 250),
    "India": (620, 280),
    "Siam": (700, 300),
    
    # Australia
    "Indonesia": (700, 360),
    "NewGuinea": (790, 360),
    "WesternAustralia": (740, 450),
    "EasternAustralia": (810, 450),
}

# Accurate continent shapes based on the official Risk board
CONTINENT_SHAPES = {
    "NorthAmerica": [
        (70, 100), (110, 80), (160, 65), (220, 60), (280, 65), (330, 80),  # Northern edge
        (360, 95), (370, 120), (350, 110), (320, 95), (290, 90),           # Greenland
        (260, 110), (230, 130), (210, 150), (190, 170), (180, 190),        # Eastern Canada
        (190, 210), (205, 240), (190, 270), (170, 290), (150, 310),        # Eastern/Central US
        (130, 290), (110, 260), (100, 230), (90, 200),                     # Western US
        (80, 170), (70, 140), (65, 120)                                    # Alaska & Canada west coast
    ],
    "SouthAmerica": [
        (150, 310), (170, 310), (190, 320), (205, 340), (220, 360),        # North/Central America connection
        (240, 380), (250, 400), (255, 425), (245, 460), (235, 480),        # East coast
        (215, 490), (195, 480), (180, 460), (170, 435), (165, 405),        # South/West coasts
        (170, 380), (165, 350), (155, 330)                                 # West coast/Panama
    ],
    "Europe": [
        (385, 110), (415, 95), (445, 90), (475, 95), (505, 105),           # Northern edge
        (530, 120), (545, 140), (535, 160), (520, 175), (505, 185),        # Eastern Europe
        (485, 195), (460, 200), (435, 195), (415, 185), (400, 170),        # Southern Europe
        (395, 150), (390, 130)                                            # Western Europe
    ],
    "Africa": [
        (415, 275), (440, 265), (465, 260), (490, 265), (515, 275),        # Northern Africa
        (530, 295), (540, 320), (545, 345), (540, 370), (530, 395),        # East Africa
        (515, 420), (500, 445), (480, 465), (455, 470), (430, 460),        # South Africa
        (415, 435), (400, 405), (395, 375), (395, 345), (400, 310)         # West Africa
    ],
    "Asia": [
        (545, 140), (570, 120), (605, 100), (640, 85), (680, 80),          # Northern edge
        (720, 85), (760, 95), (790, 110), (815, 130), (830, 155),          # Northeast
        (825, 185), (810, 215), (790, 240), (770, 260), (745, 280),        # East coast
        (720, 300), (690, 315), (660, 320), (630, 315), (600, 300),        # Southeast
        (575, 280), (555, 255), (540, 225), (535, 195), (535, 170),        # South/Southwest
        (540, 155)                                                         # Back to Ukraine border
    ],
    "Australia": [
        (690, 345), (715, 340), (740, 340), (765, 345), (790, 350),        # Northern edge (Indonesia/NG)
        (815, 365), (830, 385), (835, 410), (830, 435), (815, 455),        # Eastern Australia
        (795, 470), (770, 475), (745, 470), (725, 455), (710, 435),        # Southern Australia
        (700, 410), (695, 380), (690, 360)                                # Western Australia
    ]
}

# More accurate territory shapes based on actual Risk board
TERRITORY_SHAPES = {
    # North America
    "Alaska": [
        (70, 110), (85, 90), (105, 95), (115, 110), (115, 130), 
        (100, 140), (80, 135), (65, 120)
    ],
    "NorthwestTerritory": [
        (115, 110), (140, 95), (180, 95), (210, 105), (215, 125),
        (190, 135), (160, 145), (135, 140), (115, 130)
    ],
    "Greenland": [
        (290, 60), (320, 55), (350, 75), (370, 95), (360, 115),
        (335, 110), (315, 100), (295, 85), (280, 70)
    ],
    "Alberta": [
        (135, 140), (160, 145), (165, 165), (150, 185), (135, 185),
        (125, 170), (120, 155)
    ],
    "Ontario": [
        (190, 135), (215, 125), (240, 140), (245, 165), (230, 185),
        (210, 195), (185, 185), (165, 165), (160, 145)
    ],
    "Quebec": [
        (240, 140), (270, 135), (285, 145), (290, 165), (275, 185),
        (250, 190), (230, 185), (245, 165)
    ],
    "WesternUS": [
        (135, 185), (150, 185), (165, 165), (185, 185), (180, 210),
        (170, 230), (145, 235), (130, 225), (125, 205)
    ],
    "EasternUS": [
        (185, 185), (210, 195), (230, 185), (250, 190), (240, 220),
        (220, 240), (200, 245), (180, 230), (180, 210)
    ],
    "CentralAmerica": [
        (145, 235), (170, 230), (180, 230), (200, 245), (190, 270),
        (180, 290), (165, 310), (155, 295), (145, 270), (140, 250)
    ],
    
    # South America
    "Venezuela": [
        (180, 290), (190, 270), (210, 280), (230, 290), (245, 315),
        (240, 335), (225, 345), (210, 340), (195, 320), (185, 305)
    ],
    "Peru": [
        (195, 320), (210, 340), (225, 345), (235, 365), (240, 385),
        (225, 405), (210, 410), (200, 395), (195, 375), (185, 350)
    ],
    "Brazil": [
        (225, 345), (240, 335), (260, 340), (280, 350), (295, 370),
        (290, 395), (275, 415), (260, 420), (240, 405), (235, 365)
    ],
    "Argentina": [
        (225, 405), (240, 405), (260, 420), (265, 445), (255, 470),
        (240, 485), (225, 470), (215, 445), (210, 425)
    ],
    
    # Europe
    "Iceland": [
        (395, 110), (410, 105), (425, 110), (425, 125), (415, 135),
        (400, 130), (390, 120)
    ],
    "Scandinavia": [
        (455, 80), (480, 85), (490, 100), (485, 120), (470, 135),
        (450, 130), (440, 115), (445, 95)
    ],
    "GreatBritain": [
        (400, 150), (410, 145), (425, 155), (430, 170), (420, 185),
        (405, 180), (395, 165)
    ],
    "NorthernEurope": [
        (450, 130), (470, 135), (490, 145), (495, 165), (480, 180),
        (460, 185), (440, 175), (435, 155), (440, 140)
    ],
    "Ukraine": [
        (490, 100), (520, 100), (550, 115), (555, 140), (545, 160),
        (525, 170), (505, 170), (490, 145), (485, 120)
    ],
    "WesternEurope": [
        (435, 155), (440, 175), (450, 195), (445, 215), (430, 225),
        (415, 220), (405, 200), (410, 180), (420, 185), (430, 170)
    ],
    "SouthernEurope": [
        (460, 185), (480, 180), (495, 165), (505, 170), (525, 170),
        (520, 190), (505, 205), (490, 215), (470, 210), (450, 195)
    ],
    
    # Africa
    "NorthAfrica": [
        (415, 220), (430, 225), (445, 215), (470, 210), (490, 215),
        (505, 230), (495, 255), (480, 275), (455, 290), (430, 295),
        (410, 280), (400, 260), (405, 235)
    ],
    "Egypt": [
        (490, 215), (505, 205), (520, 210), (535, 235), (525, 255),
        (510, 275), (495, 280), (480, 275), (495, 255), (505, 230)
    ],
    "EastAfrica": [
        (510, 275), (525, 255), (545, 270), (560, 290), (565, 320),
        (550, 350), (535, 365), (520, 370), (505, 355), (495, 335),
        (490, 310), (495, 280)
    ],
    "Congo": [
        (480, 275), (495, 280), (490, 310), (495, 335), (485, 360),
        (470, 375), (450, 370), (440, 350), (445, 325), (455, 290)
    ],
    "SouthAfrica": [
        (485, 360), (505, 355), (520, 370), (530, 390), (525, 420),
        (510, 440), (485, 455), (465, 445), (455, 420), (460, 390),
        (470, 375)
    ],
    "Madagascar": [
        (550, 410), (570, 410), (575, 435), (565, 455), (545, 450),
        (540, 430)
    ],
    
    # Asia
    "Ural": [
        (550, 115), (580, 105), (605, 115), (615, 135), (610, 160),
        (590, 175), (570, 170), (555, 150), (555, 140)
    ],
    "Siberia": [
        (605, 115), (630, 90), (660, 85), (680, 100), (685, 120),
        (670, 130), (650, 135), (630, 140), (615, 135)
    ],
    "Yakutsk": [
        (680, 100), (710, 75), (735, 65), (755, 75), (765, 95),
        (750, 110), (730, 115), (700, 110), (685, 120)
    ],
    "Kamchatka": [
        (755, 75), (780, 70), (810, 85), (830, 105), (835, 125),
        (820, 140), (805, 145), (785, 135), (765, 120), (765, 95)
    ],
    "Irkutsk": [
        (685, 120), (700, 110), (730, 115), (750, 110), (760, 120),
        (755, 140), (735, 155), (710, 160), (690, 150), (670, 130)
    ],
    "Mongolia": [
        (710, 160), (735, 155), (755, 140), (780, 150), (795, 170),
        (780, 190), (755, 200), (730, 195), (715, 180), (705, 170)
    ],
    "Japan": [
        (835, 175), (850, 170), (860, 185), (855, 205), (840, 215),
        (825, 210), (820, 195), (825, 180)
    ],
    "Afghanistan": [
        (570, 170), (590, 175), (610, 160), (630, 170), (625, 190),
        (610, 210), (590, 215), (570, 200), (565, 185)
    ],
    "China": [
        (630, 170), (650, 135), (670, 130), (690, 150), (705, 170),
        (715, 180), (730, 195), (720, 215), (705, 230), (680, 240),
        (655, 230), (640, 215), (625, 190)
    ],
    "MiddleEast": [
        (525, 170), (545, 160), (565, 185), (570, 200), (590, 215),
        (580, 235), (565, 250), (545, 260), (530, 245), (520, 220),
        (520, 190)
    ],
    "India": [
        (590, 215), (610, 210), (625, 190), (640, 215), (655, 230),
        (650, 250), (635, 270), (615, 280), (595, 275), (580, 260),
        (580, 235)
    ],
    "Siam": [
        (655, 230), (680, 240), (705, 230), (715, 245), (720, 270),
        (710, 290), (690, 305), (670, 300), (650, 280), (635, 270),
        (650, 250)
    ],
    
    # Australia
    "Indonesia": [
        (710, 290), (730, 305), (750, 330), (740, 350), (720, 360),
        (700, 355), (685, 340), (690, 315)
    ],
    "NewGuinea": [
        (790, 330), (820, 330), (830, 345), (825, 365), (805, 375),
        (780, 370), (770, 350), (775, 335)
    ],
    "WesternAustralia": [
        (740, 390), (755, 385), (775, 395), (780, 415), (770, 435),
        (750, 450), (730, 445), (720, 430), (725, 410)
    ],
    "EasternAustralia": [
        (780, 370), (805, 375), (830, 390), (840, 410), (835, 440),
        (820, 460), (800, 465), (780, 450), (770, 435), (780, 415),
        (775, 395)
    ]
}

# NEW – path to the Risk board image
BOARD_IMAGE_PATH = "risk_board.png"

class GameVisualization:
    def __init__(self, game_board):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.display.set_caption("Risk Simulator")

        self.font = pygame.font.SysFont("Arial", FONT_SIZE)
        self.large_font = pygame.font.SysFont("Arial", LARGE_FONT_SIZE)
        self.game_board = game_board
        self.clock = pygame.time.Clock()
        self.running = True

        # prepare board bitmap
        self._load_and_scale_board()

    def _load_and_scale_board(self):
        img_orig = pygame.image.load(BOARD_IMAGE_PATH).convert_alpha()
        rect = img_orig.get_rect()
        scale = min(SCREEN_WIDTH/rect.w, SCREEN_HEIGHT/rect.h)
        new_size = (int(rect.w * scale), int(rect.h * scale))
        self._board_scale = scale
        self._board_img = pygame.transform.smoothscale(img_orig, new_size)
        self._board_pos = ((SCREEN_WIDTH - new_size[0])//2, (SCREEN_HEIGHT - new_size[1])//2)

    def _board_to_screen(self, pt):
        return (int(pt[0] * self._board_scale) + self._board_pos[0],
                int(pt[1] * self._board_scale) + self._board_pos[1])

    def draw_connection(self, t1, t2):
        # draw curved or straight antialiased line between two territories
        if t1 not in TERRITORY_COORDS or t2 not in TERRITORY_COORDS:
            return
        x1, y1 = self._board_to_screen(TERRITORY_COORDS[t1])
        x2, y2 = self._board_to_screen(TERRITORY_COORDS[t2])
        dx, dy = x2 - x1, y2 - y1
        dist = math.hypot(dx, dy)
        if dist < 100:
            pygame.draw.aaline(self.screen, CONNECTION_COLOR, (x1, y1), (x2, y2))
            return
        midx, midy = (x1+x2)/2, (y1+y2)/2
        curve = min(dist * 0.15, 50)
        nx, ny = -dy/dist, dx/dist
        cx, cy = midx + nx*curve, midy + ny*curve
        pts = []
        for t in (i/100 for i in range(0,101,5)):
            bx = (1-t)**2*x1 + 2*(1-t)*t*cx + t*t*x2
            by = (1-t)**2*y1 + 2*(1-t)*t*cy + t*t*y2
            pts.append((bx, by))
        pygame.draw.aalines(self.screen, CONNECTION_COLOR, False, pts)

    def draw_connections(self):
        """Draw all adjacency lines by iterating over board adjacencies"""
        for terr1, neighbors in self.game_board.adjacencies.items():
            for terr2 in neighbors:
                # Draw each connection only once
                if terr1 < terr2:
                    self.draw_connection(terr1, terr2)

    def draw_territory(self, name, territory):
        # filled circle + outline over the board image
        if name not in TERRITORY_COORDS:
            return
        x, y = self._board_to_screen(TERRITORY_COORDS[name])
        color = TERRITORY_COLORS.get(territory.owner, TERRITORY_COLORS[None])
        pygame.draw.circle(self.screen, color, (x, y), TERRITORY_RADIUS)
        pygame.draw.circle(self.screen, BORDER_COLOR, (x, y), TERRITORY_RADIUS, LINE_WIDTH)
        # label
        short = self._abbreviate_name(name)
        lbl = self.font.render(short, True, TEXT_COLOR)
        self.screen.blit(lbl, (x-lbl.get_width()//2, y-TERRITORY_RADIUS-15))
        # armies
        if territory.armies:
            army = self.font.render(str(territory.armies), True, TEXT_COLOR)
            bg = pygame.Surface((army.get_width()+6, army.get_height()+2), pygame.SRCALPHA)
            bg.fill((255,255,255,180))
            self.screen.blit(bg, (x-bg.get_width()//2, y-bg.get_height()//2))
            self.screen.blit(army, (x-army.get_width()//2, y-army.get_height()//2))

    # keep your full first _abbreviate_name; delete any duplicate below
    def _abbreviate_name(self, name):
        abbreviations = {
            "Alaska": "AK",
            "NorthwestTerritory": "NW Terr.",
            "Greenland": "Green.",
            "Alberta": "AB",
            "Ontario": "ON",
            "Quebec": "QC",
            "WesternUS": "W. US",
            "EasternUS": "E. US",
            "CentralAmerica": "C. America",
            "Venezuela": "Ven.",
            "Peru": "Per.",
            "Brazil": "Bra.",
            "Argentina": "Arg.",
            "Iceland": "Ice.",
            "Scandinavia": "Scan.",
            "GreatBritain": "G.B.",
            "NorthernEurope": "N. Euro.",
            "Ukraine": "Ukr.",
            "WesternEurope": "W. Euro.",
            "SouthernEurope": "S. Euro.",
            "NorthAfrica": "N. Afr.",
            "Egypt": "Eg.",
            "EastAfrica": "E. Afr.",
            "Congo": "Congo",
            "SouthAfrica": "S. Afr.",
            "Madagascar": "Mad.",
            "Ural": "Ural",
            "Siberia": "Sibe.",
            "Yakutsk": "Yak.",
            "Kamchatka": "Kam.",
            "Irkutsk": "Irk.",
            "Mongolia": "Mong.",
            "Japan": "Jap.",
            "Afghanistan": "Afg.",
            "China": "Chi.",
            "MiddleEast": "M.E.",
            "India": "Ind.",
            "Siam": "Siam",
            "Indonesia": "Indo.",
            "NewGuinea": "N. Guinea",
            "WesternAustralia": "W. Aus.",
            "EasternAustralia": "E. Aus.",
        }
        return abbreviations.get(name, name)

    def draw_board(self, players=None, current_player=None, phase=None, diplomacy=None):
        # 1) ocean
        self.screen.fill(BACKGROUND_COLOR)
        # 2) board image
        self.screen.blit(self._board_img, self._board_pos)
        # 3) adjacency lines
        self.draw_connections()
        # 4) territories
        for nm, terr in self.game_board.territories.items():
            self.draw_territory(nm, terr)
        # 5) UI overlays unchanged
        if players is not None:
            self.draw_player_stats(players)
            
            # Draw cards panel for the current player
            if current_player:
                self.draw_cards_panel(players, current_player)
                self.draw_reinforcements_indicator(current_player)
            
            # Draw diplomacy panel if available
            if diplomacy:
                self.draw_diplomacy_panel(players, diplomacy)
        
        # Draw legend/info box in the bottom left
        if current_player is not None and phase is not None:
            info_box_height = 80
            info_box_width = 300
            pygame.draw.rect(self.screen, (0, 0, 0, 100), 
                            (10, SCREEN_HEIGHT - info_box_height - 10, 
                             info_box_width, info_box_height))
            
            # Current player and phase info
            turn_text = self.large_font.render(f"{current_player.name}'s Turn", True, (255, 255, 255))
            self.screen.blit(turn_text, (20, SCREEN_HEIGHT - info_box_height))
            
            phase_text = self.font.render(f"Phase: {phase}", True, (255, 255, 255))
            self.screen.blit(phase_text, (20, SCREEN_HEIGHT - info_box_height + 30))
            
            # Controls info
            controls_text = self.font.render("Press ESC to exit", True, (200, 200, 200))
            self.screen.blit(controls_text, (20, SCREEN_HEIGHT - info_box_height + 55))
        
        # Update the display
        pygame.display.flip()
    
    def check_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close()
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.close()
                    return False
        return True
    
    def close(self):
        self.running = False
        pygame.quit()
        
    def pause(self, seconds=0.5):
        """Pause for a specified number of seconds while checking for exit events"""
        start_time = time.time()
        while time.time() - start_time < seconds:
            if not self.check_events():
                return False
            self.clock.tick(30)
        return True

    def draw_player_stats(self, players):
        sidebar_x = SCREEN_WIDTH - 200
        sidebar_y = 10
        sidebar_width = 190
        sidebar_height = 25 * len(players) + 30
        sidebar_surface = pygame.Surface((sidebar_width, sidebar_height), pygame.SRCALPHA)
        sidebar_surface.fill((230, 230, 230, 200))
        self.screen.blit(sidebar_surface, (sidebar_x, sidebar_y))
        header_text = self.font.render("PLAYERS", True, (0, 0, 0))
        self.screen.blit(header_text, (sidebar_x + 10, sidebar_y + 10))
        pygame.draw.line(self.screen, (100, 100, 100),
                        (sidebar_x + 10, sidebar_y + 30),
                        (sidebar_x + sidebar_width - 10, sidebar_y + 30), 2)
        y_offset = sidebar_y + 40
        for player in players:
            if player.is_eliminated():
                continue
            player_color = TERRITORY_COLORS.get(player.name, (150, 150, 150))
            pygame.draw.rect(self.screen, player_color, (sidebar_x + 10, y_offset, 15, 15))
            name_to_display = player.name
            if len(name_to_display) > 13:
                name_to_display = name_to_display[:10] + "..."
            name_text = self.font.render(name_to_display, True, (0, 0, 0))
            self.screen.blit(name_text, (sidebar_x + 30, y_offset))
            territories = len(player.territories_owned)
            total_armies = sum(self.game_board.territories[t].armies for t in player.territories_owned)
            reinforcement_text = f"+{player.reinforcements}" if player.reinforcements > 0 else ""
            stat_text = self.font.render(f"{territories}🌐 {total_armies}⚔ {reinforcement_text}", True, (60, 60, 60))
            self.screen.blit(stat_text, (sidebar_x + 30, y_offset + 14))
            y_offset += 25

    def draw_cards_panel(self, players, current_player):
        if not current_player or current_player.is_eliminated() or not current_player.cards:
            return
        cards_x = SCREEN_WIDTH - 200
        cards_y = 250
        panel_width = 190
        card_width = 40
        card_height = 60
        card_spacing = 5
        cards_header = self.font.render(f"{current_player.name.upper()} CARDS", True, (0, 0, 0))
        self.screen.blit(cards_header, (cards_x + (panel_width - cards_header.get_width()) // 2, cards_y))
        pygame.draw.line(self.screen, (100, 100, 100),
                        (cards_x + 10, cards_y + 20),
                        (cards_x + panel_width - 10, cards_y + 20), 2)
        cards_per_row = min(4, len(current_player.cards))
        rows_needed = (len(current_player.cards) + cards_per_row - 1) // cards_per_row
        total_cards_height = rows_needed * (card_height + card_spacing) + 10
        cards_bg_height = total_cards_height + 30
        cards_surface = pygame.Surface((panel_width, cards_bg_height), pygame.SRCALPHA)
        cards_surface.fill((230, 230, 230, 200))
        self.screen.blit(cards_surface, (cards_x, cards_y))
        for i, card in enumerate(current_player.cards):
            row = i // cards_per_row
            col = i % cards_per_row
            card_x = cards_x + 10 + col * (card_width + card_spacing)
            card_y = cards_y + 30 + row * (card_height + card_spacing)
            card_color = CARD_COLORS.get(card.type, (200, 200, 200))
            pygame.draw.rect(self.screen, card_color, (card_x, card_y, card_width, card_height))
            pygame.draw.rect(self.screen, (0, 0, 0), (card_x, card_y, card_width, card_height), 1)
            type_text = self.font.render(card.type[0], True, (0, 0, 0))
            self.screen.blit(type_text, (card_x + (card_width - type_text.get_width()) // 2, card_y + 5))
            if card.territory:
                terr_name = self._abbreviate_name(card.territory, 5)
                terr_text = pygame.font.SysFont("Arial", 10).render(terr_name, True, (0, 0, 0))
                self.screen.blit(terr_text, (card_x + (card_width - terr_text.get_width()) // 2, card_y + card_height - 15))

    def draw_reinforcements_indicator(self, current_player):
        if not current_player or current_player.reinforcements <= 0:
            return
        x, y = 10, 10
        width, height = 200, 60
        reinforcement_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        reinforcement_surface.fill((230, 230, 230, 200))
        self.screen.blit(reinforcement_surface, (x, y))
        header_text = self.font.render("REINFORCEMENTS", True, (0, 0, 0))
        self.screen.blit(header_text, (x + 10, y + 10))
        reinforcement_text = self.large_font.render(f"{current_player.reinforcements}", True, (200, 0, 0))
        self.screen.blit(reinforcement_text, (x + 20, y + 30))
        player_color = TERRITORY_COLORS.get(current_player.name, (150, 150, 150))
        pygame.draw.rect(self.screen, player_color, (x + width - 100, y + 30, 15, 15))
        name_to_display = current_player.name
        if len(name_to_display) > 10:
            name_to_display = name_to_display[:7] + "..."
        name_text = self.font.render(name_to_display, True, (0, 0, 0))
        self.screen.blit(name_text, (x + width - 80, y + 30))

    def draw_diplomacy_panel(self, players, diplomacy):
        # stub: implement if needed or skip
        pass

# Simple test if run directly
if __name__ == "__main__":
    game_board = GameBoard()
    vis = GameVisualization(game_board)
    vis.draw_board()
    time.sleep(5)  # Display for 5 seconds
    vis.close()