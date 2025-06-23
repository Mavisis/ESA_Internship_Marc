import pygame

import os

from screens.base_screen import Screen, Button, WHITE



class CoverScreen(Screen):

    def __init__(self):

        super().__init__('cover')

        images_dir = os.path.join(os.path.dirname(__file__), '..', 'images')

        bg_path = os.path.join(images_dir, 'main_menu.png')

        self.background = pygame.image.load(bg_path).convert()

        display_info = pygame.display.Info()

        self.background = pygame.transform.scale(

            self.background, (display_info.current_w, display_info.current_h)

        )

        # Define buttons

        self.buttons = []

        # Start -> main menu

        b1 = Button((100, 400, 200, 50), 'Start (1)', pygame.K_1)

        self.buttons.append((b1, 'main'))

        # Quit -> exit app

        b2 = Button((100, 500, 200, 50), 'Quit (Q)', pygame.K_q)

        self.buttons.append((b2, None))



    def draw(self, surface):

        surface.blit(self.background, (0, 0))

        for btn, _ in self.buttons:

            btn.draw(surface)

        return super().draw(surface)



    def handle_event(self, event):

        print(f"CoverScreen.handle_event: received {event}")

        if event.type == pygame.KEYDOWN:

            for btn, target in self.buttons:

                if btn.key_shortcut and event.key == btn.key_shortcut:

                    print(f"CoverScreen: switching to {target}")

                    if target is None:

                        pygame.event.post(pygame.event.Event(pygame.QUIT))

                        return None

                    self.next_state = target

                    return target

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

            for btn, target in self.buttons:

                if btn.is_clicked(event.pos):

                    print(f"CoverScreen: switching to {target}")

                    if target is None:

                        pygame.event.post(pygame.event.Event(pygame.QUIT))

                        return None

                    self.next_state = target

                    return target

        return None
