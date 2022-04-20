import consulta_ao_banco
import pygame
import image_generator
import debugger
import numpy as np


class EnvironmentGenerator:
    def __init__(self):
        self.consultor = consulta_ao_banco.ConsultorDB()
        self.have_changes = False

    def big_last_save(self):
        self.consultor.bigger_commit()

    def its_safe_to_commit(self):
        if self.have_changes:
            self.consultor.commit()
            self.have_changes = False

    def delete_chunk(self, chunk):
        if chunk.around_chunks_changes:
            new_around = chunk.get_around_chunks()
            self.consultor.update_chunk_around(chunk.index, new_around)
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

    def buscar_blocos(self, pos, chunk_id=None, by_pos=True):
        if by_pos:
            pos_p = f'{pos[0]},{pos[1]}'
            result = self.consultor.get_chunk_by_pos(pos_p)
            if result:  # Already exists
                chunk_index, _, around_chunks = result[0]
                around_chunks = [int(x) if x != '|' else None for x in around_chunks.split()]
                blocks = self.consultor.search_chunk(chunk_index)
                chunk = Chunk(pos, chunk_index, around_chunks, blocks=self.raw_to_processed_block_transformer(blocks))

            else:  # Not exists yet
                # b == (index, type, chunk)
                chunk = Chunk(pos, self.consultor.last_chunk_index, [None for i in range(4)])
                self.consultor.increment_last_chunk_index()

                pre_saved_blocks = list()

                for li, line in enumerate(chunk.blocks):
                    for ci, column in enumerate(line):
                        for layer, type in enumerate(column):
                            pre_saved_blocks.append((li*Chunk.chunk_length*2+ci*2+layer, int(type), pos_p))

                self.consultor.write_chunk(pos_p, pre_saved_blocks, chunk.get_around_chunks())

                self.have_changes = True

        else:
            chunk_index, pos, around_chunks = self.consultor.get_chunk_by_id(chunk_id)
            pos = [int(x) for x in pos.split(',')]
            around_chunks = [int(x) if x != '|' else None for x in around_chunks.split()]
            blocks = self.consultor.search_chunk(chunk_index)
            chunk = Chunk(pos, chunk_index, around_chunks, blocks=self.raw_to_processed_block_transformer(blocks))

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
                    ambiente[line][column] = [3, 0]
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
                block_array[line][column] = [tipo, 0]
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

    def __init__(self, loc, index, around_chunks, blocks=None):
        self.loc = loc
        self.index = index
        self.blocks = blocks
        self.block_changes = list()
        self.render: image_generator.ChunkRender = None

        self.around_chunks = around_chunks
        self.around_chunks_changes = False

        if self.blocks is None:
            self.blocks = EnvironmentGenerator.environment_generator(self.loc)

        self.len_platforms = 0

        self.platforms = self.array_abstraction()

    def disconnect_render(self):
        self.render.disconnect()
        self.render = None

    def get_around_chunks(self):
        return ' '.join([str(chunk_id) if chunk_id is not None else '|' for chunk_id in self.around_chunks])

    def remove_block(self, platform):
        pos = platform.get_pos()
        self.blocks[pos[0]][pos[1]][pos[2]] = 0
        self.platforms.remove(platform)
        self.render.remove_block(platform)
        self.block_changes.append(self.RemoveChange(platform.get_global_indexer()))

    def set_around_chunks(self, chunk_id: int, pos: int):
        """
        Chunks have an attribute that store the around chunks id for optimized sql query
        the order is like this:
            0
        3  self  1
            2

        """
        if self.around_chunks[pos] is None:
            self.around_chunks[pos] = chunk_id
            self.around_chunks_changes = True
        else:
            if self.around_chunks[pos] != chunk_id:
                raise Exception(f"O around do chunk {self.index}, na posição {pos}, já estava setado, antigo:{self.around_chunks[pos]}, novo: {chunk_id}")

    def array_abstraction(self):
        platforms = list()
        for li, line in enumerate(self.blocks):
            for ci, column in enumerate(line):
                for layer, ptype in enumerate(column):
                    if ptype == 0:  # Só cria plataformas quando o espaço não é vazio
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