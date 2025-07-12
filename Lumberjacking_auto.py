# Razor Enhanced Lumberjacking Script (v8.6 - Y-Coordinate Boundary)
#
# What it does:
# 1. Prompts you to target your axe to ensure a stable start.
# 2. Uses the robust PathFinding module for all movement.
# 3. Scans for the nearest tree, ignoring any trees outside the defined boundaries.
# 4. Remembers which trees are depleted to avoid getting stuck.
# 5. Automatically finds and equips a new axe if your current one breaks.
# 6. When your backpack is full, it makes boards. If still full, it runs to your house and deposits.
# 7. After depositing, it returns to a static, safe spot in the forest.
# 8. If attacked, it will flee to your house for safety.
#
# How to use:
# 1. IMPORTANT: Fill out the house and forest coordinates in the Configuration section.
# 2. Place this script in your Razor Enhanced 'Scripts' folder.
# 3. Stand in a forested area and run the script. It will prompt you for your axe.
# 4. To stop, you must manually stop it from the Razor Enhanced scripts tab.

import sys
import math

# --- Configuration ---

# The coordinates of a safe spot at your house (e.g., on your porch).
HOUSE_X = 1658
HOUSE_Y = 1225

# A static, safe coordinate in the forest to return to after banking.
FOREST_RETURN_X = 1661
FOREST_RETURN_Y = 1255

# The serial number of your secure crate for unloading.
# Use Razor's inspector to get this number (e.g., 0x400123AB)
CRATE_SERIAL = 0x79595453

# The health percentage below which the script will flee to the house.
FLEE_HEALTH_PERCENT = 75

# Item IDs
AXE_GRAPHICS = [0x0F49, 0x0F47, 0x0F45, 0x13FB]
LOG_GRAPHIC = 0x1BDD
BOARD_GRAPHIC = 0x1BD7

# The radius (in tiles) around the player to scan for trees.
TREE_SEARCH_RADIUS = 15

# The script will stop if your weight is this close to your maximum weight.
WEIGHT_LIMIT_OFFSET = 25

# Delay in milliseconds after each chop/craft attempt.
ACTION_DELAY = 3500

# The time (in milliseconds) to wait for your character to walk back from the house.
RETURN_WALK_TIMEOUT = 30000

# A list of static tile IDs for various tree types.
TREE_GRAPHICS = [
    0x0CCA, 0x0CCB, 0x0CCC, 0x0CCD, 0x0CD0, 0x0CD3, 0x0CD6, 0x0CD8,
    0x0CDA, 0x0CDD, 0x0CE0, 0x0CE3, 0x0CE6, 0x0D43, 0x0D59, 0x0D70,
    0x0D85, 0x0D94, 0x0D98, 0x0DA4, 0x0DA8
]

# --- Helper Functions ---

def find_and_equip_new_axe():
    """Finds a new axe in the backpack and equips it."""
    for axe_id in AXE_GRAPHICS:
        new_axe = Items.FindByID(axe_id, -1, Player.Backpack.Serial)
        if new_axe:
            Misc.SendMessage(">> New axe found! Equipping...", 68)
            Player.EquipItem(new_axe.Serial)
            Misc.Pause(1000)
            return new_axe.Serial
    return 0

def make_boards(axe_serial):
    """Finds all logs in the backpack and converts them to boards using a stable loop."""
    Misc.SendMessage(">> Making boards...", 68)
    while True:
        if Items.FindBySerial(axe_serial) is None:
            axe_serial = find_and_equip_new_axe()
            if axe_serial == 0:
                Misc.SendMessage(">> Out of axes while making boards!", 33)
                return 0
        
        logs = Items.FindByID(LOG_GRAPHIC, -1, Player.Backpack.Serial, True)
        if logs is None:
            Misc.SendMessage(">> Finished making boards.", 68)
            break
            
        Items.UseItem(axe_serial)
        if Target.WaitForTarget(2000):
            Target.TargetExecute(logs.Serial)
            Misc.Pause(ACTION_DELAY)
        else:
            Misc.SendMessage(">> Error waiting for target on logs.", 33)
            break
    return axe_serial

def find_walkable_neighbor(x, y):
    """Finds a walkable tile adjacent to the target coordinates."""
    neighbors = [(0, -1), (1, 0), (0, 1), (-1, 0), (-1, -1), (1, -1), (1, 1), (-1, 1)]
    for dx, dy in neighbors:
        check_x, check_y = x + dx, y + dy
        land_id = Statics.GetLandID(check_x, check_y, Player.Map)
        if not Statics.GetLandFlag(land_id, 'Impassable'):
            statics_at_neighbor = Statics.GetStaticsTileInfo(check_x, check_y, Player.Map)
            is_blocked = False
            for static_item in statics_at_neighbor:
                if Statics.GetTileFlag(static_item.StaticID, 'Impassable'):
                    is_blocked = True
                    break
            if not is_blocked:
                return (check_x, check_y)
    return (None, None)

