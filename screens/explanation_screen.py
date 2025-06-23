import pygame
import cv2
import numpy as np
import os
from screens.base_screen import Screen, Button, WHITE

class ExplanationScreen(Screen):
    def __init__(self):
        super().__init__('explanation')
        # ────── video setup ──────
        self.video_played     = False
        self.interrupt_playback = False
        self.video_path       = os.path.abspath(
            os.path.join(os.path.dirname(__file__),
                         '..', 'images', 'FULL_SAR_ANIMATION.mp4'))
        # ─── audio setup ───
        self.audio_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__),
                         '..', 'images', 'FULL_SAR_ANIMATION.wav'))
        pygame.mixer.init()

        # ─── UI setup ───
        self.font   = pygame.font.SysFont(None, 36)
        self.button = Button((100, 400, 250, 50),
                             'Continue to interferogram (3)',
                             pygame.K_3)

    def play_video(self, surface):
        # start audio
        try:
            pygame.mixer.music.load(self.audio_path)
            pygame.mixer.music.play()
        except Exception as e:
            print("Warning: could not play audio:", e)

        cap   = cv2.VideoCapture(self.video_path)
        clock = pygame.time.Clock()
        w, h  = surface.get_size()

        if not cap.isOpened():
            print("Error: Cannot open video file")
            return

        while cap.isOpened() and not self.interrupt_playback:
            ret, frame = cap.read()
            if not ret:
                break

            # BGR→RGB, resize, and blit directly
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (w, h))
            frame_surf = pygame.image.frombuffer(
                frame.tobytes(), (w, h), 'RGB'
            )

            surface.blit(frame_surf, (0, 0))
            pygame.display.update()

            # handle input
            for event in pygame.event.get():
                result = self.handle_event(event)
                if result == 'interferogram':
                    cap.release()
                    pygame.mixer.music.stop()
                    self.video_played = True
                    return
                elif self.interrupt_playback:
                    cap.release()
                    pygame.mixer.music.stop()
                    return

            # clock.tick(30)

        cap.release()
        pygame.mixer.music.stop()
        self.video_played = True

    def draw(self, surface):
        if not self.video_played:
            self.play_video(surface)
        return super().draw(surface)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_3:
                self.next_state = 'interferogram'
                return 'interferogram'
            elif event.key == pygame.K_q:
                self.interrupt_playback = True
        return None
