import bpy
import bmesh
import os.path
from math import radians
from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       EnumProperty,
                       PointerProperty,
                       )
from bpy.types import (Panel,
                       Operator,
                       PropertyGroup,
                       AddonPreferences,
                       )
                       
class Key(object):
    name = "";
    description = "";
    type = "";
    
    def __init__(self, name = "unknown", description = "unknown", type = "string"):
        self.name = name
        self.description = description
        self.type = type
        
def string_key(name, description):
    return Key(name, description, "string")
def int_key (name, description):
    return Key(name, description, "integer")
def float_key (name, description):
    return Key(name, description, "float")
def point_key (name, description):
    return Key(name, description, "point")
def description_key (name, description):
    return Key(name, description, "description")
                       
class Entity(object):
    name = "";
    description = "";
    spawnflags = [];
    keys = [];
    
def _decal():
    ent = Entity()
    ent.name = "_decal"
    ent.keys.append(
        string_key(
        "target",
        "The name of the entity targeted at for projection."
        ))
    return ent
        
def _skybox():
    ent = Entity()
    ent.name = "_skybox"
    ent.keys.append(
        description_key(
        "angles",
        "Individual control of PITCH, YAW, and ROLL"
        ))
    ent.keys.append(
        description_key(
        "scale",
        "scaling factor (default 64), good values are between 50 and 300, depending on the map."
        ))
    return ent

def ammo_blaster():
    ent = Entity()
    ent.name = "ammo_blaster"
    ent.keys.append(
        float_key(
        "wait",
        "Time in seconds before item respawns after being picked up (default 5, -1 = never respawn)."
        ))
    ent.keys.append(
        float_key(
        "random",
        "Random time variance in seconds added or subtracted from 'wait' delay (default 0 - see Notes)."
        ))
    ent.keys.append(
        int_key(
        "count",
        "Sets the amount of ammo given to the player when weapon is picked up."
        ))
    ent.keys.append(
        int_key(
        "team",
        "Set this to team items. Teamed items will respawn randomly after team master is picked up (see Notes)."
        ))
    ent.keys.append(
        string_key(
        "target",
        "picking up the item will trigger the entity this points to."
        ))
    ent.keys.append(
        string_key(
        "targetname",
        "A target_give entity can point to this for respawn freebies."
        ))
    ent.keys.append(
        int_key(
        "notfree",
        "When set to 1, entity will not spawn in 'Free for all' and 'Tournament' modes."
        ))
    ent.keys.append(
        int_key(
        "notteam",
        "When set to 1, entity will not spawn in 'Teamplay' and 'CTF' modes."
        ))
    ent.keys.append(
        int_key(
        "notsingle",
        "When set to 1, entity will not spawn in Single Player mode (bot play mode)."
        ))
    ent.keys.append(
        int_key(
        "notbot",
        "When set to 1, bots will not be able to see or use this entity."
        ))
    
    ent.spawnflags.append(
        "suspended"
        )
    return ent

def ammo_detpack():
    ent = Entity()
    ent.name = "ammo_detpack"
    ent.keys.append(
        float_key(
        "wait",
        "Time in seconds before item respawns after being picked up (default 5, -1 = never respawn)."
        ))
    ent.keys.append(
        float_key(
        "random",
        "Random time variance in seconds added or subtracted from 'wait' delay (default 0 - see Notes)."
        ))
    ent.keys.append(
        int_key(
        "count",
        "Sets the amount of ammo given to the player when weapon is picked up."
        ))
    ent.keys.append(
        int_key(
        "team",
        "Set this to team items. Teamed items will respawn randomly after team master is picked up (see Notes)."
        ))
    ent.keys.append(
        string_key(
        "target",
        "picking up the item will trigger the entity this points to."
        ))
    ent.keys.append(
        string_key(
        "targetname",
        "A target_give entity can point to this for respawn freebies."
        ))
    ent.keys.append(
        int_key(
        "notfree",
        "When set to 1, entity will not spawn in 'Free for all' and 'Tournament' modes."
        ))
    ent.keys.append(
        int_key(
        "notteam",
        "When set to 1, entity will not spawn in 'Teamplay' and 'CTF' modes."
        ))
    ent.keys.append(
        int_key(
        "notsingle",
        "When set to 1, entity will not spawn in Single Player mode (bot play mode)."
        ))
    ent.keys.append(
        int_key(
        "notbot",
        "When set to 1, bots will not be able to see or use this entity."
        ))
    ent.spawnflags.append(
        "suspended"
        )
    return ent

def info_player_start():
    ent = Entity()
    ent.name = "info_player_start"
    ent.keys.append(
        string_key(
        "target",
        "Targets will be fired when someone spawns in on them. "
        ))
    ent.keys.append(
        int_key(
        "notfree",
        "When set to 1, entity will not spawn in 'Free for all' and 'Tournament' modes."
        ))
    ent.keys.append(
        int_key(
        "notteam",
        "When set to 1, entity will not spawn in 'Teamplay' and 'CTF' modes."
        ))
    ent.keys.append(
        int_key(
        "notsingle",
        "When set to 1, entity will not spawn in Single Player mode (bot play mode)."
        ))
    ent.keys.append(
        int_key(
        "notbots",
        "When set to 1, bots will not be able to see or use this entity."
        ))
    ent.keys.append(
        int_key(
        "nohumans",
        "Will prevent non-bots from using this spot."
        ))
    return ent

def misc_model():
    ent = Entity()
    ent.name = "misc_model"
    ent.keys.append(
        string_key(
        "model",
        "arbitrary .md3 or .ase file to display  "
        ))
    ent.keys.append(
        int_key(
        "_rs",
        "(or _receiveshadows) - Allows per-entity control over shadow reception. Defaults to 1 on everything. 0 = receives no shadows, 1 = receives world shadows. Can be used in conjunction with _cs (or _castshadows) for tighter control of where, exactly, certain shadows fall. A _rs value greater than 1 (say, '7') would receive world shadows, as well as shadows from any entity with a corresponding _cs value ('7' again). A _rs value less than 1 (say, '-7') would receive shadows only from entities with a corresponding _cs value ('-7') and not receive world shadows. _rs is used on any entity.  "
        ))
    ent.keys.append(
        int_key(
        "_cs",
        "(or _castshadows) Allows per-entity control over shadow casting. Defaults to 0 on entities, 1 on world. 0 = no shadow casting, 1 = casts shadows on world. Can be used in conjunction with _rs (or _receiveshadows) for tighter control of where, exactly, certain shadows fall. A _cs value greater than 1 (say, '7') would cast shadows on the world, and on any entity with a corresponding _rs value ('7' again, in our case) as well. A _cs value less than 1 (say, '-7') would cast shadows only on entities with a corresponding _rs value ('-7') and not cast shadows on the world. _cs is used on any entity. misc_model entities, which are static, belongs to world.  "
        ))
    ent.keys.append(
        int_key(
        "_remap",
        "Remap the shader of a model (*See notes.)  "
        ))
    ent.spawnflags.append(
        "rmg"
        )
    ent.spawnflags.append(
        "solid"
        )
    ent.spawnflags.append(
        "lit"
        )
    return ent

ent_list = {}
ent_list["_decal"] = _decal()
ent_list["_skybox"] = _skybox()
ent_list["ammo_blaster"] = ammo_blaster()
ent_list["ammo_detpack"] = ammo_detpack()
ent_list["info_player_start"] = info_player_start()
ent_list["misc_model"] = misc_model()

for ent in ent_list:
    print (ent_list[ent].name)