import random
import math

ACTIONS = ["UP", "DOWN", "LEFT", "RIGHT", "EXTINGUISH", "STAY"]

class FirefighterAgent:
    def __init__(self, x, y, extinguishing_radius=4):
        self.x = x
        self.y = y
        self.extinguishing_radius = extinguishing_radius
        self.q_table = {}  # Will be replaced with shared Q-table
        self.alpha = 0.1   # Learning rate
        self.gamma = 0.9   # Discount factor
        self.epsilon = 0.2 # Exploration rate
        self.last_reward = 0
        self.extinguished_count = 0

    def get_state(self, env):
        """Detect fires in all directions within visibility range"""
        fire_dirs = []
        for dx in [-2, -1, 0, 1, 2]:
            for dy in [-2, -1, 0, 1, 2]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = self.x + dx, self.y + dy
                if env.in_bounds(nx, ny) and (nx, ny) in env.fire_cells:
                    fire_dirs.append((dx, dy))
        
        return (self.x // 10, self.y // 10,  # Coarse position
                tuple(fire_dirs))

    def _get_fires_in_radius(self, env):
        """Get all fires within extinguishing radius"""
        fires = []
        for dx in range(-self.extinguishing_radius, self.extinguishing_radius + 1):
            for dy in range(-self.extinguishing_radius, self.extinguishing_radius + 1):
                distance = math.sqrt(dx**2 + dy**2)
                if distance > self.extinguishing_radius:
                    continue
                nx, ny = self.x + dx, self.y + dy
                if env.in_bounds(nx, ny) and (nx, ny) in env.fire_cells:
                    fires.append((nx, ny))
        return fires


    def choose_action(self, state):
        """Epsilon-greedy action selection"""
        if random.random() < self.epsilon:
            return random.choice(ACTIONS)
        
        self.q_table.setdefault(state, {a: 0 for a in ACTIONS})
        return max(self.q_table[state].items(), key=lambda x: x[1])[0]

    def update_q(self, state, action, reward, next_state):
        """Q-learning update rule"""
        self.q_table.setdefault(state, {a: 0 for a in ACTIONS})
        self.q_table.setdefault(next_state, {a: 0 for a in ACTIONS})
        
        old_q = self.q_table[state][action]
        max_next_q = max(self.q_table[next_state].values())
        new_q = old_q + self.alpha * (reward + self.gamma * max_next_q - old_q)
        
        self.q_table[state][action] = new_q
        self.last_reward = reward

    def adjacent_cells(self, env):
        """Get walkable adjacent cells"""
        neighbors = []
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
            nx, ny = self.x + dx, self.y + dy
            if env.in_bounds(nx, ny) and env.grid[ny][nx] != "T":
                neighbors.append((nx, ny))
        return neighbors

    def step(self, env):
        state = self.get_state(env)
        action = self.choose_action(state)

        dx, dy = 0, 0
        reward = -0.1  # Small penalty for existing

        if action == "UP":
            dy = -1
        elif action == "DOWN":
            dy = 1
        elif action == "LEFT":
            dx = -1
        elif action == "RIGHT":
            dx = 1
        elif action == "EXTINGUISH":
            extinguished = False
            for fx, fy in self._get_fires_in_radius(env):
                if env.extinguish(fx, fy):
                    self.extinguished_count += 1
                    reward += 10  # Base reward
                    # Bonus for extinguishing multiple fires
                    reward += 5 * len(self._get_fires_in_radius(env))  
                    extinguished = True
            
            if not extinguished:
                reward = -2  # Penalty for failed extinguishing attempt

        # Movement logic (unchanged)
        new_x, new_y = self.x + dx, self.y + dy
        if env.in_bounds(new_x, new_y) and env.grid[new_y][new_x] != "T":
            self.x, self.y = new_x, new_y

        next_state = self.get_state(env)
        self.update_q(state, action, reward, next_state)