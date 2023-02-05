import numpy as np
from ai import BaseAI

CREATOR = 'JanDerGrosse'
KNIGHTS = []

"""Map codes:
no info: -1
obstacle: 1
gem: 2
else: 0
"""
GLOBAL_MAP = np.full((1792, 960), 0)

ENEMY_FLAG = None

TARGETS_RED_TRAVEL = ((1750, 100), (1750, 900))
TARGETS_RED_SEEK = ((1750, 900), (1750, 100))

TARGETS_BLUE_TRAVEL = ((30, 100), (30, 900))
TARGETS_BLUE_SEEK = ((30, 900), (30, 100))



def incorporate_local_map(knight_pos: (int, int), knight_range: int, local_map: np.ndarray):
    knight_x, knight_y = knight_pos
    if local_map.shape[0] == 2 * knight_range + 1:
        local_x_start = knight_x - knight_range
    else:
        if knight_x < knight_range:
            local_x_start = 0
        else:
            local_x_start = knight_x - knight_range
    if local_map.shape[1] == 2 * knight_range + 1:
        local_y_start = knight_y - knight_range
    else:
        if knight_y < knight_range:
            local_y_start = 0
        else:
            local_y_start = knight_y - knight_range
    global_slice = GLOBAL_MAP[local_x_start:local_x_start + local_map.shape[0],
                   local_y_start:local_y_start + local_map.shape[1]]
    global_slice[...] = np.where(local_map == 1, 1, global_slice)


def distance(a, b):
    return np.linalg.norm(a - b)


def trace(a, b, n):
    delta = b - a
    return (a + np.outer(np.linspace(0, 1, n), delta)).astype(int)


def path_is_blocked(a, b, n=10):
    tr = trace(a, b, n)
    return np.any(GLOBAL_MAP[(tr[:, 0], tr[:, 1])] == 1)


def is_out_of_bounds(pos: np.ndarray):
    return not (0 <= pos[0] < GLOBAL_MAP.shape[0] and 0 <= pos[1] < GLOBAL_MAP.shape[1])


def direction_from_heading(heading, speed):
    angle = heading - 180 * np.pi
    return speed * np.array((np.cos(angle), np.sin(angle)))


def neighbours(pos: np.ndarray, speed: float):
    res = []
    for heading in range(0, 360, 360 // 6):
        candidate = (pos + direction_from_heading(heading, speed)).astype(int)
        if not is_out_of_bounds(candidate) and not path_is_blocked(pos, candidate):
            res.append(candidate)
    return res


def find_path(start: np.array, goal: np.array, speed: float):
    pos = start
    bfs_queue = [[pos]]
    best = None
    best_dist = 10000
    seen = set()
    while bfs_queue:
        current = bfs_queue.pop(0)
        if (d := distance(current[-1], goal)) < best_dist:
            best_dist = d
            best = current

        if len(current) == 7:
            continue
        neigh = neighbours(current[-1], speed)
        if not neigh:
            continue
        for n in neigh:
            if tuple(n) in seen:
                continue
            bfs_queue.append(current + [n])
            seen.add(tuple(n))
    return best[1:]


def reset():
    global KNIGHTS, GLOBAL_MAP, ENEMY_FLAG
    KNIGHTS = []
    GLOBAL_MAP[...] = 0
    ENEMY_FLAG = None

class Slayer(BaseAI):

    def __init__(self, *args, **kwargs):
        if len(KNIGHTS) == 3:
            reset()

        if kwargs:
            self.index = len(KNIGHTS)
            KNIGHTS.append(self)

            self.previous_position = [0, 0]
            self.current_position = [0, 0]
            self.circling_castle = False
            self.path = []
            self.seeking = False
            self.seek_targets = TARGETS_RED_SEEK if kwargs['team'] == 'red' else TARGETS_BLUE_SEEK
            self.tick = 0
            if self.index < 2:
                self.seek_index = self.index
                kind = 'healer'
            else:
                kind = 'warrior'
        else:
            kind = 'warrior'

        super().__init__(*args, creator=CREATOR, kind=kind, **kwargs)

    def run(self, t: float, dt: float, info: dict):
        global ENEMY_FLAG

        self.tick += 1
        me = info['me']
        pos = np.array(me['position'])
        speed = me['speed'] * dt
        heading = me['heading']

        self.previous_position = self.current_position
        self.current_position = pos

        if self.opposing_team in info['flags']:
            ENEMY_FLAG = info['flags'][self.opposing_team]

        if ENEMY_FLAG is not None and self.index < 2 and distance(pos, ENEMY_FLAG) < 90:
            self.enter_castle(pos)
            return

        if not self.stop:
            if distance(pos, self.previous_position) < 2:
                self.random_path(pos, speed)

        if self.index == 2:
            target = info['flags'][self.team]
            if distance(pos, target) < 10:
                self.stop = True
                return
        else:
            target = self.get_target(pos)

        if distance(pos, target) < 20:
            self.goto = target
            return

        if not self.path:
            self.path = find_path(pos, target, speed)
            if not self.path:
                self.heading = (heading + 180) % 360
                return
        elif self.tick % 5 == self.index:
            incorporate_local_map(me['position'], me['view_radius'], info['local_map'])

        self.goto = tuple(self.path.pop(0))

    def get_target(self, pos):
        if ENEMY_FLAG is not None:
            return ENEMY_FLAG
        if self.team == 'red':
            if not self.seeking:
                if pos[0] > 1650:
                    self.seeking = True
                return TARGETS_RED_TRAVEL[self.index]
            if abs(self.seek_targets[self.seek_index][1] - pos[1]) < 50:
                self.seek_index = (self.seek_index + 1) % 2
            return self.seek_targets[self.seek_index]
        if self.team == 'blue':
            if not self.seeking:
                if pos[0] < 200:
                    self.seeking = True
                return TARGETS_BLUE_TRAVEL[self.index]
            if abs(self.seek_targets[self.seek_index][1] - pos[1]) < 50:
                self.seek_index = (self.seek_index + 1) % 2
            return self.seek_targets[self.seek_index]

    def random_path(self, pos, speed):
        self.path = []
        for _ in range(3):
            pos = pos + direction_from_heading(np.random.random() * 360.0, speed).astype(int)
            self.path.append(pos)

    def enter_castle(self, pos):
        if not self.circling_castle:
            self.circle(pos)
        if self.path:
            self.goto = tuple(self.path[0])
            if distance(pos, self.path[0]) < 5:
                self.path.pop(0)
            return
        self.goto = ENEMY_FLAG


    def circle(self, pos):
        f = np.array(ENEMY_FLAG)
        for angle, delta in zip((0, 180, 270, 90), ((80, 0), (-80, 0), (0, 80), (0, -80))):
            if not path_is_blocked(f, f+np.array(delta), 100):
                e_angle = angle
                break
        else:
            e_angle = 0  # in case te above fails, let's at least not crash

        t = np.linspace(0, 1, 40)
        r = 60
        p_angle = np.arctan2(pos[1]-f[1], pos[0]-f[0])
        angles = t * e_angle/180*np.pi + (1-t) * p_angle
        self.path = [f + r * np.array([np.cos(a), np.sin(a)]) for a in angles]
        self.circling_castle = True


team = {
    'Gleidi Geschmeidi': Slayer,
    'Mme. Vajine': Slayer,
    'Sir Cumbert': Slayer
}
