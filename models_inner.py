import copy
import random
from enum import Enum


SIZE = 6  # Размер поля


class SeaBattleException(Exception):
    def __init__(self, text):
        self.txt = text


class ShipDirection(Enum):
    empty = 0  # Для однопалубников
    gorisontal = 1
    vertical = 2


class ShootResult(Enum):
    missed = 0  # Мимо
    injure = 1  # Ранил
    killed = 2  # Убил


class Dot:
    def __init__(self, x, y):
        self.__x = None
        self.__y = None
        self.x = x
        self.y = y

    @property
    def x(self):
        return self.__x

    @x.setter
    def x(self, new_x):
        self.check_coord(new_x)
        self.__x = new_x

    @property
    def y(self):
        return self.__y

    @y.setter
    def y(self, new_y):
        self.check_coord(new_y)
        self.__y = new_y

    def __str__(self):
        return f"{self.x},{self.y}"

    @staticmethod
    def check_coord(coord):
        if type(coord) != int:
            raise SeaBattleException("Координаты должны быть целыми числами.")
        if coord <= 0:
            raise SeaBattleException("Координаты должны быть больше нуля.")

    def get_direction(self, other):
        if other.x == self.x and abs(other.y - self.y) == 1:
            return ShipDirection.gorisontal
        elif other.y == self.y and abs(other.x - self.x) == 1:
            return ShipDirection.vertical
        return None

    def near_with(self, other):
        """Проверяем, соприкасается ли с переданной точкой.
        Соприкасаться может как по вертикали/горизонтали, так и по диагонали."""
        return abs(self.x - other.x) <= 1 and abs(self.y - other.y) <= 1

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y


class ShipPart(Dot):
    """Палуба корабля."""

    def __init__(self, x, y):
        super(ShipPart, self).__init__(x, y)
        self.alive = True

    def __str__(self):
        return f"Палуба ({self.x},{self.y}) " + "целая." if self.alive else "подбита."


class Ship:
    """Корабль."""

    def __init__(self, *ship_parts):
        """
        :param ship_parts: добавляемые палубы
        """

        self.__direction = ShipDirection.empty
        self.__parts = []
        for part in ship_parts:
            self.add_part(part)

    @property
    def direction(self):
        return self.__direction

    @property
    def ship_parts(self):
        # Не даем изменять палубы корабля напрямую, поэтому возвращаем копию
        return copy.deepcopy(self.__parts)

    def add_part(self, part):
        if part in self.__parts:
            raise SeaBattleException("Такая палуба уже есть на корабле.")
        first_part = len(self.__parts) == 0
        can_add = first_part  # Если палуб еще нет, то проверять нечего, добавляем
        for p in self.__parts:
            # Проверяем, соприкасается ли с имеющимися палубами
            if self.__direction == ShipDirection.gorisontal:
                if part.x == p.x and abs(part.y - p.y) == 1:
                    can_add = True
                    break
            elif self.__direction == ShipDirection.vertical:
                if part.y == p.y and abs(part.x - p.x) == 1:
                    can_add = True
                    break
            else:
                # Надо определить направление корабля по уже имеющейся и переданной палубе.
                # Либо вернуть ошибку если палубы не соприкасаются.
                d = p.get_direction(part)
                if d:
                    self.__direction = d
                    can_add = True
                    break
        if can_add:
            self.__parts.append(part)
        else:
            raise SeaBattleException("Палуба не соприкасается с уже имеющимися на корабле,"
                                     " либо содержит неверное направление")

    def shoot(self, dot):
        for p in self.__parts:
            if p == dot:
                p.alive = False
                return ShootResult.injure if self.is_alive else ShootResult.killed
        return ShootResult.missed

    @property
    def size(self):
        return len(self.__parts)

    @property
    def is_alive(self):
        return any(p.alive for p in self.__parts)

    def __eq__(self, other):
        return self.__parts == other.__parts

    def __str__(self):
        return "Корабль со следующими палубами:\n" + "\n".join(p.__str__() for p in self.__parts)

    def compatible_with(self, other):
        """Проверка возможности размещения вместе с кораблем other на одном поле."""
        for p in self.__parts:
            for other_p in other.__parts:
                if abs(p.x - other_p.x) <= 1 and abs(p.y - other_p.y) <= 1:
                    return False
        return True

    def remove_near_dots(self, available_dots):
        # Все точки вокруг корабля надо убрать из available_dots
        to_remove = []
        for d in available_dots:
            for p in self.ship_parts:
                if d.near_with(p):
                    to_remove.append(d)
                    break
        for d in to_remove:
            available_dots.remove(d)


