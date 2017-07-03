aws-parsecf
===========

(Tries to) parse AWS CloudFormation’s intrinsic functions in the
template.

Quick Start
-----------

First, install the library:

.. code:: bash

    pip install aws-parsecf

Then, from a Python interpreter:

.. code:: python

    import aws_parsecf

    with open('/path/to/cloudformation.json', 'r') as f:
        print(aws_parsecf.load_json(f))

**Note** that some of the intrinsic functions require a configured
environment (like ``"Fn::GetAZs"``), so if you don’t have it set:

.. code:: bash

    aws configure

Usage
-----

3 simple methods:

.. code:: python

    aws_parsecf.load_json(stream, region)
    aws_parsecf.loads_json(string, region)
    aws_parsecf.load_yaml(stream_or_string, region)

``region`` is optional, and defaults to the region you specified when using
``aws configure``. If you didn’t specify a default region in
``aws configure``, or you want to override it, you should specify your
region:

.. code:: python

    aws_parsecf.load_json(stream, region='us-west-1')

Contributing
------------

Running tests:

.. code:: bash

    ./setup.py install
    ./setup.py test

Missing pieces:

-  Support YAML short form.

You know the drill, PR!
