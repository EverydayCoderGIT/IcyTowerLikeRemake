#region Imports
#pygame
import pygame
from pygame import event, surface, display, image, Rect, time, mixer, font
from pygame.key import ScancodeWrapper
from pygame.time import Clock
from pygame.surface import SurfaceType

# Path
from os import path

# Typing
from typing import Union

# Class types
from enum import Enum
from dataclasses import dataclass

# Math
import random
import numpy as np
import math
#endregion

@dataclass
class configuration:

    # Window and background
    # Set the window size
    window_size : (float, float) = (500, 700)
    # FPS settings
    target_FPS : float = 60
    # Screen title
    title : str = "Icy Tower Python Remake"
    # Background image
    background_image_path : str = './assets/BackgroundGradient.png'

    # Audio and music
    background_music_path : str = './assets/jump_higher_run_faster.ogg'


    # Player

    # Character sprite sheet
    character_sprite_sheet: str = r'.\assets\character.png'
    # Character sprite sheet offset
    character_sprite_offset: (float, float) = (0, 13)
    # Character sprite sheet size
    character_sprite_sheet_size: (float, float) = (37, 51)
    # Player max jump height
    max_jump_height = 150
    # Player horizontal movement speed
    horizontal_movement_speed : float = 0.5
    # Player vertical movement speed
    vertical_movement_speed : float = 1.0
    # How many sprite sheet updates of the character should be updated each second
    character_sprite_fps: float = 12

    # Platform

    # Platform sprite path
    platform_sprite_path: str = r'.\assets\tile_00.png'
    # Platform texture size
    platform_texture_size: (float, float) = (64, 64)
    # Platform texture render height (It as assumed to be square so only one dimension is defined)
    platform_render_height: float = 40
    # Platform vertical movement speed
    platform_speed = 0.04
    # Procedural generation limits
    platform_random_factor: (float, float) = (0.2, 0.8)
    # Increment after number of platforms passed
    level_number_of_platforms = 5
    # Number of platforms to skip between each two platforms
    skip_platform_count : int = 4
    # Number of platforms per screen
    number_of_platforms: int = 4

    # Score  control
    # Score font color
    score_font_color : (float,float,float) = (255,0,0)
    # Score panel background color
    score_panel_background_color : (float,float,float) = (0,0,0)
    # Booster threshold
    booster_threshold: float = 0.5 * 1000  # ms
    # Booster lifetime
    booster_lifetime: float = 5 * 1000 # ms
    # Font size
    font_size : int = 36
    # Score coordinates
    score_coordinates : (float,float) = (0,10)
    # Score data file path
    score_data_file_path : str = r'./score_data.dat'
    # game over screen coordinates
    game_over_coordinates : (float,float) = (30,300)

#region Platform
@dataclass
class Platform:
    """
    Platform data

    <------------------------width-------------------------->

    (x,y)---------------Top y-coordinate--------------------      /\
    |                                                       |     ||
    |                                                       |     ||
    |                                                       |     ||
    x-Left coordinate                       Right x-coordinate   height
    |                                                       |     ||
    |                                                       |     ||
    |                                                       |     ||
    |-------------------Bottom y-coordinate-----------------|     \/
    """
    x_coord : float = 100 # X coordinate of the platform
    y_coord : float = 400 # Y coordinate of the platform
    width : float = 100 # Width of the platform
    height : float = 40 # Height of the platform
    platform_color : (float,float,float) = (255,0,0) # Color of the platform (Used only for debugging
    in_view : bool = True # A boolean value to indicate if the platform is in the player view
    visited_by_player : bool = False # Used for score calculation

    # Internal attributes
    _bottom : float = y_coord + height # Bottom coordinate of the platfrom
    _top : float = y_coord # Top coordinate of the platform
    _right : float = x_coord + width # Right coordinate of the platform
    _left : float = x_coord # Left coordinate of the platform


    # Properties
    @property
    def top(self) -> float:
        """
        :return:  top y-coordinate as float
        """
        self._top = self.y_coord
        return self._top

    @property
    def right(self) -> float:
        """
        :return: right x-coordinate as float
        """
        self._right = self.x_coord + self.width
        return self._right

    @property
    def left(self) -> float:
        """
        :return: left x-coordinate as float
        """
        self._left = self.x_coord
        return self._left

    @property
    def bottom(self):
        """
        :return: right x-coordinate as float
        """
        self._bottom = self.y_coord + self.height
        return self._bottom
