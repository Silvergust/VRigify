import bpy

from mathutils import (
Vector
)

center_bone_names = []
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
                    "MCH_FootRoot_",
                    "MCH_ArmParent_",
                    "MCH_ArmSocket_",
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

    def make_ik_constraint(armature, owner_posebone, extremity_posebone, pole_posebone, chain_count=2):
        constraint = owner_posebone.constraints.new(type='IK')
        constraint.target = armature
        constraint.subtarget = extremity_posebone.name
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
        print(self.armature)
        #self.leg_parents = Pair()
        #self.leg_sockets = Pair()
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
        heel_base_editbone.parent = heel_back_editbone
        
        heel_back_editbone = armature.data.edit_bones.new(name='MCH_HeelBack_' + side_string)
        heel_back_editbone.head = heel_base_editbone.tail
        heel_back_editbone.tail = heel_base_editbone.tail + Vector((0, 0, 0.1))
        self.heel_names[side_string] = heel_base_editbone.name
        
        control_bone = armature.data.edit_bones.new(name='CTRL_Heel_' + side_string)
        control_bone.head = heel_back_editbone.head + Vector((0, 0.05, 0))
        control_bone.tail = control_bone.head + Vector((0, 0, 0.05))
        
        foot_root = armature.data.edit_bones.new("MCH_FootRoot_" + side_string)
        foot_root.head = self.base_foot_editbones[side_string].head
        foot_root.tail = self.base_foot_editbones[side_string].head + Vector((0, -0.1, 0))
        
        ## Create constraints
        bpy.ops.object.mode_set(mode='POSE')
        pose_bones = self.armature.pose.bones
        
        print(heel_back_editbone.name)
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
            prop_name = parent_name + "_influence_"
        self.assign_influence_driver(copy_trns_constraint, prop_name + side)
        
        return parent.name, socket.name


    def add_leg_socket_mechanism(self, side):
        bpy.ops.object.mode_set(mode='EDIT')
        self.detect_base_leg_bones()
        hips_bone = self.armature.data.edit_bones["J_Bip_C_Hips"]
        upper_bone = self.base_upper_leg_editbones[side]
        names = self.add_socket_mechanism(side, hips_bone, "MCH_LegParent_", "MCH_LegSocket_", upper_bone, "leg_follows_hip_")
        self.leg_parent_names[side] = names[0]
        self.leg_socket_names[side] = names[1]
        return names
    
    
    def add_arm_socket_mechanism(self, side):
        bpy.ops.object.mode_set(mode='EDIT')
        self.detect_base_arm_bones()
        shoulder_bone = self.armature.data.edit_bones["J_Bip_" + side + "_Shoulder"]
        upper_bone = self.base_upper_arm_editbones[side]
        names = self.add_socket_mechanism(side, shoulder_bone, "MCH_ArmParent_", "MCH_ArmSocket_", upper_bone, "arm_follows_shoulder_")
        self.arm_parent_names[side] = names[0]
        self.arm_socket_names[side] = names[1]
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
    
    
    def create_arm_bones(self, suffix, side):
        bpy.ops.object.mode_set(mode='EDIT')
        self.detect_base_arm_bones()
        
        edit_bones = self.armature.data.edit_bones
        upper_arm_editbone = edit_bones.new("MCH_UpperArm" + suffix + "_" + side)
        upper_arm_editbone.head = self.base_upper_arm_editbones[side].head
        upper_arm_editbone.tail = self.lower_arm_editbones[side].head
        
        lower_arm_editbone = edit_bones.new("MCH_LowerArm" + suffix + "_" + side)
        lower_arm_editbone.head = self.base_lower_arm_editbones[side].head
        lower_arm_editbone.tail = self.base_hand_editbones[side].head
        
        hand_editbone = edit_bones.new("MCH_Hand" + suffix + "_" + side)
        hand_editbone.head = lower_arm_editbone.tail
        hand_editbone.tail = lower_leg_editbone.tail + Vector((0.1 * (1 if side == 'L' else -1), 0, 0))
    
        upper_arm_editbone.parent = edit_bones[self.arm_parent_names[side]]
        lower_arm_editbone.parent = upper_arm_editbone
        foot_editbone.parent = lower_arm_editbone
        
        return upper_arm_editbone, lower_arm_editbone, hand_editbone
    
    
    def add_leg_fk_chain(self, side):
        upper_leg_editbone, lower_leg_editbone, foot_editbone = self.create_leg_bones("_FK", side)
        self.upper_leg_fk_names[side] = upper_leg_editbone.name
        self.lower_leg_fk_names[side] = lower_leg_editbone.name
        self.foot_fk_names[side] = foot_editbone.name
        #edit_bones = self.armature.data.edit_bones   
        
        foot_editbone = self.armature.data.edit_bones["J_Bip_" + side + "_Foot"]
        #foot_editbone.parent = lower_leg_editbone
        self.armature.data.edit_bones["J_Bip_" + side + "_ToeBase"].parent = foot_editbone
        
        
    def add_arm_fk_chain(self, side):
        upper_arm_editbone, lower_arm_editbone, hand_editbone = self.create_arm_bones("_FK", side)
        self.upper_arm_fk_names[side] = upper_arm_editbone.name
        self.lower_arm_fk_names[side] = lower_arm_editbone.name
        self.hand_fk_names[side] = arm_editbone.name
        
        
    def add_ik_chain(self, side, pole_name, pole_offset, first_link, second_link, final_link): 
        edit_bones = self.armature.data.edit_bones
        pose_bones = self.armature.pose.bones 
        
        
        pole_subtarget_editbone = edit_bones.new(pole_name + side)
        pole_subtarget_editbone.head = second_link.head + pole_offset
        pole_subtarget_editbone.tail = pole_subtarget_editbone.head + 0.2 * pole_offset
        
        bpy.ops.object.mode_set(mode='POSE')
        final_link_posebone = pose_bones[final_link.name]
        second_link_posebone = pose_bones[second_link.name]
        pole_subtarget_posebone = pose_bones[pole_subtarget_editbone.name]
        
        bpy.ops.object.mode_set(mode='POSE')
        iK_constraint = Utilities.make_ik_constraint(self.armature, second_link_posebone, final_link_posebone, pole_subtarget_posebone)
        
        return pole_subtarget_posebone.name
    
    
    def add_leg_ik_chain(self, side):
        upper_leg_editbone, lower_leg_editbone, foot_editbone = self.create_leg_bones("_IK", side)
        foot_editbone.parent = None
        
        self.upper_leg_ik_names[side] = upper_leg_editbone.name
        self.lower_leg_ik_names[side] = lower_leg_editbone.name
        self.foot_ik_names[side] = foot_editbone.name
        
        self.knee_target_names[side] = self.add_ik_chain(side, "CTRL_KneeTarget_", Vector((0, -1, 0)), upper_leg_editbone, lower_leg_editbone, foot_editbone)
   
        
        
        
    #def add_leg_ik_chain(self, side):
        #upper_leg_editbone, lower_leg_editbone, foot_editbone = self.create_leg_bones("_IK", side)
        #foot_editbone.parent = None
        #self.upper_leg_ik_names[side] = upper_leg_editbone.name
        #self.lower_leg_ik_names[side] = lower_leg_editbone.name
        #self.foot_ik_names[side] = foot_editbone.name
        
        #edit_bones = self.armature.data.edit_bones
        #knee_subtarget_editbone = edit_bones.new("CTRL_KneeTarget_" + side)
        #knee_subtarget_editbone.head = lower_leg_editbone.head + Vector((0, -1, 0))
        #knee_subtarget_editbone.tail = knee_subtarget_editbone.head + Vector((0, -0.2, 0))

        #bpy.ops.object.mode_set(mode='POSE')
        #pose_bones = self.armature.pose.bones   
        
        #foot_posebone = pose_bones[foot_editbone.name]
        #lower_leg_posebone = pose_bones[lower_leg_editbone.name]
        #knee_subtarget_posebone = pose_bones[knee_subtarget_editbone.name]
        
        #Utilities.make_ik_constraint(self.armature, lower_leg_posebone, foot_posebone, knee_subtarget_posebone)
        
        
    def setup_leg_fkik_mechanism(self, side):
        bpy.ops.object.mode_set(mode='EDIT')
        self.detect_base_leg_bones()
        pose_bones = self.armature.pose.bones
        
        # Set base bones to copy FK chain rotations
        Utilities.make_copy_rot_constraint(self.armature, pose_bones[self.base_upper_leg_editbones[side].name], pose_bones[self.upper_leg_fk_names[side]])
        Utilities.make_copy_rot_constraint(self.armature, pose_bones[self.base_lower_leg_editbones[side].name], pose_bones[self.lower_leg_fk_names[side]])
        Utilities.make_copy_rot_constraint(self.armature, pose_bones[self.base_foot_editbones[side].name], pose_bones[self.foot_fk_names[side]])
        
        #Set base bones to copy IK chain rotations, and create drivers to control their influence  
        constraint = Utilities.make_copy_rot_constraint(self.armature, pose_bones[self.base_upper_leg_editbones[side].name], pose_bones[self.upper_leg_ik_names[side]])
        self.assign_influence_driver(constraint, 'leg_fk_ik_' + side)
        constraint = Utilities.make_copy_rot_constraint(self.armature, pose_bones[self.base_lower_leg_editbones[side].name], pose_bones[self.lower_leg_ik_names[side]])
        self.assign_influence_driver(constraint, 'leg_fk_ik_' + side)
        constraint = Utilities.make_copy_rot_constraint(self.armature, pose_bones[self.base_foot_editbones[side].name], pose_bones[self.foot_ik_names[side]])
        self.assign_influence_driver(constraint, 'leg_fk_ik_' + side)
        
        edit_bones = self.armature.data.edit_bones
        edit_bones[self.heel_names[side]].parent = edit_bones[self.foot_ik_names[side]]
        
        
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
            
        
if __name__ == '__main__':
    armature = bpy.context.active_object
    print("\n\n\n ########## \n\n\n")
    
    
    try:
        vrig = VRigify(armature)
        print("AAA")
        #print(armature.data.edit_bones.keys())
        #print(armature.pose.bones.keys())
        vrig.reset()
        
        #vrig.add_heel_mechanism('L')
        #vrig.add_leg_socket_mechanism('L')
        #vrig.add_leg_fk_chain('L')
        #vrig.add_leg_ik_chain('L')
        #vrig.setup_leg_fkik_mechanism('L')
        
        #vrig.setup_leg_rig()
        
        vrig.setup_leg_rig('L')
        
        #vrig.setup_leg_rig('R')
        
        #vrig.add_palm_rig('L')
        #vrig.add_arm_socket_mechanism('L')
        #vrig.add_arm_socket_mechanism('R')
    except:
        #vrig.reset()
        a = 1/0