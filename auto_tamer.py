'''
Author: Aga - original author of the uosteam script
Other Contributors: TheWarDoctorDoctor95 - converted to Razor Enhanced script
Last Contribution By: TheWarDoctor95 - March 19, 2019
Modified by Gemini to be a standalone script with improved reliability and features.

Description: Tames nearby animals to train Animal Taming to GM. This script has been
refactored to fix bugs, implement missing logic, and improve robustness based on the
Razor Enhanced API.
'''

# --- Imports ---
from System.Collections.Generic import List
from System import Int32, Byte

## Script options ##
# Change to the name that you want to rename the tamed animals to
renameTamedAnimalsTo = 'bacon'
# Add any name of pets to ignore
petsToIgnore = [
    renameTamedAnimalsTo,
    # My animals
    'Magmaguard', 'Saphira', 'Your Worst Nightmare',
    # Viper's animals
    'Murder Pony', 'Toothless',
]
# Change to the number of followers you'd like to keep.
numberOfFollowersToKeep = 1
# Set to the maximum number of times to attempt to tame a single animal. 0 == attempt until tamed
maximumTameAttempts = 15
# Set the minimum taming difficulty to use when finding animals to tame
minimumTamingDifficulty = 10.0
# MODIFIED: Set the maximum taming difficulty relative to your current skill level.
# A value of 10.0 would let the script try to tame creatures up to 10 points
# higher than your skill. Set to 0.0 to only tame creatures at or below your skill level.
maximumDifficultyOffset = 0.0
# Set this to how you would like to heal your character if they take damage
# Options are: 'Healing', 'Magery', 'None'
healUsing = 'None'
# True or False to use Peacemaking if needed
enablePeacemaking = False
# True or False to track the animal being tamed
enableFollowAnimal = True
# Change depending on the latency to your UO shard
journalEntryDelayMilliseconds = 100
targetClearDelayMilliseconds = 100

# --- Tameable Animal Data (Replaces external file) ---
tameable_data = {
    # Min skill 0
    0x00D9: 0.0,   # dog
    0x001D: 0.0,   # gorilla
    0x033F: 0.0,   # parrot
    0x00CD: 0.0,   # rabbit
    0x012E: 0.0,   # skittering hopper
    0x0116: 0.0,   # squirrel
    0x0027: 0.0,   # mongbat
    # Min skill 10
    0x0006: 10.0,  # bird (various)
    0x083E: 10.0,  # starling
    0x00C9: 10.0,  # cat
    0x00D0: 10.0,  # chicken
    0x0058: 10.0,  # mountain goat
    0x00EE: 10.0,  # rat
    # Min skill 20
    0x00E7: 20.0,  # cow (brown)
    0x00D8: 20.0,  # cow (black)
    0x00D1: 20.0,  # goat
    0x00CB: 20.0,  # pig
    0x00CF: 20.0,  # sheep
    0x0317: 20.0,  # giant beetle
    0x0033: 20.0,  # slime
    # Min skill 30
    0x0005: 30.0,  # eagle
    # Min skill 40
    0x0122: 40.0,  # boar
    0x0051: 40.0,  # bullfrog
    0x0117: 40.0,  # ferret
    0x00D7: 40.0,  # giant rat
    0x00ED: 40.0,  # hind
    0x00C8: 40.0,  # horse
    0x00E2: 40.0,  # horse2
    0x00CC: 40.0,  # horse3
    0x00E4: 40.0,  # horse4
    0x0123: 40.0,  # pack horse
    0x0124: 40.0,  # pack llama
    0x00D2: 40.0,  # desert ostard
    0x00DB: 40.0,  # forest ostard
    0x00E1: 40.0,  # timber wolf
    0x0115: 40.0,  # rideable wolf
    # Min skill 50
    0x00D3: 50.0,  # black bear
    0x00D5: 50.0,  # polar bear
    0x00DC: 50.0,  # llama
    0x00DD: 50.0,  # walrus
    # Min skill 60
    0x00CA: 60.0,  # alligator
    0x00A7: 60.0,  # brown bear
    0x003F: 60.0,  # cougar
    0x0030: 60.0,  # scorpion
    # Min skill 70
    0x00D4: 70.0,  # grizzly bear
    0x003C: 70.0,  # young dragon (drake)
    0x00EA: 70.0,  # great hart
    0x0040: 70.0,  # snow leopard
    0x0041: 70.0,  # snow leopard2
    0x00D6: 70.0,  # panther
    0x0034: 70.0,  # snake
    0x001C: 70.0,  # giant spider
    0x0019: 70.0,  # grey wolf (light)
    0x001B: 70.0,  # grey wolf (dark)
    # Min skill 80
    0x0022: 80.0,  # white wolf (dark)
    0x0025: 80.0,  # white wolf (light)
    # Min skill 90
    0x00E8: 90.0,  # bull (solid)
    0x00E9: 90.0,  # bull (spotted)
    0x0647: 90.0,  # hellcat (small) - Note: This is a color, using Body 0x00C9
    0x00DA: 90.0,  # frenzied ostard
    0x0014: 90.0,  # frost spider
    0x0050: 90.0,  # giant toad / giant ice worm
    # Min skill 100
    0x003D: 100.0, # drake (red)
    0x007F: 100.0, # hellcat (large)
    0x0062: 100.0, # hellhound
    0x004A: 100.0, # imp
    0x00CE: 100.0, # lava lizard
    0x00BB: 100.0, # ridgeback
    0x00BC: 100.0, # savage ridgeback
    0x0017: 100.0, # dire wolf
    # Min skill 110
    0x00F4: 110.0, # rune beetle
    0x003B: 110.0, # dragon
    0x000B: 110.0, # dread spider
    0x00B4: 110.0, # white wyrm
    # Min skill 120
    0x006A: 120.0, # shadow wyrm
}

