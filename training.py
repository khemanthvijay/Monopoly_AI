# OM

import torch
import random
from main_game import MonopolyGame  # Import your MonopolyGame class
from agent_2 import DQNAgent  # Import your DQNAgent class

class MonopolyTrainer:
    def __init__(self, num_episodes=1000, save_interval=50, model_path="dqn_model.pth"):
        self.num_episodes = num_episodes
        self.save_interval = save_interval
        self.model_path = model_path
        self.game = MonopolyGame(num_players=4, ai_player_id=3)  # Initialize the Monopoly game
        self.agent = self.game.ai_agent  # Use the same DQNAgent as defined in MonopolyGame
        self.agent.load_model()  # Load the model if it exists
        self.total_rewards = []  # Track rewards for performance evaluation

    def train(self):
        for episode in range(self.num_episodes):
            print(f"Starting Episode {episode + 1}/{self.num_episodes}")
            self.game.reset()  # Reset the game for a new episode
            episode_reward = 0
            self.game.ai_player_id = random.randint(0, 3)
            done = False

            while not done:
                self.game.take_turn()
                done = self.game.game_over
            episode_reward = self.game.total_reward

            # Perform additional training at the end of the game
            for _ in range(10):
                self.agent.train(32)

            # Update the target network periodically
            if episode % 10 == 0:
                self.agent.update_target_network()

            # Save the model periodically
            if episode % self.save_interval == 0:
                self.agent.save_model()

            self.total_rewards.append(episode_reward)
            print(f"Episode {episode + 1} completed with reward: {episode_reward}")

        print("Training Complete!")
        self.agent.save_model()  # Save the final model

    def evaluate_performance(self):
        print("Evaluating performance over last 10 episodes...")
        if len(self.total_rewards) >= 10:
            avg_reward = sum(self.total_rewards[-10:]) / 10
            print(f"Average reward over last 10 episodes: {avg_reward}")
        else:
            print("Not enough episodes completed to evaluate performance.")

if __name__ == "__main__":
    trainer = MonopolyTrainer(num_episodes=500, save_interval=50, model_path="dqn_model.pth")
    trainer.train()
    trainer.evaluate_performance()
