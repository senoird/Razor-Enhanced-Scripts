# Razor Enhanced Lumberjacking Script (v6.3)
#
# What it does:
# 1. Automatically finds and uses the axe in your right hand.
# 2. Scans for the nearest tree, pathfinds to it, and chops it until depleted.
# 3. Remembers which trees are depleted to avoid getting stuck.
# 4. Automatically finds and equips a new axe if your current one breaks.
# 5. When your backpack is full of logs, it converts them to boards.
# 6. When your backpack is full of boards, it runs to your house, adjusts position, and deposits boards.
# 7. If attacked, it will flee to your house for safety.
# 8. When out of trees or axes, it will run home and deposit before stopping.
#
# How to use:
# 1. IMPORTANT: Fill out the house coordinates and your crate's serial number in the Configuration section.
# 2. Place this script in your Razor Enhanced 'Scripts' folder.
# 3. Equip an axe in your right hand. Have more axes in your backpack.
# 4. Stand in a forested area and run the script.
# 5. To stop, you must manually stop it from the Razor Enhanced scripts tab.

import sys
import math

# --- Configuration ---

# The coordinates of a safe spot at your house (e.g., on your porch).
HOUSE_X = 1658
HOUSE_Y = 1225

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

# A list of static tile IDs for various tree types.
TREE_GRAPHICS = [
    0x0CCA, 0x0CCB, 0x0CCC, 0x0CCD, 0x0CD0, 0x0CD3, 0x0CD6, 0x0CD8,
    0x0CDA, 0x0CDD, 0x0CE0, 0x0CE3, 0x0CE6, 0x0D43, 0x0D59, 0x0D70,
    0x0D85, 0x0D94, 0x0D98, 0x0DA4, 0x0DA8
]

# --- Helper Functions ---

def smart_move(x, y, z):
    """
    Intelligently moves the player, using the best pathfinding method based on distance.
    Returns True on success, False on failure.
    """
    distance = math.sqrt((Player.Position.X - x)**2 + (Player.Position.Y - y)**2)
    
    # If the distance is short (likely on-screen), use the simpler method.
    if distance < 16:
        Player.PathFindTo(x, y, z)
        # Give it a generous pause to complete the short walk.
        Misc.Pause(int(distance * 600)) # Adjust multiplier as needed
        # Check if we made it close enough
        final_dist = math.sqrt((Player.Position.X - x)**2 + (Player.Position.Y - y)**2)
        if final_dist > 3:
            Misc.SendMessage(">> Short-distance pathfinding failed.", 138)
            return False
        return True
    # If the distance is long, use the more robust method.
    else:
        path = PathFinding.GetPath(x, y, True)
        if not path or not PathFinding.RunPath(path, 60.0, False, False):
            Misc.SendMessage(">> Long-distance pathfinding failed.", 33)
            return False
        return True

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
    """Finds all logs in the backpack and converts them to boards."""
    Misc.SendMessage(">> Making boards...", 68)
    while True:
        if Items.FindBySerial(axe_serial) is None:
            axe_serial = find_and_equip_new_axe()
            if axe_serial == 0:
                Misc.SendMessage(">> Out of axes while making boards!", 33)
                return 0
        logs = Items.FindByID(LOG_GRAPHIC, -1, Player.Backpack.Serial)
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
    """Finds the closest reachable tree that is not on the ignore list."""
    closest_tree = None
    min_dist = float('inf')
    tree_x, tree_y = 0, 0
    for x in range(Player.Position.X - TREE_SEARCH_RADIUS, Player.Position.X + TREE_SEARCH_RADIUS + 1):
        for y in range(Player.Position.Y - TREE_SEARCH_RADIUS, Player.Position.Y + TREE_SEARCH_RADIUS + 1):
            if (x, y) in ignore_list:
                continue
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
    """Saves location, goes to the house, deposits boards, and returns."""
    Misc.SendMessage(">> Full of boards! Running to the house.", 68)
    start_x, start_y = Player.Position.X, Player.Position.Y
    
    # Pathfind to house
    if not smart_move(HOUSE_X, HOUSE_Y, Player.Position.Z):
        Misc.SendMessage(">> Failed to find a path to the house! Stopping script.", 33)
        return False

    # Adjust position after arriving
    Misc.SendMessage(">> Arrived at house. Adjusting position...", 68)
    for i in range(5):
        Player.Run("North")
        Misc.Pause(200)
        
    # Add a delay after arriving at the house
    Misc.SendMessage(">> Pausing before deposit...", 68)
    Misc.Pause(5000)

    # Deposit boards into the specified crate
    while True:
        boards = Items.FindByID(BOARD_GRAPHIC, -1, Player.Backpack.Serial)
        if boards is None:
            break
        Items.Move(boards, crate_serial, 0)
        Misc.Pause(1000)
    Misc.SendMessage(">> Finished depositing boards.", 68)
    
    # Added 3-second delay after depositing
    Misc.Pause(3000)

    # Pathfind back to lumberjacking spot
    Misc.SendMessage(">> Returning to the forest...", 78)
    return_x, return_y = find_walkable_neighbor(start_x, start_y)
    if return_x is None:
        Misc.SendMessage(">> Cannot find a walkable spot to return to! Stopping.", 33)
        return False
        
    if not smart_move(return_x, return_y, Player.Position.Z):
        Misc.SendMessage(">> Failed to find a path back to the forest! Stopping script.", 33)
        return False
        
    return True