class PlatformManager:

    def __init__(self, window : surface):
        # Platform list
        self.platforms : list[Platform] = list()

        # Window and screen variables
        self.window : window = window
        self.window_size : (float,float) = self.window.get_size()

        # Platform geometries
        self.max_platform_width : float = configuration.platform_random_factor[1] * self.window_size[0]
        self.min_platform_width : float = configuration.platform_random_factor[0] * self.window_size[0]
        self.platform_height : float = configuration.platform_render_height

        # Procedural generation settings
        self.side_left : bool = random.choice([True,False])
        self.side : bool = random.choice([True,False])
        self.skip_platform_count : int = configuration.skip_platform_count
        self.platform_speed : float = configuration.platform_speed

        # Load platform texture
        self.platform_texture : surface = image.load(configuration.platform_sprite_path)
        self.platform_texture_size : (float, float) = configuration.platform_texture_size

        # Initialize the first set platforms
        self.update_and_return_platforms()


    def add_platform(self, y_coord : float = 0):
        random_platform_width : float = random.uniform(self.min_platform_width, self.max_platform_width)
        width : float = math.ceil(random_platform_width/ self.platform_height) * self.platform_height
        x_coord : float = 0
        if (self.side):
            if self.side_left:
                x_coord = 0
            else:
                x_coord = self.window_size[0] - width
            self.side_left = not self.side_left  #
        else:
            x_coord = self.window_size[0] / 2 - width / 2
        self.side = not self.side

        self.platforms.append(Platform(x_coord=x_coord, y_coord=y_coord, width=width, height=self.platform_height))

    def update_and_return_platforms(self, delta : float = 1/60*1000, speed_multiplier : float = 1, update_position : bool = False):

        if self.platforms == []:
            for platform_i in np.arange(1,configuration.number_of_platforms * self.skip_platform_count,self.skip_platform_count):
                y_coord : float = platform_i * self.platform_height
                self.add_platform(y_coord=y_coord)
        else:
            if update_position:
                for platform in self.platforms:
                    platform.y_coord += configuration.platform_speed * speed_multiplier * delta
                    if platform.y_coord >= self.window_size[1]:
                        self.platforms.remove(platform)
                        self.add_platform(y_coord=self.platform_height)

    def render_platforms(self):
        # Scale the sprite to the desired tile size
        scaled_sprite : surface = pygame.transform.scale(self.platform_texture, (self.platform_height, self.platform_height))

        for platform in self.platforms:
            for x_coord in np.arange(platform.x_coord,platform.x_coord + platform.width,platform.height):
                self.window.blit(scaled_sprite,(x_coord,platform.y_coord))

            #pygame.draw.rect(self.window,
            #                 platform.platform_color, Rect(platform.x_coord,
            #                                                     platform.y_coord,
            #                                                     platform.width,
            #                                                     platform.height))
#endregion

#region Player
class PlayerAnimationState(Enum):
    idle = "idle"
    moving_right = "moving_right"
    moving_left = "moving_left"
    jumping_up_right = "jumping_up_right"
    jumping_up_left = "jumping_up_left"
    jumping_up_or_down = "jumping_up_or_down"