def find_closest_tree(ignore_list):
    """Finds the closest reachable tree that is not on the ignore list or past the boundaries."""
    closest_tree = None
    min_dist = float('inf')
    tree_x, tree_y = 0, 0
    for x in range(Player.Position.X - TREE_SEARCH_RADIUS, Player.Position.X + TREE_SEARCH_RADIUS + 1):
        for y in range(Player.Position.Y - TREE_SEARCH_RADIUS, Player.Position.Y + TREE_SEARCH_RADIUS + 1):
            if (x, y) in ignore_list:
                continue
            
            # Check if the tree is past our hard X-coordinate boundary.
            if x >= 1659:
                continue # This tree is too far east, skip it.
                
            # NEW: Check if the tree is past our hard Y-coordinate boundary.
            if y < 1260:
                continue # This tree is too far south, skip it.

            tile_info_list = Statics.GetStaticsTileInfo(x, y, Player.Map)
            for tile in tile_info_list:
                if tile.StaticID in TREE_GRAPHICS:
                    dist = math.sqrt((Player.Position.X - x)**2 + (Player.Position.Y - y)**2)
                    if dist < min_dist:
                        min_dist = dist
                        closest_tree = tile
                        tree_x = x
                        tree_y = y
    if closest_tree:
        return (closest_tree, tree_x, tree_y)
    else:
        return (None, 0, 0)

def go_to_house_and_deposit(crate_serial):
    """Goes to the house, deposits resources, and returns to a static forest spot."""
    Misc.SendMessage(">> Full! Running to the house.", 68)
    
    path = PathFinding.GetPath(HOUSE_X, HOUSE_Y, True)
    if not path or not PathFinding.RunPath(path, 60.0, False, False):
        Misc.SendMessage(">> Failed to find a path to the house! Stopping script.", 33)
        return False

    # Adjust position after arriving
    Misc.SendMessage(">> Arrived at house. Adjusting position...", 68)
    for i in range(5):
        Player.Run("North")
        Misc.Pause(500)
        
    Misc.SendMessage(">> Pausing before deposit...", 68)
    Misc.Pause(5000)

    # Deposit boards and logs into the specified crate
    while True:
        boards = Items.FindByID(BOARD_GRAPHIC, -1, Player.Backpack.Serial)
        logs = Items.FindByID(LOG_GRAPHIC, -1, Player.Backpack.Serial)
        if boards is None and logs is None:
            break
        if boards: Items.Move(boards, crate_serial, 0)
        if logs: Items.Move(logs, crate_serial, 0)
        Misc.Pause(1000)
    Misc.SendMessage(">> Finished depositing resources.", 68)
    
    Misc.Pause(3000)

    # Pathfind back to the static forest spot using the simple method
    Misc.SendMessage(">> Returning to the forest at X:{} Y:{}".format(FOREST_RETURN_X, FOREST_RETURN_Y), 78)
    Player.PathFindTo(FOREST_RETURN_X, FOREST_RETURN_Y, Player.Position.Z)
    Misc.Pause(RETURN_WALK_TIMEOUT)
        
    return True

def go_home_and_finish(crate_serial, axe_serial):
    """Makes a final run to the house to deposit everything before stopping."""
    Misc.SendMessage(">> Finishing up. Making final boards...", 68)
    axe_serial = make_boards(axe_serial)

    Misc.SendMessage(">> Running to the house.", 68)
    path = PathFinding.GetPath(HOUSE_X, HOUSE_Y, True)
    if not path or not PathFinding.RunPath(path, 60.0, False, False):
        Misc.SendMessage(">> Failed to find a path home! Stopping in place.", 33)
        return

    # Adjust position after arriving
    Misc.SendMessage(">> Arrived at house. Adjusting position...", 68)
    for i in range(5):
        Player.Run("North")
        Misc.Pause(500)

    if Items.FindByID(BOARD_GRAPHIC, -1, Player.Backpack.Serial) is not None or Items.FindByID(LOG_GRAPHIC, -1, Player.Backpack.Serial) is not None:
        Misc.SendMessage(">> Depositing final load.", 68)
        while True:
            boards = Items.FindByID(BOARD_GRAPHIC, -1, Player.Backpack.Serial)
            logs = Items.FindByID(LOG_GRAPHIC, -1, Player.Backpack.Serial)
            if boards is None and logs is None:
                break
            if boards: Items.Move(boards, crate_serial, 0)
            if logs: Items.Move(logs, crate_serial, 0)
            Misc.Pause(1000)
        Misc.SendMessage(">> Finished depositing final load.", 68)
    else:
        Misc.SendMessage(">> No final resources to deposit.", 68)

