# Razor Enhanced Lumberjacking Script (v3.3)
#
# What it does:
# 1. Automatically finds and uses the axe in your right hand.
# 2. Scans for the nearest tree, finds a walkable spot next to it, pathfinds, and chops.
# 3. Remembers which trees are depleted to avoid getting stuck.
# 4. Automatically finds and equips a new axe if your current one breaks.
# 5. When your backpack is full, it automatically converts all logs to boards.
# 6. Stops automatically if you are full of boards or out of axes.
#
# How to use:
# 1. Place this script in your Razor Enhanced 'Scripts' folder.
# 2. Equip an axe in your right hand. Have more axes in your backpack.
# 3. Stand in a forested area and run the script.
# 4. To stop, you must manually stop it from the Razor Enhanced scripts tab.

import sys
import math

# --- Configuration ---

# A list of graphic IDs for axes. The script will search for these if your current axe breaks.
# The script will also automatically add the ID of your equipped axe to this list.
AXE_GRAPHICS = [0x0F49, 0x0F47, 0x0F45, 0x13FB]
LOG_GRAPHIC = 0x1BDD

# The radius (in tiles) around the player to scan for trees.
TREE_SEARCH_RADIUS = 15

# The script will stop if your weight is this close to your maximum weight.
# This leaves some room to walk without being over-encumbered.
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
        # Check if the axe is still valid
        if Items.FindBySerial(axe_serial) is None:
            axe_serial = find_and_equip_new_axe()
            if axe_serial == 0:
                Misc.SendMessage(">> Out of axes while making boards!", 33)
                return 0 # Signal to stop

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
    # Check neighbors in a specific order: N, E, S, W, etc.
    neighbors = [(0, -1), (1, 0), (0, 1), (-1, 0), (-1, -1), (1, -1), (1, 1), (-1, 1)]
    for dx, dy in neighbors:
        check_x, check_y = x + dx, y + dy
        land_id = Statics.GetLandID(check_x, check_y, Player.Map)
        # Check if the land tile is considered impassable
        if not Statics.GetLandFlag(land_id, 'Impassable'):
            # Also check for blocking static items at that location
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

    # Iterate through tiles in a square radius around the player
    for x in range(Player.Position.X - TREE_SEARCH_RADIUS, Player.Position.X + TREE_SEARCH_RADIUS + 1):
        for y in range(Player.Position.Y - TREE_SEARCH_RADIUS, Player.Position.Y + TREE_SEARCH_RADIUS + 1):
            # Check if this coordinate is on the ignore list
            if (x, y) in ignore_list:
                continue
                
            tile_info_list = Statics.GetStaticsTileInfo(x, y, Player.Map)
            for tile in tile_info_list:
                if tile.StaticID in TREE_GRAPHICS:
                    # Calculate distance manually to avoid the Point3D error
                    dx = Player.Position.X - x
                    dy = Player.Position.Y - y
                    dist = math.sqrt(dx*dx + dy*dy)
                    if dist < min_dist:
                        min_dist = dist
                        closest_tree = tile
                        tree_x = x
                        tree_y = y
                        
    if closest_tree:
        return (closest_tree, tree_x, tree_y)
    else:
        return (None, 0, 0)

# --- Main Script ---

Misc.SendMessage(">> Starting Lumberjacking Script...", 68)
Misc.Pause(500) # Add a small pause for initialization

# 1. Initial Setup: Find and validate equipped axe
equipped_axe = Player.GetItemOnLayer('RightHand')
# If nothing in right hand, check left hand (for two-handed weapons)
if equipped_axe is None:
    equipped_axe = Player.GetItemOnLayer('LeftHand')

if equipped_axe is None:
    Misc.SendMessage(">> No axe equipped in either hand! Stopping script.", 33)
    sys.exit()

