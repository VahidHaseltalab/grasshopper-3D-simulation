# =============================================================================
# G-code simulator on grasshopper 3D 
# https://youtu.be/lSWfTrf4IHk
# =============================================================================
__author__ = "Vahid"
__version__ = "2019.01.13"

import rhinoscriptsyntax as rs
import time
import Grasshopper as gh
import Rhino
import scriptcontext as sc
import System as sys
t = float(t)
def updateComponent(t):
    
    """ Updates this component, similar to using a grasshopper timer """
    
    # Define callback action
    def callBack(e):
        ghenv.Component.ExpireSolution(False)
        
    # Get grasshopper document
    ghDoc = ghenv.Component.OnPingDocument()
    
    # Schedule this component to expire
    ghDoc.ScheduleSolution(t,gh.Kernel.GH_Document.GH_ScheduleDelegate(callBack)) 
    # Note that the first input here is how often to update the component (in milliseconds)
# read each g-code line and extract each axis motion for CNC machine
def dcode1(a):
    global p1x, p1y, A, B, Z
    for i in range(len(a)):
        if a[i][0] == "X":
            p1x = int(a[i][1:])
        elif a[i][0] == "Y":
            p1y = int(a[i][1:])
        elif a[i][0] == "A":
            A = int(a[i][1:])
        elif a[i][0] == "B":
            B = int(a[i][1:])
        elif a[i][0] == "Z":
            Z = int(a[i][1:])
    return p1x, p1y, A, B, Z
# read each g-code line and extract each axis motion for FFF printer
def dcode2(a):
    global p2x, p2y, A, B, Z
    bo = False
    for i in range(len(a)): # check each index of the list
        if a[i][0] == "X":
            bo = True
            p2x = float(a[i][1:])
        elif a[i][0] == "Y":
            bo = True
            p2y = float(a[i][1:])
        elif a[i][0] == "A":
            A = float(a[i][1:])
        elif a[i][0] == "B":
            B = float(a[i][1:])
        elif a[i][0] == "Z":
            bo = True
            Z = float(a[i][1:])
        else: pass
    return p2x, p2y, A, B, Z, bo

# Get to the GH objects
ghObjects = ghenv.Component.OnPingDocument().Objects
for obj in ghObjects:
    if obj.NickName == "Z-translation" and type(obj) is gh.Kernel.Special.GH_NumberSlider:
        Zslider = obj
    elif obj.NickName == "A-rotation" and type(obj) is gh.Kernel.Special.GH_NumberSlider:
        Aslider = obj
    elif obj.NickName == "B-rotation" and type(obj) is gh.Kernel.Special.GH_NumberSlider:
        Bslider = obj
    elif obj.NickName == "p1-Y translation" and type(obj) is gh.Kernel.Special.GH_NumberSlider:
        p1yslider = obj
    elif obj.NickName == "p1-X translation" and type(obj) is gh.Kernel.Special.GH_NumberSlider:
        p1xslider = obj
    elif obj.NickName == "p2-Y translation" and type(obj) is gh.Kernel.Special.GH_NumberSlider:
        p2yslider = obj
    elif obj.NickName == "p2-X translation" and type(obj) is gh.Kernel.Special.GH_NumberSlider:
        p2xslider = obj
    elif obj.NickName == "Work_piece" and type(obj) is gh.Kernel.Special.GH_NumberSlider:
        wp = obj

# Baking for G1 code
def bake(ob):
    sc.doc = ghdoc
    
    #get object id from grasshopper
    obj_id = ob
    #convert grasshopper object into rhino object
    doc_obj = rs.coercerhinoobject(obj_id)
    
    #make attributes and geometry from rhino object
    attributes = doc_obj.Attributes
    geometry = doc_obj.Geometry
    
    #go rhino document
    sc.doc = Rhino.RhinoDoc.ActiveDoc
    
    #bake object with attributes
    rhino_obj = sc.doc.Objects.Add(geometry, attributes)
    
    #back to gh
    sc.doc = ghdoc

# Instantiate/reset persisent starting counter variable
if "count" not in globals():
    count = 0; modelbool = 0
    p1x = -80; p1y = -30; A = 0; B = 0;layer = 0.0001
    Z = 0; p2x = 0; p2y = 0; g1 = 0;p = 0
# Reseting the counters
if reset:
    count = 0
    p1x = -50; p1y = -30; A = 0; B = 0
    Z = 0; p2x = 0; p2y = 0; g1 = 0;layer = 0.0001
    p1xslider.Slider.Value = p1x
    p1yslider.Slider.Value = p1y
    Aslider.Slider.Value = A
    Bslider.Slider.Value = B
    Zslider.Slider.Value = Z
    p2xslider.Slider.Value = p2x
    p2yslider.Slider.Value = p2y
    wp.Slider.Value = 0.3

