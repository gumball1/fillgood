# Force patching Kodi API
from kover import autoinstall  # noqa: F401
# Basic logging.
from .libraries.log_utils import log  # noqa: F401

import sys
PY2 = sys.version_info < (3, 0)


# Monkey-patching datetime.strptime
# see: https://forum.kodi.tv/showthread.php?tid=112916&pid=2953239
# see: https://bugs.python.org/issue27400
import datetime as datetime_module            # noqa: E402
from datetime import datetime as _datetime    # noqa: E402

if not getattr(datetime_module, '_datetime_is_patched', False):
    class datetime(_datetime):
        @classmethod
        def strptime(cls, date_string: str, format: str) -> _datetime:
            # log(f"Monkey-patching datetime.strptime  {date_string=}", 1)
            try:
                return _dt_strptime(date_string, format)
            except TypeError:
                import time
                return datetime(*(time.strptime(date_string, format)[0:6]))

    _dt_strptime = _datetime.strptime
    datetime_module.datetime = datetime
    datetime_module._datetime = _datetime
    datetime_module._datetime_is_patched = True

