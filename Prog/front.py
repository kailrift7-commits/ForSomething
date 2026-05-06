import consts as c 
import back as Back
import pygame
from io import BytesIO
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import numpy as np


SQUARE_FONT = pygame.font.Font(None, c.SQUARE_FONT_SIZE)

_TEMP_TEXT_CACHE = {}
for temp in range(-60, 121):
    _TEMP_TEXT_CACHE[temp] = SQUARE_FONT.render(str(temp), True, c.MAIN_TEXT_COLOR)

# Кэш для "H" и сенсорных температур
_H_TEXT_SURF = SQUARE_FONT.render("H", True, c.MAIN_TEXT_COLOR)
_SENSOR_TEXT_CACHE = {}

class Button:
    def __init__(self, pos, size, function, text, font):
        self.onePress = False
        self.isAlreadyPressed = False
        self.height = size[0]
        self.width = size[1]
        self.X = pos[0]
        self.Y = pos[1]
        self.function = function
        self.text = text

        self.buttonSurface = pygame.Surface((self.width, self.height))
        self.buttonRect = pygame.Rect(self.X, self.Y, self.width, self.height)
        self.buttonSurf = font.render(text, True, (20, 20, 20))
        self.colors = {
            'normal': (240, 240, 240),
            'hover': (150, 150, 150),
            'pressed': (40, 40, 40)
        }
    
    def process(self):
        mousePos = pygame.mouse.get_pos()
        self.buttonSurface.fill(self.colors['normal'])
        if self.buttonRect.collidepoint(mousePos):
            self.buttonSurface.fill(self.colors['hover'])
            if pygame.mouse.get_pressed(num_buttons=3)[0]:
                self.buttonSurface.fill(self.colors['pressed'])
                if self.onePress:
                    self.function()
                elif not self.isAlreadyPressed:
                    self.function()
                    self.isAlreadyPressed = True
            else:
                self.isAlreadyPressed = False
        self.buttonSurface.blit(self.buttonSurf, [
            self.buttonRect.width / 2 - self.buttonSurf.get_rect().width / 2,
            self.buttonRect.height / 2 - self.buttonSurf.get_rect().height / 2
        ])
        Back.screen.blit(self.buttonSurface, self.buttonRect)

def printSomething():
    print("something")

def adjustDesiredTemp():
    Back.desired_temp += 1
def descendDesiredTemp():
    Back.desired_temp -= 1
def adjustOutdoorTemp():
    Back.outdoor_temp += 1
def descendOutdoorTemp():
    Back.outdoor_temp -= 1

objects = []
objects.append(Button((c.X_SCREEN_OFFSET + c.SQUARE_SIZE * c.ROOM_SIZE_X + 10 + 410, 0 + 10 + 50 * 4), (40, 40), descendDesiredTemp, '<', SQUARE_FONT))
objects.append(Button((c.X_SCREEN_OFFSET + c.SQUARE_SIZE * c.ROOM_SIZE_X + 10 + 410 + 50, 0 + 10 + 50 * 4), (40, 40), adjustDesiredTemp, '>', SQUARE_FONT))
objects.append(Button((c.X_SCREEN_OFFSET + c.SQUARE_SIZE * c.ROOM_SIZE_X + 10 + 410, 0 + 10 + 50), (40, 40), descendOutdoorTemp, '<', SQUARE_FONT))
objects.append(Button((c.X_SCREEN_OFFSET + c.SQUARE_SIZE * c.ROOM_SIZE_X + 10 + 410 + 50, 0 + 10 + 50), (40, 40), adjustOutdoorTemp, '>', SQUARE_FONT))

