Healthchecks Decorator
======================

|PyPI| |Status| |Python Version| |License|

|Read the Docs| |Tests| |Codecov|

|pre-commit| |Black|

.. |PyPI| image:: https://img.shields.io/pypi/v/healthchecks-decorator.svg
   :target: https://pypi.org/project/healthchecks-decorator/
   :alt: PyPI
.. |Status| image:: https://img.shields.io/pypi/status/healthchecks-decorator.svg
   :target: https://pypi.org/project/healthchecks-decorator/
   :alt: Status
.. |Python Version| image:: https://img.shields.io/pypi/pyversions/healthchecks-decorator
   :target: https://pypi.org/project/healthchecks-decorator
   :alt: Python Version
.. |License| image:: https://img.shields.io/pypi/l/healthchecks-decorator
   :target: https://opensource.org/licenses/MIT
   :alt: License
.. |Read the Docs| image:: https://img.shields.io/readthedocs/healthchecks-decorator/latest.svg?label=Read%20the%20Docs
   :target: https://healthchecks-decorator.readthedocs.io/
   :alt: Read the documentation at https://healthchecks-decorator.readthedocs.io/
.. |Tests| image:: https://github.com/danidelvalle/healthchecks-decorator/workflows/Tests/badge.svg
   :target: https://github.com/danidelvalle/healthchecks-decorator/actions?workflow=Tests
   :alt: Tests
.. |Codecov| image:: https://codecov.io/gh/danidelvalle/healthchecks-decorator/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/danidelvalle/healthchecks-decorator
   :alt: Codecov
.. |pre-commit| image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
   :target: https://github.com/pre-commit/pre-commit
   :alt: pre-commit
.. |Black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
   :alt: Black


A simple python decorator for `healthchecks.io`_.

Features
--------

* Just decorate your function with ``@healthcheck`` 🚀.
* Support sending ``/start`` signals to measure job execution times ⏲️.
* Support both SaaS and self-hosted endpoints 😊.


Requirements
------------

* None - only pure python 🐍.


Installation
------------

You can install *Healthchecks Decorator* via pip_ from PyPI_:

.. code:: console

   $ pip install healthchecks-decorator


Usage
-----

.. code:: python

   from healthchecks_decorator import healthcheck

   @healthcheck(url="https://hc-ping.com/<uuid>")
   def my_job():
      """Job with a success healthcheck signal when done"""
      pass


   @healthcheck(url="https://hc-ping.com/<uuid>", send_start=True)
   def my_job2():
      """Job with also a /start signal before starting"""
      pass


Please see the `Documentation`_ for details.


Contributing
------------

Contributions are very welcome.
To learn more, see the `Contributor Guide`_.


License
-------

Distributed under the terms of the `MIT license`_,
*Healthchecks Decorator* is free and open source software.


Issues
------

If you encounter any problems,
please `file an issue`_ along with a detailed description.


Credits
-------
* `healthchecks.io`_.
* This project was generated from `@cjolowicz`_'s `Hypermodern Python Cookiecutter`_ template.

.. _@cjolowicz: https://github.com/cjolowicz
.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _MIT license: https://opensource.org/licenses/MIT
.. _PyPI: https://pypi.org/
.. _Hypermodern Python Cookiecutter: https://github.com/cjolowicz/cookiecutter-hypermodern-python
.. _file an issue: https://github.com/danidelvalle/healthchecks-decorator/issues
.. _pip: https://pip.pypa.io/
.. github-only
.. _Contributor Guide: CONTRIBUTING.rst
.. _Documentation: https://healthchecks-decorator.readthedocs.io/
.. _healthchecks.io: https://healthchecks.io/
