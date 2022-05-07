import pygame
import sys
from world_generator import *
from waiters import *
import debugger
from fisics import PixelPerSecond, PixelPerSecondSquared, Friction

pygame.init()


class Personagem:
    dimensions = [30, 80]

    def __init__(self, frame_rate, owner):
        self.rect = pygame.Rect((200, 0), self.dimensions)
        self.color = pygame.Color(0, 100, 0, a=0)
        self.velocidade = [PixelPerSecond(
            0, 500, frame_rate), PixelPerSecond(0, 2000, frame_rate)]
        self.gravidade = PixelPerSecondSquared(2000, frame_rate)
        self.aceleracao_horizontal = PixelPerSecondSquared(3000, frame_rate)
        self.atrito = Friction(2000, frame_rate)
        self.contador = 0
        self.owner = owner
        self.falling = False
        self.pulou = False
        self.right = False
        self.left = False
        self.up = False
        self.down = False
        self.facing_right = True

        self.imagens = [
            [pygame.transform.scale(pygame.image.load(f'game_images/previous/d{x}.png'), tuple(self.dimensions)).convert() for x in
             range(1, 7)],
            [pygame.transform.flip(pygame.transform.scale(pygame.image.load(f'game_images/previous/d{x}.png'), tuple(self.dimensions)), True, False).convert() for x in
             range(1, 7)],
            pygame.transform.scale(pygame.image.load('game_images/previous/d3.png'), tuple(self.dimensions)).convert(),
            pygame.transform.scale(pygame.image.load('game_images/previous/d3.png'), tuple(self.dimensions)).convert(),
            pygame.transform.scale(pygame.image.load('game_images/previous/d1.png'), tuple(self.dimensions)).convert()]

        for imagem in self.imagens:
            if type(imagem) == list:
                for sprite in imagem:
                    sprite.set_colorkey((255, 255, 255))
                    sprite.convert()
            else:
                imagem.set_colorkey((255, 255, 255))
                imagem.convert()

        self.imagem = self.imagens[4]

    def atualizar_frame(self):
        if self.contador >= 12:
            self.contador = 0
        
        if self.falling:
            if self.velocidade[0].get() < 0:
                if self.imagem != self.imagens[3]:
                    self.owner.pre_render_changes = True
                #self.imagem = self.imagens[3]

                if self.facing_right:
                    self.imagem = self.imagens[3]
                else:
                    self.imagem = pygame.transform.flip(
                        self.imagens[3], True, False)

            else:
                if self.imagem != self.imagens[2]:
                    self.owner.pre_render_changes = True
                #self.imagem = self.imagens[2]

                if self.facing_right:
                    self.imagem = self.imagens[2]
                else:
                    self.imagem = pygame.transform.flip(
                        self.imagens[2], True, False)

        elif self.left:
            if self.imagem != self.imagens[1][(self.contador // 2)]:
                self.owner.pre_render_changes = True
            self.imagem = self.imagens[1][(self.contador // 2)]

        elif self.right:
            if self.imagem != self.imagens[0][(self.contador // 2)]:
                self.owner.pre_render_changes = True
            self.imagem = self.imagens[0][(self.contador // 2)]

        else:
            #Faz o cursor não ser atualizado com o bonequinho parado
            '''if self.imagem != self.imagens[4]:
                self.owner.pre_render_changes = True'''

            self.owner.pre_render_changes = True

            if self.facing_right:
                self.imagem = self.imagens[4]
            else:
                self.imagem = pygame.transform.flip(
                    self.imagens[4], True, False)

        self.contador += 1

class GerenciadorDeElementos:
    def __init__(self, janela):
        self.janela = janela
        self.fps = 60
        self.personagem = Personagem(frame_rate=self.fps, owner=self)
        self.platform_meta_data = PlatformData()
        self.loop_waiters = [MoveCharacterXWaiter(
            self.personagem, self), MoveCharacterYWaiter(self.personagem, self)]
        self.QUIT = False
        self.pre_render_changes = False
        self.pos_render_changes = False
        self.rendered = False
        self.contador = 0
        self.pos_de_apresentacao = [0, 0]
        self.environment_generator = EnvironmentGenerator()
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
        global HEIGHT, WIDTH
        self.monitor_de_lotes()

        for waiter in self.loop_waiters:
            waiter.init_loop()

        self.pre_render_changes = False

        for chunk in self.chunks.values():
            for platform in chunk.platforms:
                for waiter in self.loop_waiters:
                    waiter.run(platform)

                if WIDTH >= (platform.x + self.pos_de_apresentacao[0]) >= -50 and -50 < (platform.y + self.pos_de_apresentacao[1]) < HEIGHT:
                    if self.pos_render_changes:
                        if platform.layer == 0:
                            self.janela.blit(self.platform_meta_data.PLATFORM_IMAGES[platform.type], (
                                platform.x+self.pos_de_apresentacao[0], platform.y+self.pos_de_apresentacao[1]))
                        else:
                            self.janela.blit(self.platform_meta_data.PLATFORM_IMAGES_UN[platform.type], (
                                platform.x+self.pos_de_apresentacao[0], platform.y+self.pos_de_apresentacao[1]))

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
        self.pos_de_apresentacao[0] = pygame.display.Info(
        ).current_w // 2 - self.personagem.rect.center[0]
        self.pos_de_apresentacao[1] = pygame.display.Info(
        ).current_h * 2 // 3 - self.personagem.rect.center[1]

    def desenhar_personagem(self):
        self.personagem.atualizar_frame()
        if self.pos_render_changes:
            self.janela.blit(self.personagem.imagem, (
                self.personagem.rect.x + self.pos_de_apresentacao[0], self.personagem.rect.y + self.pos_de_apresentacao[1]))

            self.rendered = True

    def desenhar_cursor(self):
        mx, my = pygame.mouse.get_pos()
        cursor_rect.center = [mx, my]
        self.janela.blit(cursor, cursor_rect)

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

        self.desenhar_cursor()

        if self.pre_render_changes != self.pos_render_changes:
            self.pos_render_changes = self.pre_render_changes

    def verificador_clicar_bloco(self, pos):
        self.loop_waiters.append(MouseClickWaiter(
            pos, self.pos_de_apresentacao, self.personagem.rect.x, self.personagem.rect.y, self))

    def verificador_clicar_bloco_add(self, pos):
        self.loop_waiters.append(MouseClickWaiter(
            pos, self.pos_de_apresentacao, self.personagem.rect.x, self.personagem.rect.y, self))

    def monitor_de_movimentos(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.QUIT = True
                self.environment_generator.big_last_save()
                if DEBUG:
                    self.environment_generator.consultor.clear_database()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.verificador_clicar_bloco(event.pos)
                elif event.button == 3:
                    self.verificador_clicar_bloco_add(event.pos)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    self.personagem.right = True
                    self.personagem.facing_right = True
                if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    self.personagem.left = True
                    self.personagem.facing_right = False
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
                global imagem, HEIGHT, WIDTH
                imagem = pygame.transform.scale(pygame.image.load('./game_images/forest_background.webp'),
                                                (pygame.display.Info().current_w, pygame.display.Info().current_h)).convert()
                infoObject = pygame.display.Info()
                WIDTH = int(infoObject.current_w)
                HEIGHT = int(infoObject.current_h)
                self.pre_render_changes = True


if __name__ == '__main__':
    DEBUG = False

    pygame.display.init()

    screen = pygame.display.set_mode((700, 400), pygame.RESIZABLE, 16)
    pygame.display.set_caption('Cube\'s Odyssey')

    infoObject = pygame.display.Info()
    print(infoObject)
    WIDTH = int(infoObject.current_w)
    HEIGHT = int(infoObject.current_h)

    pygame.event.set_allowed(
        [pygame.QUIT, pygame.KEYDOWN, pygame.KEYUP, pygame.VIDEORESIZE])

    imagem = pygame.transform.scale(pygame.image.load('./game_images/forest_background.webp'), (pygame.display.Info().current_w, pygame.display.Info().current_h)).convert()

    gerenciador = GerenciadorDeElementos(screen)

    mainClock = pygame.time.Clock()
    counter = 0

    cursor = pygame.image.load("game_images/cursor.png").convert_alpha()
    cursor_rect = cursor.get_rect(center=[0, 0])
    pygame.mouse.set_visible(False)

    # loop #
    while 1:
        if gerenciador.pos_render_changes:
            screen.blit(imagem, (0, 0))

        gerenciador.atualizar()

        if gerenciador.QUIT:
            break

        if gerenciador.rendered:
            pygame.display.update()
            gerenciador.rendered = False

        mainClock.tick(gerenciador.fps)
        if counter % 100 == 0:
            print(mainClock.get_fps())

        counter += 1

    pygame.quit()
    sys.exit()
