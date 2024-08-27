"""
Simple program to show moving a sprite with the keyboard.

This program uses the Arcade library found at http://arcade.academy

Artwork from https://kenney.nl/assets/space-shooter-redux

"""

import arcade
import arcade.color

# Import sprites from local file my_sprites.py
from my_sprites import Player, PlayerShot, Balloon

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

    def get_balloons(self, rows=3,cols=10, balloon_size=30, use_spatial_hash=True):
        """
        Returns a list of SpriteLists with rows of Balloons.
        """

        # Balloon rows will alternate between these textures
        # Note: Make sure the names are unique
        textures = [
            arcade.Texture.create_filled("balloon_a", (balloon_size, balloon_size), arcade.color.BABY_BLUE_EYES),
            arcade.Texture.create_filled("balloon_b", (balloon_size, balloon_size), arcade.color.PINK),
            arcade.Texture.create_filled("balloon_C", (balloon_size, balloon_size), arcade.color.GREEN_YELLOW),
        ]

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


    def on_show_view(self):
        """
        This is run once when we switch to this view
        """

        # Variable that will hold a list of shots fired by the player
        self.player_shot_list = arcade.SpriteList()


        self.physics_engine = arcade.PymunkPhysicsEngine(
            gravity=(0,-30),
            # damping=1.0
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
                )
                self.physics_engine.set_velocity(b, (balloon_speed,0 ))
            # Flip direction for next row
            balloon_speed *= -1

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

        # Update the player shots
        self.player_shot_list.on_update(delta_time)


        self.physics_engine.step()

        # Wrap balloons when off screen
        for row in self.balloon_rows:
           for b in row:
               if (new_pos := b.get_wrap_pos()) is not None:
                   self.physics_engine.set_position(b, new_pos)

        # The game is over when the player scores a 100 points
        if self.player_score >= 100:
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

            # Add the new shot to the list of shots
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