class Field:
    """Игровое поле."""

    EMPTY_CELL = chr(0x25A1)
    CELL_SHOOTED = chr(0x25E6)
    CELL_CONTOURED = "-"
    SHIP_CELL_ALIVE = chr(0x25A0)
    SHIP_CELL_KILLED = "x"

    def __init__(self, *ships, size=SIZE):
        random.seed()
        self.__size = size
        self.__init_board()
        self.__ships = []
        for s in ships:
            self.add_ship(s)

    @property
    def size(self):
        return self.__size

    @property
    def ships(self):
        # Не даем менять напрямую
        for s in self.__ships:
            yield copy.deepcopy(s)

    def __init_board(self):
        """Пустое пронумерованное поле."""
        self.__board = [[" "] + list(map(str, range(1, self.size + 1)))]  # Номера колонок
        for i in range(1, self.size + 1):
            line = [str(i)] + [Field.EMPTY_CELL for _ in range(self.size)]
            self.__board.append(line)

    def add_ship(self, ship: Ship):
        if ship in self.__ships:
            raise SeaBattleException("Такой корабль уже есть на поле.")

        ship_size = ship.size
        # Проверка кол-ва кораблей по размеру (кол-ву палуб)
        ships_cnt_with_eq_size = len(["" for s in self.__ships if s.size == ship_size])
        if ship_size == 3:
            if ships_cnt_with_eq_size == 1:
                raise SeaBattleException("Трехпалубник может быть только один.")
        elif ship_size == 2:
            if ships_cnt_with_eq_size == 2:
                raise SeaBattleException("Двухпалубников может быть только два.")
        elif ship_size == 1:
            if ships_cnt_with_eq_size == 4:
                raise SeaBattleException("Однопалубников может быть только четыре.")
        else:
            raise SeaBattleException(f"Корабля размером в {ship_size} палуб не может быть.")

        # Проверка координат корабля
        if self.ship_out(ship):
            raise SeaBattleException("Корабль  выходит за размеры поля.")
        for s in self.__ships:
            if not s.compatible_with(ship):
                raise SeaBattleException(f"{ship} \nне может быть размещен вместе с кораблем ниже.\n{s}")

        # Если нигде не бросили исключение, то можно добавлять корабль на поле
        self.__ships.append(ship)
        for p in ship.ship_parts:
            self.__board[p.x][p.y] = Field.SHIP_CELL_ALIVE

    def out(self, dot):
        return dot.x > self.size or dot.y > self.size

    def ship_out(self, ship: Ship):
        for p in ship.ship_parts:
            if self.out(p):
                return True
        return False

    def all_ships_exist(self):
        ship_sizes = [3, 2, 2, 1, 1, 1, 1]
        for s in self.__ships:
            ship_sizes.remove(s.size)
        return len(ship_sizes) == 0

    def shoot(self, dot):
        if self.out(dot):
            raise SeaBattleException("Точка выходит за пределы поля.")
        for s in self.__ships:
            res = s.shoot(dot)
            if res != ShootResult.missed:
                self.__board[dot.x][dot.y] = Field.SHIP_CELL_KILLED
                if res == ShootResult.killed:
                    self.contour_killed_ship(s)
                return res
        self.__board[dot.x][dot.y] = Field.CELL_SHOOTED
        return ShootResult.missed

    def contour_killed_ship(self, s: Ship):
        coords = [Dot(p.x, p.y) for p in s.ship_parts]
        for i in range(1, self.size + 1):
            for j in range(1, self.size + 1):
                for c in coords:
                    d = Dot(i, j)
                    if d not in coords and d.near_with(c):
                        self.__board[i][j] = Field.CELL_CONTOURED

    @property
    def has_alive_ships(self):
        return any([s.is_alive for s in self.ships])

    def show_position(self, hidden=False):
        for row in self.__board:
            for v in row:
                if hidden:
                    if v == Field.SHIP_CELL_ALIVE:
                        v = Field.EMPTY_CELL
                    print(f"{v:2s}", end="")
                else:
                    print(f"{v:2s}", end="")
            print()

    @staticmethod
    def rnd_coords():
        v = random.randint(0, SIZE * SIZE - 1)
        x = v // SIZE
        y = v - x * SIZE
        return x + 1, y + 1  # Координаты начинаются с 1, а не 0

    @staticmethod
    def read_player_field():
        print(
            "Введите координаты кораблей. Должен быть указан 1 трехпалубный корабль, 2 двухпалубных и 4 однопалубных.",
            "\nПример кораблей:",
            "1,1 1,2 1,3; 4,2 4,3; 6,1 6,2; 1,5; 3,6; 6,4; 6,6"
            f"\nКаждая палуба задается парой чисел от 1 до {SIZE}, разделенных запятой: сначала срока, а затем столбец.",
            "\nКоординаты палуб отделяются друг от друга пробелами.",
            "\nОписание всех палуб корабля нужно завершить точкой с запятой.",
        )
        while True:
            try:
                field = Field()
                ships_str = input()
                # ships_str = "1,1 1,2 1,3; 4,2 4,3; 6,1 6,2; 1,5; 3,6; 6,4; 6,6"
                for ship_raw in ships_str.split(";"):
                    ship = Ship()
                    for coords in ship_raw.strip().split():
                        ship.add_part(
                            ShipPart(
                                *tuple(
                                    map(int, coords.split(","))
                                )
                            )
                        )
                    field.add_ship(ship)
                if not field.all_ships_exist():
                    raise SeaBattleException("Не заданы все корабли.")
                return field
            except Exception as e:
                print("Ошибка парсинга координат.")
                if type(e) is SeaBattleException:
                    print(e)
                print("Попробуйте ввести их еще раз.")


