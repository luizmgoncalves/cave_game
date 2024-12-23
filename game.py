import pygame
import sys
from world_generator import *
from waiters import *
import debugger
from fisics import PixelPerSecond, PixelPerSecondSquared, Friction

pygame.init()


class Personagem:
    dimensions = [40, 40]

    def __init__(self, frame_rate, owner):
        self.rect = pygame.Rect((200, 0), self.dimensions)
        self.color = pygame.Color(0, 100, 0, a=0)
        self.velocidade = [PixelPerSecond(0, 600, owner), PixelPerSecond(0, 1500, owner)]
        self.gravidade = PixelPerSecondSquared(2000, owner)
        self.aceleracao_horizontal = PixelPerSecondSquared(3000, owner)
        self.atrito = Friction(4000, owner)
        self.contador = 0
        self.owner = owner
        self.falling = False
        self.pulou = False
        self.right = False
        self.left = False
        self.up = False
        self.down = False

        self.imagens = [
            [pygame.transform.scale(pygame.image.load(f'game_images/d{x}.png'), tuple(self.dimensions)).convert() for x in
             range(1, 6)],
            [pygame.transform.flip(pygame.transform.scale(pygame.image.load(f'game_images/d{x}.png'), tuple(self.dimensions)), True, False).convert() for x in
             range(1, 6)],
            pygame.transform.scale(pygame.image.load('game_images/d3.png'), tuple(self.dimensions)).convert(),
            pygame.transform.flip(pygame.transform.scale(pygame.image.load('game_images/d3.png'), tuple(self.dimensions)), True, False).convert(),
            pygame.transform.scale(pygame.image.load('game_images/d1.png'), tuple(self.dimensions)).convert()]

        for imagem in self.imagens:
            if type(imagem) == list:
                for sprite in imagem:
                    #sprite.set_colorkey((255, 255, 255))
                    sprite.convert()
            else:
                #imagem.set_colorkey((255, 255, 255))
                imagem.convert()

        self.imagem = self.imagens[4]

    def atualizar_frame(self):
        if self.contador >= 50:
            self.contador = 0        

        if self.falling:
            if self.velocidade[0].get() < 0:
                if self.imagem != self.imagens[3]:
                    self.owner.pre_render_changes = True
                self.imagem = self.imagens[3]
            else:
                if self.imagem != self.imagens[2]:
                    self.owner.pre_render_changes = True
                self.imagem = self.imagens[2]

        elif self.left:
            if self.imagem != self.imagens[1][(self.contador // 10)]:
                    self.owner.pre_render_changes = True
            self.imagem = self.imagens[1][(self.contador // 10)]

        elif self.right:
            if self.imagem != self.imagens[0][(self.contador // 10)]:
                    self.owner.pre_render_changes = True
            self.imagem = self.imagens[0][(self.contador // 10)]

        else:
            if self.imagem != self.imagens[4]:
                    self.owner.pre_render_changes = True
            self.imagem = self.imagens[4]
        
        self.contador += 1


class GerenciadorDeElementos:
    def __init__(self, janela, world_name: str, DEBUG=False):
        self.janela = janela
        infoObject = pygame.display.Info()
        self.WIDTH = int(infoObject.current_w)
        self.HEIGHT = int(infoObject.current_h)
        self.DEBUG = DEBUG
        self.bg_image = pygame.transform.scale(pygame.image.load('./game_images/forest_background.webp'),
                                    (pygame.display.Info().current_w, pygame.display.Info().current_h)).convert()
        self.fps = 60
        self.fps_r = 60
        self.personagem = Personagem(frame_rate=self.fps, owner=self)
        self.platform_meta_data = PlatformData()
        self.loop_waiters = [MoveCharacterXWaiter(self.personagem, self), MoveCharacterYWaiter(self.personagem, self)]
        self.QUIT = False
        self.retornar = False
        self.pre_render_changes = False
        self.pos_render_changes = False
        self.rendered = False
        self.contador = 0
        self.pos_de_apresentacao = [0, 0]
        self.environment_generator = EnvironmentGenerator(world_name)
        self.main_platforms_loop_requests = {'mining_request': False,
                                             'update_colidable_platforms': False,
                                             'put_in': False}

        self.chunks = {'0, 0': self.environment_generator.buscar_blocos([-1, -1]),
                       '0, 1': self.environment_generator.buscar_blocos([0, -1]),
                       '0, 2': self.environment_generator.buscar_blocos([1, -1]),
                       '1, 0': self.environment_generator.buscar_blocos([-1, 0]),
                       '1, 1': self.environment_generator.buscar_blocos([0, 0]),
                       '1, 2': self.environment_generator.buscar_blocos([1, 0]),
                       '2, 0': self.environment_generator.buscar_blocos([-1, 1]),
                       '2, 1': self.environment_generator.buscar_blocos([0, 1]),
                       '2, 2': self.environment_generator.buscar_blocos([1, 1])}

    def monitor_de_lotes(self):
        # avançar horizontalmente

        if self.personagem.rect.centerx > (self.chunks['1, 1'].loc[0] + 1) * Chunk.dimensions[0]:

            self.chunks['0, 0'], self.chunks['1, 0'], self.chunks['2, 0'] = self.chunks['0, 1'], self.chunks[
                '1, 1'], self.chunks['2, 1']
            self.chunks['0, 1'], self.chunks['1, 1'], self.chunks['2, 1'] = self.chunks['0, 2'], self.chunks[
                '1, 2'], self.chunks['2, 2']

            self.chunks['0, 2'] = self.environment_generator.buscar_blocos(
                    [self.chunks['0, 1'].loc[0] + 1, self.chunks['0, 1'].loc[1]])

            self.chunks['1, 2'] = self.environment_generator.buscar_blocos(
                    [self.chunks['1, 1'].loc[0] + 1, self.chunks['1, 1'].loc[1]])

            self.chunks['2, 2'] = self.environment_generator.buscar_blocos(
                    [self.chunks['2, 1'].loc[0] + 1, self.chunks['2, 1'].loc[1]])


        if self.personagem.rect.centerx < (self.chunks['1, 1'].loc[0]) * Chunk.dimensions[0]:
            self.chunks['0, 2'], self.chunks['1, 2'], self.chunks['2, 2'] = self.chunks['0, 1'], self.chunks[
                '1, 1'], self.chunks['2, 1']
            self.chunks['0, 1'], self.chunks['1, 1'], self.chunks['2, 1'] = self.chunks['0, 0'], self.chunks[
                '1, 0'], self.chunks['2, 0']
            
            self.chunks['0, 0'] = self.environment_generator.buscar_blocos(
                    [self.chunks['0, 1'].loc[0] - 1, self.chunks['0, 1'].loc[1]])

            self.chunks['1, 0'] = self.environment_generator.buscar_blocos(
                    [self.chunks['1, 1'].loc[0] - 1, self.chunks['1, 1'].loc[1]])

            self.chunks['2, 0'] = self.environment_generator.buscar_blocos(
                    [self.chunks['2, 1'].loc[0] - 1, self.chunks['2, 1'].loc[1]])


        # avançar verticalmente
        if self.personagem.rect.centery < (self.chunks['1, 1'].loc[1]) * Chunk.dimensions[0]:
            self.chunks['2, 0'], self.chunks['2, 1'], self.chunks['2, 2'] = self.chunks['1, 0'], self.chunks[
                '1, 1'], self.chunks['1, 2']
            self.chunks['1, 0'], self.chunks['1, 1'], self.chunks['1, 2'] = self.chunks['0, 0'], self.chunks[
                '0, 1'], self.chunks['0, 2']

            self.chunks['0, 0'] = self.environment_generator.buscar_blocos(
                    [self.chunks['1, 0'].loc[0], self.chunks['1, 0'].loc[1] - 1])

            self.chunks['0, 1'] = self.environment_generator.buscar_blocos(
                    [self.chunks['1, 1'].loc[0], self.chunks['1, 1'].loc[1] - 1])

            self.chunks['0, 2'] = self.environment_generator.buscar_blocos(
                    [self.chunks['1, 2'].loc[0], self.chunks['1, 2'].loc[1] - 1])


        if self.personagem.rect.centery > (self.chunks['1, 1'].loc[1] + 1) * Chunk.dimensions[0]:
            self.chunks['0, 0'], self.chunks['0, 1'], self.chunks['0, 2'] = self.chunks['1, 0'], self.chunks[
                '1, 1'], self.chunks['1, 2']
            self.chunks['1, 0'], self.chunks['1, 1'], self.chunks['1, 2'] = self.chunks['2, 0'], self.chunks[
                '2, 1'], self.chunks['2, 2']

            self.chunks['2, 0'] = self.environment_generator.buscar_blocos(
                    [self.chunks['1, 0'].loc[0], self.chunks['1, 0'].loc[1] + 1])

            self.chunks['2, 1'] = self.environment_generator.buscar_blocos(
                    [self.chunks['1, 1'].loc[0], self.chunks['1, 1'].loc[1] + 1])

            self.chunks['2, 2'] = self.environment_generator.buscar_blocos(
                    [self.chunks['1, 2'].loc[0], self.chunks['1, 2'].loc[1] + 1])


    def update_platforms(self):
        self.monitor_de_lotes()


        for waiter in self.loop_waiters:
            waiter.init_loop()
        
        self.pre_render_changes = False

        for chunk in self.chunks.values():
            for platform in chunk.platforms:
                for waiter in self.loop_waiters:
                    waiter.run(platform)

                if self.WIDTH>=(platform.x +self.pos_de_apresentacao[0])>=-Chunk.platform_dimensions[0] and -Chunk.platform_dimensions[1]<(platform.y + self.pos_de_apresentacao[1])<self.HEIGHT:
                    if self.pos_render_changes:
                        if platform.layer==0:
                            self.janela.blit(self.platform_meta_data.PLATFORM_IMAGES[platform.type], (platform.x+self.pos_de_apresentacao[0], platform.y+self.pos_de_apresentacao[1]))
                        else:
                            self.janela.blit(self.platform_meta_data.PLATFORM_IMAGES_UN[platform.type], (platform.x+self.pos_de_apresentacao[0], platform.y+self.pos_de_apresentacao[1]))

        to_destroy_waiters = []

        for waiter in self.loop_waiters:
            waiter.finalise_loop()
            if waiter.one_time:
                to_destroy_waiters.append(waiter)

        for waiter in to_destroy_waiters:
            self.loop_waiters.remove(waiter)

        to_destroy_waiters.clear()

        self.gerenciador_de_movimento_vertical()
        self.gerenciador_de_movimento_horizontal()
        self.desenhar_personagem()



    def atualizar_monitor(self):
        self.pos_de_apresentacao[0] = pygame.display.Info().current_w // 2 - self.personagem.rect.center[0]
        self.pos_de_apresentacao[1] = pygame.display.Info().current_h * 2 // 3 - self.personagem.rect.center[1]

    def desenhar_personagem(self):
        self.personagem.atualizar_frame()
        if self.pos_render_changes:
            self.janela.blit(self.personagem.imagem, (
                self.personagem.rect.x + self.pos_de_apresentacao[0], self.personagem.rect.y + self.pos_de_apresentacao[1]))

            self.rendered = True
        


    def gerenciador_de_movimento_vertical(self):
        if self.personagem.up and not self.personagem.pulou and not self.personagem.falling:
            self.personagem.velocidade[1].set(-1000)
            self.personagem.pulou = True

        self.personagem.gravidade.acelerate_vel(self.personagem.velocidade[1])

    def gerenciador_de_movimento_horizontal(self):
        if self.personagem.left:
            self.personagem.aceleracao_horizontal.acelerate_vel(self.personagem.velocidade[0], negative=True)

        elif self.personagem.right:
            self.personagem.aceleracao_horizontal.acelerate_vel(self.personagem.velocidade[0])
        elif not self.personagem.falling:
            self.personagem.atrito.decelerate(self.personagem.velocidade[0])

    def its_safe_for_commit_verifier(self):
        if self.personagem.velocidade[0].get() == 0 and self.personagem.velocidade[1].get() == 0:
            self.environment_generator.its_safe_to_commit()

    def atualizar_contador(self):
        if self.contador == 240:
            self.contador = 0
            return None

        self.contador += 1

    def atualizar(self):
        self.atualizar_contador()

        self.its_safe_for_commit_verifier()

        self.update_platforms()

        self.atualizar_monitor()

        self.monitor_de_movimentos()
        
        if self.pre_render_changes != self.pos_render_changes:
            self.pos_render_changes = self.pre_render_changes

    def verificador_clicar_bloco(self, pos):
        self.loop_waiters.append(MouseClickWaiter(pos, self.pos_de_apresentacao, self.personagem.rect.x, self.personagem.rect.y, self))

    def monitor_de_movimentos(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.environment_generator.big_last_save()
                if self.DEBUG:
                    self.environment_generator.consultor.clear_database()
                
                if event.type == pygame.QUIT:
                    self.QUIT = True
                else:
                    self.retornar = True

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.verificador_clicar_bloco(event.pos)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    self.personagem.right = True
                if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    self.personagem.left = True
                if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    self.personagem.down = True
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    self.personagem.up = True

            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    self.personagem.right = False
                if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    self.personagem.left = False
                if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    self.personagem.down = False
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    self.personagem.up = False
            
            elif event.type == pygame.VIDEORESIZE:
                self.bg_image = pygame.transform.scale(pygame.image.load('./game_images/forest_background.webp'),
                                    (pygame.display.Info().current_w, pygame.display.Info().current_h)).convert()
                infoObject = pygame.display.Info()
                self.WIDTH = int(infoObject.current_w)
                self.HEIGHT = int(infoObject.current_h)
                self.pre_render_changes = True


def run(screen: pygame.surface.Surface, world_name: str, debug: bool=False):
    pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.KEYUP, pygame.VIDEORESIZE])

    gerenciador = GerenciadorDeElementos(screen, world_name, debug)

    mainClock = pygame.time.Clock()

    font = pygame.font.SysFont("Arial", 18)

    # loop #
    while 1:
        if gerenciador.pos_render_changes:
            screen.blit(gerenciador.bg_image, (0, 0))

        gerenciador.atualizar()

        if gerenciador.QUIT:
            sys.exit()
        
        if gerenciador.retornar:
            break

        if gerenciador.rendered:
            fps = str(int(mainClock.get_fps()))
            screen.blit(font.render(fps, 1, pygame.Color("coral")), (10,0))
            pygame.display.flip()
            gerenciador.rendered = False

        mainClock.tick(gerenciador.fps)
        gerenciador.fps_r = mainClock.get_fps()


if __name__ == '__main__':
    DEBUG = True

    pygame.display.init()

    screen = pygame.display.set_mode((700, 400), pygame.RESIZABLE, 16, vsync=1)
    pygame.display.set_caption('Cube\'s Odyssey')

    #screen = screen ## world_name = test123 ## debug = DEBUG

    run(screen, 'test344', DEBUG)