# --- Timers ---
noAnimalsToTrainTimerMilliseconds = 10000
catchUpToAnimalTimerMilliseconds = 20000
animalTamingTimerMilliseconds = 13000
peacemakingTimerMilliseconds = 10000
bandageTimerMilliseconds = 5000

# --- Globals for script logic ---
recently_tamed_serials = []


def GetAnimalsInSkillRange(min_difficulty, max_offset):
    """
    Gets a list of Body IDs for animals that are within the player's tameable range.
    """
    animal_ids = List[Int32]()
    current_skill = Player.GetSkillValue('Animal Taming')
    max_difficulty = current_skill + max_offset
    
    Misc.SendMessage("Current Taming: %.1f. Targeting difficulty range: %.1f to %.1f" % (current_skill, min_difficulty, max_difficulty), 90)

    for body_id, tame_diff in tameable_data.items():
        if tame_diff >= min_difficulty and tame_diff <= max_difficulty:
            animal_ids.Add(body_id)
    return animal_ids

def FindBandage():
    return Items.FindByID(0x0E21, -1, Player.Backpack.Serial)

def FindInstrument():
    instrument_ids = [0x0EB1, 0x0EB2, 0x0EB3, 0x0E9C]
    for item in Player.Backpack.Contains:
        if item.ItemID in instrument_ids:
            return item
    return None

