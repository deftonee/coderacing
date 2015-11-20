from math import hypot, pi

from model.Car import Car
from model.Game import Game
from model.Move import Move
from model.World import World
from model.TileType import TileType

TURN_TILES = (TileType.LEFT_TOP_CORNER, TileType.RIGHT_TOP_CORNER, TileType.LEFT_BOTTOM_CORNER,
              TileType.RIGHT_BOTTOM_CORNER, TileType.LEFT_HEADED_T, TileType.RIGHT_HEADED_T,
              TileType.TOP_HEADED_T, TileType.BOTTOM_HEADED_T)
DEAD_TILES = (TileType.EMPTY, TileType.UNKNOWN)
TURN_SPEED = 10

SMALL_SPEED = 0.5
MEDIUM_SPEED = 4
MAX_TICKS_WITHOUT_MOVE = 8
MAX_REAR_MOVE_TICKS = 80
LEFT = (-1, 0)
RIGHT = (1, 0)
UPPER = (0, -1)
LOWER = (0, 1)
NEIGHBOURS = (LEFT, RIGHT, UPPER, LOWER)


class MyStrategy:
    rear_move_ticks_remain = 0
    ticks_without_move = 0
    grid = [[]]
    grid_width = 0
    grid_height = 0

    @staticmethod
    def get_wheel_turn_to_waypoint(unit, x, y):
        return unit.get_angle_to(x, y) * 32.0 / pi

    def steps_to_point(self, ux, uy, px, py):
        print(ux, uy)
        if ux == px and uy == py:
            return [(px, py)]
        neighbours = [(0, 0), (0, 0), (0, 0), (0, 0)]
        lx = ux - px
        ly = uy - py
        if abs(lx) >= abs(ly):
            neighbours[0], neighbours[3] = (LEFT, RIGHT) if lx < 0 else (RIGHT, LEFT)
            neighbours[1], neighbours[2] = (UPPER, LOWER) if ly < 0 else (LOWER, UPPER)
        else:
            neighbours[0], neighbours[3] = (UPPER, LOWER) if ly < 0 else (LOWER, UPPER)
            neighbours[1], neighbours[2] = (LEFT, RIGHT) if lx < 0 else (RIGHT, LEFT)
        for neighbour in neighbours:
            x = ux + neighbour[0]
            y = uy + neighbour[1]
            if not (0 <= x < self.grid_width and 0 <= y < self.grid_height) or \
                    self.grid[x][y] not in DEAD_TILES:
                continue
            path = self.steps_to_point(x, y, px, py)
            if path:
                return [(x, y)] + path
        return None

    def move(self, me: Car, world: World, game: Game, move: Move):
        self.grid = world.tiles_x_y
        self.grid_width = len(world.tiles_x_y[0])
        self.grid_height = len(world.tiles_x_y)

        next_tile_type = world.tiles_x_y[me.next_waypoint_x][me.next_waypoint_y]
        curr_tile_x = int(me.x // game.track_tile_size + (
            -1 if me.x % game.track_tile_size == 0 else 0))
        curr_tile_y = int(me.y // game.track_tile_size + (
            -1 if me.y % game.track_tile_size == 0 else 0))


        print('----------', world.tick)
        if world.tick == 0:
            for r in world.tiles_x_y:
                print(r)
        print(me.next_waypoint_x, me.next_waypoint_y, next_tile_type)
        # print(curr_tile_x, curr_tile_y)

        print(self.steps_to_point(curr_tile_x, curr_tile_y, me.next_waypoint_x, me.next_waypoint_y))

        # print(self.ticks_without_move, self.rear_move_ticks_remain)


        # print(me.speed_x, me.speed_y)
        # print(me.x, me.y)

        # до начала движения
        if world.tick < game.initial_freeze_duration_ticks:
            move.engine_power = 1.0
            return

        # задний ход
        if self.rear_move_ticks_remain > 0:
            self.rear_move_ticks_remain -= 1
            next_x = (me.next_waypoint_x + 0.5) * game.track_tile_size
            next_y = (me.next_waypoint_y + 0.5) * game.track_tile_size
            move.wheel_turn = -1 if self.get_wheel_turn_to_waypoint(me, next_x, next_y) > 0 else 1
            move.engine_power = -1.0
            return

        # счётчик простоя
        if abs(me.speed_x) < SMALL_SPEED and abs(me.speed_y) < SMALL_SPEED:
            self.ticks_without_move += 1
        else:
            self.ticks_without_move = 0
        if self.ticks_without_move > MAX_TICKS_WITHOUT_MOVE:
            self.ticks_without_move = 0
            self.rear_move_ticks_remain = MAX_REAR_MOVE_TICKS

        # move.engine_power = 1.0
        # move.use_nitro = True

        # есть ли машины рядом
        cars_is_close = False
        for car in world.cars:
            if car.id != me.id and me.get_distance_to_unit(car) <= me.width:
                cars_is_close = True

        if cars_is_close and any((
            all((
                next_tile_type == TileType.VERTICAL,
                abs(me.speed_x) < SMALL_SPEED,
                abs(me.speed_y) > MEDIUM_SPEED,
            )),
            all((
                next_tile_type == TileType.HORIZONTAL,
                abs(me.speed_y) < SMALL_SPEED,
                abs(me.speed_x) > MEDIUM_SPEED,
            ))
        )):
            move.engine_power = 1.0
            return

        next_x = (me.next_waypoint_x + 0.5) * game.track_tile_size
        next_y = (me.next_waypoint_y + 0.5) * game.track_tile_size

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

        move.wheel_turn = self.get_wheel_turn_to_waypoint(me, next_x, next_y)
        speed_module = hypot(me.speed_x, me.speed_y)
        if speed_module > TURN_SPEED and next_tile_type in TURN_TILES:
            move.brake = True

        move.engine_power = 1.0


        # print(me.x, me.y)
        # print(me.next_waypoint_x, me.next_waypoint_y)