def check_health_and_flee():
    """Checks player health and flees to the house if necessary."""
    if Player.Hits < (Player.HitsMax * (FLEE_HEALTH_PERCENT / 100.0)):
        Misc.SendMessage(">> Health is low! Fleeing to the house!", 33)
        path = PathFinding.GetPath(HOUSE_X, HOUSE_Y, True)
        if not path or not PathFinding.RunPath(path, 60.0, False, False):
            Misc.SendMessage(">> Flee path failed! Trying to manually escape.", 33)
        
        # Adjust position after arriving
        Misc.SendMessage(">> Arrived at house. Adjusting position...", 68)
        for i in range(5):
            Player.Run("North")
            Misc.Pause(500)
            
        Misc.SendMessage(">> Arrived at house safely. Stopping script.", 68)
        sys.exit() # Stop the script for safety

# --- Main Script ---

Misc.SendMessage(">> Starting Lumberjacking Script...", 68)
Misc.Pause(1500) # Increased initial pause for stability

# Initial Setup
Misc.SendMessage(">> Please target your first axe.", 68)
axe_serial = Target.PromptTarget()
if axe_serial == 0:
    Misc.SendMessage(">> Canceled. No axe selected.", 33)
    sys.exit()

depleted_trees = []

# Main Loop
while True:
    check_health_and_flee() # Check health at the start of every major action
    
    if Items.FindBySerial(axe_serial) is None:
        axe_serial = find_and_equip_new_axe()
        if axe_serial == 0:
            Misc.SendMessage(">> No more axes found! Returning to house.", 33)
            go_home_and_finish(CRATE_SERIAL, axe_serial)
            break
            
    if Player.Weight >= (Player.MaxWeight - WEIGHT_LIMIT_OFFSET):
        axe_serial = make_boards(axe_serial)
        if axe_serial == 0:
            go_home_and_finish(CRATE_SERIAL, axe_serial)
            break
        if Player.Weight >= (Player.MaxWeight - WEIGHT_LIMIT_OFFSET):
            if not go_to_house_and_deposit(CRATE_SERIAL):
                break # Stop if banking fails
        continue

    tree, tree_x, tree_y = find_closest_tree(depleted_trees)
    if tree is None:
        Misc.SendMessage(">> No more trees found in range. Returning to house.", 33)
        go_home_and_finish(CRATE_SERIAL, axe_serial)
        break

    walk_to_x, walk_to_y = find_walkable_neighbor(tree_x, tree_y)
    if walk_to_x is None:
        depleted_trees.append((tree_x, tree_y))
        continue

    path = PathFinding.GetPath(walk_to_x, walk_to_y, True)
    if not path or not PathFinding.RunPath(path, 15.0, False, False):
        depleted_trees.append((tree_x, tree_y))
        continue
        
    Misc.Pause(500)

    # Dedicated loop for chopping a single tree until it is empty.
    while True:
        # Check for overweight or broken axe before each chop.
        if Player.Weight >= (Player.MaxWeight - WEIGHT_LIMIT_OFFSET):
            Misc.SendMessage(">> Overweight, stopping chop on this tree.", 68)
            break # Exit inner loop to trigger board making/banking
        if Items.FindBySerial(axe_serial) is None:
            Misc.SendMessage(">> Axe broke, stopping chop on this tree.", 138)
            break # Exit inner loop to find a new axe

        Journal.Clear()
        Items.UseItem(axe_serial)
        if Target.WaitForTarget(2000):
            Target.TargetExecute(tree_x, tree_y, tree.StaticZ, tree.StaticID)
        else:
            Misc.SendMessage(">> Error: Timed out waiting for target.", 33)
            depleted_trees.append((tree_x, tree_y))
            break

        Misc.Pause(ACTION_DELAY)
        
        # Check journal messages to see if the tree is depleted
        if (Journal.Search("There are no logs left") or 
                Journal.Search("That is too far away") or 
                Journal.Search("There's not enough wood here to harvest")):
            Misc.SendMessage(">> Tree depleted. Finding new tree.", 78)
            depleted_trees.append((tree_x, tree_y))
            break # Exit inner loop to find a new tree

Misc.SendMessage(">> Lumberjacking script finished.", 68)

