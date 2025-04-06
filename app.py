import pygame
import sys
import random
from model import Environment, GRID_SIZE
from agents import FirefighterAgent

# Constants
CELL_SIZE = 4
WINDOW_SIZE = GRID_SIZE * CELL_SIZE
COLORS = {
    " ": (40, 40, 40),       # Burned areas
    "F": (255, 80, 80),      # Active fire
    "A1": (80, 180, 255),    # Agent 1 (Blue)
    "A2": (80, 180, 255),    # Agent 2 (Orange)
    "A3": (80, 180, 255),    # Agent 3 (Purple)
    "T": (50, 120, 50)       # Trees
}

def create_simulation(load_q=None, tree_density=0.3):
    """Initialize simulation with shared Q-learning"""
    env = Environment(tree_density=tree_density)
    
    # Shared Q-table for cooperative learning
    shared_q = {} if load_q is None else load_q
    
    # Strategic starting positions
    agents = [
        FirefighterAgent(30, 30),
        FirefighterAgent(GRID_SIZE-30, 30),
        FirefighterAgent(GRID_SIZE//2, GRID_SIZE-30)
    ]
    
    for i, agent in enumerate(agents):
        agent.q_table = shared_q
        env.add_agent(agent)
    
    return env, agents

def draw_environment(env, agents, screen):
    """Render the grid with optimized drawing"""
    # Draw terrain
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            cell = env.grid[y][x]
            color = COLORS.get(cell, (255,255,255))
            pygame.draw.rect(screen, color, (x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE, CELL_SIZE))
    
    # Draw agents on top
    for i, agent in enumerate(agents):
        color = COLORS[f"A{i+1}"]
        center_x = agent.x * CELL_SIZE + CELL_SIZE//2
        center_y = agent.y * CELL_SIZE + CELL_SIZE//2
        pygame.draw.circle(screen, color, (center_x, center_y), CELL_SIZE//2)

def draw_stats(env, agents, episode, font, screen):
    """Display real-time metrics"""
    trees = sum(row.count('T') for row in env.grid)
    stats = [
        f"Episode: {episode}",
        f"Fires active: {len(env.fire_cells)}",
        f"Total extinguished: {sum(a.extinguished_count for a in agents)}",
        f"Q-table size: {len(agents[0].q_table)}"
    ]
    
    for i, text in enumerate(stats):
        text_surface = font.render(text, True, (255, 255, 255))
        screen.blit(text_surface, (10, 10 + i * 20))

def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
    pygame.display.set_caption("Cooperative Firefighting RL")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont('Arial', 16)
    
    # Initialize
    env, agents = create_simulation()
    episode = 1
    running = True
    
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  # Reset manually
                    env, agents = create_simulation(load_q=agents[0].q_table)
                    episode += 1
        
        # Simulation step
        env.step()
        
        # Rendering
        draw_environment(env, agents, screen)
        draw_stats(env, agents, episode, font, screen)
        pygame.display.flip()
        
        # Reset conditions
        if env.fire_engulfed():
            print(f"Episode {episode} ended. Restarting...")
            episode += 1
            env, agents = create_simulation(load_q=agents[0].q_table)
        
        clock.tick(100)  # Cap at 30 FPS

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()