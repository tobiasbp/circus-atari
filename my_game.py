"""
Simple program to show moving a sprite with the keyboard.

This program uses the Arcade library found at http://arcade.academy

Artwork from https://kenney.nl/assets/space-shooter-redux

"""

import arcade
import arcade.color

# Import sprites from local file my_sprites.py
from my_sprites import Player, PlayerShot, Balloon, Wall

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

    def c_balloon_shot(self, sprite_balloon, sprite_shot, arbiter, space, _data):

        if arbiter.is_first_contact:
            # Start the Balloon death sequence
            # It will kill() itself at the end of the sequence
            sprite_balloon.start_death_sequence()

            # Remove the balloon from the physics engine (PyMunk space) as
            # it should no longer be tracked for collisions
            # The sprite is still associated with the Arcade physics engine, so it is still moved.
            # Is this a dirty hack?
            # space.remove(arbiter.shapes[0])

            # Remove the shot from everything (I think)
            sprite_shot.kill()

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
                    texture = textures[row%len(textures)]
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

        # Variable that will hold a list of shots fired by the player
        self.player_shot_list = arcade.SpriteList()

        # Walls that objects can  bounce off off
        self.walls = self.get_walls()

        self.physics_engine = arcade.PymunkPhysicsEngine(
            gravity=(0,-30),
            # damping=1.0
        )

        # Add walls
        self.physics_engine.add_sprite_list(
            self.walls,
            body_type=arcade.PymunkPhysicsEngine.STATIC
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
            second_type="shot",
            post_handler=self.c_balloon_shot
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
        self.player_shot_list.draw()

        self.walls.draw()

        for row in self.balloon_rows:
            row.draw()

        # Draw the player sprite
        self.player.draw()

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
        # Shots reflect on left, right & top. Removed bottom.
        for s in self.player_shot_list:
            # Get the physics object for the sprite
            so = self.physics_engine.get_physics_object(s)
            # Get the current sprite velocity
            sv = so.body.velocity
            # Bounce x
            if s.center_x > SCREEN_WIDTH or s.center_x < 0:
                self.physics_engine.set_velocity(s, (sv[0] * -1, sv[1]))
            # Bounce top
            elif s.center_y > SCREEN_HEIGHT:
                self.physics_engine.set_velocity(s, (sv[0], sv[1] * -1))
            elif s.center_y < 0:
                s.remove_from_sprite_lists()

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
            new_shot = PlayerShot(
                center_x=self.player.center_x,
                center_y=self.player.center_y,
                speed=PLAYER_SHOT_SPEED,
                max_y_pos=SCREEN_HEIGHT,
                scale=SPRITE_SCALING,
            )

            self.physics_engine.add_sprite(new_shot, mass=0.1, collision_type="shot")
            self.physics_engine.set_velocity(new_shot, (800, 1000))

            # Add the new shot to the list of shots (so we can draw the sprites)
            self.player_shot_list.append(new_shot)

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
