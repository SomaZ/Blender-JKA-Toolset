bl_info = {
    "name": "Q3 map helper",
    "description": "This plugin is able to automaticly import fbx files made with Noesis from Q3 based bsp files. It also tries to join meshes based on their lightmap id, if Noesis exported an .meshlmid file too. Then there is a q3 shader interpreter for the cycles rendering engine. After you are satisfied with the scene lighting, you can tell the plugin to prepair lightmap baking. You can simply start baking lightmaps from the cycles baking tab. It will try baking lightmaps for every selected object in the scene",
    "author": "SomaZ",
    "version": (0, 7, 8),
    "blender": (2, 79, 0),
    "location": "3D View > Q3 Tools",
    "warning": "", # used for warning icon and text in addons panel
    "wiki_url": "",
    "tracker_url": "",
    "category": "Development"
}

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
                       
# ------------------------------------------------------------------------
#    functions
# ------------------------------------------------------------------------
def updatePreviewCube(self, context):
    addon_name = __name__.split('.')[0]
    prefs = context.user_preferences.addons[addon_name].preferences
    scene = context.scene
    q3mapImportTool = scene.q3mapImportTool
    basePath = prefs.base_path
    shaderPath = prefs.shader_dir
    
    try:
        shaderCube = bpy.data.objects["ShaderPreviewCube"]
        mesh = shaderCube.data
    except:
        # Create an empty mesh and the object.
        mesh = bpy.data.meshes.new('ShaderPreviewCube')
        shaderCube = bpy.data.objects.new("ShaderPreviewCube", mesh)
        
        # Add the object into the scene.
        scene.objects.link(shaderCube)
        scene.objects.active = shaderCube
        shaderCube.select = True
        
        # Construct the bmesh cube and assign it to the blender mesh.
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=10.0)
        bm.to_mesh(mesh)
        bm.free()
        
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_all(action='INVERT')
        bpy.ops.uv.reset()
        bpy.ops.object.mode_set(mode='OBJECT')
        
        mesh = scene.objects["ShaderPreviewCube"].data
        mesh.uv_textures[0].name = "UVMap"
        
    counter = 0
    for mat in mesh.materials:
        if (mat.name.lower().strip(" \t\r\n") == scene.q3mapImportTool.shader.lower().strip(" \t\r\n")):
            mesh.polygons[0].material_index = counter
            mesh.polygons[1].material_index = counter
            mesh.polygons[2].material_index = counter
            mesh.polygons[3].material_index = counter
            mesh.polygons[4].material_index = counter
            mesh.polygons[5].material_index = counter
            break
        counter += 1
  
def previewShader(self, context):
    
    addon_name = __name__.split('.')[0]
    prefs = context.user_preferences.addons[addon_name].preferences
    scene = context.scene
    q3mapImportTool = scene.q3mapImportTool
    
    basePath = prefs.base_path
    shaderPath = prefs.shader_dir

    try:
        shaderCube = bpy.data.objects["ShaderPreviewCube"]
        mesh = scene.objects["ShaderPreviewCube"].data
        mesh.materials.clear()
        mesh.uv_textures[0].name = "UVMap"
    except:
        # Create an empty mesh and the object.
        mesh = bpy.data.meshes.new('ShaderPreviewCube')
        shaderCube = bpy.data.objects.new("ShaderPreviewCube", mesh)
        
        # Add the object into the scene.
        scene.objects.link(shaderCube)
        scene.objects.active = shaderCube
        shaderCube.select = True
        
        # Construct the bmesh cube and assign it to the blender mesh.
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=10.0)
        bm.to_mesh(mesh)
        bm.free()
        
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_all(action='INVERT')
        bpy.ops.uv.reset()
        bpy.ops.object.mode_set(mode='OBJECT')
        
        mesh = scene.objects["ShaderPreviewCube"].data
        mesh.uv_textures[0].name = "UVMap"
        
    shaderList = []
    shaderList.append(basePath + shaderPath + scene.q3mapImportTool.shaderF + ".shader")
        
    for shaderFile in shaderList:
        try:
            isOpen = 0
            with open(shaderFile) as lines:
                for line in lines:
                    #skip empty lines or comments
                    if ((line.strip(" \t\r\n").startswith('/')) and (line.strip("\t\r\n") != ' ')): 
                        continue
                    #content
                    if not(line.strip(" \t\r\n").startswith('{')) and not(line.strip(" \t\r\n").startswith('}')):
                        if (isOpen == 0):
                            currentShader = line.strip(" \t\r\n")
                    #marker open
                    if line.strip(" \t\r\n").startswith('{'):
                        isOpen = isOpen + 1.
                    #marker close
                    if line.strip(" \t\r\n").startswith('}'):
                        #close material
                        if (isOpen == 1):
                            try:
                                mesh.materials.append(bpy.data.materials[currentShader])
                            except:
                                mat = bpy.data.materials.new(name= currentShader)
                                mesh.materials.append(mat)  
                                mat.use_nodes = True
                        isOpen -= 1                      
        except:
            print (('error in shaderfile ') + shaderFile)
    
    q3mapImportTool.onlyPreviewCube = True
    bpy.ops.q3map.interpret_shaders()
    q3mapImportTool.onlyPreviewCube = False
            
# ------------------------------------------------------------------------
#    store properties in the user preferences
# ------------------------------------------------------------------------
                       
class Q3MapHelperAddonPreferences(AddonPreferences):
    bl_idname = __name__

    base_path = StringProperty(
        name="basepath",
        description="It's the basepath",
        default="",
        maxlen=2048,
        )
        
    shader_dir = StringProperty(
        name="shader dir",
        description="It's the shader directory",
        default="shaders\\",
        maxlen=2048,
        )
        
    useGPU = BoolProperty(
        name="Enable GPU computing",
        description="This will automaticly make your GPU the cycles rendering device and adjusts tile size accordingly.",
        default = True
        )

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, "base_path")
        row.operator("q3map.get_basepath", icon="FILE_FOLDER", text="")
        layout.prop(self, "shader_dir")
        layout.prop(self, "useGPU")
                       
# ------------------------------------------------------------------------
#    store properties in the active scene
# ------------------------------------------------------------------------

