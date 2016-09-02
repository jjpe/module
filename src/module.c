#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <czmq.h>
#include "../include/emacs-module.h"

// This states that the module is GPL-compliant.
// Emacs won't load the module if this symbol is undefined.
int plugin_is_GPL_compatible = 0;


// Module entry point
int emacs_module_init(struct emacs_runtime *ert) {

    return 0;
}

/*  LocalWords:  czmq
 */
