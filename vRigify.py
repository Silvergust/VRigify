import bpy

from mathutils import (
Vector
)

center_bone_names = []
side_bone_names = [ "MCH_HeelBase_",
                    "MCH_HeelBack_",
                    "CTRL_Heel_",
                    "MCH_FootRoot_",
                    "MCH_UpperLeg_FK_",
                    "MCH_LowerLeg_FK_",
                    "MCH_Foot_FK_",
                    "MCH_UpperLeg_IK_",
                    "MCH_LowerLeg_IK_",
                    "MCH_Foot_IK_",
                    "CTRL_KneeTarget_",
                    "MCH_LegParent_",
                    "MCH_LegSocket_",
                    "CTRL_Palm_",
                    "CTRL_Fingers_"]

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
        print(self.armature)
        #self.leg_parents = Pair()
        #self.leg_sockets = Pair()
        self.leg_parent_names = Pair() # It's not nice like this, but bone addresses are bound to change unpredictably during execution,
        self.leg_socket_names = Pair() # it's more reliable to look them up by their names
        self.knee_target_names = Pair()
        
        self.upper_leg_fk_names = Pair()
        self.lower_leg_fk_names = Pair()
        self.foot_fk_names = Pair()
        
        self.upper_leg_ik_names = Pair()
        self.lower_leg_ik_names = Pair()
        self.foot_ik_names = Pair()
        
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
        self.base_hand_editbones = Pair(edit_bones["J_Bip_L_Hand"], edit_bones["J_Bip_R_Hand"])
    
    def reset(self, side_string=None):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.armature.select_all(action='DESELECT')
        edit_bones = self.armature.data.edit_bones
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
        
        
    def add_heel_mechanism(self, side_string):
        bpy.ops.object.mode_set(mode='EDIT')
        self.detect_base_leg_bones()
        
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
    socket_name: Name of the socket bone to add (sans the side suffix).'''
    def add_socket_mechanism(self, side, outer_bone, parent_name, socket_name, first_link, second_link):
        bpy.ops.object.mode_set(mode='EDIT')
        
        edit_bones = self.armature.data.edit_bones
        
        parent = armature.data.edit_bones.new(parent_name + side)
        parent.head = self.base_upper_leg_editbones[side].head
        parent.tail = parent.head + Vector((0, -0.1, 0))
        
        socket = armature.data.edit_bones.new(socket_name + side)
        socket.head = self.base_upper_leg_editbones[side].head
        socket.tail = socket .head+ Vector((0, -0.05, 0))
        
        socket.parent = outer_bone
        first_link.parent = parent
        second_link.parent = first_link
    
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
    
        self.assign_influence_driver(copy_trns_constraint, "follow_socket_rotation")
        
        return parent.name, socket.name


    def add_leg_socket_mechanism(self, side):
        bpy.ops.object.mode_set(mode='EDIT')
        hips_bone = self.armature.data.edit_bones["J_Bip_C_Hips"]
        upper_bone = self.base_upper_leg_editbones[side]
        lower_bone = self.base_lower_leg_editbones[side]
        names = self.add_socket_mechanism(side, hips_bone, "MCH_Parent_", "MCH_Socket_", upper_bone, lower_bone)
        self.leg_parent_names[side] = names[0]
        self.leg_socket_names[side] = names[1]
        return names
    
        
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
        foot_editbone.head = lower_leg_editbone.tail
        foot_editbone.tail = lower_leg_editbone.tail + Vector((0, 0, -0.15))
        
        upper_leg_editbone.parent = edit_bones[self.leg_parent_names[side]]
        lower_leg_editbone.parent = upper_leg_editbone
        foot_editbone.parent = lower_leg_editbone
        
        return upper_leg_editbone, lower_leg_editbone, foot_editbone
    
    
    def add_leg_fk_chain(self, side):
        upper_leg_editbone, lower_leg_editbone, foot_editbone = self.create_leg_bones("_FK", side)
        self.upper_leg_fk_names[side] = upper_leg_editbone.name
        self.lower_leg_fk_names[side] = lower_leg_editbone.name
        self.foot_fk_names[side] = foot_editbone.name
        edit_bones = self.armature.data.edit_bones   
        
        #bpy.ops.object.mode_set(mode='POSE')
        #pose_bones = self.armature.pose.bones
        
        #base_upper_leg_posebone = pose_bones[self.base_upper_leg_editbones[side].name]
        #Utilities.make_copy_rot_constraint(armature, base_upper_leg_posebone, pose_bones[upper_leg_editbone.name])
        
        #lower_leg_posebone = pose_bones[lower_leg_editbone.name]
        #base_lower_leg_posebone = pose_bones[self.base_lower_leg_editbones[side].name]
        #Utilities.make_copy_rot_constraint(armature, base_lower_leg_posebone, pose_bones[lower_leg_editbone.name])
        
        
    def add_leg_ik_chain(self, side):
        upper_leg_editbone, lower_leg_editbone, foot_editbone = self.create_leg_bones("_IK", side)
        foot_editbone.parent = None
        self.upper_leg_ik_names[side] = upper_leg_editbone.name
        self.lower_leg_ik_names[side] = lower_leg_editbone.name
        self.foot_ik_names[side] = foot_editbone.name
        
        edit_bones = self.armature.data.edit_bones
        knee_subtarget_editbone = edit_bones.new("CTRL_KneeTarget_" + side)
        knee_subtarget_editbone.head = lower_leg_editbone.head + Vector((0, -1, 0))
        knee_subtarget_editbone.tail = knee_subtarget_editbone.head + Vector((0, -0.2, 0))

        bpy.ops.object.mode_set(mode='POSE')
        pose_bones = self.armature.pose.bones   
        
        foot_posebone = pose_bones[foot_editbone.name]
        lower_leg_posebone = pose_bones[lower_leg_editbone.name]
        knee_subtarget_posebone = pose_bones[knee_subtarget_editbone.name]
        ik_constraint = lower_leg_posebone.constraints.new(type='IK')
        ik_constraint.target = self.armature
        ik_constraint.subtarget = foot_posebone.name
        ik_constraint.pole_target = self.armature
        ik_constraint.pole_subtarget = knee_subtarget_posebone.name
        ik_constraint.chain_count = 2
        
        
    def setup_leg_mechanism(self, side):
        bpy.ops.object.mode_set(mode='EDIT')
        self.detect_base_leg_bones()
        pose_bones = self.armature.pose.bones
        
        # Set base bones to copy FK chain rotations
        Utilities.make_copy_rot_constraint(self.armature, pose_bones[self.base_upper_leg_editbones[side].name], pose_bones[self.upper_leg_fk_names[side]])
        Utilities.make_copy_rot_constraint(self.armature, pose_bones[self.base_lower_leg_editbones[side].name], pose_bones[self.lower_leg_fk_names[side]])
        Utilities.make_copy_rot_constraint(self.armature, pose_bones[self.base_foot_editbones[side].name], pose_bones[self.foot_fk_names[side]])
        
        #Set base bones to copy IK chain rotations, and create drivers to control their influence  
        constraint = Utilities.make_copy_rot_constraint(self.armature, pose_bones[self.base_upper_leg_editbones[side].name], pose_bones[self.upper_leg_ik_names[side]])
        self.assign_influence_driver(constraint, 'fk_ik')
        constraint = Utilities.make_copy_rot_constraint(self.armature, pose_bones[self.base_lower_leg_editbones[side].name], pose_bones[self.lower_leg_ik_names[side]])
        self.assign_influence_driver(constraint, 'fk_ik')
        constraint = Utilities.make_copy_rot_constraint(self.armature, pose_bones[self.base_foot_editbones[side].name], pose_bones[self.foot_ik_names[side]])
        self.assign_influence_driver(constraint, 'fk_ik')
        
    def add_palm_rig(self, side):
        self.detect_base_arm_bones()
        edit_bones = self.armature.data.edit_bones
        
        palm_editbone = edit_bones.new("CTRL_Palm_" + side)
        palm_editbone.head = self.base_hand_editbones[side].head + Vector((0, 0, 0.05))
        palm_editbone.tail = palm_editbone.head + Vector((0.06 * (1 if side == 'L' else -1), 0, 0))
        palm_editbone.parent = self.base_hand_editbones[side]
        
        fingers_editbone = edit_bones.new("CTRL_Fingers_" + side)
        fingers_editbone.head = palm_editbone.tail
        fingers_editbone.tail = fingers_editbone.head + Vector((0.03 * (1 if side == 'L' else -1), 0, 0))
        fingers_editbone.parent = palm_editbone
        
        edit_bones["J_Bip_" + side + "_Little1"].parent = palm_editbone
        edit_bones["J_Bip_" + side + "_Ring1"].parent = palm_editbone
        edit_bones["J_Bip_" + side + "_Little1"].parent = palm_editbone
        edit_bones["J_Bip_" + side + "_Little1"].parent = palm_editbone
        #Create finger bones on palm
        
if __name__ == '__main__':
    armature = bpy.context.active_object
    print("\n\n\n ########## \n\n\n")
    try:
        vrig = VRigify(armature)
        vrig.reset()
        
        vrig.add_heel_mechanism('L')
        vrig.add_leg_socket_mechanism('L')
        vrig.add_leg_fk_chain('L')
        vrig.add_leg_ik_chain('L')
        vrig.setup_leg_mechanism('L')
        vrig.add_palm_rig('L')
    except:
        vrig.reset()
        a = 1/0