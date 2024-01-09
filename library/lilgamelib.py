import pygame
import sys, os, time, copy

pygame.init()


#CONFIGURATION CONSTANTS

WINDOW = None
WINDOW_SCALE = 1
ADAPT_ASPECT_RATIO = False
WINDOW_SIZE = (900, 600)
PADDING_FUNCTIONAL_WINDOW = (0, 0) #functional window is the portion of the window constrained by WINDOW_SIZE
AUTO_CENTER_FUNCTIONAL_WINDOW = True
FUNCTIONAL_WINDOW_BORDERS = False
FUNCTIONAL_WINDOW_BORDER_COL = (0, 0, 0)
DRAW_OBJS_INSIDE_FUNCTIONAL_WINDOW = False
AUTO_SYNC_GUI_SPRITES = True

#GAME CONTROL VARIABLES

run = True

#LOOP CONSTANTS

AUTO_SCREEN_UPDATE = True
QUIT_BUTTON_FUNCTION = None

#OTHERS
DISPLAY_INFO = pygame.display.Info()



#---------------------------------------------EXCEPTIONS---------------------------------------------

class game_exceptions:

    class IncorrectParamException(Exception):
        def __init__(self, function_name : str, param_name : str,  correct_values=None):
            if correct_values:
                super().__init__(f"function {function_name} only accept values: " + ' '.join([str(v) for v in correct_values]) + f", for parameter: {param_name}.")
            else:
                super().__init__(f"wrong value was given for parameter: {param_name} in function: {function_name}.")
    
    class PathException(Exception):
        def __init__(self, err_path=None, message=None):
            if message:
                super().__init__(message)
            else:
                if err_path:
                    super().__init__(f"path: '{err_path}' is not a valid path.")
                else:
                    super().__init__("path given is not a valid path.")

    class UnableToFindPath(PathException):
        def __init__(self, err_path=None, reason=None):
            if err_path:
                if reason:
                    super().__init__(message=f'unable to search for path: "{err_path}", {reason}.')
                else:
                    super().__init__(message=f'unable to search for path: "{err_path}".')
            else:
                super().__init__(message="an exception was raised trying to search for a path.")

    class BadConfiguration(Exception):
        pass

    class SpriteException(Exception):
        pass

    class BadSpriteConfiguration(SpriteException, BadConfiguration):
        pass



#--------------------------------------CONFIGURATION FUNCTIONS---------------------------------------

def window_resize_x(param):
    global WINDOW, WINDOW_SIZE
    return round(param * WINDOW.get_size()[0] / WINDOW_SIZE[0])

def window_resize_y(param):
    global WINDOW, WINDOW_SIZE
    return round(param * WINDOW.get_size()[1] / WINDOW_SIZE[1])


def config_window_size():
    global WINDOW, WINDOW_SIZE, WINDOW_SCALE, ADAPT_ASPECT_RATIO, DISPLAY_INFO, PADDING_FUNCTIONAL_WINDOW, AUTO_CENTER_FUNCTIONAL_WINDOW

    if WINDOW_SIZE:
        WINDOW_SIZE = [int(size * WINDOW_SCALE) for size in WINDOW_SIZE]
    else:
        WINDOW_SIZE = [int(size * WINDOW_SCALE) for size in WINDOW.get_size()]
        
    if ADAPT_ASPECT_RATIO: #aspect ratio of the functional window will be the same as the monitor
        WINDOW_SIZE[1] = int(WINDOW_SIZE[0] * (DISPLAY_INFO.current_h / DISPLAY_INFO.current_w))
    WINDOW_SIZE = tuple(WINDOW_SIZE)

    if AUTO_CENTER_FUNCTIONAL_WINDOW:
        PADDING_FUNCTIONAL_WINDOW = ((WINDOW.get_size()[0] - WINDOW_SIZE[0]) // 2, (WINDOW.get_size()[1] - WINDOW_SIZE[1]) // 2)


#---------------------------------------CONFIGURATION CLASSES----------------------------------------

class GamePath:
    def __init__(self, name : str, path : str, game_path_list : list, children : list =[]):
        self.name = name
        self.path = path
        self.game_path_list = game_path_list
        self.children = children
        self.parent = None

    def __repr__(self):
        return self.name


class g_paths:
    game_path = os.getcwd()
    sprites_path = None
    sprites = []

    @staticmethod
    def build_paths(game_path_name : str, pathignore : str =None):
        if not hasattr(g_paths, game_path_name):
            raise game_exceptions.PathException(game_path_name)
        game_path_list = eval(f"g_paths.{game_path_name}")
        
        if eval(f"g_paths.{game_path_name}_path"): #if the user has set a custom path
            if os.sep in eval(f"g_paths.{game_path_name}_path"):
                current_path = eval(f"g_paths.{game_path_name}_path")
            else:
                current_path = os.path.join(g_paths.game_path, eval(f"g_paths.{game_path_name}_path"))
        else:
            current_path = os.path.join(g_paths.game_path, game_path_name) #default path

        ignore = []
        if pathignore:
            for p in pathignore:
                if not p.find('.'):
                    ignore.append(p)
                else:
                    ignore.append('.' + p)
            
        def build(current_path):
            nonlocal game_path_list, ignore
            
            if os.path.isfile(current_path):
                if all([os.path.splitext(current_path)[-1] != p for p in ignore]):
                    new_path = GamePath(os.path.splitext(current_path.split(os.sep)[-1])[0], current_path, game_path_list, [])
                    game_path_list.append(new_path)
                    return new_path

            elif os.path.isdir(current_path): #if the file is a directory, build function must be applied to its children
                children = []
                for p in os.listdir(current_path):
                    child = build(os.path.join(current_path, p)) #if pathignore is set build() may return None
                    if child:
                        children.append(child) #build function is applied to all the children recursively
                new_path = GamePath(os.path.splitext(current_path.split(os.sep)[-1])[0], current_path, game_path_list, children)
                game_path_list.append(new_path)
                return new_path

        build(current_path)
        if not game_path_list:
            exc_reason = f"couldn't create any path in g_paths.{game_path_name} list. Try to configure g_paths.{game_path_name}_path or check if your folder of interest is named '{game_path_name}'"
            raise game_exceptions.UnableToFindPath(game_path_name, exc_reason)
        
        for p in game_path_list:
            if p.name == game_path_name: #assigns a parent to the main directory (which is the game directory)
                p.parent = g_paths.game_path.split(os.sep)[-1]
            elif eval(f"g_paths.{game_path_name}_path"):
                if p.name == eval(f"g_paths.{game_path_name}_path").split(os.sep)[-1]:
                    p.parent = g_paths.game_path.split(os.sep)[-1]
                
            for child in p.children:
                child.parent = p
        
        return game_path_list


    @staticmethod
    def add(game_path_name : str, build=True):
        exec(f"g_paths.{game_path_name} = []")
        exec(f"g_paths.{game_path_name}_path = None")
        if build:
            g_paths.build_paths(game_path_name)


    @staticmethod
    def get(game_path_list : list, path_name : str, parent_name : str =None, child_name : str =None):
        found = []
        for p in game_path_list:
            if p.name == path_name:
                if parent_name:
                    if p.parent.name != parent_name:
                        continue
                if child_name:
                    if all([child.name != child_name for child in p.children]): #no child is the one specified in child_name
                        continue
                found.append(p)
                
        if len(found) == 1:
            return found[0]
        elif len(found) == 0:
            return None
        else:
            exc_message = f"multiple results were found: {found}. Try to provide a parent or a children directory to narrow down the results"
            raise game_exceptions.UnableToFindPath(path_name, exc_message)


#------------------------------------------GENERAL CLASSES-------------------------------------------

class Sprite:
    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls)
        if type(args[1]) == pygame.Surface or "image" in kwargs:
            obj._manual_init(*args, **kwargs)
        else:
            obj._standard_init(*args, **kwargs)
        return obj


    def _manual_init(self, name : str, image):
        self.name = name
        self.img = image
        self.img_rect = self.img.get_rect()
        self.dimension = (self.img_rect.w, self.img_rect.h)

        
    def _standard_init(self, name : str, path=None, parent_name : str =None, dimension : tuple =None, convert="alpha"):
        self.name = name
        if path:
            self.path = path
        else:
            path_obj = g_paths.get(g_paths.sprites, name, parent_name)
            if path_obj:
                self.path = path_obj.path
            else:
                exc_message = f"no paths were found with name {name} in 'g_paths.sprites'"
                raise game_exceptions.UnableToFindPath(name, exc_message)

        #chooses the convert method
        if convert != True and convert != False and convert != "alpha":
            raise IncorrectParamException("Sprite.__init__", "convert", [True, False, "alpha"])
        if convert == "alpha":
            self.img = pygame.image.load(self.path).convert_alpha()
        elif convert:
            self.img = pygame.image.load(self.path).convert()
        else:
            self.img = pygame.image.load(self.path)

        if dimension:
            self.img = pygame.transform.scale(self.img, dimension)

        self.img_rect = self.img.get_rect()


    def position(self, x, y, center=False):
        if center:
            self.img_rect.center = x, y
        else:
            self.img_rect.x, self.img_rect.y = x, y


    def draw(self, surface):
        surface.blit(self.img, self.img_rect)


    @staticmethod
    def _search_spritesheet(name, path, parent_name, convert):
        if path:
            sprites_path = path
        else:
            path_obj = g_paths.get(g_paths.sprites, name, parent_name)
            if path_obj:
                sprites_path = path_obj.path
            else:
                exc_message = f"no paths were found with name {name} in 'g_paths.sprites'"
                raise game_exceptions.UnableToFindPath(name, exc_message)

        if convert != True and convert != False and convert != "alpha":
            raise IncorrectParamException("Sprite.from_spritesheet", "convert", [True, False, "alpha"])
        if convert == "alpha":
            spritesheet_img = pygame.image.load(sprites_path).convert_alpha()
        elif convert:
            spritesheet_img = pygame.image.load(sprites_path).convert()
        else:
            spritesheet_img = pygame.image.load(sprites_path)

        return spritesheet_img, sprites_path


    @staticmethod
    def from_spritesheet(name : str, padding : tuple, columns : int, rows : int,
                         path=None, parent_name : str =None, dimension : tuple =None, convert="alpha"):
        
        spritesheet_img, sprites_path = Sprite._search_spritesheet(name, path, parent_name, convert)
        spritesheet_img_rect = spritesheet_img.get_rect()

        sprites = []
        sprite_num = 0
        sprite_w = spritesheet_img_rect.w / columns - padding[0]
        sprite_h = spritesheet_img_rect.h / rows - padding[1]

        for row in range(0, rows):
            for col in range(0, columns):
                sprite = Sprite(name+f"_{sprite_num}", sprites_path, parent_name, None, convert)
                sprites.append(sprite)
                sprite_num += 1
                
                if convert == "alpha":
                    sprite.img = pygame.Surface((sprite_w, sprite_h), pygame.SRCALPHA).convert_alpha()
                elif convert:
                    sprite.img = pygame.Surface((sprite_w, sprite_h)).convert()
                else:
                    sprite.img = pygame.Surface((sprite_w, sprite_h))
                sprite.img_rect = sprite.img.get_rect()

                sprite.img.blit(spritesheet_img,
                                  ( -col * (sprite_w + padding[0]) - padding[0] // 2,
                                   -row * (sprite_h + padding[1]) - padding[1] // 2
                                    )
                                )
        
        if dimension:
            for sprite in sprites:
                sprite.img = pygame.transform.scale(sprite.img, dimension)
                sprite.img_rect = sprite.img.get_rect()
       
        return sprites


    @staticmethod
    def from_non_regular_spritesheet(name : str, rects : list, path=None, parent_name : str =None, dimensions : list =None, convert="alpha"):
        spritesheet_img, sprites_path = Sprite._search_spritesheet(name, path, parent_name, convert)

        sprites = []
        sprite_num = 0

        for i, rect in enumerate(rects):
            sprite = Sprite(name+f"_{sprite_num}", sprites_path, parent_name, None, convert)
            sprites.append(sprite)
            sprite_num += 1
            
            if convert == "alpha":
                sprite.img = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA).convert_alpha()
            elif convert:
                sprite.img = pygame.Surface((rect.w, rect.h)).convert()
            else:
                sprite.img = pygame.Surface((rect.w, rect.h))
                
            sprite.img.blit(spritesheet_img, (-rect.x, -rect.y))
            if dimensions:
                sprite.img = pygame.transform.scale(sprite.img, dimensions[i])
                sprite.img_rect = sprite.img.get_rect()
       
        return sprites



