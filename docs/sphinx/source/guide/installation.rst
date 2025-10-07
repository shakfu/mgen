Installation
============

Requirements
------------

- Python 3.9 or higher
- pip or uv package manager

Basic Installation
------------------

Install MGen using pip::

   pip install mgen

Or using uv::

   uv pip install mgen

With Formal Verification
-------------------------

To enable Z3-based formal verification, install with the z3 extra::

   pip install mgen[z3]

Or::

   uv pip install mgen[z3]

Development Installation
------------------------

Clone the repository and install in development mode::

   git clone https://github.com/shakfu/mgen.git
   cd mgen
   uv sync --group dev

This installs all development dependencies including:

- pytest (testing)
- mypy (type checking)
- ruff (linting)
- sphinx (documentation)

Verify Installation
-------------------

Check that MGen is installed correctly::

   mgen --version

Run the test suite::

   make test

Or with uv::

   uv run pytest
