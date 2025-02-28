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

import ast
import datetime
import json
import os
import re
import sys
import urllib
from sqlite3 import dbapi2 as database

from past.builtins import basestring

try:
    import urllib.parse as urllib
except:
    pass

import xbmc, xbmcvfs
from ptw.libraries import cleantitle
from ptw.libraries import control
from ptw.libraries import cache
from ptw.libraries.log_utils import log, fflog
from ptw.debug import log_exception, fflog_exc


class lib_tools:
    @staticmethod
    def create_folder(folder):
        try:
            folder = xbmcvfs.makeLegalFilename(folder)
            control.makeFile(folder)  # xbmcvfs.mkdir
            if "ftp://" in folder:
                try:
                    from ftplib import FTP
                    ftparg = re.compile(r"ftp://(.+?):(.+?)@(.+?):?(\d+)?/(.+/?)").findall(folder)
                    ftp = FTP(ftparg[0][2], ftparg[0][0], ftparg[0][1])
                    try:
                        ftp.cwd(ftparg[0][4])
                    except:
                        ftp.mkd(ftparg[0][4])
                    ftp.quit()
                except Exception:
                    fflog_exc(1)
                    pass
        except Exception:
            fflog_exc(1)
            pass

    @staticmethod
    def write_file(path, content):
        try:
            path = xbmcvfs.makeLegalFilename(path)
            if not isinstance(content, basestring):
                content = str(content)
            file = control.openFile(path, "w")
            file.write(str(content))
            file.close()
        except Exception as e:
            fflog_exc(1)
            pass

    @staticmethod
    def nfo_url(media_string, ids):
        tvdb_url = "http://thetvdb.com/?tab=series&id=%s"
        tmdb_url = "https://www.themoviedb.org/%s/%s"
        imdb_url = "http://www.imdb.com/title/%s/"
        if "tvdb" in ids:
            return tvdb_url % (str(ids["tvdb"]))
        elif "tmdb" in ids:
            return tmdb_url % (media_string, str(ids["tmdb"]))
        elif "imdb" in ids:
            return imdb_url % (str(ids["imdb"]))
        else:
            return ""

    @staticmethod
    def check_sources(
        title,
        localtitle,
        year,
        imdb,
        tvdb=None,
        tmdb=None,
        season=None,
        episode=None,
        tvshowtitle=None,
        premiered=None,
    ):
        try:
            from ptw.libraries import sources
            src = sources.sources().getSources(title, localtitle, year, imdb, tvdb, tmdb, season, episode, tvshowtitle, premiered)
            return src and len(src) > 5
        except Exception:
            fflog_exc(1)
            return False

    @staticmethod
    def legal_filename(filename):
        #fflog(f'{filename=}')
        filename = filename.strip()
        filename = re.sub(r"(?!%s)[^\w\-_\.]", " ", filename)  # wcześniej była kropka
        filename = re.sub(r"\.+", ".", filename)
        filename = re.sub(re.compile(r"(CON|PRN|AUX|NUL|COM\d|LPT\d)\.", re.I), "\\1_", filename)
        filename = filename.strip(". ")  # kropka nie może być na początku
        xbmcvfs.makeLegalFilename(filename)
        return filename

    @staticmethod
    def make_path(base_path, title, year="", season=""):
        #fflog(f'{base_path=} {title=}')
        show_folder = re.sub(r"[^\w\-_\. ]", " ", title)  # wcześniej była podłoga
        show_folder = show_folder.strip("._ ")
        show_folder = "%s (%s)" % (show_folder, year) if year else show_folder
        path = os.path.join(base_path, show_folder)
        if season:
            path = os.path.join(path, "Season %s" % season)
        return path



