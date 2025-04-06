import random
import math

GRID_SIZE = 150

class Environment:
    def __init__(self, tree_density=0.3, fire_spread_radius=3, spread_delay=30):
        """
        Initialize the environment with:
        - tree_density: Percentage of grid covered by trees (0-1)
        - fire_spread_radius: How many cells fire can jump (1=adjacent only)
        - spread_delay: Steps between spread events (higher=slower spread)
        """
        self.grid_width = GRID_SIZE
        self.grid_height = GRID_SIZE
        self.grid = [[" " for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        
        # Fire spread parameters
        self.fire_spread_radius = max(1, min(fire_spread_radius, 5))  # Clamped 1-5
        self.spread_delay = max(1, spread_delay)  # Minimum 1 step delay
        self.spread_timer = 0
        
        # Generate environment
        self._place_spaced_trees(tree_density)
        self.fire_cells = set()
        self.agents = []
        self._start_fires(num_fires=5)

    def _place_spaced_trees(self, density):
        """Place trees ensuring no two touch (3x3 area check)"""
        positions = [(x, y) for y in range(GRID_SIZE) for x in range(GRID_SIZE)]
        random.shuffle(positions)
        
        trees_placed = 0
        target_trees = int(GRID_SIZE * GRID_SIZE * density)
        
        for x, y in positions:
            if trees_placed >= target_trees:
                break
                
            # Check 3x3 neighborhood
            can_place = True
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                        if self.grid[ny][nx] == "T":
                            can_place = False
                            break
                if not can_place:
                    break
            
            if can_place:
                self.grid[y][x] = "T"
                trees_placed += 1

    def _start_fires(self, num_fires):
        """Ignite random trees, ensuring they're spaced apart"""
        tree_locations = [(x, y) for y in range(GRID_SIZE) for x in range(GRID_SIZE) 
                         if self.grid[y][x] == "T"]
        
        # Ensure fires start spaced out
        selected = []
        attempts = 0
        while len(selected) < min(num_fires, len(tree_locations)) and attempts < 100:
            x, y = random.choice(tree_locations)
            if all(math.sqrt((x-sx)**2 + (y-sy)**2) > self.fire_spread_radius 
                  for (sx, sy) in selected):
                selected.append((x, y))
                self._ignite_tree(x, y)
            attempts += 1

    def _ignite_tree(self, x, y):
        """Convert a tree to fire"""
        if self.grid[y][x] == "T":
            self.grid[y][x] = "F"
            self.fire_cells.add((x, y))

    def _get_trees_in_radius(self, x, y):
        """Find all trees within fire spread radius (circular area)"""
        trees = []
        for dy in range(-self.fire_spread_radius, self.fire_spread_radius+1):
            for dx in range(-self.fire_spread_radius, self.fire_spread_radius+1):
                nx, ny = x + dx, y + dy
                distance = math.sqrt(dx**2 + dy**2)
                if (0 <= nx < self.grid_width and 
                    0 <= ny < self.grid_height and
                    distance <= self.fire_spread_radius and
                    self.grid[ny][nx] == "T"):
                    trees.append((nx, ny))
        return trees

    def step(self):
        """Progress simulation by one step"""
        self.spread_timer += 1
        
        # 1. Handle agent movements/actions
        for agent in self.agents:
            if self.grid[agent.y][agent.x] == "A":
                self.grid[agent.y][agent.x] = " "
    
    # Let each agent take their turn
        for agent in self.agents:
            agent.step(self)
        
        # Update all agents' new positions
        for agent in self.agents:
            if self.in_bounds(agent.x, agent.y) and self.grid[agent.y][agent.x] == " ":
                self.grid[agent.y][agent.x] = "A"

        # 2. Spread fire only when timer reaches delay
        if self.spread_timer >= self.spread_delay:
            self.spread_timer = 0
            new_fires = set()
            
            for x, y in self.fire_cells:
                for nx, ny in self._get_trees_in_radius(x, y):
                    new_fires.add((nx, ny))
            
            for x, y in new_fires:
                self._ignite_tree(x, y)

    # Utility methods
    def add_agent(self, agent):
        """Add an agent to the environment"""
        if self.grid[agent.y][agent.x] == " ":  # Ensure starting position is empty
            self.agents.append(agent)
            self.grid[agent.y][agent.x] = "A"
        else:
            # Find nearest empty spot if default position is occupied
            for radius in range(1, 10):
                for dx in range(-radius, radius+1):
                    for dy in range(-radius, radius+1):
                        nx, ny = agent.x + dx, agent.y + dy
                        if self.in_bounds(nx, ny) and self.grid[ny][nx] == " ":
                            agent.x, agent.y = nx, ny
                            self.agents.append(agent)
                            self.grid[ny][nx] = "A"
                            return

    def in_bounds(self, x, y):
        """Check if coordinates are within grid"""
        return 0 <= x < self.grid_width and 0 <= y < self.grid_height

    def extinguish(self, x, y):
        """Extinguish fire and return True if successful"""
        if (x, y) in self.fire_cells:
            self.grid[y][x] = " "  # Convert to empty space
            self.fire_cells.remove((x, y))
            return True
        return False

    def fire_engulfed(self):
        """Check if fire has taken over too much of the grid"""
        trees_remaining = 0
        threshold = self.grid_width * self.grid_height * 0.02  # 10%
        
        # Fast row-by-row count with early exit
        for row in self.grid:
            trees_remaining += row.count('T')
            if trees_remaining >= threshold:
                return False
        
        return True