import os

import pygame

import numpy as np

import cv2

from collections import deque

from pyk4a import PyK4A, Config, FPS

from pyk4a.calibration import DepthMode

from screens.base_screen import Screen, Text, WHITE

import pygame  # import Pygame for UI and event handling

import numpy as np  # import NumPy for numerical operations

import cv2  # import OpenCV for image processing

from collections import deque  # import deque for frame buffering

from screens.base_screen import Screen, Text, WHITE  # import base classes and constants

from pyk4a.calibration import DepthMode  # needed to specify depth mode

from pyk4a import FPS  # needed to specify camera FPS



class LiveInteractionScreen(Screen):

    def __init__(self):

        super().__init__('interaction')

        self.k4a = None

        self.running = False

        self.reference_frame = None

        self.frame_buffer = deque(maxlen=5)

        self.capture_counter = 0



        # default effective wavelength in millimeters (tunable via l/s/c keys)

        self.wavelength_mm = 50.0  # initial placeholder

        # synthetic geometry parameters

        self.B_perp    = 1.0      # baseline factor

        self.R_slant   = 0.40     # slant range [m]

        self.sin_theta = 1.0      # near-nadir

        self.update_scale()



        project_root = os.path.dirname(os.path.dirname(__file__))

        self.save_dir = os.path.join(project_root, 'captures')

        os.makedirs(self.save_dir, exist_ok=True)



        # font for control panel

        pygame.font.init()

        self.font = pygame.font.SysFont(None, 24)

        self.BLACK = (0, 0, 0)



    def update_scale(self):

        """Recompute the interferometric scale factor."""

        self.scale = (

            4 * np.pi * self.B_perp * self.sin_theta

        ) / (((self.wavelength_mm * 1e-3)) * self.R_slant)



    def start_kinect(self):
        print("LiveInteractionScreen: starting Kinect")

        self.k4a = PyK4A(
            Config(
                depth_mode=DepthMode.WFOV_UNBINNED,
                camera_fps=FPS.FPS_15,
                synchronized_images_only=False,
            )
        )
        self.k4a.start()
        self.running = True
        print(f"  using effective wavelength = {self.wavelength_mm} mm (scale={self.scale:.2e})")
        self.reference_frame = self.calibrate_reference()
            

    def calibrate_reference(self):

            cap = self.k4a.get_capture()  # safely get a new capture

            if cap.depth is None:

                raise RuntimeError("Failed to capture reference depth frame")  # guard against failures

            return cap.depth  # return raw depth array





    def phi_to_rgb(self, phi_wrap: np.ndarray) -> np.ndarray:

        norm = phi_wrap / (2 * np.pi)

        hue = (norm * 180).astype(np.uint8)

        hsv = np.zeros((phi_wrap.shape[0], phi_wrap.shape[1], 3), dtype=np.uint8)

        hsv[..., 0] = hue

        hsv[..., 1] = 255

        hsv[..., 2] = 255

        return cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)



    def draw(self, surface):

        if not self.running:

            self.start_kinect()  # ensure Kinect is active before drawing





        width, height = surface.get_width(), surface.get_height()

        side = height  # make square of full window height

        panel_width = width - side



        # capture and process depth

        cap = self.k4a.get_capture()

        depth = cap.depth

        if depth is not None:

            self.frame_buffer.append(depth)

            if len(self.frame_buffer) == self.frame_buffer.maxlen:

                avg = np.mean(self.frame_buffer, axis=0).astype(np.float32)

                mask = (avg > 0) & (self.reference_frame > 0)

                diff_mm = np.where(mask, avg - self.reference_frame, 0.0)

                diff_mm[np.abs(diff_mm) < 2.0] = 0.0



                delta_h = diff_mm * 1e-3

                delta_phi = self.scale * delta_h

                phi_wrap = np.mod(delta_phi, 2 * np.pi)



                fringe_rgb = self.phi_to_rgb(phi_wrap)

                img = cv2.resize(fringe_rgb, (side, side))

                self.last_image = img



        # draw the left square image

        if hasattr(self, 'last_image'):

            surf_img = pygame.surfarray.make_surface(np.transpose(self.last_image, (1, 0, 2)))

            surface.blit(surf_img, (0, 0))



        # draw the right control panel

        if panel_width > 0:

            panel_rect = pygame.Rect(side, 0, panel_width, height)

            pygame.draw.rect(surface, self.BLACK, panel_rect)



            font = pygame.font.SysFont("consolas", 32, bold=False)



            # Define header and footer

            left_header = Text("Frequency Control", pos=(0, 0), font=font, color=WHITE)

            right_header = Text("Menu Controls", pos=(0, 0), font=font, color=WHITE)

            footer = Text(f"Current λ: {self.wavelength_mm:.1f} mm", pos=(0, 0), font=font, color=WHITE)



            # Define columns

            left_col_lines = [

                "",

                "L → λ = 236 mm",

                "S → λ = 96 mm",

                "C → λ = 56 mm",

                "+ → Increase λ",

                "- → Decrease λ",

                ""

            ]

            right_col_lines = [

                "",

                "R → Recalibrate",

                "P → Save image",

                "Q → Quit"

            ]



            left_texts = [Text(line, pos=(0, 0), font=font, color=WHITE) for line in left_col_lines]

            right_texts = [Text(line, pos=(0, 0), font=font, color=WHITE) for line in right_col_lines]



            line_height = font.get_height() + 10

            col_spacing = 40

            col_width = (panel_width - col_spacing) // 2



            total_rows = max(len(left_texts), len(right_texts))

            total_text_height = (total_rows + 3) * line_height  # +3: 2 headers + 1 footer

            start_y = (height - total_text_height) // 2



            # Draw headers

            left_header_x = side + (col_width - font.size(left_header.text)[0]) // 2

            left_header.pos = (left_header_x, start_y)

            left_header.draw(surface)



            right_header_x = side + col_width + col_spacing + (col_width - font.size(right_header.text)[0]) // 2

            right_header.pos = (right_header_x, start_y)

            right_header.draw(surface)



            # Draw left and right columns

            y = start_y + line_height

            for i in range(total_rows):

                if i < len(left_texts):

                    left_x = side + (col_width - font.size(left_texts[i].text)[0]) // 2

                    left_texts[i].pos = (left_x, y)

                    left_texts[i].draw(surface)

                if i < len(right_texts):

                    right_x = side + col_width + col_spacing + (col_width - font.size(right_texts[i].text)[0]) // 2

                    right_texts[i].pos = (right_x, y)

                    right_texts[i].draw(surface)

                y += line_height



            # Draw footer

            footer_x = side + (panel_width - font.size(footer.text)[0]) // 2

            footer.pos = (footer_x, y)

            footer.draw(surface)



        return super().draw(surface)



    def handle_event(self, event):

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_q:

                print("LiveInteractionScreen: stopping Kinect and returning to main")

                self.running = False

                if self.k4a:

                    self.k4a.stop()

                    self.k4a = None

                self.next_state = 'main'

                return 'main'



            elif event.key == pygame.K_r:

                print("LiveInteractionScreen: recalibrating reference")

                self.reference_frame = self.calibrate_reference()



            elif event.key == pygame.K_l:

                self.wavelength_mm = 236.0

                self.update_scale()

                print(f"LiveInteractionScreen: wavelength set to {self.wavelength_mm} mm")



            elif event.key == pygame.K_s:

                self.wavelength_mm = 96.0

                self.update_scale()

                print(f"LiveInteractionScreen: wavelength set to {self.wavelength_mm} mm")



            elif event.key == pygame.K_c:

                self.wavelength_mm = 56.0

                self.update_scale()

                print(f"LiveInteractionScreen: wavelength set to {self.wavelength_mm} mm")



            elif event.key in (pygame.K_PLUS, pygame.K_KP_PLUS):

                self.wavelength_mm = min(self.wavelength_mm + 5.0, 500.0)

                self.update_scale()

                print(f"LiveInteractionScreen: wavelength increased to {self.wavelength_mm} mm")



            elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):

                self.wavelength_mm = max(self.wavelength_mm - 5.0, 0.00001)

                self.update_scale()

                print(f"LiveInteractionScreen: wavelength decreased to {self.wavelength_mm} mm")



            elif event.key == pygame.K_p:

                if hasattr(self, 'last_image'):

                    filename = os.path.join(self.save_dir, f'interferogram_{self.capture_counter:03d}.png')

                    cv2.imwrite(filename, cv2.cvtColor(self.last_image, cv2.COLOR_RGB2BGR))

                    print(f"LiveInteractionScreen: saved {filename}")

                    self.capture_counter += 1



        return None
