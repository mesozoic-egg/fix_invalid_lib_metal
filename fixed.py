"""
Tested on M2 macOS 14 

$ uname -a
Darwin pg20.local 23.6.0 Darwin Kernel Version 23.6.0: Mon Jul 29 21:16:46 PDT 2024; root:xnu-10063.141.2~1/RELEASE_ARM64_T8112 arm64

$ python --version
Python 3.10.0

$ python fixed.py
"""


# Below is pasted from the ops_metal.py file from metal-cdll branch from https://github.com/tinygrad/tinygrad/pull/6545
from __future__ import annotations
import ctypes
import functools
from typing import Any, cast, TypeVar
from ctypes.macholib.dyld import dyld_find


# This prevents ctypes from converting response to plain int, and dict.fromkeys() can use it to dedup
class objc_id(ctypes.c_void_p):
    def __hash__(self): return hash(self.value)
    def __eq__(self, other): return self.value == other.value


class objc_instance(objc_id):  # method with name "new", "alloc" should be freed after use
    def __del__(self): msg(self, "release")


@functools.lru_cache(None)
def sel(name: str): return libobjc.sel_registerName(name.encode())


def find_and_load(name: str): return ctypes.CDLL(dyld_find(name))


class MTLResourceOptions:
    MTLResourceCPUCacheModeDefaultCache = 0
    MTLResourceStorageModeShared = 0 << 4


class MTLPipelineOption:
    MTLPipelineOptionNone = 0


libobjc = find_and_load("/usr/lib/libobjc.dylib")
libmetal = find_and_load("/Library/Frameworks/Metal.framework/Metal")
# Must be loaded for default Metal Device: https://developer.apple.com/documentation/metal/1433401-mtlcreatesystemdefaultdevice?language=objc
find_and_load("/Library/Frameworks/CoreGraphics.framework/CoreGraphics")
# libdispatch is part of libSystem on mac
libdispatch = find_and_load("/usr/lib/libSystem.dylib")
libobjc.objc_getClass.restype = objc_id
libobjc.sel_registerName.restype = objc_id
libmetal.MTLCreateSystemDefaultDevice.restype = objc_instance
libdispatch.dispatch_data_create.restype = objc_instance

T = TypeVar("T")
# Ignore mypy error reporting incompatible default, because typevar default only works on python 3.12


# type: ignore [assignment]
def msg(ptr: objc_id, selector: str, /, *args: Any, restype: type[T] = objc_id) -> T:
    # Using attribute access returns a new reference so setting restype is safe
    sender = libobjc["objc_msgSend"]
    sender.restype = restype
    return sender(ptr, sel(selector), *args)


def to_ns_str(s: str): return msg(libobjc.objc_getClass(b"NSString"),
                                  "stringWithUTF8String:", s.encode(), restype=objc_instance)


# Here's the fixed example by calling the dyld runtime directly
src = """#include <metal_stdlib>
using namespace metal;
kernel void r_5(device int* data0, const device int* data1, uint3 gid [[threadgroup_position_in_grid]], uint3 lid [[thread_position_in_threadgroup]]) {
  int acc0 = -2147483648;
  int val0 = *(data1+0);
  int val1 = *(data1+1);
  int val2 = *(data1+2);
  int val3 = *(data1+3);
  int val4 = *(data1+4);
  int alu0 = max(((val0+1)*2*val0),0);
  int alu1 = max(((val1+1)*2*val1),0);
  int alu2 = max(((val2+1)*2*val2),0);
  int alu3 = max(((val3+1)*2*val3),0);
  int alu4 = max(((val4+1)*2*val4),0);
  int alu5 = max(alu0,acc0);
  int alu6 = max(alu1,alu5);
  int alu7 = max(alu2,alu6);
  int alu8 = max(alu3,alu7);
  int alu9 = max(alu4,alu8);
  *(data0+0) = alu9;
}"""


def get_err_str(err):
    if err.value is None:
        print("Error is None")
        return
    return bytes(msg(msg(err, "localizedDescription", restype=objc_instance),
                     "UTF8String", restype=ctypes.c_char_p)).decode()


options = msg(libobjc.objc_getClass(b"MTLCompileOptions"),
              "new", restype=objc_instance)

device = libmetal.MTLCreateSystemDefaultDevice()

compileError = objc_instance(0)
library = msg(device, "newLibraryWithSource:options:error:", to_ns_str(src),
              options, ctypes.byref(compileError), restype=objc_instance)
if library.value is None:
    print("library compile failed")
    print("reason:", get_err_str(compileError))
    exit(1)

library_contents = msg(library, "libraryDataContents", restype=objc_instance)
objc_returned_len = msg(library_contents, "length", restype=objc_instance)
print(f"{objc_returned_len.value=}")
lib_bytes = ctypes.string_at(msg(library_contents, "bytes"), cast(
    int, objc_returned_len.value))

print("lib len", len(lib_bytes))
name = "r_5"
data = libdispatch.dispatch_data_create(lib_bytes, len(lib_bytes), None, None)

newLibError = objc_instance(0)
library2 = msg(device, "newLibraryWithData:error:", data,
               ctypes.byref(newLibError), restype=objc_instance)

if library2.value is None:
    print("Library creation failed")
    print("reason:", get_err_str(newLibError))
    exit(1)

fxn = msg(library2, "newFunctionWithName:",
          to_ns_str(name), restype=objc_instance)
descriptor = msg(libobjc.objc_getClass(
    b"MTLComputePipelineDescriptor"), "new", restype=objc_instance)

msg(descriptor, "setComputeFunction:", fxn)
msg(descriptor, "setSupportIndirectCommandBuffers:", True)

newComputePipelineError = objc_instance(0)
pipeline_state = msg(device, "newComputePipelineStateWithDescriptor:options:reflection:error:",
                     descriptor, MTLPipelineOption.MTLPipelineOptionNone, None, ctypes.byref(newComputePipelineError), restype=objc_instance)
if pipeline_state.value is None:
    print("pipeline creation failed")
    print("reason:", get_err_str(newComputePipelineError))
    exit(1)
