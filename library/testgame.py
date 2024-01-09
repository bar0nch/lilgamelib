import sys, os
sys.path.append(os.path.join(os.getcwd(), "test", "test2"))

import pygame
import lilgamelib as lgl
import time

pygame.init()

#lgl.FUNCTIONAL_WINDOW_BORDERS = True


lgl.WINDOW_SIZE = (1000, 700)
lgl.WINDOW = pygame.display.set_mode(flags=pygame.FULLSCREEN)
lgl.config_window_size()


lgl.g_paths.build_paths("sprites", pathignore=['.kra', '.kra~'])

ball_sprites = lgl.Sprite.from_spritesheet("ball animation", (2, 2), columns=4, rows=3, dimension=(128, 128))
ball_shine = lgl.SpriteAnimation(update_time=0.09, sprites=ball_sprites[1:4], one_time=True)
ball_bluify = lgl.SpriteAnimation(update_time=0.1, sprites=ball_sprites[4:9], one_time=True)
redify_sprite_list = ball_sprites[4:9][:]
redify_sprite_list.reverse()
ball_redify = lgl.SpriteAnimation(update_time=0.1, sprites=redify_sprite_list, one_time=True)
blue_ball_shine = lgl.SpriteAnimation(update_time=0.09, sprites=ball_sprites[9:], one_time=True)

ball = lgl.GameObject()
ball.config_coords((100,100))
ball.sprite_group = lgl.SpriteGroup(default="idle",
                                    states={"idle":ball_sprites[0],
                                            "shine":None,
                                            "blue":ball_sprites[8],
                                            "blue_shine":None},
                                    transitions=[lgl.SpriteTransition("idle", "shine", ball_shine),
                                                 lgl.SpriteTransition("idle", "blue", ball_bluify),
                                                 lgl.SpriteTransition("blue", "idle", ball_redify),
                                                 lgl.SpriteTransition("blue", "blue_shine", blue_ball_shine),
                                                 ]
                                    )
ball.sync_sprites()



class MySlider(lgl.gui.Slider):
    slider_sprites = lgl.Sprite.from_non_regular_spritesheet("slider",
                                                             [pygame.Rect(0,0,12,12),
                                                              pygame.Rect(12,0,12,12),
                                                              pygame.Rect(24,0,1,6),
                                                              pygame.Rect(25,0,6,6),
                                                              pygame.Rect(25,6,6,6)],
                                                             dimensions=[(48,48), (48,48), (4,24), (24,24), (24,24)])
    bar_sprites_dict = {"mid":slider_sprites[2],
                        "left":slider_sprites[3],
                        "right":slider_sprites[4]}

    @staticmethod
    def bar_build_func(sprites, length):
        bar_surf = pygame.Surface((lgl.WINDOW.get_size()[0], sprites["mid"].img_rect.h), pygame.SRCALPHA)
        bar_surf_rect = bar_surf.get_rect()

        bar_surf.blit(sprites["left"].img, (0,0))
        mid_bar_images = 0
        bar_ends_width = sprites["left"].img_rect.w + sprites["right"].img_rect.w
        
        for x in range(sprites["left"].img_rect.w, length - sprites["left"].img_rect.w, sprites["mid"].img_rect.w):
            segment = sprites["mid"].img.copy()
            segment_rect = segment.get_rect()
            segment_rect.x = x
            segment_rect.centery = bar_surf_rect.centery
            bar_surf.blit(segment, segment_rect)
            mid_bar_images += 1

        bar_surf.blit(sprites["right"].img, (sprites["left"].img_rect.w + sprites["mid"].img_rect.w * mid_bar_images, 0))
        
        return bar_surf, sprites["mid"].img_rect.w * mid_bar_images + bar_ends_width, sprites["mid"].img_rect.h

    bar_ds = lgl.DynamicSprite(bar_build_func, bar_sprites_dict, "bar")

    def __init__(self, section, value_range, length, margins={"top":0,"bottom":0,"left":0,"right":0}):
        scroll_sprite_group = lgl.SpriteGroup(default="idle",
                                              states={"idle":self.slider_sprites[0], "moving":self.slider_sprites[1]},
                                              transitions=[lgl.SpriteTransition("idle", "moving"),
                                                           lgl.SpriteTransition("moving", "idle")])
        bar_sprite_group = lgl.SpriteGroup(default="bar", states={"bar":self.bar_ds.build_sprite(length)})

        super().__init__(section, value_range, scroll_sprite_group, bar_sprite_group, margins=margins)

    def update(self):
        super().update()
        if self.move_scroll:
            self.scroll_sprite_group.change_state("moving")
        else:
            self.scroll_sprite_group.change_state("idle")



