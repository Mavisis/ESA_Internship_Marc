import pygame

import os

from screens.base_screen import Screen, Button, BLUE, WHITE



class MainMenuScreen(Screen):

    def __init__(self):

        super().__init__('main')

        project_root = os.path.dirname(os.path.dirname(__file__))

        image_path = os.path.join(project_root, 'images', 'main_menu.png')

        self.background = pygame.image.load(image_path).convert()

        display_info = pygame.display.Info()

        self.background = pygame.transform.scale(

            self.background, (display_info.current_w, display_info.current_h)

        )

        # Define buttons

        self.buttons = []

        b1 = Button((100, 300, 300, 50), 'Live Interaction (L)', pygame.K_l)

        self.buttons.append((b1, 'interaction'))

        b2 = Button((100, 400, 300, 50), 'Explanation (E)', pygame.K_e)

        self.buttons.append((b2, 'explanation'))

        b3 = Button((100, 500, 300, 50), 'Back to Cover (C)', pygame.K_c)

        self.buttons.append((b3, 'cover'))



    def draw(self, surface):

        surface.blit(self.background, (0, 0))

        title = pygame.font.SysFont(None, 48).render('Main Menu', True, BLUE)

        surface.blit(title, ((surface.get_width() - title.get_width()) // 2, 100))

        instr = pygame.font.SysFont(None, 36).render('Select an option:', True, (0, 0, 0))

        surface.blit(instr, (100, 200))

        for btn, _ in self.buttons:

            btn.draw(surface)

        return super().draw(surface)



    def handle_event(self, event):

        print(f"MainMenuScreen.handle_event: received {event}")

        if event.type == pygame.KEYDOWN:

            for btn, state in self.buttons:

                if btn.key_shortcut and event.key == btn.key_shortcut:

                    print(f"MainMenuScreen: switching to {state}")

                    self.next_state = state

                    return state

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

            for btn, state in self.buttons:

                if btn.is_clicked(event.pos):

                    print(f"MainMenuScreen: switching to {state}")

                    self.next_state = state

                    return state

        return None
