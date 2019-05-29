"""
Simple 2d world where the player can interact with the items in the world.
"""

__author__ = ""
__date__ = ""
__version__ = "1.1.0"
__copyright__ = "The University of Queensland, 2019"

import tkinter as tk
import random
from collections import namedtuple
from tkinter import simpledialog
import pymunk

from block import Block, ResourceBlock, BREAK_TABLES, LeafBlock, TrickCandleFlameBlock,CraftingTableBlock,HiveBlock,FurnaceBlock
from grid import Stack, Grid, SelectableGrid, ItemGridView
from item import Item, SimpleItem, HandItem, BlockItem, MATERIAL_TOOL_TYPES, TOOL_DURABILITIES, ToolItem, FoodItem, FOOD_STRENGTH
from player import Player
from dropped_item import DroppedItem
from crafting import GridCrafter, CraftingWindow
from world import World
from core import positions_in_range
from game import GameView, WorldViewRouter
from mob import Mob,Bird,Sheep,Bee,BEE_SWARM_DISTANCE

BLOCK_SIZE = 2**5
GRID_WIDTH = 2**5
GRID_HEIGHT = 2**4

# Task 3/Post-grad only:
# Class to hold game data that is passed to each thing's step function
# Normally, this class would be defined in a separate file
# so that type hinting could be used on PhysicalThing & its
# subclasses, but since it will likely need to be extended
# for these tasks, we have defined it here
GameData = namedtuple('GameData', ['world', 'player'])


def create_block(*block_id):
    """(Block) Creates a block (this function can be thought of as a block factory)

    Parameters:
        block_id (*tuple): N-length tuple to uniquely identify the block,
        often comprised of strings, but not necessarily (arguments are grouped
        into a single tuple)

    Examples:
        >>> create_block("leaf")
        LeafBlock()
        >>> create_block("stone")
        ResourceBlock('stone')
        >>> create_block("mayhem", 1)
        TrickCandleFlameBlock(1)
    """
    if len(block_id) == 1:
        block_id = block_id[0]
        if block_id == "leaf":
            return LeafBlock()
        elif block_id in BREAK_TABLES:
            return ResourceBlock(block_id, BREAK_TABLES[block_id])
        elif block_id == "crafting_table":
            return CraftingTableBlock()
        elif block_id == "honey":
            return ResourceBlock(block_id, BREAK_TABLES[block_id])
        elif block_id == "hive":
            return HiveBlock()
        elif block_id =="furnace":
            return FurnaceBlock()

    elif block_id[0] == 'mayhem':
        return TrickCandleFlameBlock(block_id[1])

    raise KeyError(f"No block defined for {block_id}")


def create_item(*item_id):
    """(Item) Creates an item (this function can be thought of as a item factory)

    Parameters:
        item_id (*tuple): N-length tuple to uniquely identify the item,
        often comprised of strings, but not necessarily (arguments are grouped
        into a single tuple)

    Examples:
        >>> create_item("dirt")
        BlockItem('dirt')
        >>> create_item("hands")
        HandItem('hands')
        >>> create_item("pickaxe", "stone")  # *without* Task 2.1.2 implemented
        Traceback (most recent call last):
        ...
        NotImplementedError: "Tool creation is not yet handled"
        >>> create_item("pickaxe", "stone")  # *with* Task 2.1.2 implemented
        ToolItem('stone_pickaxe')
    """
    if len(item_id) == 2:

        if item_id[0] in MATERIAL_TOOL_TYPES and item_id[
                1] in TOOL_DURABILITIES:
            return ToolItem(f"{item_id[1]}_{item_id[0]}", item_id[1],
                            TOOL_DURABILITIES[item_id[1]])
        elif item_id[0] == "food":
            return FoodItem(item_id[1], FOOD_STRENGTH[item_id[1]])
    elif len(item_id) == 1:

        item_type = item_id[0]

        if item_type == "hands":
            return HandItem("hands")

        elif item_type == "stick":
            return BlockItem(item_type)

        # Task 1.4 Basic Items: Create wood & stone here
        elif item_type in ITEM_COLOURS.keys():
            return BlockItem(item_type)

    raise KeyError(f"No item defined for {item_id}")