def go_home_and_finish(crate_serial, axe_serial):
    """Makes a final run to the house to deposit everything before stopping."""
    Misc.SendMessage(">> Finishing up. Making final boards...", 68)
    axe_serial = make_boards(axe_serial)

    Misc.SendMessage(">> Running to the house.", 68)
    if not smart_move(HOUSE_X, HOUSE_Y, Player.Position.Z):
        Misc.SendMessage(">> Failed to find a path home! Stopping in place.", 33)
        return

    # Adjust position after arriving
    Misc.SendMessage(">> Arrived at house. Adjusting position...", 68)
    for i in range(5):
        Player.Run("North")
        Misc.Pause(200)

    if Items.FindByID(BOARD_GRAPHIC, -1, Player.Backpack.Serial) is not None:
        Misc.SendMessage(">> Depositing final load.", 68)
        while True:
            boards = Items.FindByID(BOARD_GRAPHIC, -1, Player.Backpack.Serial)
            if boards is None:
                break
            Items.Move(boards, crate_serial, 0)
            Misc.Pause(1000)
        Misc.SendMessage(">> Finished depositing final load.", 68)
    else:
        Misc.SendMessage(">> No final boards to deposit.", 68)

def check_health_and_flee():
    """Checks player health and flees to the house if necessary."""
    if Player.Hits < (Player.HitsMax * (FLEE_HEALTH_PERCENT / 100.0)):
        Misc.SendMessage(">> Health is low! Fleeing to the house!", 33)
        if not smart_move(HOUSE_X, HOUSE_Y, Player.Position.Z):
            Misc.SendMessage(">> Flee path failed! Trying to manually escape.", 33)
        
        # Adjust position after arriving
        Misc.SendMessage(">> Arrived at house. Adjusting position...", 68)
        for i in range(5):
            Player.Run("North")
            Misc.Pause(200)
            
        Misc.SendMessage(">> Arrived at house safely. Stopping script.", 68)
        sys.exit() # Stop the script for safety

# --- Main Script ---

Misc.SendMessage(">> Starting Lumberjacking Script...", 68)
Misc.Pause(500)

# Initial Setup
equipped_axe = Player.GetItemOnLayer('RightHand')
if equipped_axe is None:
    equipped_axe = Player.GetItemOnLayer('LeftHand')
if equipped_axe is None:
    Misc.SendMessage(">> No axe equipped in either hand! Stopping script.", 33)
    sys.exit()
if equipped_axe.ItemID not in AXE_GRAPHICS:
    AXE_GRAPHICS.append(equipped_axe.ItemID)
axe_serial = equipped_axe.Serial
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

    if not smart_move(walk_to_x, walk_to_y, Player.Position.Z):
        depleted_trees.append((tree_x, tree_y))
        continue
        
    Misc.Pause(500)

    while True:
        check_health_and_flee() # Check health between each chop
        if Player.Weight >= (Player.MaxWeight - WEIGHT_LIMIT_OFFSET):
            break
        if Items.FindBySerial(axe_serial) is None:
            break

        Journal.Clear()
        Items.UseItem(axe_serial)
        if Target.WaitForTarget(2000):
            Target.TargetExecute(tree_x, tree_y, tree.StaticZ, tree.StaticID)
        else:
            break
        Misc.Pause(ACTION_DELAY)
        
        if (Journal.Search("There are no logs left") or 
                Journal.Search("That is too far away") or 
                Journal.Search("There's not enough wood here to harvest")):
            depleted_trees.append((tree_x, tree_y))
            break

Misc.SendMessage(">> Lumberjacking script finished.", 68)
