import pygame
from menu import Menu
import game
import sys

if __name__ == '__main__':
    DEBUG = True

    screen = pygame.display.set_mode((700, 600), pygame.RESIZABLE)

    pygame.display.set_caption('Cube\'s Odyssey')

    menu = Menu(screen)

    mainClock = pygame.time.Clock()

    while 1:
        menu.render()
        menu.event_handler()
        match menu.curr_state:
            case 'quitting':
                break
            case 'playing':
                menu.stop_state()
                game.run(screen, menu.play_world)
    
    if menu.curr_state == 'quitting':
        sys.exit()
    
    
    
