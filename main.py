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

WIDTH = 1550
HEIGHT = 900
TITLE = "Angry birds"
GRAVITY = -900

class LevelWinView(arcade.View):
    def __init__(self, next_level_idx, stars=0):
        super().__init__()
        self.next_level_idx = next_level_idx
        self.stars = stars

    def on_show_view(self):
        arcade.set_background_color(arcade.color.DARK_GREEN)

    def on_draw(self):
        self.clear()
        arcade.draw_text(
            "¡Nivel ganado!",
            WIDTH // 2,
            HEIGHT // 2 + 100,
            arcade.color.YELLOW,
            50,
            anchor_x="center"
        )
        # Mostrar estrellas
        star_text = f"Estrellas: {'★' * self.stars}{'☆' * (3 - self.stars)}"
        arcade.draw_text(
            star_text,
            WIDTH // 2,
            HEIGHT // 2 + 40,
            arcade.color.GOLD,
            40,
            anchor_x="center"
        )
        if self.next_level_idx < len(LEVELS):
            arcade.draw_text(
                "Presiona ENTER para siguiente nivel",
                WIDTH // 2,
                HEIGHT // 2 - 30,
                arcade.color.WHITE,
                28,
                anchor_x="center"
            )
        else:
            arcade.draw_text(
                "¡Juego completado!",
                WIDTH // 2,
                HEIGHT // 2 - 30,
                arcade.color.WHITE,
                28,
                anchor_x="center"
            )
            arcade.draw_text(
                "Presiona ESC para volver al menú",
                WIDTH // 2,
                HEIGHT // 2 - 80,
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
        # Handler específico: pájaro (1) toca cerdo (2)
        self.bird_pig_handler = self.space.add_collision_handler(1, 2)
        self.bird_pig_handler.begin = self.bird_hits_pig

        # Puntaje y efectos flotantes
        self.score = 0
        self.floating_scores = []  # lista de dicts: {x, y, value, timer}

        # Botón de recarga
        self.reload_texture = arcade.load_texture("assets/img/reload.png")
        self.reload_button_pos = (WIDTH - 60, HEIGHT - 60)
        self.reload_button_size = 48

        # Paredes invisibles solo para cerdos
        self.left_wall = pymunk.Segment(self.space.static_body, (0, 0), (0, HEIGHT), 1)
        self.right_wall = pymunk.Segment(self.space.static_body, (WIDTH - 40, 0), (WIDTH - 40, HEIGHT), 1)
        self.left_wall.sensor = True
        self.right_wall.sensor = True
        self.space.add(self.left_wall, self.right_wall)

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

        self.sling_texture = arcade.load_texture("assets/img/sling-3.png")
        self.sling_width, self.sling_height = 90, 120
        self.floor_y = 15              # coincide con tu segmento del piso
        self.sling_left = 30           # margen desde el borde izquierdo
        self.sling_bottom = self.floor_y + 2  # 2 px por encima del piso

        # Punto fijo de lanzamiento (centro del PNG)
        self.sling_anchor = (
            self.sling_left + self.sling_width // 2,
            self.sling_bottom + self.sling_height // 2,
        )
        self.sling_radius = 45  # radio para “agarrar” la resortera


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
            # Limitar movimiento horizontal de cerdos con paredes invisibles
            pig.body.position = (x, y)
            pig.body.velocity_func = self.pig_velocity_limiter
            self.sprites.append(pig)
            self.world.append(pig)

    def pig_velocity_limiter(self, body, gravity, damping, dt):
        # Limita el movimiento horizontal de los cerdos para que no salgan del área
        pymunk.Body.update_velocity(body, gravity, damping, dt)
        if body.position.x < 20:
            body.position = (20, body.position.y)
            body.velocity = (0, body.velocity.y)
        elif body.position.x > WIDTH - 40:
            body.position = (WIDTH - 40, body.position.y)
            body.velocity = (0, body.velocity.y)


    def set_window(self, window):
        self._window = window

    def toggle_fullscreen(self):
        if self._window:
            self._window.set_fullscreen(not self._window.fullscreen)
            logger.debug(f"Fullscreen set to {self._window.fullscreen}")

        # agregar un collision handler
        self.handler = self.space.add_default_collision_handler()

    def bird_hits_pig(self, arbiter, space, data):
        # Eliminar el cerdo cuando lo toca un pájaro
        pig_hit = None
        for obj in self.world:
            if isinstance(obj, Pig) and obj.shape in arbiter.shapes:
                pig_hit = obj
                break
        if pig_hit:
            x, y = pig_hit.center_x, pig_hit.center_y
            pig_hit.remove_from_sprite_lists()
            if pig_hit.shape.space is not None:
                pig_hit.shape.space.remove(pig_hit.shape, pig_hit.body)
            self.score += 100
            self.floating_scores.append({'x': x, 'y': y, 'value': 100, 'timer': 0.0})
        return True

    def create_bird(self, bird_type, impulse_vector, x, y):
        # crear pajaro del tipo que queremos
        # Llevar la cuenta de pájaros lanzados
        if not hasattr(self, "birds_launched"):
            self.birds_launched = 0
        self.birds_launched += 1
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
        # Eliminar cerdos si un pájaro está muy cerca (1mm)
        pigs_to_remove = []
        for pig in [obj for obj in self.world if isinstance(obj, Pig)]:
            for bird in [obj for obj in self.world if isinstance(obj, (Bird, YellowBird, BlueBird))]:
                dx = pig.center_x - bird.center_x
                dy = pig.center_y - bird.center_y
                dist = math.hypot(dx, dy)
                if dist <= 1.0:
                    pigs_to_remove.append(pig)
                    break
        for pig in pigs_to_remove:
            x, y = pig.center_x, pig.center_y
            pig.remove_from_sprite_lists()
            if pig.shape.space is not None:
                pig.shape.space.remove(pig.shape, pig.body)
            self.score += 100
            self.floating_scores.append({'x': x, 'y': y, 'value': 100, 'timer': 0.0})
        # Actualizar efectos flotantes de puntaje
        for fs in self.floating_scores:
            fs['y'] += 60 * delta_time  # sube
            fs['timer'] += delta_time
        self.floating_scores = [fs for fs in self.floating_scores if fs['timer'] < 1.0]
        # conteo ESC
        if self.esc_held:
            self.esc_timer += delta_time
            if self.esc_timer >= 5.0:
                arcade.exit()

    def check_level_win(self):
        pigs_left = [obj for obj in self.world if isinstance(obj, Pig)]
        if not pigs_left:
            # Calcular estrellas
            level = LEVELS[self.level_idx]
            num_pigs = len(level["pigs"])
            birds_used = getattr(self, "birds_launched", 0)
            if birds_used <= num_pigs:
                stars = 3
            elif birds_used == num_pigs + 1:
                stars = 2
            elif birds_used == num_pigs + 2:
                stars = 1
            else:
                stars = 0
            next_level = self.level_idx + 1
            self.window.show_view(LevelWinView(next_level, stars=stars))

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
        # Revisar botón de recarga primero
        if button == arcade.MOUSE_BUTTON_LEFT:
            bx, by = self.reload_button_pos
            s = self.reload_button_size // 2
            if bx - s < x < bx + s and by - s < y < by + s:
                self.score = 0
                self.restart_level()
                return

            # Modo catapulta
            if self.catapult_mode:
                if self.can_launch and not self.catapult_bird_ready:
                    bird = self.create_bird(self.current_bird_type, get_impulse_vector(Point2D(), Point2D()), x, y)
                    self.catapult.load_bird(bird)
                    self.sprites.append(bird)
                    self.birds.append(bird)
                    self.current_bird = bird
                    self.catapult_bird_ready = True
                    self.can_launch = True
                elif self.catapult_bird_ready and not self.catapult.counterweight_ready:
                    self.catapult.start_counterweight_draw(x, y)
                elif self.catapult_bird_ready and self.catapult.counterweight_ready:
                    ok = self.catapult.drop_bird_at(x, y, height=400)
                    if ok:
                        self.can_launch = False
                        self.bird_stopped_timer = 0
            # Modo resortera
            else:
                if self.can_launch:
                    dx = x - self.sling_anchor[0]
                    dy = y - self.sling_anchor[1]
                    if (dx*dx + dy*dy) ** 0.5 <= self.sling_radius:
                        self.start_point = Point2D(self.sling_anchor[0]+100, self.sling_anchor[1]+50)
                        self.end_point = Point2D(x, y)
                        self.draw_line = True
                    else:
                        self.draw_line = False

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

        # Dibujar resortera
        arcade.draw_texture_rect(
            self.sling_texture,
            arcade.LRBT(
                self.sling_left + 100,
                self.sling_left + self.sling_width + 100,
                self.sling_bottom,
                self.sling_bottom + self.sling_height,
            ),
        )

        # Dibujar botón de recarga
        bx, by = self.reload_button_pos
        arcade.draw_texture_rect(
            self.reload_texture,
            arcade.LRBT(
                bx - self.reload_button_size // 2,
                bx + self.reload_button_size // 2,
                by - self.reload_button_size // 2,
                by + self.reload_button_size // 2,
            ),
        )

        self.sprites.draw()

        # Dibujar catapulta si está activa
        if self.catapult_mode:
            self.catapult.draw()

        # dibujar trayectoria segmentada (1/4 de parábola) para resortera
        if self.draw_line and self.can_launch and not self.catapult_mode:
            # Calcular vector de impulso (ángulo y fuerza)
            from game_logic import get_impulse_vector
            impulse_vector = get_impulse_vector(self.start_point, self.end_point)
            angle = impulse_vector.angle
            velocity = impulse_vector.impulse * 4  # Ajusta el factor para que la parábola sea visible
            g = abs(GRAVITY)
            x0, y0 = self.start_point.x, self.start_point.y
            num_points = 20
            t_total = (2 * velocity * math.sin(angle)) / g if g != 0 else 1
            t_max = t_total * 0.25  # Solo 1/4 del trayecto
            for i in range(num_points):
                t = t_max * i / (num_points - 1)
                x = x0 + velocity * math.cos(angle) * t
                y = y0 + velocity * math.sin(angle) * t - 0.5 * g * t * t
                arcade.draw_circle_filled(x, y, 6, arcade.color.AERO_BLUE)



        # interfaz
        self.draw_ui()
        # Indicación sutil para reiniciar
        arcade.draw_text("Presiona 'R' para reiniciar nivel", WIDTH - 260, 18, arcade.color.LIGHT_GRAY, 16)


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

        # PUNTAJE en esquina superior derecha
        arcade.draw_text(f"Puntaje: {self.score}", 700, 750, arcade.color.GOLD, 28, anchor_x="left")

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

        arcade.draw_text(instruction, 600, 800, arcade.color.YELLOW, 18)

        arcade.draw_text("R: Reiniciar | SPACE: Habilidad especial",
                        1100, 825, arcade.color.LIGHT_GRAY, 20)

        # Dibujar efectos flotantes de puntaje
        for fs in self.floating_scores:
            arcade.draw_text(f"{fs['value']}", fs['x'], fs['y'], arcade.color.GOLD, 32, anchor_x="center", anchor_y="center")

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
        self.birds_launched = 0

        # recargar nivel
        self.load_level(self.level_idx)
        logger.debug(f"Nivel {self.level_idx + 1} reiniciado")

def main():
    window = arcade.Window(WIDTH, HEIGHT, TITLE, fullscreen=True)
    menu = MenuView()
    window.show_view(menu)
    arcade.run()

if __name__ == "__main__":
    main()