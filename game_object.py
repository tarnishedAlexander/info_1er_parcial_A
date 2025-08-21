import math
import arcade
import pymunk
from game_logic import ImpulseVector


class Bird(arcade.Sprite):
    def __init__(
        self,
        image_path: str,
        impulse_vector: ImpulseVector,
        x: float,
        y: float,
        space: pymunk.Space,
        mass: float = 5,
        radius: float = 12,
        max_impulse: float = 100,
        power_multiplier: float = 50,
        elasticity: float = 0.8,
        friction: float = 1,
        collision_layer: int = 0,
        life_time: float = 5.0,
    ):
        super().__init__(image_path, 1)
        moment = pymunk.moment_for_circle(mass, 0, radius)
        body = pymunk.Body(mass, moment)
        body.position = (x, y)

        impulse = min(max_impulse, impulse_vector.impulse) * power_multiplier
        impulse_pymunk = impulse * pymunk.Vec2d(1, 0)
        body.apply_impulse_at_local_point(impulse_pymunk.rotated(impulse_vector.angle))
        shape = pymunk.Circle(body, radius)
        shape.elasticity = elasticity
        shape.friction = friction
        shape.collision_type = collision_layer

        space.add(body, shape)

        self.body = body
        self.shape = shape

        self.life_time = life_time
        self.time_alive = 0.0

    def update(self, delta_time):
        self.center_x = self.shape.body.position.x
        self.center_y = self.shape.body.position.y
        self.radians = self.shape.body.angle

        self.time_alive += delta_time
        if self.time_alive >= self.life_time:
            if self.shape.space is not None:
                self.shape.space.remove(self.shape, self.body)
            self.remove_from_sprite_lists()


class Pig(arcade.Sprite):
    def __init__(
        self,
        x: float,
        y: float,
        space: pymunk.Space,
        mass: float = 2,
        elasticity: float = 0.8,
        friction: float = 0.4,
        collision_layer: int = 0,
    ):
        super().__init__("assets/img/pig_failed.png", 0.1)
        moment = pymunk.moment_for_circle(mass, 0, self.width / 2 - 3)
        body = pymunk.Body(mass, moment)
        body.position = (x, y)
        shape = pymunk.Circle(body, self.width / 2 - 3)
        shape.elasticity = elasticity
        shape.friction = friction
        shape.collision_type = collision_layer
        space.add(body, shape)
        self.body = body
        self.shape = shape

    def update(self, delta_time):
        self.center_x = self.shape.body.position.x
        self.center_y = self.shape.body.position.y
        self.radians = self.shape.body.angle

class YellowBird(Bird):
    """
    Yellow bird that can boost its impulse when clicked during flight
    """
    def __init__(
        self,
        image_path: str,
        impulse_vector: ImpulseVector,
        x: float,
        y: float,
        space: pymunk.Space,
        boost_multiplier: float = 1.3,
        **kwargs
    ):
        super().__init__(image_path, impulse_vector, x, y, space, **kwargs)
        # Resize to 40x40 pixels
        self.scale = 40 / max(self.width, self.height)
        self.boost_multiplier = boost_multiplier
        self.has_boosted = False  # Prevent multiple boosts
        self.is_in_flight = False
    
    def update(self, delta_time):
        super().update(delta_time)
        # Check if bird is in flight (has significant velocity)
        velocity = self.body.velocity
        self.is_in_flight = velocity.length > 10  # Threshold for being "in flight"
    
    def boost(self):
        """Apply boost to the bird if it hasn't been used yet"""
        if not self.has_boosted and self.is_in_flight:
            # Get current velocity direction
            current_velocity = self.body.velocity
            if current_velocity.length > 0:
                # Apply boost in current direction
                boost_impulse = current_velocity.normalized() * (current_velocity.length * self.boost_multiplier)
                self.body.velocity = boost_impulse
                self.has_boosted = True
                return True
        return False


class BlueBird(Bird):
    """
    Blue bird that splits into 3 birds when clicked during flight
    """
    def __init__(
        self,
        image_path: str,
        impulse_vector: ImpulseVector,
        x: float,
        y: float,
        space: pymunk.Space,
        **kwargs
    ):
        super().__init__(image_path, impulse_vector, x, y, space, **kwargs)
        # Resize to 40x40 pixels
        self.scale = 40 / max(self.width, self.height)
        self.has_split = False
        self.is_in_flight = False
    
    def update(self, delta_time):
        super().update(delta_time)
        velocity = self.body.velocity
        self.is_in_flight = velocity.length > 10
    
    def split(self, sprite_list):
        """Split into 3 birds with 30-degree separation"""
        if not self.has_split and self.is_in_flight:
            current_velocity = self.body.velocity
            current_position = self.body.position
            
            if current_velocity.length > 0:
                # Get current angle
                current_angle = math.atan2(current_velocity.y, current_velocity.x)
                
                # Create 3 birds with -30, 0, +30 degree offsets
                angles = [current_angle + math.radians(30), 
                         current_angle, 
                         current_angle - math.radians(30)]
                
                new_birds = []
                for angle in angles:
                    # Create new impulse vector with same magnitude but different direction
                    new_velocity = pymunk.Vec2d(
                        current_velocity.length * math.cos(angle),
                        current_velocity.length * math.sin(angle)
                    )
                    
                    # Create new blue bird
                    space = self.body.space
                    if space is None:
                        continue  # Skip creation if space is None
                    new_bird = BlueBird(
                        "assets/img/blue.png",
                        ImpulseVector(angle, current_velocity.length),
                        current_position.x,
                        current_position.y,
                        space,
                        mass=self.body.mass,
                        radius=self.shape.radius
                    )
                    # Set velocity directly instead of applying impulse
                    new_bird.body.velocity = new_velocity
                    new_bird.has_split = True  # Prevent further splitting
                    new_birds.append(new_bird)
                    sprite_list.append(new_bird)
                
                # Remove original bird
                self.remove_from_sprite_lists()
                if self.shape.space is not None:
                    self.shape.space.remove(self.shape, self.body)
                self.has_split = True
                
                return new_birds
        return []

class PassiveObject(arcade.Sprite):
    def __init__(
        self,
        image_path: str,
        x: float,
        y: float,
        space: pymunk.Space,
        mass: float = 2,
        elasticity: float = 0.8,
        friction: float = 1,
        collision_layer: int = 0,
    ):
        super().__init__(image_path, 1)

        moment = pymunk.moment_for_box(mass, (self.width, self.height))
        body = pymunk.Body(mass, moment)
        body.position = (x, y)
        shape = pymunk.Poly.create_box(body, (self.width, self.height))
        shape.elasticity = elasticity
        shape.friction = friction
        shape.collision_type = collision_layer
        space.add(body, shape)
        self.body = body
        self.shape = shape

    def update(self, delta_time):
        self.center_x = self.shape.body.position.x
        self.center_y = self.shape.body.position.y
        self.radians = self.shape.body.angle


class Column(PassiveObject):
    def __init__(self, x, y, space):
        super().__init__("assets/img/column.png", x, y, space)


class StaticObject(arcade.Sprite):
    def __init__(
            self,
            image_path: str,
            x: float,
            y: float,
            space: pymunk.Space,
            mass: float = 2,
            elasticity: float = 0.8,
            friction: float = 1,
            collision_layer: int = 0,
    ):
        super().__init__(image_path, 1)

