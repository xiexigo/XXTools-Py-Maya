# -*- coding: UTF-8 -*-

import maya.cmds as cmd

#查找源节点
def searchSourceNodes(nodeName):
	connections = cmd.listConnections(nodeName, s=True, d=False)
	if connections == None or len(connections) == 0:
		return []
	nodeList = []
	for node in connections:
		if nodeList.count(node) == 0 :
			nodeList.append(node)
	curList = nodeList
	for node in curList:
		nextSearchNodes = searchSourceNodes(node)
		nodeList.extend(nextSearchNodes)
	return nodeList

#寻找输入源中所有的file节点
def searchFileNodes(nodeList):
	nodeList = nodeList or []
	fileNode = []
	for node in nodeList:
		fileNode.extend(cmd.ls(searchSourceNodes(node), type="file"))
	return fileNode

class TextureEntity(object):	
	def __init__(self, nodeName):
		super(TextureEntity, self).__init__()
		if cmd.objectType(nodeName) == "file":
			self.textureNode = nodeName
	def getFileName(self):
		return cmd.getAttr(self.textureNode + ".fileTextureName")
	def renameByFileName(self):
		filepath = self.getFileName()
		strs = filepath.split("/")
		fileFullname = strs[-1]
		filename = fileFullname.split(".")[0]
		cmd.rename( self.textureNode, "tex_"+filename)

#获得物体的UVSets
def getUVSets(obj):
    return cmd.polyUVSet(obj, query=True, allUVSets=True )
#获得物体的UVSets的数量
def getUVSetsCount(obj):
    return len(getUVSets(obj))
#选中UVSets数量不符的物体
def checkSelectedObjectUVSetCount(number):
	number = number or 1
	objs = []
	sel = cmd.ls(selection=True)
	for obj in sel:
		count = getUVSetsCount(obj)
		if count != number:
			objs.append(obj)
	if len(objs)>0:
	    cmd.select(objs)
	else:
		cmd.select(cl=True)


#################################################

# 获取所有子物体
def getAllChildren(obj):
	children = []
	cs = cmd.listRelatives(obj, c=True, f=True, typ="transform")
	for c in (cs or []):
		children.append(c)
		children.extend(getAllChildren(c))
	return children

# 获取无路径名称
def getNoPathName(fullname):
	names = fullname.split("|")
	return names[-1]

# two array add one by one
def arrayPlus(a,b):
	result = []
	for i in xrange(min(len(a),len(b))):
		result.append(a[i]+b[i])
	return result

# [] -> [[],[],[],[]]
def array2Matrix44(m):
	return [\
		[m[0],	m[1],	m[2],	m[3]],\
		[m[4],	m[5],	m[6],	m[7]],\
		[m[8],	m[9],	m[10],	m[11]],\
		[m[12],	m[13],	m[14],	m[15]]]

# [[1,2],[3,4]] * [[1,2],[3,4]] = 
def matrixMultiply(a,b):
	c = []
	row = len(a)
	col = len(b[0])
	m = len(b)
	for i in xrange(row):
		c.append([]);
		for j in xrange(col):
			r = 0
			for k in xrange(m):
				r += a[i][k]*b[k][j]
			c[i].append(r)
	return c

# Get localToWorld transform matrix
def getWorldXformMatrix(obj):
	mt = array2Matrix44(cmd.getAttr(obj+".xformMatrix"))
	parents = cmd.listRelatives(obj, parent = True, fullPath = True)
	if parents == None:
		# no parent.
		return mt
	else:
		pmt = getWorldXformMatrix(parents[0])
		return matrixMultiply(mt,pmt)
		
# Get world translate
def getWorldTranslate(obj):
	mt = getWorldXformMatrix(obj)
	return [mt[3][0],mt[3][1],mt[3][2]]

class Node:
	def __init__(self, mesh, vtxCount = 0):
		self.mesh_ = mesh
		vtxs = cmd.filterExpand(mesh + ".vtx[*]", ex=True, sm=31)
		vtxCount = vtxCount or 0
		self.vtxStart_ = vtxCount
		self.vtxEnd_ = vtxCount + len(vtxs) - 1
		self.children_ = []

	def getVtx(self):
		return ".vtx["+ str(self.vtxStart_) + ":"+ str(self.vtxEnd_) +"]"

	def getEndVtxIndex(self):
		return self.vtxEnd_

	def setJoint(self,joint):
		self.joint_ = joint
	def getJoint(self):
		return self.joint_

	def addChild(self, node):
		self.children_.append(node)
	def getChildren(self):
		return self.children_