def FindAnimalToTame():
    '''
    Finds the best animal to tame nearby, prioritizing the highest difficulty for skill gain.
    '''
    global minimumTamingDifficulty, recently_tamed_serials, maximumDifficultyOffset

    animalFilter = Mobiles.Filter()
    animalFilter.Enabled = True
    animalFilter.Bodies = GetAnimalsInSkillRange(minimumTamingDifficulty, maximumDifficultyOffset)
    animalFilter.RangeMin = 0
    animalFilter.RangeMax = 12
    animalFilter.IsHuman = 0
    animalFilter.IsGhost = 0
    animalFilter.CheckIgnoreObject = True

    tameableMobiles = Mobiles.ApplyFilter(animalFilter)
    
    valid_mobiles = []
    for mobile in tameableMobiles:
        if not (mobile.Name in petsToIgnore or mobile.Serial in recently_tamed_serials):
            valid_mobiles.append(mobile)

    if not valid_mobiles:
        return None

    best_target = None
    highest_difficulty = -1.0

    for mobile in valid_mobiles:
        difficulty = tameable_data.get(mobile.Body, -1.0)
        
        if difficulty > highest_difficulty:
            highest_difficulty = difficulty
            best_target = mobile
        elif difficulty == highest_difficulty:
            if best_target is None or Player.DistanceTo(mobile) < Player.DistanceTo(best_target):
                best_target = mobile
                
    return best_target


def FollowMobile(mobile, maxDistanceToMobile=2):
    Timer.Create('catchUpToAnimalTimer', catchUpToAnimalTimerMilliseconds)
    while Player.DistanceTo(mobile) > maxDistanceToMobile:
        if not Timer.Check('catchUpToAnimalTimer'):
            Misc.SendMessage('Timeout while trying to follow mobile.', 33)
            return False
        Player.PathFindTo(mobile.Position.X, mobile.Position.Y, mobile.Position.Z)
        Misc.Pause(1000)
        if not Mobiles.FindBySerial(mobile.Serial):
            Misc.SendMessage('Mobile disappeared while following.', 33)
            return False
    return True