class MyScrollbar:
    scrollbar_sprites = lgl.Sprite.from_non_regular_spritesheet("scrollbar_compressed",
                                                                [pygame.Rect(0,0,2,1),
                                                                 pygame.Rect(2,0,4,3),
                                                                 pygame.Rect(2,4,4,2),
                                                                 pygame.Rect(6,0,4,3),
                                                                 pygame.Rect(6,4,4,2),
                                                                 pygame.Rect(10,0,6,6),
                                                                 pygame.Rect(16,0,6,2),
                                                                 pygame.Rect(22,0,6,6),
                                                                 pygame.Rect(16,4,6,2),
                                                                 pygame.Rect(28,0,6,3),
                                                                 pygame.Rect(28,3,6,3)],
                                                                dimensions=[(8, 4),
                                                                            (16, 12),
                                                                            (16, 8),
                                                                            (16, 12),
                                                                            (16, 8),
                                                                            (24, 24),
                                                                            (24, 8),
                                                                            (24, 24),
                                                                            (24, 8),
                                                                            (24, 12),
                                                                            (24, 12),])

    scrollbar_sprites_dict = {"bar": scrollbar_sprites[0],
                              "idle bar top": scrollbar_sprites[1],
                              "idle bar midtop": scrollbar_sprites[2],
                              "idle bar bottom": scrollbar_sprites[3],
                              "idle bar midbottom": scrollbar_sprites[4],
                              "moving bar top": scrollbar_sprites[5],
                              "moving bar midtop": scrollbar_sprites[6],
                              "moving bar bottom": scrollbar_sprites[7],
                              "moving bar midbottom": scrollbar_sprites[8],
                              "moving bar short top": scrollbar_sprites[9],
                              "moving bar short bottom": scrollbar_sprites[10]}

    @staticmethod
    def bar_build_func(sprites, height, adapt_height=True):
        bar_surf = pygame.Surface((sprites["bar"].img_rect.w, lgl.WINDOW.get_size()[1]), pygame.SRCALPHA)
        bar_surf_rect = bar_surf.get_rect()
        if adapt_height:
            adapted_height = lgl.window_resize_y(height)
        else:
            adapted_height = height
        for y in range(sprites["bar"].img_rect.h, adapted_height, sprites["bar"].img_rect.h):
            segment = sprites["bar"].img.copy()
            segment_rect = segment.get_rect()
            segment_rect.centerx = bar_surf_rect.centerx
            segment_rect.y = y
            bar_surf.blit(segment, segment_rect)
        return bar_surf, sprites["bar"].img_rect.w, adapted_height - sprites["bar"].img_rect.h

    @staticmethod
    def idle_scroll_build_func(sprites):
        scroll_surf_height = sprites["idle bar top"].img_rect.h + sprites["idle bar midtop"].img_rect.h * 2 + sprites["idle bar midbottom"].img_rect.h * 2 + sprites["idle bar bottom"].img_rect.h
        scroll_surf = pygame.Surface((sprites["idle bar top"].img_rect.w, scroll_surf_height), pygame.SRCALPHA)
        scroll_surf.blit(sprites["idle bar top"].img, (0,0))
        scroll_surf.blit(sprites["idle bar midtop"].img, (0,sprites["idle bar top"].img_rect.h))
        scroll_surf.blit(sprites["idle bar midtop"].img, (0,sprites["idle bar top"].img_rect.h+sprites["idle bar midtop"].img_rect.h))
        scroll_surf.blit(sprites["idle bar midbottom"].img, (0,sprites["idle bar top"].img_rect.h+sprites["idle bar midtop"].img_rect.h*2))
        scroll_surf.blit(sprites["idle bar midbottom"].img, (0,sprites["idle bar top"].img_rect.h+sprites["idle bar midtop"].img_rect.h*2+sprites["idle bar midbottom"].img_rect.h))
        scroll_surf.blit(sprites["idle bar bottom"].img, (0,sprites["idle bar top"].img_rect.h+sprites["idle bar midtop"].img_rect.h*2+sprites["idle bar midbottom"].img_rect.h*2))
        return scroll_surf

    @staticmethod
    def pushed_scroll_build_func(sprites):
        scroll_surf_height = sprites["moving bar top"].img_rect.h + sprites["moving bar midtop"].img_rect.h * 2 + sprites["moving bar midbottom"].img_rect.h * 2 + sprites["moving bar bottom"].img_rect.h
        scroll_surf = pygame.Surface((sprites["moving bar top"].img_rect.w, scroll_surf_height), pygame.SRCALPHA)
        scroll_surf.blit(sprites["moving bar top"].img, (0,0))
        scroll_surf.blit(sprites["moving bar midtop"].img, (0,sprites["moving bar top"].img_rect.h))
        scroll_surf.blit(sprites["moving bar midtop"].img, (0,sprites["moving bar top"].img_rect.h+sprites["moving bar midtop"].img_rect.h))
        scroll_surf.blit(sprites["moving bar midbottom"].img, (0,sprites["moving bar top"].img_rect.h+sprites["moving bar midtop"].img_rect.h*2))
        scroll_surf.blit(sprites["moving bar midbottom"].img, (0,sprites["moving bar top"].img_rect.h+sprites["moving bar midtop"].img_rect.h*2+sprites["moving bar midbottom"].img_rect.h))
        scroll_surf.blit(sprites["moving bar bottom"].img, (0,sprites["moving bar top"].img_rect.h+sprites["moving bar midtop"].img_rect.h*2+sprites["moving bar midbottom"].img_rect.h*2))
        return scroll_surf

    bar_ds = lgl.DynamicSprite(bar_build_func, scrollbar_sprites_dict, "bar")
    scroll_i_ds = lgl.DynamicSprite(idle_scroll_build_func, scrollbar_sprites_dict, "idle_scroll")
    scroll_p_ds = lgl.DynamicSprite(pushed_scroll_build_func, scrollbar_sprites_dict, "pushed_scroll")
    
    def __init__(self, link_object, coords : tuple, height : int, value_range : tuple):
        def scrollsync():
            self.scrollbar.sync_sprites(bar=False)
        bar_spritegroup = lgl.SpriteGroup(default="bar",
                                          states={"bar":self.bar_ds.build_sprite(height)})
        scroll_spritegroup = lgl.SpriteGroup(default="idle",
                                             states={"idle":self.scroll_i_ds.build_sprite(), "pushed":self.scroll_p_ds.build_sprite()},
                                             transitions=[lgl.SpriteTransition("idle", "pushed", on_next_state_begin=scrollsync),
                                                          lgl.SpriteTransition("pushed", "idle", on_next_state_begin=scrollsync)])
        self.scrollbar = lgl.gui.VerticalScrollbar(link_object, coords, height, value_range, bar_spritegroup, scroll_spritegroup)
        self.scrollbar.sync_sprites(bar=False)


    def event_update(self, event):
        self.scrollbar.event_update(event)

    def update(self):
        if self.scrollbar.move_scroll:
            my_scrollbar.scrollbar.scroll_sprite_group.change_state("pushed")
        else:
            my_scrollbar.scrollbar.scroll_sprite_group.change_state("idle")
        
        self.scrollbar.update()
        self.scrollbar.bar_sprite_group.update_state_sprite_w_pos("bar", self.bar_ds.build_sprite(self.scrollbar.height, adapt_height=False))
        if not my_scrollbar.scrollbar.scroll_sprite_group.get_transition(my_scrollbar.scrollbar.scroll_sprite_group.cur_state):
            self.scrollbar.sync_rects(scroll=False)

    def draw(self):
        self.scrollbar.draw()



