import ast
import numpy as np
import warnings

cache = {}


def constant_value(constant):
    return lambda v_min, v_max, size: constant * np.ones(size)


def dyn_rules(func, f_min=0, f_max=1200):
    def rule(text):
        def values(size):
            (v_min, v_max, type_name) = get_values(text)
            if type_name not in ["QF", "AGE"]:
                warnings.warn(f"{type_name} missing…")
            if v_min == None:
                v_min = f_min
            if v_max == None:
                v_max = f_max
            return func(v_min, v_max, size)

        return values

    return rule


def get_values(text):
    if text not in cache:
        cache[text] = compute(text)

    return cache[text]


def compute(text):
    p = ast.parse(text)
    assert len(p.body) == 1
    e = p.body[0]

    min_v = None
    min_operator = None
    max_v = None
    max_operator = None
    if type(e.value) == ast.Name:
        variable_name = e.value.id
    elif len(e.value.ops) == 2:
        min_v = e.value.left.value
        min_operator = e.value.ops[0]

        max_v = e.value.comparators[1].value
        max_operator = e.value.ops[1]

        variable_name = e.value.comparators[0].id
    elif type(e.value.ops[0]) == ast.Eq:
        if type(e.value.comparators[0]) == ast.Name:
            variable_name = e.value.comparators[0].id
            min_v = e.value.left.value
        else:
            variable_name = e.value.left.id
            min_v = e.value.comparators[0].value
        max_v = min_v + 1
    else:
        if type(e.value.comparators[0]) == ast.Name:
            variable_name = e.value.comparators[0].id
            min_v = e.value.left.value
            min_operator = e.value.ops[0]
        else:
            variable_name = e.value.left.id
            max_v = e.value.comparators[0].value
            max_operator = e.value.ops[0]

    if min_operator and type(min_operator) == ast.Lt:
        min_v += 1
    if max_operator and type(max_operator) == ast.LtE:
        max_v += 1

    return (min_v, max_v, variable_name)


def test_simple():
    assert compute("0<=QF<40") == (0, 40, "QF")


def test_shift_max():
    assert compute("0<=QF<=40") == (0, 41, "QF")


def test_shift_min():
    assert compute("0<QF<40") == (1, 40, "QF")


def test_single_min():
    assert compute("0<=QF") == (0, None, "QF")


def test_single_max():
    assert compute("QF<40") == (None, 40, "QF")


def test_equal():
    assert compute("QF==0") == (0, 1, "QF")


def test_unconstraint():
    assert compute("QF") == (None, None, "QF")


def test_tuple():
    assert compute("QF({'21':12})") == (None, None, "QF")


def test_cache():
    res = get_values("QF<40")
    res_cached = get_values("QF<40")
    res_new = compute("QF<40")

    assert id(res_cached) == id(res)
    assert res_new == res
    assert id(res_new) != id(res)
