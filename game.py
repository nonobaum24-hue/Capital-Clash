import os
import pygame
from mainloop import mainloop
from boss_fight import boss_fight
from startmenu import startmenu

screen = startmenu()
print('erfolgreicher skip')
mainloop(screen)
print('jetzt würde boss kommen')
boss_fight(screen)

pygame.quit()