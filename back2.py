import consts as c
import pygame

# BASIC STRUCTS (без изменений)
class HasTemp:
    def __init__(self, row, col, curtemp=0, settemp=0):
        self.curtemp = curtemp
        self.settemp = settemp
        self.X = col
        self.Y = row

class Heater(HasTemp):
    def __init__(self, row, col, curtemp=100, settemp=100, sensor_group=0):
        super().__init__(row, col, curtemp=curtemp, settemp=settemp)
        self.sensor_group = sensor_group

class Window(HasTemp):
    def __init__(self, row, col, curtemp=0, settemp=0, sensor_group=0):
        super().__init__(row, col, curtemp=curtemp, settemp=settemp)
        self.sensor_group = sensor_group
        self.open = False

class Door(HasTemp):
    def __init__(self, row, col, curtemp=0, settemp=0, sensor_group=0):
        super().__init__(row, col, curtemp=curtemp, settemp=settemp)
        self.sensor_group = sensor_group
        self.open = False
class AirConditioner(HasTemp):
    def __init__(self,row,col,sensor_group=0):
        super().__init__(row,col,curtemp=0,settemp=0)
        self.sensor_group = sensor_group
class Sensor(HasTemp):
    def __init__(self, row, col):
        super().__init__(row, col)

# Precomputed temperature palette for fast color mapping (-60°C to 120°C)
_TEMP_PALETTE = []
for temp in range(-60, 121):
    if temp <= -30:
        color = (0, 0, 255)
    elif temp <= 0:
        t = (temp + 30) / 30
        color = (0, int(255 * t), int(255 * (1 - t)))
    elif temp <= 30:
        t = temp / 30
        color = (int(255 * t), 255, 0)
    elif temp <= 60:
        t = (temp - 30) / 30
        color = (255, int(255 * (1 - t)), 0)
    else:
        color = (255, 0, 0)
    _TEMP_PALETTE.append(color)

def temperature_to_color(temp):
    idx = int(round(temp)) + 60  # -60°C -> index 0
    if idx < 0:
        return _TEMP_PALETTE[0]
    if idx >= len(_TEMP_PALETTE):
        return _TEMP_PALETTE[-1]
    return _TEMP_PALETTE[idx]

# Neighbor cache (rebuild when layout changes)
_neighbor_cache = None
_layout_dirty = True

def _rebuild_neighbor_cache():
    global _neighbor_cache, _layout_dirty, _heater_group_map,_ac_group_map
    _neighbor_cache = [[[] for _ in range(c.ROOM_SIZE_X)] for _ in range(c.ROOM_SIZE_Y)]
    _heater_group_map = [[-1 for _ in range(c.ROOM_SIZE_X)] for _ in range(c.ROOM_SIZE_Y)]
    _ac_group_map = [[-1 for _ in range(c.ROOM_SIZE_X)] for _ in range(c.ROOM_SIZE_Y)]

    for heater in heaters:
        _heater_group_map[heater.Y][heater.X] = heater.sensor_group
    for ac in air_conditioners:
        _ac_group_map[ac.Y][ac.X] = ac.sensor_group
    
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for i in range(c.ROOM_SIZE_Y):
        for j in range(c.ROOM_SIZE_X):
            neighbors = []
            for di, dj in directions:
                ni, nj = i + di, j + dj
                if 0 <= ni < c.ROOM_SIZE_Y and 0 <= nj < c.ROOM_SIZE_X:
                    cell_color = colors[ni][nj]
                    if cell_color == c.WALLS_COLOR:
                        k = K_wall
                    elif cell_color == c.WINDOW_COLOR:
                        k = K_window
                    elif cell_color in (c.HEATER_COLOR,c.AC_COLOR):
                        k = K_air  # Heater influence handled separately via signal
                    else:
                        k = K_air
                    neighbors.append((ni, nj, k))
            _neighbor_cache[i][j] = neighbors
    
    _layout_dirty = False

