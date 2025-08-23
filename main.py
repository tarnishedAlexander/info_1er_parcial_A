import math
import logging
import arcade
import pymunk
from game_object import Bird, BlueBird, Column, Pig, YellowBird
from catapult import Catapult
from game_logic import get_impulse_vector, Point2D, get_distance
from levels import LEVELS

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("arcade").setLevel(logging.WARNING)
logging.getLogger("pymunk").setLevel(logging.WARNING)
logging.getLogger("PIL").setLevel(logging.WARNING)
logger = logging.getLogger("main")

WIDTH = 1800
HEIGHT = 800
TITLE = "Angry birds"
GRAVITY = -900

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
            game = GameView(level_idx=self.next_level_idx)
            game.set_window(self.window)
            self.window.show_view(game)
        elif symbol == arcade.key.ESCAPE:
            menu = MenuView()
            self.window.show_view(menu)


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
            "Catapult Edition",
            WIDTH // 2,
            HEIGHT // 2 + 50,
            arcade.color.ORANGE,
            font_size=30,
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
            game = GameView()
            game.set_window(self.window)
            self.window.show_view(game)
        elif symbol == arcade.key.ESCAPE:
            arcade.exit()


class GameView(arcade.View):

    def __init__(self, level_idx=0):
        super().__init__()
        self._window = None
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

        # variables de turnos
        self.current_bird = None
        self.can_launch = True
        self.bird_stopped_timer = 0

        # sistema de catapulta
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
        
    def create_bird(self, bird_type, impulse_vector, x, y):
        # crear pajaro del tipo que queremos
        if bird_type == "yellow":
            bird = YellowBird("assets/img/yellow.png", impulse_vector, x, y, self.space)
        elif bird_type == "blue":
            bird = BlueBird("assets/img/blue.png", impulse_vector, x, y, self.space)
        else:
            bird = Bird("assets/img/red-bird3.png", impulse_vector, x, y, self.space)
        return bird

    def on_update(self, delta_time: float):
        self.space.step(1 / 60.0)
        self.sprites.update(delta_time)
        if self.catapult_mode:
            self.catapult.update(delta_time)
        self.check_bird_status(delta_time)
        self.check_level_win()
        # conteo ESC
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
        # ver si el pajaro ya se detuvo para poder lanzar otro
        if self.current_bird and not self.can_launch:
            # revisar si el pajaro sigue existiendo y tiene poca velocidad
            if self.current_bird in self.birds:
                velocity = self.current_bird.body.velocity
                speed = velocity.length

                # si se mueve muy lento, empezar el timer
                if speed < 5:
                    self.bird_stopped_timer += delta_time
                    # esperar 1 segundo despues de parar
                    if self.bird_stopped_timer >= 1.0:
                        logger.debug("Bird has stopped, can launch next bird")
                        self.can_launch = True
                        self.current_bird = None
                        self.bird_stopped_timer = 0
                else:
                    # resetear timer si se mueve otra vez
                    self.bird_stopped_timer = 0
            else:
                # pajaro fue destruido, se puede lanzar otro
                logger.debug("Bird was removed, can launch next bird")
                self.can_launch = True
                self.current_bird = None
                self.bird_stopped_timer = 0

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            if self.catapult_mode:
                if self.can_launch and not self.catapult_bird_ready:
                    # Cargar pajaro en catapulta
                    bird = self.create_bird(self.current_bird_type, get_impulse_vector(Point2D(), Point2D()), x, y)
                    self.catapult.load_bird(bird)
                    self.sprites.append(bird)
                    self.birds.append(bird)
                    self.current_bird = bird
                    self.catapult_bird_ready = True
                    self.can_launch = True

                elif self.catapult_bird_ready and not self.catapult.counterweight_ready:
                    # empezar a dibujar rampa
                    self.catapult.start_counterweight_draw(x, y)

                elif self.catapult_bird_ready and self.catapult.counterweight_ready:
                    # soltar pajaro
                    ok = self.catapult.drop_bird_at(x, y, height=400)
                    if ok:
                        self.can_launch = False
                        self.bird_stopped_timer = 0
            else:
                # modo resortera
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
            # terminar de dibujar rampa
            self.catapult.update_counterweight_draw(x, y)
            self.catapult.finish_counterweight_draw()
            logger.debug("Rampa completada")
        elif not self.catapult_mode:
            # lanzar con resortera
            if button == arcade.MOUSE_BUTTON_LEFT and self.draw_line and self.can_launch:
                logger.debug(f"Lanzando desde resortera: {self.end_point}")
                self.draw_line = False
                impulse_vector = get_impulse_vector(self.start_point, self.end_point)
                bird = self.create_bird(self.current_bird_type, impulse_vector, x, y)
                self.sprites.append(bird)
                self.birds.append(bird)
                self.current_bird = bird
                self.can_launch = False
                self.bird_stopped_timer = 0
                logger.debug("Pajaro lanzado")

    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.ESCAPE:
            self.esc_held = True
            self.esc_timer = 0.0
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
            # cambiar entre resortera y catapulta
            self.catapult_mode = not self.catapult_mode
            logger.debug(f"Catapult mode: {self.catapult_mode}")
            # resetear catapulta
            self.catapult_bird_ready = False
            self.can_launch = True
        elif symbol == arcade.key.SPACE:
            # usar habilidad especial
            if self.current_bird:
                if isinstance(self.current_bird, YellowBird):
                    if hasattr(self.current_bird, 'is_in_flight') and self.current_bird.is_in_flight:
                        self.current_bird.boost()
                        logger.debug("Yellow bird boosted!")
                elif isinstance(self.current_bird, BlueBird):
                    if hasattr(self.current_bird, 'is_in_flight') and self.current_bird.is_in_flight:
                        new_birds = self.current_bird.split(self.sprites)
                        if new_birds:
                            for new_bird in new_birds:
                                self.birds.append(new_bird)
                            logger.debug(f"Blue bird split into {len(new_birds)} birds!")
        elif symbol == arcade.key.R:
            logger.debug("Reiniciando nivel")
            self.restart_level()

    def on_key_release(self, symbol, modifiers):
        if symbol == arcade.key.ESCAPE:
            self.esc_held = False
            self.esc_timer = 0.0

    def on_draw(self):
        self.clear()
        # Dibujar fondo
        arcade.draw_texture_rect(self.background, arcade.LRBT(0, WIDTH, 0, HEIGHT))
        self.sprites.draw()

        # Dibujar catapulta si está activa
        if self.catapult_mode:
            self.catapult.draw()

        # dibujar linea de punteria para resortera
        if self.draw_line and self.can_launch and not self.catapult_mode:
            arcade.draw_line(self.start_point.x, self.start_point.y, self.end_point.x, self.end_point.y,
                             arcade.color.BLACK, 3)

        # interfaz
        self.draw_ui()

    def draw_ui(self):
        # contador de salida
        if self.esc_held:
            countdown = max(0, 5 - int(self.esc_timer))
            arcade.draw_text(f"Saliendo en {countdown}...", WIDTH // 2, HEIGHT // 2, 
                           arcade.color.RED, 40, anchor_x="center")

        # info del juego
        arcade.draw_text(f"Nivel: {self.level_idx + 1}/{len(LEVELS)}", 
                        10, HEIGHT - 30, arcade.color.WHITE, 20)
        
        arcade.draw_text(f"Pájaro: {self.current_bird_type.title()} (1-3 para cambiar)", 
                        10, HEIGHT - 60, arcade.color.WHITE, 20)
        
        mode_text = "Catapulta" if self.catapult_mode else "Resortera"
        arcade.draw_text(f"Modo: {mode_text} (C para cambiar)", 
                        10, HEIGHT - 90, arcade.color.WHITE, 20)

        # instrucciones
        if self.catapult_mode:
            if not self.catapult_bird_ready:
                instruction = "Click para cargar pájaro en catapulta"
            elif not self.catapult.counterweight_ready:
                instruction = "Dibuja la rampa arrastrando el mouse"
            else:
                instruction = "Click donde quieres que caiga el pájaro"
        else:
            if not self.can_launch:
                instruction = "Esperando que el pájaro se detenga..."
            else:
                instruction = "Arrastra para apuntar, suelta para disparar"
                
        arcade.draw_text(instruction, 10, 30, arcade.color.YELLOW, 18)
        
        arcade.draw_text("R: Reiniciar | SPACE: Habilidad especial", 
                        10, 10, arcade.color.LIGHT_GRAY, 14)

    def restart_level(self):
        # limpiar pajaros actuales
        for bird in self.birds:
            if bird.shape.space is not None:
                bird.shape.space.remove(bird.shape, bird.body)
        
        # resetear estado
        self.current_bird = None
        self.can_launch = True
        self.bird_stopped_timer = 0
        self.catapult_bird_ready = False
        self.draw_line = False
        
        # recargar nivel
        self.load_level(self.level_idx)
        logger.debug(f"Nivel {self.level_idx + 1} reiniciado")

def main():
    window = arcade.Window(WIDTH, HEIGHT, TITLE)
    menu = MenuView()
    window.show_view(menu)
    arcade.run()

if __name__ == "__main__":
    main()