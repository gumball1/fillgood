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

import os
import sys

from ptw.libraries import control
from ptw.libraries import trakt

from ptw.libraries.log_utils import log, fflog
from ptw.debug import log_exception, fflog_exc

sysaddon = sys.argv[0]
syshandle = int(sys.argv[1])

artPath = control.artPath()
addonFanart = control.addonFanart()
imdbCredentials = False if control.setting("imdb.user") == "" else True
tmdbCredentials = False if control.setting("tmdb.sessionid") == "" else True
traktCredentials = trakt.getTraktCredentialsInfo()
traktIndicators = trakt.getTraktIndicatorsInfo()
queueMenu = control.lang(32065)


class navigator:

    def __init__(self):
        # fix for not always current value
        global syshandle
        syshandle = int(sys.argv[1])


    def root(self):  # główne menu
        self.addDirectoryItem(32001, "movieNavigator", "movies.png", "DefaultMovies.png")
        self.addDirectoryItem(32002, "tvNavigator", "tvshows.png", "DefaultTVShows.png")
        downloads = (True
                     if control.setting("downloads") == "true"
                        and (len(control.listDir(control.setting("movie.download.path"))[0]) > 0
                             or len(control.listDir(control.setting("tv.download.path"))[0]) > 0)
                     else False)
        if downloads:
            self.addDirectoryItem(32009, "downloadNavigator", "downloads.png", "DefaultFolder.png")
        self.addDirectoryItem(32010, "searchNavigator", "search.png", "DefaultFolder.png")
        self.addDirectoryItem(32008, "toolNavigator", "tools.png", "DefaultAddonProgram.png")
        self.endDirectory()


    def movies(self, lite=False):
        self.addDirectoryItem(32010, "movieSearch", "search.png", "DefaultMovies.png")
        if (traktCredentials == True or imdbCredentials == True or tmdbCredentials == True):
            self.addDirectoryItem(32003, "mymovieNavigator", "mymovies.png", "DefaultVideoPlaylists.png")
        self.addDirectoryItem(32005, "movies&url=tmdb_new", "latest-movies.png", "DefaultRecentlyAddedMovies.png", )
        self.addDirectoryItem("Nadchodzące", "movies&url=tmdb_upcoming", "latest-movies.png", "DefaultRecentlyAddedMovies.png", )
        self.addDirectoryItem(32022, "movies&url=tmbd_cinema", "in-theaters.png", "DefaultRecentlyAddedMovies.png", )
        self.addDirectoryItem(32007, "movieSearchFromEPG", "channels.png", "DefaultMovies.png")  # what is on TV
        self.addDirectoryItem((32018,"  (wg TMDB)"), "movies&url=tmdb_popular", "people-watching.png", "DefaultMovies.png")
        self.addDirectoryItem((32017,"  (wg Trakt)"), "movies&url=trending", "featured.png", "DefaultRecentlyAddedMovies.png")  # from trakt
        self.addDirectoryItem(32020, "movies&url=boxoffice", "box-office.png", "DefaultMovies.png")  # from trakt
        self.addDirectoryItem("Najwyżej oceniane  (wg TMDB)", "movies&url=tmdb_top_rated", "highly-rated.png", "DefaultMovies.png")
        self.addDirectoryItem(32631, "moviesAwards", "awards.png", "DefaultMovies.png")
        self.addDirectoryItem(32011, "movieGenres", "genres.png", "DefaultMovies.png")
        # self.addDirectoryItem(32632, "movieCompanies", "companies.png", "DefaultMovies.png")  # nie zrobione w movies.py
        self.addDirectoryItem(32014, "movieLanguages", "languages.png", "DefaultMovies.png")
        self.addDirectoryItem("Rok (lub lata)", "movieYears", "years.png", "DefaultMovies.png")
        self.addDirectoryItem("Kategorie wiekowe", "movieCertificates", "certificates.png", "DefaultMovies.png")
        self.endDirectory()


    def mymovies(self, lite=False):  # indywidualne listy z trakt, tmdb lub imdb
        self.accountCheck()

        if traktCredentials:
            self.addDirectoryItem(32032, "movies&url=traktcollection", "trakt.png", "DefaultMovies.png", queue=True,
                context=(32551, "moviesToLibrary&url=traktcollection"), )

            self.addDirectoryItem(32033, "movies&url=traktwatchlist", "trakt.png", "DefaultMovies.png", queue=True,
                context=(32551, "moviesToLibrary&url=traktwatchlist"), )

            self.addDirectoryItem(32035, "movies&url=traktfeatured", "featured.png", "DefaultMovies.png", queue=True, )  # Proponowane

            self.addDirectoryItem(32036, "movies&url=trakthistory", "trakt.png", "DefaultMovies.png",
              #context=("Odśwież teraz", "movies&url=trakthistory&refresh=1", "showdir"),  # sprawdzić, czy potrzebne, bo tam jakoś to inaczej jest to rozwiązane niż w serialach
              # refresh=True,  # jak coś, to teraz tak można
            )

        if tmdbCredentials:
            self.addDirectoryItem("Obserwowane TMDB", "movies&url=tmdbuserwatchlist", "tmdb.png", "DefaultMovies.png",
                refresh=True,
                queue=True,
                context=(32551, "moviesToLibrary&url=tmdbuserwatchlist"),
                )

            self.addDirectoryItem("Ulubione TMDB", "movies&url=tmdbuserfavourite", "tmdb.png", "DefaultMovies.png",
                refresh=True,
                queue=True,
                context=(32551, "moviesToLibrary&url=tmdbuserfavourite"),
                )

        if imdbCredentials:
            self.addDirectoryItem("Obserwowane IMDb",   "movies&url=imdbwatchlist", "imdb.png", "DefaultMovies.png",
                            # context=("Odśwież teraz", "movies&url=imdbwatchlist&refresh=1", "showdir"),
                            # context=(32551, "moviesToLibrary&url=imdbwatchlist"),  # na razie nie można kilku pozycji dodać - trzeba przerobić funkcję addDirectoryItem
                            # context=[(1menu), (2menu)]
                            refresh=True,
                            queue=True,
                            context=(32551, "moviesToLibrary&url=imdbwatchlist"),
                            )

        self.addDirectoryItem("Własne listy", "movieUserlists", "userlists.png", "DefaultMovies.png")

        self.endDirectory()


    def tvshows(self, lite=False):
        self.addDirectoryItem(32010, "tvSearch", "search.png", "DefaultTVShows.png")
        if (traktCredentials == True or imdbCredentials == True or tmdbCredentials == True):
            self.addDirectoryItem(32004, "mytvNavigator", "mytvshows.png", "DefaultVideoPlaylists.png")
        self.addDirectoryItem(control.lang(32017)+"  (wg Trakt)", "tvshows&url=trending", "featured.png", "DefaultRecentlyAddedEpisodes.png", )  # by trakt
        self.addDirectoryItem(control.lang(32018)+"  (wg TMDB)", "tvshows&url=tmdb_popular", "people-watching.png", "DefaultMovies.png")
        self.addDirectoryItem((32026,"  (TMDB)"), "tvshows&url=tmdb_premiere", "new-tvshows.png", "DefaultTVShows.png")
        self.addDirectoryItem((32024,"  (TMDB)"), "tvshows&url=tmbd_airing", "airing-today.png", "DefaultTVShows.png")
        self.addDirectoryItem("Najwyżej oceniane  (wg TMDB)", "tvshows&url=tmdb_top_rated", "highly-rated.png", "DefaultTVShows.png")
        self.addDirectoryItem(32011, "tvGenres", "genres.png", "DefaultTVShows.png")
        self.addDirectoryItem(32016, "tvNetworks", "networks.png", "DefaultTVShows.png")
        self.addDirectoryItem((32012," (lata)"), "tvYears", "years.png", "DefaultTVShows.png")
        self.addDirectoryItem(32014, "tvLanguages", "languages.png", "DefaultTVShows.png")
        self.addDirectoryItem("Kategorie wiekowe", "tvCertificates", "certificates.png", "DefaultTVShows.png")
        self.endDirectory()


    def mytvshows(self, lite=False):
        self.accountCheck()
        if traktCredentials == True:

            self.addDirectoryItem(32032, "tvshows&url=traktcollection", "trakt.png", "DefaultTVShows.png",
                context=(32551, "tvshowsToLibrary&url=traktcollection"), )

            self.addDirectoryItem(32033, "tvshows&url=traktwatchlist", "trakt.png", "DefaultTVShows.png",
                context=(32551, "tvshowsToLibrary&url=traktwatchlist"), )

            self.addDirectoryItem(32035, "tvshows&url=traktfeatured", "trakt.png", "DefaultTVShows.png")  # Proponowane

            self.addDirectoryItem(32036,   "calendar&url=trakthistory", "trakt.png", "DefaultTVShows.png",
               # context=("Odśwież teraz", "calendar&url=trakthistory&refresh=1", "showdir"), )
               refresh=True, ) # jak coś, to teraz tak można

            self.addDirectoryItem(32037, "calendar&url=progress", "trakt.png", "DefaultRecentlyAddedEpisodes.png",
               context=("Odśwież teraz", "calendar&url=progress&refresh=1", "showdir"), queue=True, )  # Postęp

            self.addDirectoryItem(32038, "calendar&url=mycalendar", "trakt.png", "DefaultRecentlyAddedEpisodes.png", queue=True, )  # odcinki

        if tmdbCredentials:
            self.addDirectoryItem("Obserwowane TMDB", "tvshows&url=tmdbuserwatchlist", "tmdb.png", "DefaultMovies.png",
                refresh=True, queue=True, context=(32551, "tvshowsToLibrary&url=tmdbuserwatchlist"), )

            self.addDirectoryItem("Ulubione TMDB", "tvshows&url=tmdbuserfavourite", "tmdb.png", "DefaultMovies.png",
                refresh=True, queue=True, context=(32551, "tvshowsToLibrary&url=tmdbuserfavourite"), )

        if imdbCredentials:
            self.addDirectoryItem("Obserwowane IMDb", "tvshows&url=imdbwatchlist", "imdb.png", "DefaultTVShows.png",
                refresh=True, queue=True, context=(32551, "tvshowsToLibrary&url=imdbwatchlist"), )

        self.addDirectoryItem(32040, "tvUserlists", "userlists.png", "DefaultTVShows.png")  # Listy seriali

        if traktCredentials:
            self.addDirectoryItem(32041, "episodeUserlists", "userlists.png", "DefaultTVShows.png")  # Listy odcinków

        self.endDirectory()


    def tools(self): #WIELKIE PORZĄDKI - wywalenie skrótów do ustawień, zostawienie biblioteki i konserwacji
        self.addDirectoryItem(32043, "openSettings", "tools.png", "DefaultAddonProgram.png", isFolder=False)
        self.addDirectoryItem(32556, "libraryNavigator", "tools.png", "DefaultAddonProgram.png")
        self.addDirectoryItem(32049, "viewsNavigator", "tools.png", "DefaultAddonProgram.png", isFolder=True)
        self.addDirectoryItem("[B]FanFilm[/B]: Cache", "cacheNavigator", "tools.png", "DefaultAddonProgram.png", isFolder=True)
        self.addDirectoryItem(32073, "authTrakt", "trakt.png", "DefaultAddonProgram.png", isFolder=False)
        self.endDirectory()


    def cache(self):
        self.addDirectoryItem(32604, "clearCacheSearch", "tools.png", "DefaultAddonProgram.png", isFolder=False)
        self.addDirectoryItem(32050, "clearSources", "tools.png", "DefaultAddonProgram.png", isFolder=False)
        self.addDirectoryItem(32052, "clearCache", "tools.png", "DefaultAddonProgram.png", isFolder=False)
        self.endDirectory()


    def library(self):
        self.addDirectoryItem(32559, control.setting("library.movie"), "movies.png",  "DefaultMovies.png",  isAction=False, )
        self.addDirectoryItem(32560, control.setting("library.tv"),    "tvshows.png", "DefaultTVShows.png", isAction=False, )
        self.addDirectoryItem("[B]FanFilm[/B]: Aktualizowanie biblioteki seriali", "updateLibrary&query=tool", "library_update.png", "DefaultAddonProgram.png", isFolder=True)

        if trakt.getTraktCredentialsInfo():
            self.addDirectoryItem(32561, "moviesToLibrary&url=traktcollection",  "trakt.png", "DefaultMovies.png",  isFolder=True, )
            self.addDirectoryItem(32562, "moviesToLibrary&url=traktwatchlist",   "trakt.png", "DefaultMovies.png",  isFolder=True, )
            self.addDirectoryItem(32563, "tvshowsToLibrary&url=traktcollection", "trakt.png", "DefaultTVShows.png", isFolder=True, )
            self.addDirectoryItem(32564, "tvshowsToLibrary&url=traktwatchlist",  "trakt.png", "DefaultTVShows.png", isFolder=True, )

        if tmdbCredentials:
            self.addDirectoryItem("[B]TMDB[/B]: Importuj obserwowane filmy",   "moviesToLibrary&url=tmdbuserwatchlist",  "tmdb.png", "DefaultMovies.png",  isFolder=True, )
            self.addDirectoryItem("[B]TMDB[/B]: Importuj ulubione filmy",      "moviesToLibrary&url=tmdbuserfavourite",  "tmdb.png", "DefaultMovies.png",  isFolder=True, )
            self.addDirectoryItem("[B]TMDB[/B]: Importuj obserwowane seriale", "tvshowsToLibrary&url=tmdbuserwatchlist", "tmdb.png", "DefaultTVShows.png", isFolder=True, )
            self.addDirectoryItem("[B]TMDB[/B]: Importuj ulubione seriale",    "tvshowsToLibrary&url=tmdbuserfavourite", "tmdb.png", "DefaultTVShows.png", isFolder=True, )

        if imdbCredentials:
            self.addDirectoryItem("[B]IMDb[/B]: Importuj obserwowane filmy",   "moviesToLibrary&url=imdbwatchlist",  "imdb.png", "DefaultMovies.png",  isFolder=True, )
            self.addDirectoryItem("[B]IMDb[/B]: Importuj obserwowane seriale", "tvshowsToLibrary&url=imdbwatchlist", "imdb.png", "DefaultTVShows.png", isFolder=True, )

        self.endDirectory()


    def downloads(self):
        movie_downloads = control.setting("movie.download.path")
        tv_downloads = control.setting("tv.download.path")

        if len(control.listDir(movie_downloads)[0]) > 0:
            self.addDirectoryItem(32001, movie_downloads, "movies.png", "DefaultMovies.png", isAction=False, )

        if len(control.listDir(tv_downloads)[0]) > 0:
            self.addDirectoryItem(32002, tv_downloads, "tvshows.png", "DefaultTVShows.png", isAction=False)

        self.addDirectoryItem("Menadżer pobierania", "downloadManager", "downloads.png", "DefaultFolder.png", )

        self.endDirectory()


    def search(self): #DODANIE ALL
        self.addDirectoryItem(32001, "movieSearch", "search.png", "DefaultMovies.png")
        self.addDirectoryItem(32002, "tvSearch", "search.png", "DefaultTVShows.png")
        self.addDirectoryItem(32029, "moviePerson", "people-search.png", "DefaultMovies.png")
        self.addDirectoryItem(32030, "tvPerson", "people-search.png", "DefaultTVShows.png")
        self.endDirectory()


    def views(self):
        try:            
            items = [
                     (control.lang(32001), "movies"),
                     (control.lang(32002), "tvshows"),
                     (control.lang(32054), "seasons"),
                     (control.lang(32038), "episodes"),
                     (control.lang(32345), "files"),
                     ("Katalogi menu", "addons"),
                    ]

            select = control.selectDialog([i[0] for i in items], control.lang(32049))

            if select == -1:
                control.directory(syshandle, cacheToDisc=False)
                control.execute('Action(Back)')
                return False

            content = items[select][1]

            title = control.lang(32059)  # KLIKNIJ TUTAJ ABY ZAPISAĆ WIDOK
            url = "{}?action=addView&content={}".format(sysaddon, content)

            poster, banner, fanart = control.addonPoster(), control.addonBanner(), control.addonFanart()

            item = control.item(label=title)

            item.setInfo(type="Video", infoLabels={"title": title})
            item.setArt({"icon": poster, "thumb": poster, "poster": poster, "banner": banner})
            item.setProperty("Fanart_Image", fanart)

            control.addItem(handle=syshandle, url=url, listitem=item, isFolder=False)
            control.content(syshandle, content)
            control.directory(syshandle, cacheToDisc=True)

            from ptw.libraries import views
            views.setView(content, {})
        except Exception:
            fflog_exc(1)
            return


    def accountCheck(self):
        if (traktCredentials == False and imdbCredentials == False and tmdbCredentials == False):
            control.infoDialog(control.lang(32042), sound=True, icon="WARNING")
            sys.exit()


    def infoCheck(self, version):
        """ nie wiem, do czego to służy """
        try:
            control.infoDialog("", control.lang(32074), time=5000, sound=False)  # POMOC
            return "1"
        except Exception:
            # fflog_exc(1)
            return "1"


    def clearCache(self):
        yes = control.yesnoDialog(control.lang(32056))
        if not yes:
            return
        from ptw.libraries import cache
        cache.cache_clear()
        control.infoDialog(control.lang(32057), sound=True, icon="INFO")


    def clearCacheMeta(self):
        yes = control.yesnoDialog(control.lang(32056))
        if not yes:
            return
        from ptw.libraries import cache
        cache.cache_clear_meta()
        control.infoDialog(control.lang(32057), sound=True, icon="INFO")


    def clearCacheProviders(self):
        yes = control.yesnoDialog(control.lang(32056))
        if not yes:
            return
        from ptw.libraries import cache
        cache.cache_clear_providers()
        control.infoDialog(control.lang(32057), sound=True, icon="INFO")


    def clearCacheSearch(self, content=None):
        yes = control.yesnoDialog(control.lang(32056))
        if not yes:
            return False
        from ptw.libraries import cache
        cache.cache_clear_search(content)
        control.infoDialog(control.lang(32057), sound=True, icon="INFO")


    def removeFromSearchHistory(self, term, content=None):
        yes = control.yesnoDialog(f'Czy chcesz usunąć z historii wyszukiwania element [CR][B]{term}[/B] ? ')
        if not yes:
            return False
        from ptw.libraries import cache
        cache.cache_clear_search_by_term(term, content)
        control.infoDialog(control.lang(32057), sound=True, icon="INFO")


    def clearCacheAll(self):
        yes = control.yesnoDialog(control.lang(32056))
        if not yes:
            return
        from ptw.libraries import cache
        cache.cache_clear_all()
        control.infoDialog(control.lang(32057), sound=True, icon="INFO")


    def clearCacheAllSilent(self):
        from ptw.libraries import cache
        cache.cache_clear_all()


    def addDirectoryItem(self, name, query, thumb, icon, context=None, refresh=False, queue=False, isAction=True, isFolder=True, ):
        if isinstance(name, tuple):
            name, name2 = name
        else:
            name2 = ""
        try:
            #name = control.lang(name)
            name = control.lang(name)
        except:
            pass

        url = "{}?action={}".format(sysaddon, query) if isAction == True else query

        if "http" not in thumb:
            thumb = os.path.join(artPath, thumb) if not artPath is None else icon

        cm = []

        if refresh:
            cm.append(("Odśwież teraz", "Container.Update(%s&refresh=1)" % url))

        if not context is None:
            """ można odblokować, ale na razie nie ma takiej potrzeby
            if not isinstance(context, list):  # ale trzeba mieć pewność, że nigdzie w innych plikach nie jest używana lista, tylko krotka (jeśli odwołują się do tej metody)
                context0 = [context]
            else:
                context0 = context
            for context in context0:
                # wcięcie
            """
            label = control.lang(context[0]) if isinstance(context[0], int) else context[0]
            function = "RunPlugin" if not (len(context)==3 and context[2]) else "Container.Update"  # "showdir" , czyli wyświetlaj katalog chyba (Container.Update)
            cm.append((label, "{}({}?action={})".format(function, sysaddon, context[1]),))

        if queue:
            cm.append((queueMenu, "RunPlugin(%s?action=queueItem)" % sysaddon))

        item = control.item(label=name+name2)
        item.addContextMenuItems(cm)
        item.setArt({"icon": icon, "thumb": thumb})
        if not addonFanart is None:
            item.setProperty("Fanart_Image", addonFanart)
        control.addItem(handle=syshandle, url=url, listitem=item, isFolder=isFolder)


    def endDirectory(self, cacheToDisc=True, succeeded=True, updateListing=False):
        control.content(syshandle, "addons")
        control.directory(syshandle, cacheToDisc=cacheToDisc, succeeded=succeeded, updateListing=updateListing)
        # views.setView("addons")  # dodatkowa funkcja FanFilm  NIE WIEM, CZY TU WARTO