class libmovies:  # filmy
    def __init__(self):
        self.library_folder = os.path.join( control.transPath(control.setting("library.movie")), "" )
        self.check_setting = control.setting("library.check_movie") or "false"
        self.library_setting = control.setting("library.update") or "true"
        self.dupe_setting = control.setting("library.check") or "true"
        self.silentDialog = False
        self.infoDialog = False


    def add(self, name, title, localtitle, year, imdb, tmdb, range=False):
        fflog(f'próba dodania filmu do biblioteki \n {name=} {title=} {year=} {imdb=} {tmdb=} {range=}', 0)
        if (
            not control.condVisibility("Window.IsVisible(infodialog)")
            and not control.condVisibility("Player.HasVideo")
            and self.silentDialog is False
        ):
            control.infoDialog(control.lang(32552).encode("utf-8"), time=10000000)  # Adding to library...
            self.infoDialog = True
            message = ""

        lib = []
        if self.dupe_setting == "true":
            try:
                # fflog('sprawdzenie, czy tytuł nie jest już w bibliotece')
                id = [imdb, tmdb] if not tmdb == "0" else [imdb]
                lib = control.jsonrpc(
                    '{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": {"filter":{"or": [{"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}]}, "properties" : ["imdbnumber", "originaltitle", "year"]}, "id": 1}'
                    % (year, str(int(year) + 1), str(int(year) - 1))
                )
                lib = json.loads(lib)["result"]["movies"]
                lib = [
                    i
                    for i in lib
                    if str(i["imdbnumber"]) in id
                    or (i["originaltitle"] == title and str(i["year"]) == year)
                ]
                lib = lib[0] if lib else []
            except Exception:
                fflog_exc(1)
                pass

        files_added = 0

        if not lib:
            try:
                if self.check_setting == "true":
                    if self.infoDialog:
                        control.infoDialog("sprawdzenie, czy są źródła", time=5000)
                    src = lib_tools.check_sources(title, localtitle, year, imdb)
                    if not src:
                        message = 'weryfikacja negatywna (brak źródeł)'
                        fflog(message)
                        raise Exception()
                # fflog('można dodać', 0)
                self.strmFile({"name": name, "title": title, "localtitle": localtitle, "year": year, "imdb": imdb, "tmdb": tmdb})
                files_added += 1
            except Exception:
                fflog(1)
                pass
        else:
            message = f'pozycja jest już w bibliotece \n {title=} {year=}'
            fflog(message)

        if range:  # to przy kilku tytułach naraz chyba
            return

        if self.infoDialog:
            message = control.lang(32554) if not message else message
            control.infoDialog(message, time=2500)  # Process Complete or other error message

        if (
            self.library_setting == "true"
            and not control.condVisibility("Library.IsScanningVideo")
            and files_added > 0
        ):
            control.execute("UpdateLibrary(video)")
        else:
            # fflog('koniec dodawania filmu')
            pass


    def silent(self, url):
        if not control.condVisibility("Window.IsVisible(infodialog)") and not control.condVisibility("Player.HasVideo"):
            control.infoDialog(control.lang(32552), time=10000000)  # Adding to library...
            self.infoDialog = True
            self.silentDialog = True

        # fflog('pobranie informacji o filmie z internetu')
        from resources.lib.indexers import movies
        items = movies.movies().get(url, idx=False)

        if items is None:
            items = []

        monitor = xbmc.Monitor()

        fflog(f'{len(items)=}',1,1)
        for i in items:
            try:
                if monitor.abortRequested():
                    return sys.exit()
                    
                self.add(
                    "%s (%s)" % (i["originaltitle"], i["year"]),
                    i["originaltitle"],
                    i["title"],
                    i["year"],
                    i["imdb"],
                    i["tmdb"],
                    range=True,
                )
            except:
                pass

        if self.infoDialog:
            self.silentDialog = False
            control.infoDialog("Skończono synchronizację filmów", time=1)
            
        if self.library_setting == "true" and not control.condVisibility("Library.IsScanningVideo"):
            control.execute("UpdateLibrary(video)")
        else:
            fflog('ukończono synchronizację filmów')
            pass


    def range(self, url):
        yes = control.yesnoDialog(control.lang(32555))
        if not yes:
            return

        if not control.condVisibility("Window.IsVisible(infodialog)") and not control.condVisibility("Player.HasVideo"):
            control.infoDialog(control.lang(32552), time=10000000)  # Adding to library...
            self.infoDialog = True

        # fflog('pobranie informacji o filmach z internetu')
        from resources.lib.indexers import movies
        items = movies.movies().get(url, idx=False)
        if items is None:
            items = []

        monitor = xbmc.Monitor()

        fflog(f'{len(items)=}',1,1)
        for i in items:
            try:
                if monitor.abortRequested():
                    return sys.exit()
                self.add(
                    "%s (%s)" % (i["originaltitle"], i["year"]),
                    i["originaltitle"],
                    i["title"],
                    i["year"],
                    i["imdb"],
                    i["tmdb"],
                    range=True,
                )
            except:
                pass

        if self.infoDialog:
            control.infoDialog(control.lang(32554), time=1)  # Process Complete

        if self.library_setting == "true" and not control.condVisibility("Library.IsScanningVideo"):
            control.execute("UpdateLibrary(video)")
        else:
            # fflog('koniec funkcji "range" dla filmów')
            pass


    def multi(self, select):
        list = ast.literal_eval(cache.cache_get(select)["value"])
        choice = [f'{i["title_multi"]} ({i["year"]})'.replace(" ()","") for i in list]
        select = control.dialog.multiselect("Wybierz tytuły", choice)
        if not select:
            return
        # items = [list[i] for i in select]
        yes = control.yesnoDialog(control.lang(32555))  # potwierdzenie, czy kontynuować
        if not yes:
            return

        if not control.condVisibility("Window.IsVisible(infodialog)") and not control.condVisibility("Player.HasVideo"):
            control.infoDialog(control.lang(32552), time=10000000)  # Adding to library...
            self.infoDialog = True

        items = [list[i] for i in select] or None

        if items is None:
            items = []

        monitor = xbmc.Monitor()

        fflog(f'{len(items)=}',1,1)
        for i in items:
            try:
                if monitor.abortRequested():
                    return sys.exit()
                self.add(
                    "%s (%s)" % (i["title"], i["year"]),
                    i["title"],
                    i["title_multi"],
                    i["year"],
                    i["imdb"],
                    i["tmdb"],
                    range=True,
                )
            except:
                pass

        if self.infoDialog:
            control.infoDialog(control.lang(32554), time=1)  # Process Complete

        if self.library_setting == "true" and not control.condVisibility("Library.IsScanningVideo"):
            control.execute("UpdateLibrary(video)")
        else:
            # fflog('koniec dodawania wielu filmów do biblioteki')
            pass


    def strmFile(self, i):
        try:
            name, title, localtitle, year, imdb, tmdb = (
                i["name"],
                i["title"],
                i["localtitle"],
                i["year"],
                i["imdb"],
                i["tmdb"],
            )
            if year == "None" or year is None:
                year = ""

            sysname = urllib.quote_plus(name)
            systitle = urllib.quote_plus(title)
            syslocaltitle = urllib.quote_plus(localtitle)
            if control.setting("library.localtitles_for_filenames") == "true" and localtitle:
                #transtitle = cleantitle.normalize(localtitle.translate({ord(c): "" for c in r'\/:*?"<>|'}))
                transtitle = localtitle.translate({ord(c): "" for c in r'\/:*?"<>|'})
            else:
                #transtitle = cleantitle.normalize(title.translate({ord(c): "" for c in r'\/:*?"<>|'}))
                transtitle = title.translate({ord(c): "" for c in r'\/:*?"<>|'})

            content = "%s?action=play&name=%s&title=%s&localtitle=%s&year=%s&imdb=%s&tmdb=%s" % (
                sys.argv[0],
                sysname,
                systitle,
                syslocaltitle,
                year,
                imdb if imdb else "",
                tmdb if tmdb else "",
            )

            folder = lib_tools.make_path(self.library_folder, transtitle, year)

            lib_tools.create_folder(folder)
            filename = lib_tools.legal_filename(transtitle) + f" ({year}).strm"
            filename = filename.replace(" ()", "")  # jakby nie było roku
            lib_tools.write_file(os.path.join(folder, filename), content,)
            lib_tools.write_file(os.path.join(folder, "movie.nfo"), lib_tools.nfo_url("movie", i))
        except Exception:
            fflog_exc(1)
            pass



