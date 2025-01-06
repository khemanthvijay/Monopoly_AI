# OM
import torch, numpy as np
from main_game import MonopolyGame
class TestClass:
    def __init__(self, model_path=None):
        self.model_path = model_path
        self.game = MonopolyGame(num_players=4, ai_player_id=2, human_player=-1)
        self.total_rewards = []

        if model_path:
            #self.q_network = torch.load(model_path)
            #self.q_network.eval()  # Set to evaluation mode
            self.game.ai_agent.q_network = torch.load(model_path)
            self.game.ai_agent.q_network.eval()
            self.game.ai_agent.epsilon = 0
            
    def play_game(self):
        while not self.game.game_over:
            self.game.take_turn()

        print(f"Total reward: {self.game.total_reward}")
        print(f"Game Round: {self.game.game_round}")
        print(f"Total rounds: {self.game.total_rounds}")  

        print(self.game.players[self.game.ai_player_id].round_completed)

if __name__ == "__main__":
    game = TestClass( model_path= './dqn_model_AI.pth')
    game.play_game()

# 3944,16202, 535, 903, 6500, 258