def TrainAnimalTaming():
    global renameTamedAnimalsTo, numberOfFollowersToKeep, maximumTameAttempts
    global enablePeacemaking, enableFollowAnimal, healUsing, recently_tamed_serials

    if Player.GetRealSkillValue('Animal Taming') >= Player.GetSkillCap('Animal Taming'):
        Misc.SendMessage("You've already maxed out Animal Taming!", 65)
        return

    animalBeingTamed = None
    timesTried = 0
    Timer.Create('animalTamingTimer', 1)
    if enablePeacemaking:
        Timer.Create('peacemakingTimer', 1)
    if healUsing == 'Healing':
        Timer.Create('bandageTimer', 1)

    Journal.Clear()
    Misc.ClearIgnore()
    Player.SetWarMode(False)

    while not Player.IsGhost and Player.GetRealSkillValue('Animal Taming') < Player.GetSkillCap('Animal Taming'):
        Misc.Pause(100)

        if animalBeingTamed and not Mobiles.FindBySerial(animalBeingTamed.Serial):
            animalBeingTamed = None
            continue
        if animalBeingTamed and maximumTameAttempts > 0 and timesTried >= maximumTameAttempts:
            Misc.IgnoreObject(animalBeingTamed)
            animalBeingTamed = None
            timesTried = 0
            continue
        
        if enablePeacemaking and not Timer.Check('peacemakingTimer') and Journal.Search("is attacking you!"):
            instrument = FindInstrument()
            if instrument:
                Player.UseSkill('Peacemaking')
                Target.WaitForTarget(1000, False)
                Target.Self()
                Timer.Create('peacemakingTimer', peacemakingTimerMilliseconds)
                Misc.Pause(3000)
            else:
                Misc.SendMessage('No instrument found to use Peacemaking!', 33)

        if Player.Hits < Player.HitsMax and healUsing != 'None':
            if healUsing == 'Healing' and not Timer.Check('bandageTimer'):
                bandage = FindBandage()
                if bandage:
                    Items.UseItem(bandage)
                    Target.WaitForTarget(1000, False)
                    Target.Self()
                    Timer.Create('bandageTimer', bandageTimerMilliseconds)
            elif healUsing == 'Magery':
                required_mana = 11 if (Player.HitsMax - Player.Hits) > 30 else 4
                if Player.Mana >= required_mana:
                    spell = 'Greater Heal' if (Player.HitsMax - Player.Hits) > 30 else 'Heal'
                    Spells.CastMagery(spell)
                    Target.WaitForTarget(1000, False)
                    Target.Self()
                    Misc.Pause(2000)

        if animalBeingTamed is None:
            animalBeingTamed = FindAnimalToTame()
            if animalBeingTamed is None:
                Misc.SendMessage("No suitable animals found. Waiting...", 88)
                Misc.Pause(5000)
                continue
            else:
                Misc.SendMessage('Found animal to tame: %s' % animalBeingTamed.Name, 90)
                timesTried = 0

        if Player.DistanceTo(animalBeingTamed) > 2:
            if enableFollowAnimal:
                if not FollowMobile(animalBeingTamed, 2):
                    Misc.IgnoreObject(animalBeingTamed)
                    animalBeingTamed = None
                    continue
            else:
                Misc.IgnoreObject(animalBeingTamed)
                animalBeingTamed = None
                continue
        
        if not Timer.Check('animalTamingTimer'):
            Journal.Clear()
            Player.UseSkill('Animal Taming')
            Target.WaitForTarget(2000, True)
            Target.TargetExecute(animalBeingTamed)
            timesTried += 1
            
            # MODIFIED: Increased max wait time to 15 seconds.
            max_wait_ms = 15000
            wait_interval_ms = 500 # Using a slightly longer pause between checks
            time_waited = 0
            tame_result = "in_progress"
            
            while tame_result == "in_progress" and time_waited < max_wait_ms:
                # First, check for a success or failure message to end the loop early.
                if Journal.Search("It seems to accept you as master") or Journal.Search("That wasn't even challenging"):
                    tame_result = "success"
                    continue
                elif Journal.Search("You fail to tame the") or Journal.Search("You must wait") or Journal.Search("already tame") or Journal.Search("too far away"):
                    tame_result = "failure"
                    continue
                
                # MODIFIED: If still in progress, check distance and move closer without restarting.
                if Player.DistanceTo(animalBeingTamed) > 4:
                    Misc.SendMessage("Animal is moving, staying close...", 88)
                    Player.PathFindTo(animalBeingTamed.Position.X, animalBeingTamed.Position.Y, animalBeingTamed.Position.Z)
                    # Pause after moving to allow character to catch up
                    Misc.Pause(wait_interval_ms) 
                
                Misc.Pause(wait_interval_ms)
                time_waited += wait_interval_ms
            
            if tame_result == "success":
                tamed_serial = animalBeingTamed.Serial
                Misc.Pause(2500) 
                recently_tamed_serials.append(tamed_serial)
                if len(recently_tamed_serials) > 50:
                    recently_tamed_serials.pop(0)
                if animalBeingTamed.Name != renameTamedAnimalsTo:
                    Misc.PetRename(animalBeingTamed, renameTamedAnimalsTo)
                    Misc.Pause(1000)
                if Player.Followers >= numberOfFollowersToKeep:
                    followers_before_release = Player.Followers
                    tamed_animal_object = Mobiles.FindBySerial(tamed_serial)
                    if tamed_animal_object:
                        Mobiles.SingleClick(tamed_animal_object)
                        context_menu = Misc.WaitForContext(tamed_animal_object, 2000)
                        release_entry_number = -1
                        if context_menu:
                            for entry in context_menu:
                                if "release" in entry.Entry.lower():
                                    release_entry_number = entry.Response
                                    break
                        if release_entry_number != -1:
                            Misc.ContextReply(tamed_animal_object, release_entry_number)
                            release_gump_id = 0xd01621a
                            if Gumps.WaitForGump(release_gump_id, 3000):
                                Gumps.SendAction(release_gump_id, 2)
                                Misc.Pause(1500)
                Misc.IgnoreObject(tamed_serial)
                animalBeingTamed = None
            else:
                if Journal.Search("already tame") or Journal.Search("too far away"):
                    Misc.IgnoreObject(animalBeingTamed)
                animalBeingTamed = None
            Timer.Create('animalTamingTimer', 2000)

# Start Animal Taming
TrainAnimalTaming()