class Transform:
	def __init__(self):
		self.t = []
		self.r = []
		self.s = []
		

def getWorldTransfrom(obj, t):
	rp = list(cmd.getAttr(obj+".rp")[0])
	rpt = list(cmd.getAttr(obj+".rpt")[0])
	p = arrayPlus(rp,rpt)
	# convert to([x,y,z,1])
	p.append(1)
	mt = getWorldXformMatrix(obj)
	wp = matrixMultiply([p], mt)
	t.t = [wp[0][0],wp[0][1],wp[0][2]]
	t.r = list(cmd.getAttr(obj+".rotate")[0])
	t.s = list(cmd.getAttr(obj+".scale")[0])


# Create joint by object, recursive function for autoBind()
def createJointByObj(obj, vtxStartIndex = 0):
	t = Transform()
	getWorldTransfrom(obj, t)
	node = Node(obj, vtxStartIndex)
	jointName = ""
	if vtxStartIndex == 0:
		jointName = "root"
	else:
		jointName = obj.split("|")[-1]
	joint = cmd.joint(a=True, p=tuple(t.t), s=tuple(t.s), n=jointName)
	cmd.rotate(t.r[0], t.r[1], t.r[2], joint)
	# print(joint)
	node.setJoint(joint)
	vtxStartIndex = node.getEndVtxIndex()+1

	children = cmd.listRelatives(obj, c=True, f=True, typ="transform")
	# print("vtxStartIndex ", vtxStartIndex)
	if children!=None :
		for c in children:
			cmd.select(joint)
			nodeInfo = createJointByObj(c, vtxStartIndex)
			subNode = nodeInfo[0]
			node.addChild(subNode)
			vtxStartIndex = nodeInfo[1]
	return (node, vtxStartIndex)

# recursive call autoWeight for node and all children
def autoSkinWeight(mesh,skin,node):
	vtx = mesh + node.getVtx()
	joint = node.getJoint()
	print(skin,vtx,joint)
	cmd.skinPercent(skin, vtx, transformValue=[(joint, 1.0)])
	for subNode in node.getChildren():
		autoSkinWeight(mesh, skin, subNode)

# autoBind
def autoBind(name = None):
	obj = cmd.ls(sl = True, l = True)[0]	
	cmd.select(d=True)
	nodeInfo = createJointByObj(obj)
	node = nodeInfo[0]
	joint = node.getJoint()
	print("joint ready!")
	uniteInfo = cmd.polyUnite(obj, ch=1, mergeUVSets=1)
	outObj = uniteInfo[0]
	print("combin objects complete! newObject: " + outObj)
	cmd.delete(uniteInfo, ch=True)
	skin = cmd.skinCluster(joint, outObj, mi=2)[0]
	autoSkinWeight(outObj,skin,node)
	if name :
		outObj = cmd.ls(cmd.rename(outObj, name), l = True)[0]
	return (outObj,skin,node)

def MultiBind(name = None):
	objs = cmd.ls(sl = True, l = True, type = "transform")
	if len(objs)>0 :
		joints = []
		nodes = []
		parent = cmd.listRelatives(objs[0], parent = True, fullPath = True)
		locator = "|"+cmd.spaceLocator(n = "root")[0]
		locator = cmd.parent(locator, parent)[0]
		vtxStartIndex = 0
		for obj in objs:
			t = Transform()
			getWorldTransfrom(obj, t)
			node = Node(obj, vtxStartIndex)
			cmd.select(locator, r = True)
			joint = cmd.joint(a=True, p=tuple(t.t), s=tuple(t.s), n=obj.split("|")[-1])
			cmd.rotate(t.r[0], t.r[1], t.r[2], joint)
			node.setJoint(joint)
			vtxStartIndex = node.getEndVtxIndex()+1
			joints.append(joint)
			nodes.append(node)
		uniteInfo = cmd.polyUnite(objs, ch=1, mergeUVSets=1)
		outObj = uniteInfo[0]
		print("combin objects complete! newObject: " + outObj)
		cmd.delete(uniteInfo, ch=True)
		skin = cmd.skinCluster(joints, outObj, mi=2)[0]
		for node in nodes:			
			autoSkinWeight(outObj,skin,node)
		if name :
			outObj = cmd.ls(cmd.rename(outObj, name), l = True)[0]
		outObj = cmd.parent(outObj, parent)[0]
		return (outObj,locator,joints)