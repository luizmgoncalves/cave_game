import consulta_ao_banco
import pygame
import debugger
import numpy as np


class EnvironmentGenerator:
    def __init__(self):
        self.consultor = consulta_ao_banco.ConsultorDB()
        self.have_changes = False
        self.all_chunks = {}
        self.all_chunks_pos = {}
        result = self.consultor.get_all()
        
        for chunk in result:  # Already exists
            chunk_index, _, _ = chunk
            blocks = self.consultor.search_chunk(chunk_index)
            self.all_chunks[chunk_index] = Chunk([int(x) for x in chunk[1].split(',')], chunk_index, blocks=self.raw_to_processed_block_transformer(blocks))
            self.all_chunks_pos[chunk[1]] = chunk_index


    def big_last_save(self):
        for chunk in self.all_chunks.values():
            self.delete_chunk(chunk)
        
        self.consultor.bigger_commit()

    def its_safe_to_commit(self):
        if self.have_changes:
            self.consultor.commit()
            self.have_changes = False

    def delete_chunk(self, chunk):
        if chunk.was_added:
            # b == (index, type, chunk)
            pos_p = f'{chunk.loc[0]},{chunk.loc[1]}'
            pre_saved_blocks = list()

            for li, line in enumerate(chunk.blocks):
                for ci, column in enumerate(line):
                    for layer, type in enumerate(column):
                        pre_saved_blocks.append((li*Chunk.chunk_length*2+ci*2+layer, int(type), pos_p))

            self.consultor.write_chunk(pos_p, pre_saved_blocks)

            self.have_changes = True

        if chunk.block_changes:
            block_list = list()

            for change in chunk.block_changes:
                # b == (index, type, chunk)

                changed_block = {'type': change.new_value,
                                 'global_indexer': change.index}
                block_list.append(tuple(changed_block.values()))

            self.consultor.update_blocks(block_list)

            self.have_changes = True

            chunk.block_changes.clear()
    
    def chunk_exists(self, pos) -> bool:
        try:
            res = self.all_chunks_pos[pos]
            return res
        except KeyError:
            return None

    def buscar_blocos(self, pos):
        pos_p = f'{pos[0]},{pos[1]}'
        try: 
            result = self.all_chunks_pos[pos_p]
            # Already exists
            chunk = self.all_chunks[result]
        except KeyError: # Not exists yet
            chunk = self.all_chunks[self.consultor.last_chunk_index] = Chunk(pos, self.consultor.last_chunk_index)
            self.all_chunks_pos[pos_p] = self.consultor.last_chunk_index
            self.consultor.increment_last_chunk_index()

        return chunk

    @staticmethod
    def raw_to_processed_block_transformer(blocks):
        # block == (index, type, chunk)

        chunk_blocks = np.uint8(np.zeros((Chunk.chunk_length, Chunk.chunk_length, 2)))

        counter = 0

        for line in range(Chunk.chunk_length):
            for column in range(Chunk.chunk_length):
                for layer in range(2):
                    try:
                        chunk_blocks[line][column][layer] = blocks[counter][1]
                        counter += 1
                    except:
                        print(blocks)
                        print(counter)
                        raise Exception()

        return chunk_blocks

    @staticmethod
    def environment_generator(pos_absolute=[0, 0]):
        ambiente = np.uint8(np.zeros((Chunk.chunk_length, Chunk.chunk_length, 2)))
        if pos_absolute[1] == 0:
            return EnvironmentGenerator.surface_generator()

        elif pos_absolute[1] > 0:
            for line in range(0, Chunk.chunk_length):
                for column in range(0, Chunk.chunk_length):
                    ambiente[line][column] = [3, 3]
            return ambiente
        else:
            return ambiente

    @staticmethod
    def surface_generator():
        import random
        block_array = np.uint8(np.zeros((Chunk.chunk_length, Chunk.chunk_length, 2)))
        surface_line = 10
        first_line = True

        for line in range(surface_line, Chunk.chunk_length):
            for column in range(0, Chunk.chunk_length):
                if first_line:
                    tipo = 1
                else:
                    tipo = 2
                block_array[line][column] = [tipo, tipo]
            first_line = False

        trees = [random.randrange(0, Chunk.chunk_length, random.randint(2, 6)) for x in range(0, 3)]
        trees = set(trees)
        trees = [[tree, random.randint(2, 5)] for tree in trees]
        for tree in trees:
            height_atual = surface_line - 1
            for block in range(tree[1]):
                block_array[height_atual][tree[0]] = [4, 0]
                height_atual -= 1

        return block_array


