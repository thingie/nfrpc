nfrpc
=====

native python3 fastrpc

Very simple implementation of the FastRPC protocol used by seznam.cz
(and pretty much nobody else). Implemented in Python3, not compatible
with python 2. It's not meant to replace 'official' C implementation,
just to provide some FRPC functionality without having to compile
an external library, that is currently packaged only for Debian.

FastRPC protocol is basically XML-RPC without XML, using binary encoding.
Some behavior and data types is different. Specification is here:
http://fastrpc.sourceforge.net/?page=manual&sub=spec
