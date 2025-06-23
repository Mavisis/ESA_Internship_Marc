import os

import time

import pygame

import numpy as np

import cv2

from datetime import datetime

from multiprocessing import Process, Queue

from pyk4a import PyK4A, Config, FPS

from pyk4a.calibration import DepthMode

from screens.base_screen import Screen, WHITE

import pygame  # import Pygame for UI

import numpy as np  # import NumPy for numerical computations

import cv2  # import OpenCV for image conversions

from multiprocessing import Process, Queue  # import for feedback subprocess

from screens.base_screen import Screen, WHITE  # import base Screen and color constants

from pyk4a.calibration import DepthMode  # needed to specify depth mode

from pyk4a import FPS  # needed to specify camera FPS

from matplotlib import cm
import random



def feedback_process(queue: Queue, position=(100, 100), size=(400, 400)):

    os.environ['SDL_VIDEO_WINDOW_POS'] = f"{position[0]},{position[1]}"

    pygame.init()

    screen = pygame.display.set_mode(size, pygame.NOFRAME)

    pygame.display.set_caption("Feedback")



    color = [255, 255, 255]

    target_color = [255, 255, 255]

    fade_start_time = None

    fade_duration = 2.0  # seconds

    clock = pygame.time.Clock()

    running = True



    while running:

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                running = False



        # Check for transition signal

        if not queue.empty():

            msg = queue.get()

            if msg == "trigger":

                fade_start_time = time.time()

                color = [255, 0, 0]

                target_color = [0, 255, 0]



        # Handle fade

        if fade_start_time is not None:

            t = time.time() - fade_start_time

            if t >= fade_duration:

                color = [255, 255, 255]

                fade_start_time = None

            else:

                progress = t / fade_duration

                color = [

                    int(255 * (1 - progress)),

                    int(255 * progress),

                    0

                ]



        screen.fill(color)

        pygame.display.flip()

        clock.tick(60)



    pygame.quit()





class InterferogramScreen(Screen):

    def __init__(self):

        super().__init__('interferogram')

        # Kinect setup

        self.k4a = PyK4A(Config(

            depth_mode=DepthMode.WFOV_UNBINNED,

            camera_fps=FPS.FPS_15,

            synchronized_images_only=False

        ))

        self.k4a.start()



        # Feedback process communication

        self.feedback_queue = Queue()

        self.feedback_proc = Process(target=feedback_process, args=(self.feedback_queue, (1920, 0)))

        self.feedback_proc.start()



        # Frame averaging & processing

        self.FRAME_AVG_COUNT = 15

        self.UPSCALE_FACTOR = 2

        self.MAX_DISPLAY_DEPTH_MM = 300

        self.INTERFERO_WAVELENGTH = 7.0



        # State

        self.clock = pygame.time.Clock()

        self.display_mode = 'instructions'

        self.previous_mode = None

        self.instr_timer = pygame.time.get_ticks()

        self.ref_depth_map = None

        self.cur_depth_map = None

        self.interfero_surf = None

        self.spinner_angle = 0.0



        # Fonts

        pygame.font.init()

        self.font_big = pygame.font.SysFont(None, 48)

        self.font_small = pygame.font.SysFont(None, 32)



        # Static texts

        self.header_text = 'Interferogram Workflow'

        self.footer_text = 'Q - Quit'



    def capture_and_average_depth(self, count, upscale):

        frames = []

        for _ in range(count):

            cap = self.k4a.get_capture()

            if cap.depth is not None:

                frames.append(cap.depth.astype(np.float32))

        ups = [cv2.resize(f, (f.shape[1]*upscale, f.shape[0]*upscale), interpolation=cv2.INTER_CUBIC)

               for f in frames]

        return np.mean(ups, axis=0).astype(np.int32)



    def compute_interferogram_surface(self, ref_map, cur_map):

        dz = cur_map.astype(np.float32) - ref_map.astype(np.float32)

        dz[np.abs(dz) < 1] = 0

        phase = np.angle(np.exp(1j * (4 * np.pi / self.INTERFERO_WAVELENGTH) * dz))

        normed = (phase + np.pi) / (2 * np.pi)

        h = (normed * 179).astype(np.uint8)

        s = np.full_like(h, 255)

        v = np.full_like(h, 255)

        hsv = cv2.merge([h, s, v])

        rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

        surf = pygame.surfarray.make_surface(rgb.swapaxes(0,1))

        return surf



    def draw_spinner(self, surface):

        self.spinner_angle += 0.1

        r, x, y = 20, 50, self.height - 50

        rect = pygame.Rect(x-r, y-r, 2*r, 2*r)

        pygame.draw.arc(surface, WHITE, rect,

                        self.spinner_angle,

                        self.spinner_angle + np.pi*1.5, 4)



    def draw_clock(self, surface):

        now = datetime.now().strftime('%H:%M:%S')

        txt = self.font_small.render(now, True, WHITE)

        surface.blit(txt, (self.width - txt.get_width() - 20, 20))



    def get_middle_prompt(self):

        if self.display_mode == 'instructions':

            return ['Step 1:', '', 'Press 1 to capture', '','REFERENCE depth']

        elif self.display_mode == 'reference':

            return ['Step 2:','', 'Press 2 to capture','', 'CURRENT depth']

        elif self.display_mode == 'current':

            return ['Step 3:','', 'Press 3 to compute', '','INTERFEROGRAM']

        elif self.display_mode == 'interferogram':

            return ['Interferogram ready','', 'Press W for live view' ,'','Press R to reset']

        elif self.display_mode == 'live':

            return ['Live stream active','', 'Press R to restart workflow']

        return []



    def depth_to_surface(self, depth_map, size):

        gray = np.zeros_like(depth_map, dtype=np.uint8)

        mask = depth_map > 0

        clipped = np.minimum(depth_map.astype(np.float32), self.MAX_DISPLAY_DEPTH_MM)

        normed = ((1.0 - clipped / self.MAX_DISPLAY_DEPTH_MM) * 255).astype(np.uint8)

        gray[mask] = normed[mask]

        rgb = np.stack([gray]*3, axis=2)

        surf = pygame.surfarray.make_surface(rgb.swapaxes(0,1))

        return pygame.transform.scale(surf, (size, size))

    
    # def depth_to_surface(self, depth_map, size):
    #     # Create empty RGB array
    #     color_map = np.zeros((*depth_map.shape, 3), dtype=np.uint8)
        
    #     mask = depth_map > 0
    #     clipped = np.minimum(depth_map.astype(np.float32), self.MAX_DISPLAY_DEPTH_MM)
    #     normed = ((1.0 - clipped / self.MAX_DISPLAY_DEPTH_MM) * 255).astype(np.uint8)
        
    #     # Apply a colormap - here's an example using a jet-like colormap
    #     # Blue (low values) to Red (high values)
    #     for y in range(depth_map.shape[0]):
    #         for x in range(depth_map.shape[1]):
    #             if mask[y, x]:
    #                 value = normed[y, x]
    #                 if value < 128:
    #                     # Blue to Cyan transition
    #                     color_map[y, x, 0] = 0
    #                     color_map[y, x, 1] = value * 2
    #                     color_map[y, x, 2] = 255
    #                 else:
    #                     # Cyan to Red transition
    #                     color_map[y, x, 0] = (value - 128) * 2
    #                     color_map[y, x, 1] = 255 - (value - 128) * 2
    #                     color_map[y, x, 2] = 255 - (value - 128) * 2
        
    #     surf = pygame.surfarray.make_surface(color_map.swapaxes(0,1))
    #     return pygame.transform.scale(surf, (size, size))


    def draw(self, surface):

        self.width, self.height = surface.get_width(), surface.get_height()

        square_side = self.height

        panel_width = self.width - square_side

        surface.fill((0,0,0))



