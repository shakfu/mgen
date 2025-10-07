Backends API
============

Backend base classes and implementations.

Base Classes
------------

LanguageBackend
~~~~~~~~~~~~~~~

.. autoclass:: mgen.backends.base.LanguageBackend
   :members:
   :undoc-members:
   :show-inheritance:

AbstractEmitter
~~~~~~~~~~~~~~~

.. autoclass:: mgen.backends.base.AbstractEmitter
   :members:
   :undoc-members:
   :show-inheritance:

AbstractFactory
~~~~~~~~~~~~~~~

.. autoclass:: mgen.backends.base.AbstractFactory
   :members:
   :undoc-members:
   :show-inheritance:

C Backend
---------

.. automodule:: mgen.backends.c
   :members:
   :undoc-members:
   :show-inheritance:

C++ Backend
-----------

.. automodule:: mgen.backends.cpp
   :members:
   :undoc-members:
   :show-inheritance:

Rust Backend
------------

.. automodule:: mgen.backends.rust
   :members:
   :undoc-members:
   :show-inheritance:

Go Backend
----------

.. automodule:: mgen.backends.go
   :members:
   :undoc-members:
   :show-inheritance:

Haskell Backend
---------------

.. automodule:: mgen.backends.haskell
   :members:
   :undoc-members:
   :show-inheritance:

OCaml Backend
-------------

.. automodule:: mgen.backends.ocaml
   :members:
   :undoc-members:
   :show-inheritance:

Backend Selection
-----------------

Backends are selected via the ``target_language`` parameter::

   from mgen.pipeline import PipelineConfig

   # C backend
   config = PipelineConfig(target_language="c")

   # Rust backend
   config = PipelineConfig(target_language="rust")

   # etc.

Available backends: ``c``, ``cpp``, ``rust``, ``go``, ``haskell``, ``ocaml``

Extending Backends
------------------

To add a new backend:

1. Subclass ``LanguageBackend``
2. Implement required abstract methods
3. Create backend-specific emitter, factory, builder
4. Register in ``mgen.backends.__init__.py``

See ``CLAUDE.md`` for detailed architecture notes.