if p == 2:
    dx = -314.81; dy = 191.19; dz = 227.5
    xx2 = dx - p2xslider.Slider.Value
    yy2 = dy - p2yslider.Slider.Value 
    zz2 = Zslider.Slider.Value  + dz
    pt1 = [xx2,yy2,zz2]

elif p == 1:
    dx = -346.2; dy = 110; dz = 215
    xx1 = dx - p1xslider.Slider.Value
    yy1 = dy - p1yslider.Slider.Value 
    zz1 = Zslider.Slider.Value  + dz
    ptt1 = rs.AddPoint([xx1,yy1,zz1])
# variable a presents each line of g-code
a = Gcodes[count]
# decision between the process of printing or machining is defined by P1 and P2
if a[0] == "P1":
    p = 1
elif a[0] == "P2":
    p = 2
else: pass
# define the target slider amounts
if a[0] != '' and len(a) > 1:
    if (a[0] == "G1" or a[0] == "G0") and p == 1:
        p1x, p1y, A, B, Z = dcode1(a)
        p1x += 30; p1y += 25
        if a[0] == "G1": 
            g1 = True
            ### last model
            if p == 1:
                sc.doc = Rhino.RhinoDoc.ActiveDoc
                rs.ClearCommandHistory()
                rs.Command("SelAll")
                if rs.CommandHistory()[-31:-1] == "No objects added to selection.":
                    bake(mod1)
                    rs.Command("SelAll")
                model = rs.SelectedObjects()
                sc.doc = ghdoc
        elif a[0] == "G0": g1 = False
    elif (a[0] == "G1" or a[0] == "G0") and p == 2:
        p2x, p2y, A, B, Z, bo = dcode2(a)
        if Z != Zslider.Slider.Value:
            modelbool = 1
        else:
            modelbool = 0
        if a[0] == "G1": g1 = True
        elif a[0] == "G0": g1 = False
    else:
        pass
# the current position of sliders
position = [p1x, p1y, A, B, Z,p2x, p2y]

# Update the variable and component
if len(a) > 1:
    # rewrite the sliders value
    p1xslider.Slider.Value = p1x
    p1yslider.Slider.Value = p1y
    Aslider.Slider.Value = A
    Bslider.Slider.Value = B
    Zslider.Slider.Value = Z
    p2xslider.Slider.Value = p2x
    p2yslider.Slider.Value = p2y
    wp.Slider.Value = Z
    updateComponent(t)
### Update Gcode line number
if bool and count < len(Gcodes)-1:
    count +=1
    updateComponent(t)
if modelbool:
    sc.doc = Rhino.RhinoDoc.ActiveDoc
    rs.Command("SelAll")
    rs.Command("Delete")
    sc.doc = ghdoc
# Update the counter for changing the g-code line
if p == 2:
    try:
        dx = -314.81; dy = 191.19; dz = 227.5
        #dx = -400; dy = 110; dz = 200
        xx2 = dx - p2xslider.Slider.Value
        yy2 = dy - p2yslider.Slider.Value 
        zz2 = Zslider.Slider.Value  + dz
        pt2 = [xx2,yy2,zz2]
        pt3 = [xx2,yy2,zz2-0.1]
        vc = rs.VectorCreate(pt1,pt2)
        plane = rs.PlaneFromNormal(pt2,vc)
        p1 = rs.MovePlane(rs.WorldXYPlane(),pt2)
        cr = rs.AddCircle(p1,0.4)
        tt = rs.PlaneCurveIntersection(plane,cr)
        path = rs.AddLine(pt2,pt3)
        lin = rs.AddLine(tt[0][1],tt[1][1])
    except: pass
elif p == 1:
    dx = -346.2; dy = 110; dz = 215
    xx1 = dx - p1xslider.Slider.Value
    yy1 = dy - p1yslider.Slider.Value 
    zz1 = Zslider.Slider.Value  + dz
    ptt2 = rs.AddPoint([xx1,yy1,zz1])

# Baking the relating object based on G1 code
if g1 and p == 1:
    lnn = rs.AddLine(ptt1,ptt2)
    drll = rs.AddPipe(lnn,0,5,cap = 2)
    model1 = rs.BooleanDifference(model,drll)
    rs.Command("SelAll")
    rs.Command("Delete")
    bake(lnn)
elif g1 and p == 2:
    try:
        ln3 = rs.AddLine(pt2,pt1)
        srf = rs.ExtrudeCurve(lin,path)
        srf1 = rs.ExtrudeSurface(srf,ln3)
        bake(srf1)
    except: pass