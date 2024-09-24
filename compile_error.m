/*
 * To compile objective-c on the command line:
 *
 * gcc -framework Foundation objc-gcc.m
 * clang -framework CoreGraphics -framework Foundation -framework Metal compile_error.m -o compile_error && ./compile_error
 *
 * You may have to link with -lobjc or other libs,
 * as required.
 */

#import <Foundation/Foundation.h>
#import <Metal/Metal.h>
#import <CoreGraphics/CoreGraphics.h>

int main(int argc, char** argv)
{
        id<MTLDevice> device = MTLCreateSystemDefaultDevice();
        id<MTLCommandQueue> commandQueue = [device newCommandQueue];
        NSError* compileError;
        MTLCompileOptions* compileOptions = [MTLCompileOptions new];
        id<MTLLibrary> library = [device newLibraryWithSource:
@"#include <metal_stdlib>\n"
"using namespace metal;\n"
"kernel void r_5(device int* data0, const device int* data1, uint3 gid [[threadgroup_position_in_grid]], uint3 lid [[thread_position_in_threadgroup]]) {\n"
"  int acc0 = -2147483648;\n"
"  int val0 = *(data1+0);\n"
"  int val1 = *(data1+1);\n"
"  int val2 = *(data1+2);\n"
"  int val3 = *(data1+3);\n"
"  int val4 = *(data1+4);\n"
"  int alu0 = max(((val0+1)*2*val0),0);\n"
"  int alu1 = max(((val1+1)*2*val1),0);\n"
"  int alu2 = max(((val2+1)*2*val2),0);\n"
"  int alu3 = max(((val3+1)*2*val3),0);\n"
"  int alu4 = max(((val4+1)*2*val4),0);\n"
"  int alu5 = max(alu0,acc0);\n"
"  int alu6 = max(alu1,alu5);\n"
"  int alu7 = max(alu2,alu6);\n"
"  int alu8 = max(alu3,alu7);\n"
"  int alu9 = max(alu4,alu8);\n"
"  *(data0+0) = alu9;\n"
"}\n"
         options: compileOptions error: nil];


        NSData *libraryDataContents = [(id)library libraryDataContents];
        printf("libraryDataContents: %p\n", libraryDataContents);
        NSUInteger length = [libraryDataContents length];
        printf("length: %d\n", length);
        char *name = object_getClassName(libraryDataContents);
        printf("name: %s\n", name);
        return 0;
        id<MTLFunction> kernelFunction = [library newFunctionWithName:@"add"];
        NSError *error = NULL;
        [commandQueue commandBuffer];
        id<MTLCommandBuffer> commandBuffer = [commandQueue commandBuffer];
        id<MTLComputeCommandEncoder> encoder = [commandBuffer computeCommandEncoder];
        [encoder setComputePipelineState:[device newComputePipelineStateWithFunction:kernelFunction error:&error]];
        float input[] = {1,2};
        NSInteger dataSize = sizeof(input);
        
        [encoder setBuffer:[device newBufferWithBytes:input length:dataSize options:0]
                    offset:0
                   atIndex:0];
        
        id<MTLBuffer> outputBuffer = [device newBufferWithLength:sizeof(float) options:0];
        [encoder setBuffer:outputBuffer offset:0 atIndex:1];
        MTLSize numThreadgroups = {1,1,1};
        MTLSize numgroups = {1,1,1};
        [encoder dispatchThreadgroups:numThreadgroups threadsPerThreadgroup:numgroups];
        [encoder endEncoding];
        [commandBuffer commit];
        [commandBuffer waitUntilCompleted];
        float *output = [outputBuffer contents];
        printf("result = %f\n", output[0]);
}