button_sprites = lgl.Sprite.from_spritesheet("buttons", (2, 2), columns=6, rows=2, dimension=(128, 128))

btn1_hover_anim = lgl.SpriteAnimation(update_time=0.08, sprites=button_sprites[1:3], one_time=True)
btn1_reverse_hover_anim = lgl.SpriteAnimation(update_time=0.08, sprites=[button_sprites[2],button_sprites[1]], one_time=True)
btn1_click_anim = lgl.SpriteAnimation(update_time=0.3, sprites=[button_sprites[4]], one_time=True)
button1_spritegroup = lgl.SpriteGroup(default="IDLE",
                                      states={"IDLE":button_sprites[0],
                                              "HOVERED":button_sprites[3],
                                              "CLICKED":button_sprites[5],
                                              },
                                      transitions=[lgl.SpriteTransition("IDLE", "HOVERED", btn1_hover_anim),
                                                   lgl.SpriteTransition("HOVERED", "IDLE", btn1_reverse_hover_anim),
                                                   lgl.SpriteTransition("HOVERED", "CLICKED", btn1_click_anim),
                                                   lgl.SpriteTransition("CLICKED", "HOVERED", btn1_click_anim),
                                                   lgl.SpriteTransition("CLICKED", "IDLE", btn1_reverse_hover_anim)]
                                      )

