# Razor Enhanced Carpentry Training Script
#
# What it does:
# 1. Restocks boards from a specified crate when you run low.
# 2. Finds and uses saws from a specified tool pouch.
# 3. Automatically selects the correct item to craft based on your Carpentry skill.
# 4. After crafting, it intelligently disposes of the item by either destroying it with an axe or moving it to a trash barrel.
# 5. Automatically finds a new saw or axe if one breaks.
# 6. Runs continuously until you run out of materials or tools.
#
# How to use:
# 1. IMPORTANT: Fill out the 'training_plan' dictionary below with the correct gump button IDs for your server.
# 2. Place this script in your Razor Enhanced 'Scripts' folder.
# 3. Have a crate with boards, a pouch with saws, an axe, and a trash barrel nearby.
# 4. Run the script and follow the prompts to target your items.
# 5. To stop, you must manually stop it from the Razor Enhanced scripts tab.

import sys
import math

# --- Configuration ---

# The ItemID for the tools and materials we will use.
SAW_ID = 0x1034
AXE_ID = 0x0F43 
BOARD_ID = 0x1BD7

# The script will restock boards when you have fewer than this many.
BOARD_RESTOCK_THRESHOLD = 30

# The weight to leave free when restocking to ensure you can walk.
WEIGHT_BUFFER = 50

# Delay in milliseconds after each craft/destroy attempt.
ACTION_DELAY = 3000

# This dictionary defines your entire training path.
# You MUST fill this out with the correct gump button IDs for your server.
# Use Razor's Gump Inspector tool to find these numbers.
training_plan = {
    "Medium Crate": {
        "min_skill": 30.0, "max_skill": 48.0, "boards": 20, "graphic": 0x0E3F,
        "category_gump": 41, "item_gump": 42, "disposal_method": "destroy"
    },
    "Large Crate": {
        "min_skill": 48.0, "max_skill": 53.0, "boards": 30, "graphic": 0x0E3D,
        "category_gump": 41, "item_gump": 62, "disposal_method": "destroy"
    },
    "Wooden Shield": {
        "min_skill": 53.0, "max_skill": 60.0, "boards": 15, "graphic": 0x1B7A,
        "category_gump": 81, "item_gump": 2, "disposal_method": "trash"
    },
    "Fukiya": {
        "min_skill": 60.0, "max_skill": 74.0, "boards": 10, "graphic": 0x27F5,
        "category_gump": 61, "item_gump": 82, "disposal_method": "trash"
    },
    "Quarter Staff": {
        "min_skill": 74.0, "max_skill": 79.0, "boards": 6, "graphic": 0x0E89,
        "category_gump": 61, "item_gump": 22, "disposal_method": "trash"
    },
    "Gnarled Staff": {
        "min_skill": 79.0, "max_skill": 82.0, "boards": 7, "graphic": 0x13F8,
        "category_gump": 61, "item_gump": 42, "disposal_method": "trash"
    },
    "Black Staff": {
        "min_skill": 82.0, "max_skill": 96.0, "boards": 8, "graphic": 0x0DF0,
        "category_gump": 61, "item_gump": 302, "disposal_method": "trash"
    },
    "Wild Staff": {
        "min_skill": 96.0, "max_skill": 100.0, "boards": 10, "graphic": 0x27A8,
        "category_gump": 61, "item_gump": 122, "disposal_method": "trash"
    }
}

# --- Helper Functions ---

def get_board_count():
    """Counts the number of boards in the player's backpack."""
    return Items.ContainerCount(Player.Backpack.Serial, BOARD_ID, -1, True)

def restock_boards(crate_serial):
    """Restocks boards from the supply crate using a single, calculated move."""
    Misc.SendMessage(">> Restocking boards...", 68)
    
    # Open the supply crate
    Items.UseItem(crate_serial)
    Misc.Pause(1000)
    
    # Find boards in the crate
    boards_in_crate = Items.FindByID(BOARD_ID, -1, crate_serial)
    if boards_in_crate is None:
        Misc.SendMessage(">> Supply crate is out of boards!", 33)
        return False

    # Calculate the precise number of boards to move.
    available_weight = Player.MaxWeight - Player.Weight - WEIGHT_BUFFER
    if available_weight <= 0:
        Misc.SendMessage(">> You are too heavy to restock more boards.", 138)
        return True

    # Assuming 1 board = 1 stone for this calculation
    boards_to_move = int(available_weight)

    # Don't try to move more boards than are in the stack
    if boards_to_move > boards_in_crate.Amount:
        boards_to_move = boards_in_crate.Amount

    if boards_to_move > 0:
        Misc.SendMessage(">> Attempting to move {} boards...".format(boards_to_move), 78)
        Items.Move(boards_in_crate.Serial, Player.Backpack.Serial, boards_to_move)
        Misc.Pause(1500) # Pause to allow the item to move and weight to update
    else:
        Misc.SendMessage(">> No room for more boards.", 138)
            
    Misc.SendMessage(">> Finished restocking.", 68)
    return True