# Left: visualization (ORIGINAL FUNCTIONALITY - UNTOUCHED)
        out_surf = None

        if self.display_mode == 'instructions':
            out_surf = None
        elif self.display_mode == 'reference' and self.ref_depth_map is not None:
            out_surf = self.depth_to_surface(self.ref_depth_map, square_side)
        elif self.display_mode == 'current' and self.cur_depth_map is not None:
            out_surf = self.depth_to_surface(self.cur_depth_map, square_side)
        elif self.display_mode == 'interferogram' and self.interfero_surf is not None:
            out_surf = pygame.transform.scale(self.interfero_surf, (square_side, square_side))
        elif self.display_mode == 'live':
            cap = self.k4a.get_capture()
            if cap.depth is not None:
                up = cv2.resize(cap.depth.astype(np.float32),
                                (cap.depth.shape[1]*self.UPSCALE_FACTOR, cap.depth.shape[0]*self.UPSCALE_FACTOR),
                                interpolation=cv2.INTER_CUBIC).astype(np.int32)
                out_surf = self.depth_to_surface(up, square_side)

        # Draw original content
        if out_surf:
            surface.blit(out_surf, (0,0))


        # Right panel

        panel_rect = pygame.Rect(square_side, 0, panel_width, self.height)

        pygame.draw.rect(surface, (0,0,0), panel_rect)

        header_surf = self.font_small.render(self.header_text, True, WHITE)

        surface.blit(header_surf, (square_side + (panel_width - header_surf.get_width())//2, 20))

        lines = self.get_middle_prompt()

        line_surfs = [self.font_big.render(line, True, WHITE) for line in lines]

        total_h = sum(s.get_height() for s in line_surfs)

        start_y = (self.height - total_h) // 2

        for i, surf in enumerate(line_surfs):

            x = square_side + (panel_width - surf.get_width()) // 2

            y = start_y + sum(s.get_height() for s in line_surfs[:i])

            surface.blit(surf, (x, y))

        foot_surf = self.font_small.render(self.footer_text, True, WHITE)

        foot_y = self.height - foot_surf.get_height() - 20

        surface.blit(foot_surf, (square_side + (panel_width - foot_surf.get_width())//2, foot_y))



        # overlays

        self.draw_spinner(surface)

        self.draw_clock(surface)

        return super().draw(surface)



    def handle_event(self, event):

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_q:

                self.feedback_proc.terminate()

                self.k4a.stop()

                self.next_state = 'main'

                return 'main'

            elif event.key == pygame.K_1:

                self.ref_depth_map = self.capture_and_average_depth(self.FRAME_AVG_COUNT, self.UPSCALE_FACTOR)

                self.display_mode = 'reference'

                self.feedback_queue.put("trigger")

            elif event.key == pygame.K_2:

                self.cur_depth_map = self.capture_and_average_depth(self.FRAME_AVG_COUNT, self.UPSCALE_FACTOR)

                self.display_mode = 'current'

                self.feedback_queue.put("trigger")

            elif event.key == pygame.K_3 and self.ref_depth_map is not None and self.cur_depth_map is not None:

                self.interfero_surf = self.compute_interferogram_surface(self.ref_depth_map, self.cur_depth_map)

                self.display_mode = 'interferogram'

            elif event.key == pygame.K_w:

                self.feedback_proc.terminate()

                self.k4a.stop()

                self.k4a = None

                self.next_state = 'interaction'

                return 'interaction'

            elif event.key == pygame.K_r:

                self.ref_depth_map = None

                self.cur_depth_map = None

                self.interfero_surf = None

                self.display_mode = 'instructions'

                self.instr_timer = pygame.time.get_ticks()

        return None