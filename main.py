import pygame
from menu import Menu
import game
import sys

if __name__ == '__main__':
    DEBUG = True

    screen = pygame.display.set_mode((700, 600), pygame.RESIZABLE)

    pygame.display.set_caption('Cube\'s Odyssey')

    menu = Menu(screen)

    while 1:
        menu.render()
        menu.event_handler()
        if menu.curr_state in ['quitting', 'playing']:
            break
    
    if menu.curr_state == 'quitting':
        sys.exit()
    
    game.run(screen, menu.play_world)
    
