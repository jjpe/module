////////////////////////////////////////////////////////////////////////////////
//  This module is a very basic Elisp FFI bridge to ZMQ functionality.        //
//  However it could easily be expanded to the the entire ZMQ API.            //
//  What it DOES allow for is sending and receiving arbitrarily               //
//  large strings natively over ZMQ, with low latencies.                      //
//                                                                            //
//  As the symbol above already hints at, this entire Emacs module is         //
//  compatible with the GNU GPLv3. This symbol, and the licensing it          //
//  implies, are requirements that must be met before Emacs will load         //
//  the module.                                                               //
//                                                                            //
// Copyright, Joey Ezechiëls, September 2016                                  //
////////////////////////////////////////////////////////////////////////////////

#include <assert.h>
#include <stdio.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#include <czmq.h>
#include "../include/emacs-module.h"

// This symbol states that the module is GPL-compliant.
// Emacs won't load the module if it is not declared.
int plugin_is_GPL_compatible;

////////////////////////////////////////////////////////////////////////////////
//  Convenience macros to allow the C code in this file to easily call a      //
//  small subset of Elisp functionality.                                      //
//  NOTE: These macros assume an (emacs_env *) pointer called 'env' is        //
//  initialized and in scope.                                                 //
////////////////////////////////////////////////////////////////////////////////
/* Intern a symbol based on the given name. */
#define SYM(name)  env->intern(env, name)

/* Create an Elisp integer */
#define INT(value)  env->make_integer(env, value)

/* Create an Elisp string */
#define STR(s, len)  env->make_string(env, s, len)

/* Compare 2 ELisp atoms */
#define EQ(item0, item1)  env->eq(env, item0, item1)

/* Call an ELisp fn. The args argument must be of type emacs_value[]. */
#define CALL(fn_name, nargs, args)                                       \
    env->funcall(env, SYM(fn_name), nargs, args);

/* define a function.
lsym: a string representing the elisp fn name
csym: the name of the c function to be called
amin: the minimal number of args the fn accepts
amax: the maximal number of args the fn accepts
doc:  a docstring
data: ?? WTF is this ??
 */
#define DEFUN(lsym, csym, amin, amax, doc, data) ({                     \
            emacs_value args[] = {                                      \
                SYM(lsym),                                              \
                env->make_function(env, amin, amax, csym, doc, data)    \
            };                                                          \
            CALL("fset", 2, args);                                      \
        })

/* define a function.
lsym: a string representing the elisp fn name
csym: the name of the c function to be called
amin: the minimal number of args the fn accepts
amax: the maximal number of args the fn accepts
doc:  a docstring  */
#define DEFN(lsym, csym, amin, amax, doc)                               \
    DEFUN(lsym, csym, amin, amax, doc, NULL)

#define MESSAGE(msg_literal) ({                                         \
            char *s = msg_literal;                                      \
            emacs_value args[] = { STR(s, strlen(s)) };                 \
            CALL("message", 1, args);                                   \
        })

/* #define FMT(fmt, fmtargs...) ({                                         \ */
/*             char s[6 KiB]; /\* TODO: Might be too small sometimes *\/     \ */
/*             int slen = sprintf(s, fmt, fmtargs);                        \ */
/*             emacs_value args[] = { STR(s, slen) };                      \ */
/*             CALL("message", 1, args);                                   \ */
/*         }) */

/* #define ZMQ_ERR_DIAG() ({                                               \ */
/*             FMT("errno == eagain:   %d", (errno == EAGAIN));            \ */
/*             FMT("errno == enotsup:  %d", (errno == ENOTSUP));           \ */
/*             FMT("errno == efsm:     %d", (errno == EFSM));              \ */
/*             FMT("errno == eterm:    %d", (errno == ETERM));             \ */
/*             FMT("errno == enotsock: %d", (errno == ENOTSOCK));          \ */
/*             FMT("errno == eintr:    %d", (errno == EINTR));             \ */
/*         }) */

/* #define RETURN_ZMQ_ERROR_KW() ({                                        \ */
/*             switch(errno) {                                             \ */
/*             case EAGAIN:    return SYM(":EAGAIN");                      \ */
/*             case ENOTSUP:   return SYM(":ENOTSUP");                     \ */
/*             case EFSM:      return SYM(":EFSM");                        \ */
/*             case ETERM:     return SYM(":ETERM");                       \ */
/*             case ENOTSOCK:  return SYM(":ENOTSOCK");                    \ */
/*             case EINTR:     return SYM(":EINTR");                       \ */
/*             default:        return SYM(":unknown-error");               \ */
/*             }                                                           \ */
/*         }) */

/* macro to provide a feature to emacs. */
#define PROVIDE(feature) ({                                             \
            emacs_value args[] = { SYM(feature) };                      \
            CALL("provide", 1, args);                                   \
        })

// Invalid marker for ZMQ constants
#define ZMQ_INVALID -1

