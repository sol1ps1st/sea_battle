from models_outer import Game

YES_CHAR = 'y'  # Положительное подтверждение от пользователя


if __name__ == '__main__':
    first_game = True
    g = Game()
    g.greet()
    while True:
        print(
            "Хотите сыграть в",
            "новую" if not first_game else "",
            f"игру? ({YES_CHAR} - да, любой другой символ - нет)"
        )
        first_game = False
        if input().strip() != YES_CHAR:
            break
        print(
            "Ваше игровое поле можно сгенерировать случайно, либо ввести вручную."
            f"\nДля генерации введите ({YES_CHAR}). Любой другой символ - задать вручную"
        )
        g.auto_field = input().strip() == YES_CHAR
        g.start()
