The package is published on https://github.com/openpolis/django-eztaskmanager.

This is the procedure to follow.

Generate a new version with bumpversion.
It is not necessary to create a version for each commit; versioning can be planned.
Each new version has a tag, and pushing to the main branch triggers linting and tests on the Python/Django matrix;

.. code-block:: bash

    git commit -m "-- your changelog message --"
    bumpversion patch
    git push
    git push --tags

Create a new release from a tag, on github.com, https://github.com/openpolis/django-eztaskmanager/releases.
Manually specifying the previous release (for the changelog). Each new release builds and publishes to pypi.org using poetry.
To update the documentation, just push to the repository.
https://readthedocs.io is automatically synchronized with the GitHub repository.
After a few minutes, the changes are collected by the site, which then builds and publishes the latest version.

The package contains libraries for both rq and celery.
Therefore, the installation of the package for Celery should only contain configuration changes.
This makes the package larger, but maintenance and installation are simpler.
For example, the tests require the libraries, even if only for mocking purposes.






