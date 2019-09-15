import bpy

from mathutils import (
Vector
)

skeleton_object = bpy.context.active_object
armature = bpy.data.armatures['Armature']


edit_bones = bpy.context.active_object.data.edit_bones
#pose_bones = bpy.context.active_object.data.bones
#pose_bones = bpy.context.pose_object.pose.bones
pose_bones = bpy.context.active_object.pose.bones
bpy.ops.object.mode_set(mode='EDIT')

center_bone_names = []
side_bone_names = [ "MCH_HeelBase_",
                    "MCH_HeelBack_",
                    "CTRL_Heel_",
                    "MCH_FootRoot_",
                    "MCH_UpperLeg_FK_",
                    "MCH_LowerLeg_FK_",
                    "MCH_UpperLeg_IK_",
                    "MCH_LowerLeg_IK_",
                    "MCH_LegParent_",
                    "MCH_LegSocket_"]

class Utilities:
    def make_copy_rot_constraint(armature, owner_bone, target_bone, space='WORLD'): #I'd love to not have armature as argument and find it from owner_bone instead
        constraint = owner_bone.constraints.new(type='COPY_ROTATION')
        constraint.target = armature
        constraint.subtarget = target_bone.name
        #constraint.use_limit_x = True
        constraint.target_space = space
        constraint.owner_space = space

    def clone_bone(original_bone, clone_name, length_factor=1.0):
        new_bone = armature.data.edit_bones.new(name=clone_name)
        new_bone.head = original_bone.head
        new_bone.tail = original_bone.head + (original_bone.tail - original_bone.head)*length_factor

    def reset(side_string=None):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.armature.select_all(action='DESELECT')
        if side_string==None:
            Utilities.reset('L')
            Utilities.reset('R')
            for name in center_bone_names:
                if name in edit_bones.keys():
                    edit_bones[name].select = True
        else:
            for name in side_bone_names:
                if name + side_string in edit_bones.keys():
                    edit_bones[name + side_string].select = True
        bpy.ops.armature.delete()

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
    def __init__(self, armature):
        self.armature = armature
        self.base_upper_leg_editbones = Pair(edit_bones["J_Bip_L_UpperLeg"], edit_bones["J_Bip_R_UpperLeg"])
        self.base_lower_leg_editbones = Pair(edit_bones["J_Bip_L_LowerLeg"], edit_bones["J_Bip_R_LowerLeg"])
        
        self.base_foot_editbones = Pair(edit_bones['J_Bip_L_Foot'], edit_bones['J_Bip_R_Foot'])
        self.base_toe_editbones = Pair(edit_bones['J_Bip_L_ToeBase'], edit_bones['J_Bip_R_ToeBase'])
        
        self.leg_parent = Pair()
        self.leg_socket = Pair()
        
    def add_heel_mechanism(self, side_string):
        bpy.ops.object.mode_set(mode='EDIT')
        
        ## Create new bones
        heel_base_editbone = armature.data.edit_bones.new(name='MCH_HeelBase_' + side_string)
        heel_base_editbone.tail = Vector((self.base_foot_editbones[side_string].tail.x, 0.1, 0.0))
        heel_base_editbone.head = Vector((self.base_foot_editbones[side_string].tail.x,  -0.1, 0.0))
        
        heel_back_editbone = armature.data.edit_bones.new(name='MCH_HeelBack_' + side_string)
        heel_back_editbone.head = heel_base_editbone.tail
        heel_back_editbone.tail = heel_base_editbone.tail + Vector((0, 0, 0.1))
        heel_base_editbone.parent = heel_back_editbone
        
        control_bone = armature.data.edit_bones.new(name='CTRL_Heel_' + side_string)
        control_bone.head = heel_back_editbone.head + Vector((0, 0.05, 0))
        control_bone.tail = control_bone.head + Vector((0, 0, 0.05))
        
        foot_root = armature.data.edit_bones.new("MCH_FootRoot_" + side_string)
        foot_root.head = self.base_foot_editbones[side_string].head
        foot_root.tail = self.base_foot_editbones[side_string].head + Vector((0, -0.1, 0))
        
        ## Assign parents
        self.base_foot_editbones[side_string].parent = heel_base_editbone
        self.base_toe_editbones[side_string].parent = heel_back_editbone
        control_bone.parent = foot_root
        heel_back_editbone.parent = foot_root
        heel_base_editbone.parent = heel_back_editbone
        
        ## Create constraints
        bpy.ops.object.mode_set(mode='POSE')
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
        

    def add_leg_socket_mechanism(self, side):
        bpy.ops.object.mode_set(mode='EDIT')
        
        #upper_leg_bone = edit_bones["J_Bip_" + side_string + "_UpperLeg"]
        #lower_leg_bone = edit_bones["J_Bip_" + side_string + "_LowerLeg"]
        foot_bone = edit_bones["J_Bip_" + side + "_Foot"]
        hips_bone = edit_bones["J_Bip_C_Hips"]
        
        #upper_leg_editbone = armature.data.edit_bones.new("MCH_UpperLeg_FK_" + side_string)
        #upper_leg_editbone.head = self.base_upper_leg_editbones[side].head
        #upper_leg_editbone.tail = self.base_lower_leg_editbones.head
        
        #lower_leg_editbone = armature.data.edit_bones.new("MCH_LowerLeg_FK_" + side_string)
        #lower_leg_editbone.head = lower_leg_bone.head
        #lower_leg_editbone.tail = foot_bone.head
        
        self.leg_parent[side] = armature.data.edit_bones.new('MCH_LegParent_' + side)
        self.leg_parent[side].head = self.base_upper_leg_editbones[side].head
        self.leg_parent[side].tail = self.base_upper_leg_editbones[side].head + Vector((0, -0.1, 0))
        
        self.leg_socket[side] = armature.data.edit_bones.new('MCH_LegSocket_' + side)
        self.leg_socket[side].head = self.base_upper_leg_editbones[side].head
        self.leg_socket[side].tail = self.base_upper_leg_editbones[side].head + Vector((0, -0.05, 0))
        
        self.leg_socket[side].parent = hips_bone
        #upper_leg_editbone.parent = self.leg_parent[side]
        #lower_leg_editbone.parent = upper_leg_editbone
        self.base_upper_leg_editbones[side].parent = self.leg_parent[side]
        self.base_lower_leg_editbones[side].parent = self.base_upper_leg_editbones[side]
         
        bpy.ops.object.mode_set(mode='POSE')
        leg_socket_posebone = pose_bones[self.leg_socket[side].name]
        leg_parent_posebone = pose_bones[self.leg_parent[side].name]
        
        copy_loc_constraint = leg_parent_posebone.constraints.new(type='COPY_LOCATION')
        copy_loc_constraint.target = armature
        copy_loc_constraint.subtarget = leg_socket_posebone.name
        
        copy_trns_constraint = leg_parent_posebone.constraints.new(type='COPY_TRANSFORMS')
        copy_trns_constraint.target = armature
        copy_trns_constraint.subtarget = leg_socket_posebone.name
        
        # Setup driver
        trns_driver = copy_trns_constraint.driver_add('influence')
        var = trns_driver.driver.variables.new()
        var.type = 'SINGLE_PROP'
        target = var.targets[0]
        target.id_type = 'OBJECT'
        target.id = skeleton_object
        armature['isolate_rotation'] = 0.0
        target.data_path = '["isolate_rotation"]'
        trns_driver.driver.expression = var.name
        
        return
    
        # FK
        # Make deform chain copy FK chain's rotations
        #upper_leg_posebone = pose_bones[upper_leg_editbone.name]
        #upper_leg_posebone = pose_bones[self.base_upper_leg_editbones[side].name]
        base_upper_leg_posebone = pose_bones[self.base_upper_leg_editbones[side].name]
        Utilities.make_copy_rot_constraint(armature, base_upper_leg_posebone, upper_leg_posebone)
        
        lower_leg_posebone = pose_bones[lower_leg_editbone.name]
        base_lower_leg_posebone = pose_bones[self.base_lower_leg_editbones[side].name]
        Utilities.make_copy_rot_constraint(armature, base_lower_leg_posebone, lower_leg_posebone)
        
        # END OF FK
        
        
        
    def add_leg_fk_mechanism(self, side):
        None
        
    def add_leg_ik_mechanism(self, side):
        None
        
    
if __name__ == '__main__':
    Utilities.reset()
    armature = bpy.context.active_object
    try:
        vrig = VRigify(armature)
        #vrig.add_heel_mechanism('L')
        #vrig.add_heel_mechanism('R')
        vrig.add_leg_socket_mechanism('L')
    except:
        Utilities.reset()
        a = 1/0