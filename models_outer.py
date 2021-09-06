import random

from models_inner import(
    Dot,
    ShipPart,
    Ship,
    Field,
    SeaBattleException,
    ShootResult,
    ShipDirection,
    FieldGenerator,
)


class Player:
    def __init__(self, field):
        self.field = field  # Своя доска.

    def ask(self):
        pass

    def enemy_shoot(self, shot_dot):  # Выстрел противника по нашей доске.
        try:
            res = self.field.shoot(shot_dot)
        except SeaBattleException as e:
            print(e)
        return res


class User(Player):
    def __init__(self, field):
        super(User, self).__init__(field)

    def ask(self):
        while True:
            try:
                shot_dot = Dot(
                    *tuple(
                        map(
                            int,
                            input(
                                "\nВведите координаты выстрела. \nНомер строки и столбца, разделенные пробелом: "
                            ).split()
                        )
                    )
                )
                if self.field.out(shot_dot):
                    raise SeaBattleException("Выстрел за пределы доски.")
            except SeaBattleException as e:
                print(e)
                continue
            except (ValueError, TypeError) as e:
                print("Координаты неверные.")
                continue
            else:
                return shot_dot


class AI(Player):
    def __init__(self, field):
        super(AI, self).__init__(field)
        self.__available_dots_for_shot = []  # Список доступных для выстрела точек
        for i in range(1, self.field.size + 1):
            for j in range(1, self.field.size + 1):
                self.__available_dots_for_shot.append(Dot(i, j))
        self.__hunting_ship = Ship()  # Раненый корабль за которым охотимся

    def ask(self):
        dot = self.__gen_next_shot()
        print(f"\nКомпьютер стреляет по координатам {dot.x, dot.y}")
        input("Нажмите Enter чтобы продолжить.")
        return dot

    def __gen_next_shot(self):
        if self.__hunting_ship.size == 0:
            return self.__available_dots_for_shot.pop(random.randint(0, len(self.__available_dots_for_shot) - 1))
        else:
            # Если есть раненый корабль, то добиваем его.
            if self.__hunting_ship.direction == ShipDirection.empty:
                # Пока подбита только 1 палуба, направления корабля не знаем.
                p = self.__hunting_ship.ship_parts[0]
                for d in self.__available_dots_for_shot:
                    if (d.x == p.x and abs(d.y - p.y) == 1) or (d.y == p.y and abs(d.x - p.x) == 1):
                        self.__available_dots_for_shot.remove(d)
                        return d
            else:
                # Знаем направление корабля, т.е. есть 2 палубы
                direction = self.__hunting_ship.direction
                p1 = self.__hunting_ship.ship_parts[0]
                p2 = self.__hunting_ship.ship_parts[1]
                for d in self.__available_dots_for_shot:
                    if (
                            direction == ShipDirection.gorisontal and d.x == p1.x and (
                            abs(d.y - p1.y) == 1 or abs(d.y - p2.y) == 1)
                    ) or (
                            direction == ShipDirection.vertical and d.y == p1.y and (
                            abs(d.x - p1.x) == 1 or abs(d.x - p2.x) == 1)
                    ):
                        self.__available_dots_for_shot.remove(d)
                        return d
        raise SeaBattleException("Не смогли сгенерировать ход")

    def add_ai_shot(self, dot, res):
        if res != ShootResult.missed:
            self.__hunting_ship.add_part(ShipPart(dot.x, dot.y))
        if self.__hunting_ship.size > 0 and res == ShootResult.killed:
            # Все точки вокруг убитого корабля надо убрать из доступных ходов
            self.__hunting_ship.remove_near_dots(self.__available_dots_for_shot)
            self.__hunting_ship = Ship()


class Game:
    def __init__(self, auto_field=True):
        self.user = None
        self.ai = None
        self.__auto_field = True  # Признак автогенерации поля пользователя
        random.seed()

    @staticmethod
    def greet():
        print(
            "Игра \"морской бой\" c компьютером."
            "\nИгровое поле представляет собой квадрат, размером 6*6 клеток."
            "\nВ вашем распоряжении 1 корабль на 3 клетки, 2 корабля на 2 клетки и 4 корабля на одну клетку."
            "\nКорабли должны распогалаться строго вертикально или горизонтально."
        )

    def start(self):
        self.init_players_fields()
        self.loop()

    @property
    def auto_field(self):
        return self.__auto_field

    @auto_field.setter
    def auto_field(self, value):
        self.__auto_field = bool(value)

    def init_players_fields(self):
        # user_field = Field(
        #     Ship(
        #         ShipPart(1, 1),
        #         ShipPart(1, 2),
        #         ShipPart(1, 3),
        #     ),
        #     Ship(
        #         ShipPart(3, 1),
        #         ShipPart(4, 1),
        #     ),
        #     Ship(
        #         ShipPart(6, 2),
        #         ShipPart(6, 3),
        #     ),
        #     Ship(
        #         ShipPart(2, 6),
        #     ),
        #     Ship(
        #         ShipPart(4, 6),
        #     ),
        #     Ship(
        #         ShipPart(6, 6),
        #     ),
        #     Ship(
        #         ShipPart(4, 4),
        #     ),
        # )
        # ai_field = Field(
        #     Ship(
        #         ShipPart(3, 1),
        #         ShipPart(4, 1),
        #         ShipPart(5, 1),
        #     ),
        #     Ship(
        #         ShipPart(1, 2),
        #         ShipPart(1, 3),
        #     ),
        #     Ship(
        #         ShipPart(5, 3),
        #         ShipPart(6, 3),
        #     ),
        #     Ship(
        #         ShipPart(1, 5),
        #     ),
        #     Ship(
        #         ShipPart(3, 3),
        #     ),
        #     Ship(
        #         ShipPart(4, 5),
        #     ),
        #     Ship(
        #         ShipPart(6, 6),
        #     ),
        # )
        fgen = FieldGenerator()
        if self.auto_field:
            self.user = User(fgen.generate_rnd_field())
        else:
            self.user = User(Field.read_player_field())
        self.ai = AI(fgen.generate_rnd_field())

    def loop(self):
        self.show_position()
        ai_step = False
        while True:
            if self.loop_step(ai_step):
                return  # Есть выигрыш, заканчиваем
            else:
                ai_step = not ai_step

    def loop_step(self, ai_step=False):
        """
        Цикл выстрелов одного игрока до тех пор, пока не будет промаха или его победы
        :param ai_step: True если ход комьютера
        :return: True если есть победитель, False если промазали
        """
        while True:
            has_winner = False
            if ai_step:
                mover = self.ai
                other_player = self.user
            else:
                mover = self.user
                other_player = self.ai

            dot = mover.ask()
            try:
                res = other_player.enemy_shoot(dot)
            except SeaBattleException as e:
                print(e)
                continue
            if mover == self.ai:
                self.ai.add_ai_shot(dot, res)
            if res == ShootResult.missed:
                print("Промазал!")
                break
            elif res == ShootResult.injure:
                print("Ранил!")
                self.show_position()
            elif res == ShootResult.killed:
                print("Убил!")
                if not other_player.field.has_alive_ships:
                    has_winner = True
                    print("Вы проиграли." if ai_step else "Вы выиграли!")
                    break
                else:
                    self.show_position()
        self.show_position(enemy_hidden=not has_winner)
        return has_winner

    def show_position(self, enemy_hidden=True):
        print("Ваша доска:")
        self.user.field.show_position()
        print("Доска компьютера:")
        self.ai.field.show_position(enemy_hidden)
