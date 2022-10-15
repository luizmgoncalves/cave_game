import pygame
import world_generator

class MainPlatformLoopWaiter:
    def __init__(self):
        self._initialized = False
        self._finalised = True
        self._stop_waiter = False
        self.one_time = False
        self.finalise_arguments = []

    def stop_waiter(self):
        self._stop_waiter = True

    def finalise_function(self, *args, **kwargs):
        pass

    def init_loop(self):
        if self._finalised:
            self._initialized = True
            self._finalised = False
        else:
            raise Exception("Waiter was initialized without finalised")

    def finalise_loop(self, *args, **kwargs):
        if self._initialized:
            self._initialized = False
            self._finalised = True
            self._stop_waiter = False
            self.finalise_function(*self.finalise_arguments)
        else:
            raise Exception('Waiter was finalised without initialization')

    def loop_function(self, platform):
        pass

    def run(self, platform):
        if self._initialized:
            if not self._stop_waiter:
                self.loop_function(platform)
        else:
            raise Exception('Waiter was runned without initialization')


class MouseClickWaiter(MainPlatformLoopWaiter):
    def __init__(self, pos, pos_de_apresentacao, personagem_x, personagem_y, elements_manager):
        super(MouseClickWaiter, self).__init__()
        self.pos = pos
        self.elements_manager = elements_manager
        self.pos_de_apresentacao = pos_de_apresentacao
        self.personagem_x = personagem_x
        self.personagem_y = personagem_y
        self.one_time = True
        self.platform = None

    def finalise_function(self):
        if self.platform:
            self.platform.owner.remove_block(self.platform)

    def loop_function(self, platform):
        from math import hypot
        if (platform.collidepoint(self.pos[0] - self.pos_de_apresentacao[0], self.pos[1] - self.pos_de_apresentacao[1]) and
                (hypot(platform.x - self.personagem_x, platform.y - self.personagem_y) < 200)):
            self.stop_waiter()
            self.elements_manager.pre_render_changes = True
            self.platform = platform


class MoveCharacterXWaiter(MainPlatformLoopWaiter):
    def __init__(self, character, owner):
        super().__init__()
        self.one_time = False
        self.character = character
        self.virtual_rect = None
        self.collide = False
        self.owner = owner

    def init_loop(self):
        super().init_loop()
        self.virtual_rect = self.character.rect.copy()
        self.virtual_rect.x += self.character.velocidade[0].get()
        self.collide = False

    def loop_function(self, platform):
        if self.virtual_rect.colliderect(platform) and platform.colidable:
            if self.character.velocidade[0].value > 0:
                self.virtual_rect.right = platform.left
                self.character.velocidade[0].set(0)
            if self.character.velocidade[0].value < 0:
                self.virtual_rect.left = platform.right
                self.character.velocidade[0].set(0)

            self.collide = True
            self.stop_waiter()
            

    def finalise_function(self, *args, **kwargs):
        if self.character.rect.x != self.virtual_rect.x:
            self.owner.pre_render_changes = True
        
        self.character.rect.x = self.virtual_rect.x


class MoveCharacterYWaiter(MainPlatformLoopWaiter):
    def __init__(self, character, owner):
        super().__init__()
        self.one_time = False
        self.character = character
        self.virtual_rect = None
        self.collide = False
        self.owner = owner

    def init_loop(self):
        super().init_loop()
        self.virtual_rect = self.character.rect.copy()
        self.virtual_rect.y += self.character.velocidade[1].get()
        self.collide = False
        if self.character.velocidade[1].value > 0 and not self.character.falling:
            self.character.falling = False
        else:
            self.character.falling = True

    def loop_function(self, platform):
        if self.virtual_rect.colliderect(platform) and platform.colidable:
            if self.character.velocidade[1].value > 0:
                self.virtual_rect.bottom = platform.top
                if self.character.pulou:
                    self.character.pulou = False
                self.character.velocidade[1].set(0)

                self.character.falling = False

            if self.character.velocidade[1].value < 0:
                self.virtual_rect.top = platform.bottom
                self.character.velocidade[1].set(0)

            self.collide = True
            self.stop_waiter()

    def finalise_function(self, *args, **kwargs):
        if self.character.rect.y != self.virtual_rect.y:
            self.owner.pre_render_changes = True

        self.character.rect.y = self.virtual_rect.y
