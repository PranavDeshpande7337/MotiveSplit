"""Parse an agent reply into a decision. Never clamps: out-of-range or absent integers are parse_failed."""
import re

import config

_INT_FIELD = re.compile(r"^(-?\d+)\.?$")        # whole field must be one integer (optional trailing full stop)
_ANY_INT = re.compile(r"(?<![\w.])-?\d+(?!\w|\.\d)")


def _result(decision, flags, reason, error=None):
    return {"decision": decision, "flags": flags, "reason": reason.strip(), "parse_error": error}


def _check_range(value, flags, reason):
    if 0 <= value <= config.ENDOWMENT:
        return _result(value, flags, reason)
    return _result(None, flags + ["parse_failed"], reason, "out_of_range")


def parse_reply(reply):
    tag = config.DECISION_TAG
    pos = reply.rfind(tag)

    if pos == -1:                                   # fallback: whole reply, last standalone integer
        flags = ["tags_missing"]
        found = _ANY_INT.findall(reply)
        if not found:
            return _result(None, flags + ["parse_failed"], reply, "no_integer")
        return _check_range(int(found[-1]), flags, reply)

    reason = reply[:pos]
    section = reply[pos + len(tag):]
    section = section.lstrip()
    if section[:1] == ":" or (section[:1] == "-" and not section[1:2].isdigit()):
        section = section[1:]                       # leading ':' or '-' separator; '-3' stays a negative number
    lines = [ln.strip() for ln in section.splitlines() if ln.strip()]
    if not lines:
        return _result(None, ["parse_failed"], reason, "no_integer")
    field = lines[0]
    m = _INT_FIELD.match(field)
    if not m:
        return _result(None, ["parse_failed"], reason, "non_integer" if re.search(r"\d", field) else "no_integer")
    return _check_range(int(m.group(1)), [], reason)