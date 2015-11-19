from math import hypot, pi

from model.Car import Car
from model.Game import Game
from model.Move import Move
from model.World import World
from model.TileType import TileType

SMALL_SPEED = 1


class MyStrategy:
    prev_tile_x = None
    prev_tile_y = None
    prev_tile_type = TileType.UNKNOWN

    def move(self, me: Car, world: World, game: Game, move: Move):
        # print('--------------------------------------')
        # print(game.track_tile_size, me.next_waypoint_x, me.next_waypoint_y)
        # print(me.speed_x, me.speed_y)

        next_tile_type = world.tiles_x_y[me.next_waypoint_x][me.next_waypoint_y]
        curr_tile_x = me.x / game.track_tile_size
        curr_tile_y = me.y / game.track_tile_size

        if self.prev_tile_x is None and self.prev_tile_y is None:
            self.prev_tile_x = me.next_waypoint_x
            self.prev_tile_y = me.next_waypoint_y
            self.prev_tile_type = next_tile_type

        cars_is_close = False
        for car in world.cars:
            if car.id != me.id and me.get_distance_to_unit(car) <= me.width:
                cars_is_close = True

        if cars_is_close and any((
            all((
                next_tile_type == TileType.VERTICAL,
                abs(me.speed_x) < SMALL_SPEED
            )),
            all((
                next_tile_type == TileType.HORIZONTAL,
                abs(me.speed_y) < SMALL_SPEED
            ))
        )):
            move.engine_power = 1.0
        else:

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

            angle_to_waypoint = me.get_angle_to(next_x, next_y)
            speed_module = hypot(me.speed_x, me.speed_y)

            move.engine_power = 1.0
            move.wheel_turn = angle_to_waypoint * 32.0 / pi

            if speed_module ** 2 * abs(angle_to_waypoint) > 2.5 **2 * pi:
                move.brake = True
        # print(me.x, me.y)
        # print(me.next_waypoint_x, me.next_waypoint_y)
