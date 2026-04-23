import importlib
import core.MayaWidget
importlib.reload(core.MayaWidget)
from core.MayaWidget import MayaWidget # Calling to the MayaWidget file to get the commands

import importlib
import core.MayaUtilities # Calling to the MayaUtilities file
importlib.reload(core.MayaUtilities) 
from core.MayaUtilities import (CreateCircleControllerForJnt,
                                 CreateBoxControllerForJnt, 
                                 CreatePlusController, 
                                 ConfigureCtrlForJnt, 
                                 GetObjectPositionAsMVec)
# Above is all of the imported functions that will be needed throughout the code
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout,QLineEdit, QPushButton, QLabel, QColorDialog
# Above is the imported Widget information
import maya.cmds as mc
from maya.OpenMaya import MVector 

# The Rigging functions within the widget. The major mechanics within the widget for the arm rigging functions
class LimbRigger:
    def __init__(self):
        self.nameBase = ""
        self.controllerSize = 10
        self.blendControllerSize = 4
        self.controlColorRGB = [0,0,0]

    def SetNameBase(self,newNameBase):
        self.nameBase = newNameBase
        print(f"name base is set to: {self.nameBase}")

    def SetControllerSize(self, newControllerSize):
        self.controllerSize = newControllerSize

    def SetBlendControllerSize(self, newBlendControllerSize):
        self.blendControllerSize = newBlendControllerSize

    def RigLimb(self):
        print("Start rigging!!") 
        rootJnt, midJnt, endJnt = mc.ls(sl=True)
        print(f"found root {rootJnt}, mid: {midJnt} and end: {endJnt}")
    # Adding the circle controllers for FK for the Shoulder, Elbow, and Wrist
        rootCtrl, rootCtrlGrp = CreateCircleControllerForJnt(rootJnt, "fk_" + self.nameBase, self.controllerSize)
        midCtrl, midCtrlGrp = CreateCircleControllerForJnt(midJnt, "fk_" + self.nameBase, self.controllerSize)
        endCtrl, endCtrlGrp = CreateCircleControllerForJnt(endJnt, "fk_" + self.nameBase, self.controllerSize) 

        mc.parent(endCtrlGrp, midCtrl)
        mc.parent(midCtrlGrp, rootCtrl)
    # Adding the Box Controller on the Wrist for IK
        endIKCtrl, endIKCtrlGrp = CreateBoxControllerForJnt(endJnt, "ik_" + self.nameBase, self.controllerSize) 
    # Adding the IK FK Blend to the Plus shape to switch between the two
        ikFKBlendCtrlPrefix = self.nameBase + "_ikfkBlend"
        ikFkBlendController = CreatePlusController(ikFKBlendCtrlPrefix, self.blendControllerSize)
        ikFkBlendController,ikFkBlendControllerGrp = ConfigureCtrlForJnt(rootJnt, ikFkBlendController, False)
    # Switching between Fk and IK
        ikFkBlendAttrName = "ikfkBlend"
        mc.addAttr(ikFkBlendController, ln = ikFkBlendAttrName, min = 0, max = 1, k = True) 

        ikHandleName = "ikHandle_" + self.nameBase
        mc.ikHandle(n = ikHandleName, sj = rootJnt, ee = endJnt, sol = "ikRPsolver")

        rootJntLoc = GetObjectPositionAsMVec(rootJnt)
        endJntLoc = GetObjectPositionAsMVec(endJnt)
    # Adding the Elbow controller for IK in the form of a Pole Vector
        poleVectorVals = mc.getAttr(f"{ikHandleName}.poleVector")[0] 
        poleVecDir = MVector(poleVectorVals[0], poleVectorVals[1], poleVectorVals[2]) 
        poleVecDir.normalize() 

        rootToEndVec = endJntLoc - rootJntLoc
        rootToEndDist = rootToEndVec.length()

        poleVectorCtrlLoc = rootJntLoc + rootToEndVec/2.0 + poleVecDir * rootToEndDist 

        poleVectorCtrlName = "ac_ik_" + self.nameBase + "poleVector"
        mc.spaceLocator(n=poleVectorCtrlName)

        poleVectorCtrlGrpName = poleVectorCtrlName + "_grp"
        mc.group(poleVectorCtrlName, n = poleVectorCtrlGrpName) 

        mc.setAttr(f"{poleVectorCtrlGrpName}.translate", poleVectorCtrlLoc.x, poleVectorCtrlLoc.y, poleVectorCtrlLoc.z, type = "double3")
        mc.poleVectorConstraint(poleVectorCtrlName, ikHandleName) 

        mc.parent(ikHandleName, endIKCtrl) 
        mc.setAttr(f"{ikHandleName}.v",0) 
    # Commands to the FK IK Blend so that the function works in the ChannelBox
        mc.connectAttr(f"{ikFkBlendController}.{ikFkBlendAttrName}", f"{ikHandleName}.ikBlend")
        mc.connectAttr(f"{ikFkBlendController}.{ikFkBlendAttrName}", f"{endIKCtrlGrp}.v")
        mc.connectAttr(f"{ikFkBlendController}.{ikFkBlendAttrName}",f"{poleVectorCtrlGrpName}.v")

        reverseNodeName = f"{self.nameBase}_reverse"
        mc.createNode("reverse", n = reverseNodeName) 

        mc.connectAttr(f"{ikFkBlendController}.{ikFkBlendAttrName}", f"{reverseNodeName}.inputX")
        mc.connectAttr(f"{reverseNodeName}.outputX", f"{rootCtrlGrp}.v")
    # Adding the orient constraint on the wrist
        orientConstraint = None
        wristConnections = mc.listConnections(endJnt)
        for connection in wristConnections:
            if mc.objectType(connection) == "orientConstraint":
                orientConstraint = connection
                break
   
        mc.connectAttr(f"{ikFkBlendController}.{ikFkBlendAttrName}",f"{orientConstraint}.{endIKCtrl}W1")
        mc.connectAttr(f"{reverseNodeName}.outputX", f"{orientConstraint}.{endCtrl}W0") 
    # Oranization commands for putting the rig Controllers, parents, vecorts, everything we added above into groups in the Outliner    
        topGrpName = f"{self.nameBase}_rig_grp"
        mc.group(n=topGrpName, empty = True) 
    # Names to all the empty groups to place the controllers in
        mc.parent(rootCtrlGrp, topGrpName) # Name and empties of the root of shoulder controller
        mc.parent(ikFkBlendControllerGrp, topGrpName) # Name and empties of the ikfkBlend Controller
        mc.parent(endIKCtrlGrp, topGrpName) # Name of the IK Controller group
        mc.parent(poleVectorCtrlGrpName, topGrpName)

        mc.setAttr(topGrpName + ".overrideEnabled",1) 
        mc.setAttr(topGrpName + ".overrideRGBColors",1) 
        mc.setAttr(topGrpName + ".overrideColorRGB", self.controlColorRGB[0], self.controlColorRGB[1], self.controlColorRGB[2])
        # add color override for the topGrpName to be self.controlColorRGB

