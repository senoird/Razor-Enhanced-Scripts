# Razor Enhanced Advanced Blacksmithing Training Script (v5.2)
#
# What it does:
# 1. Automatically determines which item to craft based on your real blacksmithing skill.
# 2. Automatically finds a new smithing hammer from your backpack if the current one breaks.
# 3. Crafts that item repeatedly until you run out of ingots or your skill is high enough for the next item.
# 4. Before switching to a new item, it closes any open gumps, then smelts ALL previously crafted items.
# 5. Continues this cycle until you stop the script or run out of materials/tools.
#
# How to use:
# 1. IMPORTANT: Carefully fill out the 'training_plan' dictionary and other configuration variables below.
#    You MUST use Razor's Gump Inspector tool to find the correct gump button IDs for your server.
# 2. Place this script in your Razor Enhanced 'Scripts' folder.
# 3. Stand near a forge or anvil.
# 4. Have your smithing tool(s) in your backpack and a container with ingots nearby.
# 5. Run the script. It will only ask for your initial tool and ingot container once.

from System.Collections.Generic import List

# --- Configuration ---

# The ItemID for the smithing tool you are using.
# 0x13E3 is a standard Smith's Hammer. 0x0FB4 is for Tongs.
SMITH_TOOL_ID = 0x13E3

# The Gump Button ID for the "Smelt Item" action in the smithing gump.
SMELT_BUTTON_ID = 27

# This dictionary defines your entire training path.
# You MUST fill this out with the correct values for your server.
training_plan = {
    "Mace": {
        "min_skill": 40.0, "max_skill": 45.0, "ingots": 6, "graphic": 0x0F5C,
        "category_gump": 8, "item_gump": 22
    },
    "Maul": {
        "min_skill": 45.0, "max_skill": 50.0, "ingots": 8, "graphic": 0x143B,
        "category_gump": 8, "item_gump": 29
    },
    "Cutlass": {
        "min_skill": 50.0, "max_skill": 55.0, "ingots": 10, "graphic": 0x1441,
        "category_gump": 9, "item_gump": 30
    },
    "Longsword": {
        "min_skill": 55.0, "max_skill": 59.5, "ingots": 12, "graphic": 0x0F61,
        "category_gump": 9, "item_gump": 28
    },
    "Scimitar": {
        "min_skill": 59.5, "max_skill": 70.5, "ingots": 13, "graphic": 0x13B6,
        "category_gump": 61, "item_gump": 162
    },
    "Platemail Gorget": {
        "min_skill": 70.5, "max_skill": 106.4, "ingots": 10, "graphic": 0x1413,
        "category_gump": 1, "item_gump": 182
    },
    "Platemail Gloves": {
        "min_skill": 106.4, "max_skill": 108.9, "ingots": 12, "graphic": 0x1414,
        "category_gump": 12, "item_gump": 50
    },
    "Platemail Arms": {
        "min_skill": 108.9, "max_skill": 116.3, "ingots": 18, "graphic": 0x1410,
        "category_gump": 12, "item_gump": 49
    },
    "Platemail Legs": {
        "min_skill": 116.3, "max_skill": 118.8, "ingots": 20, "graphic": 0x1411,
        "category_gump": 12, "item_gump": 52
    },
    "Platemail Tunic": {
        "min_skill": 118.8, "max_skill": 120.0, "ingots": 25, "graphic": 0x1415,
        "category_gump": 12, "item_gump": 53
    }
}

# Delays (in milliseconds)
CRAFT_TIMEOUT = 8000
SMELT_DELAY = 2000 # Pause after each smelt action.

# --- Helper Functions ---

def wait_for_journal_message(messages, timeout_ms):
    timer_name = "journal_wait_timer"
    Timer.Create(timer_name, timeout_ms)
    while not Timer.Check(timer_name):
        for msg in messages:
            if Journal.Search(msg):
                return True
        Misc.Pause(100)
    return False

def get_ingot_count(container_serial):
    ingot_id = 0x1BF2
    return Items.ContainerCount(container_serial, ingot_id, -1, True)

def get_item_to_craft():
    current_skill = Player.GetRealSkillValue("Blacksmith")
    for item_name, details in training_plan.items():
        if current_skill >= details["min_skill"] and current_skill < details["max_skill"]:
            Misc.SendMessage(">> Skill is {:.1f}. Next item: {}".format(current_skill, item_name), 68)
            return item_name, details
    return None, None
    
def find_any_crafted_item():
    """Finds a single instance of any item from the training plan in the backpack."""
    for details in training_plan.values():
        item = Items.FindByID(details["graphic"], -1, Player.Backpack.Serial, True)
        if item is not None:
            return item
    return None

