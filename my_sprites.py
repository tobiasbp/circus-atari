import arcade

class Acrobat(arcade.Sprite):
    """
    A flying acrobat
    """
    def __init__(self, center_x, center_y, color=arcade.color.RED, scale=1):
        # Create a texture if none is supplied
        texture = arcade.Texture.create_filled(
            "acrobat",
            (50,50),
            color=color,
        )

        # Pass arguments to class arcade.Sprite
        super().__init__(
            center_x=center_x,
            center_y=center_y,
            texture=texture,
            scale=scale,
        )

class Wall(arcade.Sprite):        
    """
    A wall that objects will bounce off of
    """
    def __init__(self, center_x, center_y, width, height, colour=arcade.color.PERSIAN_INDIGO):

        texture = arcade.Texture.create_filled(
            "wall",
            (width,height),
            colour
        )

        # Pass arguments to class arcade.Sprite
        super().__init__(
            center_x=center_x,
            center_y=center_y,
            texture = texture
        )

class Balloon(arcade.Sprite):
    """
    The Balloon
    """
    def __init__(self,center_x,center_y,min_x=0,max_x=1024,size=30,color=arcade.color.PINK):
        texture = arcade.Texture.create_filled(
            f"balloon_{color}",
            (30,30),
            color,
        )

        # Pass arguments to class arcade.Sprite
        super().__init__(
            center_x=center_x,
            center_y=center_y,
            texture = texture
        )

        self.min_x = min_x
        self.max_x = max_x

    def get_wrap_pos(self):
        """
        Return new position if Baloon is in a wrap position.
        Otherwise, return None.
        The physics engine will call this function to potentially move the sprite.
        """
        if self.center_x < self.min_x:
            return (self.max_x, self.center_y)
        elif self.center_x > self.max_x:
            # self.center_x = self.min_x
            return (self.min_x, self.center_y)

        return None

    def start_death_sequence(self):

        self.alpha -= 1

    def update(self):
        if self.alpha < 255:
            self.alpha *= 0.91
            if self.alpha < 1:
                self.kill()

class Player(arcade.Sprite):
    """
    The player
    """

    def __init__(self, min_x_pos, max_x_pos, center_x=0, center_y=0, scale=1):
        """
        Setup new Player object
        """
        t = arcade.Texture.create_filled("seesaw", [400, 40], arcade.color.JAZZBERRY_JAM)

        # Limits on player's x position
        self.min_x_pos = min_x_pos
        self.max_x_pos = max_x_pos
        self.lives = 3

        # Pass arguments to class arcade.Sprite
        super().__init__(
            center_x=center_x,
            center_y=center_y,
            texture=t,
            scale=scale,
            angle=-20
        )

        # The (Fake) Acrobat waiting to be launched
        self.passanger = Acrobat(center_x, center_y, scale = 0.5)

    @property
    def left_side_down(self):
        return self.angle < 0

    def flip(self):
        self.angle *= -1

    def update(self):
        """
        Move the sprite
        """

        if self.left_side_down:
            self.passanger.center_x = self.center_x + self.width/2
        else:
            self.passanger.center_x = self.center_x - self.width/2
