import pygame, sys
from screens.cover_screen import CoverScreen
from screens.explanation_screen import ExplanationScreen
from screens.main_menu_screen import MainMenuScreen
from screens.interaction_screen import LiveInteractionScreen
from screens.interferogram_screen import InterferogramScreen  # Assuming this is the same as interaction
from screens.base_screen import WHITE  # import background color

# Initialize Pygame
pygame.init()

# Windowed fullscreen (borderless window matching display resolution)
info = pygame.display.Info()
# SCREEN_W, SCREEN_H = 1920, 1080 
SCREEN_W, SCREEN_H = info.current_w, info.current_h
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.NOFRAME)

clock = pygame.time.Clock()

# State -> Screen instance mapping
screens = {
    'cover': CoverScreen(),
    'explanation': ExplanationScreen(),
    'main': MainMenuScreen(),
    'interaction': LiveInteractionScreen(),
    'interferogram': InterferogramScreen()  # Assuming this is the same as interaction'
}

state = 'cover'

while True:
    for ev in pygame.event.get():
        # Quit events
        if ev.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        # Global escape key to quit
        elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
            pygame.quit(); sys.exit()

        # Delegate event to current screen for navigation
        tgt = screens[state].handle_event(ev)
        if tgt:
            state = tgt

    # Clear screen before drawing new frame
    screen.fill(WHITE)
    # Render current screen
    screens[state].draw(screen)
    pygame.display.flip()
    # clock.tick(60)