#PO ZMIANIE SUPER_INFO PAMIĘTAĆ O TYTUŁACH!
class libtvshows:
    def __init__(self):
        self.library_folder = os.path.join(control.transPath(control.setting("library.tv")), "")
        self.version = control.version()
        self.check_setting = control.setting("library.check_episode") or "false"
        self.include_unknown = control.setting("library.include_unknown") or "true"
        # self.include_future = control.setting("library.include_future") or "false"
        self.delay_before_add = int(control.setting("library.delay_before_add")) or 0
        self.library_setting = control.setting("library.update") or "true"
        self.dupe_setting = control.setting("library.check") or "true"
        self.datetime = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
        self.date = (self.datetime - datetime.timedelta(hours=6)).strftime("%Y%m%d")  # dzisiejsza data
        self.silentDialog = False
        self.infoDialog = False
        self.block = False


    def add(
        self,
        tvshowtitle,
        year,
        imdb,
        tmdb,
        season=None,
        episode=None,
        meta=None,
        range=False,
        localtvshowtitle="",
    ):
        fflog(f'próba dodania do biblioteki serialu \n{tvshowtitle=} {year=} {imdb=} {tmdb=} {season=} {episode=} {range=} {localtvshowtitle=}', 0)
        if (
            not control.condVisibility("Window.IsVisible(infodialog)")
            and not control.condVisibility("Player.HasVideo")
            and self.silentDialog is False
        ):
            control.infoDialog(control.lang(32552), time=10000000)  # Adding to library...
            self.infoDialog = True

        message = ""

        # fflog(f'pobranie informacji o odcinkach serialu z internetu  {tvshowtitle=} {year=}')
        from resources.lib.indexers import episodes
        items = episodes.episodes().get(tvshowtitle, year, imdb, tmdb, season, episode, meta, localtvshowtitle=localtvshowtitle, idx=False)

        # fflog(f'{len(items)=}',1,1)

        try:
            items = [
                {
                    "title": i["title"],
                    "year": i["year"],
                    "imdb": i["imdb"],
                    "tmdb": i["tmdb"],
                    "season": i["season"],
                    "episode": i["episode"],
                    "tvshowtitle": i["tvshowtitle"],
                    "localtvshowtitle": i["localtvshowtitle"],
                    "premiered": i["premiered"],
                }
                for i in items
            ]
        except Exception:
            items = []

        lib = None
        try:
            if not items:
                message = f'nie udało się pobrać informacji o serialu i odcinkach z internetu'
                fflog(message)
                raise Exception(f'{items=}')

            if not self.dupe_setting == "true":
                fflog(f'NIE sprawdzam istnienia odcinków w bibliotece')
                # NIE sprawdzam w lokalnej bazie, ale możliwe, że mam z internetu
                raise Exception()

            id = [items[0]["imdb"], items[0]["tmdb"]]

            lib = control.jsonrpc(
                '{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "params": {"properties" : ["imdbnumber", "title", "year"]}, "id": 1}'
            )
            lib = json.loads(lib)["result"]["tvshows"]
            lib = [
                i["title"]
                for i in lib
                if str(i["imdbnumber"]) in id
                or (
                    i["title"] == items[0]["tvshowtitle"]
                    and str(i["year"]) == items[0]["year"]
                )
            ][0]
            # pobranie listy odcinków
            lib = control.jsonrpc(
                '{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": {"filter":{"and": [{"field": "tvshow", "operator": "is", "value": "%s"}]}, "properties": ["season", "episode"]}, "id": 1}'
                % lib
            )
            lib = json.loads(lib)["result"]["episodes"]
            lib = ["S%02dE%02d" % (int(i["season"]), int(i["episode"])) for i in lib]
            # ustalenie listy odcinków, których jeszcze nie ma w bibliotece
            items = [
                i
                for i in items
                if not "S%02dE%02d" % (int(i["season"]), int(i["episode"])) in lib
            ]
            if items:
                fflog(f'ustalono listę odcinków, których jeszcze nie ma w bibliotece')
                pass
            else:
                fflog(f'brak brakujących odcinków do dodania')
                pass
        except Exception:
            #fflog_exc(1)
            pass

        files_added = 0
        monitor = xbmc.Monitor()
        
        # fflog(f'{len(items)=}',1,1)
        for i in items:  # odcinki do sprawdzenia
            try:
                if monitor.abortRequested():
                    return sys.exit()

                if self.check_setting == "true":
                    if i["episode"] == "1":  # tylko dla 1 odcinka (ale każdego sezonu)
                        message = f'sprawdzenie, czy są źródła\n sezon: {i["season"]}  odc. {i["episode"]}'
                        fflog(message)
                        if self.infoDialog:
                            control.infoDialog(message, time=5000)
                        self.block = True
                        src = lib_tools.check_sources(
                            i["title"],
                            i.get("localtitle", ""),
                            i["year"],
                            i["imdb"],
                            i.get("tvdb"),
                            i["tmdb"],
                            i["season"],
                            i["episode"],
                            i["tvshowtitle"],
                            i["premiered"],
                        )
                        if src:
                            self.block = False
                            message = ""
                    if self.block:
                        message = f'weryfikacja negatywna (brak źródeł)'
                        fflog(message + f'{i["tvshowtitle"]=}')
                        raise Exception()

                premiered = i.get("premiered", "0")
                if ((
                     premiered != "0"
                     and ( (prem := int(re.sub("[^0-9]", "", str(premiered)))) > int(self.date)  # jeszcze niewyemitowany (znana data premiery)
                          # and self.include_future != "true"
                          or self.delay_before_add and (prem > (int(self.date) - int(self.delay_before_add)))
                        )
                    )
                    or (premiered == "0" and not self.include_unknown == "true")  # brak informacji o premierze
                    ):
                    fflog(f'pomijam odcinek  {i["season"]=} {i["episode"]=}  {premiered=}  ({self.include_unknown=}  {self.delay_before_add=})')
                    continue
                fflog(f'dodaję odcinek {i["season"]=} {i["episode"]=}', 0)
                self.strmFile(i)  # utworzenie pliku strm na dysku dla odcinka
                files_added += 1
            except Exception:
                # fflog_exc(1)
                pass

        if range:
            return

        if self.infoDialog is True:
            message = control.lang(32554) if not message else message
            control.infoDialog(message, time=2500)  # Process Complete or other message error

        if (
            self.library_setting == "true"
            and not control.condVisibility("Library.IsScanningVideo")
            and files_added > 0
        ):
            control.execute("UpdateLibrary(video)")
        else:
            # fflog('koniec dodawania serialu do biblioteki')
            pass


    def silent(self, url):
        if not control.condVisibility("Window.IsVisible(infodialog)") and not control.condVisibility("Player.HasVideo"):
            control.infoDialog(control.lang(32608), time=10000000)  # Auto Syncing Trakt Library
            self.infoDialog = True
            self.silentDialog = True

        # fflog(f'pobranie informacji o serialach z internetu')
        from resources.lib.indexers import tvshows
        items = tvshows.tvshows().get(url, idx=False)

        if items is None:
            items = []

        monitor = xbmc.Monitor()

        fflog(f'{len(items)=}',1,1)
        for i in items:
            try:
                if monitor.abortRequested():
                    return sys.exit()
                self.add(i["originaltitle"], i["year"], i["imdb"], i["tmdb"], range=True)
            except Exception:
                pass

        if self.infoDialog is True:
            self.silentDialog = False
            control.infoDialog("Skończono synchronizację seriali", time=1)

        if self.library_setting == "true" and not control.condVisibility("Library.IsScanningVideo"):
            control.execute("UpdateLibrary(video)")
        else:
            # fflog("Skończono synchronizację seriali")
            pass


    def range(self, url):
        yes = control.yesnoDialog(control.lang(32555))
        if not yes:
            return

        if not control.condVisibility("Window.IsVisible(infodialog)") and not control.condVisibility("Player.HasVideo"):
            control.infoDialog(control.lang(32552), time=10000000)  # Adding to library...
            self.infoDialog = True

        # fflog(f'pobranie informacji o serialach z internetu')
        from resources.lib.indexers import tvshows
        items = tvshows.tvshows().get(url, idx=False)

        if items is None:
            items = []

        monitor = xbmc.Monitor()

        fflog(f'{len(items)=}',1,1)
        for i in items:
            try:
                if monitor.abortRequested():
                    return sys.exit()
                self.add(i["originaltitle"], i["year"], i["imdb"], i["tmdb"], range=True)
            except Exception:
                pass

        if self.infoDialog:
            control.infoDialog(control.lang(32554), time=1)  # Process Complete

        if self.library_setting == "true" and not control.condVisibility("Library.IsScanningVideo"):
            control.execute("UpdateLibrary(video)")
        else:
            # fflog('koniec funkcji "range" dla seriali')
            pass


    def strmFile(self, i):
        try:
            title, year, imdb, tmdb, season, episode, tvshowtitle, localtvshowtitle, premiered = (
                i["title"],
                i["year"],
                i["imdb"],
                i["tmdb"],
                i["season"],
                i["episode"],
                i["tvshowtitle"],
                i["localtvshowtitle"],
                i["premiered"],
            )

            episodetitle = urllib.quote_plus(title)
            systitle = urllib.quote_plus(tvshowtitle)
            syspremiered = urllib.quote_plus(premiered)

            table = str.maketrans(dict.fromkeys(r'\/:*?"<>|'))
            if control.setting("library.localtitles_for_filenames") == "true" and localtvshowtitle:
                transtitle = localtvshowtitle.translate(table)
            else:
                transtitle = tvshowtitle.translate(table)

            content = (
                #"%s?action=play&title=%s&year=%s&imdb=%s&tmdb=%s&season=%s&episode=%s&tvshowtitle=%s&date=%s"
                "%s?action=play&title=%s&year=%s&imdb=%s&tmdb=%s&season=%s&episode=%s&tvshowtitle=%s&premiered=%s"
                % (
                    sys.argv[0],
                    episodetitle,
                    year,
                    imdb,
                    tmdb,
                    season,
                    episode,
                    systitle,
                    syspremiered,
                )
            )

            folder = lib_tools.make_path(self.library_folder, transtitle, year)
            if not os.path.isfile(os.path.join(folder, "tvshow.nfo")):
                lib_tools.create_folder(folder)
                lib_tools.write_file(os.path.join(folder, "tvshow.nfo"), lib_tools.nfo_url("tv", i))

            folder = lib_tools.make_path(self.library_folder, transtitle, year, season)
            lib_tools.create_folder(folder)
            lib_tools.write_file(
                os.path.join(
                    folder,
                    lib_tools.legal_filename("%s S%02dE%02d" % (transtitle, int(season), int(episode))) + ".strm",
                ),
                content,
            )
        except Exception:
            fflog_exc(1)
            pass