////////////////////////////////////////////////////////////////////////////////
//  ZMQ socket types                                                          //
////////////////////////////////////////////////////////////////////////////////
#define ZMQ_PAIR     0
#define ZMQ_PUB      1
#define ZMQ_SUB      2
#define ZMQ_REQ      3
#define ZMQ_REP      4
#define ZMQ_DEALER   5
#define ZMQ_ROUTER   6
#define ZMQ_PULL     7
#define ZMQ_PUSH     8
#define ZMQ_XPUB     9
#define ZMQ_XSUB    10
#define ZMQ_STREAM  11

bool socket_type_valid(int socket_type) {
    return ZMQ_PAIR <= socket_type && socket_type <= ZMQ_STREAM;
}

emacs_value socket_type_to_elisp(emacs_env *env, int socket_type) {
    assert(socket_type_valid(socket_type));
    switch(socket_type) {
    case ZMQ_PAIR:    return SYM(":zmq-pair");
    case ZMQ_PUB:     return SYM(":zmq-pub");
    case ZMQ_SUB:     return SYM(":zmq-sub");
    case ZMQ_REQ:     return SYM(":zmq-req");
    case ZMQ_REP:     return SYM(":zmq-rep");
    case ZMQ_DEALER:  return SYM(":zmq-dealer");
    case ZMQ_ROUTER:  return SYM(":zmq-router");
    case ZMQ_PULL:    return SYM(":zmq-pull");
    case ZMQ_PUSH:    return SYM(":zmq-push");
    case ZMQ_XPUB:    return SYM(":zmq-xpub");
    case ZMQ_XSUB:    return SYM(":zmq-xsub");
    case ZMQ_STREAM:  return SYM(":zmq-stream");
    default:          return SYM(":unkown-socket-type");
    }
}

intmax_t socket_type_to_c(emacs_env *env, emacs_value socket_type_kw) {
    if      (EQ(socket_type_kw, SYM(":zmq-pair")))   return ZMQ_PAIR;
    else if (EQ(socket_type_kw, SYM(":zmq-pub")))    return ZMQ_PUB;
    else if (EQ(socket_type_kw, SYM(":zmq-sub")))    return ZMQ_SUB;
    else if (EQ(socket_type_kw, SYM(":zmq-req")))    return ZMQ_REQ;
    else if (EQ(socket_type_kw, SYM(":zmq-rep")))    return ZMQ_REP;
    else if (EQ(socket_type_kw, SYM(":zmq-dealer"))) return ZMQ_DEALER;
    else if (EQ(socket_type_kw, SYM(":zmq-router"))) return ZMQ_ROUTER;
    else if (EQ(socket_type_kw, SYM(":zmq-pull")))   return ZMQ_PULL;
    else if (EQ(socket_type_kw, SYM(":zmq-push")))   return ZMQ_PUSH;
    else if (EQ(socket_type_kw, SYM(":zmq-xpub")))   return ZMQ_XPUB;
    else if (EQ(socket_type_kw, SYM(":zmq-xsub")))   return ZMQ_XSUB;
    else if (EQ(socket_type_kw, SYM(":zmq-stream"))) return ZMQ_STREAM;
    else                                             return ZMQ_INVALID;
}

////////////////////////////////////////////////////////////////////////////////
//  Emacs subrs                                                               //
////////////////////////////////////////////////////////////////////////////////
static emacs_value Fzmq_new_socket(emacs_env *env,
                                   ptrdiff_t nargs,
                                   emacs_value args[],
                                   void *data) {
    assert(nargs == 1);
    if (!args[0]) { return SYM("nil"); /* TODO: Handle error */ }

    const intmax_t socket_type = socket_type_to_c(env, args[0]);
    zsock_t *socket = zsock_new(socket_type);
    if (!socket) { return SYM("nil"); /* TODO: Handle error */ }

    MESSAGE("[spoofax module] Created socket");
    return env->make_user_ptr(env, (void (*)(void *))zsock_destroy, socket);
}

static emacs_value Fzmq_destroy_socket(emacs_env *env,
                                       ptrdiff_t nargs,
                                       emacs_value args[],
                                       void *data) {
    assert(nargs == 1);
    if (!args[0]) { return SYM("nil"); /* TODO: Handle error */ }

    zsock_t *socket = env->get_user_ptr(env, args[0]);
    if (!socket) { return SYM("nil"); /* TODO: Handle error */ }

    zsock_destroy(&socket);
    MESSAGE("[spoofax module] Destroyed socket");
    return SYM("t");
}

static emacs_value Fzmq_connect(emacs_env *env,
                                ptrdiff_t nargs,
                                emacs_value args[],
                                void *data) {
    assert(nargs == 2);
    if (!args[0]) { return SYM("nil"); /* TODO: Handle error */ }
    if (!args[1]) { return SYM("nil"); /* TODO: Handle error */ }

    zsock_t *socket = env->get_user_ptr(env, args[0]);
    if (!socket) { return SYM("nil"); /* TODO: Handle error */ }

    // Get the necessary buffer length:
    ptrdiff_t addrlen = 0;
    env->copy_string_contents(env, args[1], NULL, &addrlen);

    bool ok;
    char address[addrlen];

    // Copy the string:
    ok = env->copy_string_contents(env, args[1], address, &addrlen);
    if (!ok) { return SYM("nil"); /* TODO: Handle error */}

    // Connect the socket
    ok = 0 == zsock_connect(socket, "%s", address);
    if (!ok) { return SYM("nil"); /* TODO: Handle error */ }

    MESSAGE("[spoofax module] Connected socket");
    return SYM("t");
}

