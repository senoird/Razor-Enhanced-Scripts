# Razor Enhanced Auto-Smelting Script (v3)
#
# What it does:
# 1. Prompts you to target your smithing tool (e.g., a smith's hammer or tongs).
# 2. Prompts you to target an example of the item you want to smelt from your backpack.
# 3. Automatically finds all items of that type in your backpack and smelts them one by one.
#
# How to use:
# 1. Place this script in your Razor Enhanced 'Scripts' folder.
# 2. Make sure you have your smithing tool and the items to be smelted in your backpack.
# 3. Stand near a forge or anvil.
# 4. Run the script from within Razor Enhanced.
# 5. Follow the in-game target prompts.

from System.Collections.Generic import List

# --- Configuration ---
# Adjust this delay (in milliseconds) to match your server's speed and prevent issues.
# A value between 1000ms and 2000ms is usually safe.
smelting_delay = 1500

# --- Script Start ---

Misc.SendMessage(">> Starting Auto-Smelting Script...", 68)

# 1. Get the smithing tool
Misc.SendMessage(">> Please target your smithing tool.", 68)
smith_tool_serial = Target.PromptTarget()
if smith_tool_serial == 0:
    Misc.SendMessage(">> Canceled. No tool selected.", 33)
    Stop
smith_tool = Items.FindBySerial(smith_tool_serial)
if smith_tool is None:
    Misc.SendMessage(">> Canceled. Invalid tool selected.", 33)
    Stop

# 2. Get the item type to smelt
Misc.SendMessage(">> Please target an item in your backpack to smelt.", 68)
item_to_smelt_serial = Target.PromptTarget()
if item_to_smelt_serial == 0:
    Misc.SendMessage(">> Canceled. No item selected.", 33)
    Stop

item_to_smelt_example = Items.FindBySerial(item_to_smelt_serial)
if item_to_smelt_example is None or item_to_smelt_example.RootContainer != Player.Backpack.Serial:
    Misc.SendMessage(">> Canceled. You must target an item inside your backpack.", 33)
    Stop

# Store the ItemID (also known as Graphics ID) of the selected item
item_id_to_smelt = item_to_smelt_example.ItemID
item_name = item_to_smelt_example.Name or "item" # Use a generic name if none exists
Misc.SendMessage(">> Preparing to smelt all '{}' items.".format(item_name), 68)
Misc.Pause(500)

# 3. Find all items of that type in the backpack first
# This creates a list of all items we need to process.
smelt_filter = Items.Filter()
smelt_filter.Graphics.Add(item_id_to_smelt)
# Apply the filter to all items Razor knows about
all_matching_items = Items.ApplyFilter(smelt_filter)

# Now, create a final list containing only items in the player's backpack
items_to_smelt = []
for item in all_matching_items:
    # item.RootContainer gets the top-level container (e.g., your backpack)
    if item.RootContainer == Player.Backpack.Serial:
        items_to_smelt.append(item)

if not items_to_smelt:
    Misc.SendMessage(">> No '{}' items found in your backpack.".format(item_name), 33)
    Stop

Misc.SendMessage(">> Found {} '{}' items to smelt.".format(len(items_to_smelt), item_name), 68)
Misc.Pause(1000)

# 4. Main smelting loop
# Use the smithing tool ONCE to open the gump
Items.UseItem(smith_tool)

# Wait for the initial gump to appear
if not Gumps.WaitForGump(0, 3000):
    Misc.SendMessage(">> Error: Smithing gump did not appear.", 33)
    Stop

for item in items_to_smelt:
    # Before each attempt, ensure the main smithing gump is present.
    # On many servers, the gump returns to the main menu after each craft/smelt.
    if not Gumps.HasGump():
        Misc.SendMessage(">> Smithing gump closed unexpectedly. Stopping script.", 33)
        break

    # Check if the item still exists (it might have been smelted already in a stack)
    if Items.FindBySerial(item.Serial) is None:
        continue

    Misc.SendMessage(">> Attempting to smelt {}...".format(item_name), 78)

    # Press the "Smelt Item" button. This is button #27 on many servers.
    Gumps.SendAction(Gumps.CurrentGump(), 27)

    # After clicking the smelt button, a target cursor appears
    if Target.WaitForTarget(2000):
        Target.TargetExecute(item.Serial)
    else:
        Misc.SendMessage(">> Error: Timed out waiting for item target.", 33)
        break

    # Wait for the action to complete before starting the next item
    Misc.Pause(smelting_delay)

Misc.SendMessage(">> Auto-smelting script finished.", 68)
# --- Script End ---
