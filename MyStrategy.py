from math import hypot, pi

from model.Car import Car
from model.Game import Game
from model.Move import Move
from model.World import World
from model.TileType import TileType

TURN_TILES = (TileType.LEFT_TOP_CORNER, TileType.RIGHT_TOP_CORNER, TileType.LEFT_BOTTOM_CORNER,
              TileType.RIGHT_BOTTOM_CORNER, TileType.LEFT_HEADED_T, TileType.RIGHT_HEADED_T,
              TileType.TOP_HEADED_T, TileType.BOTTOM_HEADED_T)

TURN_SPEED = 10
SMALL_SPEED = 0.1
MEDIUM_SPEED = 4


NEXT_TILE_OFFSET = 0.5

DEFAULT_ST = 0
ACCELERATION_ST = 1
REVERSE_ST = 2

TICKS_WITHOUT_MOVE = {
    DEFAULT_ST: 10,
    ACCELERATION_ST: 100
}
MAX_REAR_MOVE_TICKS = 100
MAX_REAR_TICKS_TO_STOP = 20

LEFT = (-1, 0)
RIGHT = (1, 0)
UP = (0, -1)
DOWN = (0, 1)
STEP_OPTIONS = (LEFT, RIGHT, UP, DOWN)
DEAD_ENDS = {
    TileType.VERTICAL: (LEFT, RIGHT, ),
    TileType.HORIZONTAL: (UP, DOWN, ),
    TileType.LEFT_TOP_CORNER: (LEFT, UP, ),
    TileType.RIGHT_TOP_CORNER: (RIGHT, UP, ),
    TileType.LEFT_BOTTOM_CORNER: (LEFT, DOWN, ),
    TileType.RIGHT_BOTTOM_CORNER: (RIGHT, DOWN, ),
    TileType.LEFT_HEADED_T: (RIGHT, ),
    TileType.RIGHT_HEADED_T: (LEFT, ),
    TileType.TOP_HEADED_T: (DOWN, ),
    TileType.BOTTOM_HEADED_T: (UP, ),
}


