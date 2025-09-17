# Simple Imbuing Material Looter for Razor Enhanced
# Auto-loots gold, gems, and items with "major magic" or "artifact" for unraveling

# Configuration
LOOT_DELAY = 500  # Delay between looting items in milliseconds
MAX_LOOT_ATTEMPTS = 20  # Maximum items to loot per corpse
CORPSE_TIMEOUT = 5000  # How long to wait for corpse contents to load

# Gem ItemIDs (common gems in UO)
GEM_IDS = [
    0x0F0F,  # Emerald
    0x0F10,  # Sapphire
    0x0F11,  # Ruby
    0x0F15,  # Star Sapphire
    0x0F16,  # Emerald
    0x0F18,  # Diamond
    0x0F21,  # Citrine
    0x0F25,  # Amber
    0x0F26,  # Amethyst
    0x3197,  # Perfect Emerald
    0x3198,  # Dark Sapphire
    0x3199,  # Turquoise
    0x3192,  # Ecru Citrine
    0x3193,  # Fire Ruby
    0x3194,  # Blue Diamond
    0x3195,  # Brilliant Amber
    0x3196   # Perfect Emerald
]

def is_imbuing_material(item):
    """Check if item has 'major magic', 'artifact', is gold, or is a gem"""
    try:
        # Always loot gold
        if item.ItemID == 0x0EED:  # Gold pile
            return True, "Gold"
        
        # Check gems by ItemID
        if item.ItemID in GEM_IDS:
            return True, "Gem"
        
        # Wait for item properties to load if not already loaded
        if not item.PropsUpdated:
            Items.WaitForProps(item, 1000)
        
        # Get item properties as text
        props = Items.GetPropStringList(item)
        if not props:
            return False, "No properties"
        
        # Join all properties into one string for easier searching
        all_props = ' '.join(props).lower()
        
        # Check for "major magic"
        if 'major magic' in all_props:
            return True, "Major Magic"
        
        # Check for "artifact"
        if 'artifact' in all_props:
            return True, "Artifact"
        
        return False, "Not major magic or artifact"
        
    except Exception as e:
        Misc.SendMessage(f"Error checking item: {str(e)}", 33)
        return False, f"Error: {str(e)}"

def loot_corpse(corpse):
    """Loot imbuing materials from a corpse"""
    try:
        Misc.SendMessage(f"Examining corpse: 0x{corpse.Serial:08X}", 88)
        
        # Wait for corpse contents to load
        Items.WaitForContents(corpse, CORPSE_TIMEOUT)
        
        if not corpse.Contains:
            Misc.SendMessage("Corpse is empty or contents not loaded", 33)
            return
        
        looted_count = 0
        
        # Check each item in the corpse
        for item in corpse.Contains:
            if looted_count >= MAX_LOOT_ATTEMPTS:
                Misc.SendMessage("Max loot attempts reached", 33)
                break
            
            is_imbuing, reason = is_imbuing_material(item)
            
            if is_imbuing:
                try:
                    # Move item to backpack
                    Items.Move(item, Player.Backpack, -1)
                    Misc.Pause(LOOT_DELAY)
                    
                    looted_count += 1
                    item_name = item.Name if item.Name else f"ItemID: 0x{item.ItemID:04X}"
                    Misc.SendMessage(f"Looted for imbuing: {item_name} ({reason})", 68)
                    
                except Exception as e:
                    Misc.SendMessage(f"Failed to loot {item.Name}: {str(e)}", 33)
        
        if looted_count == 0:
            Misc.SendMessage("No imbuing materials found in corpse", 88)
        else:
            Misc.SendMessage(f"Successfully looted {looted_count} items for imbuing!", 68)
            
    except Exception as e:
        Misc.SendMessage(f"Error looting corpse: {str(e)}", 33)

def find_open_corpse():
    """Find an open corpse container"""
    try:
        # Create filter for corpses
        corpse_filter = Items.Filter()
        corpse_filter.Enabled = True
        corpse_filter.OnGround = 1
        corpse_filter.IsCorpse = 1
        corpse_filter.RangeMax = 2  # Only corpses within 2 tiles
        
        # Get all nearby corpses
        corpses = Items.ApplyFilter(corpse_filter)
        
        # Look for corpses that have been recently opened (have contents loaded)
        for corpse in corpses:
            # Check if corpse is already opened by looking for contents
            if corpse.Contains and len(corpse.Contains) > 0:
                return corpse
        
        return None
        
    except Exception as e:
        Misc.SendMessage(f"Error finding corpse: {str(e)}", 33)
        return None

def main():
    """Main script loop"""
    Misc.SendMessage("Imbuing Material Looter started!", 68)
    Misc.SendMessage("Auto-looting major magic and artifact items for unraveling.", 88)
    
    last_looted_corpse = None
    
    while True:
        try:
            # Find an open corpse
            corpse = find_open_corpse()
            
            if corpse and corpse.Serial != last_looted_corpse:
                loot_corpse(corpse)
                last_looted_corpse = corpse.Serial
                
            # Small delay to prevent excessive CPU usage
            Misc.Pause(250)
            
        except KeyboardInterrupt:
            Misc.SendMessage("Script stopped by user", 33)
            break
        except Exception as e:
            Misc.SendMessage(f"Unexpected error: {str(e)}", 33)
            Misc.Pause(1000)  # Wait a second before retrying

# Start the script
if __name__ == "__main__":
    main()
