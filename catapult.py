# catapult.py — Rampa estática (garabato) + caída de pájaro por click
import arcade
import pymunk
import math

class Catapult:
    """
    - El usuario dibuja un garabato (línea gruesa).
    - Ese garabato se convierte en una rampa ESTÁTICA (no le afecta la gravedad).
    - Se prepara un pájaro (queda STATIC), y cuando el usuario hace click en algún lugar
      después de dibujar la rampa, el pájaro se suelta desde arriba de ese punto y cae
      usando la rampa para llegar al cerdo.
    """
    def __init__(self, x, y, space, arm_length=180):
        self.x = x
        self.y = y
        self.space = space

        # Estado del pájaro
        self.bird_loaded = None  # sprite del pájaro (arcade.Sprite), con body pymunk

        # Estado del garabato/rampa
        self.counterweight_points = []
        self.counterweight_body = None   # STATIC
        self.counterweight_shapes = []
        self.counterweight_drawing = False
        self.counterweight_ready = False
        self.counterweight_timer = 0.0   # por si quieres limpiar luego (opcional)

        # Compatibilidad con tu API previa (no hay brazo real ya)
        self.arm_body = None
        self.arm_shape = None
        self.pivot_joint = None
        self.support_shape = None
        self.bird_joint = None
        self.counterweight_joint = None

        # (Opcional) base visual para que no se vea vacío
        self._setup_dummy_visual()

    # -------------------- Visual "dummy" opcional --------------------
    def _setup_dummy_visual(self):
        base_y = self.y
        altura = 40
        points = [
            (self.x + 20, base_y),
            (self.x + 120, base_y),
            (self.x + 70, base_y + altura)
        ]
        support_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        support_shape = pymunk.Poly(support_body, points)
        support_shape.friction = 1.0
        support_shape.elasticity = 0.0
        self.space.add(support_body, support_shape)
        self.support_shape = support_shape

    # -------------------- Pájaro --------------------
    def load_bird(self, bird):
        """
        En lugar de montarlo a un brazo, lo dejamos preparado (STATIC)
        hasta que el usuario haga click para soltarlo.
        """
        self.bird_loaded = bird
        # Lo dejamos estático y sin velocidad; tú decides dónde mostrarlo (opcional).
        bird.body.velocity = (0, 0)
        bird.body.angular_velocity = 0
        bird.body.body_type = pymunk.Body.STATIC  # ¡no cae todavía!

        # (Opcional) podrías posicionarlo cerca de la rampa o donde prefieras:
        # bird.body.position = (self.x + 80, self.y + 180)

        # Sin junta
        if self.bird_joint:
            try:
                self.space.remove(self.bird_joint)
            except Exception:
                pass
        self.bird_joint = None

    def drop_bird_at(self, x, y, height=400):
        """
        Suelta el pájaro desde arriba del punto (x, y).
        Lo pasamos a DYNAMIC y le damos gravedad normal.
        """
        if not self.bird_loaded:
            return False
        body = self.bird_loaded.body
        # Pasamos a dinámico y colocamos arriba del click
        body.body_type = pymunk.Body.DYNAMIC
        body.position = (x, y + height)
        body.velocity = (0, 0)
        body.angular_velocity = 0
        return True

    # -------------------- Garabato / Rampa --------------------
    def start_counterweight_draw(self, x, y):
        self.counterweight_drawing = True
        self.counterweight_points = [(x, y)]

    def update_counterweight_draw(self, x, y):
        if self.counterweight_drawing:
            self.counterweight_points.append((x, y))

    def finish_counterweight_draw(self):
        """
        Convierte el trazo en rampa ESTÁTICA (segmentos en un body STATIC).
        """
        self.counterweight_drawing = False

        # Quita la rampa anterior si había
        self._remove_ramp()

        if len(self.counterweight_points) < 2:
            self.counterweight_ready = False
            return

        # Cuerpo estático para que NO le afecte la gravedad
        body = pymunk.Body(body_type=pymunk.Body.STATIC)
        # No hace falta position/angle en STATIC; vamos a crear segmentos en coords del mundo

        shapes = []
        for i in range(len(self.counterweight_points) - 1):
            ax, ay = self.counterweight_points[i]
            bx, by = self.counterweight_points[i + 1]
            seg = pymunk.Segment(body, (ax, ay), (bx, by), 14)
            seg.friction = 1.2      # que deslice poco (rampa “pegajosa”)
            seg.elasticity = 0.1    # poca elasticidad para no “rebotar” raro
            shapes.append(seg)

        self.space.add(body, *shapes)
        self.counterweight_body = body
        self.counterweight_shapes = shapes
        self.counterweight_ready = True
        self.counterweight_timer = 0.0

    def _remove_ramp(self):
        if self.counterweight_shapes:
            for s in self.counterweight_shapes:
                try:
                    self.space.remove(s)
                except Exception:
                    pass
        self.counterweight_shapes = []
        if self.counterweight_body:
            try:
                self.space.remove(self.counterweight_body)
            except Exception:
                pass
        self.counterweight_body = None

    # -------------------- Update / Draw --------------------
    def update(self, delta_time=1/60):
        # (Opcional) limpieza automática de la rampa tras X segundos:
        # if self.counterweight_ready:
        #     self.counterweight_timer += delta_time
        #     if self.counterweight_timer >= 30.0:
        #         self._remove_ramp()
        #         self.counterweight_ready = False
        pass

    def draw(self):
        # base visual (triangulito)
        if self.support_shape:
            s = self.support_shape.get_vertices()
            arcade.draw_triangle_filled(s[0].x, s[0].y, s[1].x, s[1].y, s[2].x, s[2].y, arcade.color.DARK_BROWN)

        # vista previa durante el dibujo
        if self.counterweight_drawing and len(self.counterweight_points) > 1:
            arcade.draw_line_strip(self.counterweight_points, arcade.color.GRAY, 8)

        # rampa estática
        if self.counterweight_shapes:
            verts = []
            # ojo: como son segmentos en coords mundo, los puntos ya son absolutos
            for seg in self.counterweight_shapes:
                a = seg.a
                b = seg.b
                verts.append((a.x, a.y))
            if verts:
                # Conectar en pantalla. Para que se vea bonito, rehacemos la polilínea
                pts = [seg.a for seg in self.counterweight_shapes] + [self.counterweight_shapes[-1].b]
                arcade.draw_line_strip([(p.x, p.y) for p in pts], arcade.color.DARK_SLATE_GRAY, 16)
