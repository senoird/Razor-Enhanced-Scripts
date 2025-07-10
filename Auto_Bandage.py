# Razor Enhanced Auto-Heal Script
#
# What it does:
# 1. Continuously monitors your character's health.
# 2. If health drops below the configured threshold (default 90%), it will
#    automatically find and use a bandage on you.
# 3. It includes a timer to prevent re-bandaging before the previous one has finished.
#
# How to use:
# 1. Place this script in your Razor Enhanced 'Scripts' folder.
# 2. Run the script. It will run in the background.
# 3. To stop the script, you must manually stop it from the Razor Enhanced scripts tab.

# --- Configuration ---

# The health percentage below which the script will attempt to heal.
HEALTH_THRESHOLD = 90

# The time (in milliseconds) to wait after applying a bandage before trying another.
# This should be long enough for the bandage to complete its healing.
# 10000ms (10 seconds) is a safe value for most servers.
BANDAGE_DELAY = 5000

# The ItemID for clean bandages.
BANDAGE_ID = 0x0E21

# --- Script Start ---

Misc.SendMessage(">> Auto-Heal Script Started. Monitoring health...", 68)

while True:
    # Pause at the start of each loop to prevent high CPU usage.
    Misc.Pause(500)
    
    # Check if a bandage timer is already active. If so, do nothing.
    if Timer.Check("bandage"):
        continue

    # Calculate current health percentage
    # We use float() to ensure the division is accurate.
    health_percent = (float(Player.Hits) / float(Player.HitsMax)) * 100
    
    # 1. Check if health is below the threshold
    if health_percent < HEALTH_THRESHOLD:
        
        # 2. Find bandages in the backpack
        bandages = Items.FindByID(BANDAGE_ID, -1, Player.Backpack.Serial)
        
        if bandages is not None:
            Misc.SendMessage(">> Health is low! Applying bandages...", 78)
            
            # 3. Use the bandage on yourself
            Items.UseItem(bandages)
            
            # Wait for the target cursor to appear before targeting.
            if Target.WaitForTarget(1000):
                Target.Self()
            else:
                Misc.SendMessage(">> Error: Timed out waiting for bandage target.", 33)
                continue # Skip setting the timer and try again on the next loop.
            
            # 4. Set a timer to prevent spamming bandages
            # This ensures we wait for the current bandage to finish.
            Timer.Create("bandage", BANDAGE_DELAY)
        else:
            # If no bandages are found, notify the user and stop the script.
            Misc.SendMessage(">> Out of bandages! Stopping Auto-Heal script.", 33)
            Stop

# --- Script End ---
