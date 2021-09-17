# demo by "wkta"
# (contact: crypto@gaudia-tech.com)
# Visit http://kata.games to learn more
# about this new technology...
# Or you can join:
# https://discord.gg/3NFfvHAt44
# Be a part of the revolution/ create your own
# pygame games for the Web!
import math
import random
import katagames_sdk.engine as kataen

pygame = kataen.import_pygame()
CogObject = kataen.CogObject
EventReceiver = kataen.EventReceiver
EngineEvTypes = kataen.EngineEvTypes
SCR_SIZE = [0, 0]
NB_ROCKS = 9
bullets = list()
FG_COLOR = (119, 255, 0)
music_snd = None
view = ctrl = None


class Vector2d:
    def __init__(self, x=0.0, y=0.0):
        self.x, self.y = float(x), float(y)

    @classmethod
    def new_from_angle(cls, theta):
        coord_x = math.cos(theta)
        coord_y = math.sin(theta)
        return cls(coord_x, coord_y)

    def get_int_coords(self):
        return int(self.x), int(self.y)

    def length(self):
        return math.sqrt(self.x ** 2 + self.y ** 2)

    def multiply(self, facteur):
        self.x *= facteur
        self.y *= facteur

    @property
    def rtuple(self):
        return self.x, self.y

    def clone(self):
        return self.__class__(self.x, self.y)

    def __add__(self, other_vect):
        return self.__class__(self.x + other_vect.x, self.y + other_vect.y)


class RockSprite(pygame.sprite.Sprite):
    snd = None

    def __init__(self):
        super().__init__()
        if self.__class__.snd:
            pass
        else:
            self.__class__.snd = pygame.mixer.Sound('assets/explosion_002.wav')
            self.__class__.snd.set_volume(0.66)
        self.image = pygame.image.load('assets/rock.png')
        self.image.set_colorkey((0xff, 0, 0xff))
        pos = [random.randint(0, SCR_SIZE[0] - 1), random.randint(0, SCR_SIZE[1] - 1)]
        self.rect = self.image.get_rect()
        self.rect.topleft = pos
        self.vx = random.choice((1, -1)) * random.randint(1, 3)
        self.vy = random.choice((1, -1)) * random.randint(1, 3)
        self.cpt = 1
        self.zombie = False
        self.immunity = 0

    def destroyed(self):
        self.__class__.snd.play(0)

    def update(self):
        if self.immunity:
            self.immunity -= 1
        if self.cpt == 0:
            x, y = self.rect.topleft
            x += self.vx
            y += self.vy
            self.rect.topleft = x, y
            if self.rect.left >= SCR_SIZE[0]:
                self.rect.right = 0
            elif self.rect.right < 0:
                self.rect.left = SCR_SIZE[0] - 2
            if self.rect.top >= SCR_SIZE[1]:
                self.rect.bottom = 0
            elif self.rect.bottom < 0:
                self.rect.top = SCR_SIZE[1] - 2
        self.cpt = (self.cpt + 1) % 3

    def inv_speed(self):
        self.immunity = 128
        self.vx *= -1
        self.vy *= -1


