# -*- coding: utf-8 -*-
"""
    FanFilm Add-on
    
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


import hashlib
import re
import time
import os

from ast import literal_eval

try:
    from sqlite3 import dbapi2 as db, OperationalError
except ImportError:
    from pysqlite2 import dbapi2 as db, OperationalError

from ptw.libraries import control, log_utils
from ptw.libraries.log_utils import log, fflog
from ptw.debug import log_exception, fflog_exc

data_path = control.dataPath


def get(function, duration, *args, output_type=None):
    """
    :param function: Function to be executed
    :param duration: Duration of validity of cache in hours
    :param args: Optional arguments for the provided function
    """
    try:
        key = _hash_function(function, args)
        # fflog(f'\n\n{key=}')
        cache_result = cache_get(key)
        if cache_result:
            # fflog(f'jest taki rekord w bazie cache')
            try:
                result = literal_eval(cache_result['value'])
            except Exception:
                result = None
                # fflog(f'jakiś błąd danych tego rekordu')
                fflog_exc(0)
            if _is_cache_valid(cache_result['date'], duration):
                # fflog(f"dane pobrane zostały z cache")
                if output_type == "tuple":
                    result = (result, True)
                return result
            else:
                # fflog(f"przeterminowany rekord, bo {duration=}  {cache_result.get('date')=}")
                pass
        else:
            # fflog('nie ma takiego pasującego rekordu w cache')
            pass

        # fflog(f'do wykonania: {function=}   {args=}')
        fresh_result = repr(function(*args))  # may need a try-except block for server timeouts
        # fflog(f'{fresh_result=}')

        if True:  # dodałem
            # fflog(f'wstawienie każdego wyniku do bazy')
            cache_insert(key, fresh_result)  # wstawienie do bazy
            return literal_eval(fresh_result)
        # czyli dalsza częśc kodu się nie wykonuje już
        if cache_result and (result and len(result) == 1) and fresh_result == '[]': # fix for syncSeason mark unwatched season when it's the last item remaining
            fflog(f'tutaj 1 {result[0]=}')
            if result[0].isdigit():  # dlaczego taki warunek?
            # if True:
                remove(function, *args)  # usunięcie rekordu z bazy cache
                fflog('tutaj 2')
                return []

        invalid = False
        try:  # Sometimes None is returned as a string instead of None type for "fresh_result"
            if not fresh_result:
                invalid = True
            elif fresh_result == 'None' or fresh_result == '' or fresh_result == '[]' or fresh_result == '{}':  # tylko, że czasami chcemy, aby wynik był [] czy {}, czyli to, co zwraca rzeczywiście funkcja
                invalid = True
            elif len(fresh_result) == 0:
                invalid = True
        except:
            pass
        fflog(f'{invalid=}')
        if invalid:  # If the cache is old, but we didn't get "fresh_result", return the old cache  # no i mi to właśnie psuło!
            if cache_result:
                fflog(f'zwrócenie poprzedniego wyniku')
                return result
            else:
                return None  # do not cache_insert() None type, sometimes servers just down momentarily  - A NIŻEJ jest wstawiane None - to dlaczego? Może kiedyś tak było (w dawniejszych czasach)
        else:
            if '404:NOT FOUND' in fresh_result:
                fflog(f'wstawienie pustego wyniku do bazy')
                cache_insert(key, None)  # cache_insert() "404:NOT FOUND" cases only as None type
                return None
            else:
                fflog(f'wstawienie wyniku do bazy')
                cache_insert(key, fresh_result)  # wstawienie do bazy
            return literal_eval(fresh_result)

    except Exception:
        from ptw.libraries import log_utils
        log_utils.log('Cache:', log_utils.LOGDEBUG)
        fflog_exc(1)
        return None


def timeout(function_, *args):
    try:
        key = _hash_function(function_, args)
        result = cache_get(key)
        time_out = int(result['date']) if result else 0
        # time_out = int(result["date"])
        # log_utils.log(f'{time_out=}')
        return time_out
    except Exception:
        return 0
        # return None


def cache_existing(function, *args):
    try:
        cache_result = cache_get(_hash_function(function, args))
        if cache_result:
            return literal_eval(cache_result['value'])
        else:
            return None
    except:
        from ptw.libraries import log_utils
        log_utils.log('Cache:', log_utils.LOGDEBUG)
        return None


def cache_get(key, db_path=None):
    # type: (str, str) -> dict or None
    try:
        cursor = _get_connection_cursor()
        cursor.execute('''SELECT * FROM cache WHERE key=?''', (key,))
        return cursor.fetchone()
    except OperationalError:
        # fflog_exc(1)
        return None


def cache_insert(key, value, db_path=None):
    # type: (str, str) -> None
    cursor = _get_connection_cursor()
    now = int(time.time())
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS cache (key TEXT, value TEXT, date INTEGER, UNIQUE(key))")

    update_result = cursor.execute(
        "UPDATE cache SET value=?,date=? WHERE key=?", (value, now, key)
    )

    if update_result.rowcount == 0:
        cursor.execute(
            "INSERT INTO cache Values (?, ?, ?)", (key, value, now)
        )

    cursor.connection.commit()


def remove(function, *args):
    try:
        key = _hash_function(function, args)
        key_exists = cache_get(key)
        if key_exists:
            dbcon = _get_connection()
            dbcur = _get_connection_cursor(dbcon)
            dbcur.execute('''DELETE FROM cache WHERE key=?''', (key,))
            dbcur.connection.commit()
    except:
        from ptw.libraries import log_utils
        log_utils.log('Cache:', log_utils.LOGDEBUG)
    try:
        dbcur.close()
        dbcon.close()
    except:
        pass


def cache_clear_old():
    try:
        cursor = _get_connection_cursor()

        for t in [cache_table, "rel_list", "rel_lib"]:
            try:
                cursor.execute("DROP TABLE IF EXISTS %s" % t)
                cursor.execute("VACUUM")
                cursor.commit()
            except:
                pass
        cache_clear_meta()
    except:
        pass


def cache_clear(flush_only=False):
    cleared = False
    dbcon = None
    try:
        dbcon = _get_connection()
        dbcur = _get_connection_cursor(dbcon)
        if flush_only:
            dbcur.execute('''DELETE FROM cache''')
            dbcur.connection.commit() # added this for what looks like a 19 bug not found in 18, normal commit is at end
            dbcur.execute('''VACUUM''')
            cleared = True
        else:
            dbcur.execute('''DROP TABLE IF EXISTS cache''')
            dbcur.execute('''VACUUM''')
            dbcur.connection.commit()
            cleared = True
    except:
        from ptw.libraries import log_utils
        log_utils.log('Cache:', log_utils.LOGDEBUG)
        cleared = False
    finally:
        if dbcon is not None:
            dbcon.close()
    #return cleared


def cache_clear_meta():
    try:
        cursor = _get_connection_cursor_meta()

        for t in ["meta"]:
            try:
                cursor.execute("DROP TABLE IF EXISTS %s" % t)
                cursor.execute("VACUUM")
                cursor.commit()
            except:
                pass
    except:
        pass


def cache_clear_providers():
    try:
        cursor = _get_connection_cursor_providers()

        for t in ["rel_src", "rel_url"]:
            try:
                cursor.execute("DROP TABLE IF EXISTS %s" % t)
                cursor.execute("VACUUM")
                cursor.commit()
            except:
                pass
    except:
        pass


def cache_clear_search(content=None):
    try:
        cursor = _get_connection_cursor_search()
        allowed_content = ["tvshow", "movies"]
        if content not in allowed_content:
            content = allowed_content
        else:
            content = [content]
        for t in content:
            try:
                cursor.execute("DROP TABLE IF EXISTS %s" % t)
                cursor.execute("VACUUM")
                cursor.commit()
            except:
                pass
    except Exception as e:
        log_utils.log(f"[cache_clear_search] Error: {e}")


def cache_clear_search_by_term(term_value, content=None):
    try:
        cursor = _get_connection_cursor_search()
        allowed_content = ["tvshow", "movies"]
        if content not in allowed_content:
            content = allowed_content
        else:
            content = [content]
        for t in content:
            cursor.execute("DELETE FROM %s WHERE term = ?" % t, (term_value,))
            cursor.connection.commit()
    except Exception as e:
        log_utils.log(f"[cache_clear_search_by_term] Error: {e}")


def cache_clear_all():
    cache_clear()
    cache_clear_meta()
    cache_clear_providers()


def _get_connection_cursor(conn=None):
    if conn is None:
        conn = _get_connection()
    return conn.cursor()


def _get_connection():
    if not control.existsPath(control.dataPath):
        control.makeFile(control.dataPath)
    dbcon = db.connect(control.cacheFile, timeout=60) # added timeout 3/23/21 for concurrency with threads
    dbcon.execute('''PRAGMA page_size = 32768''')
    dbcon.execute('''PRAGMA journal_mode = OFF''')
    dbcon.execute('''PRAGMA synchronous = OFF''')
    dbcon.execute('''PRAGMA temp_store = memory''')
    dbcon.execute('''PRAGMA mmap_size = 30000000000''')
    dbcon.row_factory = _dict_factory
    return dbcon


def _get_connection_cursor_meta():
    conn = _get_connection_meta()
    return conn.cursor()


def _get_connection_meta():
    control.makeFile(data_path)
    conn = db.connect(os.path.join(data_path, control.metacacheFile))
    conn.row_factory = _dict_factory
    return conn


def _get_connection_cursor_providers():
    conn = _get_connection_providers()
    return conn.cursor()


def _get_connection_providers():
    control.makeFile(data_path)
    conn = db.connect(os.path.join(data_path, control.providercacheFile))
    conn.row_factory = _dict_factory
    return conn


def _get_connection_cursor_search():
    conn = _get_connection_search()
    return conn.cursor()


def _get_connection_search():
    control.makeFile(data_path)
    conn = db.connect(os.path.join(data_path, control.searchFile))
    conn.row_factory = _dict_factory
    return conn


def _dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def _hash_function(function_instance, *args):
    return _get_function_name(function_instance) + _generate_md5(args)


def _get_function_name(function_instance):
    return re.sub(
        r".+\smethod\s|.+function\s|\sat\s.+|\sof\s.+", "", repr(function_instance)
    )


def _generate_md5(*args):
    md5_hash = hashlib.md5()
    try:
        [md5_hash.update(str(arg)) for arg in args]
    except:
        [md5_hash.update(str(arg).encode('utf-8')) for arg in args]
    return str(md5_hash.hexdigest())


def _is_cache_valid(cached_time, cache_timeout):
    now = int(time.time())
    diff = now - cached_time
    return (cache_timeout * 3600) > diff


def get_old(function_, duration, *args, **table):

    try:
        response = None

        f = repr(function_)
        f = re.sub(r".+\smethod\s|.+function\s|\sat\s.+|\sof\s.+", "", f)

        a = hashlib.md5()
        for i in args:
            try:
                a.update(str(i))
            except:
                a.update(str(i).encode('utf-8'))
        a = str(a.hexdigest())
    except Exception:
        pass

    try:
        table = table["table"]
    except Exception:
        table = "rel_list"

    try:
        control.makeFile(control.dataPath)
        dbcon = db.connect(control.cacheFile)
        dbcur = dbcon.cursor()
        dbcur.execute(
            "SELECT * FROM {tn} WHERE func = '{f}' AND args = '{a}'".format(
                tn=table, f=f, a=a
            )
        )
        match = dbcur.fetchone()

        try:
            response = literal_eval(match[2].encode("utf-8"))
        except AttributeError:
            response = literal_eval(match[2])

        t1 = int(match[3])
        t2 = int(time.time())
        update = (abs(t2 - t1) / 3600) >= int(duration)
        if not update:
            return response
    except Exception:
        pass

    try:
        r = function_(*args)
        if (r is None or r == []) and response is not None:
            return response
        elif r is None or r == []:
            return r
    except Exception:
        return

    try:
        r = repr(r)
        t = int(time.time())
        dbcur.execute(
            "CREATE TABLE IF NOT EXISTS {} ("
            "func TEXT, "
            "args TEXT, "
            "response TEXT, "
            "added TEXT, "
            "UNIQUE(func, args)"
            ");".format(table)
        )
        dbcur.execute(
            "DELETE FROM {0} WHERE func = '{1}' AND args = '{2}'".format(table, f, a)
        )
        dbcur.execute("INSERT INTO {} Values (?, ?, ?, ?)".format(table), (f, a, r, t))
        dbcon.commit()
    except Exception:
        pass

    try:
        return literal_eval(r.encode("utf-8"))
    except Exception:
        return literal_eval(r)


def _get_connection_old():
    control.makeFile(data_path)
    conn = db.connect(os.path.join(data_path, "cache.db"))
    conn.row_factory = _dict_factory
    return conn
