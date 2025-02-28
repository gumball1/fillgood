# -*- coding: utf-8 -*-

"""
    FanFilm Add-on
    Copyright (C) 2024 FanFilm

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import pkgutil

from ptw.libraries import log_utils
# from ptw.debug import log_exception, fflog_exc, fflog


def sources(provider="", language=None):
    try:
        __all__ = [x[1] for x in os.walk(os.path.dirname(__file__))][0]  # ['en', 'pl', '__pycache__']

        if language:
            if isinstance(language, str):
                __all__ = [f for f in __all__ if language in f]
            else:  # list, tuple
                __all__ = [f for f in __all__ for l in language if l in f]
            # log_utils.log(f'[__init__.py] {__all__=}', 1)  # np. tylko ['pl']
        sourceDict = []

        for i in __all__:
            for loader, module_name, is_pkg in pkgutil.walk_packages([os.path.join(os.path.dirname(__file__), i)]):
                # fflog(f'{loader=} {module_name=}  {is_pkg=}')
                if is_pkg:  # nie wiem co to oznacza, ale wszystkie scrapery mają False
                    continue
                if provider and module_name != provider:
                    continue
                try:
                    # module = loader.find_module(module_name).load_module(module_name)  # The `find_module` method was deprecated in Python 3.4 and removed in Python 3.12.
                    module = loader.find_spec(module_name).loader.load_module(module_name)  # The new import system uses `find_spec` instead.  https://community.cloudera.com/t5/Support-Questions/Correct-python-version-for-python-extension/td-p/387962#
                    sourceDict.append( (module_name, module.source(),) )
                    # sourceDict.append( (module_name, os.path.join(loader, module_name) ) )  # taka próba innego podejścia, ale chyba nie będzie to wykorzystane
                except Exception as e:
                    if not(module_name == 'library' and i == 'en'):
                        print("Module error: " + module_name)
                        log_utils.log('[__init__.py] Provider loading Error - "%s" from [%s]: %s' % (module_name, i, e), log_utils.LOGWARNING, )
                    else:
                        # log_utils.log('[__init__.py] "library.py" z folderu "en" przeniosłem do źródeł PL', 0)
                        pass
        # log_utils.log(f'[__init__.py] {len(sourceDict)=}', 1)
        return sourceDict
    except Exception:
        # fflog_exc(1)
        return []