# Global state
K_window, K_door, K_wall, K_air = 0.02, 0.01, 0.008, 0.1
K_signal = 0.001  # Heater influence coefficient

regulationType = 'p'  # r, p, pi, pid
outdoor_temp = 20
desired_temp = 17
setting_obj = 'heater'
sensor_group = 0
show_plot = False
cooling_mode = False

sensors = [[] for _ in range(c.SENSORS_GROUPS_COUNT)]
heaters = []
air_conditioners = []
_group_signals = [0.0] * c.SENSORS_GROUPS_COUNT
_ac_group_map = [[-1 for _ in range(c.ROOM_SIZE_X)] for _ in range(c.ROOM_SIZE_Y)]
_heater_group_map = [[-1 for _ in range(c.ROOM_SIZE_X)] for _ in range(c.ROOM_SIZE_Y)]
windows = []
doors = []

sensors_average = []
sensors_average_history = []

# Single temperature grid (no memory leak!)
_current_temperatures = [[20.0 for _ in range(c.ROOM_SIZE_X)] for _ in range(c.ROOM_SIZE_Y)]
# Compatibility wrapper: temperatures[-1] still works
temperatures = [_current_temperatures]

# Initialize room layout
colors = [[(200, 200, 200) for _ in range(c.ROOM_SIZE_X)] for _ in range(c.ROOM_SIZE_Y)]
colors = [[c.OUTDOOR_COLOR for _ in range(c.ROOM_SIZE_X)] for _ in range(c.ROOM_SIZE_Y)]
for i in range(1, c.ROOM_SIZE_Y - 1):
    for j in range(1, c.ROOM_SIZE_X - 1):
        colors[i][j] = c.WALLS_COLOR
for i in range(2, c.ROOM_SIZE_Y - 2):
    for j in range(2, c.ROOM_SIZE_X - 2):
        colors[i][j] = c.FLOOR_COLOR

dont_change_mask = [
    [colors[i][j] not in (c.OUTDOOR_COLOR, c.WALLS_COLOR) for j in range(c.ROOM_SIZE_X)]
    for i in range(c.ROOM_SIZE_Y)
]
dont_change_temp = [
    [colors[i][j] != c.OUTDOOR_COLOR for j in range(c.ROOM_SIZE_X)]
    for i in range(c.ROOM_SIZE_Y)
]

# Precompute neighbors after initialization
_rebuild_neighbor_cache()

# Pygame setup
screen = pygame.display.set_mode((c.WIDTH, c.HEIGHT))
clock = pygame.time.Clock()

# UI elements
squares = [
    [
        pygame.Rect(x * c.SQUARE_SIZE + c.X_SCREEN_OFFSET,
                    y * c.SQUARE_SIZE + c.Y_SCREEN_OFFSET,
                    c.SQUARE_SIZE,
                    c.SQUARE_SIZE)
        for x in range(c.ROOM_SIZE_X)
    ]
    for y in range(c.ROOM_SIZE_Y)
]

# Functions
def change_color(row, col, color):
    colors[row][col] = color

def set_object(pos, setting_obj):
    global _layout_dirty
    i, j = pos
    match setting_obj:
        case 'heater':
            set_heater(i, j)
        case 'ac':
            set_air_conditioner(i,j)
        case 'wall':
            set_wall(i, j)
        case 'floor':
            set_floor(i, j)
        case 'door':
            set_door(i, j)
        case 'sensor':
            set_sensor(i, j)
        case 'window':
            set_window(i, j)
        case 'outdoor':
            set_outdoor(i, j)
    _layout_dirty = True

def set_heater(row, col):
    global sensor_group, _layout_dirty
    change_color(row, col, c.HEATER_COLOR)
    _current_temperatures[row][col] = 100.0
    dont_change_mask[row][col] = False
    heaters.append(Heater(row, col, sensor_group=sensor_group))
    _layout_dirty = True

