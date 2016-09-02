LIBS := $(pkg-config --libs --cflags libczmq)

foo:
	echo ${MY_OS}


ifeq ($(OS),Darwin)
	MY_OS="Darwin"
	echo "yay Darwin"
endif
ifeq ($(OS),Linux)
	MY_OS="Linux"
	echo "yay Linux"
else
	echo "boo" $(OS)
endif


# # TODO: Make this portable. Atm this Makefile will likely only work on my
# #       machine due to the INCLUDES and LIBS below. The resolution will
# #       likely be to include a list of libs and headers that must be
# #       installed. Getting that to work on various Linux distributions
# #       should be straightforward; Windows will be another matter.

# CC=gcc
# LD=gcc
# INCLUDES=-I./include \
# 	-I/usr/local/Cellar/zeromq/HEAD/include
# # INCLUDES=-I/Users/j/Development/emacs/src \
# # 	 -I/usr/local/Cellar/zeromq/HEAD/include
# LIBS=-lzmq \
#      -L/usr/local/Cellar/zeromq/HEAD/lib/ \
#      -L/usr/local/lib/
# WFLAGS=-Wall -Werror -std=gnu99
# SRCDIR=./src
# OUTDIR=./lib
# O_FILE=$(OUTDIR)/zmq_module.o
# SO_FILE=$(OUTDIR)/libzmq_module.so

# zmq_module:
# 	mkdir $(OUTDIR)
# 	$(CC) -c $(INCLUDES) $(WFLAGS) -fpic -o $(O_FILE) $(SRCDIR)/zmq_module.c
# 	$(LD) $(INCLUDES) $(LIBS) -shared -o $(SO_FILE) $(O_FILE)

# zm:  zmq_module # shorter alias

# clean:
# 	rm -rf $(OUTDIR)/

# # TODO: Might be useful for unit and performance testing
# # test:
# # 	$(EMACS) -Q -batch -L . $(LOADPATH) \
# # 		-l test/test.el \
# # 		-f ert-run-tests-batch-and-exit

# # (load "/Users/j/Documents/TUDelft/MSc/thesis/prototypes/monto-mode/module/libzmq_module.so")
