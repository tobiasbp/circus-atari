"""
Simple program to show moving a sprite with the keyboard.

This program uses the Arcade library found at http://arcade.academy

Artwork from https://kenney.nl/assets/space-shooter-redux

"""

import arcade
import arcade.color
import random

import arcade.color

# Import sprites from local file my_sprites.py
from my_sprites import Acrobat, Player, Balloon, Wall

# Set the scaling of all sprites in the game
SPRITE_SCALING = 0.5

# Set the size of the screen
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Variables controlling the player
PLAYER_LIVES = 3
PLAYER_SPEED_X = 200
PLAYER_START_X = SCREEN_WIDTH / 2
PLAYER_START_Y = 50
PLAYER_SHOT_SPEED = 300

FIRE_KEY = arcade.key.SPACE


class GameView(arcade.View):
    """
    The view with the game itself
    """

    def c_balloon_acrobat(self, sprite_balloon, sprite_acrobat, arbiter, space, _data):

        if arbiter.is_first_contact:

            # Function for creating particles with
            # the same texture as the balloon
            get_particle = lambda emitter: arcade.FadeParticle(
                filename_or_texture=sprite_balloon.texture,
                change_xy=arcade.rand_in_circle((0.0, 0.0), 3.0),
                lifetime=random.uniform(0.5, 1.0),
                scale=sprite_balloon.scale/2,
                change_angle=random.randint(-10,10),
            )

            # Create a burst emitter
            e = arcade.Emitter(
                center_xy=sprite_balloon.position,
                emit_controller=arcade.EmitBurst(random.randint(10, 20)),
                particle_factory=get_particle
            )

            # Add the new emitter to the game views list of emitters
            self.burst_emitters.append(e)

            # Remove the balloon
            sprite_balloon.kill()

    def c_acrobat_floor(self, sprite_acrobat, sprite_floor, arbiter, space, _data):
        sprite_acrobat.kill()

    def get_balloons(self, rows=3,cols=10, balloon_size=30, use_spatial_hash=True):
        """
        Returns a list of SpriteLists with rows of Balloons.
        """

        # Balloon rows will alternate between these colors
        colors = [
            arcade.color.BABY_BLUE_EYES,
            arcade.color.PINK,
            arcade.color.GREEN_YELLOW,
        ]

        # Build textures from colors
        textures = []
        for i, color in enumerate(colors):
            textures.append(
                arcade.Texture.create_filled(
                    name=f"balloon_{i}",
                    size=(balloon_size, balloon_size),
                    color=color,
                )
            )

        # The max and min x position of the balloons
        # Positions need to be off screen
        balloon_min_x = -1 * balloon_size
        balloon_max_x = SCREEN_WIDTH + balloon_size

        # The space between ballons
        spacing = round((SCREEN_WIDTH+2*balloon_size)/(cols))

        # The list of SpriteLists to return
        rows_of_baloons = []

        for row in range(rows):
            # Add an empty row
            rows_of_baloons.append(
                arcade.SpriteList(use_spatial_hash=use_spatial_hash)
            )
            for col in range(cols):
                b = Balloon(
                    #size=balloon_size,
                    center_x = col * spacing,
                    center_y = SCREEN_HEIGHT - 1*balloon_size - row * spacing,
                    min_x = balloon_min_x,
                    max_x = balloon_max_x,
                    # texture = textures[row%len(textures)]
                    color = colors[row%len(colors)]
                    )

                # Add balloon to the current row
                rows_of_baloons[-1].append(b)

        return rows_of_baloons

    def get_walls(self, level=1):
        """
        Add walls that physics objects will bounce off of
        """
        walls = arcade.SpriteList()

        if level == 1:
            pw = 80 # Platform width
            ph = 30 # Platform height
            py = 200
            walls.append(Wall(pw/2,py,pw,ph)) # Left
            walls.append(Wall(SCREEN_WIDTH - pw/2,py,pw,ph)) # Right

        else:
            raise Exception("Unsupported level")

        return walls


    def on_show_view(self):
        """
        This is run once when we switch to this view
        """
        self.burst_emitters: list[arcade.Emitter] = []

        # Variable that will hold a list of shots fired by the player
        self.acrobats = arcade.SpriteList()

        # Walls that objects can  bounce off off
        self.walls = self.get_walls()

        self.physics_engine = arcade.PymunkPhysicsEngine(
            gravity=(0,-30),
            # damping=1.0
        )

        # Add an invisible ceiling
        self.physics_engine.add_sprite(
            Wall(SCREEN_WIDTH/2, SCREEN_HEIGHT+5, SCREEN_WIDTH*2, 10),
            body_type=arcade.PymunkPhysicsEngine.STATIC,
            collision_type="ceiling",
            elasticity=0.9,

        )

        # Add an invisible floor
        self.physics_engine.add_sprite(
            Wall(SCREEN_WIDTH/2, -20/2, SCREEN_WIDTH*2, 20),
            body_type=arcade.PymunkPhysicsEngine.STATIC,
            collision_type="floor"
        )

        # Add walls
        self.physics_engine.add_sprite_list(
            self.walls,
            body_type=arcade.PymunkPhysicsEngine.STATIC,
            collision_type="wall"
            )

        # A list of SpriteLists containing rows of Balloons
        self.balloon_rows = self.get_balloons()

        # Add Balloons to the physics engine with no gravity
        # Set their speeds
        balloon_speed = -20
        for row in self.balloon_rows:
            for b in row:
                self.physics_engine.add_sprite(
                    sprite=b,
                    gravity=(0.0, 0.0),
                    elasticity=0.9,
                    # friction=0.9,
                    collision_type="balloon",
                    # radius=30,
                    mass=1.0,
                    # max_vertical_velocity=1.0,
                )
                self.physics_engine.set_velocity(b, (balloon_speed,0 ))
            # Flip direction for next row
            balloon_speed *= -1


        self.physics_engine.add_collision_handler(
            first_type="balloon",
            second_type="acrobat",
            post_handler=self.c_balloon_acrobat
            )

        self.physics_engine.add_collision_handler(
            first_type="acrobat",
            second_type="floor",
            post_handler=self.c_acrobat_floor
            )

        # Set up the player info
        self.player_score = 0
        self.player_lives = PLAYER_LIVES

        # Create a Player object
        self.player = Player(
            center_x=PLAYER_START_X,
            center_y=PLAYER_START_Y,
            min_x_pos=0,
            max_x_pos=SCREEN_WIDTH,
            scale=SPRITE_SCALING,
        )

        # Track the current state of what keys are pressed
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False

        # Get list of joysticks
        joysticks = arcade.get_joysticks()

        if joysticks:
            print("Found {} joystick(s)".format(len(joysticks)))

            # Use 1st joystick found
            self.joystick = joysticks[0]

            # Communicate with joystick
            self.joystick.open()

            # Map joysticks functions to local functions
            self.joystick.on_joybutton_press = self.on_joybutton_press
            self.joystick.on_joybutton_release = self.on_joybutton_release
            self.joystick.on_joyaxis_motion = self.on_joyaxis_motion
            self.joystick.on_joyhat_motion = self.on_joyhat_motion

        else:
            print("No joysticks found")
            self.joystick = None

        # Set the background color
        arcade.set_background_color(arcade.color.AMAZON)

    def on_draw(self):
        """
        Render the screen.
        """

        # Clear screen so we can draw new stuff
        self.clear()

        # Draw the player shot
        self.acrobats.draw()

        self.walls.draw()

        for row in self.balloon_rows:
            row.draw()

        # Draw the player sprite
        self.player.draw()

        for e in  self.burst_emitters:
            e.draw()

        # Draw players score on screen
        arcade.draw_text(
            f"SCORE: {self.player_score}",  # Text to show
            10,  # X position
            SCREEN_HEIGHT - 20,  # Y positon
            arcade.color.WHITE,  # Color of text
        )

    def on_update(self, delta_time):
        """
        Movement and game logic
        """
        for e in self.burst_emitters:
            e.update()

            if e.can_reap():
                self.burst_emitters.remove(e)

        # Shots reflect on left, right & top. Removed bottom.
        for a in self.acrobats:
            # Get the physics object for the sprite
            physics_object = self.physics_engine.get_physics_object(a)
            # Get the current sprite velocity
            velocity_x, velocity_y = physics_object.body.velocity
            # Bounce x
            if a.center_x > SCREEN_WIDTH or a.center_x < 0:
                self.physics_engine.set_velocity(a, (velocity_x * -1, velocity_y))
            elif a.center_y < 0:
                a.remove_from_sprite_lists()

        # Calculate player speed based on the keys pressed
        self.player.change_x = 0

        # Move player with keyboard
        if self.left_pressed and not self.right_pressed:
            self.player.change_x = -PLAYER_SPEED_X
        elif self.right_pressed and not self.left_pressed:
            self.player.change_x = PLAYER_SPEED_X

        # Move player with joystick if present
        if self.joystick:
            self.player.change_x = round(self.joystick.x) * PLAYER_SPEED_X

        # Update player sprite
        self.player.on_update(delta_time)

        # Physics engine updates sprites
        self.physics_engine.step()

        # Wrap balloons when off screen
        for i, row in enumerate(self.balloon_rows):
            # print(f"Length of balloon row {i}:", len(row))
           for b in row:
               b.update()
               # get potential new position from balloon
               new_pos = b.get_wrap_pos()
               if new_pos is not None:
                   self.physics_engine.set_position(b, new_pos)

        # The game is over when the player scores a 100 points
        if self.player_score >= 1000:
            self.game_over()

    def game_over(self):
        """
        Call this when the game is over
        """

        # Create a game over view
        game_over_view = GameOverView(score=self.player_score)

        # Change to game over view
        self.window.show_view(game_over_view)

    def on_key_press(self, key, modifiers):
        """
        Called whenever a key is pressed.
        """

        # End the game if the escape key is pressed
        if key == arcade.key.ESCAPE:
            self.game_over()

        # Track state of arrow keys
        if key == arcade.key.UP:
            self.up_pressed = True
        elif key == arcade.key.DOWN:
            self.down_pressed = True
        elif key == arcade.key.LEFT:
            self.left_pressed = True
        elif key == arcade.key.RIGHT:
            self.right_pressed = True

        if key == FIRE_KEY:
            # Player gets points for firing?
            self.player_score += 10

            # Create the new shot
            a = Acrobat(
                center_x=self.player.center_x,
                center_y=self.player.center_y,
                scale=SPRITE_SCALING,
            )

            self.physics_engine.add_sprite(
                sprite=a,
                mass=1.0,
                collision_type="acrobat",
                elasticity=0.5,
            )
            self.physics_engine.set_velocity(a, (random.randint(-100,100), 500))

            # Add the new shot to the list of shots (so we can draw the sprites)
            self.acrobats.append(a)

    def on_key_release(self, key, modifiers):
        """
        Called whenever a key is released.
        """

        if key == arcade.key.UP:
            self.up_pressed = False
        elif key == arcade.key.DOWN:
            self.down_pressed = False
        elif key == arcade.key.LEFT:
            self.left_pressed = False
        elif key == arcade.key.RIGHT:
            self.right_pressed = False

    def on_joybutton_press(self, joystick, button_no):
        print("Button pressed:", button_no)
        # Press the fire key
        self.on_key_press(FIRE_KEY, [])

    def on_joybutton_release(self, joystick, button_no):
        print("Button released:", button_no)

    def on_joyaxis_motion(self, joystick, axis, value):
        print("Joystick axis {}, value {}".format(axis, value))

    def on_joyhat_motion(self, joystick, hat_x, hat_y):
        print("Joystick hat ({}, {})".format(hat_x, hat_y))


