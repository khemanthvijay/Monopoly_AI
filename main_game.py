# OM

from collections import Counter
import numpy as np
import random, time

from agent_2 import DQNAgent
class Player:
    def __init__(self, id, position=1, cash=1000):
        self.id = id
        self.position = position
        self.in_jail = [False, 0]  # [is_in_jail, turns_in_jail]
        self.cash = cash
        self.owned_cards = []
        self.bankrupt = False
        self.max_cash_turns = 0
        self.round_completed = 0

    def move(self, steps, board_size):
        if self.position == 41:
            self.position = 10+steps
        else:
            if self.position+steps >= 41:
                self.position = (self.position+steps)%board_size+1
                self.control_cash(100)  # Passed "Start"
                print(f"Player {self.id} has crossed Start and now has ${self.cash}")
                self.round_completed += 1
            else:
                self.position = (self.position+steps)%board_size
    def control_cash(self, amount):
        self.cash += amount
        if self.cash >= 4000:
            self.cash = 4000 # max
            self.max_cash_turns += 1
        if self.max_cash_turns >=4:
            self.cash = 200
            self.max_cash_turns = 0
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
    def __init__(self, price, position, group):
        self.position = position
        self.price = price
        self.group = group
        self.owner = None
        self.mortgaged = False

class SpecialProperty:
    def __init__(self, position):
        self.position = position
    

