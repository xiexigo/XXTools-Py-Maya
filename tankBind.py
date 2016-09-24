import XXTools as xxt
import maya.cmds as cmd
import math as math

#坦克绑定(全骨骼版)
def TankBind():
	for obj in cmd.ls(sl=True):
	    t = cmd.getAttr(obj+".translate")[0]
	    cmd.setAttr(obj+".translate", 0,0,0)
	    body = None
	    for c in cmd.listRelatives(obj, c=True, f=True, typ="transform"):
	        print(c)
	        if c.lower().find("body") >= 0:
	            body = c
	            break
	    if body != None:
	        cmd.select(body)
	        bindInfo = xxt.autoBind("Body")
	        root = bindInfo[2].getJoint()
	        for j in cmd.listRelatives(root, c=True, f=True, typ="transform"):
	            if j.lower().find("wheel") >= 0:
	                attr = j+".rx"
	                cmd.setKeyframe(attr, v=0, t=0)
	                cmd.setKeyframe(attr, v=360, t=60)
	                cmd.keyTangent(attr, itt = "spline", ott = "spline")
	        cmd.setAttr(bindInfo[0]+".inheritsTransform", False)
	        cmd.parent(bindInfo[0],root,obj)
	    else:
	        print("can't find body")
	    print(t)
	    cmd.setAttr(obj+".translate", t[0],t[1],t[2])

#轮子分组
def GroupWheel():
	wheels = cmd.ls(sl = True, l = True, type = "transform")
	if len(wheels)<=0:
		return
	cmd.makeIdentity(apply=True, t=1, r=1, s=1, n=0, pn=1)
	cmd.CenterPivot()
	parent = cmd.listRelatives(wheels[0], parent = True, fullPath = True)[0]
	center = 0
	if parent:
		#如果有父物体，中心为父物体中心
		pt = xxt.Transform()
		xxt.getWorldTransfrom(parent, pt)
		center = pt.t[0]
	l = []
	r = []
	print("一共%d个轮子"%len(wheels))
	for w in wheels:
		t = xxt.Transform()
		xxt.getWorldTransfrom(w, t)
		#以中心为界左右分组
		if t.t[0]<center:
			l.append([w,t])
		else:
			r.append([w,t])
	l.sort(lambda a,b:cmp(a[1].t[2], b[1].t[2]), reverse=True)#按z从大到小排序
	r.sort(lambda a,b:cmp(a[1].t[2], b[1].t[2]), reverse=True)#按z从大到小排序
	count = min(len(l),len(r))
	print("一共%d排轮子"%(count))
	ws = []
	for i in range(count):
		w = cmd.polyUnite([l[i][0], r[i][0]], name="Wheel%d"%(i))[0]
		cmd.delete(w, ch=True)
		w = cmd.parent(w, parent)[0]
		ws.append(w)
	cmd.select(ws, r=True)
	cmd.makeIdentity(apply=True, t=1, r=1, s=1, n=0, pn=1)
	cmd.CenterPivot()

#绑定轮子添加轮子动画
def BindWheel():
	bindInfo = xxt.MultiBind(name = "Wheel")
	joints = bindInfo[2]
	for j in joints:
		attr = j+".rx"
		cmd.setKeyframe(attr, v=0, t=0)
		cmd.setKeyframe(attr, v=360, t=30)
		cmd.keyTangent(attr, itt = "spline", ott = "spline")

#获取物体包围盒
def GetSize(obj):
	count = len(cmd.filterExpand(obj+".vtx[*]", ex=True, fp=True , sm=31))
	_min = list(cmd.getAttr(obj+".vrts[0]")[0])
	_max = list(cmd.getAttr(obj+".vrts[0]")[0])
	for i in range(count):		
		pos = cmd.getAttr(obj+".vrts[%d]"%i)[0]
		_min[0] = min(_min[0], pos[0])
		_min[1] = min(_min[1], pos[1])
		_min[2] = min(_min[2], pos[2])
		_max[0] = max(_max[0], pos[0])
		_max[1] = max(_max[1], pos[1])
		_max[2] = max(_max[2], pos[2])
	return (_max[0] - _min[0], _max[1] - _min[1], _max[2] - _min[2])

#设置炮台,制作动画
def SetCannon(angle = 10, distance = 0.2):
	angle = -angle
	cannon = cmd.ls(sl=True, l = True, type = "transform")[0]
	barrel1 = cmd.listRelatives(cannon, c=True, f=True, typ="transform")[0]
	barrel2 = cmd.listRelatives(barrel1, c=True, f=True, typ="transform")[0]
	size = GetSize(barrel2)
	print(size)
	cmd.setAttr(barrel1+".rotateX", angle)
	parent = cmd.listRelatives(cannon, parent = True, fullPath = True)[0]
	barrel2 = cmd.parent(barrel2, parent)[0]
	cannonShape = cmd.listRelatives(cannon, s=True, f=True)[0]
	barrel1Shape = cmd.listRelatives(barrel1, s=True, f=True)[0]
	barrel2Shape = cmd.listRelatives(barrel2, s=True, f=True)[0]
	newCanon = cmd.polyUnite([cannonShape, barrel1Shape], name="Cannon")[0]
	cmd.delete(newCanon, ch=True)
	newCanon = cmd.parent(newCanon, parent)[0]
	barrel2 = cmd.parent(barrel2, newCanon)[0]
	start = cmd.getAttr(barrel2+".t")[0]
	print("Start: "+str(start))
	d = size[2]*distance
	offset = (0.0, math.sin(math.radians(angle))*d, math.cos(math.radians(angle))*d)
	print("Offset: "+str(offset))
	end = (start[0]-offset[0], start[1]+offset[1], start[2]-offset[2])
	print("End: "+str(end))
	cmd.setKeyframe(barrel2, at="translateY", v=start[1], t=31)
	cmd.setKeyframe(barrel2, at="translateZ", v=start[2], t=31)
	cmd.setKeyframe(barrel2, at="translateY", v=end[1], t=33)
	cmd.setKeyframe(barrel2, at="translateZ", v=end[2], t=33)
	cmd.setKeyframe(barrel2, at="translateY", v=start[1], t=42)
	cmd.setKeyframe(barrel2, at="translateZ", v=start[2], t=42)
	cmd.keyTangent(barrel2, at="translateY", itt = "spline", ott = "spline")
	cmd.keyTangent(barrel2, at="translateZ", itt = "spline", ott = "spline")
	barrel2 = cmd.rename(barrel2, "barrel1")

#坦克工具窗口
def ShowWindowTank():
	if cmd.window("windowTank", ex=True):
		cmd.deleteUI("windowTank")
	window = cmd.window("windowTank", t="Tank Binding", s=False, rtf=True)
	cmd.columnLayout( adjustableColumn=True )
	cmd.button(label="全骨骼版坦克绑定（过期）", w=300, command=("TankBind()"))
	cmd.button(label="左右轮合并", w=300, command=("GroupWheel()"))
	cmd.button(label="绑定轮子", w=300, command=("BindWheel()"))
	angleField = cmd.floatSliderGrp(label='炮管仰角', extraLabel='℃', field=True, minValue=0.0, maxValue=30.0, value=0, step=5, fieldStep=5)
	cmd.button(label="设置炮台", w=300, command=lambda c:SetCannon(angle=cmd.floatSliderGrp(angleField, q=True, v=True)))
	cmd.setParent('..')
	cmd.showWindow(window)

ShowWindowTank()