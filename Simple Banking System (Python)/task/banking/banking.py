import sqlite3
from random import randint


class TransactionError(Exception):
    pass


class Card:
    """Класс с пользователями."""

    def __init__(self, connect, cursor, card=None, code=None, balance=0) -> None:
        self.connect = connect
        self.cursor = cursor
        if card is None or code is None:
            self.number = self.__create_card()
            self.code = self.__create_code()
            self.balance = balance
            self.__save_to_db()
        else:
            self.number = card
            self.code = code
            self.balance = balance

    def __save_to_db(self):
        self.cursor.execute("""
        INSERT INTO card (number, pin, balance)
        VALUES (?, ?, ?)
         """, (self.number, self.code, self.balance))
        self.connect.commit()

    @staticmethod
    def __create_card() -> str:
        """Генерирует карту, соответствующую алгоритму Луна."""
        inn = '400000'
        # Сокращаем на одну цифру для добавления контрольной суммы
        # Вычисляем контрольную цифру
        account_number = f'{inn}{randint(1, 999999999):09d}'
        checksum = Card.calculate_luhn_checksum(account_number)
        # Возвращаем полный номер карты с контрольной цифрой
        return f'{account_number}{checksum}'

    @staticmethod
    def calculate_luhn_checksum(account_number: str) -> int:
        """Вычисляет контрольную цифру для номера счета по алгоритму Луна."""
        digits = [int(digit) for digit in account_number]
        # Применяем шаги алгоритма Луна к каждому второму числу, начиная с предпоследнего
        for i in range(len(digits) - 1, -1, -2):
            digits[i] = digits[i] * 2
            if digits[i] > 9:
                digits[i] -= 9
        # Суммируем все цифры
        total_sum = sum(digits)
        # Вычисляем контрольную цифру так, чтобы сумма была кратна 10
        checksum = (10 - total_sum % 10) % 10
        return checksum

    @staticmethod
    def is_valid_card_number(number: str) -> bool:
        """Проверяет валидность номера карты по алгоритму Луна."""
        card_number_without_checksum = number[:-1]
        checksum = Card.calculate_luhn_checksum(card_number_without_checksum)
        return str(checksum) == number[-1]

    @staticmethod
    def __create_code() -> str:
        """Генерирует код."""
        return f"{randint(1, 9999):04d}"

    @classmethod
    def check_card(cls, connect, cursor, number: str, code=None):
        """Проверяет наличие пользователя в базе."""

        if code:
            cursor.execute("""
            SELECT number, pin, balance 
            FROM card 
            WHERE number = ? AND pin = ?
            """, (number, code))
        else:
            cursor.execute("""
            SELECT number, pin, balance 
            FROM card 
            WHERE number = ? 
            """, (number,))

        result = cursor.fetchone()
        if result:
            return cls(connect, cursor,
                       card=result[0], code=result[1], balance=result[2])
        else:
            return None

    def update_balance(self, money: int) -> None:
        """Обновить баланс карты."""
        print(f"Updating balance for card number: {type(self.number)}")
        self.cursor.execute("""
                UPDATE card
                SET balance = balance + ?
                WHERE number = ?
                """, (money, self.number))
        self.connect.commit()

        self.cursor.execute("""
                SELECT balance 
                FROM card 
                WHERE number = ? 
                """, (self.number,))
        result = self.cursor.fetchone()
        self.balance = result[0]

    def delete_card(self) -> None:
        """Удаление карты из базы данных."""
        self.cursor.execute("""
        DELETE FROM card
        WHERE number = ?
        """, (self.number,))

        self.connect.commit()


class SimpleBankingSystem:
    """Простое банковское приложение."""

    def __init__(self, connect, cursor) -> None:
        self.anon_user_commands = {
            1: ('Create an account', self.__create_account),
            2: ('Log into account', self.__login),
            0: ('Exit', self.__exit_program),
        }
        self.user_commands = {
            1: ('Balance', self.__balance),
            2: ('Add income', self.__add_income),
            3: ('Do transfer', self.__do_transfer),
            4: ('Close account', self.__close_account),
            5: ('Log out', self.__logout),
            0: ('Exit', self.__exit_program),
        }
        self.card = None
        self.running = True
        self.connect = connect
        self.cursor = cursor

    def start(self):
        """Запускает приложение и принимает номера команд."""
        while self.running:
            if self.card is None:
                command_str = ''.join([f'{key}. {value[0]}\n'
                                       for key, value in
                                       self.anon_user_commands.items()])

                command = int(input(command_str))
                self.anon_user_commands[command][1]()

            else:
                command_str = ''.join([f'{key}. {value[0]}\n'
                                       for key, value in
                                       self.user_commands.items()])

                command = int((input(command_str)))
                self.user_commands[command][1]()

    def __exit_program(self) -> None:
        """Меняет флаг класса для завершения программы."""
        self.running = False
        print('Bye!')

    def __create_account(self) -> None:
        """Создает аккаунт пользователя."""
        user = Card(self.connect,
                    self.cursor)

        print(f'Your card has been created\n'
              f'Your card number:\n'
              f'{user.number}\n'
              f'Your card PIN:\n'
              f'{user.code}')

    def __login(self) -> None:
        """
        На основании номера карты и кода ищет
        пользователя и добавляет его в переменную.
        """
        card = input('Enter your card number:\n')
        code = input('Enter your PIN:\n')

        self.card = Card.check_card(self.connect, self.cursor, card, code)

        if self.card:
            print('You have successfully logged in!\n')
        else:
            print("Wrong card number or PIN!\n")

    def __logout(self) -> None:
        """Удаляет пользователя из переменной user."""
        self.card = None
        print('You have successfully logged out!\n')

    def __balance(self) -> None:
        """Выводит баланс карты пользователя."""
        print(self.card.balance)

    def __add_income(self) -> None:
        """Добавляет деньги на счет."""
        income = int(input('Enter income:\n'))
        self.card.update_balance(income)
        print('Income was added!')

    def __do_transfer(self) -> None:
        """Валидация и перевод денег """
        print('Transfer')
        try:
            number = input('Enter card number:\n')

            if number == self.card.number:
                raise TransactionError("You can't transfer money to the same account!")
            elif not Card.is_valid_card_number(number):
                raise TransactionError("Probably you made a mistake in the card number. Please try again!")

            transfer_card = Card.check_card(self.connect, self.cursor, number)
            if transfer_card is None:
                raise TransactionError("Such a card does not exist.")

            transfer_money = int(input('Enter how much money you want to transfer:\n'))
            if transfer_money > self.card.balance:
                raise TransactionError("Not enough money!")

            self.card.update_balance(transfer_money * -1)
            transfer_card.update_balance(transfer_money)
        except TransactionError as e:
            print(e)

    def __close_account(self) -> None:
        """Удаление карты."""
        self.card.delete_card()
        self.card = None


def main():
    connect = sqlite3.connect('card.s3db')
    cursor = connect.cursor()
    cursor.execute(""" 
        CREATE TABLE IF NOT EXISTS card (
        id INTEGER PRIMARY KEY,
        number TEXT,
        pin TEXT,
        balance INTEGER DEFAULT 0
        );
        """)

    bank = SimpleBankingSystem(connect, cursor)
    bank.start()

    connect.commit()
    cursor.close()
    connect.close()


if __name__ == '__main__':
    main()