class FieldGenerator:
    def __init__(self, field_size=SIZE, ship_sizes=[3, 2, 2, 1, 1, 1, 1], max_tries=1000):
        self.__ship_sizes = ship_sizes.copy()
        self.field_size = field_size
        self.__available_dots_for_ships = []
        self.__max_tries = max_tries
        self.__field = Field()

    def __reset_available_dots_for_ships(self):
        self.__available_dots_for_ships = []
        for i in range(1, self.field_size + 1):
            for j in range(1, self.field_size + 1):
                self.__available_dots_for_ships.append(Dot(i, j))

    def generate_rnd_field(self):
        """Алгорим не оптимальный вообще ни разу.
        Генерируем поле последовательно: корабль за кораблем.
        На каждый размер корабля сначала  определяем список из возможных его размещений.
        Выбираем рандомный вариант, а если список путой, то начинаем генерировать поля с нуля.
        Таких попыток может быть max_tries итераций. Если не смогли сгенерировать, то брасаем исключение."""
        try_cnt = 0
        while True:
            field = Field()
            self.__reset_available_dots_for_ships()
            try:
                for ship_size in self.__ship_sizes:
                    variants = self.__dots_for_ship_size(ship_size)
                    if not variants:
                        raise SeaBattleException(f"Нет доступных вариантов размещения корабля размером {ship_size}")
                    else:
                        var = variants[random.randint(0, len(variants) - 1)]
                        s = Ship(*[ShipPart(dot.x, dot.y) for dot in var])
                        field.add_ship(s)
                        s.remove_near_dots(self.__available_dots_for_ships)
                return field
            except SeaBattleException:
                try_cnt += 1
                if try_cnt == self.__max_tries:
                    raise SeaBattleException("Не удаось сгенерировать поле.")

    def __dots_for_ship_size(self, ship_size):
        """
        :param ship_size: Размер корабля
        :return: Все возможные варианты размещения - список из список точек (палуб)
        """

        variants = []
        for d in self.__available_dots_for_ships:
            # Пробуем двигаться от точки по всем 4 направлениям
            for direction in [ShipDirection.vertical, ShipDirection.gorisontal]:
                for adder in [1, -1]:
                    variant = [d]
                    for c in range(1, ship_size):  # 1 палуба уже есть - это точка dot
                        try:
                            if direction == ShipDirection.vertical:
                                check_dot = Dot(d.x + c * adder, d.y)
                            else:
                                check_dot = Dot(d.x, d.y + c * adder)
                            if check_dot not in self.__available_dots_for_ships:
                                break
                        except SeaBattleException:
                            break
                        if self.__field.out(check_dot):
                            break
                        else:
                            variant.append(check_dot)
                    if len(variant) == ship_size:
                        # Варианты будут повторяться: [(1,1) (1,2)] и [(1,2) (1,1)], но на логику это никак не повлияет.
                        # Сортировать точки в списке и затем проверять входжение будет дольше.
                        variants.append(variant)
        return variants
