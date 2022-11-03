import debugger
import sqlite3
import world_generator
import os


class ConsultorDB:
    def __init__(self):
        self.banco_sql = sqlite3.connect('game_db.db')
        self.cursor = self.banco_sql.cursor()

        self.last_block_index = None
        self.last_chunk_index = None

        self.read_last_index()

    def commit(self):
        print('to comitando')
        self.banco_sql.commit()

    def increment_last_chunk_index(self):
        self.last_chunk_index += 1
        print("Last index = ", self.last_chunk_index)

    def increment_last_block_index(self):
        self.last_block_index += 1

    def read_last_index(self):
        self.cursor.execute(f"SELECT * FROM last_index")
        resposta = self.cursor.fetchall()

        if not len(resposta):
            self.last_block_index = 1
            self.last_chunk_index = 1
            return

        self.last_block_index = resposta[0][0]
        self.last_chunk_index = resposta[0][1]
        print(resposta)
        print("Reading index = ", self.last_chunk_index)

    def write_last_index(self):
        self.cursor.execute(f"DELETE FROM last_index WHERE TRUE")
        self.cursor.execute(f"INSERT INTO last_index values ('{self.last_block_index}', '{self.last_chunk_index}')")
        print("Writing last index = ", self.last_chunk_index)

    def update_blocks(self, block_list): # block list = ((new_type, block_id), ...)
        self.cursor.executemany(f"UPDATE blocks SET ptype = ? WHERE global_indexer = ?", block_list)

    def get_chunk_by_pos(self, pos):
        self.cursor.execute(f"SELECT * FROM chunks WHERE chunk='{pos}'")
        result = self.cursor.fetchall()
        return result if len(result) > 0 else False

    def get_chunk_by_id(self, chunk_id):
        self.cursor.execute(f"SELECT * FROM chunks WHERE indexer='{chunk_id}'")
        return self.cursor.fetchall()[0]

    def write_chunk(self, pos, block_list):
        self.cursor.execute(f"INSERT INTO chunks (chunk) values ('{pos}')")

        self.cursor.executemany(f"INSERT INTO blocks (indexer, ptype, chunk) values (?, ?, ?)", block_list)

    def search_chunk(self, chunk_index):
        self.cursor.execute(f"SELECT * FROM chunks WHERE indexer='{chunk_index}'")
        if len(self.cursor.fetchall()) == 0:
            print("Deu ruim >:) kkkkkkk !!!")
            raise Exception()

        self.cursor.execute(f"SELECT indexer, ptype, chunk FROM blocks WHERE global_indexer > {(chunk_index-1)*world_generator.Chunk.chunk_length*world_generator.Chunk.chunk_length*2} and global_indexer <= {chunk_index*40*40*2}")
        return self.cursor.fetchall()
    
    def get_all(self):
        self.cursor.execute(f"SELECT * FROM chunks")
        return self.cursor.fetchall()

    def clear_database(self):
        self.clear_blocks_table()
        self.clear_chunks_table()
        self.clear_last_index_table()

    def clear_last_index_table(self):
        self.cursor.execute("DELETE from last_index ")
        # Clear table because all blocks have a positive or null type

        self.banco_sql.commit()

    def clear_blocks_table(self):
        self.cursor.execute("DELETE from blocks ")
        # Clear table because all blocks have a positive or null type

        self.banco_sql.commit()

    def clear_chunks_table(self):
        self.cursor.execute("DELETE from chunks ")
        # CLear table because all chunks have a not null string in "chunk" field
        self.banco_sql.commit()

    def bigger_commit(self):
        self.write_last_index()
        b = debugger.DurationTest()
        self.banco_sql.commit()
        b.get_atual_delay('o ultimo e maior commit!')


def generate_db(name: str):
    database = sqlite3.connect(f'db/{name}.db')
    cursor = database.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS "last_index" (
        "last_block_index"	INTEGER,
        "last_chunk_index"	INTEGER
    );""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS "chunks" (
        "indexer"	INTEGER,
        "chunk"	TEXT,
        "around_chunks"	TEXT,
        PRIMARY KEY("indexer")
    );""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS "blocks" (
        "global_indexer"	INTEGER,
        "indexer"	INTEGER,
        "ptype"	INTEGER,
        "chunk"	TEXT,
        PRIMARY KEY("global_indexer")
    );""")

def delete_db(name: str):
    os.remove(f'db/{name}.db')


if __name__ == '__main__':
    def CDB():
        db = ConsultorDB()
        db.clear_database()

    while True:
        input_str = input('cursor-db>> ')

        if input_str == 'exit':
            break
        try:
            eval(input_str)
        except Exception as error:
            print(f'Error: {error}')