class DynamicSprite:
    def __init__(self, build_function, sprites : dict, name : str):
        self.name = name
        self.sprites = sprites
        self.build_function = build_function
        self._id = 0


    def build_sprite(self, *args, **kwargs):
        build_result = self.build_function(self.sprites, *args, **kwargs)
        if type(build_result) == tuple:
            sprite, sprite_w, sprite_h = build_result
            final_sprite = pygame.Surface((sprite_w, sprite_h), pygame.SRCALPHA).convert_alpha()
            final_sprite.blit(sprite, (0,0))
        else:
            final_sprite = build_result
        self._id += 1
        return Sprite(self.name + f"_{self._id}", final_sprite)



class SpriteAnimation:
    def __init__(self, update_time, sprites : list, one_time=False):
        self.update_time = update_time
        self.one_time = one_time
        self.sprites = sprites
        
        self.cur_sprite = self.sprites[0]
        self.active = False
        
        self._prev_update_time = None
        self._cur_update_time = 0
        self._sprite_index = 0


    def position(self, x, y, center=False):
        for sprite in self.sprites:
            if center:
                sprite.img_rect.center = x, y
            else:
                sprite.img_rect.x, sprite.img_rect.y = x, y


    def update(self):
        if self.active:
            if self._prev_update_time == None:
                self._prev_update_time = time.time()
            self._cur_update_time = time.time()

            if self._cur_update_time - self._prev_update_time >= self.update_time: #animation changes current sprite
                self._sprite_index += 1
                if self._sprite_index >= len(self.sprites):
                    self._sprite_index = 0
                    if self.one_time:
                        self.active = False
                self.cur_sprite = self.sprites[self._sprite_index]
                self._prev_update_time = time.time()

    def draw(self, surface):
        surface.blit(self.cur_sprite.img, self.cur_sprite.img_rect)



class SpriteTransition:
    def __init__(self, initial_state : str, final_state : str, animation=None, duration=None, on_transition_begin=None, on_transition_end=None, on_next_state_begin=None):
        self.active = False
        self.name = initial_state + '-' + final_state
        self.initial_state = initial_state
        self.final_state = final_state
        self.animation = animation
        self.duration = duration
        self.on_transition_begin = on_transition_begin
        self.on_transition_end = on_transition_end
        self.on_next_state_begin = on_next_state_begin

        self._last_activation_time = 1


    def __repr__(self):
        return f"<SpriteTransition {self.name} active:{self.active}>"


    def activate(self):
        self.active = True
        if self.animation:
            self.animation.active = True
        if self.duration:
            self._last_activation_time = time.time()
        if self.on_transition_begin:
            self.on_transition_begin()

    def deactivate(self):
        self.active = False
        if self.animation:
            self.animation.active = False
        if self.on_transition_end:
            self.on_transition_end()


    def update(self):
        if self.animation:
            self.animation.update()

        if not self.duration and not self.animation:
            self.deactivate()

        if self.active:
            if self.duration:
                if time.time() - self._last_activation_time >= self.duration:
                    self.deactivate() #SpriteGroup will check that the animation is not active and will transition to the final state
            else:
                if self.animation:
                    if self.animation.one_time:
                        if not self.animation.active:
                            self.deactivate()


    def draw(self, surface):
        if self.animation:
            self.animation.draw(surface)