class PlayerAnimations:

    def __init__(self):
        # General properties
        self.sprite_offset: (float, float) = configuration.character_sprite_offset
        self.player_sprite_path: str = configuration.character_sprite_sheet
        self.player_size : (float,float) = configuration.character_sprite_sheet_size
        self.character_sprite_fps: float = configuration.character_sprite_fps # frames per second for the spritesheet

        # Character sprite control
        self.character_sprite_timer : float = 0  # in ms
        self.character_animation_pointer: int = 0
        self.current_player_sprite : surface = None
        self.character_sprite: surface = None
        self.character_animations_frames : dict = {}
        self.animations_key_in_sprite_sheet = {"idle" : ((4,0),3, False),
                                               "moving_right" : ((112,0),4, False),
                                               "moving_left": ((112, 0), 4, True),
                                               "jumping_up_right" : ((265, 0),4, False),
                                               "jumping_up_left": ((265, 0), 4, True),
                                               "jumping_up_or_down": ((265,0), 1,  False)}

        self._current_running_animation : PlayerAnimationState = PlayerAnimationState.moving_left

        # Animations
        self.load_animations()

    def load_sprite_sheet(self) -> Union[SurfaceType]:

        # Load the sprite sheet
        sprite_sheet = image.load(self.player_sprite_path).convert_alpha()

        # Return the sprite sheet
        return sprite_sheet

    def get_sprite(self, sheet : surface, rectangle : (float,float,float,float)) -> surface:
        """Extracts a single sprite from a sprite sheet.

        Args:
            sheet: The loaded sprite sheet.
            rectangle: A tuple (x, y, width, height) representing the area to extract.

        Returns:
            A Pygame surface representing the extracted sprite.
        """
        rect = Rect(rectangle)
        sprite = surface.Surface(rect.size, pygame.SRCALPHA)
        sprite.blit(sheet, (0, 0), rect)
        return sprite

    def extract_frames(self, sprite_sheet : surface, offset_x : float, offset_Y : float,
                       frame_width : float, frame_height : float, num_frames : int, flip_vertical : bool = False) -> list[surface]:
        frames : list[surface] = []
        for i in range(num_frames):
            frame_rect : (float,float,float,float) = (offset_x + i * (frame_width + self.sprite_offset[0]), 
                          offset_Y + self.sprite_offset[1],
                          frame_width,
                          frame_height)
            frame_sprite : surface = self.get_sprite(sprite_sheet, frame_rect)
            frame_sprite : surface = pygame.transform.flip(frame_sprite, flip_vertical, False)
            frame_sprite.set_colorkey((111, 49, 152))
            frames.append(frame_sprite)
        return frames

    def load_animations(self) -> None:
        sprite_sheet : surface = self.load_sprite_sheet()

        for animation in PlayerAnimationState:
            self.character_animations_frames[animation.value] = self.extract_frames(
                                                       sprite_sheet=sprite_sheet,
                                                       offset_x=self.animations_key_in_sprite_sheet[animation.value][0][0],
                                                       offset_Y=self.animations_key_in_sprite_sheet[animation.value][0][1],
                                                       frame_width=self.player_size[0],
                                                       frame_height=self.player_size[1],
                                                       num_frames=self.animations_key_in_sprite_sheet[animation.value][1],
                                                       flip_vertical= self.animations_key_in_sprite_sheet[animation.value][2])

    def update_player_sprite(self, delta : float) -> surface:
        self.character_sprite_timer += delta

        if self.character_sprite_timer >= 1/self.character_sprite_fps * 1000:
            if self.character_animation_pointer < len(self.character_animations_frames[self._current_running_animation.value]) - 1:
                self.character_animation_pointer += 1
            else:
                self.character_animation_pointer = 0
            self.character_sprite_timer = 0

        self.current_player_sprite = self.character_animations_frames[self._current_running_animation.value][self.character_animation_pointer]

        return self.current_player_sprite

    def change_animation_state(self, new_animation_state : PlayerAnimationState) -> None:
        if not self._current_running_animation == new_animation_state:
            self._current_running_animation = new_animation_state
            self.character_animation_pointer = 0
class PlayerMovementState(Enum):
    idle = 0
    moving_right = 1
    moving_left = 2
class PlayerJumpState(Enum):
    idle = 0
    jumping_up = 1
    jumping_down = 2