class ShipModel(CogObject):
    DASH_DISTANCE = 55
    DELTA_ANGLE = 0.04
    SPEED_CAP = 192
    RAD = 5

    def __init__(self):
        super().__init__()
        self._position = None
        self._angle = None
        self._speed = None
        self.reset()

    @property
    def pos(self):
        return self._position.rtuple

    def reset(self):
        initpos = (SCR_SIZE[0] // 2, SCR_SIZE[1] // 2)
        self._position = Vector2d(*initpos)
        self._angle = 0
        self._speed = Vector2d()

    def three_pt_repr(self):
        orientation = -self._angle
        pt_central = self._position.rtuple
        temp = [Vector2d.new_from_angle(orientation - (2.0 * math.pi / 3)),
                Vector2d.new_from_angle(orientation),
                Vector2d.new_from_angle(orientation + (2.0 * math.pi / 3))]
        for tv in temp:
            tv.y *= -1
        temp[0].multiply(1.2 * self.RAD)
        temp[1].multiply(3 * self.RAD)
        temp[2].multiply(1.2 * self.RAD)
        pt_li = [Vector2d(*pt_central),
                 Vector2d(*pt_central),
                 Vector2d(*pt_central)]
        for i in range(3):
            pt_li[i] += temp[i]
        return pt_li[0].rtuple, pt_li[1].rtuple, pt_li[2].rtuple

    def _update_speed_vect(self):
        lg = self._speed.length()
        self._speed = Vector2d.new_from_angle(self._angle)
        self._speed.multiply(lg)

    def ccw_rotate(self):
        self._angle -= self.__class__.DELTA_ANGLE
        self._update_speed_vect()

    def cw_rotate(self):
        self._angle += self.__class__.DELTA_ANGLE
        self._update_speed_vect()

    def get_orientation(self):
        return self._angle

    def accel(self):
        if self._speed.length() == 0:
            self._speed = Vector2d.new_from_angle(self._angle)
            self._speed.multiply(5)
        else:
            speedv_now = self._speed.length()
            speedv_now += 1
            if speedv_now > self.SPEED_CAP:
                speedv_now = self.SPEED_CAP
            self._speed = Vector2d.new_from_angle(self._angle)
            self._speed.multiply(speedv_now)

    def brake(self):
        speedv_now = self._speed.length()
        speedv_now = speedv_now * 0.96
        if speedv_now < 5:
            self._speed = Vector2d()
            return
        self._speed = Vector2d.new_from_angle(self._angle)
        self._speed.multiply(speedv_now)

    def get_position(self):
        return self._position

    def get_scr_pos(self):
        return self._position.get_int_coords()

    def update(self, delta_time):
        x = self._position.x + delta_time * self._speed.x
        y = self._position.y + delta_time * self._speed.y
        if x < 0:
            x += SCR_SIZE[0]
        elif x >= SCR_SIZE[0]:
            x -= SCR_SIZE[0]
        if y < 0:
            y += SCR_SIZE[1]
        elif y >= SCR_SIZE[1]:
            y -= SCR_SIZE[1]
        self._position.x = x
        self._position.y = y

    def shoot(self):
        sh_pos = self._position.clone()
        b_speed = Vector2d.new_from_angle(self._angle)
        b_speed.multiply(3)
        return sh_pos, b_speed


class ShipCtrl(EventReceiver):
    def __init__(self, ref_mod, rocksm):
        super().__init__()
        self._ref_ship = ref_mod
        self._ref_rocks = rocksm
        self.last_tick = None

    def proc_event(self, ev, source):
        if ev.type == EngineEvTypes.LOGICUPDATE:
            ba = pygame.key.get_pressed()
            if ba[pygame.K_UP]:
                self._ref_ship.accel()
            if ba[pygame.K_DOWN]:
                self._ref_ship.brake()
            if ba[pygame.K_RIGHT]:
                self._ref_ship.cw_rotate()
            if ba[pygame.K_LEFT]:
                self._ref_ship.ccw_rotate()
            if self.last_tick:
                tmp = ev.curr_t - self.last_tick
            else:
                tmp = 0
            self.last_tick = ev.curr_t
            self._ref_ship.update(tmp)
            for b in bullets:
                b[0].x += b[1].x
                b[0].y += b[1].y
            remove = set()
            rb = set()
            for elt in self._ref_rocks:
                for idx, b in enumerate(bullets):
                    if elt.rect.collidepoint(b[0].rtuple):
                        remove.add(elt)
                        elt.zombie = True
                        rb.add(idx)
                        break
                if not elt.zombie and not elt.immunity:
                    if elt.rect.collidepoint(self._ref_ship.pos):
                        elt.inv_speed()
                        self._ref_ship.reset()
                elt.update()
            if len(remove):
                for tmp in remove:
                    tmp.destroyed()
                    self._ref_rocks.remove(tmp)
                rbplus = list(rb)
                rbplus.sort(reverse=True)
                while len(rbplus) > 0:
                    del bullets[rbplus.pop()]
        elif ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_SPACE:
                bullets.append(self._ref_ship.shoot())


class TinyWorldView(EventReceiver):
    BG_COLOR = (0, 10, 0)

    def __init__(self, ship_model, rocksm):
        super().__init__()
        self.ship = ship_model
        self.ref_rocksm = rocksm

    def proc_event(self, ev, source):
        if ev.type == EngineEvTypes.PAINT:
            ev.screen.fill(self.BG_COLOR)
            for rock_spr in self.ref_rocksm:
                ev.screen.blit(rock_spr.image, rock_spr.rect.topleft)
            for b in bullets:
                pygame.draw.circle(ev.screen, FG_COLOR, b[0].rtuple, 3, 0)
            pygame.draw.polygon(ev.screen, FG_COLOR, self.ship.three_pt_repr(), 4)


def print_mini_tutorial():
    howto_infos = """HOW TO PLAY:
    * use arrows to move
    * use SPACE to shoot"""
    print('-' * 32)
    for line in howto_infos.split('\n'):
        print(line)
    print('-' * 32)


class IntroV(EventReceiver):
    def __init__(self):
        super().__init__()
        self.img = pygame.image.load('assets/enter_start.png')
        self.dim = self.img.get_size()
        self.painting = True

    def proc_event(self, ev, source):
        global view, ctrl, music_snd
        if self.painting:
            if ev.type == EngineEvTypes.PAINT:
                ev.screen.fill((0, 0, 0))
                ev.screen.blit(self.img, ((SCR_SIZE[0] - self.dim[0]) // 2, (SCR_SIZE[1] - self.dim[1]) // 2))
            elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_RETURN:
                self.painting = False
                print_mini_tutorial()
                pygame.mixer.init()
                music_snd = pygame.mixer.Sound('assets/ndimensions-zik.ogg')
                music_snd.set_volume(0.25)
                music_snd.play(-1)


def run_game():
    global SCR_SIZE, view, ctrl
    kataen.init(kataen.OLD_SCHOOL_MODE)
    SCR_SIZE = kataen.get_screen().get_size()
    introv = IntroV()
    shipm = ShipModel()
    li = [RockSprite() for _ in range(NB_ROCKS)]
    view = TinyWorldView(shipm, li)
    ctrl = ShipCtrl(shipm, li)
    view.turn_on()
    ctrl.turn_on()
    introv.turn_on()
    game_ctrl = kataen.get_game_ctrl()
    game_ctrl.turn_on()
    game_ctrl.loop()
    kataen.cleanup()
    print('Tech demo for the Kata.games new platform(https://kata.games)')
    
    print('Music by Matthew Pablo')
    print('http://www.matthewpablo.com')


if __name__=='__main__':
    run_game()