# Task 1.3: Implement StatusView class here
class StatusView(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.health = tk.DoubleVar()
        self.food = tk.DoubleVar()
        tk.Label(
            self,
            text="health:",
            height=2,
        ).pack(side=tk.LEFT)
        tk.Label(
            self,
            textvariable=self.health,
            height=2,
        ).pack(side=tk.LEFT)
        tk.Label(self, textvariable=self.food, height=2).pack(side=tk.RIGHT)
        tk.Label(self, text="food:", height=2).pack(side=tk.RIGHT)

    def set_health(self, health):
        self.health.set(int(health * 2) / 2)

    def set_food(self, food):
        self.food.set(int(food * 2) / 2)


BLOCK_COLOURS = {
    'diamond': 'blue',
    'dirt': '#552015',
    'stone': 'grey',
    'wood': '#723f1c',
    'leaves': 'green',
    'crafting_table': 'pink',
    'furnace': 'black',
    "wool":"#FFCEEB",
    "hive":"purple",
    "honey":"orange"
}

ITEM_COLOURS = {
    'diamond': 'blue',
    'dirt': '#552015',
    'stone': 'grey',
    'wood': '#723f1c',
    'apple': '#ff0000',
    'leaves': 'green',
    'crafting_table': 'pink',
    'furnace': 'black',
    'cooked_apple': 'red4',
    "wool":"#FFCEEB",
    "honey":"orange"
}
# 2x2 Crafting Recipes
CRAFTING_RECIPES_2x2 = [
    (
        (
            (None, 'wood'), 
            (None, 'wood')
        ), 
        Stack(create_item('stick'), 4)
    ),
    (
        (
            ('wood', 'wood'),
            (None, None)
        ),
        Stack(create_item('stick'), 4)
    ),
    (
        (
            ('wood', None),
            ('wood', None)
        ),
        Stack(create_item('stick'), 4)
    ),
    (
        (
            (None, None),
            ('wood', 'wood')
        ),
        Stack(create_item('stick'), 4)
    ),
    (
        (
            ('wood', 'wood'), 
            ('wood', 'wood')
        ),
        Stack(create_item('crafting_table'), 1)
    ),
    (
        (
            ('leaves', 'leaves'),
            ('leaves', 'leaves')
        ),
        Stack(create_item('leaves'), 4)
    )
]

# 3x3 Crafting Recipes
CRAFTING_RECIPES_3x3 = {
    (
        (
            (None, None, None),
            (None, 'wood', None),
            (None, 'wood', None)
        ),
        Stack(create_item('stick'), 16)
    ),
    (
        (
            ('wood', 'wood', 'wood'),
            (None, 'stick', None),
            (None, 'stick', None)
        ),
        Stack(create_item('pickaxe', 'wood'), 1)
    ),
    (
        (
            ('wood', 'wood', None),
            ('wood', 'stick', None),
            (None, 'stick', None)
        ),
        Stack(create_item('axe', 'wood'), 1)
    ),
    (
        (
            (None, 'wood', None),
            (None, 'stick', None),
            (None, 'stick', None)
        ),
        Stack(create_item('shovel', 'wood'), 1)
    ),
    (
        (
            (None, 'stone', None),
            (None, 'stone', None),
            (None, 'stick', None)
        ),
        Stack(create_item('sword', 'wood'), 1)
    ),
    (
        (
            ('stone', 'stone', 'stone'),
            ('stone', None, 'stone'),
            ('stone', 'stone', 'stone')
        ),
        Stack(create_item('furnace'), 1)
    )
}

SMELTING_RECIPES_1x2=[
    (
        (
            ('wood', 'apple'),
        ),
        Stack(create_item('food',"cooked_apple"), 1)
    ),

]
def load_simple_world(world):
    """Loads blocks into a world

    Parameters:
        world (World): The game world to load with blocks
    """
    block_weights = [
        (100, 'dirt'),
        (30, 'stone'),
    ]

    cells = {}

    ground = []

    width, height = world.get_grid_size()

    for x in range(width):
        for y in range(height):
            if x < 22:
                if y <= 8:
                    continue
            else:
                if x + y < 30:
                    continue

            ground.append((x, y))

    weights, blocks = zip(*block_weights)
    kinds = random.choices(blocks, weights=weights, k=len(ground))

    for cell, block_id in zip(ground, kinds):
        cells[cell] = create_block(block_id)

    trunks = [(3, 8), (3, 7), (3, 6), (3, 5)]

    for trunk in trunks:
        cells[trunk] = create_block('wood')

    leaves = [(4, 3), (3, 3), (2, 3), (4, 2), (3, 2), (2, 2), (4, 4), (3, 4),
              (2, 4)]

    for leaf in leaves:
        cells[leaf] = create_block('leaf')

    for cell, block in cells.items():
        # cell -> box
        i, j = cell

        world.add_block_to_grid(block, i, j)

    world.add_block_to_grid(create_block("mayhem", 0), 14, 8)

    world.add_mob(Bird("friendly_bird", (12, 12)), 400, 100)
    world.add_mob(Sheep("friendly_sheep", (30, 30)),200 , 100)
    for i in range(5):
        rx=random.randint(-BEE_SWARM_DISTANCE, BEE_SWARM_DISTANCE)
        ry=random.randint(-BEE_SWARM_DISTANCE, BEE_SWARM_DISTANCE)
        world.add_mob(Bee("foe_bee", (8, 8)), 300+rx, 30+ry)
    world.add_block_to_grid(create_block("hive"),15,8)
    world.add_block_to_grid(create_block("honey"),16,8)
    world.add_block_to_grid(create_block("honey"),8,8)

class Ninedraft:
    """High-level app class for Ninedraft, a 2d sandbox game"""

    def __init__(self, master):
        """Constructor

        Parameters:
            master (tk.Tk): tkinter root widget
        """

        self._master = master
        self._world = World((GRID_WIDTH, GRID_HEIGHT), BLOCK_SIZE)
        self._master.title("Ninedraft")
        load_simple_world(self._world)

        self._player = Player()
        self._world.add_player(self._player, 250, 150)

        self._world.add_collision_handler(
            "player", "item", on_begin=self._handle_player_collide_item)
        self._world.add_collision_handler("player","mob",on_post_solve=self._handle_player_collide_mob)
        self._hot_bar = SelectableGrid(rows=1, columns=10)
        self._hot_bar.select((0, 0))

        starting_hotbar = [
            Stack(create_item("dirt"), 20),
            Stack(create_item("crafting_table"), 1),
            Stack(create_item("furnace"), 1),
            Stack(create_item('axe', 'wood'), 1),
            Stack(create_item('pickaxe', 'golden'), 1),
        ]

        for i, item in enumerate(starting_hotbar):
            self._hot_bar[0, i] = item

        self._hands = create_item('hands')

        starting_inventory = [
            ((1, 5), Stack(Item('dirt'), 10)),
            ((0, 2), Stack(Item('wood'), 10)),
            ((0, 4), Stack(Item('stone'), 20)),
        ]
        self._inventory = Grid(rows=3, columns=10)
        for position, stack in starting_inventory:
            self._inventory[position] = stack

        self._crafting_window = None
        self._master.bind(
            "e", lambda e: self.run_effect(('crafting', 'basic')))

        self._view = GameView(master, self._world.get_pixel_size(),
                              WorldViewRouter(BLOCK_COLOURS, ITEM_COLOURS))
        self._view.pack()

        # Task 1.2 Mouse Controls: Bind mouse events here
        self._master.bind("<Motion>", self._mouse_move)
        self._master.bind("<1>", self._left_click)
        self._master.bind("<3>", self._right_click)

        # Task 1.3: Create instance of StatusView here
        self.status_view = StatusView(self._master)
        self.status_view.pack()
        self.status_view.set_food(self._player.get_food())
        self.status_view.set_health(self._player.get_health())

        self._hot_bar_view = ItemGridView(master, self._hot_bar.get_size())
        self._hot_bar_view.pack(side=tk.TOP, fill=tk.X)

        # Task 1.5 Keyboard Controls: Bind to space bar for jumping here
        self._master.bind("<space>", lambda x: self._jump())

        self._master.bind("a", lambda e: self._move(-1, 0))
        self._master.bind("<Left>", lambda e: self._move(-1, 0))
        self._master.bind("d", lambda e: self._move(1, 0))
        self._master.bind("<Right>", lambda e: self._move(1, 0))
        self._master.bind("s", lambda e: self._move(0, 1))
        self._master.bind("<Down>", lambda e: self._move(0, 1))
        self._master.bind("w", lambda e: self._move(0, -1))
        self._master.bind("<Up>", lambda e: self._move(0, -1))
        # Task 1.5 Keyboard Controls: Bind numbers to hotbar activation here
        for i in range(10):
            self._master.bind(
                str((i + 1) % 10),
                (lambda x: lambda e: self._activate_item(x))(i))

        # Task 1.6 File Menu & Dialogs: Add file menu here
        self.menu = tk.Menu(self._master)
        file_bar = tk.Menu(self.menu)
        file_bar.add_command(label="New Game", command=self._restart)
        file_bar.add_command(label="Exit", command=self._quit)

        self.menu.add_cascade(label='File', menu=file_bar)
        self._master.config(menu=self.menu)

        self._target_in_range = False
        self._target_position = 0, 0

        self.redraw()

        self.step()

    def _quit(self):
        result = simpledialog.messagebox.askyesno(
            title='quit', message='Do you really want to quit?')
        if result:
            self._master.quit()

    def _restart(self):
        result = simpledialog.messagebox.askyesno(
            title='restart', message='Do you really want to restart?')
        if result:
            self._master.destroy()
            root = tk.Tk()
            self.__init__(root)
            root.mainloop()

    def redraw(self):
        self._view.delete(tk.ALL)

        # physical things
        self._view.draw_physical(self._world.get_all_things())

        # target
        target_x, target_y = self._target_position
        target = self._world.get_block(target_x, target_y)
        cursor_position = self._world.grid_to_xy_centre(
            *self._world.xy_to_grid(target_x, target_y))

        # Task 1.2 Mouse Controls: Show/hide target here
        if target and self._target_in_range:
            self._view.show_target(self._player.get_position(),
                                   cursor_position)
        else:
            self._view.hide_target()

        # Task 1.3 StatusView: Update StatusView values here
        self.status_view.set_food(self._player.get_food())
        self.status_view.set_health(self._player.get_health())

        # hot bar
        self._hot_bar_view.render(self._hot_bar.items(),
                                  self._hot_bar.get_selected())

    def step(self):
        data = GameData(self._world, self._player)
        self._world.step(data)
        self.check_target()
        self.redraw()

        # Task 1.6 File Menu & Dialogs: Handle the player's death if necessary
        # ...

        self._master.after(15, self.step)

    def _move(self, dx, dy):
        velocity = self._player.get_velocity()
        self._player.set_velocity((velocity.x + dx * 80, velocity.y + dy * 80))

    def _jump(self):
        velocity = self._player.get_velocity()
        # Task 1.4: Update the player's velocity here
        self._player.set_velocity((velocity[0] * 0.8, velocity[1] - 200))

    def mine_block(self, block, x, y):
        luck = random.random()

        active_item, effective_item = self.get_holding()

        was_item_suitable, was_attack_successful = block.mine(
            effective_item, active_item, luck)

        effective_item.attack(was_attack_successful)

        if block.is_mined():
            # Task 1.2 Mouse Controls: Reduce the player's food/health appropriately
            if self._player.get_food() > 0:
                self._player.change_food(-1)
            else:
                self._player.change_health(-1)

            # Task 1.2 Mouse Controls: Remove the block from the world & get its drops
            self._world.remove_block(block)

            drops = block.get_drops(random.random(), True)
            if not drops:
                return

            x0, y0 = block.get_position()

            for i, (drop_category, drop_types) in enumerate(drops):
                print(f'Dropped {drop_category}, {drop_types}')

                if drop_category == "item":
                    physical = DroppedItem(create_item(*drop_types))

                    # this is so bleh
                    x = x0 - BLOCK_SIZE // 2 + 5 + (
                        i % 3) * 11 + random.randint(0, 2)
                    y = y0 - BLOCK_SIZE // 2 + 5 + (
                        (i // 3) % 3) * 11 + random.randint(0, 2)

                    self._world.add_item(physical, x, y)
                elif drop_category == "block":
                    self._world.add_block(create_block(*drop_types), x, y)
                elif drop_category == "mob":
                    self._world.add_mob(Bee("foe_bee",(8,8)),x,y)
                else:
                    raise KeyError(f"Unknown drop category {drop_category}")

    def get_holding(self):
        active_stack = self._hot_bar.get_selected_value()
        active_item = active_stack.get_item() if active_stack else self._hands

        effective_item = active_item if active_item.can_attack(
        ) else self._hands

        return active_item, effective_item

    def check_target(self):
        # select target block, if possible
        active_item, effective_item = self.get_holding()

        pixel_range = active_item.get_attack_range(
        ) * self._world.get_cell_expanse()

        self._target_in_range = positions_in_range(
            self._player.get_position(), self._target_position, pixel_range)

    def _mouse_move(self, event):
        self._target_position = event.x, event.y
        self.check_target()

    def _left_click(self, event):
        # Invariant: (event.x, event.y) == self._target_position
        #  => Due to mouse move setting target position to cursor
        x, y = self._target_position
        mobs=self._world.get_mobs(x,y,2.0)
        for mob in mobs:
            if mob.get_id() is "friendly_sheep":
                print('Dropped block, wool')
                physical = DroppedItem(create_item("wool"))

                # this is so bleh
                x0 = x - BLOCK_SIZE // 2 + 5 +  11 + random.randint(0, 2)
                y0 = y - BLOCK_SIZE // 2 + 5 + 11 + random.randint(0, 2)

                self._world.add_item(physical, x0, y0)
            elif mob.get_id() is "foe_bee":
                print(f"{self._player} attack a bee,damage 1 hit")
                mob.attack(True)
                self._player.change_health(-1)
                if mob.is_dead:
                    print("A bee is deaded")
                    self._world.remove_mob(mob)

        target = self._world.get_thing(x, y)
        if not target:
            return
            
        if self._target_in_range:
            block = self._world.get_block(x, y)
            if block:
                self.mine_block(block, x, y)

    def _trigger_crafting(self, craft_type):
        print(f"Crafting with {craft_type}")
        if craft_type in ("basic","crafting_table","furnace"):
            if craft_type =="basic":
                crafter = GridCrafter(CRAFTING_RECIPES_2x2)
            elif craft_type =="crafting_table":
                crafter = GridCrafter(CRAFTING_RECIPES_3x3, rows=3,columns=3)
            elif craft_type =="furnace":
                crafter = GridCrafter(SMELTING_RECIPES_1x2, rows=1,columns=2)
            self._crafting_window = CraftingWindow(
                self._master, "Smelt", self._hot_bar, self._inventory, crafter, mode="smelting" if craft_type=="furnace" else "normal")
        

    def run_effect(self, effect):
        if len(effect) == 2:
            if effect[0] == "crafting":
                craft_type = effect[1]

                if craft_type == "basic":
                    print("Can't craft much on a 2x2 grid :/")

                elif craft_type == "crafting_table":
                    print("Let's get our kraft® on! King of the brands")
                elif craft_type =="furnace":
                    print("Let's smelting by yourself")
                self._trigger_crafting(craft_type)
                return
            elif effect[0] in ("food", "health"):
                stat, strength = effect
                print(f"Gaining {strength} {stat}!")
                getattr(self._player, f"change_{stat}")(strength)
                return

        raise KeyError(f"No effect defined for {effect}")

    def _right_click(self, event):
        print("Right click")

        x, y = self._target_position
        target = self._world.get_thing(x, y)
        if target:
            # use this thing
            print(f'using {target}')
            effect = target.use()
            print(f'used {target} and got {effect}')

            if effect:
                self.run_effect(effect)

        else:
            # place active item
            selected = self._hot_bar.get_selected()

            if not selected:
                return

            stack = self._hot_bar[selected]
            drops = stack.get_item().place()

            stack.subtract(1)
            if stack.get_quantity() == 0:
                # remove from hotbar
                self._hot_bar[selected] = None

            if not drops:
                return

            # handling multiple drops would be somewhat finicky, so prevent it
            if len(drops) > 1:
                raise NotImplementedError(
                    "Cannot handle dropping more than 1 thing")

            drop_category, drop_types = drops[0]

            x, y = event.x, event.y
            if drop_category == "block":
                existing_block = self._world.get_block(x, y)

                if not existing_block:
                    self._world.add_block(create_block(drop_types[0]), x, y)
                else:
                    raise NotImplementedError(
                        "Automatically placing a block nearby if the target cell is full is not yet implemented"
                    )

            elif drop_category == "effect":
                self.run_effect(drop_types)

            else:
                raise KeyError(f"Unknown drop category {drop_category}")

    def _activate_item(self, index):
        print(f"Activating {index}")

        self._hot_bar.toggle_selection((0, index))

    def _handle_player_collide_item(self, player: Player,
                                    dropped_item: DroppedItem, data,
                                    arbiter: pymunk.Arbiter):
        """Callback to handle collision between the player and a (dropped) item. If the player has sufficient space in
        their to pick up the item, the item will be removed from the game world.

        Parameters:
            player (Player): The player that was involved in the collision
            dropped_item (DroppedItem): The (dropped) item that the player collided with
            data (dict): data that was added with this collision handler (see data parameter in
                         World.add_collision_handler)
            arbiter (pymunk.Arbiter): Data about a collision
                                      (see http://www.pymunk.org/en/latest/pymunk.html#pymunk.Arbiter)
                                      NOTE: you probably won't need this
        Return:
             bool: False (always ignore this type of collision)
                   (more generally, collision callbacks return True iff the collision should be considered valid; i.e.
                   returning False makes the world ignore the collision)
        """

        item = dropped_item.get_item()

        if self._hot_bar.add_item(item):
            print(f"Added 1 {item!r} to the hotbar")
        elif self._inventory.add_item(item):
            print(f"Added 1 {item!r} to the inventory")
        else:
            print(f"Found 1 {item!r}, but both hotbar & inventory are full")
            return True

        self._world.remove_item(dropped_item)
        return False

    def _handle_player_collide_mob(self, player: Player, mob: Mob, data,arbiter: pymunk.Arbiter):
        if mob.get_id()=="foe_bee":
            print(f"{self._player} touch a bee,get 1 damage")
            self._player.change_health(-1)

# Task 1.1 App class: Add a main function to instantiate the GUI here
def main():
    root = tk.Tk()
    Ninedraft(root)
    tk.mainloop()


if __name__ == "__main__":
    main()