# The Widget/Window information to make the function pop up in Maya
class LimbRiggerWidget(MayaWidget):
    def __init__(self):
        super().__init__()
        # Naming and adding the button to the main Widget and the Limb Rigger Button
        self.setWindowTitle("Limb Rigger") # Name of the Widget that will appear in Maya
        self.rigger = LimbRigger() 
        self.masterLayout = QVBoxLayout() 
        self.setLayout(self.masterLayout)
        
        self.masterLayout.addWidget(QLabel("Select the 3 joints of the limb, from the base to the end, and then:"))
        
        self.infoLayout = QHBoxLayout()
        self.masterLayout.addLayout(self.infoLayout)
        self.infoLayout.addWidget(QLabel("Name Base"))

        self.nameBaseLineEdit = QLineEdit()
        self.infoLayout.addWidget(self.nameBaseLineEdit)# makes the button appear on the Widget as a button
        # Names the joints selected in the Outliner when the Button is clicked
        self.setNameBaseBtn = QPushButton("Set Name Base") # Creates the name base button to name the controller
        self.setNameBaseBtn.clicked.connect(self.SetNameBaseBtnClicked) # activates the Name Base button function when clicked
        self.infoLayout.addWidget(self.setNameBaseBtn) # makes the button appear on the Widget as a button

        # add a color pick widget to the self.masterLayout
        # listen for a color change and connect to a function
        # the function needs to update the color of limbRigger: self.rigger.controlColorRGB
        self.colorPicker = QPushButton("Color Pick") # Creates the Color Picker button to name the controller
        self.colorPicker.clicked.connect(self.ColorPickerBtnClicked) # activates the Color Pick button function when clicked
        self.masterLayout.addWidget(self.colorPicker) # makes the button appear on the Widget as a button
        
        # Calling the Rig Limb Button and incorperating the code used in RigLimb to apply it
        self.rigLimbBtn = QPushButton("Rig Limb")
        self.rigLimbBtn.clicked.connect(self.RigLimbBtnClicked) # activates the Rig Limb button function when clicked
        self.masterLayout.addWidget(self.rigLimbBtn)
        

    def SetNameBaseBtnClicked(self): # Mechanics for the NameBase Button To add the naming in the Outliner
        self.rigger.SetNameBase(self.nameBaseLineEdit.text()) 

    def RigLimbBtnClicked(self): # Mechanics for the LimbRig Button to add the Rig itself
        self.rigger.RigLimb()

    def ColorPickerBtnClicked(self): # Mechanics for the Color Picker Button to change the color of the controller
        colorPicker = QColorDialog().getColor()
        self.rigger.controlColorRGB[0] = colorPicker.redF()
        self.rigger.controlColorRGB[1] = colorPicker.greenF()
        self.rigger.controlColorRGB[2] = colorPicker.blueF()
        print(self.rigger.controlColorRGB)
    # Widget Hash or address for the widget itself
    def GetWidgetHash(self):
        return "2ca60b746dd9080a287428a1235b61cb52293d295c27448cacf3da17032a9cd3"
    
# Makes it activate
def Run():
    limbRiggerWidget = LimbRiggerWidget()
    limbRiggerWidget.show()

Run() 