class SpriteGroup:
    def __init__(self, default : str, states : dict, transitions : list =[]):
        self.default = default
        self.cur_state = default
        self.states = {k.replace('-', '_'): v for k, v in states.items()}
        self.transitions = transitions

        if not self.states:
            exc_message = "SpriteTransition object cannot be initialized without defining any state."
            raise game_exceptions.BadSpriteConfiguration(exc_message)

        for transition in self.transitions:
            if transition.initial_state in self.states.keys() and transition.final_state in self.states.keys():
                continue
            exc_message = f"SpriteTransition states {transition.initial_state} or {transition.final_state}, do not match with any state specified in SpriteGroup object."
            raise game_exceptions.BadSpriteConfiguration(exc_message)


    def __repr__(self):
        return f"<{self.__class__.__name__} with states: {[k for k in self.states.keys()]}>"


    def __getitem__(self, key : str):
        return self.states[key]

    def __setitem__(self, key : str, value):
        self.states[key] = value


    def update_state_sprite_w_pos(self, state, new_sprite):
        sprite_pos = (self.states[state].img_rect.x, self.states[state].img_rect.y)
        self.states[state] = new_sprite
        new_sprite.img_rect.x, new_sprite.img_rect.y = sprite_pos


    def get_transition(self, name):
        for trans in self.transitions:
            if trans.name == name:
                return trans
        return None


    def position(self, x, y, center=False):
        for state in self.states.values():
            if state:
                state.position(x, y, center)

        for trans in self.transitions:
            if trans.animation:
                trans.animation.position(x, y, center)


    def change_state(self, new_state):
        if self.get_transition(self.cur_state): #if current state is a transition
            return
        if self.cur_state == new_state:
            return
        transition = self.get_transition(f"{self.cur_state}-{new_state}")
        if transition:
            self.cur_state = f"{self.cur_state}-{new_state}"
            transition.activate()
            return
        exc_message = f"Cannot change state of SpriteGroup '{self}' from {self.cur_state} to {new_state} due to the absence of a SpriteTransition."
        raise game_exceptions.BadSpriteConfiguration(exc_message)


    def update(self):
        transition = self.get_transition(self.cur_state)
        if self.cur_state in self.states.keys():
            cur_state_obj = self.states[self.cur_state]
        elif transition:
            cur_state_obj = transition
        else:
            exc_message = f"SpriteGroup '{self}' has unknown cur_state value: '{self.cur_state}'."
            raise game_exceptions.BadSpriteConfiguration(exc_message)
            
        if isinstance(cur_state_obj, SpriteAnimation) or isinstance(cur_state_obj, SpriteTransition):
            cur_state_obj.update()

        if isinstance(cur_state_obj, SpriteTransition):
            if not cur_state_obj.active:
                if self.states[cur_state_obj.final_state] == None:
                    self.cur_state = cur_state_obj.initial_state
                else:
                    self.cur_state = cur_state_obj.final_state
                if cur_state_obj.on_next_state_begin:
                    cur_state_obj.on_next_state_begin()


    def draw(self):
        global WINDOW

        transition = self.get_transition(self.cur_state)
        if self.cur_state in self.states.keys():
            cur_state_obj = self.states[self.cur_state]
        elif transition:
            cur_state_obj = transition
            
        if cur_state_obj:
            cur_state_obj.draw(WINDOW)



class ScreenElement:
    __elements = {}
    def __init__(self, coords : tuple):
        global PADDING_FUNCTIONAL_WINDOW, DRAW_OBJS_INSIDE_FUNCTIONAL_WINDOW
        
        ScreenElement.__elements.setdefault(type(self).__name__, [])
        ScreenElement.__elements[type(self).__name__].append(self)
        self.LOCK_RESIZE = False

        self._x = window_resize_x(coords[0])
        self._y = window_resize_y(coords[1])
        if DRAW_OBJS_INSIDE_FUNCTIONAL_WINDOW:
            self._x += PADDING_FUNCTIONAL_WINDOW[0]
            self._y += PADDING_FUNCTIONAL_WINDOW[1]


    def init_without_adaptation(self, coords : tuple):
        ScreenElement.__elements.setdefault(type(self).__name__, [])
        ScreenElement.__elements[type(self).__name__].append(self)
        self.LOCK_RESIZE = True
        self._x, self._y = coords


    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, new_x):
        self._x = new_x

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, new_y):
        self._y = new_y
        

    @classmethod
    def all(cls, strict=True):
        if strict:
            if cls.__name__ in ScreenElement.__elements.keys():
                return ScreenElement.__elements[cls.__name__]
            else:
                return []
        else:
            return ScreenElement.__elements


    def adjust_to_new_window_size(self, old_size, old_padding):
        global WINDOW_SIZE, PADDING_FUNCTIONAL_WINDOW, DRAW_OBJS_INSIDE_FUNCTIONAL_WINDOW
        
        if DRAW_OBJS_INSIDE_FUNCTIONAL_WINDOW:
            self._x = int((self._x - old_padding[0]) * WINDOW_SIZE[0] / old_size[0]) + PADDING_FUNCTIONAL_WINDOW[0]
            self._y = int((self._y - old_padding[1]) * WINDOW_SIZE[1] / old_size[1]) + PADDING_FUNCTIONAL_WINDOW[1]
        else:
            self._x = int(self._x * WINDOW_SIZE[0] / old_size[0])
            self._y = int(self._y * WINDOW_SIZE[1] / old_size[1])
        

    @classmethod
    def adjust_all_to_new_window_size(cls, old_size, old_padding):
        for elem in cls.all():
            elem.adjust_to_new_window_size(old_size, old_padding)



class GameObject(ScreenElement):
    def __init__(self):
        super().__init__((0, 0))
        self.sprite_group = None
        self.shapes = []

    def __repr__(self):
        return f"<GameObject at {self.x} {self.y}>"


    def config_coords(self, coords : tuple):
        global PADDING_FUNCTIONAL_WINDOW, DRAW_OBJS_INSIDE_FUNCTIONAL_WINDOW
        self.x = int(coords[0] * WINDOW_SIZE[0] / WINDOW.get_size()[0])
        self.y = int(coords[1] * WINDOW_SIZE[1] / WINDOW.get_size()[1])
        if DRAW_OBJS_INSIDE_FUNCTIONAL_WINDOW:
            self.x += PADDING_FUNCTIONAL_WINDOW[0]
            self.y += PADDING_FUNCTIONAL_WINDOW[1]


    def sync_sprites(self, center=False):
        if self.sprite_group == None:
            raise game_exceptions.BadSpriteConfiguration(f"{self} has no SpriteGroup, cannot call function 'sync_sprites'.")
        self.sprite_group.position(self.x, self.y, center)
    

    def event_update(self, event):
        pass
    

    def update(self):
        self.sprite_group.update()
        

    def fixed_update(self):
        if self.shapes:
            for shape in self.shapes:
                shape.shape_update()
    

    def draw(self):
        self.sprite_group.draw()


    def _auto_update(self):
        if self.shapes:
            for shape in self.shapes:
                shape.shape_auto_update()



class lglShape:
    drawing_color = (70, 250, 40)
    
    def __init__(self, game_object, coords=None, follow_func=None):
        self.game_object = game_object
        
        if coords:
            self._x = coords[0]
            self._y = coords[1]
        else:
            self._x = self.game_object.x
            self._y = self.game_object.y
            
        if follow_func:
            self.follow = follow_func
        else:
            def default_follow_func():
                self.x = self.game_object.x
                self.y = self.game_object.y


    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, new_x):
        self._x = new_x

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, new_y):
        self._y = new_y


    def shape_update(self):
        pass


    def shape_auto_update(self):
        pass


    def draw(self):
        pass



