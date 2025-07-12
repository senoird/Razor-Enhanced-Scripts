# Razor Enhanced Cotton Picking Script (v2.5 - Simplified Logic)
#
# What it does:
# 1. Scans for cotton plants as items on the ground.
# 2. Finds the nearest plant, walks to it, and picks it repeatedly.
# 3. After a successful pick, it loots the spawned cotton bale from the ground.
# 4. When a plant is picked, its ID changes, so the script automatically finds the next valid plant.
# 5. Stops automatically when you get too heavy.
#
# How to use:
# 1. Place this script in your Razor Enhanced 'Scripts' folder.
# 2. Stand in an area with cotton plants.
# 3. Run the script.
# 4. To stop, you must manually stop it from the Razor Enhanced scripts tab.

import sys
import math

# --- Configuration ---

# Item IDs
# The graphic ID for picked cotton.
COTTON_ITEM_ID = 0x0DF9 

# A list of item IDs for cotton plants.
# 0x0C53 and 0x0C54 are the most common.
COTTON_PLANT_GRAPHICS = [0x0C51, 0x0C52, 0x0C53, 0x0C54]

# The radius (in tiles) around the player to scan for plants.
PLANT_SEARCH_RADIUS = 18

# The script will stop if your weight is this close to your maximum weight.
WEIGHT_LIMIT_OFFSET = 10

# Delay in milliseconds after each picking attempt.
ACTION_DELAY = 1500

# --- Helper Functions ---

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

def find_closest_plant():
    """Finds the closest reachable cotton plant."""
    # Use an Item filter to find plants on the ground.
    plant_filter = Items.Filter()
    plant_filter.OnGround = 1 # We only want items on the ground
    plant_filter.RangeMax = PLANT_SEARCH_RADIUS
    for graphic in COTTON_PLANT_GRAPHICS:
        plant_filter.Graphics.Add(graphic)
        
    ground_plants = Items.ApplyFilter(plant_filter)
    
    closest_plant = None
    min_dist = float('inf')
    
    for plant in ground_plants:
        dist = Player.DistanceTo(plant)
        if dist < min_dist:
            min_dist = dist
            closest_plant = plant
            
    return closest_plant

# --- Main Script ---

Misc.SendMessage(">> Starting Cotton Picking Script...", 68)
Misc.Pause(2000) # Initial pause for client to settle

# Main Loop
while True:
    # Check player weight at the start of each loop.
    if Player.Weight >= (Player.MaxWeight - WEIGHT_LIMIT_OFFSET):
        Misc.SendMessage(">> You are too heavy! Stopping script.", 33)
        break
            
    # Find the next plant to pick
    plant = find_closest_plant()
    if plant is None:
        Misc.SendMessage(">> No more cotton plants found in range. Stopping script.", 33)
        break

    plant_x = plant.Position.X
    plant_y = plant.Position.Y

    # Pathfind to a walkable spot next to the plant
    walk_to_x, walk_to_y = find_walkable_neighbor(plant_x, plant_y)
    if walk_to_x is None:
        # This case is unlikely but good for safety.
        Misc.SendMessage(">> No walkable spot found near the plant.", 138)
        Misc.Pause(1000)
        continue

    path = PathFinding.GetPath(walk_to_x, walk_to_y, True)
    if not path or not PathFinding.RunPath(path, 15.0, False, False):
        Misc.SendMessage(">> Path to plant failed. Finding new plant.", 138)
        continue
        
    Misc.Pause(500)

    # Dedicated loop for picking a single plant until it is empty.
    while True:
        # Check for overweight before each pick.
        if Player.Weight >= (Player.MaxWeight - WEIGHT_LIMIT_OFFSET):
            Misc.SendMessage(">> Overweight, stopping pick on this plant.", 68)
            break
        
        # Double-click the plant to pick it.
        Items.UseItem(plant.Serial)
        Misc.Pause(ACTION_DELAY)
        
        # Check for the spawned bale to determine success.
        bale_filter = Items.Filter()
        bale_filter.Graphics.Add(COTTON_ITEM_ID)
        bale_filter.OnGround = 1
        bale_filter.RangeMax = 2 # Search within 2 tiles
        bale_list = Items.ApplyFilter(bale_filter)

        if len(bale_list) > 0:
            # Success! A bale was created.
            Misc.SendMessage(">> Found cotton bale. Picking it up...", 78)
            Items.Move(bale_list[0].Serial, Player.Backpack.Serial, 0)
            Misc.Pause(1000) # Pause after looting before trying again
        else:
            # Failure. No bale was created, so the plant must be empty.
            Misc.SendMessage(">> Plant is depleted. Finding new plant.", 78)
            break # Exit inner loop to find a new plant

Misc.SendMessage(">> Cotton picking script finished.", 68)