static emacs_value Fzmq_disconnect(emacs_env *env,
                                   ptrdiff_t nargs,
                                   emacs_value args[],
                                   void *data) {
    assert(nargs == 2);
    if (!args[0]) { return SYM("nil"); /* TODO: Handle error */ }
    if (!args[1]) { return SYM("nil"); /* TODO: Handle error */ }

    zsock_t *socket = env->get_user_ptr(env, args[0]);
    if (!socket) { /* TODO: Handle error */ }

    // Get the necessary buffer length:
    ptrdiff_t addrlen = 0;
    env->copy_string_contents(env, args[1], NULL, &addrlen);

    bool ok;
    char address[addrlen];

    // Copy the string:
    ok = env->copy_string_contents(env, args[1], address, &addrlen);
    if (!ok) { return SYM("nil"); /* TODO: Handle error */ }

    // Disconnect the socket
    ok = 0 == zsock_disconnect(socket, "%s", address);
    if (!ok) { return SYM("nil"); /* TODO: Handle error */ }

    MESSAGE("[spoofax module] Disconnected socket");
    return SYM("t");
}

static emacs_value Fzmq_send(emacs_env *env,
                             ptrdiff_t nargs,
                             emacs_value args[],
                             void *data) {
    assert(nargs == 2);
    if (!args[0]) { return SYM("nil"); /* TODO: Handle error */ }
    if (!args[1]) { return SYM("nil"); /* TODO: Handle error */ }

    zsock_t *socket = env->get_user_ptr(env, args[0]);
    if (!socket) { /* TODO: Handle error */ }

    // Get the necessary buffer length
    ptrdiff_t buflen = 0;
    env->copy_string_contents(env, args[1], NULL, &buflen);

    bool ok;
    char buf[buflen];

    // Copy the string
    ok = env->copy_string_contents(env, args[1], buf, &buflen);
    if (!ok) { return SYM("nil"); /* TODO: Handle error */ }

    // Send the string
    ok = zstr_send(socket, buf);
    if (!ok) { return SYM("nil"); /* TODO: Handle error */ }

    MESSAGE("[spoofax module] Sent message");
    return SYM("t");
}

static emacs_value Fzmq_receive(emacs_env *env,
                                ptrdiff_t nargs,
                                emacs_value args[],
                                void *data) {
    assert(nargs == 1);
    if (!args[0]) { return SYM("nil"); /* TODO: Handle error */ }

    zsock_t *socket = env->get_user_ptr(env, args[0]);
    if (!socket) { return SYM("nil"); /* TODO: Handle error */ }

    // Receive the string
    char *string = zstr_recv(socket);

    // Copy the string to Elisp
    emacs_value emacs_string = env->make_string(env, string, strlen(string));

    zstr_free(&string);
    MESSAGE("[spoofax module] Received message");
    return emacs_string;
}



// Module entry point
int emacs_module_init(struct emacs_runtime *ert) {
    emacs_env *env = ert->get_environment(ert);

    DEFN("spoofax-module/new-socket",         Fzmq_new_socket,          1, 1,
         "(SOCKET-TYPE)\n\n\
Create a new ZMQ socket of a given socket type, specified by a keyword.\n\
Valid socket types are in {:zmq-pair, :zmq-pub, :zmq-sub, :zmq-req,\n\
:zmq-rep, :zmq-dealer, :zmq-router, :zmq-pull, :zmq-push, :zmq-xpub,\n\
:zmq-xsub, :zmq-stream}.");
    DEFN("spoofax-module/destroy-socket",     Fzmq_destroy_socket,      1, 1,
         "(SOCKET)\n\n\
Destroy an existing ZMQ socket.");

    DEFN("spoofax-module/connect",            Fzmq_connect,             2, 2,
         "(SOCKET ADDRESS)\n\n\
Connect a socket to an endpoint.");
    DEFN("spoofax-module/disconnect",         Fzmq_disconnect,          2, 2,
         "(SOCKET ADDRESS)\n\n\
Disconnect a socket from an endpoint.");

    DEFN("spoofax-module/send",               Fzmq_send,                2, 2,
         "(SOCKET MESSAGE &optional FLAGS)\n\n\
Send a string message. Optionally, flags can be provided.");
    DEFN("spoofax-module/receive",            Fzmq_receive,             1, 1,
         "(SOCKET &optional FLAGS)\n\n\
Receive a message on a socket. Optionally, flags can be provided.");


    // TODO: more stuff

    PROVIDE("spoofax-module");
    MESSAGE("[spoofax module] Loaded spoofax-module");
    return 0;
}

/*  LocalWords:  czmq subrs stddef
 */