class lglCircle(lglShape):
    def __init__(self, game_object, radius, coords=None, follow_func=None):
        super().__init__(game_object, coords, follow_func)
        self.radius = radius


    def draw(self):
        pygame.draw.circle(lgl.WINDOW, lglShape.drawing_color, (self.x, self.y), self.radius)



#--------------------------------------------GUI CLASSES---------------------------------------------

class _GUIsectionslice:
    def __init__(self, section):
        self.slots = [] #list containing all the GUIobjects in this slice
        self.section = section

            
    def __getitem__(self, i):
        if i >= self.section.cols:
            self.section.cols = i + 1
            self.section.col_widths += [0] * (self.section.cols - len(self.section.col_widths))
            
            for slice_ in self.section.grid:
                if i >= len(slice_.slots):
                    slice_.slots += [None] * (self.section.cols - len(slice_.slots))
            return None
        else:
            return self.slots[i]

                
    def __setitem__(self, k, v):
        row = self.section.grid.index(self)
        
        if isinstance(v, gui.GUIobject):
            if k >= self.section.cols:
                self.section.cols = k + 1
                self.section.col_widths += [0] * (self.section.cols - len(self.section.col_widths))
                
                for slice_ in self.section.grid:
                    if k >= len(slice_.slots):
                        slice_.slots += [None] * (self.section.cols - len(slice_.slots)) #adds new columns by making each section slice list longer

            self.slots[k] = v
        else:
            exc_message = f"A non gui object: '{v}' was added to GUIsection:\n'{self.section}'."
            raise game_exceptions.BadConfiguration(exc_message)


    def __iter__(self):
        for obj in self.slots:
            yield obj

            
    def __len__(self):
        return len(self.slots)
        
    def __str__(self):
        return str(self.slots)
	    


class GUIsection(ScreenElement):
    def __init__(self, coords : tuple):
        super().__init__(coords)
        self.grid = []
        self.rows = 0
        self.cols = 0
        self.row_heights = []
        self.col_widths = []
        self.rect = pygame.Rect(self.x, self.y, 0, 0)

        self._hidden = False


    @ScreenElement.x.setter
    def x(self, new_x):
        old_x = self._x
        self._x = new_x
        self.rect.x = self._x
        for obj in self.all_objects():
            obj.x += self._x - old_x

    @ScreenElement.y.setter
    def y(self, new_y):
        old_y = self._y
        self._y = new_y
        self.rect.y = self._y
        for obj in self.all_objects():
            obj.y += self._y - old_y

		
    def __getitem__(self, i):
        if i >= self.rows:
            self.rows = i + 1
            
            for j in range(0, self.rows - len(self.grid)):
                gss = _GUIsectionslice(self)
                gss.slots = [None] * self.cols
                self.grid += [gss]
                self.row_heights.append(0)
        return self.grid[i]

	    
    def __setitem__(self, k, v):
        if k >= self.rows:
            self.rows = k + 1
            for j in range(0, self.rows - len(self.grid)):
                gss = _GUIsectionslice(self)
                gss.slots = [None] * self.cols
                self.grid += [gss]
                self.row_heights.append(0)
        self.grid[k] = v


    def __iter__(self):
        for slice_ in self.grid:
            yield slice_

		
    def __repr__(self):
        return f"<GUIsection ({self.rows} ; {self.cols})>"

        
    def __str__(self):
        s = ""
        maxlen = 34
        for slice_ in self.grid:
            for st in slice_.slots:
                if st:
                    s += repr(st.__class__).center(maxlen) + ' '
                else:
                    s += '--'.center(maxlen) + ' '
            s += '\n'*2
        return s[:-2]


    def configure_objects_pos(self):      
        for row, slice_ in enumerate(self.grid):
        
            heights = [gui_obj.rect.h + gui_obj.margins["top"] + gui_obj.margins["bottom"] for gui_obj in slice_ if gui_obj] #adjusts each row to fit the biggest object
            if heights:
                self.row_heights[row] = max(heights)
            else: # if row is empty
                self.row_heights[row] = 0
            
            for col, obj in enumerate(slice_):
                
                if row == 0: #same above but with each column
                    widths = [slice_.slots[col].rect.w + slice_.slots[col].margins["left"] + slice_.slots[col].margins["right"] for slice_ in self.grid if slice_.slots[col]]
                    if widths:
                        self.col_widths[col] = max(widths)
                    else: #if column is empty
                        self.col_widths[col] = 0

                if obj:
                    center_coords = [0, 0] #positions the new object
                    center_coords[0] = self.x + sum([w for w in self.col_widths[:col]]) + self.col_widths[col] // 2
                    center_coords[1] = self.y + sum([h for h in self.row_heights[:row]]) + self.row_heights[row] // 2
                    obj._config_position(tuple(center_coords))

        self.rect.w = sum(self.col_widths) #adjusts the dimension of the GUIsection
        self.rect.h = sum(self.row_heights)     


    def all_objects(self):
        for slice_ in self.grid:
            for obj in slice_:
                if obj:
                    yield obj


    def hide(self):
        self._hidden = True
        for obj in self.all_objects():
            obj.on_hide()


    def show(self):
        self._hidden = False
        for obj in self.all_objects():
            obj.on_show()


    def draw_grid(self, color=(40,40,40)):
        global WINDOW
        
        for row in range(self.rows + 1):
            sum([h for h in self.row_heights[:row]])
            pygame.draw.line(WINDOW, color,
                             (self.x, self.y + sum([h for h in self.row_heights[:row]])),
                             (self.x + self.rect.w, self.y + sum([h for h in self.row_heights[:row]])),
                             width=2)
            
        for col in range(self.cols + 1):
            pygame.draw.line(WINDOW, color,
                             (self.x + sum([w for w in self.col_widths[:col]]), self.y),
                             (self.x + sum([w for w in self.col_widths[:col]]), self.y + self.rect.h),
                             width=2)


    def event_update(self, event):
        for slice_ in self.grid:
            for slot in slice_.slots:
                if slot:
                    slot.event_update(event)


    def update(self):
        for slice_ in self.grid:
            for slot in slice_.slots:
                if slot:
                    slot.update()


    def draw(self):
        for slice_ in self.grid:
            for slot in slice_.slots:
                if slot:
                    slot.draw()



