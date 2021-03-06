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
SMALL_SPEED = 0.2
BIG_SPEED = 26

NEXT_TILE_OFFSET = 0.5
ANGLE_DELTA = pi / 20
PROJECTILE_THROW_DISTANCE = 2000
OIL_SPILL_DISTANCE = 2000

DEFAULT_ST = 0
ACCELERATION_ST = 1
REVERSE_ST = 2

TICKS_WITHOUT_MOVE = {
    DEFAULT_ST: 10,
    ACCELERATION_ST: 100
}
MAX_REAR_MOVE_TICKS = 110

RECURSION_DEPTH = 10

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

    tmp_route = []
    route = []

    def steps_to_point(self, ux, uy, px, py, _visited_tiles=set()):
        # print(len(_visited_tiles))
        if ux == px and uy == py or len(_visited_tiles) > RECURSION_DEPTH:
            # print('++++++++++++++++++++++++++++++++++++')
            return []
        neighbours = [(0, 0), (0, 0), (0, 0), (0, 0)]
        lx = px - ux
        ly = py - uy
        if abs(lx) >= abs(ly):
            neighbours[0], neighbours[3] = (LEFT, RIGHT) if lx < 0 else (RIGHT, LEFT)
            neighbours[1], neighbours[2] = (UP, DOWN) if ly < 0 else (DOWN, UP)
        else:
            neighbours[0], neighbours[3] = (UP, DOWN) if ly < 0 else (DOWN, UP)
            neighbours[1], neighbours[2] = (LEFT, RIGHT) if lx < 0 else (RIGHT, LEFT)
        paths = []
        for neighbour in neighbours:
            x = ux + neighbour[0]
            y = uy + neighbour[1]
            if (x, y) in _visited_tiles:
                continue
            if neighbour in DEAD_ENDS.get(self.grid[ux][uy], ()):
                continue
            if not (0 <= x < self.grid_width and 0 <= y < self.grid_height) or \
                    self.grid[x][y] == TileType.EMPTY:
                continue
            if self.grid[x][y] == TileType.UNKNOWN:
                paths.append([])
                continue
            path = self.steps_to_point(x, y, px, py, _visited_tiles | {(ux, uy)})
            if isinstance(path, list):
                paths.append([(x, y)] + path)

        if len(paths) == 0:
            return None
        elif len(paths) == 1:
            return paths[0]
        else:
            path = min(paths, key=lambda el: len(el))
            # paths = filter(lambda el: len(el) == len(path), paths)
            paths = [el for el in paths if len(el) == len(path)]
            if len(paths) == 1:
                return paths[0]
            else:
                return min(paths, key=lambda el: hypot(px-el[-1][0], py-el[-1][1]))

    @staticmethod
    def check_other_cars(_world, _me, _distance, _angle):
        for car in _world.cars:
            if car.id != _me.id and \
                    _me.get_distance_to_unit(car) <= _distance and \
                    _angle - ANGLE_DELTA < abs(_me.get_angle_to_unit(car)) < _angle + ANGLE_DELTA:
                return True
        return False

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

        print('----------', world.tick)
        # if world.tick == 0:
        #     for j in range(self.grid_height):
        #         print(', '.join([str(self.grid[i][j]).rjust(2, '0') for i in range(self.grid_width)]))
        # print(self.pts)
        # print(me.next_waypoint_x, me.next_waypoint_y)
        # print(self.ticks_without_move, self.rear_move_ticks_remain)

        # путь до следующего way point
        # if self.route:
        #     steps = self.route[len(self.tmp_route):]
        # else:
        #     if len(self.tmp_route) > 1 and self.tmp_route[0] == (curr_tile_x, curr_tile_y):
        #         self.route = list(self.tmp_route)
        #         self.tmp_route.clear()

        steps = self.steps_to_point(curr_tile_x, curr_tile_y, me.next_waypoint_x, me.next_waypoint_y)

        # if not self.tmp_route or self.tmp_route[-1] != (curr_tile_x, curr_tile_y):
        #     self.tmp_route.append((curr_tile_x, curr_tile_y))
        # print(steps, len(steps))
        straight_moves = 1
        if steps:
            next_tile_x, next_tile_y = steps[0]

            direction = (next_tile_x - curr_tile_x, next_tile_y - curr_tile_y)
            for i in range(1, len(steps)):
                if direction == (steps[i][0] - steps[i-1][0], steps[i][1] - steps[i-1][1]):
                    straight_moves += 1
                    next_tile_x, next_tile_y = steps[i]
                else:
                    break
        else:
            next_tile_x, next_tile_y = me.next_waypoint_x, me.next_waypoint_y

        next_tile_type = world.tiles_x_y[next_tile_x][next_tile_y]
        # print(straight_moves)

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
                self.ticks_without_move = 0
                self.state = REVERSE_ST
                self.rear_move_ticks_remain = MAX_REAR_MOVE_TICKS

            if self.state == ACCELERATION_ST:
                if abs(curr_speed_module) >= SMALL_SPEED:
                    self.state = DEFAULT_ST

            # print(curr_tile_x, curr_tile_y)
            # print(next_tile_x, next_tile_y, next_tile_type)
            # print(me.next_waypoint_x, me.next_waypoint_y, next_tile_type)
            # print(self.grid_width, self.grid_height)
            # print(steps)
            # print(me.speed_x, me.speed_y)
            # print(me.x, me.y)
            # print(cars_is_close)
            # print(curr_speed_module)
            # print(curr_speed_module > BIG_SPEED and straight_moves == 1)

            # # FIXME есть ли машины рядом
            # cars_is_close = False
            # for car in world.cars:
            #     if car.id != me.id and me.get_distance_to_unit(car) <= me.width * 1.2:
            #         cars_is_close = True
            #
            # if cars_is_close and any((
            #     all((
            #         next_tile_type == TileType.VERTICAL,
            #         abs(me.speed_x) < SMALL_SPEED,
            #         # abs(me.speed_y) > MEDIUM_SPEED,
            #     )),
            #     all((
            #         next_tile_type == TileType.HORIZONTAL,
            #         abs(me.speed_y) < SMALL_SPEED,
            #         # abs(me.speed_x) > MEDIUM_SPEED,
            #     ))
            # )):
            #     return self.move_forward_and_return(move)
            # # FIXME ends

            next_x = (next_tile_x + NEXT_TILE_OFFSET) * game.track_tile_size
            next_y = (next_tile_y + NEXT_TILE_OFFSET) * game.track_tile_size

            corner_tile_offset = 0.32 * game.track_tile_size
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
            elif next_tile_type == TileType.BOTTOM_HEADED_T and straight_moves == 1:
                next_y += corner_tile_offset
            elif next_tile_type == TileType.LEFT_HEADED_T and straight_moves == 1:
                next_x -= corner_tile_offset
            elif next_tile_type == TileType.RIGHT_HEADED_T and straight_moves == 1:
                next_x += corner_tile_offset
            elif next_tile_type == TileType.TOP_HEADED_T and straight_moves == 1:
                next_y -= corner_tile_offset

            angle_to_next_tile = me.get_angle_to(next_x, next_y)
            move.wheel_turn = angle_to_next_tile * 32.0 / pi

            if curr_speed_module ** 2 * abs(angle_to_next_tile) > 3 ** 2 * pi or \
                    curr_speed_module > BIG_SPEED and straight_moves == 1:
                move.engine_power = 0.7
                move.brake = True
            else:
                move.engine_power = 1.0

            # используем инвентарь
            if self.check_other_cars(world, me, PROJECTILE_THROW_DISTANCE, 0):
                move.throw_projectile = True
            if self.check_other_cars(world, me, OIL_SPILL_DISTANCE, pi) and curr_tile_type in TURN_TILES:
                move.spill_oil = True
            if straight_moves > 3 and angle_to_next_tile < ANGLE_DELTA:
                move.use_nitro = True

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
