# Every thing Looks good and runned successfully
import random

class Player:
    def __init__(self, id, position=1, cash=1000):
        self.id = id
        self.position = position
        self.in_jail = [False, 0]  # [is_in_jail, turns_in_jail]
        self.cash = cash
        self.owned_cards = []
        self.bankrupt = False

    def move(self, steps, board_size):
        self.position = (self.position + steps) % board_size

    def control_cash(self, amount):
        self.cash += amount

    def buy_property(self, property):
        if self.cash >= property.price:
            self.control_cash(-property.price)
            self.owned_cards.append(property.position)
            property.owner = self.id
            return True
        return False

    def declare_bankruptcy(self):
        self.cash = 0
        self.owned_cards.clear()
        self.bankrupt = True

class Property:
    def __init__(self, position, price, group):
        self.position = position
        self.price = price
        self.group = group
        self.owner = None

class SpecialProperty:
    def __init__(self, position):
        self.position = position

class MonopolyGame:
    def __init__(self, num_players):
        self.board = self.create_board()
        self.players = [Player(i) for i in range(num_players)]
        self.current_player_index = 0
        self.board_size = len(self.board)
        self.game_over = False

    def create_board(self):
        return [
            Property(1, 60, 1),
            Property(3, 60, 1),
            SpecialProperty(5),
            Property(6, 100, 2),
            Property(8, 100, 2),
            Property(9, 120, 2),
            Property(11, 140, 3),
            Property(12, 150, -1),
            Property(14, 140, 3),
            Property(15, 160, 3),
            SpecialProperty(18),
            Property(19, 180, 4),
            Property(21, 200, 4),
            Property(23, 220, 5),
            Property(24, 220, 5),
            Property(25, 240, 5),
            Property(27, 260, 6),
            Property(28, 260, 6),
            Property(29, 280, 6),
            Property(31, 300, 7),
            Property(32, 300, 7),
            Property(34, 320, 7),
            Property(37, 350, 8),
            Property(39, 400, 8)
        ]

    def roll_dice(self):
        return random.randint(1, 6) + random.randint(1, 6)

    def current_player(self):
        return self.players[self.current_player_index]

    def take_turn(self):
        player = self.current_player()
        if player.bankrupt:
            self.end_turn()
            return

        print(f"Player {player.id}'s turn (Cash: ${player.cash})")

        # Handle jail
        if player.in_jail[0]:
            print(f"Player {player.id} is in jail.")
            player.in_jail[1] += 1
            if player.in_jail[1] > 3 or player.cash >= 50:
                player.control_cash(-50)  # Pay to get out of jail
                player.in_jail = [False, 0]
                print(f"Player {player.id} paid $50 to get out of jail.")
            else:
                print(f"Player {player.id} waits in jail.")
                self.end_turn()
                return

        # Roll dice and move
        dice = self.roll_dice()
        print(f"Player {player.id} rolled {dice}.")
        player.move(dice, self.board_size)
        current_space = self.board[player.position]
        print(f"Player {player.id} landed on position {player.position}.")

        # Handle landing on a property
        if isinstance(current_space, Property):
            if current_space.owner and current_space.owner != player.id:
                rent = current_space.price // 10
                print(f"Player {player.id} pays ${rent} rent to Player {current_space.owner}.")
                player.control_cash(-rent)
                self.players[current_space.owner].control_cash(rent)
                if player.cash < 0:
                    player.declare_bankruptcy()
                    print(f"Player {player.id} declared bankruptcy.")
            elif current_space.owner is None:
                if player.cash >= current_space.price:
                    player.buy_property(current_space)
                    print(f"Player {player.id} bought position {player.position} for ${current_space.price}.")

        # Handle landing on a special card
        elif isinstance(current_space, SpecialProperty):
            self.handle_special_card(player, current_space)

        self.end_turn()

    def handle_special_card(self, player, special_card):
        # Example effects for special cards
        position = special_card.position
        if position == 5:  # Example: Go to Jail
            print(f"Player {player.id} is sent to jail!")
            player.in_jail = [True, 0]
            player.position = 10  # Example jail position
        elif position == 12:  # Example: Pay Tax
            tax_amount = 200
            print(f"Player {player.id} pays ${tax_amount} tax.")
            player.control_cash(-tax_amount)
            if player.cash < 0:
                player.declare_bankruptcy()
                print(f"Player {player.id} declared bankruptcy.")
        elif position == 23:  # Example: Bonus
            bonus_amount = 100
            print(f"Player {player.id} receives a bonus of ${bonus_amount}.")
            player.control_cash(bonus_amount)
        else:
            print(f"Player {player.id} landed on a special card with no specific effect.")


    def end_turn(self):
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        self.check_game_over()

    def check_game_over(self):
        active_players = [player for player in self.players if not player.bankrupt]
        if len(active_players) == 1:
            self.game_over = True
            print(f"Player {active_players[0].id} wins the game!")

    def play_game(self):
        while not self.game_over:
            self.take_turn()

# Example Game Play
if __name__ == "__main__":
    num_players = 4
    game = MonopolyGame(num_players)
    game.play_game()