class MyStrategy:
    rear_move_ticks_remain = 0
    ticks_without_move = 0
    grid = [[]]
    grid_width = 0
    grid_height = 0
    state = ACCELERATION_ST
    _visited_tiles = []

    def steps_to_point(self, ux, uy, px, py):
        # print('  ', ux, uy, self.grid[ux][uy])
        if ux == px and uy == py:
            return []
        self._visited_tiles.append((ux, uy))
        neighbours = [(0, 0), (0, 0), (0, 0), (0, 0)]
        lx = px - ux
        ly = py - uy
        if abs(lx) >= abs(ly):
            neighbours[0], neighbours[3] = (LEFT, RIGHT) if lx < 0 else (RIGHT, LEFT)
            neighbours[1], neighbours[2] = (UP, DOWN) if ly < 0 else (DOWN, UP)
        else:
            neighbours[0], neighbours[3] = (UP, DOWN) if ly < 0 else (DOWN, UP)
            neighbours[1], neighbours[2] = (LEFT, RIGHT) if lx < 0 else (RIGHT, LEFT)
        for neighbour in neighbours:
            # print('--', neighbour[0], neighbour[1])
            x = ux + neighbour[0]
            y = uy + neighbour[1]
            if (x, y) in self._visited_tiles:
                continue
            if neighbour in DEAD_ENDS.get(self.grid[ux][uy], ()):
                continue
            if not (0 <= x < self.grid_width and 0 <= y < self.grid_height) or \
                    self.grid[x][y] == TileType.EMPTY:
                continue
            if self.grid[x][y] == TileType.UNKNOWN:
                return []
            path = self.steps_to_point(x, y, px, py)
            if isinstance(path, list):
                return [(x, y)] + path
        self._visited_tiles.pop()
        return None

    @staticmethod
    def move_forward_and_return(move):
        move.engine_power = 1.0
        return

    def move(self, me: Car, world: World, game: Game, move: Move):

        self.grid = world.tiles_x_y
        self.grid_width = len(world.tiles_x_y)
        self.grid_height = len(world.tiles_x_y[0])

        curr_tile_x = int(
            me.x // game.track_tile_size + (-1 if me.x % game.track_tile_size == 0 else 0))
        curr_tile_y = int(
            me.y // game.track_tile_size + (-1 if me.y % game.track_tile_size == 0 else 0))
        curr_tile_type = world.tiles_x_y[curr_tile_x][curr_tile_y]
        curr_speed_module = hypot(me.speed_x, me.speed_y)

        # print('----------', world.tick)
        # print(self.ticks_without_move, self.rear_move_ticks_remain)
        # if world.tick == 0:
        #     for j in range(self.grid_height):
        #         print(', '.join([str(self.grid[i][j]).rjust(2, '0') for i in range(self.grid_width)]))
        # print(me.next_waypoint_x, me.next_waypoint_y)

        # путь до следующего way point
        self._visited_tiles.clear()
        steps = self.steps_to_point(curr_tile_x, curr_tile_y, me.next_waypoint_x, me.next_waypoint_y)
        if not steps:
            return self.move_forward_and_return(move)
        else:
            next_tile_x, next_tile_y = steps.pop(0)
        next_tile_type = world.tiles_x_y[next_tile_x][next_tile_y]

        if self.state == DEFAULT_ST or self.state == ACCELERATION_ST:
            # до начала движения
            if world.tick < game.initial_freeze_duration_ticks:
                return self.move_forward_and_return(move)

            # счётчик простоя перед задним ходом
            if abs(curr_speed_module) < SMALL_SPEED:
                self.ticks_without_move += 1
            else:
                self.ticks_without_move = 0
            if self.ticks_without_move > TICKS_WITHOUT_MOVE.get(self.state):
                # print(self.state, curr_speed_module)
                self.ticks_without_move = 0
                self.state = REVERSE_ST
                self.rear_move_ticks_remain = MAX_REAR_MOVE_TICKS

            if self.state == ACCELERATION_ST:
                if abs(curr_speed_module) >= SMALL_SPEED:
                    self.state = DEFAULT_ST
                    # self.ticks_without_move = 0

            # print(curr_tile_x, curr_tile_y)
            # print(next_tile_x, next_tile_y, next_tile_type)
            # print(me.next_waypoint_x, me.next_waypoint_y, next_tile_type)
            # print(self.grid_width, self.grid_height)
            # print(steps)


            # print(me.speed_x, me.speed_y)
            # print(me.x, me.y)
            # print(cars_is_close)

            # move.engine_power = .8
            # move.use_nitro = True

            # есть ли машины рядом
            cars_is_close = False
            for car in world.cars:
                if car.id != me.id and me.get_distance_to_unit(car) <= me.width * 1.2:
                    cars_is_close = True

            if cars_is_close and any((
                all((
                    next_tile_type == TileType.VERTICAL,
                    abs(me.speed_x) < SMALL_SPEED,
                    # abs(me.speed_y) > MEDIUM_SPEED,
                )),
                all((
                    next_tile_type == TileType.HORIZONTAL,
                    abs(me.speed_y) < SMALL_SPEED,
                    # abs(me.speed_x) > MEDIUM_SPEED,
                ))
            )):
                return self.move_forward_and_return(move)

            next_x = (next_tile_x + NEXT_TILE_OFFSET) * game.track_tile_size
            next_y = (next_tile_y + NEXT_TILE_OFFSET) * game.track_tile_size

            corner_tile_offset = 0.25 * game.track_tile_size
            if next_tile_type == TileType.LEFT_TOP_CORNER:
                next_x += corner_tile_offset
                next_y += corner_tile_offset
            elif next_tile_type == TileType.RIGHT_TOP_CORNER:
                next_x -= corner_tile_offset
                next_y += corner_tile_offset
            elif next_tile_type == TileType.LEFT_BOTTOM_CORNER:
                next_x += corner_tile_offset
                next_y -= corner_tile_offset
            elif next_tile_type == TileType.RIGHT_BOTTOM_CORNER:
                next_x -= corner_tile_offset
                next_y -= corner_tile_offset

            angle_to_waypoint = me.get_angle_to(next_x, next_y)
            move.wheel_turn = angle_to_waypoint * 32.0 / pi

            if curr_speed_module ** 2 * abs(angle_to_waypoint) > 3 ** 2 * pi:
                move.brake = True

            move.engine_power = 1.0

        # задний ход
        elif self.state == REVERSE_ST:
            if self.rear_move_ticks_remain > 0:
                self.rear_move_ticks_remain -= 1
                next_x = (next_tile_x + NEXT_TILE_OFFSET) * game.track_tile_size
                next_y = (next_tile_y + NEXT_TILE_OFFSET) * game.track_tile_size
                move.wheel_turn = -100 if me.get_angle_to(next_x, next_y) * 32.0 / pi > 0 else 100
                move.engine_power = -1.0
                return
            else:
                if curr_speed_module > SMALL_SPEED:
                    move.brake = True
                    move.engine_power = 1
                    return
                else:
                    self.state = ACCELERATION_ST