class PlayerScoreControl:

    def __init__(self, window : surface):

        #private attributes
        self._high_score : int = 0
        self._booster_threshold : float = configuration.booster_threshold
        self._window : surface= window
        self._timestamp : float = 0
        self._last_score_inc_stamp : float = 0
        self._booster_enabled_time_stamp : float = 0
        self._booster_on : bool = False
        self._current_score : int = 0
        self._current_score_increment : int = 10
        self._current_score_multiplier : int = 1
        self._number_visited_platforms_since_last_speed_mult_inc : int = 0
        self._speed_multiplier : float = 1
        self._level : int = 1
        self._tmp_speed_multiplier : float = 0
        self._paused : bool = False

        self._load_score_data()

    def _load_score_data(self):
        if path.exists(configuration.score_data_file_path):
            with open(configuration.score_data_file_path, 'r') as score_data_file_path:
                high_score = score_data_file_path.read()
            if high_score.isdigit():
                self._high_score = int(high_score)
            else:
                self._high_score = 0
        else:
            self._high_score = 0

    def check_and_save_high_score(self):
        if self._current_score > self._high_score:
            with open(configuration.score_data_file_path, 'w') as score_data_file_path:
                score_data_file_path.write(str(self._current_score))

    def pause_game(self):
        self._paused = True
        self._tmp_speed_multiplier = self._speed_multiplier
        self._speed_multiplier = 0

    def resume_game(self):
        self._paused = False
        self._speed_multiplier = self._tmp_speed_multiplier

    def update_score(self, delta : float):
        self._timestamp += delta
        if self._booster_on and ((self._timestamp - self._booster_enabled_time_stamp) > configuration.booster_lifetime):
            self._booster_on = False

    def increment_score_increment(self):
        self._current_score_multiplier *= 2

    def increment_score(self):
        self._current_score += self._current_score_increment * self._current_score_multiplier
        if ((self._timestamp - self._last_score_inc_stamp) <= self._booster_threshold):
            self._booster_on = True
            self._booster_enabled_time_stamp = self._timestamp
        self._last_score_inc_stamp = self._timestamp

        if  self._number_visited_platforms_since_last_speed_mult_inc >= configuration.level_number_of_platforms:
            self._number_visited_platforms_since_last_speed_mult_inc = 0
            self._speed_multiplier = np.round(self._speed_multiplier * 1.2,1)
            self._level += 1
        else:
            self._number_visited_platforms_since_last_speed_mult_inc += 1

    @property
    def get_score(self) -> int:
        return self._current_score

    @property
    def get_speed_multiplier(self) -> float:
        return self._speed_multiplier

    @property
    def is_paused(self) -> bool:
        return self._paused

    @property
    def get_high_score(self) -> int:
        return self._high_score

    def render_score(self) -> None:
        # Choose a font and size
        font = pygame.font.Font(None, configuration.font_size)

        # Render background rectangle
        pygame.draw.rect(self._window, configuration.score_panel_background_color, (0,0,configuration.window_size[0], configuration.platform_render_height))

        # Render the text into an image (Surface)
        #text_surface = font.render(f'Score : {self._current_score} Level : {self._level} Booster : {"ON" if self._booster_on else "OFF"}', True, configuration.score_font_color)
        text_surface = font.render(f'Score : {self._current_score} Level : {self._level} Speed X : {self._speed_multiplier}',
                                   True, configuration.score_font_color)

        self._window.blit(text_surface, configuration.score_coordinates)

