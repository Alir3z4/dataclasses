from dataclasses import (
    dataclass, field, FrozenInstanceError, fields, asdict, astuple
)

import inspect
import unittest
from typing import ClassVar, Any
from collections import OrderedDict

# Just any custom exception we can catch.
class CustomError(Exception): pass

class TestCase(unittest.TestCase):
    def test_no_fields(self):
        @dataclass
        class C:
            pass

        o = C()
        self.assertEqual(repr(o), 'C()')

    def test_one_field_no_default(self):
        @dataclass
        class C:
            x: int

        o = C(42)
        self.assertEqual(o.x, 42)

    def test_named_init_params(self):
        @dataclass
        class C:
            x: int

        o = C(x=32)
        self.assertEqual(o.x, 32)

    def test_two_fields_one_default(self):
        @dataclass
        class C:
            x: int
            y: int=0

        o = C(3)
        self.assertEqual((o.x, o.y), (3, 0))

        # Non-defaults following defaults.
        with self.assertRaisesRegex(TypeError,
                                    "non-default argument 'y' follows "
                                    "default argument"):
            @dataclass
            class C:
                x: int=0
                y: int

    def test_overwriting_init(self):
        with self.assertRaisesRegex(AttributeError,
                                    'Cannot overwrite attribute __init__ '
                                    'in C'):
            @dataclass
            class C:
                x: int
                def __init__(self, x):
                    self.x = 2 * x

        @dataclass(init=False)
        class C:
            x: int
            def __init__(self, x):
                self.x = 2 * x
        self.assertEqual(C(5).x, 10)

    def test_overwriting_repr(self):
        with self.assertRaisesRegex(AttributeError,
                                    'Cannot overwrite attribute __repr__ '
                                    'in C'):
            @dataclass
            class C:
                x: int
                def __repr__(self):
                    pass

        @dataclass(repr=False)
        class C:
            x: int
            def __repr__(self):
                return 'x'
        self.assertEqual(repr(C(0)), 'x')

    def test_overwriting_cmp(self):
        with self.assertRaisesRegex(AttributeError,
                                    'Cannot overwrite attribute __eq__ '
                                    'in C'):
            # This will generate the cmp functions, make sure we can't
            #  overwrite them.
            @dataclass(hash=False, frozen=False)
            class C:
                x: int
                def __eq__(self):
                    pass

        @dataclass(cmp=False)
        class C:
            x: int
            def __eq__(self, other):
                return True
        self.assertEqual(C(0), 'x')

    def test_overwriting_hash(self):
        with self.assertRaisesRegex(AttributeError,
                                    'Cannot overwrite attribute __hash__ '
                                    'in C'):
            @dataclass(frozen=True)
            class C:
                x: int
                def __hash__(self):
                    pass

        @dataclass(frozen=True,hash=False)
        class C:
            x: int
            def __hash__(self):
                return 600
        self.assertEqual(hash(C(0)), 600)

        with self.assertRaisesRegex(AttributeError,
                                    'Cannot overwrite attribute __hash__ '
                                    'in C'):
            @dataclass(frozen=True)
            class C:
                x: int
                def __hash__(self):
                    pass

        @dataclass(frozen=True, hash=False)
        class C:
            x: int
            def __hash__(self):
                return 600
        self.assertEqual(hash(C(0)), 600)

    def test_overwriting_frozen(self):
        # frozen uses __setattr__ and __delattr__
        with self.assertRaisesRegex(AttributeError,
                                    'Cannot overwrite attribute __setattr__ '
                                    'in C'):
            @dataclass(frozen=True)
            class C:
                x: int
                def __setattr__(self):
                    pass

        with self.assertRaisesRegex(AttributeError,
                                    'Cannot overwrite attribute __delattr__ '
                                    'in C'):
            @dataclass(frozen=True)
            class C:
                x: int
                def __delattr__(self):
                    pass

        @dataclass(frozen=False)
        class C:
            x: int
            def __setattr__(self, name, value):
                self.__dict__['x'] = value * 2
        self.assertEqual(C(10).x, 20)

    def test_overwrite_fields_in_derived_class(self):
        # Note that x from C1 replaces x in Base, but the order remains
        #  the same as defined in Base.
        @dataclass
        class Base:
            x: Any = 15.0
            y: int = 0

        @dataclass
        class C1(Base):
            z: int = 10
            x: int = 15

        o = Base()
        self.assertEqual(repr(o), 'Base(x=15.0,y=0)')

        o = C1()
        self.assertEqual(repr(o), 'C1(x=15,y=0,z=10)')

        o = C1(x=5)
        self.assertEqual(repr(o), 'C1(x=5,y=0,z=10)')

    def test_field_named_self(self):
        @dataclass
        class C:
            self: str
        c=C('foo')
        self.assertEqual(c.self, 'foo')

    def test_repr(self):
        @dataclass
        class B:
            x: int

        @dataclass
        class C(B):
            y: int = 10

        o = C(4)
        self.assertEqual(repr(o), 'C(x=4,y=10)')

        @dataclass
        class D(C):
            x: int = 20
        self.assertEqual(repr(D()), 'D(x=20,y=10)')

    def test_0_field_cmp(self):
        @dataclass
        class C:
            pass
        self.assertEqual(C(), C())
        self.assertLessEqual(C(), C())
        self.assertGreaterEqual(C(), C())

    def test_1_field_cmp(self):
        @dataclass
        class C:
            x: int
        self.assertEqual(C(1), C(1))
        self.assertNotEqual(C(0), C(1))
        self.assertLess(C(0), C(1))
        self.assertLessEqual(C(0), C(1))
        self.assertLessEqual(C(1), C(1))
        self.assertGreater(C(1), C(0))
        self.assertGreaterEqual(C(1), C(0))
        self.assertGreaterEqual(C(1), C(1))

    def test_simple_cmp(self):
        @dataclass
        class C:
            x: int
            y: int
        self.assertEqual(C(0, 0), C(0, 0))
        self.assertEqual(C(1, 2), C(1, 2))
        self.assertNotEqual(C(1, 0), C(0, 0))
        self.assertNotEqual(C(1, 0), C(1, 1))
        self.assertLess(C(0, 0), C(0, 1))
        self.assertLess(C(0, 0), C(1, 0))
        self.assertLessEqual(C(0, 0), C(0, 1))
        self.assertLessEqual(C(0, 1), C(0, 1))
        self.assertLessEqual(C(0, 0), C(1, 0))
        self.assertLessEqual(C(1, 0), C(1, 0))
        self.assertGreater(C(0, 1), C(0, 0))
        self.assertGreater(C(1, 0), C(0, 0))
        self.assertGreaterEqual(C(0, 1), C(0, 0))
        self.assertGreaterEqual(C(0, 1), C(0, 1))
        self.assertGreaterEqual(C(1, 0), C(0, 0))
        self.assertGreaterEqual(C(1, 0), C(1, 0))

        # For operators returning False, we have to use assertFalse.
        self.assertFalse(C(0, 1) < C(0, 0))
        self.assertFalse(C(1, 0) < C(0, 0))
        self.assertFalse(C(0, 1) <= C(0, 0))
        self.assertFalse (C(0, 2) <= C(0, 1))
        self.assertFalse(C(1, 0) <=  C(0, 0))
        self.assertFalse(C(0, 0) > C(0, 1))
        self.assertFalse(C(0, 0) > C(1, 0))
        self.assertFalse(C(0, 0) >= C(0, 1))
        self.assertFalse(C(0, 0) >= C(0, 1))
        self.assertFalse(C(0, 0) >= C(1, 0))

    def test_0_field_hash(self):
        @dataclass(hash=True)
        class C:
            pass
        self.assertEqual(hash(C()), hash(()))

    def test_1_field_hash(self):
        @dataclass(hash=True)
        class C:
            x: int
        self.assertEqual(hash(C(4)), hash((4,)))
        self.assertEqual(hash(C(42)), hash((42,)))

    def test_hash(self):
        @dataclass(hash=True)
        class C:
            x: int
            y: str
        self.assertEqual(hash(C(1, 'foo')), hash((1, 'foo')))

    def test_no_hash(self):
        @dataclass(hash=None)
        class C:
            x: int
        with self.assertRaisesRegex(TypeError,
                                    "unhashable type: 'C'"):
            hash(C(1))

    def test_hash_rules(self):
        # Test all 12 cases of:
        #  hash=True/False/None
        #  cmp=True/False
        #  frozen=True/False
        for hash,   cmp,   frozen, result in [
            (True,  False, False,  'fn'),
            (True,  False, True,   'fn'),
            (True,  True,  False,  'fn'),
            (True,  True,  True,   'fn'),
            (False, False, False,  'absent'),
            (False, False, True,   'absent'),
            (False, True,  False,  'absent'),
            (False, True,  True,   'absent'),
            (None,  False, False,  'absent'),
            (None,  False, True,   'absent'),
            (None,  True,  False,  'none'),
            (None,  True,  True,   'fn'),
            ]:
            with self.subTest(hash=hash, cmp=cmp, frozen=frozen):
                @dataclass(hash=hash, cmp=cmp, frozen=frozen)
                class C:
                    pass

                # See if the result matches what's expected.
                if result == 'fn':
                    # __hash__ contains the function we generated.
                    self.assertIn('__hash__', C.__dict__)
                    self.assertIsNot(C.__dict__['__hash__'], None)
                elif result == 'absent':
                    # __hash__ is not present in our class.
                    self.assertNotIn('__hash__', C.__dict__)
                elif result == 'none':
                    # __hash__ is set to None.
                    self.assertIn('__hash__', C.__dict__)
                    self.assertIs(C.__dict__['__hash__'], None)
                else:
                    assert False, f'unknown result {result!r}'

    def test_field_no_default(self):
        @dataclass
        class C:
            x: int = field()

        self.assertEqual(repr(C(5)), 'C(x=5)')

        with self.assertRaisesRegex(TypeError,
                                    r"__init__\(\) missing 1 required "
                                    "positional argument: 'x'"):
            C()

    def test_field_default(self):
        default = object()
        @dataclass
        class C:
            x: object = field(default=default)

        self.assertIs(C.x, default)
        c = C(10)
        self.assertEqual(c.x, 10)

        # If we delete the instance attribute, we should then see the
        #  class attribute.
        del c.x
        self.assertIs(c.x, default)

        self.assertIs(C().x, default)

    def test_not_in_repr(self):
        @dataclass
        class C:
            x: int = field(repr=False)
        with self.assertRaises(TypeError):
            C()
        c = C(10)
        self.assertEqual(repr(c), 'C()')

        @dataclass
        class C:
            x: int = field(repr=False)
            y: int
        c = C(10, 20)
        self.assertEqual(repr(c), 'C(y=20)')

    def test_not_in_cmp(self):
        @dataclass
        class C:
            x: int = 0
            y: int = field(cmp=False, default=4)

        self.assertEqual(C(), C(0, 20))
        self.assertEqual(C(1, 10), C(1, 20))
        self.assertNotEqual(C(3), C(4, 10))
        self.assertNotEqual(C(3, 10), C(4, 10))

    def test_hash_field_rules(self):
        # Test all 6 cases of:
        #  hash=True/False/None
        #  cmp=True/False
        for hash_val, cmp,   result in [
            (True,    False, 'field'),
            (True,    True,  'field'),
            (False,   False, 'absent'),
            (False,   True,  'absent'),
            (None,    False, 'absent'),
            (None,    True,  'field'),
            ]:
            with self.subTest(hash_val=hash_val, cmp=cmp):
                @dataclass(hash=True)
                class C:
                    x: int = field(cmp=cmp, hash=hash_val, default=5)

                if result == 'field':
                    # __hash__ contains the field.
                    self.assertEqual(C(5).__hash__(), hash((5,)))
                elif result == 'absent':
                    # The field is not present in the hash.
                    self.assertEqual(C(5).__hash__(), hash(()))
                else:
                    assert False, f'unknown result {result!r}'

    def test_not_in_init(self):
        # If init=False, we must have a default value.
        # Otherwise, how would it get initialized?
        with self.assertRaisesRegex(TypeError,
                                    'field x has init=False, but has no '
                                    'default value or factory function'):
            @dataclass
            class C:
                x: int = field(init=False)

        with self.assertRaisesRegex(TypeError,
                                    'field z has init=False, but has no '
                                    'default value or factory function'):
            @dataclass
            class C:
                x: int
                y: int = 0
                z: int = field(init=False)
                t: int

    def test_class_marker(self):
        @dataclass
        class C:
            x: int
            y: str = field(init=False, default=None)
            z: str = field(repr=False)

        field_dict = fields(C)
        # field_dict is an OrderedDict of 3 items, each value
        #  is in __annotations__.
        self.assertIsInstance(field_dict, OrderedDict)
        for f in field_dict.values():
            self.assertIn(f.name, C.__annotations__)

        self.assertEqual(len(field_dict), 3)
        field_list = list(field_dict.values())
        self.assertEqual(field_list[0].name, 'x')
        self.assertEqual(field_list[0].type, int)
        self.assertFalse(hasattr(C, 'x'))
        self.assertTrue (field_list[0].init)
        self.assertTrue (field_list[0].repr)
        self.assertEqual(field_list[1].name, 'y')
        self.assertEqual(field_list[1].type, str)
        self.assertIsNone(getattr(C, 'y'))
        self.assertFalse(field_list[1].init)
        self.assertTrue (field_list[1].repr)
        self.assertEqual(field_list[2].name, 'z')
        self.assertEqual(field_list[2].type, str)
        self.assertFalse(hasattr(C, 'z'))
        self.assertTrue (field_list[2].init)
        self.assertFalse(field_list[2].repr)

    def test_field_order(self):
        @dataclass
        class B:
            a: str = 'B:a'
            b: str = 'B:b'
            c: str = 'B:c'

        @dataclass
        class C(B):
            b: str = 'C:b'

        self.assertEqual([(f.name, f.default) for f in fields(C).values()],
                         [('a', 'B:a'),
                          ('b', 'C:b'),
                          ('c', 'B:c')])

        @dataclass
        class D(B):
            c: str = 'D:c'

        self.assertEqual([(f.name, f.default) for f in fields(D).values()],
                         [('a', 'B:a'),
                          ('b', 'B:b'),
                          ('c', 'D:c')])

        @dataclass
        class E(D):
            a: str = 'E:a'
            d: str = 'E:d'

        self.assertEqual([(f.name, f.default) for f in fields(E).values()],
                         [('a', 'E:a'),
                          ('b', 'B:b'),
                          ('c', 'D:c'),
                          ('d', 'E:d')])

    def test_class_attrs(self):
        # We only have a class attribute if a default value is
        #  specified, either directly or via a field with a default.
        default = object()
        @dataclass
        class C:
            x: int
            y: int = field(repr=False)
            z: object = default
            t: int = field(default=100)

        self.assertFalse(hasattr(C, 'x'))
        self.assertFalse(hasattr(C, 'y'))
        self.assertIs   (C.z, default)
        self.assertEqual(C.t, 100)

    def test_disallowed_mutable_defaults(self):
        # For the known types, don't allow mutable default values.
        for typ, empty, non_empty in [(list, [], [1]),
                                      (dict, {}, {0:1}),
                                      (set, set(), set([1])),
                                      ]:
            with self.subTest(typ=typ):
                # Can't use a zero-length value.
                with self.assertRaisesRegex(ValueError,
                                            f'mutable default {typ} for field '
                                            'x is not allowed'):
                    @dataclass
                    class Point:
                        x: typ = empty


                # Nor a non-zero-length value
                with self.assertRaisesRegex(ValueError,
                                            f'mutable default {typ} for field '
                                            'y is not allowed'):
                    @dataclass
                    class Point:
                        y: typ = non_empty

                # Check subtypes also fail.
                class Subclass(typ): pass

                with self.assertRaisesRegex(ValueError,
                                            f"mutable default .*Subclass'>"
                                            ' for field z is not allowed'
                                            ):
                    @dataclass
                    class Point:
                        z: typ = Subclass()

                # Because this is a ClassVar, it can be mutable.
                @dataclass
                class C:
                    z: ClassVar[typ] = typ()

                # Because this is a ClassVar, it can be mutable.
                @dataclass
                class C:
                    x: ClassVar[typ] = Subclass()


    def test_deliberately_mutable_defaults(self):
        # If a mutable default isn't in the known list of
        #  (list, dict, set), then it's okay.
        class Mutable:
            def __init__(self):
                self.l = []

        @dataclass
        class C:
            x: Mutable

        # These 2 instances will share this value of x.
        lst = Mutable()
        o1 = C(lst)
        o2 = C(lst)
        self.assertEqual(o1, o2)
        o1.x.l.extend([1, 2])
        self.assertEqual(o1, o2)
        self.assertEqual(o1.x.l, [1, 2])
        self.assertIs(o1.x, o2.x)

    def test_no_options(self):
        # call with dataclass()
        @dataclass()
        class C:
            x: int

        self.assertEqual(repr(C(42)), 'C(x=42)')

    def test_not_tuple(self):
        # Make sure we can't be compared to a tuple.
        @dataclass
        class Point:
            x: int
            y: int
        self.assertNotEqual(Point(1, 2), (1, 2))

        # And that we can't compare to another unrelated dataclass
        @dataclass
        class C:
            x: int
            y: int
        self.assertNotEqual(Point(1, 3), C(1, 3))

    def test_base_has_init(self):
        class B:
            def __init__(self):
                pass

        # Make sure that declaring this class doesn't raise an error.
        #  The issue is that we can't override __init__ in our class,
        #  but it should be okay to add __init__ to us if our base has
        #  an __init__.
        @dataclass
        class C(B):
            x: int = 0

    def test_frozen(self):
        @dataclass(frozen=True)
        class C:
            i: int

        c = C(10)
        self.assertEqual(c.i, 10)
        with self.assertRaises(FrozenInstanceError):
            c.i = 5
        self.assertEqual(c.i, 10)

        # Check that a derived class is still frozen, even if not
        #  marked so.
        @dataclass
        class D(C):
            pass

        d = D(20)
        self.assertEqual(d.i, 20)
        with self.assertRaises(FrozenInstanceError):
            d.i = 5
        self.assertEqual(d.i, 20)

    def test_not_tuple(self):
        # Test that some of the problems with namedtuple don't happen
        #  here.
        @dataclass
        class Point3D:
            x: int
            y: int
            z: int

        @dataclass
        class Date:
            year: int
            month: int
            day: int

        self.assertNotEqual(Point3D(2017, 6, 3), Date(2017, 6, 3))
        self.assertNotEqual(Point3D(1, 2, 3), (1, 2, 3))

        # Make sure we can't unpack
        with self.assertRaisesRegex(TypeError, 'is not iterable'):
            x, y, z = Point3D(4, 5, 6)

        # Maka sure another class with the same field names isn't
        #  equal.
        @dataclass
        class Point3Dv1:
            x: int = 0
            y: int = 0
            z: int = 0
        self.assertNotEqual(Point3D(0, 0, 0), Point3Dv1())

    def test_function_annotations(self):
        # Some dummy class and instance to use as a default.
        class F:
            pass
        f = F()

        def validate_class(cls):
            # First, check __annotations__, even though they're not
            #  function annotations.
            self.assertEqual(cls.__annotations__['i'], int)
            self.assertEqual(cls.__annotations__['j'], str)
            self.assertEqual(cls.__annotations__['k'], F)
            self.assertEqual(cls.__annotations__['l'], float)
            self.assertEqual(cls.__annotations__['z'], complex)

            # Verify __init__.

            signature = inspect.signature(cls.__init__)
            # Check the return type, should be None
            self.assertIs(signature.return_annotation, None)

            # Check each parameter.
            params = iter(signature.parameters.values())
            param = next(params)
            # This is testing an internal name, and probably shouldn't be tested.
            self.assertEqual(param.name, 'self')
            param = next(params)
            self.assertEqual(param.name, 'i')
            self.assertIs   (param.annotation, int)
            self.assertEqual(param.default, inspect.Parameter.empty)
            self.assertEqual(param.kind, inspect.Parameter.POSITIONAL_OR_KEYWORD)
            param = next(params)
            self.assertEqual(param.name, 'j')
            self.assertIs   (param.annotation, str)
            self.assertEqual(param.default, inspect.Parameter.empty)
            self.assertEqual(param.kind, inspect.Parameter.POSITIONAL_OR_KEYWORD)
            param = next(params)
            self.assertEqual(param.name, 'k')
            self.assertIs   (param.annotation, F)
            # Don't test for the default, since it's set to _MISSING
            self.assertEqual(param.kind, inspect.Parameter.POSITIONAL_OR_KEYWORD)
            param = next(params)
            self.assertEqual(param.name, 'l')
            self.assertIs   (param.annotation, float)
            # Don't test for the default, since it's set to _MISSING
            self.assertEqual(param.kind, inspect.Parameter.POSITIONAL_OR_KEYWORD)
            self.assertRaises(StopIteration, next, params)


        @dataclass
        class C:
            i: int
            j: str
            k: F=f
            l: float=field(default=None)
            z: complex=field(default=3+4j, init=False)

        validate_class(C)

        # Now repeat with __hash__.
        @dataclass(frozen=True, hash=True)
        class C:
            i: int
            j: str
            k: F=f
            l: float=field(default=None)
            z: complex=field(default=3+4j, init=False)

        validate_class(C)

    def test_dont_include_other_annotations(self):
        @dataclass
        class C:
            i: int
            def foo(self) -> int:
                return 4
            @property
            def bar(self) -> int:
                return 5
        self.assertEqual(list(C.__annotations__), ['i'])
        self.assertEqual(C(10).foo(), 4)
        self.assertEqual(C(10).bar, 5)

    def test_post_init(self):
        # Just make sure it gets called
        @dataclass
        class C:
            def __dataclass_post_init__(self):
                raise CustomError()
        with self.assertRaises(CustomError):
            C()

        @dataclass
        class C:
            i: int = 10
            def __dataclass_post_init__(self):
                if self.i == 10:
                    raise CustomError()
        with self.assertRaises(CustomError):
            C()
        # post-init gets called, but doesn't raise. This is just
        #  checking that self is used correctly.
        C(5)

        # If there's not an __init__, then post-init won't get called.
        @dataclass(init=False)
        class C:
            def __dataclass_post_init__(self):
                raise CustomError()
        # Creating the class won't raise
        C()

        @dataclass
        class C:
            x: int = 0
            def __dataclass_post_init__(self):
                self.x *= 2
        self.assertEqual(C().x, 0)
        self.assertEqual(C(2).x, 4)

        # Make sure that if we'r frozen, post-init can't set
        #  attributes.
        @dataclass(frozen=True)
        class C:
            x: int = 0
            def __dataclass_post_init__(self):
                self.x *= 2
        with self.assertRaises(FrozenInstanceError):
            C()

    def test_post_init_super(self):
        # Make sure super() post-init isn't called by default.
        class B:
            def __dataclass_post_init__(self):
                raise CustomError()

        @dataclass
        class C(B):
            def __dataclass_post_init__(self):
                self.x = 5

        self.assertEqual(C().x, 5)

        # Now call super(), and it will raise
        @dataclass
        class C(B):
            def __dataclass_post_init__(self):
                super().__dataclass_post_init__()

        with self.assertRaises(CustomError):
            C()

        # Make sure post-init is called, even if not defined in our
        #  class.
        @dataclass
        class C(B):
            pass

        with self.assertRaises(CustomError):
            C()

    def test_post_init_staticmethod(self):
        flag = False
        @dataclass
        class C:
            x: int
            y: int
            @staticmethod
            def __dataclass_post_init__():
                nonlocal flag
                flag = True

        self.assertFalse(flag)
        c = C(3, 4)
        self.assertEqual((c.x, c.y), (3, 4))
        self.assertTrue(flag)

    def test_post_init_classmethod(self):
        @dataclass
        class C:
            flag = False
            x: int
            y: int
            @classmethod
            def __dataclass_post_init__(cls):
                cls.flag = True

        self.assertFalse(C.flag)
        c = C(3, 4)
        self.assertEqual((c.x, c.y), (3, 4))
        self.assertTrue(C.flag)

    def test_class_var(self):
        # Make sure ClassVars are ignored in __init__, __repr__, etc.
        @dataclass
        class C:
            x: int
            y: int = 10
            z: ClassVar[int] = 1000
            w: ClassVar[int] = 2000
            t: ClassVar[int] = 3000

        c = C(5)
        self.assertEqual(repr(c), 'C(x=5,y=10)')
        self.assertEqual(len(fields(C)), 2)                 # We have 2 fields
        self.assertEqual(len(C.__annotations__), 5)         # And 3 ClassVars
        self.assertEqual(c.z, 1000)
        self.assertEqual(c.w, 2000)
        self.assertEqual(c.t, 3000)
        C.z += 1
        self.assertEqual(c.z, 1001)
        c = C(20)
        self.assertEqual((c.x, c.y), (20, 10))
        self.assertEqual(c.z, 1001)
        self.assertEqual(c.w, 2000)
        self.assertEqual(c.t, 3000)

    def test_frozen_class_var(self):
        # Make sure ClassVars work even if we're frozen.
        @dataclass(frozen=True)
        class C:
            x: int
            y: int = 10
            z: ClassVar[int] = 1000
            w: ClassVar[int] = 2000
            t: ClassVar[int] = 3000

        c = C(5)
        self.assertEqual(repr(C(5)), 'C(x=5,y=10)')
        self.assertEqual(len(fields(C)), 2)                 # We have 2 fields
        self.assertEqual(len(C.__annotations__), 5)         # And 3 ClassVars
        self.assertEqual(c.z, 1000)
        self.assertEqual(c.w, 2000)
        self.assertEqual(c.t, 3000)
        # We can still modify the ClassVar, it's only instances that are
        #  frozen.
        C.z += 1
        self.assertEqual(c.z, 1001)
        c = C(20)
        self.assertEqual((c.x, c.y), (20, 10))
        self.assertEqual(c.z, 1001)
        self.assertEqual(c.w, 2000)
        self.assertEqual(c.t, 3000)

    def test_default_factory(self):
        # Test a factory that returns a new list.
        @dataclass
        class C:
            x: int
            y: list=field(default_factory=list)

        c0 = C(3)
        c1 = C(3)
        self.assertEqual(c0.x, 3)
        self.assertEqual(c0.y, [])
        self.assertEqual(c0, c1)
        self.assertIsNot(c0.y, c1.y)
        self.assertEqual(repr(C(5, [1])), 'C(x=5,y=[1])')

        # Test a factory that returns a shared list.
        l = []
        @dataclass
        class C:
            x: int
            y: list=field(default_factory=lambda: l)

        c0 = C(3)
        c1 = C(3)
        self.assertEqual(c0.x, 3)
        self.assertEqual(c0.y, [])
        self.assertEqual(c0, c1)
        self.assertIs(c0.y, c1.y)
        self.assertEqual(repr(C(5, [1])), 'C(x=5,y=[1])')

        # Test various other field flags.
        # repr
        @dataclass
        class C:
            x: list=field(default_factory=list, repr=False)
        self.assertEqual(repr(C()), 'C()')
        self.assertEqual(C().x, [])

        # hash
        @dataclass(hash=True)
        class C:
            x: list=field(default_factory=list, hash=False)
        self.assertEqual(repr(C()), 'C(x=[])')
        self.assertEqual(hash(C()), hash(()))

        # init (see also test_default_factory_with_no_init)
        @dataclass
        class C:
            x: list=field(default_factory=list, init=False)
        self.assertEqual(repr(C()), 'C(x=[])')

        # cmp
        @dataclass
        class C:
            x: list=field(default_factory=list, cmp=False)
        self.assertEqual(C(), C([1]))

    def test_default_factory_with_no_init(self):
        # We need a factory with a side effect.
        class Factory:
            def __init__(self):
                self.count = 0
            def incr(self):
                self.count += 1
                return self.count

        factory = Factory()

        @dataclass()
        class C:
            x: list=field(default_factory=factory.incr, init=False)

        # Make sure the default factory is called for each new instance.
        self.assertEqual(C().x, 1)
        self.assertEqual(C().x, 2)

    def test_default_factory_not_called_if_value_given(self):
        # We need a factory that we can test if it's been called.
        class Factory:
            def __init__(self):
                self.count = 0
            def incr(self):
                self.count += 1
                return self.count
        factory = Factory()

        @dataclass
        class C:
            x: int=field(default_factory=factory.incr)

        # Make sure that if a field has a default factory function,
        #  it's not called if a value is specified.
        self.assertEqual(C().x, 1)
        self.assertEqual(C(10).x, 10)
        self.assertEqual(C().x, 2)

    def x_test_classvar_default_factory(self):
        # XXX: it's an error for a ClassVar to have a factory function
        @dataclass
        class C:
            x: ClassVar[int] = field(default_factory=int)

        self.assertIs(C().x, int)

    def test_helper_fields_works_class_instance(self):
        # Check that we can call fields() on either a class or instance,
        #  and get back the same thing.
        @dataclass
        class C:
            x: int
            y: float

        self.assertIs(fields(C), fields(C(0, 0.0)))

    def test_helper_asdict(self):
        # Basic tests for asdict(), it should return a new dictionary
        @dataclass
        class C:
            x: int
            y: int
        c = C(1, 2)

        self.assertEqual(asdict(c), {'x': 1, 'y': 2})
        self.assertEqual(asdict(c), asdict(c))
        self.assertIsNot(asdict(c), asdict(c))
        c.x = 42
        self.assertEqual(asdict(c), {'x': 42, 'y': 2})
        self.assertIs(type(asdict(c)), dict)

    def test_helper_asdict_raises_on_classes(self):
        # asdict() should raise on a class object
        @dataclass
        class C:
            x: int
            y: int
        with self.assertRaisesRegex(ValueError, 'dataclass instance'):
            asdict(C)
        with self.assertRaisesRegex(ValueError, 'dataclass instance'):
            asdict(int)

    def test_helper_astuple(self):
        # Basic tests for astuple(), it should return a new tuple
        @dataclass
        class C:
            x: int
            y: int = 0
        c = C(1)

        self.assertEqual(astuple(c), (1, 0))
        self.assertEqual(astuple(c), astuple(c))
        self.assertIsNot(astuple(c), astuple(c))
        c.y = 42
        self.assertEqual(astuple(c), (1, 42))
        self.assertIs(type(astuple(c)), tuple)

    def test_helper_astuple_raises_on_classes(self):
        # astuple() should raise on a class object
        @dataclass
        class C:
            x: int
            y: int
        with self.assertRaisesRegex(ValueError, 'dataclass instance'):
            astuple(C)
        with self.assertRaisesRegex(ValueError, 'dataclass instance'):
            astuple(int)

    def test_dynamic_class_creation(self):
        cls_dict = {'__annotations__': OrderedDict(x=int, y=int),
                    }

        # Create the class.
        cls = type('C', (), cls_dict)

        # Make it a dataclass.
        cls1 = dataclass(cls)

        self.assertEqual(cls1, cls)
        self.assertEqual(asdict(cls(1, 2)), {'x': 1, 'y': 2})

    def test_dynamic_class_creation_using_field(self):
        cls_dict = {'__annotations__': OrderedDict(x=int, y=int),
                    'y': field(default=5),
                    }

        # Create the class.
        cls = type('C', (), cls_dict)

        # Make it a dataclass.
        cls1 = dataclass(cls)

        self.assertEqual(cls1, cls)
        self.assertEqual(asdict(cls1(1)), {'x': 1, 'y': 5})

    def test_init_in_order(self):
        @dataclass
        class C:
            a: int
            b: int = field()
            c: list = field(default_factory=list, init=False)
            d: list = field(default_factory=list)
            e: int = field(default=4, init=False)
            f: int = 4

        calls = []
        def setattr(self, name, value):
            calls.append((name, value))

        C.__setattr__ = setattr
        c = C(0, 1)
        self.assertEqual(('a', 0), calls[0])
        self.assertEqual(('b', 1), calls[1])
        self.assertEqual(('c', []), calls[2])
        self.assertEqual(('d', []), calls[3])
        self.assertNotIn(('e', 4), calls)
        self.assertEqual(('f', 4), calls[4])

    def test_items_in_dicts(self):
        @dataclass
        class C:
            a: int
            b: list = field(default_factory=list, init=False)
            c: list = field(default_factory=list)
            d: int = field(default=4, init=False)
            e: int = 0

        c = C(0)
        # Class dict
        self.assertNotIn('a', C.__dict__)
        self.assertNotIn('b', C.__dict__)
        self.assertNotIn('c', C.__dict__)
        self.assertIn('d', C.__dict__)
        self.assertEqual(C.d, 4)
        self.assertIn('e', C.__dict__)
        self.assertEqual(C.e, 0)
        # Instance dict
        self.assertIn('a', c.__dict__)
        self.assertEqual(c.a, 0)
        self.assertIn('b', c.__dict__)
        self.assertEqual(c.b, [])
        self.assertIn('c', c.__dict__)
        self.assertEqual(c.c, [])
        self.assertNotIn('d', c.__dict__)
        self.assertIn('e', c.__dict__)
        self.assertEqual(c.e, 0)

def main():
    unittest.main()


if __name__ == '__main__':
    main()