def get_item_to_craft():
    """Determines which item to craft based on current skill."""
    current_skill = Player.GetRealSkillValue("Carpentry")
    for item_name, details in training_plan.items():
        if current_skill >= details["min_skill"] and current_skill < details["max_skill"]:
            Misc.SendMessage(">> Skill is {:.1f}. Next item: {}".format(current_skill, item_name), 68)
            return item_name, details
    return None, None
    
def dispose_of_item(item_graphic, pouch_serial, disposal_method, axe_serial, trash_barrel_serial):
    """Finds and disposes of the specified item."""
    item_to_dispose = Items.FindByID(item_graphic, -1, pouch_serial, True)
    
    if item_to_dispose is None:
        item_to_dispose = Items.FindByID(item_graphic, -1, Player.Backpack.Serial, True)

    if item_to_dispose:
        if disposal_method == "destroy":
            Misc.SendMessage(">> Destroying last crafted item...", 78)
            if Items.FindBySerial(axe_serial) is None:
                Misc.SendMessage(">> Axe is missing! Cannot destroy item.", 33)
                return
            Items.UseItem(axe_serial)
            if Target.WaitForTarget(2000):
                Target.TargetExecute(item_to_dispose.Serial)
                Misc.Pause(1000)
        elif disposal_method == "trash":
            Misc.SendMessage(">> Trashing last crafted item...", 78)
            Items.Move(item_to_dispose.Serial, trash_barrel_serial, 0)
            Misc.Pause(1000)
    else:
        Misc.SendMessage(">> Could not find crafted item to dispose of.", 138)

# --- Main Script ---

Misc.SendMessage(">> Starting Carpentry Training Script...", 68)
Misc.Pause(1500)

# Initial Setup
Misc.SendMessage(">> Please target your board supply crate.", 68)
crate_serial = Target.PromptTarget()
if crate_serial == 0: sys.exit()

Misc.SendMessage(">> Please target the pouch containing your saws.", 68)
saw_pouch_serial = Target.PromptTarget()
if saw_pouch_serial == 0: sys.exit()

Misc.SendMessage(">> Please target your axe for destroying items.", 68)
axe_serial = Target.PromptTarget()
if axe_serial == 0: sys.exit()

Misc.SendMessage(">> Please target your trash barrel.", 68)
trash_barrel_serial = Target.PromptTarget()
if trash_barrel_serial == 0: sys.exit()

# Main Loop
while True:
    # Add a "heartbeat" pause at the start of every loop for stability.
    Misc.Pause(250)
    
    # Check if we need to restock boards
    if get_board_count() < BOARD_RESTOCK_THRESHOLD:
        if not restock_boards(crate_serial):
            Misc.SendMessage(">> Restocking failed. Stopping script.", 33)
            break
        # After restocking, restart the loop to re-evaluate the situation.
        continue
    
    # Determine which item to craft
    item_name, craft_details = get_item_to_craft()
    if not item_name:
        Misc.SendMessage(">> You have completed the training plan! Stopping.", 68)
        break
        
    # Check if we have enough boards for the next craft
    if get_board_count() < craft_details["boards"]:
        Misc.SendMessage(">> Not enough boards for '{}'. Restocking...".format(item_name), 138)
        continue # Loop back to trigger restocking

    # Find a saw in the pouch
    saw = Items.FindByID(SAW_ID, -1, saw_pouch_serial)
    if saw is None:
        Misc.SendMessage(">> Out of saws! Stopping script.", 33)
        break
        
    # Crafting Process
    Journal.Clear()
    Items.UseItem(saw.Serial)
    if not Gumps.WaitForGump(0, 2000):
        Misc.SendMessage(">> Error: Carpentry gump did not appear.", 33)
        continue
        
    current_gump_id = Gumps.CurrentGump()
    Gumps.SendAction(current_gump_id, craft_details["category_gump"])
    Misc.Pause(750)
    
    if Gumps.HasGump():
        current_gump_id = Gumps.CurrentGump()
    else:
        Misc.SendMessage(">> Error: Gump closed after category selection.", 33)
        continue

    Gumps.SendAction(current_gump_id, craft_details["item_gump"])
    Misc.Pause(ACTION_DELAY)
    
    # Add a dedicated pause after crafting to prevent client crashes.
    Misc.Pause(2000)
    
    # Dispose of the crafted item if successful
    if not Journal.Search("You fail to create"):
        dispose_of_item(
            craft_details["graphic"], 
            saw_pouch_serial, 
            craft_details["disposal_method"], 
            axe_serial, 
            trash_barrel_serial
        )
    else:
        Misc.SendMessage(">> Craft failed. Continuing...", 138)
        
    Misc.Pause(1000) # Final pause before next loop

Misc.SendMessage(">> Carpentry training script finished.", 68)