class IntroView(arcade.View):
    """
    View to show instructions
    """

    def on_show_view(self):
        """
        This is run once when we switch to this view
        """

        # Set the background color
        arcade.set_background_color(arcade.csscolor.DARK_SLATE_BLUE)

        # Reset the viewport, necessary if we have a scrolling game and we need
        # to reset the viewport back to the start so we can see what we draw.
        arcade.set_viewport(0, self.window.width, 0, self.window.height)

    def on_draw(self):
        """
        Draw this view
        """
        self.clear()

        # Draw some text
        arcade.draw_text(
            "Instructions Screen",
            self.window.width / 2,
            self.window.height / 2,
            arcade.color.WHITE,
            font_size=50,
            anchor_x="center",
        )

        # Draw more text
        arcade.draw_text(
            "Press any key to start the game",
            self.window.width / 2,
            self.window.height / 2 - 75,
            arcade.color.WHITE,
            font_size=20,
            anchor_x="center",
        )

    def on_key_press(self, key: int, modifiers: int):
        """
        Start the game when any key is pressed
        """
        game_view = GameView()
        self.window.show_view(game_view)


class GameOverView(arcade.View):
    """
    View to show when the game is over
    """

    def __init__(self, score, window=None):
        """
        Create a Gaome Over view. Pass the final score to display.
        """
        self.score = score

        super().__init__(window)

    def setup_old(self, score: int):
        """
        Call this from the game so we can show the score.
        """
        self.score = score

    def on_show_view(self):
        """
        This is run once when we switch to this view
        """

        # Set the background color
        arcade.set_background_color(arcade.csscolor.DARK_GOLDENROD)

        # Reset the viewport, necessary if we have a scrolling game and we need
        # to reset the viewport back to the start so we can see what we draw.
        arcade.set_viewport(0, self.window.width, 0, self.window.height)

    def on_draw(self):
        """
        Draw this view
        """

        self.clear()

        # Draw some text
        arcade.draw_text(
            "Game over!",
            self.window.width / 2,
            self.window.height / 2,
            arcade.color.WHITE,
            font_size=50,
            anchor_x="center",
        )

        # Draw player's score
        arcade.draw_text(
            f"Your score: {self.score}",
            self.window.width / 2,
            self.window.height / 2 - 75,
            arcade.color.WHITE,
            font_size=20,
            anchor_x="center",
        )

    def on_key_press(self, key: int, modifiers: int):
        """
        Return to intro screen when any key is pressed
        """
        intro_view = IntroView()
        self.window.show_view(intro_view)


def main():
    """
    Main method
    """
    # Create a window to hold views
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT)

    # Game starts in the intro view
    start_view = IntroView()

    window.show_view(start_view)

    arcade.run()


if __name__ == "__main__":
    main()
