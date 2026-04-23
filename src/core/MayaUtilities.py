import maya.cmds as mc
import maya.mel as ml
from maya.OpenMaya import MVector

def ConfigureCtrlForJnt(jnt, ctrlName, doContraint=True):
    ctrlGrpName = ctrlName + "_grp"
    mc.group(ctrlName, n = ctrlGrpName)
    
    mc.matchTransform(ctrlGrpName, jnt)
    if doContraint:
        mc.orientConstraint(ctrlName, jnt) 

    return ctrlName, ctrlGrpName

# make the plus shaped controller, this will be used for the ikfk blend
def CreatePlusController(namePrefix, size = 1):
    ctrlName = f"ac_{namePrefix}"
    cmd = (f"curve - n {ctrlName} -d 1 -p 3 0 1 -p 3 0 -1 -p 1 0 -1 -p 1 0 -3 -p -1 0 -3 -p -1 0 -1 -p -3 0 -1 -p -3 0 1 -p -1 0 1 -p -1 0 3 -p 1 0 3 -p 1 0 1 -p 3 0 1 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 ;")
    ml.eval(cmd)
    mc.setAttr(f"{ctrlName}.scale", size, size, size, type = "double3")

    #freeze transfrom
    mc.makeIdentity(ctrlName, apply = True)

    # Lock everything when the cross is applied 
    mc.setAttr(f"{ctrlName}.translateX", lock = True, keyable = False, channelBox = False)
    mc.setAttr(f"{ctrlName}.translateY", lock = True, keyable = False, channelBox = False)
    mc.setAttr(f"{ctrlName}.translateZ", lock = True, keyable = False, channelBox = False)

    mc.setAttr(f"{ctrlName}.rotateX", lock = True, keyable = False, channelBox = False)
    mc.setAttr(f"{ctrlName}.rotateY", lock = True, keyable = False, channelBox = False)
    mc.setAttr(f"{ctrlName}.rotateZ", lock = True, keyable = False, channelBox = False)

    mc.setAttr(f"{ctrlName}.scaleX", lock = True, keyable = False, channelBox = False)
    mc.setAttr(f"{ctrlName}.scaleY", lock = True, keyable = False, channelBox = False)
    mc.setAttr(f"{ctrlName}.scaleZ", lock = True, keyable = False, channelBox = False)

    mc.setAttr(f"{ctrlName}.visibility", lock = True, keyable = False, channelBox = False)

    SetCurveLineWidth(ctrlName, 2) 
    return ctrlName
    # use the ml.eval() to make the plus shaped curve
    # scale the controller to the size
    # freeze transformations
    # lock and hide the translate, scale, and rotation, and visability of the controller


def CreateCircleControllerForJnt(jnt, namePrefix, radius = 10):
    ctrlName = f"ac_{namePrefix}_{jnt}" 
    mc.circle(n = ctrlName, r = radius, nr = (1,0,0))
    SetCurveLineWidth(ctrlName, 2)
    return ConfigureCtrlForJnt(jnt, ctrlName)  


def CreateBoxControllerForJnt(jnt, namePrefix, size = 10):
    ctrlName = f"ac_{namePrefix}_{jnt}"
    ml.eval(f"curve -n {ctrlName} -d 1 -p -0.242772 0 0.211132 -p 0.5 0.5 0.5 -p -0.5 0.5 0.5 -p -0.5 0.5 -0.5 -p 0.5 0.5 -0.5 -p 0.5 0.5 0.5 -p 0.5 -0.5 0.5 -p 0.5 -0.5 -0.5 -p -0.5 -0.5 -0.5 -p -0.5 -0.5 0.5 -p 0.5 -0.5 0.5 -p 0.5 0.5 0.5 -p -0.5 0.5 0.5 -p -0.5 -0.5 0.5 -p -0.5 -0.5 -0.5 -p -0.5 0.5 -0.5 -p 0.5 0.5 -0.5 -p 0.5 -0.5 -0.5 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 -k 13 -k 14 -k 15 -k 16 -k 17 ;")
    mc.setAttr(f"{ctrlName}.scale", size,size,size, type = "double3") 
    
    # same as a freeze transformation command in Maya
    mc.makeIdentity(ctrlName, apply = True)
    SetCurveLineWidth(ctrlName, 2) 
    return ConfigureCtrlForJnt(jnt, ctrlName) 

def GetObjectPositionAsMVec(objectName) -> MVector: 
    wsLoc = mc.xform(objectName, t = True, ws = True, q = True) 
    return MVector(wsLoc[0], wsLoc[1], wsLoc[2]) 

def SetCurveLineWidth(curve, newWidth):
    shapes = mc.listRelatives(curve, s = True)
    for shape in shapes:
        mc.setAttr(f"{shape}.lineWidth", newWidth)