# Automatically trust the user's equipped axe.
# If the equipped axe's ID isn't in our list, add it.
if equipped_axe.ItemID not in AXE_GRAPHICS:
    Misc.SendMessage(">> Adding your equipped axe (ID: {}) to the list of known axes.".format(hex(equipped_axe.ItemID)), 68)
    AXE_GRAPHICS.append(equipped_axe.ItemID)

axe_serial = equipped_axe.Serial
depleted_trees = [] # List to store coordinates of depleted trees

# 2. Main Loop
while True:
    # Check for a valid axe at the start of each loop.
    if Items.FindBySerial(axe_serial) is None:
        Misc.SendMessage(">> Axe broke or is missing. Searching for a new one...", 138)
        axe_serial = find_and_equip_new_axe()
        if axe_serial == 0:
            Misc.SendMessage(">> No more axes found! Stopping script.", 33)
            break
    
    # Check player weight. If too heavy, make boards.
    if Player.Weight >= (Player.MaxWeight - WEIGHT_LIMIT_OFFSET):
        axe_serial = make_boards(axe_serial)
        if axe_serial == 0: break # Stop if out of axes

        # If still too heavy after making boards, we are full.
        if Player.Weight >= (Player.MaxWeight - WEIGHT_LIMIT_OFFSET):
            Misc.SendMessage(">> You are full of boards! Stopping script.", 33)
            break
        continue # Restart the loop to find a new tree

    # Find the next tree to chop, ignoring depleted ones
    tree, tree_x, tree_y = find_closest_tree(depleted_trees)
    if tree is None:
        Misc.SendMessage(">> No more trees found in range. Stopping script.", 33)
        break

    # NEW: Find a walkable tile next to the tree to pathfind to.
    walk_to_x, walk_to_y = find_walkable_neighbor(tree_x, tree_y)
    if walk_to_x is None:
        Misc.SendMessage(">> No walkable spot found near the tree. Ignoring it.", 138)
        depleted_trees.append((tree_x, tree_y))
        continue

    Misc.SendMessage(">> Moving to chop tree at X:{} Y:{}".format(tree_x, tree_y), 78)
    
    # Use the robust PathFinding module for movement
    path = PathFinding.GetPath(walk_to_x, walk_to_y, True) # True ignores mobiles
    if not path:
        Misc.SendMessage(">> Cannot find a path to the tree. Ignoring it.", 138)
        depleted_trees.append((tree_x, tree_y))
        continue

    # Run the calculated path. Timeout is in seconds (float).
    if not PathFinding.RunPath(path, 15.0, False, False):
        Misc.SendMessage(">> Failed to follow the path. Ignoring this tree.", 138)
        depleted_trees.append((tree_x, tree_y))
        continue
        
    Misc.Pause(500) # Brief pause after arriving

    # Loop to chop the selected tree until it's depleted
    while True:
        # Re-check weight and axe before each chop
        if Player.Weight >= (Player.MaxWeight - WEIGHT_LIMIT_OFFSET):
            break # Exit inner loop to trigger board making
        if Items.FindBySerial(axe_serial) is None:
            break # Exit inner loop to trigger finding a new axe

        Journal.Clear()
        Items.UseItem(axe_serial)
        
        if Target.WaitForTarget(2000):
            # Use the correct coordinates returned from the find_closest_tree function
            Target.TargetExecute(tree_x, tree_y, tree.StaticZ, tree.StaticID)
        else:
            Misc.SendMessage(">> Error: Timed out waiting for target.", 33)
            break

        Misc.Pause(ACTION_DELAY)
        
        # Check journal messages to see if the tree is depleted
        if (Journal.Search("There are no logs left") or 
                Journal.Search("That is too far away") or 
                Journal.Search("There's not enough wood here to harvest")):
            Misc.SendMessage(">> Tree depleted or out of range. Finding new tree.", 78)
            # Add the coordinates of the depleted tree to our ignore list
            depleted_trees.append((tree_x, tree_y))
            break

Misc.SendMessage(">> Lumberjacking script finished.", 68)
# --- Script End ---
