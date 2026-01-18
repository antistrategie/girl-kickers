from .binary_io import *

KHM_VERSION = 101
KHM_MAX_OBJECT_NAME = 48
KHM_MAX_BONE_INFLUENCES = 4
KHM_MAX_BONES = 64


class sCollisionPolygon:
    def __init__(self, file):
        self.normal = ReadVector3(file)  # normal, -d
        self.d = ReadFloat(file)
        self.numIndices = ReadShort(file)
        self.indexStart = ReadShort(file)


class sCollisionMesh:
    def __init__(self):
        self.pPolygons = None
        self.pIndices = None
        self.pVertices = None
        self.numPolys = 0
        self.numIndices = 0  # triangle indices
        self.numVertices = 0


class Sphere:
    def __init__(self, radius):
        self.radius = radius


class Box:
    def __init__(self, extents):
        self.extents = extents


class Capsule:
    def __init__(self, radius, halfHeight):
        self.radius = radius
        self.halfHeight = halfHeight  # elongates the sphere defined by 'radius' on the X axis. If zero, it's a sphere. (see PhysX manual)


# planes default on +X orientation normal=(1,0,0). Rotate/displace using the collision transform
class Plane:
    def __init__(self):
        pass


class sCollisionShape:
    eCollisionType = {
        0: "SPHERE",
        1: "BOX",
        2: "CAPSULE",
        3: "CONVEX_MESH",  # triangle mesh, assumes concave. Will be cooked into a convex shape at runtime.
        4: "MESH",
        5: "PLANE",
    }

    def __init__(self):
        # self.collisionType = "SPHERE"
        self.bShared = False
        self.setSphere(0.0)
        # self.transform = Matrix.identity
        self.mesh = sCollisionMesh()

    def setSphere(self, radius):
        # self.collisionType = "SPHERE"
        self.sphere = Sphere(radius)
        self.box = None
        self.capsule = None
        self.plane = None

    def setBox(self, extents):
        # self.collisionType = "BOX"
        self.box = Box(extents)
        self.sphere = None
        self.capsule = None
        self.plane = None

    def setCapsule(self, radius, halfHeight):
        # self.collisionType = "CAPSULE"
        self.capsule = Capsule(radius, halfHeight)
        self.sphere = None
        self.box = None
        self.plane = None

    def setConvexMesh(self):
        # self.collisionType = "CONVEX_MESH"
        self.sphere = None
        self.box = None
        self.capsule = None
        self.plane = None

    def GetVolume(self):  # TODO
        return 0.0

    def toJSON(self):
        dictionary = {}
        dictionary["collisionType"] = self.eCollisionType[self.collisionType]
        dictionary["transform_matrix"] = str(self.transform)
        dictionary["transform_pos"] = str(self.transform.to_translation())
        dictionary["transform_rot"] = str(self.transform.to_quaternion())
        dictionary["transform_sca"] = str(self.transform.to_scale())
        if self.eCollisionType[self.collisionType] == "BOX":
            dictionary["extents"] = str(self.box.extents)
        elif self.eCollisionType[self.collisionType] == "CAPSULE":
            dictionary["radius"] = str(self.capsule.radius)
            dictionary["halfHeight"] = str(self.capsule.halfHeight)

        return dictionary


class sObjectBase:
    def __init__(self):
        self.szName = ""
        self.uiId = 0
        self.uiParentId = 0
        self.matLocal = None
        self.matGlobal = None

    def toJSON(self):
        dictionary = {}
        dictionary["szName"] = self.szName
        dictionary["uiId"] = self.uiId
        dictionary["uiParentId"] = self.uiParentId
        dictionary["matLocal"] = str(self.matLocal)
        dictionary["matLocalPosition"] = str(self.matLocal.to_translation())
        dictionary["matLocalRotation"] = str(self.matLocal.to_quaternion())
        dictionary["matLocalScale"] = str(self.matLocal.to_scale())
        dictionary["matGlobal"] = str(self.matGlobal)
        dictionary["matGlobalPosition"] = str(self.matGlobal.to_translation())
        dictionary["matGlobalRotation"] = str(self.matGlobal.to_quaternion())
        dictionary["matGlobalScale"] = str(self.matGlobal.to_scale())
        return dictionary