class ImporterSettings(PropertyGroup):
    
    def shaderF_list_cb(self, context):
        
        addon_name = __name__.split('.')[0]
        prefs = context.user_preferences.addons[addon_name].preferences
        
        basePath = prefs.base_path
        shaderPath = prefs.shader_dir
        currentShader = ''
        
        shaderList = []
        try:
            currentShader = (basePath + shaderPath)
            dir = os.listdir(currentShader)
            for file in dir:
                currentShader = currentShader + file
                currentFile = file.split('.')[0]
                if file.lower().endswith('.shader'):
                    shaderList.append((currentFile,currentFile,""))
        except:
            print ('could not open shader ' + currentShader)
        return shaderList
    
    def shader_list_cb(self, context):
        
        addon_name = __name__.split('.')[0]
        prefs = context.user_preferences.addons[addon_name].preferences
        
        basePath = prefs.base_path
        shaderPath = prefs.shader_dir
        currentShader = ''
        
        shaderList = []
        shaderList.append(basePath + shaderPath + bpy.context.scene.q3mapImportTool.shaderF + ".shader")
        items = []
        for shaderFile in shaderList:
            try:
                isOpen = 0
                with open(shaderFile) as lines:
                    for line in lines:
                        #skip empty lines or comments
                        if ((line.strip(" \t\r\n").startswith('/')) and (line.strip("\t\r\n") != ' ')): 
                            continue
                        #content
                        if not(line.strip(" \t\r\n").startswith('{')) and not(line.strip(" \t\r\n").startswith('}')):
                            if (isOpen == 0):
                                currentShader = line.strip(" \t\r\n")
                        #marker open
                        if line.strip(" \t\r\n").startswith('{'):
                            isOpen = isOpen + 1.
                        #marker close
                        if line.strip(" \t\r\n").startswith('}'):
                            #close material
                            if (isOpen == 1):
                                items.append((currentShader,currentShader,""))
                            isOpen -= 1                      
            except:
                print (('error in shaderfile ') + shaderFile)
        return items
    
    shaderF = bpy.props.EnumProperty(items=shaderF_list_cb,
                                    name = "ShaderFile",
                                    update = previewShader)
                                    
    shader = bpy.props.EnumProperty(items=shader_list_cb,
                                    name = "Material",
                                    update = updatePreviewCube)
                                    
    deluxeMapped = BoolProperty(
        name="is the map deluxe mapped?",
        description="If the map is deluxemapped you will only see Lightmap names that are odd or even",
        default = False
        )
    
    gl2 = BoolProperty(
        name="gl2 Materials",
        description="are there gl2 compatible materials?",
        default = False
        )

    skyNumber = IntProperty(
        name = "Sky Number",
        description="",
        default = 0,
        min = 0,
        max = 100
        )
        
    lmSize = IntProperty(
        name = "Lightmap Size",
        description="Texture size for the new lightmaps",
        default = 128,
        min = 128,
        max = 1000000
        )

    default_emissive = FloatProperty(
        name = "Default emissive value",
        description = "",
        default = 1.0,
        min = 0.05,
        max = 1000.0
        )
        
    default_sky_emissive = FloatProperty(
        name = "Default sky emissive value",
        description = "",
        default = 5.0,
        min = 0.0,
        max = 1000.0
        )
    
    default_roughness = FloatProperty(
        name = "Default roughness value",
        description = "",
        default = 0.45,
        min = 0.0,
        max = 1.0
        )
    
    map_name = StringProperty(
        name="map name",
        description="It's the map name.",
        default="",
        maxlen=2048,
        )

    selectedShaderFile = StringProperty(
        name="ShaderFile:",
        default="",
        maxlen=2048,
        )
        
    #------------------
    # "private" variables
    #------------------
    
    onlyPreviewCube = BoolProperty(
        name="onlyPreviewCube",
        description="skip the sky and sun generation?",
        default = False
        )
    
# ------------------------------------------------------------------------
#    import panel in object mode
# ------------------------------------------------------------------------

class import_panel(Panel):
    bl_idname = "import_panel"
    bl_label = "Lightmapping helper"
    bl_space_type = "VIEW_3D"   
    bl_region_type = "TOOLS"    
    bl_category = "Q3 Tools"
    bl_context = "objectmode"   

    @classmethod
    def poll(self,context):
        return True

    def draw(self, context):
        addon_name = __name__.split('.')[0]
        self.prefs = context.user_preferences.addons[addon_name].preferences
        
        layout = self.layout
        scene = context.scene
        q3mapImportTool = scene.q3mapImportTool
        
        box = layout.box()
        box.prop(q3mapImportTool, "map_name")
        box.operator("q3map.import_map")
        
        box = layout.box()
        box.prop(q3mapImportTool, "gl2")
        box.prop(q3mapImportTool, "default_emissive")
        box.prop(q3mapImportTool, "default_roughness")
        box.prop(q3mapImportTool, "default_sky_emissive")
        box.prop(q3mapImportTool, "skyNumber")
        box.row().separator()
        box.label('This will recreate')
        box.label('all existing textures and shader nodes!')
        box.operator("q3map.interpret_shaders")
        
        box = layout.box()
        box.prop(q3mapImportTool, "deluxeMapped")
        box.prop(q3mapImportTool, "lmSize")
        box.operator("q3map.prepare_baking")
        box.operator("q3map.save_baked_lms")
        
# ------------------------------------------------------------------------
#    import panel in object mode
# ------------------------------------------------------------------------

class shader_panel(Panel):
    bl_idname = "shader_panel"
    bl_label = "Shader helper"
    bl_space_type = "VIEW_3D"   
    bl_region_type = "TOOLS"    
    bl_category = "Q3 Tools"
    bl_context = "objectmode"   

    @classmethod
    def poll(self,context):
        return True

    def draw(self, context):
        addon_name = __name__.split('.')[0]
        self.prefs = context.user_preferences.addons[addon_name].preferences
        
        layout = self.layout
        scene = context.scene
        q3mapImportTool = scene.q3mapImportTool
        
        box = layout.box()
        box.row().separator()
        box.prop(q3mapImportTool, "shaderF")
        box.prop(q3mapImportTool, "shader")
        box.operator("q3map.add_material")
        box.row().separator()
    
# ------------------------------------------------------------------------
#    operators
# ------------------------------------------------------------------------
                       
class WMFileSelector(bpy.types.Operator):
    bl_idname = "q3map.get_basepath"
    bl_label = "base Path"

    filepath = bpy.props.StringProperty(subtype="FILE_PATH") 

    def execute(self, context):
        addon_name = __name__.split('.')[0]
        self.prefs = context.user_preferences.addons[addon_name].preferences
        
        fdir = self.filepath
        self.prefs.base_path = fdir
        #context.scene.q3mapImportTool.base_path = fdir
        return{'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'} 

