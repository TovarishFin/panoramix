import logging

from panoramix.core.arithmetic import is_zero
from panoramix.matcher import Any, match
from panoramix.prettify import (
    explain,
)
from panoramix.simplify import simplify_trace
from panoramix.utils.helpers import (
    find_f_list,
    opcode,
    replace,
    rewrite_trace,
)

logger = logging.getLogger(__name__)
logger.level = logging.CRITICAL  # switch to INFO for detailed

"""

    Rube Goldberg would be proud.

"""


def make_whiles(trace):
    trace = make(trace)
    explain("Loops -> whiles", trace)

    # clean up jumpdests
    trace = rewrite_trace(
        trace, lambda line: [] if opcode(line) == "jumpdest" else [line]
    )
    trace = simplify_trace(trace)

    return trace


"""

    make whiles

"""


def make(trace):
    res = []

    for idx, line in enumerate(trace):
        if m := match(line, ("if", ":cond", ":if_true", ":if_false")):
            res.append(("if", m.cond, make(m.if_true), make(m.if_false)))

        elif m := match(line, ("label", ":jd", ":vars", ...)):
            jd, vars = m.jd, m.vars
            try:
                before, inside, remaining, cond = to_while(trace[idx + 1 :], jd)
            except Exception:
                continue

            inside = inside  # + [str(inside)]

            inside = make(inside)
            remaining = make(remaining)

            for _, v_idx, v_val in vars:
                before = replace(before, ("var", v_idx), v_val)
            before = make(before)

            res.extend(before)
            res.append(("while", cond, inside, repr(jd), vars))
            res.extend(remaining)

            return res

        elif m := match(line, ("goto", ":jd", ":setvars")):
            res.append(("continue", repr(m.jd), m.setvars))

        else:
            res.append(line)

    return res


def get_jds(line):
    if m := match(line, ("goto", ":jd", ...)):
        return [m.jd]
    return []


def is_revert(trace):
    if len(trace) > 1:
        return False

    line = trace[0]
    return (line == ("return", 0)) or (opcode(line) in ("revert", "invalid"))


def to_while(trace, jd, path=None):
    path = path or []

    while True:
        if trace == []:
            raise
        line = trace[0]
        trace = trace[1:]

        if m := match(line, ("if", ":cond", ":if_true", ":if_false")):
            cond, if_true, if_false = m.cond, m.if_true, m.if_false
            if is_revert(if_true):
                path.append(("require", is_zero(cond)))
                trace = if_false
                continue

            if is_revert(if_false):
                path.append(("require", cond))
                trace = if_true
                continue

            jds_true = find_f_list(if_true, get_jds)
            jds_false = find_f_list(if_false, get_jds)

            assert (jd in jds_true) != (jd in jds_false), (jds_true, jds_false)

            def add_path(line):
                if m := match(line, ("goto", Any, ":svs")):
                    path2 = path
                    for _, v_idx, v_val in m.svs:
                        path2 = replace(path2, ("var", v_idx), v_val)

                    return path2 + [line]
                else:
                    return [line]

            if jd in jds_true:
                if_true = rewrite_trace(if_true, add_path)
                return path, if_true, if_false, cond
            else:
                if_false = rewrite_trace(if_false, add_path)
                return path, if_false, if_true, is_zero(cond)

        else:
            path.append(line)

    assert False, f"no if after label?{jd}"