class sObjectMesh(sObjectBase):
    def __init__(self):
        self.numVertices = 0
        self.pVertices = None
        self.pNormals = None
        self.pColors = None
        self.numTxCoordMaps = 0
        self.pTexCoords = [None, None]
        self.pSkinWeights = None
        self.pSkinBoneIndices = None
        self.numIndices = 0
        self.pIndices = None
        self.pFaceNormals = None
        self.numCollisions = 0
        self.pCollisions = None
        self.min = None
        self.max = None
        self.volume = 0.0

    def toJSON(self):
        print("NUM COLLISIONS", self.numCollisions)
        print("LEN COLLISIONS", len(self.pCollisions))
        dictionary = {}
        dictionary["szName"] = self.szName
        dictionary["uiId"] = self.uiId
        dictionary["uiParentId"] = self.uiParentId
        dictionary["matLocal"] = str(self.matLocal)
        dictionary["matGlobal"] = str(self.matGlobal)
        dictionary["matGlobalPosition"] = str(self.matGlobal.to_translation())
        dictionary["matGlobalRotation"] = str(self.matGlobal.to_quaternion())
        dictionary["matGlobalScale"] = str(self.matGlobal.to_scale())

        dictionary["numVertices"] = self.numVertices
        dictionary["pVertices"] = vector3ArrayToString(self.pVertices)
        dictionary["pNormals"] = vector3ArrayToString(self.pNormals)
        dictionary["pColors"] = vector4ArrayToString(self.pColors)
        dictionary["numTxCoordMaps"] = self.numTxCoordMaps
        dictionary["pTexCoords"] = vector2ArrayToString(self.pTexCoords)
        dictionary["pSkinWeights"] = skinWeightsToString(self.pSkinWeights)
        dictionary["pSkinBoneIndices"] = self.pSkinBoneIndices
        dictionary["numIndices"] = self.numIndices
        dictionary["pIndices"] = self.pIndices
        dictionary["pFaceNormals"] = vector3ArrayToString(self.pFaceNormals)

        dictionary["numCollisions"] = self.numCollisions

        dictionary["pCollisions"] = []
        if self.pCollisions != None:
            for collision in self.pCollisions:
                dictionary["pCollisions"].append(collision.toJSON())
        dictionary["min"] = vector3ToString(self.min)
        dictionary["max"] = vector3ToString(self.max)
        dictionary["volume"] = self.volume
        return dictionary


class sHeader:
    def __init__(self, file):
        self.uiSig = file.read(4)
        self.uiVer = ReadUInt(file)

    def export(file):
        file.write(b"KHM\0")
        WriteUInt(file, KHM_VERSION)


class sAnimationMaskEntry:
    def __init__(self):
        self.mask = 0
        self.szNodeName = ""

    def toJSON(self):
        dictionary = {}
        dictionary["mask"] = self.mask
        dictionary["szNodeName"] = self.szNodeName
        return dictionary


class sAnimationMask:
    def __init__(self):
        self.sAnimationMaskEntry = []
        self.numNodes = 0

    def toJSON(self):
        dictionary = {}
        dictionary["numNodes"] = self.numNodes
        dictionary["sAnimationMaskEntry"] = []
        for animationMaskEntry in self.sAnimationMaskEntry:
            dictionary["sAnimationMaskEntry"].append(animationMaskEntry.toJSON())
        return dictionary


class sNodeTransform:
    def __init__(self):
        self.qRot = None  # quaternion
        self.vTrans = None
        self.vScale = None


class sNodeAnimation:
    def __init__(self):
        self.uiNodeId = 0
        self.szNodeName = ""

    def toJSON(self):
        dictionary = {}
        dictionary["uiNodeId"] = self.uiNodeId
        dictionary["szNodeName"] = self.szNodeName
        return dictionary


class sAnimation:
    def __init__(self):
        self.pNodeAnimations = []
        self.pNodeTransforms = []
        self.numNodes = 0
        self.numNodeFrames = 0
        self.frameDurationMs = 0.0
        self.startTimeS = 0.0
        self.endTimeS = 0.0

    def toJSON(self):
        dictionary = {}
        dictionary["numNodes"] = self.numNodes
        dictionary["numNodeFrames"] = self.numNodeFrames
        dictionary["frameDurationMs"] = self.frameDurationMs
        dictionary["pNodeTransforms"] = []
        dictionary["startTimeS"] = self.startTimeS
        dictionary["endTimeS"] = self.endTimeS
        # for node in range(self.numNodes):
        #    for frame in range(self.numNodeFrames):
        #        dictionary["pNodeTransforms"].append("a")

        print("length: ", len(self.pNodeTransforms))
        for node in range(self.numNodes):
            transforms = []
            for frame in range(self.numNodeFrames - 1):
                index = (self.numNodeFrames * node) + frame
                print("index", index)
                transforms.append(pNodeTransformToString(self.pNodeTransforms[index]))

            dictionary["pNodeTransforms"].append(transforms)

        # dictionary["pNodeAnimations"] = []
        # for anim in self.pNodeAnimations:
        #    dictionary["pNodeAnimations"].append(anim.toJSON())
        # for transform in self.pNodeTransforms:
        #    dictionary["pNodeTransforms"].append(pNodeTransformToString(transform))
        return dictionary


class sModelDefinition:
    def __init__(self):
        self.pMesh = None
        self.numHelpers = 0
        self.lHelpers = None
        self.numBones = 0
        self.lBones = None
        self.pAnimation = None
        self.pAnimationMask = None
        self.membuff = None

    def GetObjectById(self, uiId):
        pass

    def GetObjectByName(self, pszName):
        pass

    def toJSON(self):
        dictionary = {}
        if self.pMesh != None:
            dictionary["pMesh"] = self.pMesh.toJSON()
        else:
            dictionary["pMesh"] = None
        dictionary["numHelpers"] = self.numHelpers
        dictionary["Helpers"] = []
        if self.lHelpers != None:
            for helper in self.lHelpers:
                dictionary["Helpers"].append(helper.toJSON())
        dictionary["numBones"] = self.numBones
        dictionary["lBones"] = []
        if self.lBones != None:
            for bone in self.lBones:
                dictionary["lBones"].append(bone.toJSON())
        if self.pAnimation != None:
            dictionary["pAnimation"] = self.pAnimation.toJSON()
        if self.pAnimationMask != None:
            dictionary["pAnimationMask"] = self.pAnimationMask.toJSON()
        return dictionary