class gui:

    class GUIobject(ScreenElement):
        def __init__(self, section, margins={"top":0, "bottom":0, "left":0, "right":0}):
            self.section = section
            self.margins = margins
            self.rect = pygame.Rect(0,0,0,0)
            self.hitbox = pygame.Rect(0,0,0,0)


        @ScreenElement.x.setter
        def x(self, new_x):
            global AUTO_SYNC_GUI_SPRITES
            hitbox_rect_dist = self.hitbox.centerx - self.rect.centerx
            self._x = new_x
            self.rect.centerx = new_x
            self.hitbox.centerx = self.rect.centerx + hitbox_rect_dist
            if AUTO_SYNC_GUI_SPRITES:
                self.sync_sprites()

        @ScreenElement.y.setter
        def y(self, new_y):
            global AUTO_SYNC_GUI_SPRITES
            hitbox_rect_dist = self.hitbox.centery - self.rect.centery
            self._y = new_y
            self.rect.centery = new_y
            self.hitbox.centery = self.rect.centery + hitbox_rect_dist
            if AUTO_SYNC_GUI_SPRITES:
                self.sync_sprites()


        def __repr__(self):
            return f"<gui.{self.__class__.__name__}>"


        def sync_sprites(self, center=True):
            if hasattr(self, "sprite_group"):
                if self.sprite_group == None:
                    raise game_exceptions.BadSpriteConfiguration(f"{self} has no SpriteGroup, cannot call function 'sync_sprites'.")
                self.sprite_group.position(self.x, self.y, center)


        def _config_position(self, coords : tuple):
            super().init_without_adaptation(coords)


        def on_hide(self):
            pass

        def on_show(self):
            pass


        def event_update(self, event):
            pass


        def update(self):
            pass


        def draw(self):
            if hasattr(self, "sprite_group"):
                self.sprite_group.draw()



    class Button(GUIobject):
        def __init__(self, section, sprite_group, hitbox_size=None, hitbox_offset=(0,0), stay_clicked=False, margins={"top":0, "bottom":0, "left":0, "right":0}):
            super().__init__(section, margins)
            if hitbox_size:
                self.hitbox = pygame.Rect(0, 0, hitbox_size[0], hitbox_size[1])
            self.hitbox_offset = hitbox_offset
            
            self.idle_states = ["IDLE"] #by default "IDLE" is the sprite group state when the button is in idle state but more states can be added and will be managed in self.idle_function
            self.idle_function = None
            self.hovered_states = ["HOVERED"]
            self.hover_function = None
            self.clicked_states = ["CLICKED"]
            self.click_function = None
            self.state = "idle" #the states determines if the button is clicked hovered or idle, it's different from self.sprite_group.cur_state since it doesn't determine a sprite change
            self.stay_clicked = stay_clicked

            self.sprite_group = sprite_group
            sprite_obj = self.sprite_group.states[self.sprite_group.default] #takes the default sprite to set the button dimension
            if isinstance(sprite_obj, Sprite):
                self.rect = pygame.Rect(sprite_obj.img_rect)
            elif isinstance(sprite_obj, SpriteAnimation):
                self.rect = pygame.Rect(sprite_obj.sprites[0].img_rect)
                
            if not hitbox_size:
                self.hitbox = self.rect


        def _config_position(self, coords : tuple):
            super()._config_position(coords)
            self.rect.center = (self._x, self._y)
            self.hitbox.center = (self._x + self.hitbox_offset[0], self._y + self.hitbox_offset[1])
            self.sync_sprites(center=True)
        

        def event_update(self, event):
            if self.stay_clicked or self.state != "clicked": #no need to perform any calculation if the state is 'clicked' unless stay_clicked is True
                if not isinstance(self.sprite_group.cur_state, SpriteTransition): #also calculating if the button is clicked is not done if the sprite group state is transitioning
                    mouse_collides = self.hitbox.collidepoint(pygame.mouse.get_pos())

                    if self.state == "hovered" and not mouse_collides: #if the button is not clicked and the mouse is not on the button hitbox
                        self.state = "idle"
                    
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        if mouse_collides:
                            if self.stay_clicked:
                                if self.state == "clicked": #if stay_clicked is True the button will change it's state only on mouse press
                                    self.state = "hovered"
                                else:
                                    self.state = "clicked"
                            else:
                                self.state = "clicked"
                                
            if event.type == pygame.MOUSEBUTTONUP and not self.stay_clicked: #if the mouse is released the button is not clicked anymore unless stay_clicked is True
                self.state = "hovered"
        

        def update(self):
            self.sprite_group.update()

            if self.hitbox.collidepoint(pygame.mouse.get_pos()):
                if not self.state == "clicked":
                    self.state = "hovered"
            else:
                if not self.stay_clicked:
                    self.state = "idle"

            if self.state == "idle":
                state = None
                if self.idle_function:
                    state = idle_function()
                    if state:
                        self.sprite_group.change_state(state)
                if not state and self.idle_states:
                    self.sprite_group.change_state(self.idle_states[-1])
            elif self.state == "hovered":
                state = None
                if self.hover_function:
                    state = hover_function()
                    if state:
                        self.sprite_group.change_state(state)
                if not state and self.hovered_states:
                    self.sprite_group.change_state(self.hovered_states[-1])
            elif self.state == "clicked":
                state = None
                if self.click_function:
                    state = click_function()
                    if state:
                        self.sprite_group.change_state(state)
                if not state and self.clicked_states:
                    self.sprite_group.change_state(self.clicked_states[-1])



    class Slider(GUIobject):
        def __init__(self,
                     section,
                     value_range,
                     scroll_sprite_group,
                     bar_sprite_group,
                     hitbox_size=None,
                     hitbox_offset=(0,0),
                     margins={"top":0,"bottom":0,"left":0,"right":0},
                     calc_value=None,
                     calc_inverse_value=None):
            super().__init__(section, margins)

            self.value_range = value_range
            self.scroll_sprite_group = scroll_sprite_group
            self.bar_sprite_group = bar_sprite_group

            if type(value_range[0]) != int or type(value_range[1]) != int:
                exc_message = f"'value_range' parameter for '{self}' must be a tuple containing 2 int values, not '{value_range}'."
                raise game_exceptions.BadConfiguration(exc_message)

            #creates the hitbox
            if hitbox_size:
                self.hitbox = pygame.Rect(0, 0, hitbox_size[0], hitbox_size[1])
            else:
                self.hitbox = pygame.Rect(self.scroll_sprite_group[self.scroll_sprite_group.default].img_rect)
            self.hitbox_offset = hitbox_offset

            #sets up the functions to calculate the value
            if calc_value:
                self.calc_value = calc_value
            else:
                self.calc_value = lambda val : val
            if calc_inverse_value:
                self.calc_inverse_value = calc_inverse_value
            else:
                self.calc_inverse_value = lambda val : val

            self.state = "idle"
            self.move_scroll = False
            self._value = value_range[0] + (value_range[1] - value_range[0]) // 2
            self.rect = pygame.Rect(self.bar_sprite_group[self.bar_sprite_group.default].img_rect)
            self.rect.h = self.scroll_sprite_group[self.scroll_sprite_group.default].img_rect.h


        @property
        def value(self):
            return self.calc_value(self._value)

        @value.setter
        def value(self, new_val):
            old_value = self._value
            self._value = self.calc_inverse_value(new_val)
            if self._value < self.value_range[0]:
                self._value = self.value_range[0]
            elif self._value > self.value_range[1]:
                self._value = self.value_range[1]
            self.hitbox.x += self.value_to_x(self._value) - self.value_to_x(old_value)


        def mouse_pos_to_raw_value(self, mouse_pos : tuple):
            if mouse_pos[0] < self.value_to_x(self.value_range[0]):
                return self.value_range[0]
            elif mouse_pos[0] > self.value_to_x(self.value_range[1]):
                return self.value_range[1]
            return self.x_to_value(mouse_pos[0])


        def value_to_x(self, raw_value):
            bar_w = self.bar_sprite_group[self.bar_sprite_group.default].img_rect.w
            weight = (raw_value - self.value_range[0]) / (self.value_range[1] - self.value_range[0]) #inverse of lerp function to calculate weight
            return round(pygame.math.lerp(self._x - bar_w // 2, self._x + bar_w // 2, weight)) #weight of the value within the value range will be the same as self._x within the bar ends position

        def x_to_value(self, x):
            bar_w = self.bar_sprite_group[self.bar_sprite_group.default].img_rect.w
            weight = (x - self._x + bar_w // 2) / bar_w #denominator would be (self._x + bar_w // 2) - (self._x - bar_w // 2) which simplified is 2 * bar_w // 2
            return round(pygame.math.lerp(self.value_range[0], self.value_range[1], weight))


        def _config_position(self, coords : tuple):
            super()._config_position(coords)
            self.rect.center = (self._x, self._y)
            self.hitbox.center = (self._x + self.hitbox_offset[0], self._y + self.hitbox_offset[1])
            self.sync_sprites()


        def sync_sprites(self, scroll=True, bar=True, center=True):
            if scroll:
                self.scroll_sprite_group.position(self.value_to_x(self._value), self._y, center)
            if bar:
                self.bar_sprite_group.position(self._x, self._y, center)


        def on_hide(self):
            self.move_scroll = False


        def event_update(self, event):
            if self.state != "scroll clicked" and self.state != "bar clicked":
                self.state = "idle"
            mouse_pos = pygame.mouse.get_pos()

            if self.hitbox.collidepoint(mouse_pos):
                if self.state == "scroll clicked":
                    if event.type == pygame.MOUSEBUTTONUP:
                        self.state = "scroll hovered"
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.state = "scroll clicked"
                    self.move_scroll = True
                else:
                    self.state = "scroll hovered"

            elif self.bar_sprite_group[self.bar_sprite_group.default].img_rect.collidepoint(mouse_pos):
                if self.state == "bar clicked":
                    if event.type == pygame.MOUSEBUTTONUP:
                        self.state = "bar hovered"
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.state = "bar clicked"
                else:
                    self.state = "bar hovered"

            else:
                self.state = "idle"

            if event.type == pygame.MOUSEBUTTONUP:
                self.move_scroll = False


        def update(self):
            if self.move_scroll:
                self.value = self.calc_value(self.mouse_pos_to_raw_value(pygame.mouse.get_pos()))
                self.sync_sprites(bar=False)

            self.scroll_sprite_group.update()
            self.bar_sprite_group.update()


        def draw(self):
            self.bar_sprite_group.draw()
            self.scroll_sprite_group.draw()



    class VerticalScrollbar(ScreenElement):
        def __init__(self, link_object, coords : tuple, height : int, value_range : tuple, bar_sprite_group, scroll_sprite_group):
            super().__init__(coords)
            self.link_object = link_object
            self.height = window_resize_y(height)
            self.value_range = value_range
            if type(value_range[0]) != int or type(value_range[1]) != int:
                exc_message = f"'value_range' parameter for vertical scrollbars must be a tuple containing 2 int values, not '{value_range}'."
                raise game_exceptions.BadConfiguration(exc_message)
            self.bar_sprite_group = bar_sprite_group
            self.bar_rect = pygame.Rect(self.bar_sprite_group[self.bar_sprite_group.default].img_rect)
            self.scroll_sprite_group = scroll_sprite_group
            self.scroll_rect = pygame.Rect(self.scroll_sprite_group[self.scroll_sprite_group.default].img_rect)

            if self.bar_rect.w > self.scroll_rect.w: #calculates sprites position
                self.bar_rect.x, self.bar_rect.y = self.x, self.y
                self.scroll_rect.centerx, self.scroll_rect.y = self.bar_rect.centerx, self.y
            elif self.bar_rect.w <= self.scroll_rect.w:
                self.scroll_rect.x, self.scroll_rect.y = self.x, self.y
                self.bar_rect.centerx, self.bar_rect.y = self.scroll_rect.centerx, self.y
            
            self.bar_sprite_group.position(self.bar_rect.x, self.bar_rect.y)
            self.scroll_sprite_group.position(self.scroll_rect.x, self.scroll_rect.y)

            self.range = self.height - self.scroll_rect.h
            self.state = "idle"
            self.move_scroll = False

            #sets the initial position of the scroll so it is synced to the object
            original_scroll_rect = self.scroll_sprite_group[self.scroll_sprite_group.default].img_rect
            original_scroll_rect.y = round((link_object.y - value_range[0]) * self.range / (value_range[1] - value_range[0]) + self.y)
            if original_scroll_rect.y > self.y + self.range: #keeps the scroll y inside the bar length
                original_scroll_rect.y = self.y + self.range
            elif original_scroll_rect.y < self.y:
                original_scroll_rect.y = self.y
            self.sync_sprites(bar=False)


        def __repr__(self):
            return "<gui.VerticalScrollbar>"


        def sync_rects(self, scroll=True, bar=True):
            if scroll:
                self.scroll_rect = pygame.Rect(self.scroll_sprite_group[self.scroll_sprite_group.cur_state].img_rect)
            if bar:
                self.bar_rect = pygame.Rect(self.bar_sprite_group[self.bar_sprite_group.cur_state].img_rect)
            self.range = self.height - self.scroll_sprite_group[self.scroll_sprite_group.default].img_rect.h


        def sync_sprites(self, scroll=True, bar=True):
            scroll_sprite_transitioning = self.scroll_sprite_group.get_transition(self.scroll_sprite_group.cur_state)
            bar_sprite_transitioning = self.bar_sprite_group.get_transition(self.bar_sprite_group.cur_state)
            
            if scroll:
                if not scroll_sprite_transitioning:
                    scroll_def_rect = self.scroll_sprite_group[self.scroll_sprite_group.default].img_rect
                    self.scroll_sprite_group.position(scroll_def_rect.centerx, scroll_def_rect.centery, center=True)
            if bar:
                if not bar_sprite_transitioning:
                    bar_def_rect = self.bar_sprite_group[self.bar_sprite_group.default].img_rect
                    self.scroll_sprite_group.position(bar_def_rect.centerx, bar_def_rect.centery, center=True)

            if not scroll_sprite_transitioning and not bar_sprite_transitioning:
                self.sync_rects(scroll, bar)


        def event_update(self, event):
            if self.state != "scroll clicked" and self.state != "bar clicked":
                self.state = "idle"
            mouse_pos = pygame.mouse.get_pos()

            if self.scroll_rect.collidepoint(mouse_pos):
                if self.state == "scroll clicked":
                    if event.type == pygame.MOUSEBUTTONUP:
                        self.state = "scroll hovered"
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.state = "scroll clicked"
                    self.move_scroll = True
                else:
                    self.state = "scroll hovered"

            elif self.bar_rect.collidepoint(mouse_pos):
                if self.state == "bar clicked":
                    if event.type == pygame.MOUSEBUTTONUP:
                        self.state = "bar hovered"
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.state = "bar clicked"
                else:
                    self.state = "bar hovered"

            else:
                self.state = "idle"

            if event.type == pygame.MOUSEBUTTONUP:
                self.move_scroll = False


        def update(self):
            if self.move_scroll:
                original_scroll_rect = self.scroll_sprite_group[self.scroll_sprite_group.default].img_rect
                original_scroll_rect.y = pygame.mouse.get_pos()[1] - self.scroll_rect.h // 2
                if original_scroll_rect.y > self.y + self.range: #keeps the scroll y inside the bar length
                    original_scroll_rect.y = self.y + self.range
                elif original_scroll_rect.y < self.y:
                    original_scroll_rect.y = self.y
                self.sync_sprites(bar=False)
                self.link_object.y = round((self.value_range[1] - self.value_range[0]) * (original_scroll_rect.y - self.y) / self.range + self.value_range[0])
                
            self.bar_sprite_group.update()
            self.scroll_sprite_group.update()


        def draw(self):
            self.bar_sprite_group.draw()
            self.scroll_sprite_group.draw()



#--------------------------------------------DEBUG WINDOW--------------------------------------------

class debug:
    class DebugWin:
        _setup = False
        active = False
        style = {"bg col": (0,0,30),
                 "txt col": (240,245,243),
                 "secondary col": (200, 207, 205),
                 "bg alpha": 190,
                 "default margin": {"top": 20, "bottom": 0, "left":70},
                 "section margin": 20,
                 "title margin": 50,
                 "btn side": 30,
                 "slider scroll rad": 10,
                 }
        adjust = "right"
        debug_keys = [pygame.K_LESS]

        coords = None
        display_surface = None
        window_title_txt_obj = None
        window_title_txt_rect = None
        
        display = []
        display_section_separators = {}

        @classmethod
        def setup(cls, size):
            global WINDOW

            #display surface creation
            cls.display_surface = pygame.Surface(size, flags=pygame.SRCALPHA)
            cls.display_surface.fill(list(cls.style["bg col"]) + [cls.style["bg alpha"]])
            window_size = WINDOW.get_size()

            #window positioning
            if cls.adjust == "right":
                cls.coords = [window_size[0] - size[0], 0]
            elif cls.adjust == "left":
                cls.coords = [-size[0], 0]
            elif cls.adjust == "up":
                cls.coords = [0, -size[1]]
            elif cls.adjust == "down":
                cls.coords = [window_size[0] - size[0], window_size[1] - size[1]]

            #window title
            font_size = 66
            if cls.adjust == "right" or cls.adjust == "left":
                font_size = int(52 * size[0] / 600) + 14
            cls.window_title_txt_obj = pygame.font.SysFont('calibri', font_size).render('DEBUG WINDOW', True, list(cls.style["txt col"])+[255])
            cls.window_title_txt_rect = cls.window_title_txt_obj.get_rect()
            cls.window_title_txt_rect.x, cls.window_title_txt_rect.y = int(50 * size[0] / 600), int(50 * size[1] / 900)

            #creation of section separation text objects
            if type(cls.display) == dict:
                for section in cls.display.keys():
                    txt_obj = pygame.font.SysFont('calibri', 20).render(section, True, list(cls.style["secondary col"])+[240])
                    txt_rect = txt_obj.get_rect()
                    cls.display_section_separators[section] = [txt_obj, txt_rect]

            #final setup
            cls.sync_objects_pos()
            cls._setup = True


        @classmethod
        def sync_objects_pos(cls):
            x0 = 0
            y0 = 0
            if cls.adjust == "up" or cls.adjust == "down":
                x0 += cls.window_title_txt_rect.x + cls.window_title_txt_rect.w + cls.style["title margin"]
            if cls.adjust == "right" or cls.adjust == "left":
                y0 += cls.window_title_txt_rect.y + cls.window_title_txt_rect.h + cls.style["title margin"]
                    
            if type(cls.display) == list:
                for obj in cls.display:
                    obj.rect.x, obj.rect.y = x0 + obj.margin["left"], y0 + obj.margin["top"]
                    y0 += obj.rect.h + obj.margin["top"] + obj.margin["bottom"]

                    
            if type(cls.display) == dict:
                y0 -= cls.style["section margin"] #so that the first section display hasn't a section margin
                for section, objects in cls.display.items():
                    y0 += cls.style["section margin"]
                    section_tuple = cls.display_section_separators[section]
                    section_tuple[1].x, section_tuple[1].y = x0, y0
                    y0 += section_tuple[1].h
                    for obj in objects:
                        obj.rect.x, obj.rect.y = x0 + obj.margin["left"], y0 + obj.margin["top"]
                        y0 += obj.rect.h + obj.margin["top"] + obj.margin["bottom"]


        @classmethod
        def activate(cls):
            cls.active = True

        @classmethod
        def deactivate(cls):
            cls.active = False

        @classmethod
        def debug_update(cls, events):
            global WINDOW
            
            if cls._setup:
                for event in events:
                    if event.type == pygame.KEYDOWN:
                        if all([event.key == k for k in cls.debug_keys]): #if all keys are pressed
                            if cls.active:
                                cls.deactivate()
                            else:
                                cls.activate()
                        
                if cls.active:
                    cls.display_surface.fill(list(cls.style["bg col"]) + [cls.style["bg alpha"]])
                    cls.display_surface.blit(cls.window_title_txt_obj, cls.window_title_txt_rect)

                    if type(cls.display) == list:
                        for obj in cls.display:
                            obj.update(events)
                    elif type(cls.display) == dict:
                        for section, objects in cls.display.items():
                            section_tuple = cls.display_section_separators[section]
                            cls.display_surface.blit(section_tuple[0], section_tuple[1])
                            if cls.adjust == "left" or cls.adjust == "right":
                                pygame.draw.line(cls.display_surface,
                                                 list(cls.style["secondary col"])+[255],
                                                 (0, section_tuple[1].y - 5),
                                                 (cls.display_surface.get_rect().w, section_tuple[1].y - 5),
                                                 width=2)
                            for obj in objects:
                                obj.update(events)

                    WINDOW.blit(cls.display_surface, tuple(cls.coords))
                    pygame.display.update()

            else:
                if cls.active:
                    exc_message = "Debug window was activated but setup wasn't made. Call DebugWin.setup first."
                    raise game_exceptions.BadConfiguration(exc_message)



    class DebugVariableDisplay:
        def __init__(self, variable : str, names : dict ={}):
            mystyle = debug.DebugWin.style
            self.names = names
            for name, var in names.items():
                exec(name + f"=names['{name}']")
            self.txt_obj = pygame.font.SysFont('calibri', 22).render(variable+" :   "+repr(eval(variable)), True, list(mystyle["txt col"])+[255])
            self.rect = self.txt_obj.get_rect()
            self.variable = variable
            self.margin = mystyle["default margin"].copy()


        def update(self, events):
            x, y = self.rect.x, self.rect.y
            for name, var in self.names.items():
                exec(name + f"=self.names['{name}']")
            self.txt_obj = pygame.font.SysFont('calibri', 22).render(self.variable+" :   "+repr(eval(self.variable)), True, list(debug.DebugWin.style["txt col"])+[255])
            self.rect = self.txt_obj.get_rect()
            self.rect.x, self.rect.y = x, y
            
            debug.DebugWin.display_surface.blit(self.txt_obj, self.rect)


    class DebugButton:
        def __init__(self, function, text : str, stay_active : bool =False):
            mystyle = debug.DebugWin.style
            
            self.function = function
            self.stay_active = stay_active
            self.active = False
            
            btn_surf = pygame.Surface((mystyle["btn side"], mystyle["btn side"]))
            btn_surf.fill(mystyle["secondary col"])
            btn_surf_rect = btn_surf.get_rect()
            txt_obj = pygame.font.SysFont('calibri', 22).render(text, True, list(mystyle["txt col"])+[255])
            txt_obj_rect = txt_obj.get_rect()
            self.surf = pygame.Surface((btn_surf.get_rect().w + 30 + txt_obj.get_rect().w, max([btn_surf.get_rect().h, txt_obj.get_rect().h])), flags=pygame.SRCALPHA)
            self.rect = self.surf.get_rect()
            btn_surf_rect.centery = self.rect.h // 2
            txt_obj_rect.x, txt_obj_rect.centery = btn_surf_rect.w + 30, self.rect.h // 2
            self.surf.blit(btn_surf, btn_surf_rect)
            self.surf.blit(txt_obj, txt_obj_rect)
            self.margin = mystyle["default margin"].copy()


        def update(self, events):
            global WINDOW
            debug.DebugWin.display_surface.blit(self.surf, self.rect)

            hitbox = pygame.Rect(self.rect)
            if debug.DebugWin.adjust == "right":
                hitbox.x += debug.DebugWin.coords[0]
            elif debug.DebugWin.adjust == "down":
                hitbox.y += debug.DebugWin.coords[1]
            hovered = hitbox.collidepoint(pygame.mouse.get_pos())

            if self.active:
                self.function()

            if hovered or self.active:
                winsize = WINDOW.get_size()
                hover_rect = pygame.Rect(self.rect[0] + 5, self.rect[1] + 5, debug.DebugWin.style["btn side"] - 10, debug.DebugWin.style["btn side"] - 10)
                hover_rect.centery = self.rect.centery
                pygame.draw.rect(debug.DebugWin.display_surface, list(debug.DebugWin.style["txt col"])+[255], hover_rect)
                
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if hovered:
                        self.function()
                        
                        if self.stay_active:
                            if self.active:
                                self.active = False
                            else:
                                self.active = True



    class DebugSlider:
        def __init__(self, value_range : tuple, variable : str, names : dict ={}, width :  int =300, only_int : bool =True):
            mystyle = debug.DebugWin.style

            for name, var in names.items():
                exec(name + f"=names['{name}']")
            
            self.variable = variable
            if not(type(eval(variable)) == int or type(eval(variable)) == float):
                exc_message = f"DebugSlider only accepts variables of int and float types. variable '{variable}' does not meet the requirements."
                raise game_exceptions.BadConfiguration(exc_message)
            self.value_range = value_range
            self.names = names
            self.width = width
            self.only_int = only_int
            self.margin = mystyle["default margin"].copy()
            self.changing = False

            #variable will be changed based on the scroll position so the scroll must be positioned according to the variable value initially
            #otherwise on the first update call the variable value will change without a user action
            if eval(variable) < value_range[0]:
                first_scroll_state = self.margin["left"]
            elif eval(variable) > value_range[1]:
                first_scroll_state = self.margin["left"] + width
            else:
                #(eval(variable) - value_range[0]) * width / (value_range[1] - value_range[0]) + self.margin['left'] = first_scroll_state
                first_scroll_state = round((eval(variable) - value_range[0]) * width / (value_range[1] - value_range[0]) + self.margin['left'])

            self.txt_obj = pygame.font.SysFont('calibri', 18).render(variable, True, list(mystyle["txt col"])+[255])
            self.scroll_rect = pygame.draw.circle(pygame.Surface((1000,1000)), list(mystyle["txt col"])+[255], (first_scroll_state,0), mystyle["slider scroll rad"])
            self.rect = pygame.Rect(0,0,width,self.txt_obj.get_rect().h+10+self.scroll_rect.h)


        def update(self, events):
            for name, var in self.names.items():
                    exec(name + f"=self.names['{name}']")
            var_txt_obj = pygame.font.SysFont('calibri', 18).render(repr(eval(self.variable)), True, list(debug.DebugWin.style["txt col"])+[255])
            if self.changing:
                circle_col = list(debug.DebugWin.style["txt col"])+[255]
            else:
                circle_col = list(debug.DebugWin.style["secondary col"])+[255]
            
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = list(pygame.mouse.get_pos())
                    mouse_pos[0] -= debug.DebugWin.coords[0]
                    mouse_pos[1] -= debug.DebugWin.coords[1]
                    if self.scroll_rect.collidepoint(mouse_pos):
                        self.changing = True
                        circle_col = list(debug.DebugWin.style["txt col"])+[255]
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.changing = False
                    circle_col = list(debug.DebugWin.style["secondary col"])+[255]
                    
            self.scroll_rect.centery = self.rect.y + self.txt_obj.get_rect().y + self.txt_obj.get_rect().h + 10 + debug.DebugWin.style["slider scroll rad"]
            if self.changing:
                mouse_pos = list(pygame.mouse.get_pos())
                mouse_pos[0] -= debug.DebugWin.coords[0]
                mouse_pos[1] -= debug.DebugWin.coords[1]
                if mouse_pos[0] < self.margin["left"]:
                    self.scroll_rect.centerx = self.margin["left"]
                elif mouse_pos[0] > self.margin["left"] + self.width:
                    self.scroll_rect.centerx = self.margin["left"] + self.width
                else:
                    self.scroll_rect.centerx = mouse_pos[0]
                #adjusts the variable to the scroll position
                exec(self.variable + f"= ({self.value_range}[1] - {self.value_range}[0]) * ({self.scroll_rect.centerx} - {self.margin}['left']) / {self.width} + {self.value_range}[0]")
                if self.only_int:
                    exec(self.variable + "= round(" + self.variable + ")")
            
            debug.DebugWin.display_surface.blit(self.txt_obj, self.rect)
            debug.DebugWin.display_surface.blit(var_txt_obj, (self.rect.x + self.txt_obj.get_rect().w + 40, self.rect.y))
            pygame.draw.line(debug.DebugWin.display_surface,
                             list(debug.DebugWin.style["secondary col"])+[255],
                             (self.rect.x, self.scroll_rect.centery),
                             (self.rect.x + self.rect.w, self.scroll_rect.centery),
                             width=6)
            pygame.draw.circle(debug.DebugWin.display_surface,
                               circle_col,
                               self.scroll_rect.center,
                               debug.DebugWin.style["slider scroll rad"])
	    
        
#-----------------------------------INGAME CONFIGURATION FUNCTIONS-----------------------------------

def rescale_window(new_scale, classes=[]):
    global WINDOW_SIZE, WINDOW_SCALE, PADDING_FUNCTIONAL_WINDOW

    old_padding = PADDING_FUNCTIONAL_WINDOW
    WINDOW_SCALE = new_scale
    old_size = WINDOW_SIZE
    config_window_size()

    if classes:
        for c in classes:
            c.adjust_all_to_new_window_size(old_size, old_padding)
    else:
        for cls_name in ScreenElement.all(strict=False).values(): #returns all objects that inherit from ScreenElement
            exec(cls_name+".adjust_all_to_new_window_size(old_size, old_padding)")
        #GameObject.adjust_all_to_new_window_size(old_size, old_padding)
        
    
#----------------------------------------------MAINLOOP----------------------------------------------

class MainLoop:
    run = False
    fix_update_time = 0.01
    
    ev_update = None
    update = None
    fix_update = None
    gfx_update = None

    @classmethod
    def start(cls):
        cls.run = True
        cls.loop()
        pygame.quit()

    @classmethod
    def end(cls):
        cls.run = False
        

    @classmethod
    def loop(cls, ev_update=None, update=None, fix_update=None, gfx_update=None):
        global run, WINDOW
        global WINDOW_SIZE, WINDOW_SCALE, PADDING_FUNCTIONAL_WINDOW, FUNCTIONAL_WINDOW_BORDERS, FUNCTIONAL_WINDOW_BORDER_COL
        global AUTO_SCREEN_UPDATE, QUIT_BUTTON_FUNCTION

        last_fix_update_time = time.time()
        
        while cls.run:
            WINSIZE = WINDOW.get_size()

            events = pygame.event.get()
            keys = pygame.key.get_pressed()
            
            for event in events:
                if event.type == pygame.QUIT:
                    if QUIT_BUTTON_FUNCTION:
                        QUIT_BUTTON_FUNCTION()
                    else:
                        cls.end()

            if cls.ev_update:
                cls.ev_update(events, keys)
                
            if cls.update:
                cls.update()
                
            if cls.gfx_update:
                cls.gfx_update()

            if cls.fix_update:
                if time.time() - last_fix_update_time >= cls.fix_update_time:
                    cls.fix_update()
                    last_fix_update_time = time.time()
            
            if FUNCTIONAL_WINDOW_BORDERS:
                pygame.draw.rect(WINDOW, FUNCTIONAL_WINDOW_BORDER_COL,
                                 (0, 0, WINSIZE[0], PADDING_FUNCTIONAL_WINDOW[1])
                                 )
                pygame.draw.rect(WINDOW, FUNCTIONAL_WINDOW_BORDER_COL,
                                 (0, PADDING_FUNCTIONAL_WINDOW[1], PADDING_FUNCTIONAL_WINDOW[0], WINSIZE[1])
                                 )
                pygame.draw.rect(WINDOW, FUNCTIONAL_WINDOW_BORDER_COL,
                                 (WINSIZE[0] - PADDING_FUNCTIONAL_WINDOW[0], PADDING_FUNCTIONAL_WINDOW[1], WINSIZE[0], WINSIZE[1])
                                 )
                pygame.draw.rect(WINDOW, FUNCTIONAL_WINDOW_BORDER_COL,
                                 (PADDING_FUNCTIONAL_WINDOW[0], WINSIZE[1] - PADDING_FUNCTIONAL_WINDOW[1], WINSIZE[0] - PADDING_FUNCTIONAL_WINDOW[0], WINSIZE[1])
                                 )

            debug.DebugWin.debug_update(events)
                
            if AUTO_SCREEN_UPDATE:
                pygame.display.update()