class Player:

    def __init__(self, window : surface, platform_manager : PlatformManager):

        # General settings
        self.window : surface = window
        self.platform_manager : PlatformManager = platform_manager
        self.window_size = self.window.get_size()
        self.move_platforms : bool = False

        # Player draw settings
        self.player_color : (float,float,float) = (255, 255, 255)  # White, used only for debugging
        self.player_size : (float,float) = configuration.character_sprite_sheet_size

        # Player coordinates
        self.x_coord : float = self.player_size[0]
        self.y_coord : float = self.window_size[1] - self.player_size[1]

        # Player movement settings
        self.tmp_jump_height : float = 0
        self.max_jump_height : float = configuration.max_jump_height
        self.horizontal_movement_speed : float = configuration.horizontal_movement_speed
        self.vertical_movement_speed : float = configuration.vertical_movement_speed

        # Player movement state
        self.player_movement_state : PlayerMovementState = PlayerMovementState.idle
        self.player_jumping_state : PlayerJumpState = PlayerJumpState.idle
        self.allow_jumping : bool = True

        # Character sprite
        self.character_animation_controller : PlayerAnimations =  PlayerAnimations()
        self.character_sprite : surface = None

        # Score control
        self.score_controller = PlayerScoreControl(self.window)

    def player_key_press(self, keys : ScancodeWrapper):
        if self.score_controller.is_paused:
            return

        self.player_movement_state = PlayerMovementState.idle

        if keys[pygame.K_RIGHT]:
            self.player_movement_state = PlayerMovementState.moving_right

        if keys[pygame.K_LEFT]:
            self.player_movement_state = PlayerMovementState.moving_left

        if keys[pygame.K_SPACE]:
            if not self.move_platforms:
                self.move_platforms = True
            if self.allow_jumping == True:
                self.player_jumping_state = PlayerJumpState.jumping_up
                self.tmp_jump_height = 0
                self.allow_jumping = False

    def update_player_outer_bounds(self):
        self.left : float = self.x_coord
        self.top : float = self.y_coord
        self.right : float = self.x_coord + self.player_size[0]
        self.bottom : float = self.y_coord + self.player_size[1]

    def check_frame_collision(self):
        if self.bottom >= self.window_size[1]:
            self.y_coord = self.window_size[1] - self.player_size[1]
            self.allow_jumping = True
            if self.move_platforms:
                self.score_controller.pause_game()
                self.score_controller.check_and_save_high_score()
                self.render_game_over()

        if self.right >= self.window_size[0]:
            self.allow_jumping = True
            self.tmp_jump_height = 0
            self.player_jumping_state = PlayerJumpState.jumping_down
            self.x_coord = self.window_size[0] - self.player_size[0]
        if self.left <= 0:
            self.allow_jumping = True
            self.tmp_jump_height = 0
            self.x_coord = 0
            self.player_jumping_state = PlayerJumpState.jumping_down

    def check_platform_collision_bottom(self, platform : Platform) -> None:
        """
        Adjusts the player y-coordinate based on collision with the given platform from the top side
        :param platform: the target platform
        :return: None
        """
        if self.top <= platform.bottom and self.top >= platform.top:
            if (self.left <= platform.right and self.left >= platform.left) or\
                    (self.right >= platform.left and self.right <= platform.right):
                self.y_coord = platform.bottom + self.player_size[1]
                self.player_jumping_state = PlayerJumpState.jumping_down

    def check_platform_collision_top(self, platform : Platform) -> None:
        """
        Adjusts the player y-coordinate based on collision with the given platform from the down side
        :param platform: the target platform
        :return: None
        """
        if self.top >= platform.top - self.player_size[1] and self.bottom <= platform.bottom:
            if (self.left <= platform.right and self.left >= platform.left) or\
                    (self.right >= platform.left and self.right <= platform.right):
                self.y_coord = platform.top - self.player_size[1]
                self.player_jumping_state = PlayerJumpState.jumping_down
                self.allow_jumping = True
                if not platform.visited_by_player:
                    self.score_controller.increment_score()
                    platform.visited_by_player = True


    def check_collision_with_platforms(self) -> None:
        """
        Loops on all platforms and checks player collision with them from the top and the bottom
        :return: None
        """
        for platform in self.platform_manager.platforms:
            self.check_platform_collision_bottom(platform)
            self.check_platform_collision_top(platform)

    def update_player_x_coord(self, delta : float) -> None:
        if self.player_movement_state == PlayerMovementState.moving_right:
            self.x_coord += self.horizontal_movement_speed * delta
            self.character_animation_controller.change_animation_state(PlayerAnimationState.moving_right)
        elif self.player_movement_state == PlayerMovementState.moving_left:
            self.character_animation_controller.change_animation_state(PlayerAnimationState.moving_left)
            self.x_coord -= self.horizontal_movement_speed * delta
        else:
            self.character_animation_controller.change_animation_state(PlayerAnimationState.idle)

    def update_player_y_coord(self, delta : float) -> None:
        if self.player_jumping_state == PlayerJumpState.jumping_up:
            if self.tmp_jump_height <= self.max_jump_height:
                self.tmp_jump_height += self.vertical_movement_speed * delta
                self.y_coord -= self.vertical_movement_speed * delta
                if self.player_movement_state == PlayerMovementState.moving_right:
                    self.character_animation_controller.change_animation_state(PlayerAnimationState.jumping_up_right)
                elif self.player_movement_state == PlayerMovementState.moving_left:
                    self.character_animation_controller.change_animation_state(PlayerAnimationState.jumping_up_left)
            else:
                self.tmp_jump_height = 0
                self.player_jumping_state = PlayerJumpState.jumping_down

        elif self.player_jumping_state == PlayerJumpState.jumping_down:
            self.y_coord += 1 * delta

    def process_player_state(self, delta : float) -> None:
        """
        :param delta: the delta from the last frame
        :return: None
        """

        # 1 Movement
        # 1.1 X-coordinate control
        self.update_player_x_coord(delta)

        # 1.2 Y-coordinate control
        self.update_player_y_coord(delta)

        # 2. Update player outer bounds
        self.update_player_outer_bounds()

        # 3. Collision detection

        # 3.1 Check collision with the frame
        self.check_frame_collision()

        # 3.2 Check collision with platforms
        self.check_collision_with_platforms()

        # 4. Update platforms
        self.platform_manager.update_and_return_platforms(delta = delta,
                                                          update_position = self.move_platforms,
                                                          speed_multiplier = self.score_controller.get_speed_multiplier)

        # 5. Update score
        self.score_controller.update_score(delta)

    def render_game_over(self) -> None:
        font = pygame.font.Font(None, configuration.font_size)

        text_game_over = font.render(f'Game Over! - Score: {self.score_controller.get_score} - High Score: {self.score_controller.get_high_score}',
                                   True, configuration.score_font_color)

        self.window.blit(text_game_over, configuration.game_over_coordinates)

    def render_player(self, delta: float) -> None:
        """
        Renders the player
        :param delta: time since last frame render
        :return: none
        """
        if not self.score_controller.is_paused:
            self.character_sprite = self.character_animation_controller.update_player_sprite(delta)
        self.process_player_state(delta)
        self.window.blit(self.character_sprite,(self.x_coord,self.y_coord))
        self.score_controller.render_score()

        #pygame.draw.circle(self.window, self.player_color,
        #                   (self.x_coord, self.y_coord), self.player_size[1]/2)
