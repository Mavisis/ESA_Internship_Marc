import pygame



WHITE = (255, 255, 255)

BLUE = (0, 100, 255)



class Button:

    def __init__(self, rect, text, key_shortcut=None,

                 font=None, text_color=(255,255,255), bg_color=(0,51,102)):

        self.rect = pygame.Rect(rect)

        self.text = text

        self.key_shortcut = key_shortcut

        self.font = font or pygame.font.SysFont(None, 36)

        self.text_color = text_color

        self.bg_color = bg_color



    def draw(self, surface):

        pygame.draw.rect(surface, self.bg_color, self.rect)

        txt_surf = self.font.render(self.text, True, self.text_color)

        surface.blit(txt_surf, (

            self.rect.x + (self.rect.width - txt_surf.get_width()) // 2,

            self.rect.y + (self.rect.height - txt_surf.get_height()) // 2

        ))



    def is_clicked(self, pos):

        return self.rect.collidepoint(pos)



class Screen:

    def __init__(self, name):

        self.name = name

        self.next_state = None



    def handle_event(self, event):

        return None



    def draw(self, surface):

        if self.next_state:

            state = self.next_state

            self.next_state = None

            return state

        return None



class Text:

    def __init__(self, text, pos, font=None, color=(255, 255, 255)):

        self.text = text

        self.pos = pos  # (x, y)

        self.font = font or pygame.font.SysFont(None, 82)

        self.color = color

        self._rendered_text = self.font.render(self.text, True, self.color)



    def draw(self, surface):

        surface.blit(self._rendered_text, self.pos)



    def set_text(self, new_text):

        self.text = new_text

        self._rendered_text = self.font.render(self.text, True, self.color)



    def set_color(self, new_color):

        self.color = new_color

        self._rendered_text = self.font.render(self.text, True, self.color)



    def set_font(self, new_font):

        self.font = new_font

        self._rendered_te