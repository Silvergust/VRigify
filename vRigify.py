import bpy
import bpy_extras


from math import(
cos,
sin
)

from mathutils import (
Vector
)

center_bone_names = ["CTRL_Hips",
                    "MCH_HipsParent",
                    "MCH_SpineParent",
                    "MCH_ChestParent",
                    "MCH_UpperChestParent",
                    "CTRL_Chest",
                    "CTRL_Neck",
                    "MCH_NeckParent",
                    "MCH_NeckSocket",
                    "MCH_HeadParent",
                    "CTRL_Global"]
                    
side_bone_names = [ "MCH_LegParent_",
                    "MCH_LegSocket_",
                    "MCH_UpperLeg_FK_",
                    "MCH_LowerLeg_FK_",
                    "MCH_Foot_FK_",
                    "MCH_UpperLeg_IK_",
                    "MCH_LowerLeg_IK_",
                    
                    "CTRL_KneeTarget_",
                    "MCH_Foot_IK_",
                    "MCH_HeelBase_",
                    "MCH_HeelBack_",
                    "CTRL_Heel_",
                    "CTRL_KneeTarget",
                    "MCH_FootRoot_",
                    "MCH_ArmParent_",
                    "MCH_ArmSocket_",
                    "MCH_UpperArm_IK_",
                    "MCH_LowerArm_IK_",
                    "CTRL_ElbowTarget_",
                    "MCH_Hand_IK_",
                    "MCH_UpperArm_FK_",
                    "MCH_LowerArm_FK_",
                    "MCH_Hand_FK_",
                    "CTRL_Palm_",
                    "CTRL_Fingers_",
                    "CTRL_Fingertips_",
                    "MCH_Little0_",
                    "MCH_Ring0_",
                    "MCH_Middle0_",
                    "MCH_Index0_",
                    "MCH_Thumb0_"]
class Layers:
    ctrl = 1
    fk = 2
    ik = 3
    
class Utilities:
    def make_copy_constraint(armature, owner_bone, target_bone, type, space='WORLD'): #I'd love to not have armature as argument and find it from owner_bone instead
        constraint = owner_bone.constraints.new(type=type)
        constraint.target = armature
        constraint.subtarget = target_bone.name
        constraint.target_space = space
        constraint.owner_space = space
        return constraint
    
    
    def make_copy_rot_constraint(armature, owner_bone, target_bone, space='WORLD'):
        return Utilities.make_copy_constraint(armature, owner_bone, target_bone, 'COPY_ROTATION', space)


    def make_multi_copy_rot_constraints(armature, first_control_bone, second_control_bone, target_bones, space='WORLD'):
        i = 0
        for bone in target_bones:
            Utilities.make_copy_rot_constraint(armature, bone, first_control_bone, space)
            Utilities.make_copy_rot_constraint(armature, bone, second_control_bone, space).influence = i / (len(target_bones)-1)
            i += 1


    def make_ik_constraint(armature, owner_posebone, extremity_posebone, pole_posebone = None, chain_count=2):
        constraint = owner_posebone.constraints.new(type='IK')
        constraint.target = armature
        constraint.subtarget = extremity_posebone.name
        if pole_posebone != None:
            constraint.pole_target = armature
            constraint.pole_subtarget = pole_posebone.name
        constraint.chain_count = chain_count
        return constraint


    def clone_bone(original_bone, clone_name, length_factor=1.0):
        new_bone = armature.data.edit_bones.new(name=clone_name)
        new_bone.head = original_bone.head
        new_bone.tail = original_bone.head + (original_bone.tail - original_bone.head)*length_factor



class Pair:
        def __init__(self, left_item=None, right_item=None):
            self.l = left_item
            self.r = right_item
            
            
        def __getitem__(self, key):
            assert(key == 'L' or key =='R')
            if key == 'L':
                return self.l
            else:
                return self.r
            
            
        def __setitem__(self, key, value):
            assert(key == 'L' or key =='R')
            if key == 'L':
                self.l = value
            else:
                self.r = value
            
            
            