class ImportMap(bpy.types.Operator):
    bl_idname = "q3map.import_map"
    bl_label = "Import Map"
    
    def execute(self, context):
        
        addon_name = __name__.split('.')[0]
        self.prefs = context.user_preferences.addons[addon_name].preferences
        
        scene = bpy.context.scene
        q3mapImportTool = scene.q3mapImportTool
        basePath = self.prefs.base_path
        mapName = q3mapImportTool.map_name

        names = []
        values = []
        textures = []
        numEnts = 0
        numLms = 0
        file = basePath + 'maps/' + mapName 

        #clear meshes
        #for mesh in bpy.data.meshes:
            #if mesh.users > 0: 
                #mesh.user_clear()
            #bpy.data.meshes.remove(mesh)
            
        #clear meshes
        #for object in bpy.data.objects:
            #if object.users > 0: 
                #object.user_clear()
            #bpy.data.objects.remove(object)

        # import map .fbx
        try:
            imported_object = bpy.ops.import_scene.fbx(filepath=(file + 'out.fbx'))
        except:
            print ('could not load map: ' + file)

        #get Lightmap ID's
        try:
            with open(file + 'out.meshlmid') as lines:
                for line in lines:
                    first, rest = line.strip(" \t\r\n[]").split(' ', 1)
                    names.append(first)
                    values.append(int(rest))
                    numEnts += 1
                    numLms = max(numLms, int(rest))
        except:
            print ('File ' + file + ' not found')

        #lightmaps
        for i in range(-3, (numLms + 1)):
            bpy.ops.object.select_all(action='DESELECT')
            obs = []
            objects = []
            name = 'Lightmap_' + str(i).zfill(4)
            found = False
            
            #find all matching objects per lm id
            for j in range(0,numEnts):
                if values[j] == i:
                    objects.append(names[j])
                    
            #select objects by lm id
            for p in objects:   
                scene.objects[p].select = True
                obs = scene.objects[p]
                mesh = obs.data
                mesh.uv_textures['DiffuseUV'].name = "UVMap"
                scene.objects.active = scene.objects[p]
                found = True

            #join selected objects 
            if found == True:
                obs.name = name
                bpy.ops.object.join()
                bpy.context.scene.objects.active = obs
            print ('Objects with Lightmap number ' + str(i) + ' of ' + str(numLms) + ' joined.')
                
        misc_models = []
        misc_models_origins = []
        misc_models_scales = []
        misc_models_angles = []
        num_misc_models = 0

        #get misc_model_static's informations
        try:
            blockOpen = 0
            is_misc_model_static = False
            has_origin = False
            model = ''
            angle = 0.0
            origin = '0 0 0'
            modelscale = 1.0
            with open(file + '_converted.map') as lines:
                for line in lines:
                    try:
                        if (line.strip(" \t\r\n") == '{'):
                            blockOpen += 1
                            continue
                        if (line.strip(" \t\r\n") == '}'):
                            if is_misc_model_static and has_origin:
                                misc_models.append(model)
                                misc_models_origins.append(origin)
                                misc_models_scales.append(modelscale)
                                misc_models_angles.append(angle)
                                num_misc_models += 1
                            model = ''
                            origin = '0 0 0'
                            modelscale = 1.0
                            angle = 0.0
                            is_misc_model_static = False
                            has_origin = False
                            blockOpen -= 1
                            continue
                        if (blockOpen == 1) and (line.strip("\t\r\n") != '') and (line.strip(" \t\r\n").startswith('"')):
                            first, rest = line.strip("\t\r\n").split(' ', 1)
                            if (first == '"classname"') and (rest == '"misc_model_static"'):
                                is_misc_model_static = True
                            if (first == '"model"'):
                                model = rest.strip('"')
                            if (first == '"angle"'):
                                angle = rest.strip('"')
                            if (first == '"origin"'):
                                origin = (rest.strip('"'))
                                has_origin = True
                            if (first == '"modelscale"'):
                                modelscale = float(rest.strip('"'))
                    except:
                        print ('line skipped ')
        except:
            print ('could not parse all models from ' + file + '_converted.map')

        #add box placeholders for misc_model_statics or entitys, could be useful for other entities (SomaZ)
        #for mms in range(0, num_misc_models):
            #x,y,z = misc_models_origins[mms].strip("\t\r\n").split(' ', 2)
            
            #add cube as representative for the misc_model_static entity
            #bpy.ops.mesh.primitive_cube_add(location=(float(x)/100,float(y)/100,float(z)/100))
            
            #make cube smaller in the viewport
            #scale = (.2,.2,.1)
            #bpy.ops.transform.resize( value=scale ) #resizes the cube
            #bpy.ops.object.transform_apply( scale=True ) #don't forget to apply!!
            
            #ob = bpy.context.object #stores the active object (the cube created above)
            #ob.name= misc_models[mms]; ob.data.name = ob.name #just naming
            
            #resizes the cube, don't apply scale! We need it for the correct scale of all the entities!
            #scale = (misc_models_scales[mms],misc_models_scales[mms],misc_models_scales[mms])
            #bpy.ops.transform.resize( value=scale ) 

        #import fitting models
        addedModels = []
        scene_objects = []
        droppedModels = []
        linkedModels = 0
        for mms in range(0, num_misc_models):   
            toAdd = True
            for name in addedModels:
                if name == misc_models[mms]:
                    toAdd = False
            if toAdd:
                addedModels.append(misc_models[mms]);
                try:
                    imported_object = bpy.ops.import_scene.fbx(filepath=(basePath + misc_models[mms][:-4] + 'out.fbx'))
                    
                    scene.objects.active = bpy.context.selected_objects[0]
                    fbx_object = bpy.context.selected_objects[0]   
                    bpy.ops.object.join()
                    
                    fbx_object.name = misc_models[mms][:-4]
                    fbx_object.data.name = misc_models[mms][:-4]
                    
                    mesh = fbx_object.data
                    mesh.uv_textures['DiffuseUV'].name = "UVMap"
                    
                    #apply the given scale, should be 0.01 by default, but we make sure it is
                    scale = (.01,.01,.01)
                    fbx_object.scale = scale
                    bpy.ops.object.transform_apply( scale=True )
                    
                    fbx_object.hide = True
                    fbx_object.hide_render = True
                except:
                    droppedModels.append(misc_models[mms][:-4] + 'out.fbx')
                    print ('could not load model: ' + (basePath + misc_models[mms][:-4] + 'out.fbx'))
                    
            # add the misc_model_static linked to the imported model
            try:
                me = bpy.data.objects[misc_models[mms][:-4]].data
                ob = bpy.data.objects.new(misc_models[mms], me)        
                bpy.context.scene.objects.link(ob)
                bpy.context.scene.update()
            
                x,y,z = misc_models_origins[mms].strip("\t\r\n").split(' ', 2)
                ob.location = (float(x)/100,float(y)/100,float(z)/100)
                scale = (misc_models_scales[mms],misc_models_scales[mms],misc_models_scales[mms])
                ob.scale = scale
                ob.rotation_euler = (0.0,0.0,radians(float(misc_models_angles[mms])))
                linkedModels += 1
            except:
                print ('could not link model: ' + (misc_models[mms][:-4] + ' is not imported (Try exporting the model again from Noesis)'))
                
        if droppedModels:
            print ('Dropped models:')
            print (' ')
        for model in droppedModels:
            print (model)
            
        return{'FINISHED'}
    