class MonopolyGame():
    def __init__(self, num_players=4, ai_player_id=1,human_player = -1):
        self.num_players = num_players
        self.players = [Player(i) for i in range(num_players)]
        self.ai_player_id = ai_player_id
        self.previous_state = []
        self.initialize_board()
        self.current_player_id = 0
        self.dice_value = [0, 0]
        self.game_over = False
        self.board_size = len(self.properties)+len(self.special_properties)
        self.human_player = human_player
        self.buy_options = 0
        self.game_round = 0

        self.ai_agent = DQNAgent(state_size=self.get_state_size(), action_size=9)  # Define state size later.
        self.total_reward = 0
        self.total_rounds = 0

    def initialize_board(self):
        self.properties = [Property(60, 2, 1),
            Property(60, 4, 1),
            Property(200, 6, 0),
            Property(100, 7, 2),
            Property(100, 9, 2),
            Property(120, 10, 2),
            Property(140, 12, 3),
            Property(150, 13, -1),
            Property(140, 14, 3),
            Property(160, 15, 3),
            Property(200, 16, 0),
            Property(180, 17, 4),
            Property(180, 19, 4),
            Property(200, 20, 4),
            Property(220, 22, 5),
            Property(220, 24, 5),
            Property(240, 25, 5),
            Property(200, 26, 0),
            Property(260, 27, 6),
            Property(260, 28, 6),
            Property(150, 29, -1),
            Property(280, 30, 6),
            Property(300, 32, 7),
            Property(300, 33, 7),
            Property(320, 35, 7),
            Property(200, 36, 0),
            Property(350, 38, 8),
            Property(400, 40, 8)
        ]
        self.special_properties = [ SpecialProperty(1),
            SpecialProperty(3),
            SpecialProperty(5),
            SpecialProperty(8),
            SpecialProperty(11),
            SpecialProperty(41),
            SpecialProperty(18),
            SpecialProperty(21),
            SpecialProperty(23),
            SpecialProperty(31),
            SpecialProperty(34),
            SpecialProperty(37),
            SpecialProperty(39)
        ]
    
    def get_state_size(self):
        self.current_state = []
        self.build_state_vector()
        return len(self.current_state)
    
    def reset(self):
        num_players = 4
        self.players = [Player(i) for i in range(num_players)]
        self.current_player_id = 0
        self.dice_value = [0, 0]
        self.game_over = False
        self.previous_state = []
        self.board = self.initialize_board()
        self.total_reward = 0
        self.game_round = 0
        print("Game has been reset.")

    def build_state_vector(self):
        self.previous_state = self.current_state
        self.current_state = []

        for player_id, player in enumerate(self.players):
            self.current_state.extend([
                player.id / len(self.players),
                player.position / self.board_size,
                min(player.cash / 10000, 1),  # 0-1 max $10,000
                1 if player.in_jail[0] else 0,   # Jail status (1 if in jail, 0 if not)
                player.in_jail[1] / 3,           # Jail roll count
                1 if player.bankrupt else 0   # Bankruptcy status
                ])
            
        for property in self.properties:
            self.current_state.extend([
                property.position / self.board_size,
                min(property.price/500,1),      # 0-1 max $1000
                property.group/8,        #max 8
                property.owner/len(self.players) if property.owner is not None else 0
                ])

        for property in self.special_properties:
            if property.position == self.players[self.ai_player_id].position:
                player = 1
            else:
                player = 0
            self.current_state.extend([
                property.position / self.board_size, 
                player
                ])
            
        self.current_state.extend([
                0,  # rent
                0,  # buy_card
                (self.dice_value[0])/6,  # rolled value (initialize with 0)
                (self.dice_value[1])/6,
                1 if self.game_over else 0,  # game over flag
                self.current_player_id/len(self.players)  # current player ID
                ])
        #self.current_state = np.array(self.current_state, dtype=np.float32)
        #print(self.current_state)

    def change_state_Vector(self, change, data):
        #print(f'change state vector for {change}')
        self.build_state_vector()
        if change == 'buy_card':
            self.current_state[-5] = data/self.board_size
        elif change == 'rent':
            self.current_state[-6] = data/2000   # -1 to1 max $2000     
        elif change == 'game_over':
            self.current_state[-2] = data/2  # win -1 lose 2 else 0     

    def take_turn(self):
        self.total_rounds += 1
        player = self.players[self.current_player_id]
        if player.bankrupt:
            self.end_turn()
            return
        if player.in_jail[0] and player.id != self.ai_player_id and self.human_player == -1:
            self.handle_Auto_Jail(player)
        elif player.id == self.ai_player_id:
            self.handle_AI_turn(player)
        elif self.human_player == player.id:
            self.handle_human_turn(player)
        else:
            self.hardcoded_turn(player)
        print(f'Handled all actions for player {player.id}')
        self.end_turn()
        #time.sleep(2)

    def handle_human_turn(self, player):
        if player.in_jail[0]:
            print(f"Player {player.id} is in jail." + f"Roll count: {player.in_jail[1]}")
            if player.in_jail[1] >=3:
                self.pay_jail(player)
            elif player.cash < 100 and player.in_jail[1] <= 3:
                self.wait_jail(player)
            else:
                decision = int(input("Press 1 to pay $200 to get out of jail or 2 to wait in jail."))
                print(f"Decision: {decision}")
                if decision == 1:
                    self.pay_jail(player)
                else:
                    self.wait_jail(player)
        dice = self.roll_dice()
        print(f"Player {player.id} rolled {dice[0]} and {dice[1]}")
        print(f"Player {player.id} moved to {player.in_jail[0]}")
        if player.in_jail[0]:
            if dice[0] == dice[1]:
                player.in_jail = [False, 0]
                self.move_player(player, dice[0] + dice[1], 'roll_dice')
                print(f"Player {player.id} got out of jail by rolling doubles.")
                self.move_player(player, dice[0] + dice[1], 'roll_dice')
            else:
                print(f"Player {player.id} is still in jail.")
                return
        else:
            self.move_player(player, dice[0] + dice[1], 0)

            

    def handle_AI_turn(self, player):
        valid_actions = []
        print(f'initial state vector')
        self.build_state_vector()
        # valid_actions.append(0)
        print(f"Player {player.id}'s Turn")
        if player.in_jail[0]:
            print(f"Player {player.id} is in jail.")
            valid_actions.clear()
            if player.in_jail[1] >= 3:
                valid_actions.append(3)
            else:
                if player.cash >= 200:
                    valid_actions.extend([3,5])
                else:
                    valid_actions.append(5)
        if len(valid_actions) >= 1:
            action = self.ai_agent.select_action(self.current_state, valid_actions)   # build state vector at start of turn
        else:
            action = 0
        self.execute_action(action, valid_actions,player)
    
    def execute_action(self, action, valid_actions, player):
        print(f"Player {player.id} chose action: {action}")
        #time.sleep(2)
        if action in valid_actions:  #  3, 5
            if action == 3:
                self.pay_jail(player)
                print(f'pay jail state vector')
                self.build_state_vector()
                reward = self.calculate_reward(player,'paid_jail', None)
                self.ai_agent.replay_buffer.add(self.previous_state, action, reward, self.current_state,1 if self.players[self.ai_player_id].bankrupt else 0)
            elif action == 5:
               self.wait_jail(player)
        dice = self.roll_dice()
        
        if player.in_jail[0]:
            self.build_state_vector()
            reward = self.calculate_reward(player,'roll_dice', None)
            self.ai_agent.replay_buffer.add(self.previous_state, 0, reward, self.current_state,1 if self.players[self.ai_player_id].bankrupt else 0)
            if dice [0] == dice[1]:
                player.in_jail = [False, 0]
                print(f"Player {player.id} got out of jail by rolling doubles.")
                print(f'luckty state vector')
                self.build_state_vector()
                reward = self.calculate_reward(player,'wait_jail', 'lucky')
                self.ai_agent.replay_buffer.add(self.previous_state, action, reward, self.current_state,1 if self.players[self.ai_player_id].bankrupt else 0)
            else:
                print(f"Player {player.id} is still in jail.")
                print(f'unlucky state vector')
                self.build_state_vector()
                reward = self.calculate_reward(player,'wait_jail', 'unlucky')
                self.ai_agent.replay_buffer.add(self.previous_state, action, reward, self.current_state,1 if self.players[self.ai_player_id].bankrupt else 0)
                # self.end_turn()
                # print(f'end state vector')
                # self.build_state_vector()
                # reward = self.calculate_reward(player,'end_turn', None)
                # self.ai_agent.replay_buffer.add(self.previous_state,2, reward, self.current_state,1 if self.players[self.ai_player_id].bankrupt else 0)
                return
        self.move_player(player, dice[0] + dice[1],action=0)
        

    def move_player(self, player, dice, action):
        player.move(dice, self.board_size)  
        print(f'move state vector')
        self.build_state_vector()
        reward = self.calculate_reward(player,'roll_dice', None)
        self.ai_agent.replay_buffer.add(self.previous_state, 0, reward, self.current_state,1 if self.players[self.ai_player_id].bankrupt else 0)
        print(f"Player {player.id} rolled {dice} and moved to position {player.position} with cash {player.cash}.")
        for prop in self.properties:
            if prop.position == player.position:
                self.handle_property(player, prop)
                break
        for special_prop in self.special_properties:
            if special_prop.position == player.position:
                self.handle_special_card(player, special_prop, dice)
                break
        return

    def handle_property(self, player, prop):
        if prop.owner is None:
            if player.cash >= prop.price:
                if self.ai_player_id == player.id:
                    self.buy_options = 1
                    action = self.ai_agent.select_action(self.current_state, [1,2])
                    
                    if action == 1:
                        print(f"Player {player.id} bought position {player.position} for ${prop.price}.")
                        player.buy_property(prop)
                        self.change_state_Vector('buy_card', prop.position)
                        reward = self.buy_card_reward(player, prop)
                        self.ai_agent.replay_buffer.add(self.previous_state, 1, reward, self.current_state,1 if self.players[self.ai_player_id].bankrupt else 0)
                        return
                elif self.human_player == player.id:
                    action = int(input("Do you want to buy this property? (1 for yes, 2 for no) "))
                    if action == 1:
                        player.buy_property(prop)
                        print(f"Player {player.id} bought position {player.position} for ${prop.price}.")
                        return
                else:
                    if self.decide_to_buy(player, prop):
                        player.buy_property(prop)
                        print(f"Player {player.id} bought position {player.position} for ${prop.price}.")
                    else:
                        print(f"Player {player.id} decided not to buy position {player.position}.")
                return
            else:
                print(f"Player {player.id} does not have enough money to buy position {player.position}.")
                return
        else:
            if player.id !=prop.owner:
                rent =  int((20*prop.price)/100)
                player.control_cash(-rent)
                self.players[prop.owner].control_cash(rent)
                print(f"Player {player.id} paid ${rent} to player {prop.owner} for rent on position {player.position}.")
                if player.id == self.ai_player_id:
                    self.change_state_Vector('rent', -rent)
                    reward = self.calculate_reward(player,'rent_paid', None)
                    self.ai_agent.replay_buffer.add(self.previous_state, 8, reward, self.current_state,1 if self.players[self.ai_player_id].bankrupt else 0)
                elif self.players[prop.owner] == self.ai_player_id:
                    self.change_state_Vector('rent', rent)
                    reward = self.calculate_reward(player,'rent_received', None)
                    self.ai_agent.replay_buffer.add(self.previous_state, 8, reward, self.current_state,1 if self.players[self.ai_player_id].bankrupt else 0)
            

    def decide_to_buy(self,player, current_space):
        if player.cash >= current_space.price:  # Player can afford the property
            if current_space.group in [1, 2, 3]:  # Low-cost, low-rent properties
                if player.cash > 500:
                    buy_probability = 0.8  # High likelihood to buy with more cash
                else:
                    buy_probability = 0.6  # Moderate likelihood to buy with low cash
        
            elif current_space.group in [4, 5, 0, -1]:  # Moderate-cost, good-rent properties
                buy_probability = 0.9  # Always try to buy, regardless of cash
        
            elif current_space.group in [6, 7, 8]:  # High-cost, high-rent properties
                if player.cash > 700:
                    buy_probability = 0.7  # Likely to buy with more cash
                else:
                    buy_probability = 0.3  # Avoid buying with low cash
        
            else:
                buy_probability = 0.0  # Default case, don't buy (e.g., unrecognized group)
                ValueError(f"Unknown property group: {current_space.group}")

            # Decide based on probability
            return random.random() < buy_probability

        return False  # Cannot afford the property

    def pay_jail(self, player):
        if player.in_jail[0]:
            player.control_cash(-100)  # Pay to get out of jail
            player.in_jail = [False, 0]
            print(f"Player {player.id} paid $200 to get out of jail.")
            
    def wait_jail(self, player):
        print(f"Player {player.id} waits in jail.")
        player.in_jail[1] += 1

    def handle_special_card(self, player, special_card,dice):
        if special_card.position == 3 or special_card.position== 18 or special_card.position == 34: # community chest
            if dice < 5:
                player.control_cash(-100)
                if self.ai_player_id == player.id:
                    print(f'special state vector')
                    self.build_state_vector()
                    reward = self.calculate_reward(player,'special_card', 100)
                    self.ai_agent.replay_buffer.add(self.previous_state, 6, reward, self.current_state, 1 if self.players[self.ai_player_id].bankrupt else 0)
            elif dice >=5 and dice < 9:
                self.move_player(player, 4,6) 
            elif dice >= 9:
                player.control_cash(150)
                if self.ai_player_id == player.id:
                    print(f'special state vector')
                    self.build_state_vector()
                    reward = self.calculate_reward(player,'special_card', 150)
                    self.ai_agent.replay_buffer.add(self.previous_state, 6, reward, self.current_state, 1 if self.players[self.ai_player_id].bankrupt else 0)
        elif special_card.position == 5:
            player.control_cash(-200)  # income tax
            if self.ai_player_id == player.id:
                print(f'income tax state vector')
                self.build_state_vector()
                reward = self.calculate_reward(player,'special_card', -200)
                self.ai_agent.replay_buffer.add(self.previous_state, 6, reward, self.current_state, 1 if self.players[self.ai_player_id].bankrupt else 0)
        elif special_card.position == 8 or special_card.position == 23 or special_card.position == 37: # chnace
            if dice < 5:
                player.control_cash(100)
                if self.ai_player_id == player.id:
                    print(f'special state vector')
                    self.build_state_vector()
                    reward = self.calculate_reward(player,'special_card', 100)
                    self.ai_agent.replay_buffer.add(self.previous_state, 6, reward, self.current_state, 1 if self.players[self.ai_player_id].bankrupt else 0)
            elif dice >=5 and dice <= 9:
                player.control_cash(-50)
                if self.ai_player_id == player.id:
                    print(f'special state vector')
                    self.build_state_vector()
                    reward = self.calculate_reward(player,'special_card', -50)
                    self.ai_agent.replay_buffer.add(self.previous_state, 6, reward, self.current_state, 1 if self.players[self.ai_player_id].bankrupt else 0)
            elif dice > 9:
                player.position = 24
                if special_card.position == 37:
                    player.control_cash(100)
                for prop in self.properties:
                    if prop.position == player.position:
                        card = prop
                        break
                if card:
                    self.handle_property(player, prop)
                    
        elif special_card.position == 11 or special_card.position == 21 or special_card.position == 1: #just visiting or free parking #start
            if self.ai_player_id == player.id:
                print(f'special state vector')
                self.build_state_vector()
                reward = self.calculate_reward(player,'special_card', 0)
                self.ai_agent.replay_buffer.add(self.previous_state, 6, reward, self.current_state, 1 if self.players[self.ai_player_id].bankrupt else 0)
            else:
                pass
        elif special_card.position == 39: # luxary tax
            player.control_cash(-100)
            if self.ai_player_id == player.id:
                print(f'special state vector')
                self.build_state_vector()
                reward = self.calculate_reward(player,'special_card', -100)
                self.ai_agent.replay_buffer.add(self.previous_state, 6, reward, self.current_state, 1 if self.players[self.ai_player_id].bankrupt else 0)
        elif special_card.position == 41 or special_card.position == 31: # jail
            print(f"Player {player.id} goes to jail.")
            player.in_jail[0] = True
            player.position = 41
            if self.ai_player_id == player.id:
                print(f'in_jail state vector')
                self.build_state_vector()
                reward = self.calculate_reward(player,'in_jail', None)
                self.ai_agent.replay_buffer.add(self.previous_state, 6, reward, self.current_state, 1 if self.players[self.ai_player_id].bankrupt else 0)
        
    def roll_dice(self):
        self.dice_value = [random.randint(1, 6) ,random.randint(1, 6)]
        return self.dice_value
    
    def calculate_reward(self, player, reason, data):
        reward = 0
        if reason == 'invalid_action':
            reward = -1
        elif reason == 'end_turn':
            if self.buy_options == 1:
                for prop in self.properties:
                    if prop.position == player.position:
                        if prop.owner is None and player.cash >= prop.price + 150:
                            reward = 3
                            break
            else:
                reward = 0.2
        elif reason == 'bankrupt':
            if len(player.owned_cards) > 3 and self.players[self.ai_player_id].round_completed > 4:
                reward = -8
            else:
                reward = -15
            player.bankrupt = True
        elif reason == 'rent_received':
            for prop in self.properties:
                if prop.position == self.players[self.current_player_id].position:
                    rent = int((20*prop.price)/100)
                    break
            min_reward = 2
            max_reward = 6
            min_rent = 12
            max_rent = 80
            reward =min_reward + ((rent - min_rent) * (max_reward - min_reward)) / (max_rent - min_rent)
        elif reason == 'rent_paid':
            for prop in self.properties:
                if prop.position == player.position:
                    rent = int((20*prop.price)/100)
                    break
            min_reward = -2
            max_reward = -6
            min_rent = 12
            max_rent = 80
            reward =min_reward + ((rent - min_rent) * (max_reward - min_reward)) / (max_rent - min_rent)
        elif reason == 'paid_jail':
            reward = 0.5 if player.cash >= 200 else -0.5 # remaining cash
        elif reason == 'wait_jail':
            if player.cash > 600:
                reward = -2
            elif player.cash > 250:
                reward = 1
            else:
                reward = 2 # Encourage waiting only when cash is low
            if data == 'lucky':
                reward += 1
            elif data == 'unlucky':
                reward -= 1
        elif reason == 'rolled_dice':
            reward = 0.5 
        elif reason == 'special_card':
            if data < 0:
                if data > -100:
                    reward = -0.5
                else:
                    reward = -1
            elif data > 0 and data < 100:
                reward = 1
            else:
                reward = 1.5
        elif reason == 'in_jail': # sent to jail
            reward = -1
        return self.reward_scaler(reward)
    def reward_scaler(self, reward):
        min_reward = -15
        max_reward = 15
        target_range = (-1,1)
        scaled_reward = (reward - min_reward) / (max_reward - min_reward)  # Scale to [0, 1]
        if target_range == (-1, 1):
            scaled_reward = 2 * scaled_reward - 1  # Scale to [-1, 1]
        self.total_reward += scaled_reward
        return scaled_reward
    
    def buy_card_reward(self, player, data):
        price = data.price
        
        # Reward and penalty thresholds
        reserve_cash_threshold = 170  # AI needs to keep this much cash to avoid penalties
        early_game_threshold = 5  # AI should aim to buy in the early rounds (before this threshold)
    
        # Early game reward for buying properties
        if player.round_completed <= early_game_threshold:
            early_game_reward = 1.5  # Encouraging early buys
        else:
            early_game_reward = 1.0  # Decrease the incentive after early rounds
            
        # Reward for keeping enough cash after buying the property
        if player.cash >= reserve_cash_threshold:
            cash_reserve_reward = 1.0  # Reward if AI keeps a sufficient cash reserve
        else:
            cash_reserve_reward = -0.5  # Penalize if not enough cash is left after buying

        # Reward for buying the property
        buy_property_reward = (price / 400) * 3  # Scaled reward based on the property price (max 3 for expensive property)

        # Total reward: combining early game reward, cash reserve reward, and property value reward
        reward = early_game_reward * buy_property_reward + cash_reserve_reward

        # Final reward within range -3 to 4 (normalized as per your requirements)
        reward = max(-3, min(4, reward))
        return self.reward_scaler(reward)


    def hardcoded_turn(self, player):
        print(f"Player {player.id}'s Turn")
        dice = self.roll_dice()
        if player.in_jail[0]:
            if dice [0] == dice[1]:
                player.in_jail = [False, 0]
                print(f"Player {player.id} got out of jail by rolling doubles.")
            else:
                print(f"Player {player.id} is still in jail.")
                self.end_turn()
        else:
            player.move(dice[0] + dice[1], self.board_size)
            print(f"Player {player.id} moved to {player.position} with cash {player.cash}.")
            for prop in self.properties:
                if prop.position == player.position:
                    self.handle_property(player, prop)
                    break
            else:
                for special_prop in self.special_properties:
                    if special_prop.position == player.position:
                        self.handle_special_card(player, special_prop, dice[0] + dice[1])
                        break
        return
        
    def handle_Auto_Jail(self, player):
        print(f"Player {player.id} is in jail.")
        player.in_jail[1] += 1
        if player.in_jail[1] >= 3 or player.cash >= 100:
            player.control_cash(-100)  # Pay to get out of jail
            player.in_jail = [False, 0]
            print(f"Player {player.id} paid $100 to get out of jail.")
        else:
            print(f"Player {player.id} waits in jail.")
        
    def end_turn(self):
        if self.current_player_id == self.ai_player_id and self.players[self.ai_player_id].bankrupt == False:
            self.current_player_id = (self.current_player_id + 1) % self.num_players
            print(f'end state vector')
            self.build_state_vector()
            reward = self.calculate_reward(self.players[self.ai_player_id], 'end_turn', None)
            self.ai_agent.replay_buffer.add(self.previous_state,2,reward,self.current_state,1 if self.players[self.ai_player_id].bankrupt else 0 )
        else:
            self.current_player_id = (self.current_player_id + 1) % self.num_players
        self.check_game_over()
        self.check_bankruptcy()
        self.check_round_over()

    def check_round_over(self):
        round_counts = Counter(player.round_completed for player in self.players)
        # Sort rounds by value in descending order
        sorted_rounds = sorted(round_counts.items(), key=lambda x: x[0], reverse=True)
        # # Check for the highest round with at least two players
        for round_value, count in sorted_rounds:
            if count >= 2:
                self.game_round = round_value
                break
            else:
                # If no round has at least two players, choose the second-highest round
                self.game_round = sorted_rounds[1][0] if len(sorted_rounds) > 1 else sorted_rounds[0][0]
                
        print(f"Game Round updated to: {self.game_round}")

    def check_bankruptcy(self):
        player = self.players[self.current_player_id]
        if player.cash <= -50:
            reward = 0
            if player.id == self.ai_player_id:
                reward = self.calculate_reward(player,'bankrupt', None)
            for prop in self.properties:
                if prop.owner == player.id:
                    prop.owner = None
            player.declare_bankruptcy()
            print(f"Player {player.id} declared bankruptcy.")
            if player.id == self.ai_player_id:
                self.change_state_Vector('game_over',2)
                self.ai_agent.replay_buffer.add(self.previous_state, 4, reward, self.current_state, True)


    def check_game_over(self):
        active_players = [player for player in self.players if not player.bankrupt]
        if len(active_players) == 1:
            self.game_over = True
            if active_players[0].id == self.ai_player_id:
                self.change_state_Vector('game_over',1)
                self.ai_agent.replay_buffer.add(self.previous_state, 7, 1, self.current_state, self.game_over)
            print(f"Player {active_players[0].id} wins the game!")

    def play_game(self):
        while not self.game_over:
            self.take_turn()
        print("Game Over!")

if __name__ == "__main__":
    game = MonopolyGame(num_players=4, ai_player_id=3)
    game.play_game()