def draw_interface():
    draw_rectangle((0, 0), (c.X_SCREEN_OFFSET, c.HEIGHT), (120, 120, 120))
    draw_rectangle((c.X_SCREEN_OFFSET + c.SQUARE_SIZE * c.ROOM_SIZE_X, 0), 
                   (c.WIDTH - c.X_SCREEN_OFFSET - c.SQUARE_SIZE * c.ROOM_SIZE_X, c.HEIGHT), 
                   (40, 40, 40))

    draw_label(f"|- Setting object -> {Back.setting_obj} -|", pygame.font.SysFont("notosansmono", 16),
               (c.X_SCREEN_OFFSET + c.SQUARE_SIZE * c.ROOM_SIZE_X + 10, 0 + 10), (400, 40), 
               c.MAIN_TEXT_COLOR, (210, 210, 210))
    draw_label(f"|- Outdoor temperature -> {Back.outdoor_temp} -|", pygame.font.SysFont("notosansmono", 16),
               (c.X_SCREEN_OFFSET + c.SQUARE_SIZE * c.ROOM_SIZE_X + 10, 0 + 10 + 50), (400, 40), 
               c.MAIN_TEXT_COLOR, (210, 210, 210))
    draw_label(f"|- Regulation Type -> {Back.regulationType} -|", pygame.font.SysFont("notosansmono", 16),
               (c.X_SCREEN_OFFSET + c.SQUARE_SIZE * c.ROOM_SIZE_X + 10, 0 + 10 + 50 + 50), (400, 40), 
               c.MAIN_TEXT_COLOR, (210, 210, 210))
    draw_label(f"|- Sensors group -> {Back.sensor_group + 1} -|", pygame.font.SysFont("notosansmono", 16),
               (c.X_SCREEN_OFFSET + c.SQUARE_SIZE * c.ROOM_SIZE_X + 10, 0 + 10 + 50 + 50 + 50), (400, 40), 
               c.MAIN_TEXT_COLOR, (210, 210, 210))
    draw_label(f"|- Regulation temperature -> {Back.desired_temp} -|", pygame.font.SysFont("notosansmono", 16),
               (c.X_SCREEN_OFFSET + c.SQUARE_SIZE * c.ROOM_SIZE_X + 10, 0 + 10 + 50 * 4), (400, 40), 
               c.MAIN_TEXT_COLOR, (210, 210, 210))
    
    for obj in objects:
        obj.process()

    if Back.show_plot:
        draw_plot(c.X_SCREEN_OFFSET + c.SQUARE_SIZE * c.ROOM_SIZE_X + 10, 0 + 10 + 50 * 5, desired_temp=Back.desired_temp)