class InterpretShaders(bpy.types.Operator):
    bl_idname = "q3map.interpret_shaders"
    bl_label = "Interpret Shaders"
    
    def execute(self, context):
        
        addon_name = __name__.split('.')[0]
        self.prefs = context.user_preferences.addons[addon_name].preferences
        
        scene = bpy.context.scene
        q3mapImportTool = scene.q3mapImportTool
        basePath = self.prefs.base_path
        useGPU = self.prefs.useGPU
        gl2 = q3mapImportTool.gl2
        onlyPreviewCube = q3mapImportTool.onlyPreviewCube
        processingObjects = []
        
        if (onlyPreviewCube):
            processingObjects.append(bpy.data.objects["ShaderPreviewCube"])
        else:
            for obj in scene.objects:
                processingObjects.append(obj )
                
        scene.render.engine = 'CYCLES'
        scene.cycles.transparent_min_bounces = 0
        scene.cycles.min_bounces = 0
        scene.cycles.transparent_max_bounces = 6
        scene.cycles.max_bounces = 6
        scene.cycles.transmission_bounces = 6
        scene.cycles.caustics_refractive = False
        scene.cycles.caustics_reflective = False
        #optimize rendering times
        if useGPU:
            scene.cycles.device = 'GPU'
            scene.render.tile_x = 256
            scene.render.tile_y = 256
        else:
            scene.cycles.device = 'CPU'
            scene.render.tile_x = 16
            scene.render.tile_y = 16
        
        if (gl2):
            nodeType = "ShaderNodeBsdfPrincipled"
        else:
            nodeType = "ShaderNodeBsdfDiffuse"
        
        shaderPath = self.prefs.shader_dir
        
        
        defaultRoughness = q3mapImportTool.default_roughness
        defaultEmissive = q3mapImportTool.default_emissive
        defaultSkyEmissive = q3mapImportTool.default_sky_emissive
        skyNumber = q3mapImportTool.skyNumber

        #delete all material nodes and textures
        if (not onlyPreviewCube):
            bpy.ops.object.select_all(action='DESELECT')
            for ob in scene.objects:
                ob.select = False
                if ob.type == 'MESH' and ob.name.startswith("Sky"):
                    ob.select = True
                    bpy.ops.object.delete()
                if ob.name.startswith("Sun"):
                    ob.select = True
                    bpy.ops.object.delete()

            for img in bpy.data.images: 
                img.user_clear()
            for img in bpy.data.images: 
                if not img.users:
                    bpy.data.images.remove(img)
                
            for tex in bpy.data.textures:
                tex.user_clear()
            for tex in bpy.data.textures:
                if not tex.users:
                    bpy.data.textures.remove(tex)
                
            for a in bpy.data.materials:
                if a.use_nodes:
                    a.node_tree.nodes.clear()
                    node_output = a.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
                    node_output.location = 400,100
                    
                    node_DiffuseBSDF = a.node_tree.nodes.new(type = nodeType)
                    node_DiffuseBSDF.location = 200,100
                    node_DiffuseBSDF.name = 'Shader'
                    
                    node_Mix = a.node_tree.nodes.new(type='ShaderNodeMixShader')
                    node_Mix.location = 400,300
                    
                    node_Mix.inputs[0].default_value = 1.0
                    
                    node_Transparent = a.node_tree.nodes.new(type='ShaderNodeBsdfTransparent')
                    node_Transparent.location = 200,300
                    
                    links = a.node_tree.links
                    link = links.new(node_DiffuseBSDF.outputs[0], node_Mix.inputs[2])
                    link = links.new(node_Transparent.outputs[0], node_Mix.inputs[1])
                    link = links.new(node_Mix.outputs[0], node_output.inputs[0])
                else:
                    a.use_nodes = True
                    a.node_tree.nodes.clear()
                    node_output = a.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
                    node_output.location = 400,100
                    
                    node_DiffuseBSDF = a.node_tree.nodes.new(type = nodeType)
                    node_DiffuseBSDF.location = 200,100
                    node_DiffuseBSDF.name = 'Shader'
                    
                    node_Mix = a.node_tree.nodes.new(type='ShaderNodeMixShader')
                    node_Mix.location = 400,300
                    
                    node_Mix.inputs[0].default_value = 1.0
                    
                    node_Transparent = a.node_tree.nodes.new(type='ShaderNodeBsdfTransparent')
                    node_Transparent.location = 200,300
                    
                    links = a.node_tree.links
                    link = links.new(node_DiffuseBSDF.outputs[0], node_Mix.inputs[2])
                    link = links.new(node_Transparent.outputs[0], node_Mix.inputs[1])
                    link = links.new(node_Mix.outputs[0], node_output.inputs[0])
        else:
            for a in bpy.data.materials:
                a.use_nodes = True
                
                try:
                    nodes = a.node_tree.nodes
                    links = a.node_tree.links
                    try:
                        node_DiffuseBSDF = nodes.get("Diffuse BSDF")
                    except:
                        node_DiffuseBSDF = a.node_tree.nodes.new(type = nodeType)
                        node_DiffuseBSDF.location = 200,100
                    node_DiffuseBSDF.name = 'Shader'
                    
                    try:
                        node_Mix = nodes.get("Mix Shader")
                    except:
                        node_Mix = a.node_tree.nodes.new(type = nodeType)
                        node_Mix.location = 400,300
                    node_Mix.inputs[0].default_value = 1.0
                    
                    try:
                        node_Transparent = nodes.get("Transparent BSDF")
                    except:
                        node_Transparent = a.node_tree.nodes.new(type = nodeType)
                        node_Transparent.location = 200,300
                        
                    link = links.new(node_DiffuseBSDF.outputs[0], node_Mix.inputs[2])
                    link = links.new(node_Transparent.outputs[0], node_Mix.inputs[1])
                    link = links.new(node_Mix.outputs[0], node_output.inputs[0])
                except:
                    print('failed adding node links to preview sphere') 

        #build shaderList
        shaderList = []
        try:
            dir = os.listdir(basePath + shaderPath)
            for file_path in dir:
                if file_path.lower().endswith('.shader'):
                    shaderList.append(basePath + shaderPath + file_path)
        except:
            print ('could not open shader')

        #get needed shaders
        neededShaders = []
        for ob in processingObjects:
            bpy.ops.object.select_all(action='DESELECT')
            ob.select = True
            scene.objects.active = ob
            for m in ob.material_slots:
                m.material.name = os.path.splitext(m.material.name)[0]
                m.material.name = os.path.splitext(m.material.name)[0]
                text = m.material.name
                toAdd = True
                for shader in neededShaders:
                    if text == shader:
                        toAdd = False
                        break
                if toAdd:
                    neededShaders.append(m.material.name)
                               
        #find shaders
        shaderNames = []
        diffuseTexture = []
        emissiveTexture = []
        is_emissive = []
        is_transparent = []
        currentShader = ''
        numberOfShaders = 0
        numberOfSkyShaders = 0
        bufferTexture = ''
        bufferDiffuseTexture = ''
        bufferEmissiveTexture = ''

        skyShaders = []
        skyShaderTextures = []

        suns = 0
        sunColor = []
        sunIntensity = []
        sunRotation = []

        for shaderFile in shaderList:
            try:
                foundShader = False
                foundDiffuse = False
                foundEmissive = False
                diffuseStage = False
                glowStage = False
                transparentStage = False
                isSky = False
                isOpen = 0
                with open(shaderFile) as lines:
                    for line in lines:
                        #skip empty lines or comments
                        if ((line.strip(" \t\r\n").startswith('/')) and (line.strip("\t\r\n") != ' ')): 
                            continue
                        #content
                        if not(line.strip(" \t\r\n").startswith('{')) and not(line.strip(" \t\r\n").startswith('}')):
                            if (isOpen == 0):
                                for shader in neededShaders:
                                    if shader == line.strip(" \t\r\n"):
                                        currentShader = line.strip(" \t\r\n")
                                        foundShader = True
                            if (isOpen == 1) and foundShader:     #special attributes like material or sky stuff
                                if line.lower().strip(" \t\r\n").startswith('skyparms'):
                                    try:
                                        try:
                                            marker, value = line.strip(" \t\r\n").split('\t', 1)
                                        except:
                                            marker, value = line.strip(" \t\r\n").split(' ', 1)
                                        isSky = True
                                        bufferDiffuseTexture = value.strip(" \t\r\n")
                                    except:
                                        print ("could not split line: " + line)
                                        
                                if line.lower().strip(" \t\r\n").startswith('surfaceparm'):
                                    try:
                                        try:
                                            marker, value = line.strip(" \t\r\n").split('\t', 1)
                                        except:
                                            marker, value = line.strip(" \t\r\n").split(' ', 1)
                                        if value.strip(" \t\r\n") == "sky":
                                            isSky = True
                                        if value.strip(" \t\r\n") == "trans":
                                            transparentStage = True
                                    except:
                                        print ("could not split line: " + line)
                                
                                if line.lower().strip(" \t\r\n").startswith('sun') or line.strip(" \t\r\n").startswith('q3map_sun') or line.strip(" \t\r\n").startswith('q3map_sunext') :
                                    try:
                                        try:
                                            marker, r, g, b, i, d, e, deviance, samples = line.strip(" \t\r\n").split('\t', 8)
                                        except:
                                            marker, r, g, b, i, d, e = line.strip(" \t\r\n").split(' ', 6)
                                        sunColor.append(r)
                                        sunColor.append(g)
                                        sunColor.append(b)
                                        sunIntensity.append(i)
                                        sunRotation.append(d)
                                        sunRotation.append(e)
                                        suns += 1
                                    except:
                                        print ("could not split line: " + line)
                                        
                            if (isOpen == 2) and foundShader:
                                
                                if line.lower().strip(" \t\r\n") == 'glow':
                                    glowStage = True
                                    
                                if line.lower().strip(" \t\r\n").startswith('surfacesprites'):
                                    diffuseStage = False
                                    glowStage = False
                                    transparentStage = False
                                    
                                if line.lower().strip(" \t\r\n").startswith('alphafunc'):
                                    marker, value = line.strip(" \t\r\n").split(' ', 1)
                                    if value.strip(" \t\r\n") == "GE192":
                                        transparentStage = True
                                    if value.strip(" \t\r\n") == "GE128":
                                        transparentStage = True
                                    
                                if line.lower().strip(" \t\r\n").startswith('blendfunc'):
                                    marker, value = line.strip(" \t\r\n").split(' ', 1)
                                    if value.strip(" \t\r\n") == "GL_ONE GL_ONE":
                                        glowStage = True
                                        
                                if line.lower().strip(" \t\r\n").startswith('tcgen'):
                                    marker, value = line.strip(" \t\r\n").split(' ', 1)
                                    if value.strip(" \t\r\n") == "environment":
                                        glowStage = False
                                        diffuseStage = False
                                
                                if line.lower().strip(" \t\r\n").startswith('alphagen'):
                                    marker, value = line.strip(" \t\r\n").split(' ', 1)
                                    if value.strip(" \t\r\n") == "lightingSpecular":
                                        glowStage = False
                                        diffuseStage = False
                                        
                                if line.lower().strip(" \t\r\n").startswith('clampmap'):
                                    marker, value = line.strip(" \t\r\n").split(' ', 1)
                                    if (value.strip(" \t\r\n") != '$lightmap'):
                                        bufferTexture = value
                                        diffuseStage = True
                                        
                                if line.lower().strip(" \t\r\n").startswith('map'):
                                    marker, value = line.strip(" \t\r\n").split(' ', 1)
                                    if (value.strip(" \t\r\n") != '$lightmap'):
                                        bufferTexture = value
                                        diffuseStage = True
                                        
                        #marker open
                        if line.strip(" \t\r\n").startswith('{'):
                            isOpen = isOpen + 1.
                            
                        #marker close
                        if line.strip(" \t\r\n").startswith('}'):
                            
                            #close stage
                            if (isOpen == 2):
                                if foundShader and (diffuseStage == True):
                                    if glowStage:
                                        bufferEmissiveTexture = bufferTexture
                                        foundEmissive = True
                                        glowStage = False
                                    else:
                                        bufferDiffuseTexture = bufferTexture
                                        
                            #close material
                            if (isOpen == 1):
                                if foundShader and not isSky:
                                    diffuseTexture.append(bufferDiffuseTexture)
                                    if foundEmissive:
                                        emissiveTexture.append(bufferEmissiveTexture)
                                        is_emissive.append(True)
                                    else:
                                        emissiveTexture.append('none')
                                        is_emissive.append(False)
                                    is_transparent.append(bool(transparentStage))
                                    numberOfShaders += 1
                                    shaderNames.append(currentShader)
                                    
                                    isSky = False
                                    foundShader = False
                                    foundEmissive = False
                                    bufferEmissiveTexture = 'none'
                                    bufferDiffuseTexture = 'none'
                                    bufferTexture = 'none'
                                    diffuseStage = False
                                    glowStage = False
                                    transparentStage = False
                                    
                                if foundShader and isSky:
                                    skyShaders.append(currentShader)
                                    skyShaderTextures.append(bufferDiffuseTexture.strip(' \t\r\n').split(' ',1)[0])
                                    numberOfSkyShaders += 1
                                    isSky = False
                                    foundShader = False
                                    foundEmissive = False
                                    bufferEmissiveTexture = 'none'
                                    bufferDiffuseTexture = 'none'
                                    bufferTexture = 'none'
                                    diffuseStage = False
                                    glowStage = False
                                    
                            isOpen -= 1                      
            except:
                print (('error in shaderfile ') + shaderFile)
                
        #sky setup (SomaZ)
        if (not onlyPreviewCube):
            i = 0
            try:
                for sunI in sunIntensity:
                    try:
                        bpy.ops.object.lamp_add(type='SUN', radius=0.1)
                        sun = scene.objects['Sun']
                        sun.name = 'Sun' + str(i)
                        sun.rotation_euler = (0.0,radians(float(90.0 - float(sunRotation[i*2 + 1]))),radians(float (sunRotation[i*2])))
                        sun.data.node_tree.nodes["Emission"].inputs[0].default_value = (float(sunColor[i*3]),float(sunColor[i*3 + 1]),float(sunColor[i*3 + 2]),1.0)
                        sun.data.node_tree.nodes["Emission"].inputs[1].default_value = float(sunI) / 10.0
                    except:
                        print ('could not parse a sun')
                    i += 1

                bpy.ops.mesh.primitive_cube_add(location=(0,0,0))
                for ob in scene.objects:
                    
                    ob.select = False
                    if ob.type == 'MESH' and ob.name.startswith("Cube"):
                        ob.name = "Sky"
                        ob.select = True
                        
                        isSky = True
                        mesh = ob.data
                        
                        if skyNumber >= numberOfSkyShaders:
                            print ('selected Sky Number is invalid. It gets replaced by 0')
                            skyNumber = 0
                        
                        texture = skyShaderTextures[skyNumber]
                        
                        try:
                            mesh.materials.append(bpy.data.materials[texture + "_up"])
                        except:
                            mat = bpy.data.materials.new(name= texture + "_up")
                            mesh.materials.append(mat)
                            mat.use_nodes = True   
                        
                        try:
                            mesh.materials.append(bpy.data.materials[texture + "_dn"])
                        except:
                            mat = bpy.data.materials.new(name= texture + "_dn")
                            mesh.materials.append(mat)  
                            mat.use_nodes = True
                        
                        try:
                            mesh.materials.append(bpy.data.materials[texture + "_ft"])
                        except:
                            mat = bpy.data.materials.new(name= texture + "_ft")
                            mesh.materials.append(mat)  
                            mat.use_nodes = True
                        
                        try:
                            mesh.materials.append(bpy.data.materials[texture + "_bk"])
                        except:
                            mat = bpy.data.materials.new(name= texture + "_bk")
                            mesh.materials.append(mat)  
                            mat.use_nodes = True
                        
                        try:
                            mesh.materials.append(bpy.data.materials[texture + "_lf"])
                        except:
                            mat = bpy.data.materials.new(name= texture + "_lf")
                            mesh.materials.append(mat) 
                            mat.use_nodes = True
                        
                        try:
                            mesh.materials.append(bpy.data.materials[texture + "_rt"])
                        except:
                            mat = bpy.data.materials.new(name= texture + "_rt")
                            mesh.materials.append(mat)
                            mat.use_nodes = True
                                
                        face_list = [face for face in mesh.polygons]

                        for face in face_list:
                            face.select = True
                            face.flip()
                            
                        bpy.ops.object.mode_set(mode='EDIT')
                        bpy.context.tool_settings.mesh_select_mode = [False, False, True]
                        bpy.ops.uv.reset()

                        bpy.ops.object.mode_set(mode='OBJECT')
                        bpy.ops.object.shade_smooth()
                        mesh.polygons[0].material_index = 4
                        mesh.polygons[1].material_index = 3
                        mesh.polygons[2].material_index = 5
                        mesh.polygons[3].material_index = 2
                        mesh.polygons[4].material_index = 1
                        mesh.polygons[5].material_index = 0
                        bpy.context.scene.update()
                        
                        ob.scale = (500.0, 500.0, 500.0)
                        ob.modifiers.new("subd", type='SUBSURF')
                        ob.modifiers['subd'].levels = 0
                        ob.modifiers['subd'].render_levels = 0
                        ob.cycles_visibility.shadow = False
            except:
                print ('could not setup the sky')
                
        #textures setup
        useShader = False
        index = 0
        textures = []
        texturePath = ' '
        emissivePath = ' '
        for m in bpy.data.materials:
            try:
                texturePath = os.path.splitext(m.name)[0]
                texturePath = os.path.splitext(texturePath)[0]
                isSky = False
                isSkyTexture = False
                
                for shader in skyShaders:
                    if shader == m.name:
                        isSky = True

                for shader in skyShaderTextures:
                    if texturePath.lower().startswith(shader.lower()):
                        isSkyTexture = True
                    
                useShader = False
                if isSky:
                    m.use_nodes = True
                    nodes = m.node_tree.nodes
                    material_output = nodes.get("Material Output")
                    node_transparentShader = nodes.new(type='ShaderNodeBsdfTransparent')
                    node_transparentShader.location = 0,400
                    links = m.node_tree.links
                    link = links.new(node_transparentShader.outputs[0], material_output.inputs[0])
                else:
                    #check if there is a shader for the material
                    for i in range(0,numberOfShaders):
                        if shaderNames[i] == texturePath:
                            useShader = True
                            texturePath = '.'.join((diffuseTexture[i]).split('.', 2)[:1])
                            emissivePath = '.'.join((emissiveTexture[i]).split('.', 2)[:1])
                            hasDiffuse = True
                            hasGlow = bool(is_emissive[i])
                            hasTransparency = bool(is_transparent[i])
                            index += 1
                            
                    if not(useShader):
                        hasDiffuse = True
                        hasTransparency = False
                        hasGlow = False
                    
                    if isSkyTexture:
                        hasDiffuse = False
                        hasGlow = True
                        emissivePath = texturePath
                    
                    try:
                        img = bpy.data.images.load(basePath + texturePath + '.jpg')
                    except:
                        try:
                            img = bpy.data.images.load(basePath + texturePath + '.tga')
                        except:
                            try:
                                img = bpy.data.images.load(basePath + texturePath + '.png')
                            except:
                                hasDiffuse = False
                                print ("Can't load image %s in shader " % texturePath, m.name)
                    if gl2:        
                        #RMO textures
                        if hasDiffuse:        
                            try:
                                rmo_img = bpy.data.images.load(basePath + texturePath + '_rmo.jpg')
                            except:
                                try:
                                    rmo_img = bpy.data.images.load(basePath + texturePath + '_rmo.tga')
                                except:
                                    try:
                                        rmo_img = bpy.data.images.load(basePath + texturePath + '_rmo.png')
                                    except:
                                        print ("Can't load rmo image %s in shader " % texturePath, m.name)
                        
                        #nh textures
                        if hasDiffuse:        
                            try:
                                nh_img = bpy.data.images.load(basePath + texturePath + '_n.jpg')
                            except:
                                try:
                                    nh_img = bpy.data.images.load(basePath + texturePath + '_n.tga')
                                except:
                                    try:
                                        nh_img = bpy.data.images.load(basePath + texturePath + '_n.png')
                                    except:
                                        print ("Can't load rmo image %s in shader " % texturePath, m.name)
                                
                                    
                    #glow textures
                    if hasGlow:
                        try:
                            img_glow = bpy.data.images.load(basePath + emissivePath + '.jpg')
                        except:
                            try:
                                img_glow = bpy.data.images.load(basePath + emissivePath + '.tga')
                            except:
                                try:
                                    img_glow = bpy.data.images.load(basePath + emissivePath + '.png')
                                except:
                                    hasGlow = False
                                    print ("image %s not found (emissive texture)" % emissivePath)
                                    
                    index = 0
                    
                    #Node setup
                    m.use_nodes = True
                    nodes = m.node_tree.nodes
                    material_output = nodes.get("Material Output")
                    
                    #is a valid material
                    if hasDiffuse or hasGlow:              
                        node_LightmapUV = nodes.new(type='ShaderNodeUVMap')
                        node_LightmapUV.uv_map = "LightmapUV"
                        node_LightmapUV.location = -500, -200
                        
                        node_DiffuseUV = nodes.new(type='ShaderNodeUVMap')
                        node_DiffuseUV.uv_map = "UVMap"
                        node_DiffuseUV.location = -250, -200
                        
                        node_lmTexture = nodes.new(type='ShaderNodeTexImage')
                        node_lmTexture.location = -500, 300
                        node_lmTexture.name = 'Lightmap'
                        node_lmTexture.label = 'Lightmap'
                
                        links = m.node_tree.links
                        link = links.new(node_LightmapUV.outputs[0], node_lmTexture.inputs[0])
                        
                        if hasDiffuse:
                            node_texture = nodes.new(type='ShaderNodeTexImage')
                            node_texture.image = img
                            node_texture.location = 0,100
                            
                            link = links.new(node_DiffuseUV.outputs[0], node_texture.inputs[0])
                            link = links.new(node_texture.outputs[0], nodes.get("Shader").inputs[0])
                            
                            if gl2:
                                try:
                                    node_seperate = nodes.new(type='ShaderNodeSeparateRGB')
                                    node_seperate.location = 0, -200
                                    node_rmotexture = nodes.new(type='ShaderNodeTexImage')
                                    node_rmotexture.image = rmo_img
                                    node_rmotexture.location = 0,-400
                                    node_rmotexture.color_space = 'NONE'
                                    node_nhtexture = nodes.new(type='ShaderNodeTexImage')
                                    node_nhtexture.image = nh_img
                                    node_nhtexture.location = 0,-700
                                    node_nhtexture.color_space = 'NONE'
                                    node_normalMap = nodes.new(type='ShaderNodeNormalMap')
                                    node_normalMap.location = 200,-700
                                    link = links.new(node_rmotexture.outputs[0], node_seperate.inputs[0])
                                    link = links.new(node_DiffuseUV.outputs[0], node_rmotexture.inputs[0])
                                    link = links.new(node_seperate.outputs[0], nodes.get("Shader").inputs['Roughness'])
                                    link = links.new(node_seperate.outputs[1], nodes.get("Shader").inputs['Metallic'])
                                    link = links.new(node_nhtexture.outputs[0], node_normalMap.inputs[1])
                                    link = links.new(node_nhtexture.outputs[1], material_output.inputs[2])
                                    link = links.new(node_DiffuseUV.outputs[0], node_nhtexture.inputs[0])
                                    link = links.new(node_normalMap.outputs[0], nodes.get("Shader").inputs['Normal'])
                                except:
                                    print('not gl2 compatible')
                        
                        if hasGlow:
                            node_addShader = nodes.new(type='ShaderNodeAddShader')
                            node_addShader.location = 0,400
                            node_glow_texture = nodes.new(type='ShaderNodeTexImage')
                            node_glow_texture.image = img_glow
                            node_glow_texture.location = -250,100
                            node_emissiveShader = nodes.new(type='ShaderNodeEmission')
                            node_emissiveShader.location = -250,300
                            
                            link = links.new(node_glow_texture.outputs[0], node_emissiveShader.inputs[0])
                            if isSkyTexture:
                                node_emissiveShader.inputs[1].default_value = defaultSkyEmissive
                                link = links.new(node_emissiveShader.outputs[0], material_output.inputs[0])
                            else:
                                nodes.get("Shader").inputs['Roughness'].default_value = defaultRoughness
                                link = links.new(nodes.get("Shader").outputs[0], node_addShader.inputs[0])
                                link = links.new(node_emissiveShader.outputs[0], node_addShader.inputs[1])
                                node_emissiveShader.inputs[1].default_value = defaultEmissive
                                link = links.new(node_DiffuseUV.outputs[0], node_glow_texture.inputs[0])
                                link = links.new(node_addShader.outputs[0], material_output.inputs[0])
                        else:
                            link = links.new(node_texture.outputs[0], nodes.get("Shader").inputs[0])
                            nodes.get("Shader").inputs['Roughness'].default_value = defaultRoughness
                            link = links.new(node_DiffuseUV.outputs[0], node_texture.inputs[0])
                            
                        if hasDiffuse:
                            link = links.new(node_texture.outputs[1], nodes.get("Mix Shader").inputs[0])
                        if hasTransparency and (not hasDiffuse) and hasGlow:
                            link = links.new(node_glow_texture.outputs[0], nodes.get("Mix Shader").inputs[0])
                            link = links.new(node_addShader.outputs[0], nodes.get("Mix Shader").inputs[2])
                            link = links.new(nodes.get("Mix Shader").outputs[0], material_output.inputs[0])
            except:
                print('could not build cycles shader for: ' + m.name)
        return{'FINISHED'}
    
