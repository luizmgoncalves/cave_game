import pygame
import sys
import os
from world_generator import *
from waiters import *
import image_generator
import debugger
from fisics import PixelPerSecond, PixelPerSecondSquared, Friction

pygame.init()


class Personagem:
    dimensions = [50, 50]

    def __init__(self, frame_rate=60):
        self.rect = pygame.Rect((200, 0), self.dimensions)
        self.color = pygame.Color(0, 100, 0, a=0)
        self.velocidade = [PixelPerSecond(0, 500, frame_rate), PixelPerSecond(0, 2000, frame_rate)]
        self.gravidade = PixelPerSecondSquared(2000, frame_rate)
        self.aceleracao_horizontal = PixelPerSecondSquared(3000, frame_rate)
        self.atrito = Friction(2000, frame_rate)
        self.contador = 0
        self.falling = False
        self.pulou = False
        self.right = False
        self.left = False
        self.up = False
        self.down = False

        self.imagens = [
            [pygame.transform.scale(pygame.image.load(f'game_images/d{x}.png'), tuple(self.dimensions)).convert() for x in
             range(1, 6)],
            [pygame.transform.scale(pygame.image.load(f'game_images/e{x}.png'), tuple(self.dimensions)).convert() for x in
             range(1, 6)],
            pygame.transform.scale(pygame.image.load('game_images/p1.png'), tuple(self.dimensions)).convert(),
            pygame.transform.scale(pygame.image.load('game_images/pe1.png'), tuple(self.dimensions)).convert(),
            pygame.transform.scale(pygame.image.load('game_images/pa.png'), tuple(self.dimensions)).convert()]

        self.imagem = self.imagens[4]

    def atualizar_frame(self):
        if self.contador >= 30:
            self.contador = 0

        if self.left and self.pulou:
            self.imagem = self.imagens[3]

        elif self.right and self.pulou:
            self.imagem = self.imagens[2]

        elif self.left:
            self.imagem = self.imagens[1][(self.contador // 6)]

        elif self.right:
            self.imagem = self.imagens[0][(self.contador // 6)]

        else:
            self.imagem = self.imagens[4]

        self.contador += 1


class GerenciadorDeElementos:
    def __init__(self, janela):
        self.janela = janela
        self.fps = 60
        self.personagem = Personagem(frame_rate=self.fps)
        self.platform_meta_data = PlatformData()
        self.loop_waiters = [MoveCharacterXWaiter(self.personagem), MoveCharacterYWaiter(self.personagem)]
        self.QUIT = False
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

        self.chunk_renders = [image_generator.ChunkRender(chunk) for chunk in self.chunks.values()]

        self.init_chunks()
        self.render_chunks()

    def connect_renders(self):
        return
        renders = list(filter(lambda r: (not r.connected), self.chunk_renders))
        chunks = list(filter(lambda ch: ch.render is None, self.chunks.values()))
        for chunk, render in zip(chunks, renders):
            render.connect(chunk)

    def render_chunks(self):
        return
        for render in self.chunk_renders:
            if not render.rendered:
                render.render()

    def init_chunks(self):

        self.chunks['0, 0'].set_around_chunks(self.chunks['0, 1'].index, 1)
        self.chunks['0, 0'].set_around_chunks(self.chunks['1, 0'].index, 2)

        self.chunks['0, 1'].set_around_chunks(self.chunks['0, 0'].index, 3)
        self.chunks['0, 1'].set_around_chunks(self.chunks['0, 2'].index, 1)
        self.chunks['0, 1'].set_around_chunks(self.chunks['1, 1'].index, 2)

        self.chunks['0, 2'].set_around_chunks(self.chunks['0, 1'].index, 3)
        self.chunks['0, 2'].set_around_chunks(self.chunks['1, 2'].index, 2)

        self.chunks['1, 0'].set_around_chunks(self.chunks['0, 0'].index, 0)
        self.chunks['1, 0'].set_around_chunks(self.chunks['1, 1'].index, 1)
        self.chunks['1, 0'].set_around_chunks(self.chunks['2, 0'].index, 2)

        self.chunks['1, 1'].set_around_chunks(self.chunks['0, 1'].index, 0)
        self.chunks['1, 1'].set_around_chunks(self.chunks['1, 2'].index, 1)
        self.chunks['1, 1'].set_around_chunks(self.chunks['2, 1'].index, 2)
        self.chunks['1, 1'].set_around_chunks(self.chunks['1, 0'].index, 3)

        self.chunks['1, 2'].set_around_chunks(self.chunks['0, 2'].index, 0)
        self.chunks['1, 2'].set_around_chunks(self.chunks['1, 1'].index, 3)
        self.chunks['1, 2'].set_around_chunks(self.chunks['2, 2'].index, 2)

        self.chunks['2, 0'].set_around_chunks(self.chunks['1, 0'].index, 0)
        self.chunks['2, 0'].set_around_chunks(self.chunks['2, 1'].index, 1)

        self.chunks['2, 1'].set_around_chunks(self.chunks['1, 1'].index, 0)
        self.chunks['2, 1'].set_around_chunks(self.chunks['2, 0'].index, 3)
        self.chunks['2, 1'].set_around_chunks(self.chunks['2, 2'].index, 1)

        self.chunks['2, 2'].set_around_chunks(self.chunks['1, 2'].index, 0)
        self.chunks['2, 2'].set_around_chunks(self.chunks['2, 1'].index, 3)

    def deletar_blocos_correntes(self):
        self.save_chunk_verifier(self.chunks.values())

    def save_chunk_verifier(self, chunks: list) -> None:
        for chunk in chunks:
            #chunk.disconnect_render()
            self.environment_generator.delete_chunk(chunk)

    def monitor_de_lotes(self):
        # avançar horizontalmente

        if self.personagem.rect.centerx > (self.chunks['1, 1'].loc[0] + 1) * Chunk.dimensions[0]:
            self.save_chunk_verifier([self.chunks['0, 0'], self.chunks['1, 0'], self.chunks['2, 0']])

            self.chunks['0, 0'], self.chunks['1, 0'], self.chunks['2, 0'] = self.chunks['0, 1'], self.chunks[
                '1, 1'], self.chunks['2, 1']
            self.chunks['0, 1'], self.chunks['1, 1'], self.chunks['2, 1'] = self.chunks['0, 2'], self.chunks[
                '1, 2'], self.chunks['2, 2']

            if self.chunks['0, 1'].around_chunks[1] is not None:
                self.chunks['0, 2'] = self.environment_generator.buscar_blocos(
                    [self.chunks['0, 1'].loc[0] + 1, self.chunks['0, 1'].loc[1]],
                    chunk_id=self.chunks['0, 1'].around_chunks[1], by_pos=False)
            else:
                self.chunks['0, 2'] = self.environment_generator.buscar_blocos(
                    [self.chunks['0, 1'].loc[0] + 1, self.chunks['0, 1'].loc[1]])

            if self.chunks['1, 1'].around_chunks[1] is not None:
                self.chunks['1, 2'] = self.environment_generator.buscar_blocos(
                    [self.chunks['1, 1'].loc[0] + 1, self.chunks['1, 1'].loc[1]],
                    chunk_id=self.chunks['1, 1'].around_chunks[1], by_pos=False)
            else:
                self.chunks['1, 2'] = self.environment_generator.buscar_blocos(
                    [self.chunks['1, 1'].loc[0] + 1, self.chunks['1, 1'].loc[1]])

            if self.chunks['2, 1'].around_chunks[1] is not None:
                self.chunks['2, 2'] = self.environment_generator.buscar_blocos(
                    [self.chunks['2, 1'].loc[0] + 1, self.chunks['2, 1'].loc[1]],
                    chunk_id=self.chunks['2, 1'].around_chunks[1], by_pos=False)
            else:
                self.chunks['2, 2'] = self.environment_generator.buscar_blocos(
                    [self.chunks['2, 1'].loc[0] + 1, self.chunks['2, 1'].loc[1]])

            self.connect_renders()
            self.render_chunks()
            self.init_chunks()

        if self.personagem.rect.centerx < (self.chunks['1, 1'].loc[0]) * Chunk.dimensions[0]:
            self.save_chunk_verifier([self.chunks['0, 2'], self.chunks['1, 2'], self.chunks['2, 2']])
            self.chunks['0, 2'], self.chunks['1, 2'], self.chunks['2, 2'] = self.chunks['0, 1'], self.chunks[
                '1, 1'], self.chunks['2, 1']
            self.chunks['0, 1'], self.chunks['1, 1'], self.chunks['2, 1'] = self.chunks['0, 0'], self.chunks[
                '1, 0'], self.chunks['2, 0']
            if self.chunks['0, 1'].around_chunks[3] is not None:
                self.chunks['0, 0'] = self.environment_generator.buscar_blocos(
                    [self.chunks['0, 1'].loc[0] - 1, self.chunks['0, 1'].loc[1]],
                    chunk_id=self.chunks['0, 1'].around_chunks[3], by_pos=False)
            else:
                self.chunks['0, 0'] = self.environment_generator.buscar_blocos(
                    [self.chunks['0, 1'].loc[0] - 1, self.chunks['0, 1'].loc[1]])

            if self.chunks['1, 1'].around_chunks[3] is not None:
                self.chunks['1, 0'] = self.environment_generator.buscar_blocos(
                    [self.chunks['1, 1'].loc[0] - 1, self.chunks['1, 1'].loc[1]],
                    chunk_id=self.chunks['1, 1'].around_chunks[3], by_pos=False)
            else:
                self.chunks['1, 0'] = self.environment_generator.buscar_blocos(
                    [self.chunks['1, 1'].loc[0] - 1, self.chunks['1, 1'].loc[1]])

            if self.chunks['2, 1'].around_chunks[3] is not None:
                self.chunks['2, 0'] = self.environment_generator.buscar_blocos(
                    [self.chunks['2, 1'].loc[0] - 1, self.chunks['2, 1'].loc[1]],
                    chunk_id=self.chunks['2, 1'].around_chunks[3], by_pos=False)
            else:
                self.chunks['2, 0'] = self.environment_generator.buscar_blocos(
                    [self.chunks['2, 1'].loc[0] - 1, self.chunks['2, 1'].loc[1]])

            self.connect_renders()
            self.render_chunks()
            self.init_chunks()

        # avançar verticalmente
        if self.personagem.rect.centery < (self.chunks['1, 1'].loc[1]) * Chunk.dimensions[0]:
            self.save_chunk_verifier([self.chunks['2, 0'], self.chunks['2, 1'], self.chunks['2, 2']])
            self.chunks['2, 0'], self.chunks['2, 1'], self.chunks['2, 2'] = self.chunks['1, 0'], self.chunks[
                '1, 1'], self.chunks['1, 2']
            self.chunks['1, 0'], self.chunks['1, 1'], self.chunks['1, 2'] = self.chunks['0, 0'], self.chunks[
                '0, 1'], self.chunks['0, 2']

            if self.chunks['1, 0'].around_chunks[0] is not None:
                self.chunks['0, 0'] = self.environment_generator.buscar_blocos(
                    [self.chunks['1, 0'].loc[0], self.chunks['1, 0'].loc[1] - 1],
                    chunk_id=self.chunks['1, 0'].around_chunks[0], by_pos=False)
            else:
                self.chunks['0, 0'] = self.environment_generator.buscar_blocos(
                    [self.chunks['1, 0'].loc[0], self.chunks['1, 0'].loc[1] - 1])

            if self.chunks['1, 1'].around_chunks[0] is not None:
                self.chunks['0, 1'] = self.environment_generator.buscar_blocos(
                    [self.chunks['1, 1'].loc[0], self.chunks['1, 1'].loc[1] - 1],
                    chunk_id=self.chunks['1, 1'].around_chunks[0], by_pos=False)
            else:
                self.chunks['0, 1'] = self.environment_generator.buscar_blocos(
                    [self.chunks['1, 1'].loc[0], self.chunks['1, 1'].loc[1] - 1])

            if self.chunks['1, 2'].around_chunks[0] is not None:
                self.chunks['0, 2'] = self.environment_generator.buscar_blocos(
                    [self.chunks['1, 2'].loc[0], self.chunks['1, 2'].loc[1] - 1],
                    chunk_id=self.chunks['1, 2'].around_chunks[0], by_pos=False)
            else:
                self.chunks['0, 2'] = self.environment_generator.buscar_blocos(
                    [self.chunks['1, 2'].loc[0], self.chunks['1, 2'].loc[1] - 1])

            self.connect_renders()
            self.render_chunks()
            self.init_chunks()

        if self.personagem.rect.centery > (self.chunks['1, 1'].loc[1] + 1) * Chunk.dimensions[0]:
            self.save_chunk_verifier([self.chunks['0, 0'], self.chunks['0, 1'], self.chunks['0, 2']])
            self.chunks['0, 0'], self.chunks['0, 1'], self.chunks['0, 2'] = self.chunks['1, 0'], self.chunks[
                '1, 1'], self.chunks['1, 2']
            self.chunks['1, 0'], self.chunks['1, 1'], self.chunks['1, 2'] = self.chunks['2, 0'], self.chunks[
                '2, 1'], self.chunks['2, 2']

            if self.chunks['1, 0'].around_chunks[2] is not None:
                self.chunks['2, 0'] = self.environment_generator.buscar_blocos(
                    [self.chunks['1, 0'].loc[0], self.chunks['1, 0'].loc[1] + 1],
                    chunk_id=self.chunks['1, 0'].around_chunks[2], by_pos=False)
            else:
                self.chunks['2, 0'] = self.environment_generator.buscar_blocos(
                    [self.chunks['1, 0'].loc[0], self.chunks['1, 0'].loc[1] + 1])

            if self.chunks['1, 1'].around_chunks[2] is not None:
                self.chunks['2, 1'] = self.environment_generator.buscar_blocos(
                    [self.chunks['1, 1'].loc[0], self.chunks['1, 1'].loc[1] + 1],
                    chunk_id=self.chunks['1, 1'].around_chunks[2], by_pos=False)
            else:
                self.chunks['2, 1'] = self.environment_generator.buscar_blocos(
                    [self.chunks['1, 1'].loc[0], self.chunks['1, 1'].loc[1] + 1])

            if self.chunks['1, 2'].around_chunks[2] is not None:
                self.chunks['2, 2'] = self.environment_generator.buscar_blocos(
                    [self.chunks['1, 2'].loc[0], self.chunks['1, 2'].loc[1] + 1],
                    chunk_id=self.chunks['1, 2'].around_chunks[2], by_pos=False)
            else:
                self.chunks['2, 2'] = self.environment_generator.buscar_blocos(
                    [self.chunks['1, 2'].loc[0], self.chunks['1, 2'].loc[1] + 1])

            self.connect_renders()
            self.render_chunks()
            self.init_chunks()

    def update_platforms(self):
        self.monitor_de_lotes()

        for waiter in self.loop_waiters:
            waiter.init_loop()

        for chunk in self.chunks.values():
            for platform in chunk.platforms:
                for waiter in self.loop_waiters:
                    waiter.run(platform)

                if ((platform.x - self.personagem.rect.centerx)**2+(platform.y - self.personagem.rect.centery)**2)**(1/2) < 700:
                    self.janela.blit(self.platform_meta_data.PLATFORM_IMAGES[platform.type], (platform.x+self.pos_de_apresentacao[0], platform.y+self.pos_de_apresentacao[1]))

        to_destroy_waiters = []

        for waiter in self.loop_waiters:
            waiter.finalise_loop()
            if waiter.one_time:
                to_destroy_waiters.append(waiter)

        for waiter in to_destroy_waiters:
            self.loop_waiters.remove(waiter)

        to_destroy_waiters.clear()

        #for render in self.chunk_renders:
        #    self.janela.blit(render.surface, (render.pos[0] + self.pos_de_apresentacao[0], render.pos[1] + self.pos_de_apresentacao[1]))


    def atualizar_monitor(self):
        self.pos_de_apresentacao[0] = pygame.display.Info().current_w // 2 - self.personagem.rect.center[0]
        self.pos_de_apresentacao[1] = pygame.display.Info().current_h * 2 // 3 - self.personagem.rect.center[1]

    def desenhar_personagem(self):
        self.personagem.atualizar_frame()
        self.janela.blit(self.personagem.imagem, (
            self.personagem.rect.x + self.pos_de_apresentacao[0], self.personagem.rect.y + self.pos_de_apresentacao[1]))

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

        self.gerenciador_de_movimento_vertical()
        self.gerenciador_de_movimento_horizontal()
        self.desenhar_personagem()
        #self.mover_personagem()

    def verificador_clicar_bloco(self, pos):
        self.loop_waiters.append(MouseClickWaiter(pos, self.pos_de_apresentacao, self.personagem.rect.x, self.personagem.rect.y, self))

    def monitor_de_movimentos(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.deletar_blocos_correntes()
                self.QUIT = True
                self.environment_generator.big_last_save()
                if DEBUG:
                    self.environment_generator.consultor.clear_database()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.verificador_clicar_bloco(event.pos)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    self.personagem.right = True
                if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    self.personagem.left = True
                if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    self.personagem.down = True
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    self.personagem.up = True

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    self.personagem.right = False
                if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    self.personagem.left = False
                if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    self.personagem.down = False
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    self.personagem.up = False


if __name__ == '__main__':
    DEBUG = True

    pygame.display.init()

    infoObject = pygame.display.Info()
    print(infoObject)
    w = int(infoObject.current_w)
    h = int(infoObject.current_h)
    screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
    pygame.display.set_caption('Cube\'s Odyssey')

    imagem = pygame.transform.scale(pygame.image.load('game_images/background_forest.png'),
                                    (pygame.display.Info().current_w, pygame.display.Info().current_h)).convert()

    gerenciador = GerenciadorDeElementos(screen)

    mainClock = pygame.time.Clock()
    counter = 0

    # loop #
    while True:
        screen.blit(imagem, (0, 0))

        gerenciador.atualizar()

        if gerenciador.QUIT:
            break

        pygame.display.update()
        mainClock.tick(gerenciador.fps)
        if counter % 100 == 0:
            print(mainClock.get_fps())

        counter += 1

    pygame.quit()
    sys.exit()
