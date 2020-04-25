import os

from topaz.objects.stringobject import W_StringObject
from topaz.utils.ll_file import O_BINARY
from topaz.objects.intobject import W_FixnumObject


def map_filemode(space, w_mode):
    encoding = ""

    if hasattr(space, 'w_ArgumentError'):
        def raise_error(space, msg):
            raise space.error(space.w_ArgumentError, msg)
    else:
        def raise_error(msg):
            return

    if w_mode is space.w_nil or w_mode is None:
        mode = os.O_RDONLY
        mode_str = "r"
    elif isinstance(w_mode, W_StringObject):
        mode_str = space.str_w(w_mode)
        mode = 0
        major_mode_seen = False
        readable = writeable = append = False

        pos = 0
        for ch in mode_str:
            pos += 1
            if ch == "b":
                mode |= O_BINARY
            elif ch == "+":
                readable = writeable = True
            elif ch == "r":
                if major_mode_seen:
                    raise_error(space, "invalid access mode %s" % mode_str)
                major_mode_seen = True
                readable = True
            elif ch == "a":
                if major_mode_seen:
                    raise_error(space, "invalid access mode %s" % mode_str)
                major_mode_seen = True
                mode |= os.O_CREAT
                append = writeable = True
            elif ch == "w":
                if major_mode_seen:
                    raise_error(space, "invalid access mode %s" % mode_str)
                major_mode_seen = True
                mode |= os.O_TRUNC | os.O_CREAT
                writeable = True
            elif ch == ":":
                encoding = mode_str[pos + 1:]
                break
            else:
                raise_error(space, "invalid access mode %s" % mode_str)
        if readable and writeable:
            mode |= os.O_RDWR
        elif readable:
            mode |= os.O_RDONLY
        elif writeable:
            mode |= os.O_WRONLY
        if append:
            mode |= os.O_APPEND
    elif isinstance(w_mode, W_FixnumObject): # TODO: user convert_type :to_int may be?
        mode = space.int_w(w_mode)
        mode_str = ""
        if mode & (os.O_APPEND):
            mode_str += "a"
        if mode & (os.O_RDONLY):
            mode_str += "r"
        if mode & (os.O_TRUNC | os.O_CREAT | os.O_WRONLY | os.O_RDWR):
            mode_str += "w"
        if mode & (O_BINARY):
            mode_str += "b"
        if len(mode_str) == 0:
            mode_str = "r"
    else:
        mode = os.O_RDONLY
        mode_str = "r"
        raise_error(space, "Expected String or Int as mode")

    return (mode, mode_str, encoding)
