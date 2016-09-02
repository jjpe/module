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
    shutil.rmtree(out_dir)
    print('[build] Cleaned output dir', out_dir)


def compile_file(src_file,
                 obj_file,
                 cc           = 'gcc',
                 include_dirs = include_dirs(),
                 warn_flags   = '-Wall -Werror'):
    cc_cmd = '{CC} -c {INCLUDES} {CFLAGS} -o {OBJ} {SRC}'.format(
        CC       = cc,
        INCLUDES = include_dirs,
        CFLAGS   = warn_flags + ' -std=gnu99 -fpic',
        OBJ      = obj_file,
        SRC      = src_file)
    print('[build] Compiling:\n{}\n'.format(cc_cmd))
    os.system(cc_cmd)

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
    print('[build] Linking dynamically:\n{}\n'.format(ld_cmd))
    os.system(ld_cmd)

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
        print('[build] Linking statically:\n{}\n'.format(ld_cmd))
        os.system(ld_cmd)

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
        compile_file(src_file, obj_file)
        link_dynamic(obj_file, so_file)
        link_static(obj_file, so_file)

if __name__ == "__main__":
    main()





































































































# def zeromq_install_dir_osx(subfile):
#     zeromq_info = subprocess.Popen(
#             ['brew', 'info', 'zeromq'],
#             stdout=subprocess.PIPE,
#             stderr=subprocess.PIPE).communicate()[0]
#     lines = [x for x in str(zeromq_info).split('\\n') if x.startswith('/')]
#     line = lines[0]
#     zeromq_dir = line.split(' (')[0]
#     return path.join(zeromq_dir, subfile)

# def zeromq_install_dir_linux(subfile):
#     pass

# def zeromq_install_dir(subfile):
#     os = platform.system()
#     if   os == 'Darwin': return zeromq_install_dir_osx(subfile)
#     elif os == 'Linux':  return zeromq_install_dir_linux(subfile)
#     else: raise Exception("OS '{}' is not supported".format(os))

# INCLUDE_DIRS_OSX =   ['./include/', zeromq_install_dir('include/')]
# INCLUDE_DIRS_LINUX = ['/usr/include/', './include/']

# LIB_DIRS_OSX =   ['/usr/local/lib/', zeromq_install_dir('lib/')]
# LIB_DIRS_LINUX = ['/usr/lib/x86_64-linux-gnu/']

# LIBS_OSX =   ['zmq']
# LIBS_LINUX = ['zmq']

# SUPPORTED_OSES = ['Darwin', 'Linux']

# def get_include_dirs(os):
#     if   os == 'Darwin': return ['-I' + d for d in INCLUDE_DIRS_OSX]
#     elif os == 'Linux':  return ['-I' + d for d in INCLUDE_DIRS_LINUX]
#     else: raise Exception("OS '{}' is not supported".format(os))

# def get_lib_dirs(os):
#     if   os == 'Darwin': return ['-L' + d for d in LIB_DIRS_OSX]
#     elif os == 'Linux':  return ['-L' + d for d in LIB_DIRS_LINUX]
#     else: raise Exception("OS '{}' is not supported".format(os))

# def get_libs(os):
#     if   os == 'Darwin': return ['-l' + l for l in LIBS_OSX]
#     elif os == 'Linux':  return ['-l' + l for l in LIBS_LINUX]
#     else: raise Exception("OS '{}' is not supported".format(os))

# def clean(out_dir):
#     import shutil
#     shutil.rmtree(out_dir)
#     print('Cleaned', out_dir)

# def build_zmq_module(cc,
#                      ld,
#                      include_dirs,
#                      libs,
#                      lib_dirs,
#                      out_dir,
#                      o_file,
#                      so_file,
#                      src_file):
#     warn_flags = '-Wall -Werror -std=gnu99'
#     if not path.exists(out_dir):
#         os.mkdir(out_dir)
#         print('Created', out_dir)
#     cc_cmd = '{CC} -c {INCS} {W} -fpic -o {OF} {SRC}'.format(
#         CC=cc, INCS=include_dirs, W=warn_flags, OF=o_file, SRC=src_file)
#     print(cc_cmd)
#     os.system(cc_cmd)
#     ld_cmd = '{LD} {INCS} {LIBS} {LIB_DIRS} -shared -o {SOF} {OF}'.format(
#         LD=ld,
#         INCS=include_dirs,
#         LIBS=libs,
#         LIB_DIRS=lib_dirs,
#         SOF=so_file,
#         OF=o_file)
#     print(ld_cmd)
#     os.system(ld_cmd)

# def parse_cli_args():
#     parser = argparse.ArgumentParser(description='Build the C module.')
#     parser.add_argument('-c', '--clean', action='store_true',
#                         help='Clean the project.')
#     parser.add_argument('-b', '--build', action='store_true', default=True,
#                         help='Build the project.')
#     return parser.parse_args()

# def main():
#     os = platform.system()
#     if os not in SUPPORTED_OSES:
#         print("OS '{}' is not supported.".format(os))
#         exit(-1)
#     ld = cc = 'gcc'
#     include_dirs = ' '.join(get_include_dirs(os))
#     libs = ' '.join(get_libs(os))
#     lib_dirs = ' '.join(get_lib_dirs(os))
#     src_dir = 'src/'
#     out_dir = 'lib/'
#     src_file = path.join(src_dir, 'zmq_module.c')
#     o_file =  path.join(out_dir, 'zmq_module.o')
#     so_file = path.join(out_dir, 'libzmq_module.so')

#     cli_args = parse_cli_args()
#     if cli_args.clean == True:
#         clean(out_dir)
#     if cli_args.build == True:
#         print("Building module for {}".format(os))
#         build_zmq_module(cc,
#                          ld,
#                          include_dirs,
#                          libs,
#                          lib_dirs,
#                          out_dir,
#                          o_file,
#                          so_filen,
#                          src_file)

# main()

#  LocalWords:  usr zeromq returncode cflags DIRS LDFLAGS LD Werror
#  LocalWords:  fpic dirs