class libepisodes:  # to chyba do automatycznej (samoczynnej ?) aktualizacji seriali TV
    def __init__(self):
        self.library_folder = os.path.join(control.transPath(control.setting("library.tv")), "")
        self.library_setting = control.setting("library.update") or "true"
        self.include_unknown = control.setting("library.include_unknown") or "true"
        # self.include_future = control.setting("library.include_future") or "false"
        self.delay_before_add = int(control.setting("library.delay_before_add")) or 0
        self.property = "%s_service_property" % control.addonInfo("name").lower()
        self.datetime = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
        self.date = (self.datetime - datetime.timedelta(hours=6)).strftime("%Y%m%d")
        self.infoDialog = False


    def update(self, query=None, info="true"):
        try:
            items = []
            season, episode = [], []
            show = [
                os.path.join(self.library_folder, i)
                for i in control.listDir(self.library_folder)[0]
            ]
            for s in show:
                try:
                    season += [os.path.join(s, i) for i in control.listDir(s)[0]]
                except Exception:
                    pass
            for s in season:
                try:
                    episode.append(
                        [
                            os.path.join(s, i)
                            for i in control.listDir(s)[1]
                            if i.endswith(".strm")
                        ][-1]
                    )
                except Exception:
                    pass

            for file in episode:
                try:
                    file = control.openFile(file)
                    read = file.read()
                    file.close()

                    if not read.startswith(sys.argv[0]):
                        raise Exception()

                    params = dict(urllib.parse_qsl(read.replace("?", "")))

                    try:
                        tvshowtitle = params["tvshowtitle"]
                    except Exception:
                        tvshowtitle = None
                    try:
                        tvshowtitle = params["show"]
                    except Exception:
                        pass
                    if tvshowtitle is None or tvshowtitle == "":
                        raise Exception(f'{tvshowtitle=}')

                    year, imdb, tmdb = params["year"], params["imdb"], params["tmdb"]

                    imdb = "tt" + re.sub("[^0-9]", "", str(imdb))

                    try:
                        tmdb = params["tmdb"]
                    except Exception:
                        tmdb = "0"

                    items.append(
                        {
                            "tvshowtitle": tvshowtitle,
                            "year": year,
                            "imdb": imdb,
                            "tmdb": tmdb,
                        }
                    )
                except Exception:
                    fflog_exc()
                    pass

            items = [i for x, i in enumerate(items) if i not in items[x + 1 :]]
            if len(items) == 0:
                fflog(f"Brak elementów do aktualizacji  {len(items)=}")
                if (
                    info == "true"
                    and not control.condVisibility("Window.IsVisible(infodialog)")
                    and not control.condVisibility("Player.HasVideo")
                ):
                    control.infoDialog("Brak elementów do aktualizacji",)
                return
                # raise Exception(f'{len(items)=}')
        except Exception:
            fflog_exc()
            return

        try:
            lib = control.jsonrpc(
                '{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "params": {"properties" : ["imdbnumber", "title", "year"]}, "id": 1}'
            )
            lib = json.loads(lib)["result"]["tvshows"]
        except Exception:
            fflog_exc()
            return

        if (
            info == "true"
            and not control.condVisibility("Window.IsVisible(infodialog)")
            and not control.condVisibility("Player.HasVideo")
        ):
            control.infoDialog(control.lang(32553), time=10000000)  # Updating TV shows...
            self.infoDialog = True

        try:
            control.makeFile(control.dataPath)
            dbcon = database.connect(control.libcacheFile)
            dbcur = dbcon.cursor()
            dbcur.execute(
                "CREATE TABLE IF NOT EXISTS tvshows ("
                "id TEXT, "
                "items TEXT, "
                "UNIQUE(id)"
                ");"
            )
        except Exception:
            fflog_exc()
            return

        try:
            from resources.lib.indexers import episodes
        except Exception:
            fflog_exc()
            return

        files_added = 0

        # __init__ doesn't get called from services so self.date never gets updated and new episodes are not added to the library
        self.datetime = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
        self.date = (self.datetime - datetime.timedelta(hours=6)).strftime("%Y%m%d")

        monitor = xbmc.Monitor()

        for item in items:
            it = None

            if monitor.abortRequested():
                return sys.exit()

            try:
                dbcur.execute("SELECT * FROM tvshows WHERE id = '%s'" % item["tmdb"])
                fetch = dbcur.fetchone()
                it = eval(fetch[1])
            except Exception:
                pass

            try:
                if not it is None:
                    raise Exception()

                it = episodes.episodes().get(
                    item["tvshowtitle"],
                    item["year"],
                    item["imdb"],
                    item["tmdb"],
                    idx=False,
                )

                status = it[0]["status"].lower()

                it = [
                    {
                        "title": i["title"],
                        "year": i["year"],
                        "imdb": i["imdb"],
                        "tmdb": i["tmdb"],
                        "season": i["season"],
                        "episode": i["episode"],
                        "tvshowtitle": i["tvshowtitle"],
                        "premiered": i["premiered"],
                    }
                    for i in it
                ]

                if status == "continuing":
                    raise Exception()
                dbcur.execute(
                    "INSERT INTO tvshows Values (?, ?)",
                    (item["tmdb"], repr(it))
                )
                dbcon.commit()
            except Exception:
                pass

            try:
                id = [item["imdb"], item["tmdb"]]
                if not item["tmdb"] == "0":
                    id += [item["tmdb"]]

                ep = [
                    x["title"]
                    for x in lib
                    if str(x["imdbnumber"]) in id
                    or (
                        x["title"] == item["tvshowtitle"]
                        and str(x["year"]) == item["year"]
                    )
                ][0]
                ep = control.jsonrpc(
                    '{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": {"filter":{"and": [{"field": "tvshow", "operator": "is", "value": "%s"}]}, "properties": ["season", "episode"]}, "id": 1}'
                    % ep
                )
                ep = json.loads(ep).get("result", {}).get("episodes", {})
                ep = [
                    {"season": int(i["season"]), "episode": int(i["episode"])}
                    for i in ep
                ]
                ep = sorted(ep, key=lambda x: (x["season"], x["episode"]))[-1]

                num = [
                    x
                    for x, y in enumerate(it)
                    if str(y["season"]) == str(ep["season"])
                    and str(y["episode"]) == str(ep["episode"])
                ][-1]
                it = [y for x, y in enumerate(it) if x > num]
                if len(it) == 0:
                    continue
            except Exception:
                continue

            for i in it:
                try:
                    if monitor.abortRequested():
                        return sys.exit()

                    premiered = i.get("premiered", "0")
                    if (
                        premiered != "0"
                        and ( int(re.sub("[^0-9]", "", str(premiered))) > int(self.date)
                            # and self.include_future != "true"
                            or self.delay_before_add and (prem > (int(self.date) - int(self.delay_before_add)))
                            )
                    ) or (premiered == "0" and not self.include_unknown == "true"):
                        continue

                    libtvshows().strmFile(i)
                    files_added += 1
                except Exception:
                    pass

        if self.infoDialog:
            control.infoDialog(control.lang(32554), time=1)  # Process Complete

        if (
            self.library_setting == "true"
            and not control.condVisibility("Library.IsScanningVideo")
            and files_added > 0
        ):
            control.execute("UpdateLibrary(video)")


    def service(self):
        try:
            lib_tools.create_folder(os.path.join(control.transPath(control.setting("library.movie")), ""))
            lib_tools.create_folder(os.path.join(control.transPath(control.setting("library.tv")), ""))
        except Exception:
            fflog_exc(1)
            pass

        try:
            control.makeFile(control.dataPath)
            dbcon = database.connect(control.libcacheFile)
            dbcur = dbcon.cursor()
            dbcur.execute(
                "CREATE TABLE IF NOT EXISTS service ("
                "setting TEXT, "
                "value TEXT, "
                "UNIQUE(setting)"
                ");"
            )
            dbcur.execute("SELECT * FROM service WHERE setting = 'last_run'")
            fetch = dbcur.fetchone()
            if fetch is None:
                serviceProperty = "1970-01-01 23:59:00.000000"
                dbcur.execute(
                    "INSERT INTO service Values (?, ?)",
                    ("last_run", serviceProperty)
                )
                dbcon.commit()
            else:
                serviceProperty = str(fetch[1])
            dbcon.close()
        except:
            try:
                return dbcon.close()
            except:
                return

        try:
            control.window.setProperty(self.property, serviceProperty)
        except:
            return

        monitor = xbmc.Monitor()
        # pętla w kółko (aż do zamknięcia Kodi chyba)
        while not monitor.abortRequested():
            try:

                serviceProperty = control.window.getProperty(self.property)

                t1 = datetime.timedelta(hours=6)
                t2 = datetime.datetime.strptime(serviceProperty, "%Y-%m-%d %H:%M:%S.%f")
                t3 = datetime.datetime.now()

                check = abs(t3 - t2) > t1
                if not check:
                    raise Exception()

                if control.player.isPlaying() or control.condVisibility("Library.IsScanningVideo"):
                    raise Exception()

                serviceProperty = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

                control.window.setProperty(self.property, serviceProperty)

                try:
                    dbcon = database.connect(control.libcacheFile)
                    dbcur = dbcon.cursor()
                    dbcur.execute(
                        "CREATE TABLE IF NOT EXISTS service ("
                        "setting TEXT, "
                        "value TEXT, "
                        "UNIQUE(setting)"
                        ");"
                    )
                    dbcur.execute("DELETE FROM service WHERE setting = 'last_run'")
                    dbcur.execute(
                        "INSERT INTO service Values (?, ?)",
                        ("last_run", serviceProperty),
                    )
                    dbcon.commit()
                    dbcon.close()
                except:
                    try:
                        dbcon.close()
                    except:
                        pass

                if not control.setting("library.service.update") == "true":
                    raise Exception()

                info = control.setting("library.service.notification") or "true"
                self.update(info=info)

            except:
                pass

            print('[libtools.py] [service] is active')
            control.sleep(10000)  # 10 sec.

        print('[libtools.py] [service] finish')