def smelt_all_crafted_items(tool_serial):
    """Smelts all crafted items, one by one, in a robust loop."""
    Misc.SendMessage(">> Starting batch smelting process...", 68)
    
    while True:
        # Close any leftover gumps before every single attempt.
        if Gumps.HasGump():
            Gumps.CloseGump(Gumps.CurrentGump())
            Misc.Pause(1000)
            
        # Find the next item to smelt
        item_to_smelt = find_any_crafted_item()
        
        # If no items are left, we're done.
        if item_to_smelt is None:
            Misc.SendMessage(">> No more crafted items found to smelt.", 78)
            break
            
        # Check for a valid smithing tool before every smelt attempt
        if Items.FindBySerial(tool_serial) is None:
            Misc.SendMessage(">> Smelting tool broke. Searching for a new one...", 138)
            new_tool = Items.FindByID(SMITH_TOOL_ID, -1, Player.Backpack.Serial)
            if new_tool:
                tool_serial = new_tool.Serial
                Misc.SendMessage(">> New smithing tool found for smelting!", 68)
                Misc.Pause(1000)
            else:
                Misc.SendMessage(">> Out of smithing tools! Cannot continue smelting.", 33)
                return tool_serial
        
        # Use the tool to open the gump
        Items.UseItem(tool_serial)
        if Gumps.WaitForGump(0, 2000):
            Gumps.SendAction(Gumps.CurrentGump(), SMELT_BUTTON_ID)
        else:
            Misc.SendMessage(">> Error: Smelting gump failed to open.", 33)
            continue
            
        # Target the item to smelt
        if Target.WaitForTarget(2000):
            Target.TargetExecute(item_to_smelt.Serial)
            Misc.Pause(SMELT_DELAY)
        else:
            Misc.SendMessage(">> Error: Timed out waiting for smelt target.", 33)
            Misc.Pause(SMELT_DELAY)
            
    Misc.SendMessage(">> Batch smelting complete.", 68)
    return tool_serial

# --- Main Logic ---

Misc.SendMessage(">> Starting Advanced Blacksmith Training Script...", 68)

# Initial Setup
Misc.SendMessage(">> Please target your first smithing tool.", 68)
smith_tool_serial = Target.PromptTarget()
if smith_tool_serial == 0: Stop
Misc.SendMessage(">> Please target your ingot container.", 68)
ingot_container_serial = Target.PromptTarget()
if ingot_container_serial == 0: Stop

# Main Training Loop
current_item_name, craft_details = get_item_to_craft()
if not current_item_name:
    Misc.SendMessage(">> Your skill is outside the defined training plan. Stopping.", 33)
    Stop

while True:
    # Check for a valid smithing tool and find a new one if it broke
    if Items.FindBySerial(smith_tool_serial) is None:
        Misc.SendMessage(">> Smithing tool broke. Searching for a new one...", 138)
        new_tool = Items.FindByID(SMITH_TOOL_ID, -1, Player.Backpack.Serial)
        if new_tool:
            smith_tool_serial = new_tool.Serial
            Misc.SendMessage(">> New smithing tool found!", 68)
            Misc.Pause(1000)
        else:
            Misc.SendMessage(">> Out of smithing tools! Stopping script.", 33)
            break

    new_item_name, new_craft_details = get_item_to_craft()
    if not new_item_name:
        Misc.SendMessage(">> You have completed the training plan!", 68)
        smith_tool_serial = smelt_all_crafted_items(smith_tool_serial)
        break
        
    if new_item_name != current_item_name:
        Misc.SendMessage(">> Skill advanced! Switching to new item.", 68)
        smith_tool_serial = smelt_all_crafted_items(smith_tool_serial)
        current_item_name = new_item_name
        craft_details = new_craft_details
        Misc.Pause(2000)
        
    if get_ingot_count(ingot_container_serial) < craft_details["ingots"]:
        Misc.SendMessage(">> Out of ingots! Smelting remaining items.", 33)
        smith_tool_serial = smelt_all_crafted_items(smith_tool_serial)
        break
        
    # Crafting Process
    Journal.Clear()
    Items.UseItem(smith_tool_serial)
    if not Gumps.WaitForGump(0, 2000):
        Misc.SendMessage(">> Error: Smithing gump did not appear. Stopping.", 33)
        break
    current_gump_id = Gumps.CurrentGump()
    Gumps.SendAction(current_gump_id, craft_details["category_gump"])
    Misc.Pause(750)
    if Gumps.HasGump():
        current_gump_id = Gumps.CurrentGump()
    else:
        Misc.SendMessage(">> Error: Gump closed after category selection. Stopping.", 33)
        break
    Gumps.SendAction(current_gump_id, craft_details["item_gump"])
    
    craft_success_messages = ["You have made progress", "you have made progress"]
    if wait_for_journal_message(craft_success_messages, CRAFT_TIMEOUT):
        Misc.SendMessage(">> Craft successful.", 78)
        Misc.Pause(1000)
    else:
        Misc.SendMessage(">> Craft failed (no journal message). Continuing...", 138)
        Misc.Pause(1000)

Misc.SendMessage(">> Blacksmith training script finished.", 68)
# --- Script End ---
