"""
Reproduced on M2 macOS 14 

$ uname -a
Darwin pg20.local 23.6.0 Darwin Kernel Version 23.6.0: Mon Jul 29 21:16:46 PDT 2024; root:xnu-10063.141.2~1/RELEASE_ARM64_T8112 arm64

$ python --version
Python 3.10.0

$ python invalid_lib_reproduce.py

options=<MTLCompileOptionsInternal: 0x60000185c200>
    preprocessorMacros:  
    fastMathEnabled = 1 
    framebufferReadEnabled = 0 
    preserveInvariance = 0 
    optimizationLevel = MTLLibraryOptimizationLevelDefault 
    libraryType = MTLLibraryTypeExecutable 
    installName = <null> 
    compileSymbolVisibility =  0 
    allowReferencingUndefinedSymbols =  0 
    maxTotalThreadsPerThreadgroup =  0 
    languageVersion = default
options.libraryType=<native-selector libraryType of <MTLCompileOptionsInternal: 0x60000185c200>
    preprocessorMacros:  
    fastMathEnabled = 1 
    framebufferReadEnabled = 0 
    preserveInvariance = 0 
    optimizationLevel = MTLLibraryOptimizationLevelDefault 
    libraryType = MTLLibraryTypeExecutable 
    installName = <null> 
    compileSymbolVisibility =  0 
    allowReferencingUndefinedSymbols =  0 
    maxTotalThreadsPerThreadgroup =  0 
    languageVersion = default>
Traceback (most recent call last):
  File "/Users/mac/py310/tinygrad/tmp/compile_error.py", line 49, in <module>
    library = unwrap2(device.newLibraryWithData_error_(data, None))
  File "/Users/mac/py310/tinygrad/tmp/compile_error.py", line 38, in unwrap2
    assert err is None, str(err)
AssertionError: Error Domain=MTLLibraryErrorDomain Code=1 "Invalid library file" UserInfo={NSLocalizedDescription=Invalid library file}
"""

import Metal, libdispatch

prg="""#include <metal_stdlib>
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



options = Metal.MTLCompileOptions.new()

print(f"{options=}")
print(f"{options.libraryType=}")
compiler = Metal.MTLCreateSystemDefaultDevice()

def unwrap2(x):
  ret, err = x
  assert err is None, str(err)
  return ret

r = compiler.newLibraryWithSource_options_error_(prg, options, None)
library = unwrap2(r)
lib = library.libraryDataContents().bytes().tobytes()

device = compiler

#### 
data = libdispatch.dispatch_data_create(lib, len(lib), None, None)
library = unwrap2(device.newLibraryWithData_error_(data, None))
fxn = library.newFunctionWithName_("r_5")
pipeline_state = unwrap2(device.newComputePipelineStateWithFunction_error_(fxn, None))