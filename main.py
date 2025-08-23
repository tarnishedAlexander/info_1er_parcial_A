
import math
import logging
import arcade
import pymunk
from game_object import Bird, BlueBird, Column, Pig, YellowBird
from catapult import Catapult
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

LEVELS = [
    {
        "pigs": [(WIDTH / 2, 100)],
        "columns": [(WIDTH // 2, 50), (WIDTH // 2 + 400, 50)],
    },
    {
        "pigs": [(WIDTH / 2, 100), (WIDTH / 2 + 200, 100)],
        "columns": [(WIDTH // 2, 50), (WIDTH // 2 + 200, 50), (WIDTH // 2 + 400, 50)],
    },
    {
        "pigs": [(WIDTH / 2, 100), (WIDTH / 2 + 200, 100), (WIDTH / 2 + 400, 100)],
        "columns": [(WIDTH // 2, 50), (WIDTH // 2 + 200, 50), (WIDTH // 2 + 400, 50), (WIDTH // 2 + 600, 50)],
    },
    {
        "pigs": [(WIDTH / 2, 100), (WIDTH / 2 + 200, 100), (WIDTH / 2 + 400, 100), (WIDTH / 2 + 600, 100)],
        "columns": [(WIDTH // 2, 50), (WIDTH // 2 + 200, 50), (WIDTH // 2 + 400, 50), (WIDTH // 2 + 600, 50), (WIDTH // 2 + 800, 50)],
    },
    {
        "pigs": [(WIDTH / 2, 100), (WIDTH / 2 + 200, 100), (WIDTH / 2 + 400, 100), (WIDTH / 2 + 600, 100), (WIDTH / 2 + 800, 100)],
        "columns": [(WIDTH // 2, 50), (WIDTH // 2 + 200, 50), (WIDTH // 2 + 400, 50), (WIDTH // 2 + 600, 50), (WIDTH // 2 + 800, 50), (WIDTH // 2 + 1000, 50)],
    },
]

# Vista de victoria de nivel
class LevelWinView(arcade.View):
    def __init__(self, next_level_idx):
        super().__init__()
        self.next_level_idx = next_level_idx

    def on_show_view(self):
        arcade.set_background_color(arcade.color.DARK_GREEN)

    def on_draw(self):
        self.clear()
        arcade.draw_text(
            "¡Nivel ganado!",
            WIDTH // 2,
            HEIGHT // 2 + 60,
            arcade.color.YELLOW,
            50,
            anchor_x="center"
        )
        if self.next_level_idx < len(LEVELS):
            arcade.draw_text(
                "Presiona ENTER para siguiente nivel",
                WIDTH // 2,
                HEIGHT // 2,
                arcade.color.WHITE,
                28,
                anchor_x="center"
            )
        else:
            arcade.draw_text(
                "¡Juego completado!",
                WIDTH // 2,
                HEIGHT // 2,
                arcade.color.WHITE,
                28,
                anchor_x="center"
            )
            arcade.draw_text(
                "Presiona ESC para volver al menú",
                WIDTH // 2,
                HEIGHT // 2 - 50,
                arcade.color.LIGHT_GRAY,
                22,
                anchor_x="center"
            )

    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.ENTER and self.next_level_idx < len(LEVELS):
            game = App(level_idx=self.next_level_idx)
            game.set_window(self.window)
            self.window.show_view(game)
        elif symbol == arcade.key.ESCAPE:
            menu = MenuView()
            self.window.show_view(menu)

import math
import logging
import arcade
import pymunk
from game_object import Bird, BlueBird, Column, Pig, YellowBird
from catapult import Catapult
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


class MenuView(arcade.View):
    def on_show_view(self):
        arcade.set_background_color(arcade.color.DARK_BLUE_GRAY)

    def on_draw(self):
        self.clear()
        arcade.draw_text(
            "ANGRY BIRDS",
            WIDTH // 2,
            HEIGHT // 2 + 100,
            arcade.color.YELLOW,
            font_size=60,
            anchor_x="center",
        )
        arcade.draw_text(
            "Presiona ENTER para Iniciar",
            WIDTH // 2,
            HEIGHT // 2,
            arcade.color.WHITE,
            font_size=30,
            anchor_x="center",
        )
        arcade.draw_text(
            "Presiona ESC para Salir",
            WIDTH // 2,
            HEIGHT // 2 - 60,
            arcade.color.LIGHT_GRAY,
            font_size=24,
            anchor_x="center",
        )

    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.ENTER:
            game = App()
            game.set_window(self.window)
            self.window.show_view(game)
        elif symbol == arcade.key.ESCAPE:
            arcade.exit()


class App(arcade.View):

    def __init__(self, level_idx=0):
        super().__init__()
        self._window = None  # Se asignará en setup
        self.background = arcade.load_texture("assets/img/background3.png")
        self.space = pymunk.Space()
        self.space.gravity = (0, GRAVITY)
        self.current_bird_type = "red"
        self.esc_held = False
        self.esc_timer = 0.0

        # agregar piso
        floor_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        floor_shape = pymunk.Segment(floor_body, [0, 15], [WIDTH, 15], 0.0)
        floor_shape.friction = 10
        self.space.add(floor_body, floor_shape)

        self.level_idx = level_idx
        self.sprites = arcade.SpriteList()
        self.birds = arcade.SpriteList()
        self.world = arcade.SpriteList()
        self.load_level(self.level_idx)

        self.start_point = Point2D()
        self.end_point = Point2D()
        self.distance = 0
        self.draw_line = False

        # Turn-based system variables
        self.current_bird = None  # Track the currently active bird
        self.can_launch = True    # Whether a new bird can be launched
        self.bird_stopped_timer = 0  # Timer to ensure bird has fully stopped

        # Catapult system
        self.catapult_mode = False
        self.catapult = Catapult(200, 100, self.space)
        self.catapult_bird_ready = False

    def load_level(self, idx):
        self.sprites = arcade.SpriteList()
        self.birds = arcade.SpriteList()
        self.world = arcade.SpriteList()
        level = LEVELS[idx]
        for x, y in level["columns"]:
            column = Column(x, y, self.space)
            self.sprites.append(column)
            self.world.append(column)
        for x, y in level["pigs"]:
            pig = Pig(x, y, self.space)
            self.sprites.append(pig)
            self.world.append(pig)


    def set_window(self, window):
        self._window = window

    def toggle_fullscreen(self):
        if self._window:
            self._window.set_fullscreen(not self._window.fullscreen)
            logger.debug(f"Fullscreen set to {self._window.fullscreen}")

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
        pass  # No usar en modo niveles

    def add_pigs(self):
        pass  # No usar en modo niveles

    def on_update(self, delta_time: float):
        self.space.step(1 / 60.0)
        self.update_collisions()
        self.sprites.update(delta_time)
        if self.catapult_mode:
            self.catapult.update(delta_time)
        self.check_bird_status(delta_time)
        self.check_level_win()
        # Conteo ESC
        if self.esc_held:
            self.esc_timer += delta_time
            if self.esc_timer >= 5.0:
                arcade.exit()

    def check_level_win(self):
        pigs_left = [obj for obj in self.world if isinstance(obj, Pig)]
        if not pigs_left:
            next_level = self.level_idx + 1
            self.window.show_view(LevelWinView(next_level))

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
            if self.catapult_mode:
                # 1) Si podemos "preparar" un pájaro y aún no está listo
                if self.can_launch and not self.catapult_bird_ready:
                    # Prepara (STATIC) el pájaro actual en la catapulta virtual
                    if self.current_bird_type == "yellow":
                        bird = YellowBird("assets/img/yellow.png", get_impulse_vector(Point2D(), Point2D()), x, y, self.space)
                    elif self.current_bird_type == "blue":
                        bird = BlueBird("assets/img/blue.png", get_impulse_vector(Point2D(), Point2D()), x, y, self.space)
                    else:
                        bird = Bird("assets/img/red-bird3.png", get_impulse_vector(Point2D(), Point2D()), x, y, self.space)

                    self.catapult.load_bird(bird)
                    self.sprites.append(bird)
                    self.birds.append(bird)
                    self.current_bird = bird
                    self.catapult_bird_ready = True
                    # OJO: seguimos permitiendo dibujar la rampa
                    self.can_launch = True  # dejamos lanzar (clics) para dibujar rampa

                # 2) Si ya está listo el pájaro pero AÚN NO hay rampa, empezamos a dibujar
                elif self.catapult_bird_ready and not self.catapult.counterweight_ready:
                    self.catapult.start_counterweight_draw(x, y)

                # 3) Si ya hay rampa lista, un click suelta el pájaro desde arriba del punto
                elif self.catapult_bird_ready and self.catapult.counterweight_ready:
                    ok = self.catapult.drop_bird_at(x, y, height=400)
                    if ok:
                        self.can_launch = False       # espera a que se detenga para el siguiente
                        self.bird_stopped_timer = 0
            else:
                # ... (tu código existente para modo "resortera" normal) ...
                if self.can_launch:
                    self.start_point = Point2D(x, y)
                    self.end_point = Point2D(x, y)
                    self.draw_line = True


    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int):
        if self.catapult_mode and self.catapult_bird_ready and self.catapult.counterweight_drawing:
            self.catapult.update_counterweight_draw(x, y)
        elif not self.catapult_mode and buttons == arcade.MOUSE_BUTTON_LEFT and self.draw_line and self.can_launch:
            self.end_point = Point2D(x, y)
            logger.debug(f"Dragging to: {self.end_point}")

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        if self.catapult_mode and self.catapult_bird_ready and self.catapult.counterweight_drawing:
            self.catapult.update_counterweight_draw(x, y)
            self.catapult.finish_counterweight_draw()
            logger.debug("Contrapeso pintado y soltado. Espera la animación de lanzamiento.")
        elif not self.catapult_mode:
            if button == arcade.MOUSE_BUTTON_LEFT and self.draw_line and self.can_launch:
                logger.debug(f"Releasing from: {self.end_point}")
                self.draw_line = False
                impulse_vector = get_impulse_vector(self.start_point, self.end_point)
                if self.current_bird_type == "yellow":
                    bird = YellowBird("assets/img/yellow.png", impulse_vector, x, y, self.space)
                elif self.current_bird_type == "blue":
                    bird = BlueBird("assets/img/blue.png", impulse_vector, x, y, self.space)
                else:
                    bird = Bird("assets/img/red-bird3.png", impulse_vector, x, y, self.space)
                self.sprites.append(bird)
                self.birds.append(bird)
                self.current_bird = bird
                self.can_launch = False
                self.bird_stopped_timer = 0
                logger.debug("Bird launched, waiting for it to stop...")

    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.ESCAPE:
            self.esc_held = True
            self.esc_timer = 0.0
        """Allow switching between bird types and activating abilities"""
        # Shift+Enter para fullscreen
        if symbol == arcade.key.ENTER and modifiers & arcade.key.MOD_SHIFT:
            self.toggle_fullscreen()
        elif symbol == arcade.key.KEY_1:
            self.current_bird_type = "red"
        elif symbol == arcade.key.KEY_2:
            self.current_bird_type = "yellow"
        elif symbol == arcade.key.KEY_3:
            self.current_bird_type = "blue"
        elif symbol == arcade.key.C:
            # Alternar entre resortera y catapulta
            self.catapult_mode = not self.catapult_mode
            logger.debug(f"Catapult mode: {self.catapult_mode}")
            # Reset catapult state if switching
            self.catapult_bird_ready = False
            self.can_launch = True
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

    def on_key_release(self, symbol, modifiers):
        if symbol == arcade.key.ESCAPE:
            self.esc_held = False
            self.esc_timer = 0.0

    def on_draw(self):
        self.clear()
        # arcade.draw_lrwh_rectangle_textured(0, 0, WIDTH, HEIGHT, self.background)
        arcade.draw_texture_rect(self.background, arcade.LRBT(0, WIDTH, 0, HEIGHT))
        self.sprites.draw()

        # Dibuja la catapulta si está en modo catapulta
        if self.catapult_mode:
            self.catapult.draw()

        # Only draw aiming line if we can launch a bird
        if self.draw_line and self.can_launch and not self.catapult_mode:
            arcade.draw_line(self.start_point.x, self.start_point.y, self.end_point.x, self.end_point.y,
                             arcade.color.BLACK, 3)

        # Draw status text
        if self.esc_held:
            countdown = max(0, 5 - int(self.esc_timer))
            arcade.draw_text(f"Saliendo en {countdown}...", WIDTH // 2, HEIGHT // 2, arcade.color.RED, 40, anchor_x="center")

        if self.catapult_mode:
            if not self.catapult_bird_ready:
                arcade.draw_text("Catapulta: Haz click para cargar pájaro.", 10, HEIGHT - 30, arcade.color.WHITE, 20)
            elif self.catapult_bird_ready and not self.catapult.counterweight_ready:
                arcade.draw_text("Dibuja la piedra contrapeso (arrastra y suelta).", 10, HEIGHT - 30, arcade.color.WHITE, 20)
            elif self.catapult_bird_ready and self.catapult.counterweight_ready:
                arcade.draw_text("¡Brazo lanzando! Espera el disparo...", 10, HEIGHT - 30, arcade.color.WHITE, 20)
            else:
                arcade.draw_text("Catapulta lista para siguiente disparo.", 10, HEIGHT - 30, arcade.color.WHITE, 20)
        else:
            if not self.can_launch:
                arcade.draw_text("Waiting for bird to stop...", 10, HEIGHT - 30, arcade.color.WHITE, 20)
            else:
                arcade.draw_text(f"Ready to launch {self.current_bird_type} bird", 10, HEIGHT - 30, arcade.color.WHITE, 20)



def main():
    window = arcade.Window(WIDTH, HEIGHT, TITLE)
    menu = MenuView()
    window.show_view(menu)
    arcade.run()


if __name__ == "__main__":
    main()