class PrepareBaking(bpy.types.Operator):
    bl_idname = "q3map.prepare_baking"
    bl_label = "Prepare Lightmap baking"
    
    def execute(self, context):
        
        scene = bpy.context.scene
        q3mapImportTool = scene.q3mapImportTool
        deluxeMapping = q3mapImportTool.deluxeMapped #skip every second lightmap, because of deluxemapping, default should be False
        lmSize = q3mapImportTool.lmSize
        gl2 = q3mapImportTool.gl2
        
        addon_name = __name__.split('.')[0]
        self.prefs = context.user_preferences.addons[addon_name].preferences
        
        basePath = self.prefs.base_path
        
        failed = False

        lms = 0

        for ob in scene.objects:
            if ob.name.startswith('Lightmap_'):
                lms += 1

        for i in range(0,lms-1):
            bpy.ops.object.select_all(action='DESELECT')
            
            if deluxeMapping:
                name = 'Lightmap_' + str(i*2).zfill(4)
            else:
                name = 'Lightmap_' + str(i).zfill(4)
            try:
                obs = scene.objects[name]
                obs.select = True
                
                scene.objects.active = scene.objects[name]
                obs.data.uv_textures["LightmapUV"].active = True
                obs.data.uv_textures["LightmapUV"].active_render = True
                
                try:
                    bpy.data.images[name].scale(lmSize,lmSize)
                    image = bpy.data.images[name]
                    if (gl2):
                        image.use_generated_float = True
                    image.use_alpha = False
                    image.filepath = basePath + "maps\\" + q3mapImportTool.map_name + "\\" + name + ".tga"
                    image.file_format = 'TARGA'
                    #image.colorspace_settings.name = 'Linear'
                except:
                    image = bpy.data.images.new(name, lmSize, lmSize)
                    if (gl2):
                        image.use_generated_float = True
                    image.use_alpha = False
                    image.filepath = basePath + "maps\\" + q3mapImportTool.map_name + "\\" + name + ".tga"
                    image.file_format = 'TARGA'
                    #image.colorspace_settings.name = 'Linear'
                try:  
                    for ms in obs.material_slots:
                        newname = os.path.splitext(ms.material.name)[0]
                        newname = os.path.splitext(newname)[0] + '.' + name
                        ms.material = ms.material.copy()
                        ms.material.name = newname
                        ms.material.node_tree.nodes['Lightmap'].image = image
                except:
                    print ('error in material slots in ' + name)
            except:
                failed = True
                print ('error in ' + name)
        
        if (not failed):
            found = False
            #select lightmapped objects
            for i in range(0,lms-1):
                if deluxeMapping:
                    name = 'Lightmap_' + str(i*2).zfill(4)
                else:
                    name = 'Lightmap_' + str(i).zfill(4)
                try:
                    scene.objects[name].select = True
                    obs = scene.objects[name]
                    scene.objects.active = scene.objects[name]
                    found = True
                except:
                    found = False
            #join selected objects 
            if found == True:
                obs.name = 'Baking Object'
                bpy.ops.object.join()
                obs.data.use_auto_smooth = False
        
        return{'FINISHED'}
    
