Verification API
================

Formal verification components using Z3 theorem prover.

Bounds Prover
-------------

.. automodule:: mgen.frontend.verifiers.bounds_prover
   :members:
   :undoc-members:
   :show-inheritance:

Theorem Prover
--------------

.. automodule:: mgen.frontend.verifiers.theorem_prover
   :members:
   :undoc-members:
   :show-inheritance:

Correctness Prover
------------------

.. automodule:: mgen.frontend.verifiers.correctness_prover
   :members:
   :undoc-members:
   :show-inheritance:

Performance Analyzer
--------------------

.. automodule:: mgen.frontend.verifiers.performance_analyzer
   :members:
   :undoc-members:
   :show-inheritance:

Z3 Formula Generator
--------------------

.. automodule:: mgen.frontend.verifiers.z3_formula_generator
   :members:
   :undoc-members:
   :show-inheritance:

Example Usage
-------------

Verifying array bounds::

   from mgen.frontend.verifiers.bounds_prover import BoundsProver
   import ast

   code = '''
   def sum_array(arr: list[int]) -> int:
       total: int = 0
       for i in range(len(arr)):
           total += arr[i]
       return total
   '''

   tree = ast.parse(code)
   prover = BoundsProver()
   result = prover.verify_memory_safety(tree.body[0])

   if result.success:
       print("Array access is SAFE")
   else:
       print("Verification failed:", result.errors)

Using with pipeline::

   from mgen.pipeline import MGenPipeline, PipelineConfig

   config = PipelineConfig(
       target_language="c",
       enable_formal_verification=True,
       strict_verification=True,
   )

   pipeline = MGenPipeline(config=config)
   result = pipeline.convert("example.py")

Verification Results
--------------------

Verification results include:

- ``success``: Boolean indicating verification success
- ``errors``: List of verification errors
- ``warnings``: List of verification warnings
- ``proofs``: Mathematical proofs (when available)
- ``counterexamples``: Examples of unsafe inputs

Strict vs Non-Strict Mode
--------------------------

**Non-strict mode** (default with ``--verify``)::

   config = PipelineConfig(
       enable_formal_verification=True,
       strict_verification=False,  # default
   )

Runs verification, shows warnings, generates code anyway.

**Strict mode** (``--verify --strict``)::

   config = PipelineConfig(
       enable_formal_verification=True,
       strict_verification=True,
   )

Runs verification, **halts** code generation on failures.

Z3 Availability
---------------

Check if Z3 is available::

   from mgen.frontend.verifiers.bounds_prover import Z3_AVAILABLE

   if Z3_AVAILABLE:
       print("Z3 is available")
   else:
       print("Install with: pip install mgen[z3]")

Verification is automatically skipped if Z3 is not installed.

See Also
--------

- :doc:`/guide/verification` - User guide for formal verification
- :doc:`frontend` - Frontend analysis APIs
- ``docs/dev/was-z3-worth-it.md`` - Deep dive on Z3 integration
