import struct

from bpy_extras.io_utils import axis_conversion
from mathutils import Matrix, Quaternion, Vector

KHM_VERSION = 101
KHM_MAX_OBJECT_NAME = 48
KHM_MAX_BONE_INFLUENCES = 4
KHM_MAX_BONES = 64


def ReadUChar(file):
    return struct.unpack("B", file.read(1))[0]


def WriteUChar(file, value):
    file.write(struct.pack("B", value))


def ReadUInt(file):
    return struct.unpack("I", file.read(4))[0]


def WriteUInt(file, value):
    file.write(struct.pack("I", value))


def ReadInt(file):
    return struct.unpack("i", file.read(4))[0]


def WriteInt(file, value):
    file.write(struct.pack("i", value))


def ReadUShort(file):
    return struct.unpack("H", file.read(2))[0]


def WriteUShort(file, value):
    file.write(struct.pack("H", value))


def ReadFloat(file):
    return struct.unpack("f", file.read(4))[0]


def WriteFloat(file, value):
    file.write(struct.pack("f", value))


def ReadVector2(file):
    return Vector((ReadFloat(file), ReadFloat(file)))


def WriteVector2(file, value):
    WriteFloat(file, value[0])
    WriteFloat(file, value[1])


def ReadVector3(file):
    return Vector((ReadFloat(file), ReadFloat(file), ReadFloat(file)))


def ReadSwizzledVector3(file):
    x = ReadFloat(file)
    y = ReadFloat(file)
    z = ReadFloat(file)
    return Vector((x, -z, y))


def WriteVector3(file, value):
    WriteFloat(file, value[0])
    WriteFloat(file, value[1])
    WriteFloat(file, value[2])


def WriteSwizzledVector3(file, value):
    WriteFloat(file, value[0])
    WriteFloat(file, value[2])
    WriteFloat(file, -value[1])


def ReadVector4(file):
    return Vector((ReadFloat(file), ReadFloat(file), ReadFloat(file), ReadFloat(file)))


def WriteVector4(file, value):
    WriteFloat(file, value[0])
    WriteFloat(file, value[1])
    WriteFloat(file, value[2])
    WriteFloat(file, value[3])


m = axis_conversion(from_forward="Z", from_up="Y", to_forward="-Y", to_up="Z").to_4x4()


def ReadQuaternion(file):
    x = ReadFloat(file)
    y = ReadFloat(file)
    z = ReadFloat(file)
    w = ReadFloat(file)
    return Quaternion((w, x, -z, y))


def WriteQuaternion(file, value):
    WriteFloat(file, value.x)
    WriteFloat(file, value.z)
    WriteFloat(file, -value.y)
    WriteFloat(file, value.w)


def ReadSBoneIndice(file):
    arr = []
    for i in range(KHM_MAX_BONE_INFLUENCES):
        arr.append(ReadUChar(file))
    return arr


def WriteSBoneIndice(file, arr):
    for i in arr:
        WriteUChar(file, i)


def ReadMatrix(file):
    r1 = (ReadFloat(file), ReadFloat(file), ReadFloat(file), ReadFloat(file))
    r2 = (ReadFloat(file), ReadFloat(file), ReadFloat(file), ReadFloat(file))
    r3 = (ReadFloat(file), ReadFloat(file), ReadFloat(file), ReadFloat(file))
    r4 = (ReadFloat(file), ReadFloat(file), ReadFloat(file), ReadFloat(file))

    pos, rot, sca = Matrix([r1, r2, r3, r4]).decompose()
    pos = Vector((pos.x, -pos.z, pos.y))
    rot = Quaternion((rot.w, rot.x, -rot.z, rot.y))

    return Matrix.LocRotScale(pos, rot, sca)


def WriteMatrix(file, value):
    # pos, rot, sca = value.decompose() #This doesn't do rotations quite right
    pos = value.to_translation()
    rot = value.to_quaternion()
    sca = value.to_scale()

    pos = Vector((pos.x, pos.z, -pos.y))
    rot = Quaternion((rot.w, rot.x, rot.z, -rot.y))
    value = Matrix.LocRotScale(pos, rot, sca)

    for x in range(4):
        for y in range(4):
            WriteFloat(file, value[x][y])


def ReadObjectName(file):
    return file.read(KHM_MAX_OBJECT_NAME).decode("utf-8").replace("\u0000", "")


def WriteObjectName(file, value):
    byte_value = value.encode("utf_8")
    file.write(byte_value)
    for i in range(KHM_MAX_OBJECT_NAME - len(value)):
        file.write(b"\0")


def WriteNull(file, amount):
    for i in range(amount):
        file.write(b"\0")
