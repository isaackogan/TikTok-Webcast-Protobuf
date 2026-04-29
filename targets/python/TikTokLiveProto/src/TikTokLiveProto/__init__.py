"""Python betterproto bindings for the TikTok Webcast protobuf schema."""

import sys as _sys
from importlib import import_module as _import_module

v1 = _import_module(".generated.v1", __name__)
_sys.modules[__name__ + ".v1"] = v1
v2 = _import_module(".generated.v2", __name__)
_sys.modules[__name__ + ".v2"] = v2

__all__ = [
    "v1",
    "v2",
]
