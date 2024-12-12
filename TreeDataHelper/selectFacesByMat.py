import maya.cmds as cmds

def select_by_material(material):
    shading_groups = cmds.ls(cmds.listConnections(material), type='shadingEngine')
    print(shading_groups)
    faces_to_select = []
    
    for sg in shading_groups:
        connections = cmds.listConnections(sg + ".dagSetMembers", type='mesh')
        
        for conn in connections:
            # Ensure we get the long name to avoid duplicates and ensure uniqueness
            full_path = cmds.ls(conn, long=True)[0]
            faces = cmds.sets(sg, query=True) or []
            for face in faces:
                open_b_idx = face.index('[')
                clos_b_idx = face.index(']')
                face_idxes_int = [int(idx) for idx in face[open_b_idx+1:clos_b_idx].split(':')]
                for i in range(face_idxes_int[0], face_idxes_int[1] + 1):
                    face_path = full_path + '.f[' + str(i) + ']'
                    faces_to_select.append(face_path)
    return faces_to_select
   
                    

trunk = select_by_material('betula_bark_a_ncl1_2')
#leaves = select_by_material('MaterialFBXASC032FBXASC035266796055')

#cmds.select('Brich_01.f[*]')
#cmds.select(leaves, deselect=True)
#cmds.select(small_branches, deselect=True)
cmds.select(trunk)






    