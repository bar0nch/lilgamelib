import pygame
import time, math

import pymunk as pm
import pymunk.pygame_util
from pymunk import Vec2d

import lilgamelib as lgl

pygame.init()



class Material:
    all_materials = {}

    def __init__(self, name, friction, elasticity, color):
        Material.all_materials[name] = self
        
        self.name = name
        self.friction = friction
        self.elasticity = elasticity
        self.color = color

    @classmethod
    def get_all(cls):
        return cls.all_materials



Material("wood", 0.4, 0.4, (140,89,53))
Material("ice", 0.1, 0.2, (150,140,240))
Material("gravity material", 1.0, 0.0, (37,252,230))



class Platform:
    all_platforms = []

    def __init__(self, position, width, steepness=0, material="wood"):
        Platform.all_platforms.append(self)
        radius = 8
        
        self.material = Material.get_all()[material]
        self.width = width
        self.steepness = steepness
        self.point_a = Vec2d(position[0] - width // 2, position[1] - steepness // 2)
        self.point_b = Vec2d(position[0] + width // 2, position[1] + steepness // 2)
        platform_moment = pm.moment_for_box(1, (math.sqrt(width ** 2 + steepness ** 2), radius))
        self.body = pm.Body(1, platform_moment, pm.Body.STATIC)
        self.body.position = position
        self.body.angle = math.atan2(steepness / 2, width / 2)
        self.shape = pm.Poly.create_box(self.body, (math.sqrt(width ** 2 + steepness ** 2), radius), radius)
        self.shape.elasticity = self.material.elasticity
        self.shape.friction = self.material.friction

        space.add(self.body, self.shape)


    @property
    def x(self):
        return self.body.position.x

    @x.setter
    def x(self, new_x):
        shift = new_x - self.body.position.x
        self.point_a = Vec2d(self.point_a.x + shift, self.point_a.y)
        self.point_b = Vec2d(self.point_b.x + shift, self.point_b.y)
        self.body.position = new_x, self.body.position.y

    @property
    def y(self):
        return self.body.position.y

    @y.setter
    def y(self, new_y):
        shift = new_y - self.body.position.y
        self.point_a = Vec2d(self.point_a.x, self.point_a.y + shift)
        self.point_b = Vec2d(self.point_b.x, self.point_b.y + shift)
        self.body.position = self.body.position.x, new_y


    def fixed_update(self):
        self.point_a = Vec2d(self.body.position.x - self.width // 2, self.body.position.y - self.steepness // 2)
        self.point_b = Vec2d(self.body.position.x + self.width // 2, self.body.position.y + self.steepness // 2)


    def draw(self):
        pygame.draw.line(lgl.WINDOW, self.material.color, self.point_a, self.point_b, width=round(self.shape.radius * 2))


    @classmethod
    def fixed_update_all(cls):
        for platform in cls.all_platforms:
            platform.fixed_update()
            
    @classmethod
    def draw_all(cls):
        for platform in cls.all_platforms:
            platform.draw()



class MovingPlatform(Platform):
    def __init__(self, position, width, point1, point2, steepness=0, material="wood"):
        super().__init__(position, width, steepness, material)
        
        self.body.body_type = pm.Body.KINEMATIC
        self.point1 = point1
        self.point2 = point2

        self._move_to = 1


    def fixed_update(self):
        module = 100
        
        if self._move_to == 1:
            if abs(self.body.position.get_distance(self.point1)) < module * lgl.MainLoop.fix_update_time:
                self.body.position = self.point1.x, self.point1.y
                self._move_to = 2
                return
            angle = math.atan2(self.point1.y - self.y, self.point1.x - self.x)
            
        elif self._move_to == 2:
            if abs(self.body.position.get_distance(self.point2)) < module * lgl.MainLoop.fix_update_time:
                self.body.position = self.point2.x, self.point2.y
                self._move_to = 1
                return
            angle = math.atan2(self.point2.y - self.y, self.point2.x - self.x)
            
        self.body.velocity = Vec2d(module * math.cos(angle), module * math.sin(angle))
        super().fixed_update()



class GravityPlatform(Platform):
    def __init__(self, position, width, steepness=0, force=Vec2d(0.0, -9810.0), gravity_direction=1):
        super().__init__(position, width, steepness, "gravity material")

        window_size = lgl.WINDOW.get_size()
        screen_angle = math.pi / 2 - self.body.angle
        
        if gravity_direction > 0:
            height_from_top_projection = self.y
            distance_from_top_projection = height_from_top_projection / math.sin(screen_angle)
            width_from_top_projection = distance_from_top_projection * math.cos(screen_angle)
            self.top_projection_point = Vec2d(self.x + width_from_top_projection, 0)
            
        elif gravity_direction < 0:
            height_from_top_projection = window_size[1] - self.y
            distance_from_top_projection = height_from_top_projection / math.sin(screen_angle)
            width_from_top_projection = distance_from_top_projection * math.cos(screen_angle)
            self.top_projection_point = Vec2d(self.x - width_from_top_projection, window_size[1])

        self.query_shape = pm.Poly( None,
                                    vertices = [
                                                self.point_a,
                                                Vec2d(self.point_a.x + self.top_projection_point.x - self.x, self.top_projection_point.y),
                                                Vec2d(self.point_b.x + self.top_projection_point.x - self.x, self.top_projection_point.y),
                                                self.point_b
                                                ]
                                   )


    def fixed_update(self):
        print(space.shape_query(self.query_shape))
                                   


    def draw(self):
        super().draw()
        pygame.draw.line(lgl.WINDOW, (240,240,240), self.body.position, self.top_projection_point)
        pygame.draw.polygon(lgl.WINDOW, (30,240,30), gravity_platform.query_shape.get_vertices(), width=2)



class ControllableShape:
    all_shapes = []
    
    def __init__(self):
        ControllableShape.all_shapes.append(self)
        self._is_agent = False
        self.queue = {}

    @classmethod
    def get_all(cls):
        for shape in cls.all_shapes:
            yield shape

    def control(self):
        for shape in ControllableShape.get_all():
            shape._is_agent = False
        self._is_agent = True



class Ball(ControllableShape):
    def __init__(self, position, mass, radius):
        super().__init__()

        self.radius = radius
        ball_moment = pm.moment_for_circle(mass, 0, radius)
        self.body = pm.Body(mass, ball_moment)
        self.body.position = position
        self.shape = pm.Circle(self.body, radius)
        self.shape.elasticity = 0.9
        self.shape.friction = 0.4

        space.add(self.body, self.shape)


    @property
    def x(self):
        return self.body.position.x

    @x.setter
    def x(self, new_x):
        self.body.position = new_x, self.body.position.y

    @property
    def y(self):
        return self.body.position.y

    @y.setter
    def y(self, new_y):
        self.body.position = self.body.position.x, new_y


    def calc_force_components_from_mouse(self, mouse_pos):
        force = self.body.position.get_dist_sqrd(mouse_pos) * 0.2
        angle = math.atan2(mouse_pos[1] - self.y, mouse_pos[0] - self.x)
        return force * math.cos(angle), force * math.sin(angle)


    def event_update(self, event, keys):
        if self._is_agent:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3:
                    self.body.position = 100, 100

            if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.queue["mouse launch"] = True

            if keys[pygame.K_RIGHT]:
                self.queue["move right"] = True
            else:
                self.queue["move right"] = False
                
            if keys[pygame.K_LEFT]:
                self.queue["move left"] = True
            else:
                self.queue["move left"] = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.queue["move up"] = True


    def update(self):
        pass


    def fixed_update(self):
        self.body.angular_velocity *= 0.985 #rolling friction
        if self.body.angular_velocity > 0 and self.body.angular_velocity < 0.0002:
            self.body.angular_velocity = 0
        elif self.body.angular_velocity < 0 and self.body.angular_velocity > -0.0002:
            self.body.angular_velocity = 0
        
        if "move right" in self.queue.keys():
            if self.queue["move right"]:
                self.body.apply_force_at_world_point((2000.0, 0.0), self.body.position)
        if "move left" in self.queue.keys():
            if self.queue["move left"]:
                self.body.apply_force_at_world_point((-2000.0, 0.0), self.body.position)
        if "move up" in self.queue.keys():
            if self.queue["move up"]:
                self.body.apply_force_at_world_point((0.0, -300000.0), self.body.position)
                self.queue["move up"] = False
                
        if "mouse launch" in self.queue.keys():
            if self.queue["mouse launch"]:
                f = self.calc_force_components_from_mouse(pygame.mouse.get_pos())
                self.body.apply_force_at_world_point((f[0], f[1] * 5), self.body.position)
                self.queue["mouse launch"] = False


    def draw(self):
        if self._is_agent:
            pygame.draw.circle(lgl.WINDOW, (240, 230, 232), self.body.position, self.radius, width=3)





class Box(ControllableShape):
    def __init__(self, position, mass, side):
        super().__init__()
        
        self.side = side
        box_moment = pm.moment_for_box(mass, (side, side))
        self.body = pm.Body(mass, box_moment)
        self.body.position = position
        self.shape = pm.Poly.create_box(self.body, (side, side), 2)
        self.shape.friction = 0.4

        space.add(self.body, self.shape)


    @property
    def x(self):
        return self.body.position.x

    @x.setter
    def x(self, new_x):
        self.body.position = new_x, self.body.position.y

    @property
    def y(self):
        return self.body.position.y

    @y.setter
    def y(self, new_y):
        self.body.position = self.body.position.x, new_y


    def calc_force_components_from_mouse(self, mouse_pos):
        force = self.body.position.get_dist_sqrd(mouse_pos) * 0.5
        angle = math.atan2(mouse_pos[1] - self.y, mouse_pos[0] - self.x)
        return force * math.cos(angle), force * math.sin(angle)


    def event_update(self, event, keys):
        if self._is_agent:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3:
                    self.body.position = 100, 100

            if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.queue["mouse launch"] = True

            if keys[pygame.K_RIGHT]:
                self.queue["move right"] = True
            else:
                self.queue["move right"] = False
                
            if keys[pygame.K_LEFT]:
                self.queue["move left"] = True
            else:
                self.queue["move left"] = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.queue["move up"] = True


    def update(self):
        pass


    def fixed_update(self):
        if "move right" in self.queue.keys():
            if self.queue["move right"]:
                self.body.apply_force_at_world_point((10000.0, 0.0), self.body.position)
        if "move left" in self.queue.keys():
            if self.queue["move left"]:
                self.body.apply_force_at_world_point((-10000.0, 0.0), self.body.position)
        if "move up" in self.queue.keys():
            if self.queue["move up"]:
                self.body.apply_force_at_world_point((0.0, -1000000.0), self.body.position)
                self.queue["move up"] = False
                
        if "mouse launch" in self.queue.keys():
            if self.queue["mouse launch"]:
                f = self.calc_force_components_from_mouse(pygame.mouse.get_pos())
                self.body.apply_force_at_world_point((f[0], f[1] * 5), self.body.position)
                self.queue["mouse launch"] = False


    def draw(self):
        if self._is_agent:
            pygame.draw.rect(lgl.WINDOW, (240, 230, 232), (self.x - self.side // 2, self.y - self.side // 2, self.side, self.side), width=3, border_radius=2)




lgl.WINDOW = pygame.display.set_mode((1600,800))
pygame.display.set_caption("pymunk test")
draw_options = pm.pygame_util.DrawOptions(lgl.WINDOW)
pause = False



space = pm.Space()
space.gravity = 0, 9810
space.iterations = 30

ground_body = space.static_body
ground = pymunk.Segment(ground_body, (0, lgl.WINDOW.get_size()[1]), (lgl.WINDOW.get_size()[0], lgl.WINDOW.get_size()[1]), 6)
ground.elasticity = 0.5
ground.friction = 0.8

ball = Ball((100,100), 1, 50)
ball.control()

box = Box((300, 100), 4, 100)

ice_platform = Platform((150, 400), 300, 10, "ice")
wood_platform = MovingPlatform((800, 600), 200, Vec2d(700, 500), Vec2d(850, 650))
gravity_platform = GravityPlatform((1100, 400), 200, -50, gravity_direction=-1)

space.add(ground)


lgl.debug.DebugWin.display.append(lgl.debug.DebugVariableDisplay("pygame.mouse.get_pos()"))
lgl.debug.DebugWin.display[-1].margin["bottom"] += 40
lgl.debug.DebugWin.display.append(lgl.debug.DebugVariableDisplay("round(wood_platform.x)", {"wood_platform":wood_platform}))
lgl.debug.DebugWin.display.append(lgl.debug.DebugVariableDisplay("round(wood_platform.y)", {"wood_platform":wood_platform}))
lgl.debug.DebugWin.display[-1].margin["bottom"] += 20
lgl.debug.DebugWin.display.append(lgl.debug.DebugVariableDisplay("ball._is_agent", {"ball":ball}))
lgl.debug.DebugWin.display.append(lgl.debug.DebugVariableDisplay("box._is_agent", {"box":box}))
lgl.debug.DebugWin.display[-1].margin["bottom"] += 60
#lgl.debug.DebugWin.display.append(lgl.debug.DebugSlider((200,600), "scrollbar.height", {"scrollbar":my_scrollbar.scrollbar}))
lgl.debug.DebugWin.setup((600, lgl.WINDOW.get_size()[1]))



def event_update(events, keys):
    global pause
    
    for event in events:
        if event.type == pygame.QUIT:
            lgl.MainLoop.end()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if box._is_agent:
                    ball.control()
                elif ball._is_agent:
                    box.control()

            elif event.key == pygame.K_ESCAPE:
                if pause:
                    pause = False
                else:
                    pause = True

        ball.event_update(event, keys)
        box.event_update(event, keys)


def update():
    if not pause:
        ball.update()
        box.update()


def fixed_update():
    if not pause:
        ball.fixed_update()
        box.fixed_update()
        Platform.fixed_update_all()
        space.step(lgl.MainLoop.fix_update_time)


def updateGFX():
    lgl.WINDOW.fill((30,26,45))
    space.debug_draw(draw_options)
    ball.draw()
    box.draw()
    Platform.draw_all()



lgl.MainLoop.ev_update = event_update
lgl.MainLoop.update = update
lgl.MainLoop.fix_update = fixed_update
lgl.MainLoop.gfx_update = updateGFX

lgl.MainLoop.start()
