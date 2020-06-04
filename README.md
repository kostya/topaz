Topaz
=====

This is fork of official repo which is not developed since 2016.

Topaz is an implementation of the Ruby programming language, written in Python,
using the RPython VM toolchain. Its goals are simplicity of implementation and
performance.

### Install using Docker

`docker build -t topaz - < Dockerfile`

To run something:

`docker run -it topaz`

`topaz /path/to/file.rb`

### Benchmarks

I added it to benchmarks here: https://github.com/kostya/jit-benchmarks, in most cases this is not final performance, and optimizations can be done