btn2_hover_anim = lgl.SpriteAnimation(update_time=0.08, sprites=button_sprites[7:9], one_time=True)
btn2_reverse_hover_anim = lgl.SpriteAnimation(update_time=0.08, sprites=[button_sprites[8],button_sprites[7]], one_time=True)
btn2_click_anim = lgl.SpriteAnimation(update_time=0.3, sprites=[button_sprites[10]], one_time=True)
button2_spritegroup = lgl.SpriteGroup(default="IDLE",
                                      states={"IDLE":button_sprites[6],
                                              "HOVERED":button_sprites[9],
                                              "CLICKED":button_sprites[11],
                                              },
                                      transitions=[lgl.SpriteTransition("IDLE", "HOVERED", btn2_hover_anim),
                                                   lgl.SpriteTransition("HOVERED", "IDLE", btn2_reverse_hover_anim),
                                                   lgl.SpriteTransition("HOVERED", "CLICKED", btn2_click_anim),
                                                   lgl.SpriteTransition("CLICKED", "HOVERED", btn2_click_anim),
                                                   lgl.SpriteTransition("CLICKED", "IDLE", btn2_reverse_hover_anim)]
                                      )

test_gui = lgl.GUIsection((200,100))
test_gui[0][0] = lgl.gui.Button(test_gui, button1_spritegroup, (int(20*128/32),int(26*128/32)), stay_clicked=True)
test_gui[0][0].margins = {"top":20, "bottom":20, "left":20, "right":20}
test_gui[0][1] = lgl.gui.Button(test_gui, button2_spritegroup, (int(20*128/32),int(26*128/32)))
test_gui[0][1].margins = {"top":20, "bottom":20, "left":20, "right":20}
test_gui[1][0] = MySlider(test_gui, (50, 100), 400)
test_gui[1][0].margins = {"top":20, "bottom":20, "left":20, "right":20}
test_gui.configure_objects_pos()

my_scrollbar = MyScrollbar(test_gui, (550, 100), 400, (lgl.window_resize_y(100), lgl.window_resize_y(300)))



def draw_hitboxes():
    for obj in test_gui.all_objects():
        pygame.draw.rect(lgl.WINDOW, (250, 0, 240), obj.hitbox, width=3)
def draw_rects():
    for obj in test_gui.all_objects():
        pygame.draw.rect(lgl.WINDOW, (220, 20, 20), obj.rect, width=3)
    pygame.draw.rect(lgl.WINDOW, (20, 20, 220), my_scrollbar.scrollbar.bar_rect, width=2)
    pygame.draw.rect(lgl.WINDOW, (220, 20, 20), my_scrollbar.scrollbar.scroll_rect, width=2)
def draw_gui_rect():
    test_gui.draw_grid()

lgl.debug.DebugWin.display.append(lgl.debug.DebugVariableDisplay("pygame.mouse.get_pos()"))
lgl.debug.DebugWin.display[-1].margin["bottom"] += 40
lgl.debug.DebugWin.display.append(lgl.debug.DebugVariableDisplay("test_gui.rect", {"test_gui":test_gui}))
lgl.debug.DebugWin.display.append(lgl.debug.DebugVariableDisplay("restart_button.rect", {"restart_button":test_gui[0][0]}))
lgl.debug.DebugWin.display.append(lgl.debug.DebugVariableDisplay("x_button.rect", {"x_button":test_gui[1][0]}))
lgl.debug.DebugWin.display.append(lgl.debug.DebugVariableDisplay("slider.value", {"slider":test_gui[1][0]}))
lgl.debug.DebugWin.display[-1].margin["bottom"] += 20
lgl.debug.DebugWin.display.append(lgl.debug.DebugButton(draw_hitboxes, "hitboxes", stay_active=True))
lgl.debug.DebugWin.display.append(lgl.debug.DebugButton(draw_rects, "rects", stay_active=True))
lgl.debug.DebugWin.display[-1].margin["bottom"] += 20
lgl.debug.DebugWin.display.append(lgl.debug.DebugButton(draw_gui_rect, "gui rect", stay_active=True))
lgl.debug.DebugWin.display[-1].margin["bottom"] += 60
lgl.debug.DebugWin.display.append(lgl.debug.DebugSlider((200,600), "scrollbar.height", {"scrollbar":my_scrollbar.scrollbar}))
lgl.debug.DebugWin.setup((600, lgl.WINDOW.get_size()[1]))




def event_update(events, keys):
    for event in events:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                lgl.MainLoop.end()
                
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                ball.sprite_group.change_state("shine")

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                ball.sprite_group.change_state("blue")

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_b:
                ball.sprite_group.change_state("blue_shine")

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_DOWN:
                ball.sprite_group.change_state("idle")

        test_gui.event_update(event)
        my_scrollbar.event_update(event)


def update():
    ball.sync_sprites()
    ball.update()
    test_gui.update()
    my_scrollbar.update()


def fixed_update():
    pass


def updateGFX():
    lgl.WINDOW.fill((250,250,250))
    ball.draw()
    test_gui.draw()
    my_scrollbar.draw()

lgl.MainLoop.ev_update = event_update
lgl.MainLoop.update = update
lgl.MainLoop.fix_update = fixed_update
lgl.MainLoop.gfx_update = updateGFX
lgl.MainLoop.start()
