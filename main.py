import pygame
from menu import Menu

if __name__ == '__main__':
    DEBUG = True

    screen = pygame.display.set_mode((700, 600), pygame.RESIZABLE)

    menu = Menu(screen)

    while 1:
        menu.render()
        menu.event_handler()
        if menu.QUIT:
            break