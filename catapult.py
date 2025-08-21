import arcade
import pymunk
import arcade
import pymunk
import math

class Catapult:
    def __init__(self, x, y, space, arm_length=180):
        self.x = x
        self.y = y
        self.arm_length = arm_length
        self.space = space
        self.bird_loaded = None
        self.counterweight_points = []
        self.counterweight_body = None
        self.counterweight_shapes = []
        self.counterweight_drawing = False
        self.counterweight_ready = False
        self.counterweight_timer = 0
        self.arm_body = None
        self.arm_shape = None
        self.pivot_joint = None
        self.support_shape = None
        self.bird_joint = None
        self.counterweight_joint = None
        self._setup_physics()

    def _setup_physics(self):
        base_y = self.y
        altura_triangulo = 60
        support_points = [
            (self.x + self.arm_length/2 - 30, base_y + 1-80),
            (self.x + self.arm_length/2 + 30, base_y + 1-80),
            (self.x + self.arm_length/2,       base_y + altura_triangulo-70)
        ]
        support_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        support_shape = pymunk.Poly(support_body, support_points)
        self.space.add(support_body, support_shape)
        self.support_shape = support_shape
        mass = 12
        arm_length = self.arm_length + 80
        moment = pymunk.moment_for_segment(mass, (-arm_length/2,0), (arm_length/2,0), 8)
        arm_body = pymunk.Body(mass, moment, body_type=pymunk.Body.DYNAMIC)
        vertice_superior = support_points[2]
        arm_body.position = vertice_superior
        arm_shape = pymunk.Segment(arm_body, (-arm_length/2,0), (arm_length/2,0), 8)
        arm_shape.friction = 1.0
        self.space.add(arm_body, arm_shape)
        pivot = pymunk.PivotJoint(arm_body, support_body, vertice_superior)
        self.space.add(pivot)
        min_angle = -math.pi/1.7
        max_angle =  math.pi/2
        rotary_limit = pymunk.RotaryLimitJoint(arm_body, support_body, min_angle, max_angle)
        self.space.add(rotary_limit)
        self.arm_body = arm_body
        self.arm_shape = arm_shape
        self.pivot_joint = pivot
        self.rotary_limit = rotary_limit
        self.arm_length = arm_length

    def load_bird(self, bird):
        self.bird_loaded = bird
        left_tip_local = pymunk.Vec2d(-self.arm_length/2, 0)
        left_tip_world = self.arm_body.position + left_tip_local.rotated(self.arm_body.angle)
        bird.body.position = left_tip_world
        bird.body.velocity = (0, 0)
        bird.body.body_type = pymunk.Body.DYNAMIC
        if self.bird_joint:
            self.space.remove(self.bird_joint)
        self.bird_joint = pymunk.PinJoint(self.arm_body, bird.body, (-self.arm_length/2, 0), (0, 0))
        self.space.add(self.bird_joint)


    def start_counterweight_draw(self, x, y):
        self.counterweight_drawing = True
        self.counterweight_points = [(x, y)]

    def update_counterweight_draw(self, x, y):
        if self.counterweight_drawing:
            self.counterweight_points.append((x, y))

    def finish_counterweight_draw(self):
        self.counterweight_body = None
        if self.counterweight_joint:
            try:
                self.space.remove(self.counterweight_joint)
            except Exception:
                pass
            self.counterweight_joint = None
        self.counterweight_shapes = []
        if len(self.counterweight_points) > 2:
            self.counterweight_timer = 0
            mass = max(40, len(self.counterweight_points) * 4)
            moment = pymunk.moment_for_circle(mass, 0, 30)
            body = pymunk.Body(mass, moment)
            first_point = self.counterweight_points[0]
            body.position = first_point
            rel_points = [(px - first_point[0], py - first_point[1]) for px, py in self.counterweight_points]
            shapes = []
            for i in range(len(rel_points)-1):
                a = rel_points[i]
                b = rel_points[i+1]
                shape = pymunk.Segment(body, a, b, 18)
                shape.friction = 1.0
                shape.elasticity = 0.0
                shapes.append(shape)
                self.counterweight_shapes.append(shape)
            self.space.add(body, *shapes)
            self.counterweight_body = body
            self.counterweight_ready = True
            self.counterweight_drawing = False
        else:
            self.counterweight_ready = False
            self.counterweight_drawing = False


    def update(self, delta_time=1/60):
        if self.bird_loaded and self.counterweight_ready:
            angle = self.arm_body.angle
            ang_vel = self.arm_body.angular_velocity
            if angle > 0.25 and ang_vel > 0:
                if self.bird_joint:
                    self.space.remove(self.bird_joint)
                    self.bird_joint = None
                self.bird_loaded = None
        if self.counterweight_ready:
            self.counterweight_timer += delta_time
            if self.counterweight_timer >= 5.0:
                if self.counterweight_joint:
                    try:
                        self.space.remove(self.counterweight_joint)
                    except Exception:
                        pass
                    self.counterweight_joint = None
                if self.counterweight_body:
                    try:
                        self.space.remove(self.counterweight_body)
                    except Exception:
                        pass
                for shape in self.counterweight_shapes:
                    try:
                        self.space.remove(shape)
                    except Exception:
                        pass
                self.counterweight_body = None
                self.counterweight_shapes = []
                self.counterweight_ready = False
                self.counterweight_timer = 0


    def draw(self):
        s = self.support_shape.get_vertices()
        arcade.draw_triangle_filled(s[0].x, s[0].y, s[1].x, s[1].y, s[2].x, s[2].y, arcade.color.DARK_BROWN)
        p_center = self.arm_body.position
        p_left  = p_center + pymunk.Vec2d(-self.arm_length/2, 0).rotated(self.arm_body.angle)
        p_right = p_center + pymunk.Vec2d( self.arm_length/2, 0).rotated(self.arm_body.angle)
        arcade.draw_line(p_left.x, p_left.y, p_right.x, p_right.y, arcade.color.BROWN, 12)
        if self.counterweight_drawing and len(self.counterweight_points) > 1:
            arcade.draw_line_strip(self.counterweight_points, arcade.color.DARK_GRAY, 10)
        if self.counterweight_body and self.counterweight_shapes:
            verts = []
            for seg in self.counterweight_shapes:
                a = self.counterweight_body.position + seg.a.rotated(self.counterweight_body.angle)
                b = self.counterweight_body.position + seg.b.rotated(self.counterweight_body.angle)
                verts.append((a.x, a.y))
            b = self.counterweight_body.position + self.counterweight_shapes[-1].b.rotated(self.counterweight_body.angle)
            verts.append((b.x, b.y))
            if len(verts) > 1:
                arcade.draw_line_strip(verts, arcade.color.DARK_GRAY, 18)

