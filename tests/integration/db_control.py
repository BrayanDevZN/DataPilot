"""Compatibility entry point; repository integration tests live in repository.py."""

import unittest

from repository import RepositoryTests

if __name__ == "__main__":
    unittest.main(verbosity=2)
