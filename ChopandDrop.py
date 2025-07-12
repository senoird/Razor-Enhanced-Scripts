# Razor Enhanced "Chop and Drop" Lumberjacking Script
#
# What it does:
# 1. Prompts you to target your axe and a weapon for combat.
# 2. If attacked, it automatically equips your weapon and waits for the fight to end.
# 3. Scans for the nearest tree, pathfinds to it, and chops it.
# 4. After each successful chop, it drops the logs on the ground next to you.
# 5. When a tree is depleted, it finds the next one and continues.
# 6. Remembers which trees are depleted to avoid getting stuck.
# 7. Automatically finds and equips a new axe if your current one breaks.
# 8. Stops automatically if you run out of axes.
#
# How to use:
# 1. Place this script in your Razor Enhanced 'Scripts' folder.
# 2. Have one or more axes and a weapon in your backpack.
# 3. Stand in a forested area and run the script. It will prompt you for your items.
# 4. To stop, you must manually stop it from the Razor Enhanced scripts tab.

import sys
import math

# --- Configuration ---

# Item IDs
AXE_GRAPHICS = [0x0F49, 0x0F47, 0x0F45, 0x13FB]
LOG_GRAPHIC = 0x1BDD

# The radius (in tiles) around the player to scan for trees.
TREE_SEARCH_RADIUS = 15

# Delay in milliseconds after each chop attempt.
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

def handle_combat(weapon_serial):
    """Equips a weapon and waits for combat to end."""
    Misc.SendMessage(">> Under attack! Equipping weapon...", 33)
    
    # Equip the designated weapon, which automatically unequips the axe.
    Player.EquipItem(weapon_serial)
    Misc.Pause(1000)
    
    Misc.SendMessage(">> In combat mode. Waiting for health to be full...", 138)
    while Player.Hits < Player.HitsMax:
        Misc.Pause(1500) # Wait and check health every 1.5 seconds.
        
    Misc.SendMessage(">> Health is full. Switching back to axe.", 68)
    
    # Unequip the weapon by equipping an axe.
    new_axe_serial = find_and_equip_new_axe()
    if new_axe_serial == 0:
        Misc.SendMessage(">> No axes to re-equip after combat! Stopping.", 33)
        sys.exit()
        
    return new_axe_serial


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

# --- Main Script ---

Misc.SendMessage(">> Starting Chop and Drop Script...", 68)
Misc.Pause(1500)

# Initial Setup
Misc.SendMessage(">> Please target your first axe.", 68)
axe_serial = Target.PromptTarget()
if axe_serial == 0:
    Misc.SendMessage(">> Canceled. No axe selected.", 33)
    sys.exit()

Misc.SendMessage(">> Please target your combat weapon in your backpack.", 68)
weapon_serial = Target.PromptTarget()
if weapon_serial == 0:
    Misc.SendMessage(">> Canceled. No weapon selected.", 33)
    sys.exit()

depleted_trees = []

# Main Loop
while True:
    # Check for combat at the start of every major loop.
    if Player.Hits < Player.HitsMax:
        axe_serial = handle_combat(weapon_serial)
        
    # Check for a valid axe.
    if Items.FindBySerial(axe_serial) is None:
        axe_serial = find_and_equip_new_axe()
        if axe_serial == 0:
            Misc.SendMessage(">> No more axes found! Stopping script.", 33)
            break
            
    # Find the next tree to chop
    tree, tree_x, tree_y = find_closest_tree(depleted_trees)
    if tree is None:
        Misc.SendMessage(">> No more trees found in range. Stopping script.", 33)
        break

    # Pathfind to a walkable spot next to the tree
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
        # Check for combat before each chop.
        if Player.Hits < Player.HitsMax:
            axe_serial = handle_combat(weapon_serial)
            break # Exit inner loop to re-evaluate after combat
            
        # Check for a broken axe.
        if Items.FindBySerial(axe_serial) is None:
            Misc.SendMessage(">> Axe broke, finding new tree.", 138)
            break

        Journal.Clear()
        Items.UseItem(axe_serial)
        if Target.WaitForTarget(2000):
            Target.TargetExecute(tree_x, tree_y, tree.StaticZ, tree.StaticID)
        else:
            Misc.SendMessage(">> Error: Timed out waiting for target.", 33)
            depleted_trees.append((tree_x, tree_y))
            break

        Misc.Pause(ACTION_DELAY)
        
        # Check for messages indicating the tree is depleted
        if (Journal.Search("There are no logs left") or 
                Journal.Search("That is too far away") or 
                Journal.Search("There's not enough wood here to harvest")):
            Misc.SendMessage(">> Tree depleted. Finding new tree.", 78)
            depleted_trees.append((tree_x, tree_y))
            break # Exit inner loop to find a new tree
        else:
            # If the chop was successful, find and drop the logs.
            logs = Items.FindByID(LOG_GRAPHIC, -1, Player.Backpack.Serial)
            if logs is not None:
                Misc.SendMessage(">> Dropping logs...", 78)
                
                # List of relative coordinates to try dropping on [dx, dy]
                drop_locations = [
                    (0, 1),   # South
                    (1, 0),   # East
                    (-1, 0),  # West
                    (0, -1)   # North
                ]
                
                for dx, dy in drop_locations:
                    drop_x = Player.Position.X + dx
                    drop_y = Player.Position.Y + dy
                    drop_z = Player.Position.Z
                    
                    Items.MoveOnGround(logs.Serial, 0, drop_x, drop_y, drop_z)
                    Misc.Pause(1200) # Give server time to process the move and update client
                    
                    # Check if the specific log item is still in the backpack
                    item_check = Items.FindBySerial(logs.Serial)
                    if item_check is None or item_check.Container != Player.Backpack.Serial:
                        break # Exit the for loop since the drop was successful
                
                # Final check to see if the logs were dropped
                final_check = Items.FindBySerial(logs.Serial)
                if final_check is not None and final_check.Container == Player.Backpack.Serial:
                    Misc.SendMessage(">> Could not drop logs. All adjacent tiles may be blocked.", 33)


Misc.SendMessage(">> Lumberjacking script finished.", 68)