def set_air_conditioner(row, col):
    global sensor_group, _layout_dirty
    change_color(row,col,c.AC_COLOR)
    _current_temperatures[row][col] = 5.0
    dont_change_mask[row][col] = False
    air_conditioners.append(AirConditioner(row, col, sensor_group=sensor_group))
    _layout_dirty = True

def set_wall(row, col):
    global _layout_dirty
    change_color(row, col, c.WALLS_COLOR)
    dont_change_mask[row][col] = False
    _layout_dirty = True

def set_floor(row, col):
    global _layout_dirty
    change_color(row, col, c.FLOOR_COLOR)
    dont_change_mask[row][col] = True
    _layout_dirty = True

def set_door(row, col):
    global _layout_dirty
    change_color(row, col, c.DOOR_COLOR)
    dont_change_mask[row][col] = False
    _layout_dirty = True

def set_sensor(row, col):
    global sensor_group
    sensors[sensor_group].append(Sensor(row, col))

def set_window(row, col):
    global _layout_dirty
    change_color(row, col, c.WINDOW_COLOR)
    dont_change_mask[row][col] = False
    _layout_dirty = True

def set_outdoor(row, col):
    global _layout_dirty
    change_color(row, col, c.OUTDOOR_COLOR)
    dont_change_mask[row][col] = False
    dont_change_temp[row][col] = False
    _layout_dirty = True

def set_outdoor_temp(set_temperature):
    for i in range(c.ROOM_SIZE_Y):
        for j in range(c.ROOM_SIZE_X):
            if colors[i][j] == c.OUTDOOR_COLOR:
                _current_temperatures[i][j] = float(set_temperature)
def remove_object(row, col):
    """Удаляет любой объект (сенсор, нагреватель, кондиционер) из ячейки"""
    global _layout_dirty
    
    # Удаляем сенсоры
    for group in sensors:
        for idx, sensor in enumerate(group):
            if sensor.X == col and sensor.Y == row:
                group.pop(idx)
                return  # Сенсор не влияет на теплопередачу, кэш не перестраиваем
    
    # Удаляем нагреватель
    for idx, heater in enumerate(heaters):
        if heater.X == col and heater.Y == row:
            heaters.pop(idx)
            set_floor(row, col)  # Возвращаем ячейку в состояние "пол"
            _layout_dirty = True
            return
    
    # Удаляем кондиционер
    for idx, ac in enumerate(air_conditioners):
        if ac.X == col and ac.Y == row:
            air_conditioners.pop(idx)
            set_floor(row, col)  # Возвращаем ячейку в состояние "пол"
            _layout_dirty = True
            return
def change_sensor():
    for group in sensors:
        for sensor in group:
            sensor.curtemp = _current_temperatures[sensor.Y][sensor.X]
            sensor.settemp = desired_temp

def calc_average_sensors():
    global sensors_average, sensors_average_history
    sensors_average = []
    for group in sensors:
        if group:
            avg = sum(s.curtemp for s in group) / len(group)
            sensors_average.append(avg)
        else:
            sensors_average.append(0.0)
    sensors_average_history.append(sensors_average[:])
    if len(sensors_average_history) > 300:
        del sensors_average_history[:140]  # In-place deletion (no copy!)

# Regulation functions
def ReleRegulation(KR, desired_t, current_t):
    return KR * (1.0 if desired_t > current_t[-1] else 0.0)

def PRegulation(KP, desired_t, current_t):
    return KP * (desired_t - current_t[-1])

def PIRegulation(KP, KI, desired_t, current_t):
    si = 0.0
    start = max(0, len(current_t) - 10)
    for i in range(start, len(current_t)):
        si += desired_t - current_t[i]
    return KI * si + KP * (desired_t - current_t[-1])

def PIDRegulation(KP, KI, KD, desired_t, current_t):
    if len(current_t) >= 2:
        return (KP * (desired_t - current_t[-1]) + 
                KD * (current_t[-2] - current_t[-1]) + 
                KI * (desired_t * len(current_t) - sum(current_t)))
    else:
        return KI * (desired_t * len(current_t) - sum(current_t)) + KP * (desired_t - current_t[-1])




