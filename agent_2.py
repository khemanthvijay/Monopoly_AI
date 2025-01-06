import os
import torch
import torch.nn as nn
import torch.optim as optim
from collections import deque
import numpy as np
import random


class ReplayBuffer:
    def __init__(self, max_size=10000):
        self.buffer = deque(maxlen=max_size)

    def add(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        indices = np.random.choice(len(self.buffer), batch_size, replace=False)
        states, actions, rewards, next_states, dones = zip(*[self.buffer[i] for i in indices])
        return (
            np.array(states),
            np.array(actions),
            np.array(rewards),
            np.array(next_states),
            np.array(dones),
        )

    def size(self):
        return len(self.buffer)


class DQNAgent:
    def __init__(
        self, state_size, action_size, model_path="dqn_model.pth", 
        learning_rate=0.001, gamma=0.99, epsilon=1.0, 
        epsilon_min=0.01, epsilon_decay=0.995, replay_buffer_size=10000
    ):
        self.state_size = state_size
        self.action_size = action_size
        self.model_path = model_path
        self.learning_rate = learning_rate
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        
        # Replay buffer
        self.replay_buffer = ReplayBuffer(max_size=replay_buffer_size)

        # Q-Networks
        self.q_network = self.build_model()
        self.target_network = self.build_model()
        self.update_target_network()

        # Optimizer
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=self.learning_rate)

    def build_model(self):
        return nn.Sequential(
            nn.Linear(self.state_size, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, self.action_size),
        )

    def update_target_network(self):
        self.target_network.load_state_dict(self.q_network.state_dict())

    def select_action(self, state, valid_actions):
        if np.random.rand() <= self.epsilon:
            # Explore: Randomly choose one valid action
            action = random.choice(valid_actions)
            print(f"Exploration: Chose action {action} from valid actions {valid_actions}")
            return action

        # Exploit: Choose the action with the highest Q-value among valid actions
        state_tensor = torch.FloatTensor(state).unsqueeze(0)  # Convert state to tensor
        q_values = self.q_network(state_tensor).detach().numpy().flatten()  # Get Q-values for all actions
    
        # Debugging output for Q-values
        print(f"Q-values: {q_values}")

        # Mask invalid actions by setting their Q-values to a very low value
        masked_q_values = np.full_like(q_values, -np.inf)  # Initialize with a very low value
        masked_q_values[valid_actions] = q_values[valid_actions]  # Retain Q-values for valid actions only

        # Debugging output for masked Q-values
        print(f"Masked Q-values: {masked_q_values}")
        print(f"Valid actions: {valid_actions}")

        # Select the action with the highest Q-value
        action = np.argmax(masked_q_values)

        # Debugging output for selected action
        print(f"Exploitation: Selected action {action} with Q-value {masked_q_values[action]}")

        return action

    def store_experience(self, state, action, reward, next_state, done):
        self.replay_buffer.add(state, action, reward, next_state, done)

    def train(self, batch_size):
        if self.replay_buffer.size() < batch_size:
            return
        
        # Sample a batch
        states, actions, rewards, next_states, dones = self.replay_buffer.sample(batch_size)

        max_length = max(len(sublist) for sublist in states)
        padded_states = [
            sublist + [0] * (max_length - len(sublist)) if len(sublist) < max_length else sublist[:max_length]
            for sublist in states]



        # Convert to tensors
        states = np.array(padded_states, dtype=np.float32)
        states = torch.FloatTensor(states)
        for action in actions:
            if action is None:
                break
        actions = np.array(actions, dtype=np.int64).flatten()
        actions = torch.LongTensor(actions)
        rewards = torch.FloatTensor(np.array(rewards, dtype=np.float32))
        next_states = torch.FloatTensor(np.array(next_states, dtype=np.float32))
        dones = torch.FloatTensor(np.array(dones, dtype=np.float32))


        # Q-value updates
        current_q = self.q_network(states).gather(1, actions.unsqueeze(1)).squeeze(1)
        next_q = self.target_network(next_states).max(1)[0]
        target_q = rewards + (1 - dones) * self.gamma * next_q

        # Loss and backpropagation
        loss = nn.MSELoss()(current_q, target_q.detach())
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        # Decay epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def save_model(self):
        torch.save(self.q_network.state_dict(), self.model_path)
        torch.save(self.q_network, "dqn_model_AI.pth")

    def load_model(self):
        if os.path.exists(self.model_path):
            self.q_network.load_state_dict(torch.load(self.model_path))
            self.target_network.load_state_dict(self.q_network.state_dict())
            print("Model loaded successfully.")
        else:
            print("No saved model found.")