class SaveBakedLMs(bpy.types.Operator):
    bl_idname = "q3map.save_baked_lms"
    bl_label = "Save baked Lightmaps"
    
    def execute(self, context):
        
        scene = bpy.context.scene
        q3mapImportTool = scene.q3mapImportTool
        deluxeMapping = q3mapImportTool.deluxeMapped #skip every second lightmap, because of deluxemapping, default should be False
        for img in bpy.data.images:
            if (img.name.startswith("Lightmap_")):
                img.save()
        
        return{'FINISHED'}
    
class AddSelectedMaterial(bpy.types.Operator):
    bl_idname = "q3map.add_material"
    bl_label = "Add material to current selection"
    
    def execute(self, context):
        scene = context.scene
        q3mapImportTool = scene.q3mapImportTool
        
        currentShader = scene.q3mapImportTool.shader
        
        for obj in bpy.context.selected_objects:
            mesh = obj.data
            try:
                mesh.materials[currentShader]
            except:
                mesh.materials.append(bpy.data.materials[currentShader])
        
        return{'FINISHED'}
    
# ------------------------------------------------------------------------
# register and unregister
# ------------------------------------------------------------------------

def register():
    bpy.utils.register_module(__name__)
    bpy.types.Scene.q3mapImportTool = PointerProperty(type=ImporterSettings)

def unregister():
    bpy.utils.unregister_module(__name__)
    del bpy.types.Scene.q3mapImportTool

if __name__ == "__main__":
    register()