def recalculate_temp(regulationType, t_desired):
    global _current_temperatures, _layout_dirty, _neighbor_cache, _group_signals
    
    if _layout_dirty:
        _rebuild_neighbor_cache()
    
    # Вычисляем базовый сигнал для каждой группы
    base_signals = [0.0] * c.SENSORS_GROUPS_COUNT
    for group_idx in range(c.SENSORS_GROUPS_COUNT):
        if sensors[group_idx] and sensors_average_history:
            sensor_history = [
                entry[group_idx] 
                for entry in sensors_average_history 
                if len(entry) > group_idx
            ]
            if sensor_history:
                if regulationType == 'r':
                    signal = ReleRegulation(100, t_desired, sensor_history)
                elif regulationType == 'p':
                    signal = PRegulation(10, t_desired, sensor_history)
                elif regulationType == 'pi':
                    signal = PIRegulation(10, 1, t_desired, sensor_history)
                elif regulationType == 'pid':
                    pid_kp, pid_ki, pid_kd = 1.8, 0.12, 0.4
                    signal = PIDRegulation(pid_kp, pid_ki, pid_kd, t_desired, sensor_history)
                else:
                    signal = 0.0
                base_signals[group_idx] = signal
    
    # Разделяем сигналы: нагреватели работают на положительном сигнале, кондиционеры — на отрицательном
    heater_signals = [max(s, 0.0) for s in base_signals]
    ac_signals = [max(-s, 0.0) for s in base_signals]
    
    # Тепловой расчёт
    new_temperatures = [[0.0] * c.ROOM_SIZE_X for _ in range(c.ROOM_SIZE_Y)]
    old_temps = _current_temperatures
    
    for i in range(c.ROOM_SIZE_Y):
        for j in range(c.ROOM_SIZE_X):
            current_temp = old_temps[i][j]
            dtemp = 0.0
            
            # ИСТОЧНИКИ ТЕМПЕРАТУРЫ: не пересчитываем, сохраняем фиксированное значение
            if colors[i][j] in (c.HEATER_COLOR, c.AC_COLOR, c.OUTDOOR_COLOR):
                new_temperatures[i][j] = current_temp
                continue
            
            for ni, nj, k_base in _neighbor_cache[i][j]:
                neighbor_temp = old_temps[ni][nj]
                dt_local = neighbor_temp - current_temp
                
                if colors[ni][nj] == c.HEATER_COLOR:
                    heater_group = _heater_group_map[ni][nj]
                    if heater_group >= 0:
                        signal = heater_signals[heater_group]
                        dtemp += K_signal * signal * dt_local
                elif colors[ni][nj] == c.AC_COLOR:
                    ac_group = _ac_group_map[ni][nj]
                    if ac_group >= 0:
                        signal = ac_signals[ac_group]
                        dtemp += K_signal * signal * dt_local
                else:
                    dtemp += k_base * dt_local
            
            new_temperatures[i][j] = current_temp + dtemp
    
    _current_temperatures = new_temperatures
    temperatures[0] = new_temperatures
    
    # ВАЖНО: принудительно устанавливаем фиксированные температуры для источников
    for heater in heaters:
        _current_temperatures[heater.Y][heater.X] = 100.0
    for ac in air_conditioners:
        _current_temperatures[ac.Y][ac.X] = 5.0
    
    # Обновляем цвета для динамических ячеек
    for i in range(c.ROOM_SIZE_Y):
        for j in range(c.ROOM_SIZE_X):
            if dont_change_mask[i][j]:
                colors[i][j] = temperature_to_color(new_temperatures[i][j])



def recalc_temp():
    set_outdoor_temp(outdoor_temp)
    recalculate_temp(regulationType, desired_temp)

def recalc():
    change_sensor()
    calc_average_sensors()
    recalc_temp()