class Chunk:
    class BlockChange:
        def __init__(self, index, new_value, *args, **kwargs):
            self.index = index
            self.new_value = new_value

    class RemoveChange(BlockChange):
        def __init__(self, index, *args, **kwargs):
            super().__init__(index=index, new_value=0, *args, **kwargs)

    class AddChange(BlockChange):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

    platform_dimensions = [50, 50]
    chunk_length = 40
    dimensions = (platform_dimensions[0] * chunk_length, platform_dimensions[1] * chunk_length)

    def __init__(self, loc, index, blocks=None):
        self.loc = loc
        self.index = index
        self.blocks = blocks
        self.block_changes = list()

        self.was_added = False

        if self.blocks is None:
            self.blocks = EnvironmentGenerator.environment_generator(self.loc)
            self.was_added = True

        self.len_platforms = 0

        self.platforms = self.array_abstraction()

    def __repr__(self):
        return f'<Chunk object id: {self.index}, loc: {self.loc}>'

    def remove_block(self, platform):
        pos = platform.get_pos()
        self.blocks[pos[0]][pos[1]][pos[2]] = 0
        self.platforms.remove(platform)
        if pos[2] == 0 and self.blocks[pos[0]][pos[1]][pos[2]+1]:
            kwargs = {'pos': (self.loc[0] * Chunk.dimensions[0] + pos[1] * Platform.dimensions[0],
                                      self.loc[1] * Chunk.dimensions[1] + pos[0] * Platform.dimensions[1]),
                              'ptype': self.blocks[pos[0]][pos[1]][pos[2]+1],
                              'layer': 1,
                              'owner': self,
                              'index': pos[0] * self.chunk_length * 2 + pos[1] * 2 + 1}  # [li, ci, layer]}

            self.platforms.append(Platform(**kwargs))

        self.block_changes.append(self.RemoveChange(platform.get_global_indexer()))

    def array_abstraction(self):
        platforms = list()
        for li, line in enumerate(self.blocks):
            for ci, column in enumerate(line):
                for layer, ptype in enumerate(column):
                    if ptype == 0:  # Só cria plataformas quando o espaço não é vazio
                        continue
                    if layer==1 and column[layer-1]:
                        continue

                    kwargs = {'pos': (self.loc[0] * Chunk.dimensions[0] + ci * Platform.dimensions[0],
                                      self.loc[1] * Chunk.dimensions[1] + li * Platform.dimensions[1]),
                              'ptype': int(ptype),
                              'layer': layer,
                              'owner': self,
                              'index': li * self.chunk_length * 2 + ci * 2 + layer}  # [li, ci, layer]}

                    platforms.append(Platform(**kwargs))
                    self.len_platforms += 1

        return platforms

    def easy_block_getter(self):
        for li, line in enumerate(self.blocks):
            for ci, column in enumerate(line):
                for layer, ptype in enumerate(column):
                    if ptype == 0:  # Só retorna plataformas quando o espaço não é vazio
                        continue
                    

                    yield {'pos': (self.loc[0] * Chunk.dimensions[0] + ci * Platform.dimensions[0],
                                   self.loc[1] * Chunk.dimensions[1] + li * Platform.dimensions[1]),
                           'type': int(ptype),
                           'layer': layer}


class Platform(pygame.Rect):
    dimensions = tuple(Chunk.platform_dimensions)
    non_colidable_types = (
        4,  # tree log
    )

    def __init__(self, pos, layer, ptype, owner: Chunk, index, *args, **kwargs):
        super().__init__(pos, self.dimensions)
        self.owner = owner
        self.layer = layer
        self.index = index
        self.colidable = False if ptype in self.non_colidable_types or layer == 1 else True

        self.type = ptype
        """
        Type and respective plataforms:
        0: air
        1: grass
        2: dirt
        3: stone
        4: tree wood
        """

    def get_pos(self):
        # li * self.chunk_length * 2 + ci * 2 + layer
        li = self.index // (Chunk.chunk_length*2)
        ci = (self.index % (Chunk.chunk_length*2))//2
        layer = self.index % 2
        return li, ci, layer

    def get_global_indexer(self):
        return (self.owner.index-1)*Chunk.chunk_length*Chunk.chunk_length*2+1+self.index


class PlatformData:
    def __init__(self):
        self.PLATFORM_IMAGES = [None,
                                pygame.transform.scale(pygame.image.load('game_images/Bloco-grama.png'),
                                                       tuple(Platform.dimensions)).convert(),
                                pygame.transform.scale(pygame.image.load('game_images/Bloco-terra.png'),
                                                       tuple(Platform.dimensions)).convert(),
                                pygame.transform.scale(pygame.image.load('game_images/Bloco-pedra.png'),
                                                       tuple(Platform.dimensions)).convert(),
                                pygame.transform.scale(pygame.image.load('game_images/wood_texture.jpg'),
                                                       tuple(Platform.dimensions)).convert()]

        self.PLATFORM_IMAGES_UN = [None]

        for image in self.PLATFORM_IMAGES[1:]:
            darken_percent = 0.50
            dark = pygame.Surface(image.get_size()).convert_alpha()
            dark.fill((0, 0, 0, darken_percent*255))
            darker = image.copy()
            darker.blit(dark, (0, 0))
            darker.convert()
            self.PLATFORM_IMAGES_UN.append(darker)

        