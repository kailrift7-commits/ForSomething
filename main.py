import pygame
pygame.init()  # ← КРИТИЧЕСКИ ВАЖНО: инициализация ДО любых импортов, использующих pygame

import back as Back
import front as Front
import consts as c

def draw_all():
    Back.screen.fill(c.BACKGROUND_COLOR)
    Front.draw_field()
    Front.draw_interface()
    pygame.display.flip()

def recalc():
    Back.recalc()

def handle_events():
    global running
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            for i in range(c.ROOM_SIZE_Y):
                for j in range(c.ROOM_SIZE_X):
                    if event.button == 1:
                        if Back.squares[i][j].collidepoint(event.pos) and Back.dont_change_mask[i][j]:
                            Back.set_object((i, j), setting_obj=Back.setting_obj)
                        elif Back.squares[i][j].collidepoint(event.pos) and not Back.dont_change_mask[i][j] and Back.setting_obj == 'floor':
                            Back.set_floor(i, j)
                        elif Back.squares[i][j].collidepoint(event.pos) and not Back.dont_change_mask[i][j] and Back.setting_obj == 'outdoor':
                            Back.set_outdoor(i, j)
                    if event.button == 3:
                        #if Back.squares[i][j].collidepoint(event.pos) and Back.dont_change_mask[i][j]:
                        #    for group in Back.sensors:
                        #        for idx, sensor in enumerate(group):
                        #            if sensor.X == j and sensor.Y == i:
                        #                group.pop(idx)
                        #                break
                        if Back.squares[i][j].collidepoint(event.pos):
                            Back.remove_object(i,j)
                    if event.button == 4:  # Mouse wheel up
                        if Back.squares[i][j].collidepoint(event.pos) and Back.dont_change_mask[i][j]:
                            Back.temperatures[-1][i][j] += 5
                    if event.button == 5:  # Mouse wheel down
                        if Back.squares[i][j].collidepoint(event.pos) and Back.dont_change_mask[i][j]:
                            Back.temperatures[-1][i][j] -= 5
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_h: Back.setting_obj = 'heater'
            if event.key == pygame.K_c: Back.setting_obj = 'ac'
            if event.key == pygame.K_w: Back.setting_obj = 'wall'
            if event.key == pygame.K_e: Back.setting_obj = 'floor'
            if event.key == pygame.K_s: Back.setting_obj = 'sensor'
            if event.key == pygame.K_r: Back.setting_obj = 'window'
            if event.key == pygame.K_d: Back.setting_obj = 'door'
            if event.key == pygame.K_f: Back.setting_obj = 'floor'
            if event.key == pygame.K_o: Back.setting_obj = 'outdoor'
            if event.key == pygame.K_LEFT:  Back.outdoor_temp -= 5
            if event.key == pygame.K_RIGHT: Back.outdoor_temp += 5
            if event.key == pygame.K_DOWN:  Back.desired_temp -= 5
            if event.key == pygame.K_UP:    Back.desired_temp += 5
            if event.key == pygame.K_6: Back.regulationType = 'r'    
            if event.key == pygame.K_7: Back.regulationType = 'p'
            if event.key == pygame.K_8: Back.regulationType = 'pi'
            if event.key == pygame.K_9: Back.regulationType = 'pid'
            if event.key == pygame.K_1: Back.sensor_group = 0
            if event.key == pygame.K_2: Back.sensor_group = 1
            if event.key == pygame.K_3: Back.sensor_group = 2
            if event.key == pygame.K_4: Back.sensor_group = 3
            if event.key == pygame.K_5: Back.sensor_group = 4
            if event.key == pygame.K_m: Back.show_plot = not Back.show_plot

running = True
fpsclock = pygame.time.Clock()

while running:
    draw_all()
    recalc()
    handle_events()
    fpsclock.tick(120)

pygame.quit()
