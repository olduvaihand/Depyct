# test/unit_tests/test_io/test_format.py
# Copyright (c) 2012 the Depyct authors and contributors <see AUTHORS>
#
# This module is part of Depyct and is released under the MIT License:
# http://www.opensource.org/licenses/mit-license.php
from depyct import testing
from depyct.io import format


class Registrant:
    extensions = ('x',)


class RegistryTest(testing.DepyctUnitTest):

    def setUp(self):
        self.registry = format._Registry()

    def test_register(self):
        self.assertNotIn('x', self.registry)
        self.registry.register(Registrant)
        self.assertEqual(self.registry['x'], Registrant)
        self.registry.unregister(Registrant)
        self.assertNotIn('x', self.registry)

    def test_register_with_also(self):
        self.assertNotIn('x', self.registry)
        self.assertNotIn('a', self.registry)
        self.registry.register(Registrant, also=('a',))
        self.assertEqual(self.registry['x'], Registrant)
        self.assertEqual(self.registry['a'], Registrant)
        self.registry.unregister(Registrant)
        self.assertNotIn('x', self.registry)
        self.assertNotIn('a', self.registry)

    def test_register_with_only(self):
        self.assertNotIn('x', self.registry)
        self.assertNotIn('z', self.registry)
        self.registry.register(Registrant, only=('z',))
        self.assertNotIn('x', self.registry)
        self.assertEqual(self.registry['z'], Registrant)
        self.registry.unregister(Registrant)
        self.assertNotIn('z', self.registry)

    def test_register_with_also_and_only(self):
        self.assertFalse(self.registry)
        with self.assertWarns(UserWarning):
          self.registry.register(Registrant, also=('a',), only=('z',))
        self.assertNotIn('x', self.registry)
        self.assertNotIn('a', self.registry)
        self.assertEqual(self.registry['z'], Registrant)
        self.registry.unregister(Registrant)
        self.assertNotIn('x', self.registry)
        self.assertNotIn('a', self.registry)
        self.assertNotIn('z', self.registry)

    def test_unregister(self):
        self.assertNotIn('x', self.registry)
        self.assertNotIn('a', self.registry)
        self.registry.register(Registrant, also=('a',))
        self.assertEqual(self.registry['x'], Registrant)
        self.assertEqual(self.registry['a'], Registrant)
        self.registry.unregister(Registrant)
        self.assertNotIn('x', self.registry)
        self.assertNotIn('a', self.registry)

    def test_unregister_with_keep(self):
        self.assertNotIn('x', self.registry)
        self.assertNotIn('a', self.registry)
        self.registry.register(Registrant, also=('a',))
        self.registry.unregister(Registrant, keep=('a',))
        self.assertNotIn('x', self.registry)
        self.assertEqual(self.registry['a'], Registrant)
        self.registry.unregister(Registrant)
        self.assertNotIn('a', self.registry)

    def test_unregister_with_discard(self):
        self.assertNotIn('x', self.registry)
        self.assertNotIn('a', self.registry)
        self.registry.register(Registrant, also=('a',))
        self.registry.unregister(Registrant, discard=('x',))
        self.assertNotIn('x', self.registry)
        self.assertEqual(self.registry['a'], Registrant)
        self.registry.unregister(Registrant)
        self.assertNotIn('a', self.registry)

    def test_unregister_with_keep_and_discard(self):
        self.assertNotIn('x', self.registry)
        self.assertNotIn('a', self.registry)
        self.registry.register(Registrant, also=('a',))
        self.registry.unregister(Registrant, keep=('a', 'x'), discard='a')
        self.assertEqual(self.registry['x'], Registrant)
        self.assertNotIn('a', self.registry)
        self.registry.unregister(Registrant)
        self.assertNotIn('x', self.registry)


if __name__ == "__main__":
    testing.main()