class VRigify:
    def __init__(self, armature_object):
        self.armature = armature_object
        
        self.leg_parent_names = Pair() # It's not nice like this, but bone addresses are bound to change unpredictably during execution,
        self.leg_socket_names = Pair() # it's more reliable to look them up by their names
        self.knee_target_names = Pair()
        
        self.upper_leg_fk_names = Pair()
        self.lower_leg_fk_names = Pair()
        self.foot_fk_names = Pair()
        self.knee_target_names = Pair()
        
        self.arm_parent_names = Pair()
        self.arm_socket_names = Pair()
        self.elbow_target_names = Pair()
        
        self.upper_leg_ik_names = Pair()
        self.lower_leg_ik_names = Pair()
        self.foot_ik_names = Pair()
        
        self.heel_names = Pair()
        self.rocker_names = Pair()
        
        self.upper_arm_fk_names = Pair()
        self.lower_arm_fk_names = Pair()
        self.hand_fk_names = Pair()
        
        self.upper_arm_ik_names = Pair()
        self.lower_arm_ik_names = Pair()
        self.hand_ik_names = Pair()
        
        self.palm_names = Pair()
        
        self.neck_name = None
        self.neck_parent_name = None
        self.neck_socket_name = None
        self.chest_control_name = None
        self.hips_control_name = None
        
        self.hips_widget_mesh = None
        self.leg_ik_widget_mesh = Pair()
        self.arm_ik_widget_mesh = Pair()
        
        self.cube_widget_object = None
        
        
    def detect_base_leg_bones(self):
        print(self.armature)
        bpy.ops.object.mode_set(mode='EDIT')
        edit_bones = self.armature.data.edit_bones
        self.base_upper_leg_editbones = Pair(edit_bones["J_Bip_L_UpperLeg"], edit_bones["J_Bip_R_UpperLeg"])
        self.base_lower_leg_editbones = Pair(edit_bones["J_Bip_L_LowerLeg"], edit_bones["J_Bip_R_LowerLeg"])
        
        self.base_hips_editbone = edit_bones['J_Bip_C_Hips']
        self.base_foot_editbones = Pair(edit_bones['J_Bip_L_Foot'], edit_bones['J_Bip_R_Foot'])
        self.base_toe_editbones = Pair(edit_bones['J_Bip_L_ToeBase'], edit_bones['J_Bip_R_ToeBase'])
        
        
    def detect_base_arm_bones(self):
        bpy.ops.object.mode_set(mode='EDIT')
        edit_bones = self.armature.data.edit_bones
        self.base_upper_arm_editbones = Pair(edit_bones["J_Bip_L_UpperArm"], edit_bones["J_Bip_R_UpperArm"])
        self.base_lower_arm_editbones = Pair(edit_bones["J_Bip_L_LowerArm"], edit_bones["J_Bip_R_LowerArm"])
        self.base_hand_editbones = Pair(edit_bones["J_Bip_L_Hand"], edit_bones["J_Bip_R_Hand"])
    
    
    def reset(self, side_string=None):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.armature.select_all(action='DESELECT')
        edit_bones = self.armature.data.edit_bones
        for layer in bpy.context.object.data.layers:
            layer = True
        if side_string==None:
            self.reset('L')
            self.reset('R')
            for name in center_bone_names:
                if name in edit_bones.keys():
                    edit_bones[name].select = True
        else:
            for name in side_bone_names:
                if name + side_string in edit_bones:
                    edit_bones[name + side_string].select = True
        bpy.ops.armature.delete()
        
    def hard_reset(self):
        bpy.ops.object.mode_set(mode='EDIT')
        edit_bones = self.armature.data.edit_bones
        for bone in edit_bones:
            if bone.basename in center_bone_names or bone.basename[0:-1] in side_bone_names:
                bone.select = True
        bpy.ops.armature.delete()
        
        
    def assign_bones_layer_belonging(self, layer_index, bool):
        for bone in self.armature.data.edit_bones:
            bone.layers[layer_index] = bool
            
            
    def add_heel_mechanism(self, side_string):
        bpy.ops.object.mode_set(mode='EDIT')
        self.detect_base_leg_bones()
        
        ## Create new bones
        heel_base_editbone = armature.data.edit_bones.new(name='MCH_HeelBase_' + side_string)
        heel_base_editbone.tail = Vector((self.base_foot_editbones[side_string].tail.x, 0.1, 0.0))
        heel_base_editbone.head = Vector((self.base_foot_editbones[side_string].tail.x,  -0.1, 0.0))
        self.rocker_names[side_string] = heel_base_editbone.name
        
        heel_back_editbone = armature.data.edit_bones.new(name='MCH_HeelBack_' + side_string)
        heel_back_editbone.head = heel_base_editbone.tail
        heel_back_editbone.tail = heel_base_editbone.tail + Vector((0, 0, 0.1))
        self.heel_names[side_string] = heel_back_editbone.name
        
        control_bone = armature.data.edit_bones.new(name='CTRL_Heel_' + side_string)
        #control_bone.layers[Layers.ctrl] = True
        control_bone.head = heel_back_editbone.head + Vector((0, 0.05, 0))
        control_bone.tail = control_bone.head + Vector((0, 0, 0.05))
        
        heel_base_editbone.parent = heel_back_editbone
        
        ## Create constraints
        bpy.ops.object.mode_set(mode='POSE')
        pose_bones = self.armature.pose.bones
        
        heel_base_posebone = pose_bones[heel_base_editbone.name]
        heel_back_posebone = pose_bones[heel_back_editbone.name]
        Utilities.make_copy_rot_constraint(armature, heel_base_posebone, control_bone, 'LOCAL')
        Utilities.make_copy_rot_constraint(armature, heel_back_posebone, control_bone, 'LOCAL')
        
        limit_rot_constraint = heel_base_posebone.constraints.new(type='LIMIT_ROTATION')
        limit_rot_constraint.use_limit_x = True
        limit_rot_constraint.owner_space = 'LOCAL'
        limit_rot_constraint.max_x = 3.14
        
        limit_rot_constraint = heel_back_posebone.constraints.new(type='LIMIT_ROTATION')
        limit_rot_constraint.use_limit_x = True
        limit_rot_constraint.owner_space = 'LOCAL'
        limit_rot_constraint.min_x = -3.14
        

    '''Creates the socket mechanism to a limb chain and returns the name of the resulting parent and socket bones.
    outer_bone: Bone that lies outside the chain, e.g. hips our shoulder bones
    parent_name: Name of the parent bone to add (sans the side suffix).
    socket_name: Name of the socket bone to add (sans the side suffix).
    prop_name: Name of the custom property to add to the armature object (sans the side suffix)'''
    def add_socket_mechanism(self, side, outer_bone, parent_name, socket_name, first_link, prop_name=None):
        bpy.ops.object.mode_set(mode='EDIT')
        
        edit_bones = self.armature.data.edit_bones
        
        parent = armature.data.edit_bones.new(parent_name + side)
        parent.head = first_link.head
        parent.tail = parent.head + Vector((0, -0.1, 0))
        
        socket = armature.data.edit_bones.new(socket_name + side)
        socket.head = first_link.head
        socket.tail = socket .head+ Vector((0, -0.05, 0))
        
        socket.parent = outer_bone
        first_link.parent = parent
    
        bpy.ops.object.mode_set(mode='POSE')
        pose_bones = self.armature.pose.bones
        
        socket_posebone = pose_bones[socket.name]
        parent_posebone = pose_bones[parent.name]
    
        copy_loc_constraint = parent_posebone.constraints.new(type='COPY_LOCATION')
        copy_loc_constraint.target = armature
        copy_loc_constraint.subtarget = socket_posebone.name
    
        copy_trns_constraint = parent_posebone.constraints.new(type='COPY_TRANSFORMS')
        copy_trns_constraint.target = armature
        copy_trns_constraint.subtarget = socket_posebone.name
    
        if prop_name == None:
            prop_name = parent_name + "_influence" + ("" if side == "" else "_")
        self.assign_influence_driver(copy_trns_constraint, prop_name + side)
        
        return parent, socket

    def add_leg_socket_mechanism(self, side):
        bpy.ops.object.mode_set(mode='EDIT')
        self.detect_base_leg_bones()
        hips_bone = self.armature.data.edit_bones["J_Bip_C_Hips"]
        upper_bone = self.base_upper_leg_editbones[side]
        parent, socket = self.add_socket_mechanism(side, hips_bone, "MCH_LegParent_", "MCH_LegSocket_", upper_bone, "leg_follows_hip_")
        self.leg_parent_names[side] = parent.name
        self.leg_socket_names[side] = socket.name
    
    
    def add_arm_socket_mechanism(self, side):
        bpy.ops.object.mode_set(mode='EDIT')
        self.detect_base_arm_bones()
        shoulder_bone = self.armature.data.edit_bones["J_Bip_" + side + "_Shoulder"]
        upper_bone = self.base_upper_arm_editbones[side]
        parent, socket = self.add_socket_mechanism(side, shoulder_bone, "MCH_ArmParent_", "MCH_ArmSocket_", upper_bone, "arm_follows_shoulder_")
        self.arm_parent_names[side] = parent.name
        self.arm_socket_names[side] = socket.name
        
        
    def add_neck_socket_mechanism(self):
        bpy.ops.object.mode_set(mode='EDIT')
        upper_chest_bone = self.armature.data.edit_bones["J_Bip_C_UpperChest"]
        neck_bone = self.armature.data.edit_bones["J_Bip_C_Neck"]
        
        parent, socket = self.add_socket_mechanism("", upper_chest_bone, "MCH_NeckParent", "MCH_NeckSocket", neck_bone, "neck_follows_chest")
        self.neck_parent_name = parent.name
        self.neck_socket_name = socket.name
        
        
    def assign_influence_driver(self, constraint, prop_name):
        driver = constraint.driver_add('influence')
        var = driver.driver.variables.new()
        var.type = 'SINGLE_PROP'
        target = var.targets[0]
        target.id_type = 'OBJECT'
        target.id = self.armature
        armature[prop_name] = 0.0
        target.data_path = '["' + prop_name + '"]'
        driver.driver.expression = var.name
        
        
    def normalize_base_leg_bone_rolls(self, side=None):
        if side == None:
            self.normalize_base_leg_bone_rolls('L')
            self.normalize_base_leg_bone_rolls('R')
            return
        bpy.ops.object.mode_set(mode='EDIT')
        self.detect_base_leg_bones()
        
        self.base_upper_leg_editbones[side].roll = 0
        self.base_lower_leg_editbones[side].roll = 0
        print(self.base_foot_editbones[side].name)
        self.base_foot_editbones[side].roll = 0
        
    
    def create_leg_bones(self, suffix, side):
        bpy.ops.object.mode_set(mode='EDIT')
        self.detect_base_leg_bones()
        
        edit_bones = self.armature.data.edit_bones
        upper_leg_editbone = edit_bones.new("MCH_UpperLeg" + suffix + "_" + side)
        upper_leg_editbone.head = self.base_upper_leg_editbones[side].head
        upper_leg_editbone.tail = self.base_lower_leg_editbones[side].head
        
        lower_leg_editbone = edit_bones.new("MCH_LowerLeg" + suffix + "_" + side)
        lower_leg_editbone.head = self.base_lower_leg_editbones[side].head
        lower_leg_editbone.tail = self.base_foot_editbones[side].head
        
        foot_editbone = edit_bones.new("MCH_Foot" + suffix + "_" + side)
        foot_editbone.head = self.base_foot_editbones[side].head
        foot_editbone.tail = self.base_foot_editbones[side].tail
        
        upper_leg_editbone.parent = edit_bones[self.leg_parent_names[side]]
        lower_leg_editbone.parent = upper_leg_editbone
        foot_editbone.parent = lower_leg_editbone
        
        return upper_leg_editbone, lower_leg_editbone, foot_editbone
    
    
    def create_arm_bones(self, suffix, side):
        bpy.ops.object.mode_set(mode='EDIT')
        self.detect_base_arm_bones()
        
        edit_bones = self.armature.data.edit_bones
        upper_arm_editbone = edit_bones.new("MCH_UpperArm" + suffix + "_" + side)
        upper_arm_editbone.head = self.base_upper_arm_editbones[side].head
        upper_arm_editbone.tail = self.base_lower_arm_editbones[side].head
        upper_arm_editbone.roll = self.base_upper_arm_editbones[side].roll
        
        lower_arm_editbone = edit_bones.new("MCH_LowerArm" + suffix + "_" + side)
        lower_arm_editbone.head = self.base_lower_arm_editbones[side].head
        lower_arm_editbone.tail = self.base_hand_editbones[side].head
        lower_arm_editbone.roll = self.base_lower_arm_editbones[side].roll
        
        hand_editbone = edit_bones.new("MCH_Hand" + suffix + "_" + side)
        hand_editbone.head = lower_arm_editbone.tail
        hand_editbone.tail = hand_editbone.head + Vector((0.1 * (1 if side == 'L' else -1), 0, 0))
        hand_editbone.roll = lower_arm_editbone.roll
    
        upper_arm_editbone.parent = edit_bones[self.arm_parent_names[side]]
        lower_arm_editbone.parent = upper_arm_editbone
        hand_editbone.parent = lower_arm_editbone
        
        return upper_arm_editbone, lower_arm_editbone, hand_editbone
    
    def lock_rotation(self, posebone):
        posebone.rotation_mode = 'XYZ'
        posebone.lock_rotation[1] = True
        posebone.lock_rotation[2] = True
    
    def add_leg_fk_chain(self, side):
        upper_leg_editbone, lower_leg_editbone, foot_editbone = self.create_leg_bones("_FK", side)
        #upper_leg_editbone.layers[Layers.fk], lower_leg_editbone.layers[Layers.fk], foot_editbone.layers[Layers.fk] = True, True, True
        self.upper_leg_fk_names[side] = upper_leg_editbone.name
        self.lower_leg_fk_names[side] = lower_leg_editbone.name
        self.foot_fk_names[side] = foot_editbone.name
        
        foot_editbone = self.armature.data.edit_bones["J_Bip_" + side + "_Foot"]
        self.armature.data.edit_bones["J_Bip_" + side + "_ToeBase"].parent = foot_editbone
        bpy.ops.object.mode_set(mode='POSE')
        pose_bones = self.armature.pose.bones
        #self.lock_rotation(pose_bones[self.upper_leg_fk_names[side])
        self.lock_rotation(pose_bones[self.lower_leg_fk_names[side]])
        #self.lock_rotation(pose_bones[self.foot_fk_names[side]])
        #upper_leg_posebone = pose_bones[self.upper_leg_fk_names[side]]
        #upper_leg_posebone.rotation_mode = 'XYZ'
        #upper_leg_posebone.lock_rotation[1] = True
        #upper_leg_posebone.lock_rotation[2] = True
        #lower_leg_posebone = pose_bones[self.lower_leg_fk_names[side]]
        #lower_leg_posebone.rotation_mode = 'XYZ'
        #lower_leg_posebone.lock_rotation[1] = True
        #lower_leg_posebone.lock_rotation[2] = True
        
        
    def add_arm_fk_chain(self, side):
        upper_arm_editbone, lower_arm_editbone, hand_editbone = self.create_arm_bones("_FK", side)
        #upper_arm_editbone.layers[Layers.fk], lower_arm_editbone.layers[Layers.fk], hand_editbone.layers[Layers.fk] = True, True, True
        self.upper_arm_fk_names[side] = upper_arm_editbone.name
        self.lower_arm_fk_names[side] = lower_arm_editbone.name
        self.hand_fk_names[side] = hand_editbone.name
        
        bpy.ops.object.mode_set(mode='POSE')
        lower_arm_posebone = self.armature.pose.bones[self.lower_arm_fk_names[side]]
        lower_arm_posebone.rotation_mode = 'XYZ'
        lower_arm_posebone.lock_rotation[1] = True
        lower_arm_posebone.lock_rotation[2] = True
        
        
    def add_ik_chain(self, side, pole_name, pole_offset, first_link, second_link, final_link, pole_angle = None): 
        edit_bones = self.armature.data.edit_bones
        pose_bones = self.armature.pose.bones 
        
        pole_subtarget_editbone = edit_bones.new(pole_name + side)
        #pole_subtarget_editbone.layers[Layers.ctrl] = True
        pole_subtarget_editbone.head = second_link.head + pole_offset
        pole_subtarget_editbone.tail = pole_subtarget_editbone.head + 0.2 * pole_offset
        
        bpy.ops.object.mode_set(mode='POSE')
        final_link_posebone = pose_bones[final_link.name]
        second_link_posebone = pose_bones[second_link.name]
        pole_subtarget_posebone = pose_bones[pole_subtarget_editbone.name]
        
        bpy.ops.object.mode_set(mode='POSE')
        ik_constraint = Utilities.make_ik_constraint(self.armature, second_link_posebone, final_link_posebone)#, pole_subtarget_posebone)
        if pole_angle == None:
            ik_constraint.pole_angle = -3.14159 / 4
        else:
            ik_constraint.pole_angle = pole_angle
        second_link_posebone.lock_ik_y = True
        second_link_posebone.lock_ik_z = True
        limit_rot_constraint = second_link_posebone.constraints.new(type="LIMIT_ROTATION")
        limit_rot_constraint.use_limit_x = True
        limit_rot_constraint.max_x = 3.14159
        return pole_subtarget_posebone.name
    
    
    def add_leg_ik_chain(self, side):
        upper_leg_editbone, lower_leg_editbone, foot_editbone = self.create_leg_bones("_IK", side)
        #foot_editbone.layers[Layers.ik] = True
        edit_bones = self.armature.data.edit_bones
        foot_editbone.parent = None
        edit_bones[self.heel_names[side]].parent = foot_editbone

        
        self.upper_leg_ik_names[side] = upper_leg_editbone.name
        self.lower_leg_ik_names[side] = lower_leg_editbone.name
        self.foot_ik_names[side] = foot_editbone.name
        
        self.knee_target_names[side] = self.add_ik_chain(side, "CTRL_KneeTarget_", Vector((0, -1, 0)), upper_leg_editbone, lower_leg_editbone, foot_editbone)

   
    def add_arm_ik_chain(self, side):
       upper_arm_editbone, lower_arm_editbone, hand_editbone = self.create_arm_bones("_IK", side)
       #upper_arm_editbone.layers[Layers.ik], lower_arm_editbone.layers[Layers.ik], hand_editbone.layers[Layers.ik] = True, True, True
       edit_bones = self.armature.data.edit_bones
       hand_editbone.parent = None
       hand_editbone.roll = lower_arm_editbone.roll
       
       self.upper_arm_ik_names[side] = upper_arm_editbone.name
       self.lower_arm_ik_names[side] = lower_arm_editbone.name
       self.hand_ik_names[side] = hand_editbone.name
       
       self.elbow_target_names[side] = self.add_ik_chain(side, "CTRL_ElbowTarget_", Vector((0, 1, 0)), upper_arm_editbone, lower_arm_editbone, hand_editbone, 3.14159 / 2)
              
        
    def setup_fkik_mechanism(self, side, first_owner_posebone, second_owner_posebone, final_owner_posebone, first_target_posebone, second_target_posebone, final_target_posebone):
        bpy.ops.object.mode_set(mode='EDIT')
        self.detect_base_leg_bones()
        pose_bones = self.armature.pose.bones
        
        # Set base bones to copy FK chain rotations
        Utilities.make_copy_rot_constraint(self.armature, first_owner_posebone, first_target_posebone)
        Utilities.make_copy_rot_constraint(self.armature, second_owner_posebone, second_target_posebone)
        Utilities.make_copy_rot_constraint(self.armature, final_owner_posebone, final_target_posebone)
        
        
    def setup_ik_driver(self, side, owner_posebone, target_ik_posebone, driver_suffix):
        constraint = Utilities.make_copy_rot_constraint(self.armature, owner_posebone, target_ik_posebone)
        self.assign_influence_driver(constraint, driver_suffix + "_fk_ik_" + side)
        
        
    def setup_leg_fkik_mechanism(self, side):
        bpy.ops.object.mode_set(mode='EDIT')
        self.detect_base_leg_bones()
        pose_bones = self.armature.pose.bones
        owner_upper_leg_posebone = pose_bones[self.base_upper_leg_editbones[side].name]
        owner_lower_leg_posebone = pose_bones[self.base_lower_leg_editbones[side].name]
        owner_foot_posebone = pose_bones[self.base_foot_editbones[side].name]
        target_upper_leg_posebone = pose_bones[self.upper_leg_fk_names[side]]
        target_lower_leg_posebone = pose_bones[self.lower_leg_fk_names[side]]
        target_foot_posebone = pose_bones[self.foot_fk_names[side]]
        
        self.setup_fkik_mechanism(side, owner_upper_leg_posebone, owner_lower_leg_posebone, owner_foot_posebone, target_upper_leg_posebone, target_lower_leg_posebone, target_foot_posebone)
        upper_leg_ik_posebone = pose_bones[self.upper_leg_ik_names[side]]
        lower_leg_ik_posebone = pose_bones[self.lower_leg_ik_names[side]]
        foot_ik_posebone = pose_bones[self.foot_ik_names[side]]
        self.setup_ik_driver(side, owner_upper_leg_posebone, upper_leg_ik_posebone, "leg")
        self.setup_ik_driver(side, owner_lower_leg_posebone, lower_leg_ik_posebone, "leg")
        self.setup_ik_driver(side, owner_foot_posebone, foot_ik_posebone, "leg")
        
        
    def setup_arm_fkik_mechanism(self, side):
        bpy.ops.object.mode_set(mode='EDIT')
        self.detect_base_arm_bones()
        pose_bones = self.armature.pose.bones
        owner_upper_arm_posebone = pose_bones[self.base_upper_arm_editbones[side].name]
        owner_lower_arm_posebone = pose_bones[self.base_lower_arm_editbones[side].name]
        owner_hand_posebone = pose_bones[self.base_hand_editbones[side].name]
        target_upper_arm_posebone = pose_bones[self.upper_arm_fk_names[side]]
        target_lower_arm_posebone = pose_bones[self.lower_arm_fk_names[side]]
        target_hand_posebone = pose_bones[self.hand_fk_names[side]]
        self.setup_fkik_mechanism(side, owner_upper_arm_posebone, owner_lower_arm_posebone, owner_hand_posebone, target_upper_arm_posebone, target_lower_arm_posebone, target_hand_posebone)
        upper_arm_ik_posebone = pose_bones[self.upper_arm_ik_names[side]]
        lower_arm_ik_posebone = pose_bones[self.lower_arm_ik_names[side]]
        hand_ik_posebone = pose_bones[self.hand_ik_names[side]]
        palm_posebone = pose_bones[self.palm_names[side]]
        self.setup_ik_driver(side, owner_upper_arm_posebone, upper_arm_ik_posebone, "arm")
        self.setup_ik_driver(side, owner_lower_arm_posebone, lower_arm_ik_posebone, "arm")
        self.setup_ik_driver(side, owner_hand_posebone, hand_ik_posebone, "arm")
        self.setup_ik_driver(side, palm_posebone, hand_ik_posebone, "arm")
        Utilities.make_copy_rot_constraint(self.armature, palm_posebone, owner_hand_posebone)
        
        
    def add_palm_rig(self, side):
        #TODO: This (and the heel rig) would've been better to have after setting up the arm bones, and use said bones as arguments where necessary to set up parenthood, etc.
        self.detect_base_arm_bones()
        edit_bones = self.armature.data.edit_bones
        
        # Create control bones
        palm_editbone = edit_bones.new("CTRL_Palm_" + side)
        #palm_editbone.layers[Layers.ctrl] = True
        palm_editbone.head = self.base_hand_editbones[side].head + Vector((0, 0, 0.05))
        palm_editbone.tail = palm_editbone.head + Vector((0.06 * (1 if side == 'L' else -1), 0, 0))
        palm_editbone.roll = (-1 if side == 'L' else 1) * 3.14159 / 2 # Assuming right hand side (most likely wrong for left hand). Non-magic numbers may be preferable
        palm_editbone.parent = self.base_hand_editbones[side] # Will almost certainly need to change
        self.palm_names[side] = palm_editbone.name
        
        fingers_editbone = edit_bones.new("CTRL_Fingers_" + side)
        #fingers_editbone.layers[Layers.ctrl]
        fingers_editbone.head = palm_editbone.tail
        fingers_editbone.tail = fingers_editbone.head + Vector((0.03 * (1 if side == 'L' else -1), 0, 0))
        fingers_editbone.parent = palm_editbone
        
        fingertips_editbone = edit_bones.new("CTRL_Fingertips_" + side)
        #fingertips_editbone.layers[Layers.ctrl]
        fingertips_editbone.head = fingers_editbone.tail
        fingertips_editbone.tail = fingertips_editbone.head + Vector((0.015 * (1 if side == 'L' else -1), 0, 0))        
        fingertips_editbone.parent = fingers_editbone
        
        little_fingers = self.add_finger_chain(side, "Little", palm_editbone, fingers_editbone, fingertips_editbone)
        ring_fingers = self.add_finger_chain(side, "Ring", palm_editbone, fingers_editbone, fingertips_editbone)
        middle_fingers = self.add_finger_chain(side, "Middle", palm_editbone, fingers_editbone, fingertips_editbone)
        index_fingers = self.add_finger_chain(side, "Index", palm_editbone, fingers_editbone, fingertips_editbone)
        
        bpy.ops.object.mode_set(mode='POSE')
        pose_bones = self.armature.pose.bones
        palm_posebone = pose_bones[palm_editbone.name]
        fingers_posebone = pose_bones[fingers_editbone.name]
        fingertips_posebone = pose_bones[fingertips_editbone.name]
        def set_finger_chain_constraints(finger_list, influence):
            finger0_posebone = pose_bones[finger_list[0].name]
            finger1_posebone = pose_bones[finger_list[1].name]
            finger2_posebone = pose_bones[finger_list[2].name]
            Utilities.make_copy_rot_constraint(self.armature, finger1_posebone, fingers_posebone, 'LOCAL').influence
            Utilities.make_copy_rot_constraint(self.armature, finger2_posebone, fingertips_posebone, 'LOCAL').influence
            
        set_finger_chain_constraints(little_fingers, 1.0)
        set_finger_chain_constraints(ring_fingers, 0.9)
        set_finger_chain_constraints(middle_fingers, 0.8)
        set_finger_chain_constraints(index_fingers, 0.5)
        
        
    def add_finger_chain(self, side, finger_suffix, palm_editbone, fingers_editbone, fingertips_editbone):
        bpy.ops.object.mode_set(mode='EDIT')
        edit_bones = self.armature.data.edit_bones
        finger1_editbone = edit_bones["J_Bip_" + side + "_" + finger_suffix + "1"]
        finger2_editbone = edit_bones["J_Bip_" + side + "_" + finger_suffix + "2"]
        
        # Create auxiliary "zeroth" finger bones between wrist and "finger" fingerbones
        finger0_editbone = edit_bones.new("MCH_" + finger_suffix + "0_" + side)
        finger0_editbone.head = self.base_hand_editbones[side].head
        finger0_editbone.tail = finger1_editbone.head
        finger0_editbone.parent = self.base_lower_arm_editbones[side]
        finger0_editbone.roll = finger1_editbone.roll
        finger0_editbone.parent = palm_editbone
        finger1_editbone.parent = finger0_editbone
        
        return [finger0_editbone, finger1_editbone, finger2_editbone]

        
    def setup_leg_rig(self, side=None):
        if side == None:
            self.setup_leg_rig('L')
            self.setup_leg_rig('R')
        else:
            self.add_heel_mechanism(side)
            self.add_leg_socket_mechanism(side)
            self.add_leg_fk_chain(side)
            self.add_leg_ik_chain(side)
            self.setup_leg_fkik_mechanism(side)
            
            
    def setup_arm_rig(self, side=None):
        if side == None:
            self.setup_arm_rig('L')
            self.setup_arm_rig('R')
        else:
            self.add_palm_rig(side)
            self.add_arm_socket_mechanism(side)
            self.add_arm_fk_chain(side)
            self.add_arm_ik_chain(side)
            self.setup_arm_fkik_mechanism(side)
        
        
    def setup_spine_bones(self):
        edit_bones = self.armature.data.edit_bones
        
        hips_editbone = edit_bones["J_Bip_C_Hips"]
        spine_editbone = edit_bones["J_Bip_C_Spine"]
        chest_editbone = edit_bones["J_Bip_C_Chest"]
        upper_chest_editbone = edit_bones["J_Bip_C_UpperChest"]
        
        offset = Vector((0, 0, 0.05))
        hips_parent_editbone = edit_bones.new("MCH_HipsParent")
        hips_parent_editbone.head = hips_editbone.head
        hips_parent_editbone.tail = hips_parent_editbone.head + offset
        hips_parent_editbone.roll = hips_editbone.roll
        spine_parent_editbone = edit_bones.new("MCH_SpineParent")
        spine_parent_editbone.head = spine_editbone.head
        spine_parent_editbone.tail = spine_parent_editbone.head + offset
        spine_parent_editbone.roll = spine_editbone.roll
        chest_parent_editbone = edit_bones.new("MCH_ChestParent")
        chest_parent_editbone.head = chest_editbone.head
        chest_parent_editbone.tail = chest_parent_editbone.head + offset
        chest_parent_editbone.roll = chest_editbone.roll
        upper_chest_parent_editbone = edit_bones.new("MCH_UpperChestParent")
        upper_chest_parent_editbone.head = upper_chest_editbone.head
        upper_chest_parent_editbone.tail = upper_chest_parent_editbone.head + offset
        upper_chest_parent_editbone.roll = upper_chest_editbone.roll
        
        spine_editbone.parent = spine_parent_editbone
        chest_parent_editbone.parent = spine_editbone
        chest_editbone.parent = chest_parent_editbone
        upper_chest_parent_editbone.parent = chest_editbone
        upper_chest_editbone.parent = upper_chest_parent_editbone
        
        return hips_parent_editbone, spine_parent_editbone, chest_parent_editbone, upper_chest_parent_editbone
    
    
    def setup_spine_mechanism(self):
        hips_parent_editbone, spine_parent_editbone, chest_parent_editbone, upper_chest_parent_editbone = self.setup_spine_bones()
        
        offset = Vector((0, 0, 0.03))
        
        edit_bones = self.armature.data.edit_bones
        hips_control_editbone = edit_bones.new("CTRL_Hips")
        #hips_control_editbone.layers[Layers.ctrl] = True
        hips_control_editbone.head = spine_parent_editbone.head
        hips_control_editbone.tail = hips_control_editbone.head + offset
        hips_control_editbone.roll = spine_parent_editbone.roll
        self.hips_control_name = hips_control_editbone.name
        edit_bones["J_Bip_C_Hips"].parent = hips_control_editbone
        
        chest_control_editbone = edit_bones.new("CTRL_Chest")
        #chest_control_editbone.layers[Layers.ctrl] = True
        chest_control_editbone.head = upper_chest_parent_editbone.tail
        chest_control_editbone.tail = chest_control_editbone.head + offset
        chest_control_editbone.roll = upper_chest_parent_editbone.roll
        self.chest_control_name = chest_control_editbone.name
        
        bpy.ops.object.mode_set(mode='POSE')
        pose_bones = self.armature.pose.bones

        hips_control_posebone = pose_bones[hips_control_editbone.name]
        hips_parent_posebone = pose_bones[hips_parent_editbone.name]
        spine_parent_posebone = pose_bones[spine_parent_editbone.name]
        chest_parent_posebone = pose_bones[chest_parent_editbone.name]
        upper_chest_parent_posebone = pose_bones[upper_chest_parent_editbone.name]
        chest_control_posebone = pose_bones[chest_control_editbone.name]
        
        spine_constraint = spine_parent_posebone.constraints.new(type='COPY_LOCATION')
        spine_constraint.target = self.armature
        spine_constraint.subtarget = hips_control_posebone.name
        
        Utilities.make_multi_copy_rot_constraints(self.armature, hips_control_posebone, chest_control_posebone, [hips_parent_posebone, spine_parent_posebone, chest_parent_posebone, upper_chest_parent_posebone])
        
        
    def setup_neck_mechanism(self):
        bpy.ops.object.mode_set(mode='EDIT')
        edit_bones = self.armature.data.edit_bones
        neck_editbone = edit_bones["J_Bip_C_Neck"]
        head_editbone = edit_bones["J_Bip_C_Head"]
        
        upper_chest_editbone = edit_bones["J_Bip_C_UpperChest"]
        
        offset = Vector((0, 0, 0.03))
        head_parent = edit_bones.new("MCH_Head_Parent")
        
        self.add_neck_socket_mechanism()
        bpy.ops.object.mode_set(mode='EDIT')
        neck_control = edit_bones.new("CTRL_Neck")
        #neck_control.layers[Layers.ctrl] = True
        neck_control.head = edit_bones[self.neck_parent_name].head
        neck_control.tail = neck_control.head + Vector((0, 0, 0.05))
        neck_control.roll = neck_editbone.roll
        self.neck_name = neck_control.name
        bpy.ops.object.mode_set(mode='POSE')
        pose_bones = self.armature.pose.bones
        neck_parent_posebone = pose_bones[self.neck_parent_name]
        head_posebone = pose_bones[head_editbone.name]
        parent_constraint = Utilities.make_copy_rot_constraint(self.armature, neck_parent_posebone, neck_control, 'LOCAL')
        parent_constraint.influence = 0.5
        bpy.context.active_object.data.bones.active = neck_parent_posebone.bone
        context = bpy.context.copy()
        context["constraint"] = neck_parent_posebone.constraints[parent_constraint.name]
        bpy.ops.constraint.move_up(context, constraint=parent_constraint.name, owner='BONE')
        Utilities.make_copy_rot_constraint(self.armature, head_posebone, neck_control, 'LOCAL')
        
        
    def setup_global_control(self):
        bpy.ops.object.mode_set(mode='EDIT')
        edit_bones = self.armature.data.edit_bones
        global_editbone = edit_bones.new("CTRL_Global")
        global_editbone.head = self.armature.location
        global_editbone.tail = self.armature.location + Vector((0, 0, 0.1))
        edit_bones[self.hips_control_name].parent = global_editbone
        edit_bones[self.neck_name].parent = global_editbone
        edit_bones[self.chest_control_name].parent = edit_bones[self.hips_control_name]
        for side in ['L', 'R']:
            edit_bones[self.knee_target_names[side]].parent = global_editbone
            edit_bones[self.elbow_target_names[side]].parent = global_editbone
            edit_bones[self.hand_ik_names[side]].parent = global_editbone
            edit_bones[self.foot_ik_names[side]].parent = global_editbone
            
        
    def create_widget(self, name, editbone, verts, edges):
        mesh = bpy.data.meshes.new(name=name)        
        mesh.from_pydata(verts, edges, [])
        mesh.validate()
    
        bpy.ops.object.mode_set(mode='OBJECT')
        self.armature.select = False
        ob = bpy_extras.object_utils.object_data_add(bpy.context, mesh)
        bpy.ops.object.select_all(action='DESELECT')
        self.armature.select = True
        bpy.context.view_layer.objects.active = self.armature
        bpy.ops.object.mode_set(mode='POSE')
        self.armature.pose.bones[editbone.name].custom_shape = ob
        bpy.ops.object.mode_set(mode='EDIT')
        
        
    def create_cuboid_widget(self, name, editbone, half_sizes, offset=Vector((0,0,0))):
        verts = [  (-half_sizes.x+offset.x, -half_sizes.y+offset.y, -half_sizes.z+offset.z), ( half_sizes.x+offset.x, -half_sizes.y+offset.y, -half_sizes.z+offset.z),
                   (-half_sizes.x+offset.x,  half_sizes.y+offset.y, -half_sizes.z+offset.z), ( half_sizes.x+offset.x,  half_sizes.y+offset.y, -half_sizes.z+offset.z),
                   (-half_sizes.x+offset.x, -half_sizes.y+offset.y,  half_sizes.z+offset.z), ( half_sizes.x+offset.x, -half_sizes.y+offset.y,  half_sizes.z+offset.z),
                   (-half_sizes.x+offset.x,  half_sizes.y+offset.y,  half_sizes.z+offset.z), ( half_sizes.x+offset.x,  half_sizes.y+offset.y,  half_sizes.z+offset.z)]
        edges = [  (0, 1), (1, 3), (3, 2), (2, 0),
                    (1, 5), (5, 4), (4, 0),
                    (2, 6), (6, 4), 
                    (6, 7), (7, 5),
                    (7, 3) ]
        self.create_widget(name, editbone, verts, edges)
        
        
    def create_cube_widget(self, name, editbone, half_size):
        self.create_cuboid_widget(name, editbone, (half_size, half_size, half_size))
        
        
    def create_circle_widget(self, name, editbone, radius):
        steps_amount = 24
        circle_verts = [ (radius*cos(theta), 0, radius*sin(theta)) for theta in [2 * i * 3.14159/steps_amount for i in range(steps_amount)]]
        circle_edges = [(i, (i+1)%len(circle_verts)) for i in range(len(circle_verts))]
        self.create_widget(name, editbone, circle_verts, circle_edges)
        
    
    def create_hips_widget(self):
        hips_editbone = self.armature.data.edit_bones["CTRL_Hips"]
        leg_editbone = self.armature.data.edit_bones["J_Bip_L_UpperLeg"]
        half_size = 1.5*(leg_editbone.center.x - hips_editbone.center.x)/(hips_editbone.tail - hips_editbone.head).magnitude
        self.create_cube_widget("WGT_Hips", hips_editbone, half_size)
        
        
    def create_chest_widget(self):
        chest_editbone = self.armature.data.edit_bones["CTRL_Chest"]
        shoulder_editbone = self.armature.data.edit_bones["J_Bip_L_Shoulder"]
        radius = (chest_editbone.center - shoulder_editbone.center).magnitude / (chest_editbone.tail - chest_editbone.head).magnitude
        self.create_circle_widget("WGT_Chest", chest_editbone, radius)
        
        
    def create_arm_fk_widgets(self, side=None):
        if side == None:
            self.create_arm_fk_widgets('L')
            self.create_arm_fk_widgets('R')
            return
        edit_bones = self.armature.data.edit_bones
        upper_editbone = edit_bones[self.upper_arm_fk_names[side]]
        self.create_circle_widget("WGT_Upper_Arm_FK_" + side, upper_editbone, 0.5)
        lower_editbone = edit_bones[self.lower_arm_fk_names[side]]
        self.create_circle_widget("WGT_Lower_Arm_FK_" + side, lower_editbone, 0.5)
        hand_editbone = edit_bones[self.hand_fk_names[side]]
        self.create_circle_widget("WGT_Hand_FK_" + side, hand_editbone, 0.8)
        
        
    def create_foot_ik_widget(self, side=None):
        if side == None:
            self.create_foot_ik_widget('L')
            self.create_foot_ik_widget('R')
            return
        foot_editbone = self.armature.data.edit_bones[self.foot_ik_names[side]]
        self.create_cuboid_widget("WGT_Foot_IK_" + side, foot_editbone, Vector((0.3, 0.9, 0.4)), Vector((0.0, 0.9, 0.0)))
        
        
    def create_leg_fk_widgets(self, side=None):
        if side == None:
            self.create_leg_fk_widgets('L')
            self.create_leg_fk_widgets('R')
            return
        edit_bones = self.armature.data.edit_bones
        upper_editbone = edit_bones[self.upper_leg_fk_names[side]]
        self.create_circle_widget("WGT_Upper_Leg_FK_" + side, upper_editbone, 0.3)
        lower_editbone = edit_bones[self.lower_leg_fk_names[side]]
        self.create_circle_widget("WGT_Lower_Leg_FK_" + side, lower_editbone, 0.3)
        foot_editbone = edit_bones[self.foot_fk_names[side]]
        self.create_circle_widget("WGT_Foot_FK_" + side, foot_editbone, 0.8)
        
        
    def create_hand_ik_widget(self, side=None):
        if side == None:
            self.create_hand_ik_widget('L')
            self.create_hand_ik_widget('R')
            return
        hand_editbone = self.armature.data.edit_bones["MCH_Hand_IK_" + side]
        self.create_cuboid_widget("WGT_Hand_IK_" + side, hand_editbone, Vector((0.3, 0.9, 0.3)), Vector((0.0, 0.9, 0.0)))
        
        
if __name__ == '__main__':
    armature = bpy.context.active_object
    
    vrig = VRigify(armature)
    vrig.reset()
    vrig.normalize_base_leg_bone_rolls()
    vrig.setup_leg_rig()
    vrig.setup_arm_rig()
    vrig.setup_spine_mechanism()
    vrig.setup_neck_mechanism()
    vrig.setup_global_control()
    #vrig.create_hips_widget()
    #vrig.create_chest_widget()
    #vrig.create_arm_fk_widgets()
    #vrig.create_hand_ik_widget()
    #vrig.create_leg_fk_widgets()
    vrig.create_foot_ik_widget()