#endregion

#region Icy Tower Remake

class IcyTowerRemake():
    def __init__(self):
        # Initialize Pygame
        pygame.init()

        # Set the window title
        display.set_caption(configuration.title)

        # Create the window
        self.window : display = display.set_mode(configuration.window_size)

        # Load background texture
        self.background_image : surface = image.load(configuration.background_image_path)

        # Init platforms
        self.platform_manager : PlatformManager = PlatformManager(self.window)

        # Init player
        self.player : Player = Player(self.window, self.platform_manager)

        # Init clock
        self.clock : Clock = time.Clock()

        # Load an play music
        mixer.music.load(configuration.background_music_path)

        # Play the music, the argument -1 makes it loop indefinitely
        mixer.music.play(-1)

    def key_down_event(self, e : event) -> bool:
        if e.key == pygame.K_ESCAPE:
            return True
        else:
            pass
            #player.player_key_down(e)
        return False

    def key_press_update(self):
        # Get all pressed keys
        all_keys : ScancodeWrapper = pygame.key.get_pressed()
        self.player.player_key_press(all_keys)

    def Render_Background(self):
        # Define the blue color
        #blue_color = (0, 0, 255)

        # Fill the window with blue color
        #self.window.fill(blue_color)

        # Draw the background image
        self.window.blit(self.background_image, (0, 0))

    def Render(self):
        # Update the FPS
        delta = self.clock.tick(configuration.target_FPS)
        if delta == 0:
            delta = 1 / 60 * 1000

        # Render the background
        self.Render_Background()

        # Render the platforms
        self.platform_manager.render_platforms()

        # Render the player
        self.player.render_player(delta)

        # Update the display
        pygame.display.flip()

    def process_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                return self.key_down_event(event)
            if event.type == pygame.QUIT:
                return True
        self.key_press_update()
        return False

    def update(self):
        # Main loop
        while True:
            if(self.process_events()):
                pygame.quit()
                break
            self.Render()

#endregion

# Main program loop
if __name__ == '__main__':
    game = IcyTowerRemake()
    game.update()