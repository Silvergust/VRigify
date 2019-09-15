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

class VRigify:
    def __init__(self, armature):
        self.armature = armature
        self.base_original_upper_leg = 
    def add_heel_mechanism(armature, side_string):
        bpy.ops.object.mode_set(mode='EDIT')
        foot_bone = edit_bones['J_Bip_' + side_string + '_Foot']
        
        ## Create new bones
        heel_base_editbone = armature.data.edit_bones.new(name='MCH_HeelBase_' + side_string)
        heel_base_editbone.tail = Vector((foot_bone.tail.x,   0.1 , 0.0))
        heel_base_editbone.head = Vector((foot_bone.tail.x,  -0.1, 0.0))
        
        heel_back_editbone = armature.data.edit_bones.new(name='MCH_HeelBack_' + side_string)
        heel_back_editbone.head = heel_base_editbone.tail
        heel_back_editbone.tail = heel_base_editbone.tail + Vector((0, 0, 0.1))
        heel_base_editbone.parent = heel_back_editbone
        
        control_bone = armature.data.edit_bones.new(name='CTRL_Heel_' + side_string)
        control_bone.head = heel_back_editbone.head + Vector((0, 0.05, 0))
        control_bone.tail = control_bone.head + Vector((0, 0, 0.05))
        
        foot_root = armature.data.edit_bones.new("MCH_FootRoot_" + side_string)
        foot_root.head = foot_bone.head
        foot_root.tail = foot_bone.head + Vector((0, -0.1, 0))
        
        ## Assign parents
        foot_bone.parent = heel_base_editbone
        toe_bone = edit_bones['J_Bip_' + side_string + '_ToeBase']
        toe_bone.parent = heel_back_editbone
        foot_bone.parent = foot_root
        control_bone.parent = foot_root
        heel_back_editbone.parent = foot_root
        heel_base_editbone.parent = foot_root
        
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
        
        bpy.ops.object.mode_set(mode='EDIT')
        foot_bone.parent = heel_base_editbone
        

    def add_leg_fk_mechanism(armature, side_string):
        bpy.ops.object.mode_set(mode='EDIT')
        
        upper_leg_bone = edit_bones["J_Bip_" + side_string + "_UpperLeg"]
        lower_leg_bone = edit_bones["J_Bip_" + side_string + "_LowerLeg"]
        foot_bone = edit_bones["J_Bip_" + side_string + "_Foot"]
        hips_bone = edit_bones["J_Bip_C_Hips"]
        
        upper_leg_editbone = armature.data.edit_bones.new("MCH_UpperLeg_FK_" + side_string)
        upper_leg_editbone.head = upper_leg_bone.head
        upper_leg_editbone.tail = lower_leg_bone.head
        
        lower_leg_editbone = armature.data.edit_bones.new("MCH_LowerLeg_FK_" + side_string)
        lower_leg_editbone.head = lower_leg_bone.head
        lower_leg_editbone.tail = foot_bone.head
        
        leg_parent = armature.data.edit_bones.new('MCH_LegParent_' + side_string)
        leg_parent.head = upper_leg_bone.head
        leg_parent.tail = upper_leg_bone.head + Vector((0, -0.1, 0))
        
        leg_socket = armature.data.edit_bones.new('MCH_LegSocket_' + side_string)
        leg_socket.head = upper_leg_bone.head
        leg_socket.tail = upper_leg_bone.head + Vector((0, -0.05, 0))
        
        leg_socket.parent = hips_bone
        upper_leg_editbone.parent = leg_parent
        lower_leg_editbone.parent = upper_leg_editbone
         
        bpy.ops.object.mode_set(mode='POSE')
        leg_socket_posebone = pose_bones[leg_socket.name]
        leg_parent_posebone = pose_bones[leg_parent.name]
        
        copy_loc_constraint = leg_parent_posebone.constraints.new(type='COPY_LOCATION')
        copy_loc_constraint.target = armature
        copy_loc_constraint.subtarget = leg_socket_posebone.name
        
        copy_trns_constraint = leg_parent_posebone.constraints.new(type='COPY_TRANSFORMS')
        copy_trns_constraint.target = armature
        copy_trns_constraint.subtarget = leg_socket_posebone.name
        
        # Make deform chain copy FK chain's rotations
        upper_leg_posebone = pose_bones[upper_leg_editbone.name]
        original_upper_leg_posebone = pose_bones[upper_leg_bone.name]
        Utilities.make_copy_rot_constraint(armature, original_upper_leg_posebone, upper_leg_posebone)
        
        lower_leg_posebone = pose_bones[lower_leg_editbone.name]
        original_lower_leg_posebone = pose_bones[lower_leg_bone.name]
        Utilities.make_copy_rot_constraint(armature, original_lower_leg_posebone, lower_leg_posebone)
        
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
        
    def add_leg_ik_mechanism(armature, side_string):
        None
        
    def add_leg_socket_mechanism(armature, side_string):
        None
    
if __name__ == '__main__':
    Utilities.reset()
    armature = bpy.context.active_object
    try:
        #add_heel_mechanism(armature, 'L')
        #add_heel_mechanism(armature, 'R')
        add_leg_mechanism(armature, 'L')
    except:
        Utilities.reset()
        a = 1/0