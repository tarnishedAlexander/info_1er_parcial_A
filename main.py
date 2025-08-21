import math
import logging
import arcade
import pymunk

from game_object import Bird, BlueBird, Column, Pig, YellowBird
from game_logic import get_impulse_vector, Point2D, get_distance

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("arcade").setLevel(logging.WARNING)
logging.getLogger("pymunk").setLevel(logging.WARNING)
logging.getLogger("PIL").setLevel(logging.WARNING)

logger = logging.getLogger("main")

WIDTH = 1800
HEIGHT = 800
TITLE = "Angry birds"
GRAVITY = -900


class App(arcade.View):
    def __init__(self):
        super().__init__()
        self.background = arcade.load_texture("assets/img/background3.png")
        # crear espacio de pymunk
        self.space = pymunk.Space()
        self.space.gravity = (0, GRAVITY)
        self.current_bird_type = "red"  

        # agregar piso
        floor_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        floor_shape = pymunk.Segment(floor_body, [0, 15], [WIDTH, 15], 0.0)
        floor_shape.friction = 10
        self.space.add(floor_body, floor_shape)

        self.sprites = arcade.SpriteList()
        self.birds = arcade.SpriteList()
        self.world = arcade.SpriteList()
        self.add_columns()
        self.add_pigs()

        self.start_point = Point2D()
        self.end_point = Point2D()
        self.distance = 0
        self.draw_line = False
        
        # Turn-based system variables
        self.current_bird = None  # Track the currently active bird
        self.can_launch = True    # Whether a new bird can be launched
        self.bird_stopped_timer = 0  # Timer to ensure bird has fully stopped

        # agregar un collision handler
        self.handler = self.space.add_default_collision_handler()
        self.handler.post_solve = self.collision_handler

    def collision_handler(self, arbiter, space, data):
        impulse_norm = arbiter.total_impulse.length
        if impulse_norm < 100:
            return True
        logger.debug(impulse_norm)
        if impulse_norm > 1200:
            for obj in self.world:
                if obj.shape in arbiter.shapes:
                    obj.remove_from_sprite_lists()
                    self.space.remove(obj.shape, obj.body)

        return True

    def add_columns(self):
        for x in range(WIDTH // 2, WIDTH, 400):
            column = Column(x, 50, self.space)
            self.sprites.append(column)
            self.world.append(column)

    def add_pigs(self):
        pig1 = Pig(WIDTH / 2, 100, self.space)
        self.sprites.append(pig1)
        self.world.append(pig1)

    def on_update(self, delta_time: float):
        self.space.step(1 / 60.0)  # actualiza la simulacion de las fisicas
        self.update_collisions()
        self.sprites.update(delta_time)
        self.check_bird_status(delta_time)

    def check_bird_status(self, delta_time: float):
        """Check if the current bird has stopped and allow launching the next one"""
        if self.current_bird and not self.can_launch:
            # Check if the bird still exists and has low velocity
            if self.current_bird in self.birds:
                velocity = self.current_bird.body.velocity
                speed = velocity.length
                
                # If bird is moving very slowly, start the timer
                if speed < 5:  # Threshold for "stopped"
                    self.bird_stopped_timer += delta_time
                    # Wait 1 second after stopping to allow for settling
                    if self.bird_stopped_timer >= 1.0:
                        logger.debug("Bird has stopped, can launch next bird")
                        self.can_launch = True
                        self.current_bird = None
                        self.bird_stopped_timer = 0
                else:
                    # Reset timer if bird starts moving again
                    self.bird_stopped_timer = 0
            else:
                # Bird was removed (destroyed), can launch next one
                logger.debug("Bird was removed, can launch next bird")
                self.can_launch = True
                self.current_bird = None
                self.bird_stopped_timer = 0

    def update_collisions(self):
        pass

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            # Only allow aiming if no bird is currently active
            if self.can_launch:
                self.start_point = Point2D(x, y)
                self.end_point = Point2D(x, y)
                self.draw_line = True
                logger.debug(f"Start Point: {self.start_point}")
            else:
                logger.debug("Cannot launch bird - wait for current bird to stop")
                                
    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int):
        if buttons == arcade.MOUSE_BUTTON_LEFT and self.draw_line and self.can_launch:
            self.end_point = Point2D(x, y)
            logger.debug(f"Dragging to: {self.end_point}")

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        if button == arcade.MOUSE_BUTTON_LEFT and self.draw_line and self.can_launch:
            logger.debug(f"Releasing from: {self.end_point}")
            self.draw_line = False
            impulse_vector = get_impulse_vector(self.start_point, self.end_point)
            
            # Create different bird types based on current selection
            if self.current_bird_type == "yellow":
                bird = YellowBird("assets/img/yellow.png", impulse_vector, x, y, self.space)
            elif self.current_bird_type == "blue":
                bird = BlueBird("assets/img/blue.png", impulse_vector, x, y, self.space)
            else:  # red bird (default)
                bird = Bird("assets/img/red-bird3.png", impulse_vector, x, y, self.space)
            
            self.sprites.append(bird)
            self.birds.append(bird)
            
            # Set as current bird and disable launching until it stops
            self.current_bird = bird
            self.can_launch = False
            self.bird_stopped_timer = 0
            logger.debug("Bird launched, waiting for it to stop...")

    def on_key_press(self, symbol, modifiers):
        """Allow switching between bird types and activating abilities"""
        if symbol == arcade.key.KEY_1:
            self.current_bird_type = "red"
        elif symbol == arcade.key.KEY_2:
            self.current_bird_type = "yellow"
        elif symbol == arcade.key.KEY_3:
            self.current_bird_type = "blue"
        elif symbol == arcade.key.SPACE:
            # Spacebar triggers ability of the current active bird (if in flight)
            if self.current_bird:
                # Handle special bird abilities
                if isinstance(self.current_bird, YellowBird):
                    if hasattr(self.current_bird, 'is_in_flight') and self.current_bird.is_in_flight:
                        success = self.current_bird.boost()
                        if success:
                            logger.debug("Yellow bird boosted!")
                        else:
                            logger.debug("Yellow bird boost failed (already used or not in flight)")
                    else:
                        logger.debug("Yellow bird not in flight")
                elif isinstance(self.current_bird, BlueBird):
                    if hasattr(self.current_bird, 'is_in_flight') and self.current_bird.is_in_flight:
                        new_birds = self.current_bird.split(self.sprites)
                        if new_birds:
                            for new_bird in new_birds:
                                self.birds.append(new_bird)
                            logger.debug(f"Blue bird split into {len(new_birds)} birds!")
                        else:
                            logger.debug("Blue bird split failed (already used or not in flight)")
                    else:
                        logger.debug("Blue bird not in flight")
                else:
                    logger.debug("Red bird has no special ability")
            else:
                logger.debug("No active bird to trigger ability")

    def on_draw(self):
        self.clear()
        # arcade.draw_lrwh_rectangle_textured(0, 0, WIDTH, HEIGHT, self.background)
        arcade.draw_texture_rect(self.background, arcade.LRBT(0, WIDTH, 0, HEIGHT))
        self.sprites.draw()
        
        # Only draw aiming line if we can launch a bird
        if self.draw_line and self.can_launch:
            arcade.draw_line(self.start_point.x, self.start_point.y, self.end_point.x, self.end_point.y,
                             arcade.color.BLACK, 3)
        
        # Draw status text
        if not self.can_launch:
            arcade.draw_text("Waiting for bird to stop...", 10, HEIGHT - 30, 
                           arcade.color.WHITE, 20)
        else:
            arcade.draw_text(f"Ready to launch {self.current_bird_type} bird", 10, HEIGHT - 30, 
                           arcade.color.WHITE, 20)


def main():
    window = arcade.Window(WIDTH, HEIGHT, TITLE)
    game = App()
    window.show_view(game)
    arcade.run()


if __name__ == "__main__":
    main()