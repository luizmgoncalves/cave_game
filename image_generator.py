import pygame
import world_generator


class ChunkRender:
    def __init__(self, chunk):
        self.surface = pygame.Surface(world_generator.Chunk.dimensions).convert()
        self.surface.set_colorkey((255, 0, 255))

        self.platform_meta_data = world_generator.PlatformData()

        self.chunk = chunk
        chunk.render = self
        self.connected = True
        self.pos = (chunk.loc[0] * chunk.dimensions[0], chunk.loc[1] * chunk.dimensions[1])
        self.rendered = False

    def remove_block(self, platform):
        li, ci, layer = platform.get_pos()
        pygame.draw.rect(self.surface, (255, 0, 255), ((ci * world_generator.Chunk.platform_dimensions[0],li * world_generator.Chunk.platform_dimensions[1]), platform.dimensions))

    def render(self):
        self.surface.fill((255, 0, 255))

        for platform in self.chunk.platforms:
            pos = platform.get_pos()
            self.surface.blit(self.platform_meta_data.PLATFORM_IMAGES[platform.type],(pos[1] * world_generator.Chunk.platform_dimensions[0], pos[0] * world_generator.Chunk.platform_dimensions[1]))

        self.rendered = True

    def disconnect(self):
        self.chunk = None
        self.connected = False
        self.rendered = False

    def connect(self, chunk):
        self.chunk = chunk
        chunk.render = self
        self.connected = True
        self.pos = (chunk.loc[0] * chunk.dimensions[0], chunk.loc[1] * chunk.dimensions[1])



