Pipeline API
============

The pipeline module provides the main entry point for code conversion.

MGenPipeline
------------

.. autoclass:: mgen.pipeline.MGenPipeline
   :members:
   :undoc-members:
   :show-inheritance:

PipelineConfig
--------------

.. autoclass:: mgen.pipeline.PipelineConfig
   :members:
   :undoc-members:
   :show-inheritance:

PipelineResult
--------------

.. autoclass:: mgen.pipeline.PipelineResult
   :members:
   :undoc-members:
   :show-inheritance:

Example Usage
-------------

Basic conversion::

   from mgen.pipeline import MGenPipeline, PipelineConfig

   config = PipelineConfig(target_language="c")
   pipeline = MGenPipeline(config=config)
   result = pipeline.convert("example.py")

   if result.success:
       print("Conversion successful")
       for path in result.output_files:
           print(f"Generated: {path}")
   else:
       print("Errors:", result.errors)

With verification::

   config = PipelineConfig(
       target_language="rust",
       enable_formal_verification=True,
       strict_verification=True,
   )
   pipeline = MGenPipeline(config=config)
   result = pipeline.convert("example.py")

Pipeline Phases
---------------

The pipeline executes in 7 phases:

1. **Validation**: Parse and validate Python AST
2. **Analysis**: Analyze types, dependencies, control flow
3. **Python Optimization**: Optimize Python AST
4. **Mapping**: Map Python constructs to target language
5. **Target Optimization**: Optimize target language constructs
6. **Generation**: Generate target language code
7. **Build**: Optionally compile/build the generated code

See Also
--------

- :doc:`backends` - Backend-specific APIs
- :doc:`verification` - Verification APIs
- :doc:`frontend` - Frontend analysis APIs
