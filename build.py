#!/usr/bin/env python3

# NOTE: The references to Linux below are specifically to Ubuntu.
# So the whole Debian family is likely to work, but e.g. Fedora might
# be problematic with the code as it is.

import os
import os.path as path
import platform
import subprocess
import sys
import argparse
import shutil

DARWIN = 'Darwin'
LINUX =  'Linux'

SUPPORTED_OSES = [
    DARWIN,
    # LINUX,   # TODO: Ubuntu has issues with locating libzmq/libczmq
               #       using pkg-config: it only shows -l args.
               #       Somehow that needs to be fixed.
]

def execute(cmd, *args):
    '''Execute a shell command with arguments. Return a map containing the keys:
* "rc":  The return code as a number
* "out": The captured output of the execution as a str
* "err": The captured error output of the execution as a str'''
    completed_proc = subprocess.run(
        [cmd] + list(args),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    return {
        'rc':  completed_proc.returncode,
        'out': completed_proc.stdout.decode().strip(),
        'err': completed_proc.stderr.decode().strip(),
    }

def libs():
    dependencies = ['libzmq', 'libczmq']
    return execute('pkg-config', '--libs-only-l', *dependencies)['out']

def lib_dirs():
    dependencies = ['libzmq', 'libczmq']
    return execute('pkg-config', '--libs-only-L', *dependencies)['out']

def include_dirs():
    dependencies = ['libzmq', 'libczmq']
    return execute('pkg-config', '--cflags-only-I', *dependencies)['out']

def clean(out_dir):
    if path.exists(out_dir) and path.isdir(out_dir):
        shutil.rmtree(out_dir)
        print('[build] Cleaned output directory', out_dir)

def compile_file(src_file,
                 obj_file,
                 cc           = 'gcc',
                 include_dirs = include_dirs(),
                 warn_flags   = '-Wall -Werror'):
    # The -c is to prevent the linker from running.
    cc_cmd = '{CC} -c {INCLUDES} {CFLAGS} -o {OBJ} {SRC}'.format(
        CC       = cc,
        INCLUDES = include_dirs,
        CFLAGS   = warn_flags + ' -std=gnu99 -fpic',
        OBJ      = obj_file,
        SRC      = src_file)
    print('[build] Compiling:\n{}'.format(cc_cmd))
    os.system(cc_cmd)
    print()

def link_dynamic(obj_file,
                 so_file,
                 ld           = 'gcc',
                 include_dirs = include_dirs(),
                 libs         = libs(),
                 lib_dirs     = lib_dirs()):
    ldflags = '-shared'
    ld_cmd = '{LD} {INCLS} {LIBS} {LIB_DIRS} {LDFLAGS} -o {SO} {OBJ}'.format(
        LD       = ld,
        INCLS    = include_dirs,
        LIBS     = libs,
        LIB_DIRS = lib_dirs,
        LDFLAGS  = ldflags,
        SO       = so_file,
        OBJ      = obj_file)
    print('[build] Linking dynamically:\n{}'.format(ld_cmd))
    os.system(ld_cmd)
    print()

def link_static(obj_file,
                so_file,
                ld           = 'gcc',
                include_dirs = include_dirs(),
                libs         = libs(),
                lib_dirs     = lib_dirs()):
    # Static linking apparently is not supported on OS X, see
    #   https://github.com/crosstool-ng/crosstool-ng/issues/31#issuecomment-71333176
    # and
    #   https://stackoverflow.com/questions/5259249/creating-static-mac-os-x-c-build
    OS = platform.system()
    if OS not in [DARWIN]:
        ldflags = '-static'
        ld_cmd = '{LD} {INCLS} {LIBS} {LIB_DIRS} {LDFLAGS} -o {SO} {OBJ}'.format(
            LD       = ld,
            INCLS    = include_dirs,
            LIBS     = libs,
            LIB_DIRS = lib_dirs,
            LDFLAGS  = ldflags,
            SO       = so_file,
            OBJ      = obj_file)
        print('[build] Linking statically:\n{}'.format(ld_cmd))
        os.system(ld_cmd)
        print()

def parse_cli_args():
    parser = argparse.ArgumentParser(description='Build the C module.')
    parser.add_argument('-c', '--clean', action='store_true',
                        help='Clean the project.')
    parser.add_argument('-b', '--build', action='store_true', default=True,
                        help='Build the project.')
    return parser.parse_args()

def main():
    OS = platform.system()
    if OS not in SUPPORTED_OSES:
        print("OS '{}' is not supported.".format(OS))
        exit(-1)
    src_file = path.abspath('src/module.c')
    out_dir =  path.abspath('target/')
    obj_file = path.join(out_dir, 'module.o')
    # Emacs expects the dylib to have an '.so' extension, even on OS X:
    so_file =  path.join(out_dir, 'module.so')

    print("[build] src_file: ", src_file)
    print("[build] out_dir:  ", out_dir)
    print("[build] obj_file: ", obj_file)
    print("[build] so_file:  ", so_file)

    args = parse_cli_args()
    if args.clean:
        clean(out_dir)
    if args.build:
        if not path.exists(out_dir):
            print("[build] Created output directory", out_dir)
            os.mkdir(out_dir)
        compile_file(src_file, obj_file)
        link_dynamic(obj_file, so_file)
        link_static(obj_file, so_file)

if __name__ == "__main__":
    main()

#  LocalWords:  usr zeromq returncode cflags DIRS LDFLAGS LD Werror
#  LocalWords:  fpic dirs