def draw_field():
    group_colors = [
        (255, 0, 0),      # Красный - группа 1
        (255, 255, 0),    # Жёлтый - группа 2
        (255, 165, 0),    # Оранжевый - группа 3
        (128, 0, 128),    # Фиолетовый - группа 4
        (0, 0, 255)       # Синий - группа 5
    ]
    
    # Сначала рисуем все ячейки поля
    for i in range(c.ROOM_SIZE_Y):
        for j in range(c.ROOM_SIZE_X):
            pygame.draw.rect(Back.screen, Back.colors[i][j], Back.squares[i][j])
    
    for i in range(c.ROOM_SIZE_Y):
        for j in range(c.ROOM_SIZE_X):
            if Back.colors[i][j] not in (c.HEATER_COLOR,c.AC_COLOR):
                temp_int = int(round(Back.temperatures[-1][i][j]))
                temp_int = max(-60, min(120, temp_int))
                text_surf = _TEMP_TEXT_CACHE[temp_int]
                text_rect = text_surf.get_rect(center=Back.squares[i][j].center)
                Back.screen.blit(text_surf, text_rect)

    # Рисуем нагреватели с индикатором группы
    for heater in Back.heaters:
        group_idx = heater.sensor_group % len(group_colors)
        # Треугольник-индикатор группы в левом верхнем углу
        pygame.draw.polygon(Back.screen, group_colors[group_idx], [
            (heater.X * c.SQUARE_SIZE + c.X_SCREEN_OFFSET + 2, 
             heater.Y * c.SQUARE_SIZE + c.Y_SCREEN_OFFSET + 2),
            (heater.X * c.SQUARE_SIZE + c.X_SCREEN_OFFSET + 10, 
             heater.Y * c.SQUARE_SIZE + c.Y_SCREEN_OFFSET + 2),
            (heater.X * c.SQUARE_SIZE + c.X_SCREEN_OFFSET + 2, 
             heater.Y * c.SQUARE_SIZE + c.Y_SCREEN_OFFSET + 10)
        ])
        # Буква "H" по центру
        draw_text("H", SQUARE_FONT, Back.squares[heater.Y][heater.X], c.MAIN_TEXT_COLOR)
    
    # Рисуем кондиционеры с цветом группы и буквой "C"
    for ac in Back.air_conditioners:
        group_idx = ac.sensor_group % len(group_colors)
        # Заливаем ячейку цветом группы для визуального выделения
        group_highlight = pygame.Surface((c.SQUARE_SIZE, c.SQUARE_SIZE), pygame.SRCALPHA)
        group_highlight.fill((*group_colors[group_idx], 64))  # 25% прозрачность
        Back.screen.blit(group_highlight, 
            (ac.X * c.SQUARE_SIZE + c.X_SCREEN_OFFSET, 
             ac.Y * c.SQUARE_SIZE + c.Y_SCREEN_OFFSET))
        # Буква "C" по центру (жирная и контрастная)
        draw_text("C", SQUARE_FONT, Back.squares[ac.Y][ac.X], (0, 0, 100))
        # Маленький индикатор режима в правом нижнем углу:
        # синий квадратик = охлаждение, красный = нагрев
        ac_temp = Back.temperatures[-1][ac.Y][ac.X]
        mode_color = (0, 0, 200) if ac_temp < 20 else (200, 0, 0)
        pygame.draw.rect(Back.screen, mode_color,
            (ac.X * c.SQUARE_SIZE + c.X_SCREEN_OFFSET + c.SQUARE_SIZE - 6,
             ac.Y * c.SQUARE_SIZE + c.Y_SCREEN_OFFSET + c.SQUARE_SIZE - 6,
             4, 4))
    
    # Рисуем сенсоры
    for group_idx, group in enumerate(Back.sensors):
        color = group_colors[group_idx % len(group_colors)]
        for sensor in group:
            center_x = sensor.X * c.SQUARE_SIZE + c.X_SCREEN_OFFSET + c.SQUARE_SIZE // 2
            center_y = sensor.Y * c.SQUARE_SIZE + c.Y_SCREEN_OFFSET + c.SQUARE_SIZE // 2
            
            # Полупрозрачный круг-фон группы
            bg_circle = pygame.Surface((c.SQUARE_SIZE * 2 // 3, c.SQUARE_SIZE * 2 // 3), pygame.SRCALPHA)
            pygame.draw.circle(bg_circle, (*color, 80), 
                (c.SQUARE_SIZE // 3, c.SQUARE_SIZE // 3), c.SQUARE_SIZE // 3)
            Back.screen.blit(bg_circle, 
                (sensor.X * c.SQUARE_SIZE + c.X_SCREEN_OFFSET + c.SQUARE_SIZE // 6,
                 sensor.Y * c.SQUARE_SIZE + c.Y_SCREEN_OFFSET + c.SQUARE_SIZE // 6))
            
            # Основной круг сенсора
            pygame.draw.circle(Back.screen, color, (center_x, center_y), c.SQUARE_SIZE // 4)
            
            # Температура белым шрифтом
            temp_rounded = round(sensor.curtemp)
            temp_surf = SQUARE_FONT.render(f"{temp_rounded}", True, (255, 255, 255))
            temp_rect = temp_surf.get_rect(center=(center_x, center_y))
            Back.screen.blit(temp_surf, temp_rect)
            
            # Номер группы в углу
            group_num = pygame.font.Font(None, 10).render(str(group_idx + 1), True, (255, 255, 255))
            Back.screen.blit(group_num, (
                sensor.X * c.SQUARE_SIZE + c.X_SCREEN_OFFSET + 2,
                sensor.Y * c.SQUARE_SIZE + c.Y_SCREEN_OFFSET + 2
            ))
    
    # Рисуем температуры только для пола (не для источников)
    for i in range(c.ROOM_SIZE_Y):
        for j in range(c.ROOM_SIZE_X):
            if Back.colors[i][j] == c.FLOOR_COLOR:
                temp_int = int(round(Back.temperatures[-1][i][j]))
                temp_int = max(-60, min(120, temp_int))
                text_surf = _TEMP_TEXT_CACHE[temp_int]
                text_rect = text_surf.get_rect(center=Back.squares[i][j].center)
                Back.screen.blit(text_surf, text_rect)


    #def draw_field():
    #    group_colors = [
    #        (255, 0, 0),      # Красный - группа 1
    #        (255, 255, 0),    # Жёлтый - группа 2
    #        (255, 165, 0),    # Оранжевый - группа 3
    #        (128, 0, 128),    # Фиолетовый - группа 4
    #        (0, 0, 255)       # Синий - группа 5
    #    ]
    #    
    #    for i in range(c.ROOM_SIZE_Y):
    #        for j in range(c.ROOM_SIZE_X):
    #            pygame.draw.rect(Back.screen, Back.colors[i][j], Back.squares[i][j])
    #
    #            if Back.colors[i][j] == c.HEATER_COLOR:
    #                text_surf = _H_TEXT_SURF
    #            elif Back.colors[i][j] == c.AC_COLOR:
    #                text_surf = SQUARE_FONT.render('C',True,(0,0,0))
    #            else:
    #                temp_int = int(round(Back.temperatures[-1][i][j]))
    #                temp_int = max(-60,min(120,temp_int))
    #                text_surf = _TEMP_TEXT_CACHE[temp_int]
    #
    #                text_rect = text_surf.get_rect(center=Back.squares[i][j].center)
    #                Back.screen.blit(text_surf,text_rect)
    #    
    #
    #    for i in range(c.ROOM_SIZE_Y):
    #        for j in range(c.ROOM_SIZE_X):    
    #            pygame.draw.rect(Back.screen, Back.colors[i][j], Back.squares[i][j])
    #            if Back.colors[i][j] != c.HEATER_COLOR:
    #                draw_text(f"{int(Back.temperatures[-1][i][j])}", SQUARE_FONT, Back.squares[i][j], c.MAIN_TEXT_COLOR)
    #            else:
    #                draw_text("H", SQUARE_FONT, Back.squares[i][j], c.MAIN_TEXT_COLOR)
    #            
    #    for heater in Back.heaters:
    #        group_idx = heater.sensor_group % len(group_colors)
    #        # Маленький треугольник-индикатор группы в углу нагревателя
    #        pygame.draw.polygon(Back.screen, group_colors[group_idx], [
    #            (heater.X * c.SQUARE_SIZE + c.X_SCREEN_OFFSET + 2, 
    #             heater.Y * c.SQUARE_SIZE + c.Y_SCREEN_OFFSET + 2),
    #            (heater.X * c.SQUARE_SIZE + c.X_SCREEN_OFFSET + 10, 
    #             heater.Y * c.SQUARE_SIZE + c.Y_SCREEN_OFFSET + 2),
    #            (heater.X * c.SQUARE_SIZE + c.X_SCREEN_OFFSET + 2, 
    #             heater.Y * c.SQUARE_SIZE + c.Y_SCREEN_OFFSET + 10)
    #        ])        
    #    for ac in Back.air_conditioners:
    #        group_idx = ac.sensor_group % len(group_colors)
    #        color = (100, 180, 255)
    #        points = [
    #            (ac.X * c.SQUARE_SIZE + c.X_SCREEN_OFFSET + c.SQUARE_SIZE - 11, 
    #             ac.Y * c.SQUARE_SIZE + c.Y_SCREEN_OFFSET + 3),
    #            (ac.X * c.SQUARE_SIZE + c.X_SCREEN_OFFSET + c.SQUARE_SIZE - 3, 
    #             ac.Y * c.SQUARE_SIZE + c.Y_SCREEN_OFFSET + 3),
    #            (ac.X * c.SQUARE_SIZE + c.X_SCREEN_OFFSET + c.SQUARE_SIZE - 3, 
    #             ac.Y * c.SQUARE_SIZE + c.Y_SCREEN_OFFSET + 11)
    #        ]
    #        pygame.draw.polygon(Back.screen, color, points)
    #    for group_idx, group in enumerate(Back.sensors):
    #        color = group_colors[group_idx % len(group_colors)]
    #        for sensor in group:
    #            center_x = sensor.X * c.SQUARE_SIZE + c.X_SCREEN_OFFSET + c.SQUARE_SIZE // 2
    #            center_y = sensor.Y * c.SQUARE_SIZE + c.Y_SCREEN_OFFSET + c.SQUARE_SIZE // 2
    #            # Большой полупрозрачный круг для фона группы
    #            pygame.draw.circle(Back.screen, (*group_colors[group_idx % len(group_colors)], 128),
    #                (center_x,
    #                 center_y),
    #                c.SQUARE_SIZE // 3, width=1)
    #            
    #            # Маленький круг-индикатор с температурой
    #            pygame.draw.circle(Back.screen, group_colors[group_idx % len(group_colors)],
    #                (center_x,
    #                 center_y),
    #                c.SQUARE_SIZE // 4)
    #            
    #            temp_rounded = round(sensor.curtemp * 2) / 2
    #            cache_key = (round(temp_rounded, 1), group_idx)
    #            if cache_key not in _SENSOR_TEXT_CACHE:
    #                _SENSOR_TEXT_CACHE[cache_key] = SQUARE_FONT.render(f"{temp_rounded:.1f}", True, (255, 255, 255))
    #            temp_surf = _SENSOR_TEXT_CACHE[cache_key]
    #            # Температура белым шрифтом
    #            #temp_text = f"{sensor.curtemp:.0f}"
    #            #text_surf = SQUARE_FONT.render(temp_text, True, (255, 255, 255))
    #            #text_rect = text_surf.get_rect(center=(
    #            #    sensor.X * c.SQUARE_SIZE + c.X_SCREEN_OFFSET + c.SQUARE_SIZE // 2,
    #            #    sensor.Y * c.SQUARE_SIZE + c.Y_SCREEN_OFFSET + c.SQUARE_SIZE // 2
    #            #))
    #            temp_rect = temp_surf.get_rect(center=(center_x, center_y))
    #            Back.screen.blit(text_surf, text_rect)
    #            
    #            # Номер группы в углу сенсора
    #            #group_text = str(group_idx + 1)
    #            #group_surf = pygame.font.Font(None, 10).render(group_text, True, (255, 255, 255))
    #            group_num = pygame.font.Font(None, 10).render(str(group_idx + 1), True, (255, 255, 255))
    #            Back.screen.blit(group_num, (
    #                sensor.X * c.SQUARE_SIZE + c.X_SCREEN_OFFSET + 2,
    #                sensor.Y * c.SQUARE_SIZE + c.Y_SCREEN_OFFSET + 2
    #            ))
    #                    
    #            #for group_idx, group in enumerate(Back.sensors):
    #            #    for sensor in group:
    #            #        # Цвет сенсора зависит от группы для визуального разделения
    #            #        group_colors = [(255, 0, 0), (255, 255, 0), (255, 165, 0), (128, 0, 128), (0, 0, 255)]
    #            #        sensor_color = group_colors[group_idx % len(group_colors)]
    #            #        
    #            #        # Основной круг сенсора
    #            #        pygame.draw.circle(Back.screen, sensor_color,
    #            #            (sensor.X * c.SQUARE_SIZE + c.X_SCREEN_OFFSET + c.SQUARE_SIZE // 2,
    #            #             sensor.Y * c.SQUARE_SIZE + c.Y_SCREEN_OFFSET + c.SQUARE_SIZE // 2),
    #            #            c.SQUARE_SIZE // 3)
    #            #        
    #            #        # Температура внутри круга белым цветом
    #            #        temp_text = f"{sensor.curtemp:.1f}"
    #            #        text_surf = SQUARE_FONT.render(temp_text, True, (255, 255, 255))
    #            #        text_rect = text_surf.get_rect(center=(
    #            #            sensor.X * c.SQUARE_SIZE + c.X_SCREEN_OFFSET + c.SQUARE_SIZE // 2,
    #            #            sensor.Y * c.SQUARE_SIZE + c.Y_SCREEN_OFFSET + c.SQUARE_SIZE // 2
    #            #        ))
    #            #        Back.screen.blit(text_surf, text_rect)
    #        # for group in Back.sensors:
    #        #     for sensor in group:
    #        #         pygame.draw.circle(Back.screen, c.SENSOR_COLOR,
    #        #             (sensor.X * c.SQUARE_SIZE + c.X_SCREEN_OFFSET + c.SQUARE_SIZE // 2,
    #        #              sensor.Y * c.SQUARE_SIZE + c.Y_SCREEN_OFFSET + c.SQUARE_SIZE // 2),
    #        #             c.SQUARE_SIZE // 2)

def draw_text(text, font, rect, color):
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=rect.center)
    Back.screen.blit(text_surface, text_rect)

def draw_rectangle(off, size, color):
    rect = pygame.Rect(off[0], off[1], size[0], size[1])
    pygame.draw.rect(Back.screen, color, rect)
    return rect  

def draw_label(text, font, off, size, colortext, color):
    rect = draw_rectangle(off, size, color)
    text_surface = font.render(text, True, colortext)
    text_rect = text_surface.get_rect(center=rect.center)
    Back.screen.blit(text_surface, text_rect)

def draw_plot(x_offset, y_offset, desired_temp):
    if not Back.sensors_average_history:
        return
    
    x = list(range(len(Back.sensors_average_history)))
    y_groups = []
    
    for j in range(len(Back.sensors_average_history[0])):
        y_groups.append([entry[j] for entry in Back.sensors_average_history if len(entry) > j])
    
    fig, ax = plt.subplots(figsize=(4, 3))
    colors_plot = ['red', 'yellow', 'orange', 'purple', 'blue']
    
    for j in range(min(len(Back.sensors_average), len(colors_plot))):
        if y_groups[j]:
            ax.plot(x[:len(y_groups[j])], y_groups[j], c=colors_plot[j], label=f"Group {j+1}")
    
    ax.axhline(y=desired_temp, color='green', linestyle='dotted', label='Target')
    ax.set_title("Sensors temperature history")
    ax.set_xlabel("Steps")
    ax.set_ylabel("Temperature (°C)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    canvas = FigureCanvas(fig)
    canvas.draw()
    
    buf = BytesIO()
    canvas.print_figure(buf, format='png', dpi=100)
    buf.seek(0)
    
    plot_image = pygame.image.load(buf)
    Back.screen.blit(plot_image, (x_offset, y_offset))
    plt.close(fig)  # Critical: free matplotlib resources
