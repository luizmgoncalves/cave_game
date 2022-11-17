import pygame
import json
import consulta_ao_banco
import os

pygame.font.init()

class Button:
    def __init__(self, content: str, x: int, y: int, width=400, height=100, font_size=50, action=None):
        self.content = content
        self.selected = False
        self.action = action
        self.font = pygame.font.SysFont("lucidacalligraphy", font_size)
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.surface.Surface((width, height), pygame.SRCALPHA).convert_alpha()
        self.text_surface = self.font.render(self.content, True, (255, 255, 255))
        self.text_rect = self.text_surface.get_rect(center=[x/2 for x in self.rect.size])
        self.render()
    
    def select(self):
        self.action()
    
    def render(self):
        if self.selected:
            self.image.fill((0, 0, 0, 200))
        else:
            self.image.fill((0, 0, 0, 100))
        self.image.blit(self.text_surface, self.text_rect)
        pygame.draw.rect(self.image, (20, 20, 20), self.rect, 5)

class Label:
    def __init__(self, content: str, x: int, y: int, width=400, height=100, font_size=50, bg_color=(0, 0, 0, 0)):
        self.content = content
        self.bg_color = bg_color
        self.font = pygame.font.SysFont("lucidacalligraphy", font_size)
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.surface.Surface((width, height), pygame.SRCALPHA).convert_alpha()
        self.text_surface = self.font.render(self.content, True, (255, 255, 255))
        self.text_rect = self.text_surface.get_rect(center=[x/2 for x in self.rect.size])
        self.render()
    
    def render(self, color=(255, 255, 255)):
        self.image.fill(self.bg_color)
        self.text_surface = self.font.render(self.content, True, color)
        self.text_rect = self.text_surface.get_rect(center=[x/2 for x in self.rect.size])
        self.image.blit(self.text_surface, self.text_rect)
        


class Menu:
    def __init__(self, screen: pygame.surface.Surface):
        self.screen = screen
        self.QUIT = False
        self.showing = False
        self._bg_image = pygame.image.load('./game_images/forest_background.webp').convert()
        self.bg_image = pygame.transform.scale(self._bg_image, (pygame.display.Info().current_w, pygame.display.Info().current_h)).convert()
        
        self.buttons = [Button("Mapas", 100, 300, action=self.show_worlds), 
                        Button("Criar mapa", 100, 410, action=self.init_writing),
                        Button("Quit", 100, 520, action=self.quit),
                        ]
        
        self.play_world = ''

        self.labels = [Label("Cave Game", 100, 100)]

        self.contents = self.buttons+self.labels

        self.curr_state = ''

        self.writing_label = Label("test", 600, 400, bg_color = (0, 0, 0, 100))

        if "worlds.json" not in os.listdir():
            with open("worlds.json", 'w') as worlds:
                worlds.write("{}")


        with open("worlds.json", 'r') as worlds:
            self.worlds: dict =  eval(str(json.load(worlds)))

        self.generate_worlds_buttons()
    
    def delete_world(self, world):
        print('deleting', world)
        consulta_ao_banco.delete_db(world)
        self.worlds.pop(world)
        self.update_worlds()
        self.stop_state()
    
    def play(self, world):
        self.curr_state = 'playing'
        self.play_world = world

    def init_world_selection(self, world):
        if not self.curr_state == 'world_s':
            self.curr_state = 'world_s'
            self.bg_image = self.screen.copy()
            shadow = pygame.Surface(self.bg_image.get_size(), pygame.SRCALPHA)
            shadow.fill((0, 0, 0, 100))
            self.bg_image.blit(shadow, (0, 0))
            self.contents = []
            self.contents.extend([
                                Button("Delete", 300, 500, action=closure(self.delete_world, world)), 
                                Button("Play", 800, 500, action=closure(self.play, world))
                                ])
            return

        self.stop_state()

    def init_writing(self):
        if not self.curr_state == 'writing':
            self.curr_state = 'writing'
            self.bg_image = self.screen.copy()
            shadow = pygame.Surface(self.bg_image.get_size(), pygame.SRCALPHA)
            shadow.fill((0, 0, 0, 100))
            self.bg_image.blit(shadow, (0, 0))
            print(self.writing_label)
            self.contents = []
            self.contents.append(self.writing_label)
            self.update_writing_label()
            return

        self.stop_state()
    
    def stop_state(self):
        self.curr_state = ''
        self.bg_image = pygame.transform.scale(self._bg_image, (pygame.display.Info().current_w, pygame.display.Info().current_h)).convert()
        self.contents = []
        self.contents = self.buttons+self.labels
    
    def quit(self):
        self.curr_state = 'quitting'
    
    def show_worlds(self):
        if not self.showing:
            self.showing = True
            self.buttons.extend(self.world_buttons)
            self.contents.extend(self.world_buttons)
            return
        
        self.un_show_worlds()
        
    def un_show_worlds(self):
        self.showing = False
        for button in self.world_buttons:
            try:
                self.buttons.remove(button)
                self.contents.remove(button)
            except:
                pass
    
    def generate_worlds_buttons(self):
        self.world_buttons = []
        pos_y = 100
        for world in self.worlds:
            self.world_buttons.append(
                Button(world, 
                       550, 
                       pos_y,
                       action = closure(self.init_world_selection, world)
                    ))
            pos_y += 110

    def update_worlds(self):
        self.un_show_worlds()
        self.generate_worlds_buttons()
        with open("worlds.json", 'w') as worlds:
            worlds.write(json.JSONEncoder().encode(self.worlds))
            
    def create_world(self) -> bool:
        if self.writing_label.content in self.worlds:
            return False
        
        from random import choice
        seed = int("".join([choice("1234567890") for _ in range(5)]))

        new_world = {'seed': seed, "db": f'{self.writing_label.content}.db'}

        self.worlds[self.writing_label.content] = new_world

        self.update_worlds()

        consulta_ao_banco.generate_db(self.writing_label.content)

        self.writing_label.content = ""

        return True

    def render(self):
        self.screen.blit(self.bg_image, (0, 0))

        for item in self.contents:
            self.screen.blit(item.image, item.rect)
        
        pygame.display.flip()
    
    def update_writing_label(self):
        if self.writing_label.content in self.worlds:
            self.writing_label.render((255, 100, 100))
        else:
            self.writing_label.render()
    
    def event_handler(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.curr_state = 'quitting'
            if event.type == pygame.MOUSEMOTION:
                for button in self.contents:
                    if not isinstance(button, Button):
                        continue

                    if button.rect.collidepoint(*event.pos):
                        button.selected = True
                        button.render()
                    else:
                        button.selected = False
                        button.render()
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for button in self.contents:
                    if not isinstance(button, Button):
                        continue
                    if button.rect.collidepoint(*event.pos):
                        button.action()

            if event.type == pygame.WINDOWRESIZED:
                self.bg_image = pygame.transform.scale(self.bg_image, (pygame.display.Info().current_w, pygame.display.Info().current_h)).convert()
            
            if event.type == pygame.KEYDOWN:
                if event.key ==  pygame.K_ESCAPE and self.curr_state:
                    self.stop_state()
                
                if self.curr_state == 'writing':
                    match event.key:
                        case pygame.K_RETURN:
                            if self.create_world():
                                self.stop_state()
                        case pygame.K_BACKSPACE:
                            self.writing_label.content = self.writing_label.content[:-1]
                            self.update_writing_label()
                        case key:
                            self.writing_label.content += event.unicode
                            self.update_writing_label()
                            
def closure(func, arg):
            def new_func():
                func(arg)
            return new_func
