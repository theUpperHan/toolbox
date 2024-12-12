import maya.cmds as cmds

def calculate_cylinder_diameter(objectName):
    boundingBox = cmds.xform(objectName, query=True, boundingBox=True, worldSpace=True)
    # [xmin, ymin, zmin, xmax, ymax, zmax]

    widthX = boundingBox[3] - boundingBox[0]  
    depthZ = boundingBox[5] - boundingBox[2]  


    diameter = max(widthX, depthZ)

    return diameter
    
objectName = 'birch01_trunk'
diameter = calculate_cylinder_diameter(objectName)
print("Diameter of the cylinder:", diameter)