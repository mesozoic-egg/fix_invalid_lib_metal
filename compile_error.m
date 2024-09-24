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
        NSError* compileError;
        MTLCompileOptions* compileOptions = [MTLCompileOptions new];
        NSString* source = @"#include <metal_stdlib>\nkernel void r_5(device int* data0, const device int* data1, uint3 gid [[threadgroup_position_in_grid]], uint3 lid [[thread_position_in_threadgroup]]) {data0[0] = 0;}";
        NSUInteger sourcelength = [source length];
        printf("sourcelength: %d\n", sourcelength);
        id<MTLLibrary> library = [device newLibraryWithSource: source
         options: compileOptions error: nil];


        NSData *libraryDataContents = [(id)library libraryDataContents];
        printf("libraryDataContents: %p\n", libraryDataContents);
        NSUInteger length = [libraryDataContents length];
        printf("length: %d\n", length);

        const void* rawbytes = [libraryDataContents bytes];
        dispatch_data_t data = dispatch_data_create(rawbytes, length, NULL, nil);
        printf("data: %p\n", data);
        NSError* _error = nil;
        id<MTLLibrary> library2 = [device newLibraryWithData:data error: _error];
        printf("library2: %p\n", library2);
        printf("error: %p\n", _error);
        id<MTLFunction> kernelFunction = [library newFunctionWithName:@"add"];
        printf("kernelFunction: %p\n", kernelFunction);
        return 0;
}