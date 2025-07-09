# Razor Enhanced Ore Smelting Script
#
# What it does:
# 1. Prompts you to target a container that holds your ore.
# 2. Prompts you to target a nearby forge.
# 3. Scans the container for all known ore types.
# 4. Smelts every piece of ore, one stack at a time, until the container is empty.
# 5. Skips ore piles that are too small to be smelted.
#
# How to use:
# 1. Place this script in your Razor Enhanced 'Scripts' folder.
# 2. Stand near a forge.
# 3. Have a container filled with various types of ore.
# 4. Run the script and follow the prompts.

# --- Configuration ---

# This list defines all the ore types the script will look for.
# Format: ( 'Ore Name', ItemID, Hue )
ore_types = [
    # Iron
    ( 'Iron Ore', 0x19B9, 0x0000 ),
    ( 'Iron Ore', 0x19B8, 0x0000 ),
    ( 'Iron Ore', 0x19B7, 0x0000 ),
    ( 'Iron Ore', 0x19BA, 0x0000 ),
    # Dull CopperD
    ( 'Dull Copper Ore', 0x19B9, 0x0973 ),
    ( 'Dull Copper Ore', 0x19B8, 0x0973 ),
    ( 'Dull Copper Ore', 0x19B7, 0x0973 ),
    ( 'Dull Copper Ore', 0x19BA, 0x0973 ),
    # Shadow IronD
    ( 'Shadow Iron Ore', 0x19B9, 0x0966 ),
    ( 'Shadow Iron Ore', 0x19B8, 0x0966 ),
    ( 'Shadow Iron Ore', 0x19B7, 0x0966 ),
    ( 'Shadow Iron Ore', 0x19BA, 0x0966 ),
    # CopperD
    ( 'Copper Ore', 0x19B9, 0x096d ),
    ( 'Copper Ore', 0x19B8, 0x096d ),
    ( 'Copper Ore', 0x19B7, 0x096d ),
    ( 'Copper Ore', 0x19BA, 0x096d ),
    # BronzeD
    ( 'Bronze Ore', 0x19B9, 0x0972 ),
    ( 'Bronze Ore', 0x19B8, 0x0972 ),
    ( 'Bronze Ore', 0x19B7, 0x0972 ),
    ( 'Bronze Ore', 0x19BA, 0x0972 ),
    # GoldenD
    ( 'Golden Ore', 0x19B9, 0x08a5 ),
    ( 'Golden Ore', 0x19B8, 0x08a5 ),
    ( 'Golden Ore', 0x19B7, 0x08a5 ),
    ( 'Golden Ore', 0x19BA, 0x08a5 ),
    # AgapiteD
    ( 'Agapite Ore', 0x19B9, 0x0979 ),
    ( 'Agapite Ore', 0x19B8, 0x0979 ),
    ( 'Agapite Ore', 0x19B7, 0x0979 ),
    ( 'Agapite Ore', 0x19BA, 0x0979 ),
    # VeriteD
    ( 'Verite Ore', 0x19B9, 0x089f ),
    ( 'Verite Ore', 0x19B8, 0x089f ),
    ( 'Verite Ore', 0x19B7, 0x089f ),
    ( 'Verite Ore', 0x19BA, 0x089f ),
    # ValoriteD
    ( 'Valorite Ore', 0x19B9, 0x08ab ),
    ( 'Valorite Ore', 0x19B8, 0x08ab ),
    ( 'Valorite Ore', 0x19B7, 0x08ab ),
    ( 'Valorite Ore', 0x19BA, 0x08ab )
]


# Delay in milliseconds after each smelt action.
# Increase this if you get "You must wait..." messages.
SMELT_DELAY = 2000

# --- Script Start ---

Misc.SendMessage(">> Starting Ore Smelting Script...", 68)

# 1. Get the ore container
Misc.SendMessage(">> Please target the container with your ore.", 68)
ore_container_serial = Target.PromptTarget()
if ore_container_serial == 0:
    Misc.SendMessage(">> Canceled. No container selected.", 33)
    Stop
ore_container = Items.FindBySerial(ore_container_serial)
if ore_container is None or not ore_container.IsContainer:
    Misc.SendMessage(">> Canceled. Invalid container selected.", 33)
    Stop

# 2. Get the forge
Misc.SendMessage(">> Please target a forge.", 68)
forge_serial = Target.PromptTarget()
if forge_serial == 0:
    Misc.SendMessage(">> Canceled. No forge selected.", 33)
    Stop
# We only need the serial for the forge, no need to find the item object.

# 3. Main smelting loop
Misc.SendMessage(">> Beginning smelting process...", 68)
Misc.Pause(1000)

for ore_name, ore_id, ore_hue in ore_types:
    while True:
        # Find a stack of the current ore type in the container
        # The 'False' flag prevents it from looking in sub-containers, which is faster.
        # Change to 'True' if your ore is in bags inside the main container.
        ore_stack = Items.FindByID(ore_id, ore_hue, ore_container_serial, False)
        
        # If no more stacks of this type are found, move to the next ore type
        if ore_stack is None:
            break
            
        Misc.SendMessage(">> Smelting {}...".format(ore_name), 78)
        
        # Smelting process: Double-click the ore, then target the forge.
        Items.UseItem(ore_stack)
        
        # Wait for the target cursor to appear
        if Target.WaitForTarget(2000):
            Target.TargetExecute(forge_serial)
            
            # Add a brief pause to allow the server to send a journal message
            Misc.Pause(500)
            
            # Check if the ore pile was too small
            if Journal.Search("There is not enough"):
                Misc.SendMessage(">> Not enough ore in this pile. Ignoring it.", 138)
                Misc.IgnoreObject(ore_stack) # Ignore this specific small pile
                continue # Continue to the next iteration of the while loop to find another stack
                
            # Pause to allow the server to process a successful smelt
            Misc.Pause(SMELT_DELAY)
        else:
            Misc.SendMessage(">> Error: Timed out waiting for target after using ore.", 33)
            # We break the inner loop to avoid getting stuck on this ore type
            break

# Clean up any items that were ignored during the process
Misc.ClearIgnore()
Misc.SendMessage(">> Ore smelting script finished.", 68)
# --- Script End ---
