import unittest

from scripts.tools.declarative_def_tools.utils import DotDict


class TestUtils(unittest.TestCase):
    def test_as_list(self):
        from scripts.tools.declarative_def_tools.utils import as_list

        self.assertEqual(['foo'], as_list('foo'))
        self.assertEqual(['foo'], as_list(['foo']))
        self.assertEqual([42], as_list(42))
        self.assertEqual([], as_list([]))
        self.assertEqual([42], as_list([42]))
        self.assertEqual([42], as_list((42,)))
        self.assertEqual([42], as_list({42}))
        self.assertEqual([None], as_list(None))

    def test_dotdict(self):
        from scripts.tools.declarative_def_tools.utils import DotDict
        original = dict({
            "a0": 1,
            "b0": [1, 2],
            "c0": 3,
            "d0": {
                "a1": 11,
                "b1": [11, 12],
                "c1": 13,
                "d1": {
                    "a2": 21,
                    "b2": [21, 22],
                    "c2": 23,
                }
            }
        })
        dotdict = DotDict(original)
        dotdict_sybling = dotdict
        dict_copy = DotDict(original.copy())
        dotdict_copy = dotdict.copy()
        self.assertEqual(original, dotdict)
        dotdict.a0 = "changed"
        self.assertEqual(1, original["a0"])
        self.assertEqual(dotdict, dotdict_sybling)
        self.assertEqual(original, dict_copy)
        self.assertEqual(original, dotdict_copy)
        dotdict.d0.a1 = "changed"
        self.assertEqual(11, original["d0"]["a1"])
        self.assertEqual(dotdict, dotdict_sybling)
        self.assertEqual(original, dict_copy)
        self.assertEqual(original, dotdict_copy)
        dotdict_sybling.d0.d1 = DotDict({"changed": True})
        self.assertEqual(True, dotdict_sybling.d0.d1.changed)
        self.assertEqual(dotdict, dotdict_sybling)
        self.assertEqual(original, dict_copy)
        self.assertEqual(original, dotdict_copy)

        # modify the list
        dotdict.b0[0] = "changed"
        self.assertEqual(1, original["b0"][0])
        self.assertEqual(dotdict, dotdict_sybling)
        self.assertEqual(original, dict_copy)
        self.assertEqual(original, dotdict_copy)

    def test_dotdict_assign(self):
        dotdict = DotDict()
        expct = DotDict()

        dotdict.assign("a0", 1)
        expct.a0 = 1
        self.assertEqual(expct, dotdict)

        dotdict.assign("b0[0]", 1)
        expct.b0 = [1]
        self.assertEqual(expct, dotdict)

        dotdict.assign("b0[3]", 3)
        expct.b0 += [None, None, 3]
        self.assertEqual(expct, dotdict)

        dotdict.assign("c0.c1[0]['hallo']", "hallo")
        expct.c0 = DotDict(c1=[DotDict(hallo="hallo")])
        self.assertEqual(expct, dotdict)

        dotdict.assign("c0.c1[0][0].c2", 3)
        expct.c0.c1[0][0] = DotDict(c2=3)
        self.assertEqual(expct, dotdict)

        dotdict.assign("c0['c1'][0][0]['d2']", "d2")
        expct.c0.c1[0][0].d2 = "d2"
        self.assertEqual(expct, dotdict)
