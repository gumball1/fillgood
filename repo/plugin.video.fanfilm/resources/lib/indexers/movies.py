"""
    Fanfilm Add-on

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

import datetime
import json
import os
import re
import sys
import urllib
from threading import Thread
from xbmc import Actor, VideoStreamDetail
from xbmcplugin import addSortMethod, SORT_METHOD_UNSORTED, SORT_METHOD_PLAYLIST_ORDER, SORT_METHOD_LABEL, SORT_METHOD_TITLE, SORT_METHOD_VIDEO_YEAR, SORT_METHOD_DURATION, SORT_METHOD_VIDEO_RATING

import requests

try:
    import urllib.parse as urllib
except:
    pass
from resources.lib.indexers import navigator
from ptw.libraries import cache
from ptw.libraries import cleantitle
from ptw.libraries import client
from ptw.libraries import control
from ptw.libraries import log_utils
from ptw.libraries.log_utils import log, fflog, _is_debugging
from ptw.debug import log_exception, fflog_exc
from ptw.libraries import playcount
from ptw.libraries import trakt
from ptw.libraries import utils
from ptw.libraries import views
from ptw.libraries import apis
from ptw.libraries import source_utils
from ptw.libraries.utils import convert


# tylko, że to się nie zmienia przy kolejnych wywołaniach podstrony
# params = dict(urllib.parse_qsl(sys.argv[2][1:])) if len(sys.argv) > 1 else {}  # nie przetestowałem do końca
params = dict(urllib.parse_qsl(sys.argv[2].replace("?", ""))) if len(sys.argv) > 1 else dict()
action = params.get("action")


class movies:
    def __init__(self):
        # fflog("inicjalizacja klasy movies")

        # fix for not always current value
        global params, action
        params = dict(urllib.parse_qsl(sys.argv[2].replace("?", ""))) if len(sys.argv) > 1 else dict()
        action = params.get("action")
        # fflog(f'{params=}')  # kontrola

        ### BASE ###
        self.idx = True
        self.next_page = True
        self.meta = None
        self.list = []
        self.session = requests.Session()
        self.imdb_link  = "http://www.imdb.com"
        self.trakt_link = "https://api.trakt.tv"
        self.tmdb_link  = "https://api.themoviedb.org/"


        ### SETTINGS ###

        self.moviessort = control.setting("movies.sort")
        if self.moviessort == "0":
            self.moviessort = "popularity.desc"
        elif self.moviessort == "1":
            self.moviessort = "primary_release_date.desc"

        self.tmdbvote = control.setting("tmdbmovie.vote")

        self.trakt_user = control.setting("trakt.user").strip()
        self.imdb_user = control.setting("imdb.user").replace("ur", "").replace("/", "").strip()
        self.user = str(control.setting("fanart.tv.user")) + str(control.setting("tm.user"))

        self.tm_user = control.setting("tm.user") or apis.tmdb_API
        self.tmdbuser = control.setting("tmdb.username") or "me"
        self.tmdb_sessionid = control.setting("tmdb.sessionid") or ""

        self.lang = control.apiLanguage()["tmdb"]  # iso 639-1 | daje 'pl' (ciekawe, czy wielkość liter ma znaczenie, bo wg Wiki to "PL"
        self.language = f"{self.lang}-{self.lang.upper()}"  # ISO_3166_1 | wg doc api z tmdb to "language-COUNTRY", czyli np. "pl-PL" (z wyjątkiem obrazków?)
        self.region = self.lang.upper()  # filter to search for and display matching release date information. This parameter is expected to be an ISO 3166-1 code


        ## DATY ##
        self.datetime = datetime.datetime.utcnow() - datetime.timedelta(hours=5)
        self.systime = self.datetime.strftime("%Y%m%d%H%M%S%f")
        self.year_date = (self.datetime - datetime.timedelta(days=365)).strftime("%Y-%m-%d")
        self.today_date = self.datetime.strftime("%Y-%m-%d")
        self.today_date_cinema = self.datetime.strftime("%Y-%m-%d")  # to samo co wyżej
        self.hidecinema = control.setting("hidecinema")
        self.hidecinema_rollback = int(control.setting("hidecinema.rollback"))
        self.hidecinema_rollback2 = self.hidecinema_rollback * 30
        self.hidecinema_date = (datetime.date.today() - datetime.timedelta(days=self.hidecinema_rollback2)).strftime("%Y-%m")
        self.cinemanow_date = datetime.date.today() - datetime.timedelta(61)  # 2 miechy wstecz
        if self.hidecinema == "true":
            self.today_date = self.hidecinema_date
        else:
            #self.today_date = ""  # bo domyślnie tmdb i tak bierze dzisiejszą, a ścieżki będą uniwersalniejsze
            pass


        ### LINKI API DO TMDB ###
        # nie wiem dokładnie, czy to służy jak jakaś skrócona wersja?
        self.metasearch = (self.tm_user, self.lang, self.today_date,)  # TODO dodatkowe ustawienia

        # "popularity.desc" is default value for "sort_by"

        self.tmdb_movie_search = "https://api.themoviedb.org/3/search/movie?api_key=%s&language=%s&sort_by=popularity.desc&query=%%s&page=1" % (self.tm_user, self.lang)

        self.tmdb_epg_search = "https://api.themoviedb.org/3/search/movie?api_key=%s&language=%s&sort_by=popularity.desc&query=%%s&page=1" % (self.tm_user, self.lang)

        self.tmdb_discover = ("https://api.themoviedb.org/3/discover/movie?api_key=%s&language=%s&sort_by=%s&primary_release_date.lte=%s&vote_count.gte=%s&include_adult=false&include_video=false&%%s&page=1" % (
            self.tm_user, self.lang, self.moviessort, self.today_date, self.tmdbvote))

        self.tmdb_language = ("https://api.themoviedb.org/3/discover/movie?api_key=%s&language=%s&sort_by=%s&primary_release_date.lte=%s&include_adult=false&include_video=false&%%s&page=1" % (
            self.tm_user, self.lang, self.moviessort, self.today_date))

        self.tmdb_discover_year = ("https://api.themoviedb.org/3/discover/movie?api_key=%s&language=%s&sort_by=primary_release_date.asc&include_adult=false&include_video=false&primary_release_year=%%s&vote_count.gte=50&with_watch_monetization_types=flatrate&page=1" % (
            self.tm_user, self.lang))

        self.tmdb_discover_years = ("https://api.themoviedb.org/3/discover/movie?api_key=%s&language=%s&sort_by=popularity.desc&primary_release_date.gte=%%s&primary_release_date.lte=%%s&vote_count.gte=%s&include_adult=false&include_video=false&page=1" % (
            self.tm_user, self.lang, self.tmdbvote))

        #self.tmdb_popular_link = ("https://api.themoviedb.org/3/movie/popular?api_key=%s&language=%s&primary_release_date.lte=%s&include_adult=false&include_video=false&page=1" % self.metasearch)
        self.tmdb_popular_link = ("https://api.themoviedb.org/3/movie/popular?api_key=%s&language=%s&region=%s&page=1" % (self.tm_user, self.language, self.region))

        self.tmdb_top_rated_link = ("https://api.themoviedb.org/3/movie/top_rated?api_key=%s&language=%s&region=%s&page=1" % (self.tm_user, self.language, self.region))

        self.tmdb_upcoming_link = ("https://api.themoviedb.org/3/movie/upcoming?api_key=%s&language=%s&region=%s&page=1" % (self.tm_user, self.language, self.region))

        self.tmdb_new_link = ("https://api.themoviedb.org/3/discover/movie?api_key=%s&language=%s&sort_by=primary_release_date.desc&primary_release_date.lte=%s&vote_count.gte=%s&include_adult=false&include_video=false&with_runtime.gte=30&%%s&page=1" % (
            self.tm_user, self.language, self.today_date, self.tmdbvote))

        # nie wiem, czy to jeszcze jest wykorzystywane
        self.tmdb_trending_link = ("https://api.themoviedb.org/3/trending/movie/week?api_key=%s&language=%s&primary_release_date.lte=%s&vote_count.gte=100&include_adult=false&include_video=false&page=1" % self.metasearch)

        self.tmdb_views_link = ("https://api.themoviedb.org/3/trending/movie/week?api_key=%s&language=%ssort_by=vote_count.desc&primary_release_date.lte=%s&vote_count.gte=1000&include_adult=false&include_video=false&page=1" % self.metasearch)

        self.tmdb_similar = ("https://api.themoviedb.org/3/movie/%%s/similar?api_key=%s&language=%s&sort_by=%s&primary_release_date.lte=%s&vote_count.gte=%s&include_adult=false&include_video=false&page=1" % (
            self.tm_user, self.lang, self.moviessort, self.today_date, self.tmdbvote))

        """
        self.tmbd_cinema_link = (
                "https://api.themoviedb.org/3/discover/movie?api_key=%s&language=%s&sort_by=primary_release_date.desc&primary_release_date.gte=%s&with_release_type=3&vote_count.gte=%s&include_adult=false&include_video=false&page=1" % (
            self.tm_user, self.lang, self.cinemanow_date, self.tmdbvote))
        self.tmbd_cinema_link = (
                "https://api.themoviedb.org/3/discover/movie?api_key=%s&language=%s&sort_by=primary_release_date.desc&primary_release_date.gte=%s&primary_release_date.lte=%s&with_release_type=2|3&vote_count.gte=%s&include_adult=false&include_video=false&with_runtime.gte=20&page=1" % (
                    self.tm_user, self.language, self.cinemanow_date, self.today_date_cinema, self.tmdbvote))
        """
        self.tmbd_cinema_link = ( "https://api.themoviedb.org/3/movie/now_playing?api_key=%s&language=%s&region=%s&page=1" % 
                    (self.tm_user, self.language, self.region) )

        self.tmdb_personid_link = ("https://api.themoviedb.org/3/search/person?api_key=%s&language=%s&query=%%s&include_adult=false&page=1" % (
            self.tm_user, self.lang))

        self.tmdb_person_link = ("https://api.themoviedb.org/3/person/%%s/movie_credits?api_key=%s&language=%s&include_adult=false&page=1" % (
            self.tm_user, self.lang))


        ### TMDB USER ###
        self.tmdb_user_lists = ("https://api.themoviedb.org/3/account/%s/lists?api_key=%s&language=%s&session_id=%s&page=1" % (
            self.tmdbuser, self.tm_user, self.lang, self.tmdb_sessionid))

        self.tmdb_lists_link = ("https://api.themoviedb.org/3/list/%%s?api_key=%s&language=%s&include_adult=false&page=1" % (
            self.tm_user, self.lang))

        self.tmdbuserwatchlist_link = ("https://api.themoviedb.org/3/account/%s/watchlist/movies?api_key=%s&language=%s&session_id=%s&sort_by=created_at.desc&page=1" % (
            self.tmdbuser, self.tm_user, self.lang, self.tmdb_sessionid))

        self.tmdbuserfavourite_link = ("https://api.themoviedb.org/3/account/%s/favorite/movies?api_key=%s&language=%s&session_id=%s&sort_by=created_at.desc&page=1" % (
            self.tmdbuser, self.tm_user, self.lang, self.tmdb_sessionid))


        ### SUPERINFO ###
        self.tmdb_arts      = "https://api.themoviedb.org/3/movie/{}/images?api_key={}".format("%s", self.tm_user, )
        self.tmdb_providers = "https://api.themoviedb.org/3/movie/%s/watch/providers?api_key=%s" % ("%s", self.tm_user)
        self.tmdb_by_imdb   = "https://api.themoviedb.org/3/find/%s?api_key=%s&external_source=imdb_id" % ("%s", self.tm_user)
        self.tmdb_api_link  = "https://api.themoviedb.org/3/movie/%s?api_key=%s&language=%s&append_to_response=credits,external_ids" % ("%s", self.tm_user, self.lang)
        self.tm_art_link    = "https://api.themoviedb.org/3/movie/%s/images?api_key=%s&language=en-US&include_image_language=en,%s,null" % ("%s", self.tm_user, self.lang)
        self.tm_img_link    = "https://image.tmdb.org/t/p/w%s%s"


        ### grafiki z FanartTV
        self.fanart_tv_user       = (control.setting("fanart.tv.user") or apis.fanarttv_client_key)
        self.fanart_tv_API_key    = (control.setting("fanart.tv.dev") or apis.fanarttv_API_key)
        self.fanart_tv_headers    = {"api-key": self.fanart_tv_API_key, "client-key": self.fanart_tv_user, }
        self.fanart_tv_art_link   = "http://webservice.fanart.tv/v3/movies/%s"
        self.fanart_tv_level_link = "https://webservice.fanart.tv/v3/level"  # ?


        ## TRAKT - POJEDYNCZE LINKI ##
        self.traktlists_link      = "http://api.trakt.tv/users/me/lists"
        self.traktlikedlists_link = "http://api.trakt.tv/users/likes/lists?limit=1000000"
        self.traktlist_link       = "http://api.trakt.tv/users/%s/lists/%s/items"
        self.traktcollection_link = "http://api.trakt.tv/users/me/collection/movies"
        self.traktwatchlist_link  = "http://api.trakt.tv/users/me/watchlist/movies"
        self.traktfeatured_link   = "http://api.trakt.tv/recommendations/movies?limit=20"
        self.trending_link        = "http://api.trakt.tv/movies/trending?limit=20&page=1"
        self.trakthistory_link    = "http://api.trakt.tv/users/me/history/movies?limit=20&page=1"
        self.boxoffice_link       = "https://api.trakt.tv/movies/boxoffice"


        ## IMDB - POJEDYNCZE LINKI ##
        #imdb_count_limit = 20  # nie wdrożone
        self.imdb_awards = "https://www.imdb.com/search/title/?groups=%s&sort=year,desc&count=100&start=1"
        # self.imdb_awards = "https://www.imdb.com/search/title/?groups=%s&sort=year,desc"  # taki adres pokazuje z przeglądarce (oczywiście po uzupełnieniu groups na np. oscar_winner) i ściąga do 25 pozycji (a w js siedzi 50 pozycji)

        # self.imdbUserLists_link = "https://www.imdb.com/list/ls%s/?view=detail&sort=alpha,asc&title_type=movie&count=100&start=1"  # nie występuje w kodzie nigdzie

        self.imdblist1_link =     "https://www.imdb.com/list/%s/?view=detail&sort=alpha,asc&title_type=movie&count=80&start=1"
        self.imdblist2_link =     "https://www.imdb.com/list/ls%s/?view=detail&sort=date_added,desc&title_type=movie&count=80&start=1"

        self.imdblists_link =     "https://www.imdb.com/user/ur%s/lists?tab=all&sort=mdfd&order=desc&filter=titles" % self.imdb_user

        self.imdbwatchlist_link = "https://www.imdb.com/user/ur%s/watchlist" % self.imdb_user
        self.imdbwatchlist1_link ="https://www.imdb.com/user/ur%s/watchlist?sort=alpha,asc&count=80&start=1" % self.imdb_user
        self.imdbwatchlist2_link ="https://www.imdb.com/user/ur%s/watchlist?sort=date_added,desc&count=80&start=1" % self.imdb_user



    ### Katalogi filmów ###


    ## Języki ##
    def languages(self):
        languages = [("Polski", "pl"),
                    ("Afrykanerski", "af"), ("Albański", "sq"), ("Angielski", "en"), ("Arabski", "ar"), ("Azerski", "az"),
                    ("Białoruski", "be"), ("Bośniacki", "bs"), ("Bułgarski", "bg"), ("Chiński", "zh"), ("Chorwacki", "hr"),
                    ("Czeski", "cs"), ("Duński", "da"), ("Estoński", "et"), ("Fiński", "fi"), ("Francuski", "fr"),
                    ("Grecki", "el"), ("Gruziński", "ka"), ("Hebrajski", "he"), ("Hindi ", "hi"), ("Hiszpański", "es"),
                    ("Holenderski", "nl"), ("Irlandzki", "ga"), ("Islandzki", "is"), ("Japoński", "ja"), ("Koreański", "ko"),
                    ("Litewski", "lt"), ("Łotewski", "lv"), ("Macedoński", "mk"), ("Mołdawski", "mo"), ("Niemiecki", "de"),
                    ("Norweski", "no"), ("Ormiański", "hy"),
                    ("Pendżabski", "pa"), ("Perski", "fa"), ("Portugalski", "pt"), ("Rosyjski", "ru"), ("Rumuński", "ro"),
                    ("Serbski", "sr"), ("Serbsko-chorwacki", "sh"), ("Słowacki", "sk"), ("Słoweński", "sl"),
                    ("Szwedzki", "sv"), ("Turecki", "tr"), ("Ukraiński", "uk"), ("Węgierski", "hu"), ("Włoski", "it"),
        ]
        for i in languages:
            self.list.append({
                                "name": i[0],
                                "url": self.tmdb_language % ("with_original_language=" + i[1]),
                                "image": "languages.png",
                                "action": "movies" + f"&item={i[1]}",
                            })
        self.addDirectory(self.list)
        return self.list


    ## Certyfikaty ##
    def certifications(self):  # tego chyba nie ma w menu (przynajmniej ja nie mogę znaleźć)
        #certificates = ["G", "PG", "PG-13", "R", "NC-17"]
        certificates = [
            ("G", "(wszystkie grupy wiekowe)"),
            ("PG", "(7+)"),
            ("PG-13", "(13+)"),
            ("R", "(16+)"),
            ("NC-17", "(18+)"),
            # ("NR", "(bez oceny)")  # a jak pod filmem pojawia się NR,18 ?? może stosować certification.gte ?
        ]
        for i in certificates:
            self.list.append({
                "name": str(i[0]) + f"  {i[1]}",
                "url": self.tmdb_discover % ("certification_country=US&certification=" + str(i[0])),
                "image": "certificates.png",
                "action": "movies" + f"&item={str(i[0])}",
                })
        self.addDirectory(self.list)
        return self.list


    ## Lata ##
    def years(self):
        navigator.navigator().addDirectoryItem(32630, "movieYearsTop", "years.png", "DefaultMovies.png")

        year = self.datetime.strftime("%Y")
        for i in range(int(year) - 0, 1899, -1):
            self.list.append({
                "name": str(i),
                "url": self.tmdb_discover_year % (str(i)),
                "image": "years.png",
                "action": "movies" + f"&item={str(i)}",
                })

        self.addDirectory(self.list)
        return self.list


    ## Lata TOP (zakres lat) ##
    def years_top(self):
        year = self.datetime.strftime("%Y")
        dec = int(year[:3]) * 10
        for i in range(dec, 1860, -10):  # od 1870
            self.list.append({"name": str(i) + "-" + str(i + 9),
                              #"url": self.tmdb_discover_years % (str(i), str(i + 9)),
                              "url": self.tmdb_discover_years % (str(i)+"-01-01", str(i + 9)+"-12-31"),
                              "image": "years.png",
                              "action": "movies" + f'&item={str(i) + "-" + str(i + 9)}',
                              })
        self.addDirectory(self.list)
        return self.list


    ## Gatunki ##
    def genres(self):
        genres = [
                  ("28", "Akcja", "Action.png"),
                  ("12", "Przygodowy", "Adventure.png"),
                  ("16", "Animacja", "Animation.png"),
                  ("35", "Komedia", "Comedy.png"),
                  ("80", "Kryminał", "Crime.png"),
                  ("99", "Dokumentalny", "Documentary.png"),
                  ("18", "Dramat", "Drama.png"),
                  ("10751", "Familijny", "Family.png"),
                  ("14", "Fantasy", "Fantasy.png"),
                  ("36", "Historyczny", "History.png"),
                  ("27", "Horror", "Horror.png"),
                  ("10402", "Muzyczny", "Music.png"),
                  ("9648", "Tajemnica", "Mystery.png"),
                  ("10749", "Romans", "Romance.png"),
                  ("878", "Sci-Fi", "Sci-Fi.png"),
                  ("53", "Thriller", "Thriller.png"),
                  ("10752", "Wojenny", "War.png"),
                  ("37", "Western", "Western.png"),
                 ]
        for i in genres:
            self.list.append({"name": i[1],
                              "url": self.tmdb_discover % ("with_genres=" + i[0]),
                              "image": i[2],
                              "action": "movies" + f"&item={i[1]}",
                             })
        self.addDirectory(self.list)
        return self.list


    ## Nagrody ##
    def awards(self):
        awards = [
                  ("best_picture_winner", "Oscary - najlepszy film", "oscar-winners.png"),
                  ("oscar_best_picture_nominees", "Oscary - najlepszy film - nominowane", "oscar-winners.png",),
                  ("best_director_winner", "Oscary - najlepszy reżyser", "oscar-winners.png",),
                  ("oscar_best_director_nominees", "Oscary - najlepszy reżyser - nominowane", "oscar-winners.png",),
                  ("oscar_winner", "Oscary - wszystkie kategorie", "oscar-winners.png",),
                  ("oscar_nominee", "Oscary - wszystkie kategorie - nominowane", "oscar-winners.png",),
                  ("emmy_winner", "Nagrody Emmy", "emmy_winner.png"),
                  ("emmy_nominee", "Nagrody Emmy - nominowane", "emmy_winner.png"),
                  ("golden_globe_winner", "Złote Globy", "golden_globe_winner.png"),
                  ("golden_globe_nominee", "Złote Globy - nominowane", "golden_globe_winner.png"),
                  ("razzie_winner", "Złote Maliny", "razzie_winners.png"),
                  ("razzie_nominee", "Złote Maliny - nominowane", "razzie_winners.png"),
                  ("national_film_preservation_board_winner", "Narodowa Rada Ochrony Filmu", "national_film_preservation_board_winner.png"),
                 ]
        i = 0
        for a in awards:
            i += 1
            self.list.append({
                "name": a[1],
                "url": self.imdb_awards % (a[0]),
                "image": a[2],
                "action": "movies" + f"&item={a[0]}",
            })
        #fflog(f'[awards] {self.list=}')
        self.addDirectory(self.list)
        return self.list


    ## Podobne filmy ##
    def similar(self, tmdb):
        movies.get(self, self.tmdb_similar % tmdb)


    ### SEARCH ###
    def search(self):
        # log_utils.fflog(f'{sys.argv=}')
        # navigator.navigator().addDirectoryItem('(odśwież)', "movieSearch", "search.png", "DefaultMovies.png")

        generate_short_path = control.setting("generate_short_path") == "true"

        navigator.navigator().addDirectoryItem("[LIGHT][B]["+control.lang(32603)+"][/B][/LIGHT]", "movieSearchnew", "search.png", "DefaultMovies.png")

        from sqlite3 import dbapi2 as database

        dbcon = database.connect(control.searchFile)
        dbcur = dbcon.cursor()

        try:
            dbcur.executescript("CREATE TABLE IF NOT EXISTS movies (ID Integer PRIMARY KEY AUTOINCREMENT, term);")
        except:
            pass

        dbcur.execute("SELECT * FROM movies ORDER BY ID DESC")

        lst = []
        delete_option = False
        for (id, term) in dbcur.fetchall():
            if term not in str(lst):  # by nie było dubli na ekranie
                lst += [term]
                delete_option = True
                navigator.navigator().addDirectoryItem(
                    term,
                    # "movieSearchterm&name=%s" % term,
                    # "movieSearchterm",  # po powrocie focus ustawia się zawsze na pierwszym elemencie
                    #"movieSearchterm&item=%s" % len(lst),  # aby po powrocie focus ustawiał się na poprzedniej pozycji
                    "movieSearchterm&item=%s" % len(lst) if generate_short_path else "movieSearchterm&name=%s" % term,
                    "search.png",
                    "DefaultMovies.png", 
                    context=("Usuń z historii", "removeFromSearchHistory&term=%s&content=movies" % urllib.quote_plus(term),),
                )
        dbcur.close()

        if delete_option:
            navigator.navigator().addDirectoryItem("[LIGHT][I]["+control.lang(32605)+"][/I][/LIGHT]", "clearCacheSearch&content=movies", "tools.png", "DefaultAddonProgram.png", isFolder=False)

        syshandle = int(sys.argv[1])
        addSortMethod(syshandle, sortMethod=SORT_METHOD_UNSORTED)
        addSortMethod(syshandle, sortMethod=SORT_METHOD_LABEL)

        navigator.navigator().endDirectory(cacheToDisc=False)


    def search_new(self):
        """
        folderpath = control.infoLabel('Container.FolderPath')
        params1 = dict(urllib.parse_qsl(folderpath.split('?')[-1]))
        action1 = params1.get('action')  # może być też puste
        if action1 == "movieSearchterm":
            # taki hack na Kodi, bo inaczej wywala do głównego menu Kodi
            control.directory(int(sys.argv[1]), cacheToDisc=True)
            url = "{}?action={}".format(sys.argv[0], "movieSearch")
            control.execute('Container.Update("%s", replace)' % url)
            return
        """
        t = control.lang(32010)
        k = control.keyboard("", t)
        k.doModal()
        q = k.getText() if k.isConfirmed() else None
        if q is None or q == "" or q == "..":
            navigator.navigator().endDirectory()
            control.execute('Action(Back)')
            return
        q = cleantitle.normalize(q)  # for polish characters
        
        from sqlite3 import dbapi2 as database
        dbcon = database.connect(control.searchFile)
        dbcur = dbcon.cursor()

        dbcur.execute("SELECT * FROM movies WHERE term=?", (q,))
        if dbcur.fetchone():
            dbcur.execute("DELETE FROM movies WHERE term=?", (q,))
        dbcur.execute("INSERT INTO movies VALUES (?,?)", (None, q))

        dbcon.commit()
        dbcur.close()
        """
        if not control.condVisibility('Window.IsActive(busydialog)'):
            navigator.navigator().addDirectoryItem('... proszę czekać, trwa wyszukiwanie ...', "movieSearch", "search.png", "DefaultMovies.png")
            control.directory(int(sys.argv[1]), cacheToDisc=False)
            url = "{}?action={}".format(sys.argv[0], "movieSearchterm&name=%s" % urllib.quote_plus(q))
            control.execute('Container.Update("%s")' % url)
            return
        """
        control.busy()
        movies.get(self, self.tmdb_movie_search % urllib.quote_plus(q))
        control.idle()


    def search_term(self, name):
        # log_utils.fflog(f"{name=}")
        if name and name != "..":
            movies.get(self, self.tmdb_movie_search % urllib.quote_plus(name))
        else:
            import xbmcgui
            xbmcgui.Dialog().notification('FanFilm', 'szukanie niemożliwe z powodu błędnego parametru', xbmcgui.NOTIFICATION_ERROR)
            navigator.navigator().endDirectory()
            log_utils.fflog(f'szukanie niemożliwe z powodu błędnego parametru {name=}')
            control.execute('Action(Back)')
        

    def search_epg(self, name, year):
        movies.get(self, self.tmdb_epg_search % (urllib.quote_plus(name) + "&year=" + (year or "")))
        

    ### SEARCH PERSONS ### TODO - historia
    def person(self):
        try:
            t = control.lang(32010)
            k = control.keyboard("", t)
            k.doModal()
            q = k.getText() if k.isConfirmed() else None

            if q is None or q == "":
                return

            q = cleantitle.normalize(q)  # for polish characters
            
            # url = self.persons_link + urllib.quote_plus(q)
            # url = '%s?action=moviePersons&url=%s' % (sys.argv[0], urllib.quote_plus(url))
            movies.persons(self, self.tmdb_personid_link % urllib.quote_plus(q))
        except Exception as e:
            print(e)
            return


    ## Osoby - wyszukiwanie##
    def persons(self, url):
        url = re.sub("(?<=api_key=)[^&]*", self.tm_user, url)
        url = re.sub("(?<=session_id=)[^&]*", self.tmdb_sessionid, url)
        tmdb_results = requests.get(url).json()

        # page = tmdb_results.get("page", 0)
        # total = tmdb_results.get("total_pages", 0)
        # if page < total and "page=" in url:
        #     next_page = re.sub(r"page=\d+", f"page={page + 1}", url)
        # else:
        #     next_page = ""
        # next_page = re.sub("(?<=api_key=)[^&]*", "", next_page)
        # next_page = re.sub("(?<=session_id=)[^&]*", "", next_page)
        for item in tmdb_results["results"]:
            if item.get("known_for_department") == "Acting":
                if item.get("profile_path"):
                    photo = str("http://www.themoviedb.org/t/p/w300_and_h450_bestv2" + item.get("profile_path", ""))
                else:
                    photo = "people.png"
                self.list.append(
                    {
                     "name": item.get("name"),
                     "url": self.tmdb_person_link % str(item.get("id")),
                     "image": photo,
                     "action": "movies",
                    }
                )

        self.list = sorted(self.list, key=lambda k: utils.title_key(k["name"]))
        self.addDirectory(self.list)
        return self.list
 
 
    ### SCRAPERY API/STRON ###

    ### TMDB ###
    def tmdb_list(self, url):
        media_list = []
        # fflog(f'{params=}', 1, 1)
        # fflog(f'{url=}',1,1)

        url = re.sub("(?<=api_key=)[^&]*", self.tm_user, url)
        url = re.sub("(?<=session_id=)[^&]*", self.tmdb_sessionid, url)

        tmdb_results = requests.get(url).json()

        page = tmdb_results.get("page", 0)
        total = tmdb_results.get("total_pages", 0)
        if page < total and "page=" in url:
            next_page = re.sub(r"page=\d+", f"page={page + 1}", url)
        else:
            next_page = ""

        # next_page = re.sub("(?<=api_key=)[^&]*", "", next_page)
        # next_page = re.sub("(?<=session_id=)[^&]*", "", next_page)
        # fflog(f'{next_page=}')

        if not self.idx:
            # fflog(f'{self.idx=}',1,1)
            if ("/watchlist/" in url or "/favorite/" in url):
                # fflog(f'kolejne strony mogą być potrzebne')
                # tmdb_results = {'results': []}
                for np in range(2, total + 1):
                    fflog(f'{np=}')
                    next_url = re.sub(r"page=\d+", f"page={np}", url)
                    # fflog(f'{next_url=}',1,1)
                    tmdb_results_tmp = requests.get(next_url).json()  # kolejny request do serwera
                    [tmdb_results['results'].append(x) for x in tmdb_results_tmp['results']]  # dodanie wyników
            else:
                fflog(f'adres url nie jest objęty warunkiem pozyskiwania kolejnych podstron')
                pass

        if "results" in tmdb_results:
            items = tmdb_results["results"]
        elif "items" in tmdb_results:
            items = tmdb_results["items"]
        elif "parts" in tmdb_results:
            items = tmdb_results["parts"]
        elif "cast" in tmdb_results:
            items = tmdb_results["cast"]
        else:
            fflog(f'[tmdb_list] błąd: brak poprawnych danych do stworzenia listy  |  {tmdb_results=}')
            return media_list

        fflog(f'{len(items)=}',1,1)
        for item in items:
            # if item.get('original_language') != 'ru':
            if item.get("media_type") != "tv":
                media_list.append({
                                   "title": item.get("title", ""),
                                   "originaltitle": item.get("original_title", ""),
                                   "year": item.get("release_date", "")[0:4],
                                   "tmdb": str(item.get("id", "")),
                                   "plot": item.get("overview", ""),
                                   "votes": item.get("vote_count", ""),
                                   "rating": item.get("vote_average", ""),
                                   "tvdb": "0",
                                   "imdb": "0",
                                   "poster": "0",
                                   "next": next_page,
                                  })

        media_list = self.worker(media_list)
        return media_list


    ### TRAKT ###
    def trakt_list(self, url, user):
        try:
            page_max_items = 20

            pagination = 0
            if not "TRAKTNEXT" in url:
                pass
            else:
                pagination = str(url).split("TRAKTNEXT=")[1]
                url = str(url).split("TRAKTNEXT=")[0]
            media_list = []

            q = dict(urllib.parse_qsl(urllib.urlsplit(url).query))
            # tmdb_results = self.find_Movie_ID(q['query'])
            q.update({"extended": "full"})
            q = (urllib.urlencode(q)).replace("%2C", ",")
            u = url.replace("?" + urllib.urlparse(url).query, "") + "?" + q
            # u2 = f'https://api.trakt.tv/search/tmdb/%s?type=movie'

            result = trakt.getTraktAsJson(u)  # pobranie z serwera ?
            #fflog(f'{result=}')
            result2 = []
            for i in result:
                try:
                    if i.get('movie'):
                        result2.append(i)
                    elif i.get('ids'):
                        result2.append(i)
                except Exception:
                    pass
            try:
                if "/users/" in url and "/collection/" in url:
                    result2 = sorted(result2, key=lambda k: utils.title_key(k['movie']["title"]))
            except:
                pass
            # result = convert(result)
            items = []
            if not self.idx:
                page_max_items = 10000
            for i in result2[int(pagination):int(pagination) + page_max_items]:
                try:
                    items.append(i["movie"])
                except Exception:
                    pass
            if len(items) == 0:
                items = result2
        except Exception as e:
            fflog_exc(1)
            pass

        try:
            q = dict(urllib.parse_qsl(urllib.urlsplit(url).query))
            if not int(q["limit"]) == len(items):
                raise Exception()
            q.update({"page": str(int(q["page"]) + 1)})
            q = (urllib.urlencode(q)).replace("%2C", ",")
            next_page = url.replace("?" + urllib.urlparse(url).query, "") + "?" + q
        except:
            next_page = ""
        # fflog(f'[trakt_list] {next_page=}')

        if not next_page and self.idx:
            if len(result2[int(pagination):int(pagination) + 21]) == 21:
                next_page = url + "TRAKTNEXT=" + str(int(pagination) + page_max_items)
            else:
                self.next_page = False

        for item in items:
            #fflog(f'{item=}')
            try:
                imdb = item["ids"]["imdb"]
                if imdb is None or imdb == "":
                    #raise Exception()
                    continue
                imdb = "tt" + re.sub("[^0-9]", "", str(imdb))
                tmdb = str(item.get("ids", {}).get("tmdb", 0))

                year = item["year"]
                year = re.sub("[^0-9]", "", str(year))
                year_now = self.datetime.strftime("%Y")

                if int(year) > int(year_now):
                    #raise Exception()
                    continue

                title = item["title"]  # angielski tytuł
                title = client.replaceHTMLCodes(title)
                localtitle = title
                localtitle = trakt.getMovieTranslation(imdb, lang=self.lang) or title  # nie wiem, czy jest sens, bo i tak to zostanie pobrane z tmdb
                """
                country = item["country"]
                fflog(f'{country=}')
                aliases = trakt.getMovieAliases(imdb)  # kicha, bo może być kilka, więc nie wiadomo które to oryginlny
                fflog(f'{aliases=}')
                """
                try:
                    premiered = item["released"]
                except:
                    premiered = "0"
                try:
                    premiered = re.compile(r"(\d{4}-\d{2}-\d{2})").findall(premiered)[0]
                except:
                    premiered = "0"

                try:
                    genre = item["genres"]
                except:
                    genre = "0"
                genre = [i.title() for i in genre]
                if not genre:
                    genre = "0"
                genre = " / ".join(genre)

                try:
                    duration = str(item["runtime"])
                except:
                    duration = "0"
                if duration is None:
                    duration = "0"

                try:
                    rating = str(item["rating"])
                except:
                    rating = "0"
                if rating is None or rating == "0.0":
                    rating = "0"

                try:
                    votes = str(item["votes"])
                except:
                    votes = "0"
                try:
                    votes = str(format(int(votes), ",d"))
                except:
                    pass
                if votes is None:
                    votes = "0"

                try:
                    mpaa = item["certification"]
                except:
                    mpaa = "0"
                if mpaa is None:
                    mpaa = "0"

                try:
                    plot = item["overview"]
                except:
                    plot = "0"
                if plot is None:
                    plot = "0"
                plot = client.replaceHTMLCodes(plot)

                try:
                    tagline = item["tagline"]
                except:
                    tagline = "0"
                if tagline is None:
                    tagline = "0"
                tagline = client.replaceHTMLCodes(tagline)

                media_list.append(
                    {"title": localtitle, "originaltitle": title, "year": year, "premiered": premiered, "genre": genre,
                     "duration": duration, "rating": rating, "votes": votes, "mpaa": mpaa, "plot": plot,
                     "tagline": tagline, "imdb": imdb, "tmdb": tmdb, "tvdb": "0", "poster": "0", "next": next_page, })

            except Exception:
                fflog_exc(1)
                pass

        #fflog(f'{media_list=}')
        media_list = self.worker(media_list)  # aby wzbogacić o informacje z tmdb
        return media_list


    ### IMDB ###
    def imdb_list(self, url):
        media_list = []
        fflog(f'[imdb_list] {url=}')

        for i in re.findall(r"date\[(\d+)]", url):
            url = url.replace("date[%s]" % i, (self.datetime - datetime.timedelta(days=int(i))).strftime("%Y-%m-%d"), )
            fflog(f'[imdb_list] {url=}')

        def imdb_watchlist_id(url):  # na razie (albo już) nieużywane
            # fflog(f'[imdb_list][imdb_watchlist_id] {url=}')
            resp = client.request(url)
            # fflog(f'[imdb_list][imdb_watchlist_id] {resp=}')
            if resp:
                resp1 = client.parseDOM(resp, "meta", ret="content", attrs={"property": "pageId"}, )
            # fflog(f'[imdb_list][imdb_watchlist_id] {resp1=}')
            if resp1:
                return resp1[0]
            else:
                return []  # nie wiem, czy to dobry zwrot
            # return resp  # kod HTML

        # fflog(f'[imdb_list] {url=}')
        if url == self.imdbwatchlist_link:
            fflog(f'[imdb_list] imdbwatchlist  (wariant 0)')
            pass
        elif url == self.imdbwatchlist1_link:
            fflog(f'[imdb_list] imdbwatchlist1 (wariant 1)')
            # coś się zmieniło na stronie IMDb - może to już niepotrzebne
            # url = cache.get(imdb_watchlist_id, 8640, url)
            # url = self.imdblist1_link % url
            pass
        elif url == self.imdbwatchlist2_link:
            fflog(f'[imdb_list] imdbwatchlist2')
            # coś się zmieniło na stronie IMDb - może to już niepotrzebne
            # url = cache.get(imdb_watchlist_id, 8640, url)
            # url = self.imdblist2_link % url
            pass
        else:
            # to nie jest watchlista
            pass
        # fflog(f'[imdb_list] {url=}')

        result = client.request(url, headers={'Accept-Language': 'pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7'})
        # result = result.replace("\n", " ")
        # fflog(f'[imdb_list] {result=}')
        if not result:
            fflog(f'{result=}')
            return

        # check if list is private
        private_list = client.parseDOM(result, "h3", attrs={"class": "ipc-title__text"})
        if private_list and "rivate list" in private_list[0]:
            # fflog(f'[imdb_list] {re.sub("<[^>]+>", "", private_list[0])}')
            fflog(f'[imdb_list] {client.replaceHTMLCodes(private_list[0])}')
            private_list_description = client.parseDOM(result, "div", attrs={"class": "ipc-title__description"})
            if private_list_description:
                fflog(f'[imdb_list] description: {private_list_description[0]}')
            control.infoDialog('Private list\n'+private_list_description[0], 'IMDb', "WARNING", 5000)
            control.sleep(5000)
            return

        jsdata = client.parseDOM(result, "script", attrs={"type": "application/json"})
        try:
            jsdata = json.loads(jsdata[0])
            # fflog(f'jsdata={json.dumps(jsdata, indent=4)}',1,1)
        except Exception:
            fflog_exc(1)
            jsdata = {}

        js_items = {}
        if jsdata:
            try:
                js_items = jsdata['props']['pageProps']
                # fflog(f'js_items={json.dumps(js_items, indent=4)}',1,1)
            except Exception:
                fflog_exc(1)

            jsdata = None

            if js_items:
                if "/list/" in url:
                    try:
                        js_items = js_items['mainColumnData']['list']['titleListItemSearch']['edges']  # pasuje do watchlist
                    except Exception:
                        fflog_exc(1)
                elif "/user/" in url:
                    try:
                        js_items = js_items['mainColumnData']['predefinedList']['titleListItemSearch']['edges']  # pasuje do watchlist
                    except Exception:
                        fflog_exc(1)
                else:
                    try:
                        js_items = js_items['searchResults']['titleResults']['titleListItems']  # pasuje do Oskarów
                    except Exception:
                        fflog_exc(1)

                fflog(f'{len(js_items)=}', 1,1)

        items = []
        #items = client.parseDOM(result, "div", attrs={"class": "lister-item .+?"})
        # items = client.parseDOM(result, "ul", attrs={"class": "ipc-metadata-list .+?"})
        # fflog(f'[imdb_list] {items=}')
        #items += client.parseDOM(result, "div", attrs={"class": "list_item.+?"})
        items += client.parseDOM(result, "li", attrs={"class": "ipc-metadata-list-summary-item"})  # każdy tytuł z osobna
        fflog(f'[imdb_list] {len(items)=}')

        if len(js_items) >= len(items):
            items = js_items

        next_page = ""
        """
        try:  # tylko, że teraz paginacja jest poprzez dynamiczne doczytywanie, więc to już nie działa Trzeba by podejrzeć, co przeglądarka wysyła i z tym kombinować.
            next_page = client.parseDOM(result, "a", ret="href", attrs={"class": ".+?ister-page-nex.+?"})
            if len(next_page) == 0:
                next_page = client.parseDOM(result, "div", attrs={"class": "pagination"})[0]
                next_page = zip(client.parseDOM(next_page, "a", ret="href"), client.parseDOM(next_page, "a"))
                next_page = [i[0] for i in next_page if "Next" in i[1]]
            next_page = url.replace(urllib.urlparse(url).query, urllib.urlparse(next_page[0]).query)
            next_page = client.replaceHTMLCodes(next_page)
        # next_page = next_page.encode("utf-8")
        except Exception:
            # fflog_exc(1)
            fflog(f'[imdb_list] brak paginacji')
            next_page = ""
        """
        
        result = None

        fflog(f'[imdb_list] zatem {len(items)=}')
        for item in items:
            # fflog(f'[imdb_list] {item=}')
            try:
                if items is js_items:
                    if "/user/" in url or "/list/" in url:
                        title = item['listItem']['titleText']['text']
                        originaltitle = item['listItem']['originalTitleText']['text']
                    else:
                        title = item['titleText']
                        originaltitle = item['originalTitleText']
                else:
                    title = client.parseDOM(item, "a")[1]  # bo pierwszy link, to obrazek
                    # fflog(f'[imdb_list] {title=}')
                    title = client.parseDOM(title, "h3", attrs={"class": "ipc-title__text"})[0]
                    title = client.replaceHTMLCodes(title)
                    title = re.sub(r"^\d+\. ", "", title)
                    # title = title.encode("utf-8").decode()
                    originaltitle = title
                # fflog(f'{title=}',1,1)

                # to się przydaje dla watchlist, ale nie wiem, czy nie popsuje list nagród (Oskarów, Malin itd)
                if items is js_items:
                    if "/user/" in url or "/list/" in url:
                        # content_type = item['listItem']['titleType']['id']  # "movie"
                        content_type = item['listItem']['titleType']['text']  # "Movie"
                    else:
                        # content_type = item['titleType']['id']  # "movie"
                        content_type = item['titleType']['text']  # ""
                else:
                    content_type = client.parseDOM(item, "span", attrs={"class": ".+? dli-title-type-data"})
                    content_type = content_type[0] if content_type else ""
                    # fflog(f'[imdb_list] {content_type=}')
                if content_type and content_type.lower() != "movie":  # przy filmach nie powinno tego być (gdy scrapujemy)
                    # fflog(f'to nie jest film {title=}  {content_type=}', 1, 1)
                    continue

                if items is js_items:
                    if "/user/" in url or "/list/" in url:
                        year = item['listItem']['releaseYear']['year']
                    else:
                        year = item['releaseYear']
                    year = str(year)
                else:
                    #year = client.parseDOM(item, "span", attrs={"class": "lister-item-year.+?"})
                    year = client.parseDOM(item, "span", attrs={"class": ".+? dli-title-metadata-item"})
                    #year += client.parseDOM(item, "span", attrs={"class": "year_type"})  # chyba już nie ma czegoś takiego (nawet nie wiem, co to było)
                    # fflog(f'[imdb_list] {year=}')
                    try:
                        if type(year) == list:
                            year = year[0]
                        year = re.compile(r"(\d{4})").findall(year)[0]
                    except:
                        year = "0"
                    # year = year.encode("utf-8")
                # fflog(f'[imdb_list] {year=} | {self.datetime.strftime("%Y")=}')
                if int(year) > int(self.datetime.strftime("%Y")):  # to coś pomija, ale dlaczego?
                    fflog(f' {int(year)=}  >  {int(self.datetime.strftime("%Y"))=} | {title=}')
                    #raise Exception()
                    # continue
                    pass

                if items is js_items:
                    if "/user/" in url or "/list/" in url:
                        imdb = item['listItem']['id']
                    else:
                        imdb = item['titleId']
                else:
                    imdb = client.parseDOM(item, "a", ret="href")[0]
                    imdb = re.findall(r"(tt\d*)", imdb)[0]
                    # imdb = imdb.encode("utf-8")

                genre = duration = rating = votes = mpaa = director = cast = plot = poster = "0"

                r""" reszta niepotrzebna bo i tak zostanie pobrana z super_info (chyba, że nie będzie tego w bazie tmdb, to wówczas warto)
                try:
                    poster = client.parseDOM(item, "img", ret="src")[0]
                except:
                    poster = "0"
                if "/nopicture/" in poster:
                    poster = "0"
                poster = re.sub(r"(?:_SX|_SY|_UX|_UY|_CR|_AL)(?:\d+|_).+?\.", "_SX500.", poster)
                poster = client.replaceHTMLCodes(poster)
                # poster = poster.encode("utf-8")

                try:
                    genre = client.parseDOM(item, "span", attrs={"class": "genre"})[0]
                except:
                    genre = "0"
                genre = " / ".join([i.strip() for i in genre.split(",")])
                if genre == "":
                    genre = "0"
                genre = client.replaceHTMLCodes(genre)
                # genre = genre.encode("utf-8")

                try:
                    duration = re.findall(r"(\d+?) min(?:s|)", item)[-1]
                except:
                    duration = "0"
                # duration = duration.encode("utf-8")

                rating = "0"
                try:
                    rating = client.parseDOM(item, "span", attrs={"class": "rating-rating"})[0]
                except:
                    pass
                try:
                    rating = client.parseDOM(rating, "span", attrs={"class": "value"})[0]
                except:
                    rating = "0"
                try:
                    rating = client.parseDOM(item, "div", ret="data-value", attrs={"class": ".*?imdb-rating"})[0]
                except:
                    pass
                if rating == "" or rating == "-":
                    rating = "0"
                rating = client.replaceHTMLCodes(rating)
                # rating = rating.encode("utf-8")

                try:
                    votes = client.parseDOM(item, "div", ret="title", attrs={"class": ".*?rating-list"})[0]
                except:
                    votes = "0"
                try:
                    votes = re.findall(r"\((.+?) vote(?:s|)\)", votes)[0]
                except:
                    votes = "0"
                if votes == "":
                    votes = "0"
                votes = client.replaceHTMLCodes(votes)
                # votes = votes.encode("utf-8")

                try:
                    mpaa = client.parseDOM(item, "span", attrs={"class": "certificate"})[0]
                except:
                    mpaa = "0"
                if mpaa == "" or mpaa == "NOT_RATED":
                    mpaa = "0"
                mpaa = mpaa.replace("_", "-")
                mpaa = client.replaceHTMLCodes(mpaa)
                # mpaa = mpaa.encode("utf-8")

                try:
                    director = re.findall(r"Director(?:s|):(.+?)(?:\||</div>)", item)[0]
                except:
                    director = "0"
                director = client.parseDOM(director, "a")
                director = " / ".join(director)
                if director == "":
                    director = "0"
                director = client.replaceHTMLCodes(director)
                # director = director.encode("utf-8")

                try:
                    cast = re.findall(r"Stars(?:s|):(.+?)(?:\||</div>)", item)[0]
                except:
                    cast = "0"
                cast = client.replaceHTMLCodes(cast)
                # cast = cast.encode("utf-8")
                cast = client.parseDOM(cast, "a")
                if not cast:
                    cast = "0"

                plot = "0"
                try:
                    plot = client.parseDOM(item, "p", attrs={"class": "text-muted"})[0]
                except:
                    pass
                try:
                    plot = client.parseDOM(item, "div", attrs={"class": "item_description"})[0]
                except:
                    pass
                plot = plot.rsplit("<span>", 1)[0].strip()
                plot = re.sub("<.+?>|</.+?>", "", plot)
                if plot == "":
                    plot = "0"
                plot = client.replaceHTMLCodes(plot)
                # plot = plot.encode("utf-8")
                """

                #media_list.append(
                media_item = (
                    {
                    "title": title,  # tytuły mogą być angielskie
                    "originaltitle": originaltitle,
                    "year": year,
                    "genre": genre,
                    "duration": duration,
                    "rating": rating,
                    "votes": votes,
                    "mpaa": mpaa,
                    "director": director,
                    "cast": cast,
                    "plot": plot,
                    "tagline": "0",
                    "imdb": imdb,
                    "tmdb": "0", "tvdb": "0",  # to chyba oznacza, że pobrano z imdb, a nie z innych (taka identyfikacja)
                    "poster": poster,
                    "next": next_page,
                    }
                )
                # fflog(f'[imdb_list] {media_item=}')
                # fflog( "[imdb_list] " + "media_item=\n" + ("\n"+chr(32)).join(map(repr, media_item.items())) )
                media_list.append(media_item)

            except Exception as e:
                print(e)
                fflog_exc(1)
                pass

        # fflog(f'[imdb_list] {media_list=}')
        media_list = self.worker(media_list)  # uzupełnienie danych z super_info
        return media_list


    ### MOJE FILMY - LISTY FILMÓW ###
    ## Listy Użytkownika (TRAKT + IMDB + TMDB)
    def userlists(self):
        fflog(f'{params=}', 1, 1)
        try:
            userlists = []
            # fflog(f'{trakt.getTraktCredentialsInfo()=}')
            if not trakt.getTraktCredentialsInfo():
                raise Exception()
                # activity = trakt.getActivity()
                # fflog(f'{activity=}')
        except Exception:
            fflog_exc(1)
            pass

        try:
            self.list = []
            if self.imdb_user == "":
                raise Exception()
            userlists += cache.get(self.imdb_user_list, 24, self.imdblists_link)
        except Exception:
            #fflog_exc(1)
            pass

        try:
            self.list = []
            if self.tmdb_sessionid == "":
                raise Exception()
            userlists += cache.get(self.tmdblist, 24, self.tmdb_user_lists)
        except Exception:
            #fflog_exc(1)
            pass

        try:
            self.list = []
            if not trakt.getTraktCredentialsInfo():
                raise Exception()
            try:
                #fflog(f'{self.traktlists_link=} {self.trakt_user=}')
                cache_timeout = cache.timeout(self.trakt_user_list, self.traktlists_link, self.trakt_user)
                #fflog(f'{cache_timeout=} {trakt.getActivity()=}')
                if not cache_timeout:
                    lists = cache.get(self.trakt_user_list, 24, self.traktlists_link, self.trakt_user)
                    #fflog(f'1 {lists=}')
                    userlists += lists
                else:
                    if trakt.getActivity() > cache.timeout(self.trakt_user_list, self.traktlists_link, self.trakt_user):
                        raise Exception()
                    else:
                        lists = cache.get(self.trakt_user_list, 24, self.traktlists_link, self.trakt_user)
                        #fflog(f'2 {lists=}')
                        userlists += lists
            except Exception:
                lists = cache.get(self.trakt_user_list, 0, self.traktlists_link, self.trakt_user)
                #fflog(f'3 {lists=}')
                userlists += lists
        except Exception:
            #fflog_exc(1)
            pass

        try:
            self.list = []
            if not trakt.getTraktCredentialsInfo():
                raise Exception()
            try:
                #fflog(f'{self.traktlikedlists_link=} {self.trakt_user=}')
                cache_timeout = cache.timeout(self.trakt_user_list, self.traktlikedlists_link, self.trakt_user)
                #fflog(f'{cache_timeout=} {trakt.getActivity()=}')
                if not cache_timeout:
                    userlists += cache.get(self.trakt_user_list, 24, self.traktlikedlists_link, self.trakt_user)
                else:
                    if trakt.getActivity() > cache.timeout(self.trakt_user_list, self.traktlikedlists_link, self.trakt_user):
                        raise Exception()
                    else:
                        userlists += cache.get(self.trakt_user_list, 24, self.traktlikedlists_link, self.trakt_user)
            except Exception:
                userlists += cache.get(self.trakt_user_list, 0, self.traktlikedlists_link, self.trakt_user)
        except Exception:
            #fflog_exc(1)
            pass

        self.list = userlists
        for i in range(0, len(self.list)):
            self.list[i].update({"action": "movies"})
        self.list = sorted(self.list, key=lambda k: utils.title_key(k["name"]))
        # fflog(f'{self.list=}')
        # fflog(f' self.list={json.dumps(self.list, indent=2)}')
        self.addDirectory(self.list, queue=True, add_refresh=True)
        return self.list


    ### TRAKT ###
    def trakt_user_list(self, url, user):
        try:
            items = trakt.getTraktAsJson(url)
        except Exception:
            fflog_exc(1)
            pass

        for item in items:
            try:
                try:
                    name = item["list"]["name"]
                except:
                    name = item["name"]
                name = client.replaceHTMLCodes(name)

                try:
                    url = (trakt.slug(item["list"]["user"]["username"]), item["list"]["ids"]["slug"],)
                except:
                    url = ("me", item["ids"]["slug"])
                url = self.traktlist_link % url
                # url = url.encode("utf-8")
                #fflog(f'{url=}')

                self.list.append({"name": name, "url": url, "context": url, "image": "trakt.png", })
            except Exception:
                fflog_exc(1)
                pass

        self.list = sorted(self.list, key=lambda k: utils.title_key(k["name"]))

        return self.list


    ## TMDB##
    def tmdblist(self, url):
        # url = self.tmdb_user_lists
        url = re.sub("(?<=api_key=)[^&]*", self.tm_user, url)
        url = re.sub("(?<=session_id=)[^&]*", self.tmdb_sessionid, url)
        tmdb_results = requests.get(url).json()

        # page = tmdb_results.get("page", 0)
        # total = tmdb_results.get("total_pages", 0)
        r"""
        if page < total and "page=" in url:
            next_page = re.sub(r"page=\d+", f"page={page + 1}", url)
        else:
            next_page = ""
        """
        # next_page = re.sub("(?<=api_key=)[^&]*", "", next_page)
        # next_page = re.sub("(?<=session_id=)[^&]*", "", next_page)
        # fflog(f'{next_page=}')

        if "results" in tmdb_results:
            items = tmdb_results["results"]
        elif "items" in tmdb_results:
            items = tmdb_results["items"]
        elif "parts" in tmdb_results:
            items = tmdb_results["parts"]
        elif "cast" in tmdb_results:
            items = tmdb_results["cast"]

        for item in items:
            # if item.get('original_language') != 'ru':
            self.list.append({
                "name": item.get("name"),
                "url": self.tmdb_lists_link % str(item.get("id")),
                "context": self.tmdb_lists_link % str(item.get("id")),
                "image": "tmdb.png",
                # "next": next_page,
                })

        # self.addDirectory(self.list)
        self.list = sorted(self.list, key=lambda k: utils.title_key(k["name"]))

        return self.list


    ### IMDB ###
    def imdb_user_list(self, url):  # to nie jest watchlista - to są listy użytkownika
        # fflog(f'[imdb_user_list] {url=}')
        try:
            result = client.request(url)
            # fflog(f'[imdb_user_list] {result=}')
            items = client.parseDOM(result, "li", attrs={"class": "ipc-metadata-list-summary-item"})
        except Exception:
            fflog_exc(1)
            items = []
            pass
        # fflog(f'[imdb_user_list] {len(items)=}')
        for item in items:
            # fflog(f'[imdb_user_list] {item=}')
            try:
                name = client.parseDOM(item, "a", attrs={"class": "ipc-metadata-list-summary-item__t"})[0]
                # fflog(f'[imdb_user_list] {name=}')
                name = client.replaceHTMLCodes(name)
                # name = name.encode("utf-8")
                # fflog(f'[imdb_user_list] {name=}')

                url = client.parseDOM(item, "a", ret="href", attrs={"class": "ipc-metadata-list-summary-item__t"})[0]  # choć tu class nie jest potrzebne
                # fflog(f'[imdb_user_list] {url=}')
                url = url.split("/list/", 1)[-1].strip("/")
                # fflog(f'[imdb_user_list] {url=}')
                url = self.imdblist1_link % url
                # fflog(f'[imdb_user_list] {url=}')
                url = client.replaceHTMLCodes(url)
                # fflog(f'[imdb_user_list] {url=}')
                # url = url.encode("utf-8")

                self.list.append({"name": name, "url": url, "context": url, "image": "imdb.png", })
            except Exception:
                fflog_exc(1)
                pass
        # fflog(f'[imdb_user_list] {len(self.list)=}')
        self.list = sorted(self.list, key=lambda k: utils.title_key(k["name"]))
        return self.list


    ### GET ###
    def get(self, url, idx=True, create_directory=True, refresh=None):
        """ tworzy różne katalogi (wirtualne) Kodi """

        # debug
        if not "http" in url: 
            fflog(f'{params=}', fn=True)
            pass
        else:
            if not _is_debugging():
                fflog(f'params={({**params, "url": "*"})}', 1, 1)
                pass
            else:
                fflog(f'params={({**params, "url": url})}', 0)

        self.idx = idx

        # sys.path.append("D:\PyCharm 2022.1.4\debug-eggs\pydevd-pycharm.egg")
        # import pydevd_pycharm
        # pydevd_pycharm.settrace('localhost', port=5678, stdoutToServer=True, stderrToServer=True)

        try:
            # if re.search("api_key=(&|$)", url):
            url = re.sub("(?<=api_key=)[^&]*", self.tm_user, url)
            url = re.sub("(?<=session_id=)[^&]*", self.tmdb_sessionid, url)

            # convert "meta" URL (like `tmdb_trending`) to full URL (like link form `self.tmdb_trending_link`)
            url = getattr(self, url + "_link", url)
            u = urllib.urlparse(url).netloc.lower()
            #control.log(f'{url=}', 1)

            if u in self.trakt_link and "/users/" in url:
                try:
                    if url == self.trakthistory_link:
                        raise Exception()
                    # if not "/users/me/" in url:
                    #     raise Exception()
                    if not self.idx:
                        self.list = cache.get(self.trakt_list, 0, url, self.trakt_user)
                    else:
                        cache_timeout = cache.timeout(self.trakt_list, url, self.trakt_user)
                        cache_timeout = 0 if refresh else cache_timeout  # nie wiem, czy to jest w ogóle potrzebne, bo tu jest to jakoś inaczej rozwiązane niż w serialach
                        if not cache_timeout or "TRAKTNEXT" in url or "page=" in url:
                            self.list = cache.get(self.trakt_list, 720, url, self.trakt_user)
                            if self.list and self.next_page and self.list[0].get("next"):
                                thread = Thread(target=cache.get, args=(self.trakt_list, 720, self.list[0].get("next"), self.trakt_user))
                                thread.start()
                        else:
                            if trakt.getActivity() > cache_timeout:
                                raise Exception()
                            else:
                                self.list = cache.get(self.trakt_list, 720, url, self.trakt_user)
                except Exception:
                    self.list = cache.get(self.trakt_list, 0, url, self.trakt_user)
                    if self.list and self.next_page and self.list[0].get("next"):
                        thread = Thread(target=cache.get, args=(self.trakt_list, 0, self.list[0].get("next"), self.trakt_user))
                        thread.start()

                if "/users/" in url and "/collection/" in url:
                    if self.list:
                        self.list = sorted(self.list, key=lambda k: utils.title_key(k["title"]))

                # if idx:  #     self.worker()

            elif u in self.tmdb_link:
                if not self.idx:
                    self.list = cache.get(self.tmdb_list, 0, url)
                else:
                    if "/watchlist/" in url or "/favorite/" in url:
                        cache_timeout = 0 if refresh else 1
                        self.list = cache.get(self.tmdb_list, cache_timeout, url)
                    else:
                        self.list = cache.get(self.tmdb_list, 24, url)
                        if self.list and self.next_page and self.list[0].get("next"):
                            thread = Thread(target=cache.get, args=(self.tmdb_list, 24, self.list[0].get("next")))
                            thread.start()

            elif u in self.trakt_link:
                self.list = cache.get(self.trakt_list, 24, url, self.trakt_user)  # if idx:  #     self.worker()
                if self.list and self.next_page and self.list[0].get("next"):
                    thread = Thread(target=cache.get, args=(self.trakt_list, 24, self.list[0].get("next"), self.trakt_user))
                    thread.start()

            elif u in self.imdb_link and ("/user/" in url or "/list/" in url):  # a /watchlist/ ? - /user/ wystarczy
                # fflog(f'imdb /user/ lub /list/  {u=}  {url=}')
                # fflog(f'{self.idx=}')
                if not self.idx or refresh:
                    self.list = cache.get(self.imdb_list, 0, url)
                else:
                    self.list = cache.get(self.imdb_list, 1, url)  # if idx:  #     self.worker()
                    if self.list and self.next_page and self.list[0].get("next"):
                        fflog(f'{self.list[0].get("next")=}')
                        thread = Thread(target=cache.get, args=(self.imdb_list, 1, self.list[0].get("next")))
                        thread.start()

            elif u in self.imdb_link:
                # fflog(f'imdb inny  {u=}  {url=}')
                self.list = cache.get(self.imdb_list, 24, url)  # if idx:  #     self.worker()
                #fflog(f'{self.list=}')
                if self.list and self.next_page and self.list[0].get("next"):
                    fflog(f'{self.list[0].get("next")=}')
                    thread = Thread(target=cache.get, args=(self.imdb_list, 24, self.list[0].get("next")))
                    thread.start()

            if idx is True and create_directory is True:
                if self.list:
                    self.movieDirectory(self.list)
                else:
                    import xbmcgui
                    xbmcgui.Dialog().notification('Błąd', 'Nic nie znaleziono', xbmcgui.NOTIFICATION_ERROR)
                    fflog( 'nic nie znaleziono', 0)
                    fflog(f'{params=}', 0)
                    fflog(f'{url=}', 0)
                    navigator.navigator().endDirectory()
                    control.execute('Action(Back)')

            return self.list
        except Exception as e:
            print(e)
            fflog_exc(1)
            return


    ### WORKER ###
    def worker(self, media_list=[], level=1):
        from threading import Thread
        from resources.lib.indexers.super_info import SuperInfo
        super_info_media_list = []
        # self.meta = []
        if not media_list:
            media_list = self.list
        total = len(media_list) if media_list else 0
        # fflog(f'{len(media_list)=}  {media_list=}')
        # for i in range(0, total):
        #     self.list[i].update({"metacache": False})
        #
        # self.list = metacache.fetch(self.list, self.lang, self.user)
        #
        # for i in range(total):
        #     self.list[i]["metacache"] = False
        #
        # self.list = metacache.fetch(self.list, self.lang, self.user)
        # log_utils.fflog(f"{len(media_list)=} {media_list=}")
        for r in range(0, total, 20):

            threads = {super_info_obj: Thread(target=super_info_obj.get_info, args=(i,)) for i in
                       range(r, min(total, r + 20)) for super_info_obj in
                       (SuperInfo(media_list, self.session, self.lang),)}

            [i.start() for i in threads.values()]
            [i.join() for i in threads.values()]

            for super_info_obj in threads:
                if super_info_obj.meta:
                    super_info_media_list.append(super_info_obj.meta[0].get('item'))

            # if self.meta:  #     metacache.insert(self.meta)
        # fflog(f'{len(super_info_media_list)=}  {super_info_media_list=}')
        return super_info_media_list


    def get_meta_for_movie(self, imdb=None, tmdb=None):
        try:
            meta = cache.cache_get("superinfo" + f"_{tmdb or imdb}")  # sprawdzenie, czy nie ma już w cache
            if not meta:
                log_utils.fflog('próba pobrania informacji o filmie przez super_info.py')
                from resources.lib.indexers.super_info import SuperInfo
                media_list = [{'tmdb': tmdb, 'imdb': imdb}]
                import requests
                session = requests.Session()
                lang = control.apiLanguage()["tmdb"]
                super_info_obj = SuperInfo(media_list, session, lang, "movie")
                super_info_obj.get_info(0)

                meta = cache.cache_get("superinfo" + f"_{tmdb or imdb}")
            if meta:
                from ast import literal_eval
                meta = meta["value"]
                meta = literal_eval(meta)
            else:
                meta = {}
        except Exception:
            meta = {}
            fflog_exc(1)
        return meta


    ### MOVIE DIR ###
    def movieDirectory(self, items):
        # sys.path.append("D:\PyCharm 2022.1.4\debug-eggs\pydevd-pycharm.egg")
        # import pydevd_pycharm
        # pydevd_pycharm.settrace('localhost', port=5678, stdoutToServer=True, stderrToServer=True)
        if items is None or len(items) == 0:
            sys.exit()

        sysaddon = sys.argv[0]
        syshandle = int(sys.argv[1])

        if control.setting("zastepcze_grafiki") == "true":
            addonPoster =  control.addonPoster()
            addonFanart = control.addonFanart()
            addonBanner = control.addonBanner()
        else:
            addonPoster = addonFanart = addonBanner = ""

        settingFanart =  control.setting("fanart")

        multi_select = []
        try:
            isOld = False
            control.item().getArt("type")
        except:
            isOld = True
        add_year = control.setting("titles.add_year") == "true"
        generate_short_path = control.setting("generate_short_path") == "true"
        # isFolder = False if control.setting("hosts.mode") == "0" else True
        isFolder = False if control.setting("hosts.mode") != "1" else True
        #isPlayable = "true" if "plugin" not in control.infoLabel("Container.PluginName") else "false"  # dziwny ten warunek (ale chyba pozwalał omijać setResolvedUrl)
        isPlayable = "true" if not isFolder else "false"
        playbackMenu = control.lang(32063) if control.setting("hosts.mode") == "2" else control.lang(32064)
        dont_use_setResolvedUrl = control.setting("player.dont_use_setResolvedUrl") == "true"
        # fflog(f'{action=}')
        indicators = playcount.getMovieIndicators(refresh=True) if action == "movies" else playcount.getMovieIndicators()
        # fflog(f'{indicators=}')
        traktCredentials = trakt.getTraktCredentialsInfo()
        traktIndicators  = trakt.getTraktIndicatorsInfo()
        watchedMenu =   control.lang(32068) if traktIndicators is True else control.lang(32066)
        unwatchedMenu = control.lang(32069) if traktIndicators is True else control.lang(32067)
        indicator_kodi = control.setting("indicator.kodi") == "true"
        queueMenu = control.lang(32065)
        traktManagerMenu = control.lang(32070)
        nextMenu = control.lang(32053)
        addToLibrary = control.lang(32551)
        addMultiToLibrary = control.lang(32635)
        kodiver = source_utils.get_kodi_version()
        # fflog(f'{kodiver.version=}')
        # fflog(f'{kodiver.major=} {kodiver.minor=}')

        # TODO: add options, example: label2Mask="[%D]|[%Y]"  # https://github.com/retrospect-addon/kodi.emulator.ascii/blob/master/xbmcplugin.py
        addSortMethod(syshandle, sortMethod=SORT_METHOD_UNSORTED, labelMask="%L")  # pokazuje napis "Domyślny", ale nie sortuje
        addSortMethod(syshandle, sortMethod=SORT_METHOD_PLAYLIST_ORDER, labelMask="%L")  # wykorzystuje countera
        addSortMethod(syshandle, sortMethod=SORT_METHOD_VIDEO_YEAR, labelMask="%L")
        addSortMethod(syshandle, sortMethod=SORT_METHOD_TITLE, labelMask="%L")
        addSortMethod(syshandle, sortMethod=SORT_METHOD_DURATION, labelMask="%L")
        addSortMethod(syshandle, sortMethod=SORT_METHOD_VIDEO_RATING, labelMask="%L")

        downloads = (
            control.setting("downloads") == "true"
            and not (
                control.setting("movie.download.path") == ""
                or control.setting("tv.download.path") == ""
            )
        )
        downloadMenu = control.lang(32403)

        unpremiered_color = control.setting("unpremiered_color")
        if unpremiered_color == "inny":
            unpremiered_color = control.setting("unpremiered_custom_color")
        else:
            colors_map = {
                "szary": "gray",
                "czerwony": "red",
                "fioletowy": "magenta",
                "pomarańczowy": "orange",
                }
            unpremiered_color = colors_map[unpremiered_color]
        # fflog(f'{unpremiered_color=}')

        counter = 1
        for i in items:

            def has(key):
                val = i.get(key)
                return val and val != "0"

            try:
                label = "{} ({})".format(i.get("label") or i.get("title"), i["year"])  # to display
                title = i.get("title")
                label = title if title and not add_year else label.replace(" ()", "", 1)
                if not label:
                    continue
                # syslabel = quote_plus(label)

                title, year = i["originaltitle"], i["year"]

                imdb, tmdb = i["imdb"], i["tmdb"]

                # prepare to context menu url
                sysname = urllib.quote_plus("{} ({})".format(title, year))
                systitle = urllib.quote_plus(title)
                syslocaltitle = urllib.quote_plus(i.get("title"))

                meta = {k: v for k, v in i.items() if not v == "0"}  # budowanie mety

                meta.pop("next", None)  # to chyba niepotrzebne tu, więc out

                meta.update({"imdbnumber": imdb})
                # meta.update({"code": tmdb})  # "code" to coś innego oznacza 
                # meta.update({"code": imdb, "imdbnumber": imdb, "imdb_id": imdb})
                # meta.update({"tmdb_id": tmdb})

                meta.update({"mediatype": "movie"})

                # meta.update({"trailer": "%s?action=trailer&name=%s" % (sysaddon, urllib.quote_plus(label))})
                meta.update({"trailer": "%s?action=trailer&name=%s&url=%s" % (sysaddon, urllib.quote_plus(label), urllib.quote_plus(meta.get("trailer") or ""))})
                # meta.update({'trailer': 'plugin://script.extendedinfo/?info=playtrailer&&id=%s' % imdb})  # zależne od pluginu extendedinfo

                if "duration" not in i:
                    # meta.update({"duration": "120"})  # nie wiem, czy trzeba wstawiać wymyślone
                    # meta.update({"duration": "1"})  # jeśli coś trzeba wstawić, to może tylko 1 sekundę wystarczy ?
                    pass
                elif i["duration"] == "0":
                    # meta.update({"duration": "120"})
                    # meta.update({"duration": "1"})
                    pass
                try:
                    if meta.get("duration") and meta.get("duration") != "0":
                        meta.update({"duration": str(int(meta["duration"]) * 60)})  # docelowo ma być w sekundach
                except:
                    pass

                poster = [i[x] for x in ["poster3", "poster", "poster2"] if i.get(x, "0") != "0"]
                poster = poster[0] if poster else addonPoster
                meta["poster"] = poster

                # eksperymenty
                icon = i.get("icon") or i.get("discart") or poster  # tylko nie wiem, czy preferowany jest kwadrat, czy prostokąt
                thumb = i.get("thumb") or i.get("fanart") or i.get("landscape") or poster  # j. w. (wg wiki to prostokąt https://kodi.wiki/view/Artwork_types )
                # ponieważ grafiki dużo ważą, może jednak zostawić pusto ?
                icon = i.get("icon") or ""
                thumb = i.get("thumb") or ""

                # try:
                #     meta.update({"genre": cleangenre.lang(meta["genre"], self.lang)})
                # except:
                #     pass

                # fflog(f'{meta.get("genre")=}')
                # fflog(f'{meta.get("country")=}')
                # fflog(f'{meta.get("originalname")=}')
                anime = False
                if meta.get("country") in ["Japan", "China", "Korea"]:
                    if any(i in meta.get("genre") for i in ["Animacja", "Fantasy", "Anime"]):
                        if source_utils.czy_litery_krzaczki(meta.get("originalname", "")):
                            anime = True

                premiered = meta.get("premiered", 0)
                if not premiered or int(re.sub("[^0-9]", "", str(premiered))) > int(re.sub("[^0-9]", "", str(self.today_date))):
                    label = f"[COLOR {unpremiered_color}][I]%s[/I][/COLOR]" % label

                if not anime:
                    if meta.get("local_premieres"):
                        local_premiered = next(
                                (i.get("release_date").split("T")[0]
                                for i in meta.get("local_premieres")
                                if i.get("type") >=3)  # 3 to kinowa
                            ,"")
                        meta["premiered"] = local_premiered or meta.get("premiered", "")

                meta = convert(meta)

                sysmeta = urllib.quote_plus(json.dumps(meta))

                # url = "{}?action=play&title={}&localtitle={}&year={}&imdb={}&tmdb={}&meta={}&t={}".format(sysaddon, systitle, syslocaltitle, year or "", imdb, tmdb, sysmeta, self.systime, )
                url = "{}?action=play&title={}&localtitle={}&year={}&imdb={}&tmdb={}&meta={}".format(sysaddon, systitle, syslocaltitle, year or "", imdb, tmdb, sysmeta, )
                sysurl = urllib.quote_plus(url)  # potrzebne dla context menu
                fullpath = ""
                if generate_short_path and isFolder:  # zastanowić się nad isFolder
                    fullpath = url
                    url = "{}?action=play&item={}".format(sysaddon, counter)
                    #sysurl = urllib.quote_plus(url)  # czy trzeba ?  bo może bardziej zaszkodzi
                    pass

                # path = "{}?action=play&title={}&year={}&imdb={}".format(sysaddon, systitle, year or "", imdb, )


                cm = []  # prepare context menu

                if not isFolder:
                    cm.append(("EDYTUJ dane do wyszukiwarki", "RunPlugin(%s?action=alterSources&url=%s)" % (sysaddon, sysurl+"%26customTitles%3D1"),))
                    # cm.append(("EDYTUJ dane do wyszukiwarki", "RunPlugin(%s)" % (url + "&customTitles=1"),))
                else:
                    if not generate_short_path:
                        cm.append(("EDYTUJ dane do wyszukiwarki", "Container.Update(%s?action=alterSources&url=%s)" % (sysaddon, sysurl+"%26customTitles%3D1"),))
                    else:
                        cm.append(("EDYTUJ dane do wyszukiwarki", "Container.Update(%s)" % (url + "&customTitles=1"),))

                if not isFolder:
                    if kodiver.major < 21 or kodiver.major >= 21 and kodiver.minor < 2:
                        cm.append((queueMenu, "RunPlugin(%s?action=queueItem)" % sysaddon))

                if not generate_short_path:
                    #cm.append(("Znajdź podobne", "ActivateWindow(10025,%s?action=similar&tmdb=%s)" % (sysaddon, tmdb),))
                    cm.append(("Znajdź podobne", "Container.Update(%s?action=similar&tmdb=%s)" % (sysaddon, tmdb),))
                else:
                    cm.append(("Znajdź podobne", "Container.Update(%s?action=similar)" % (sysaddon,),))

                # if traktCredentials:
                if isFolder or (traktIndicators or not indicator_kodi):
                    try:
                        overlay = int(playcount.getMovieOverlay(indicators, imdb))
                        # fflog(f'{overlay=}  {imdb=}  {title=}  {label=} ')
                        if overlay == 7:
                            cm.append((unwatchedMenu, "RunPlugin(%s?action=moviePlaycount&imdb=%s&query=6)" % (sysaddon, imdb),))
                            meta.update({"playcount": 1, "overlay": 7})  # to zmienia ptaszki
                            pass
                        else:
                            cm.append((watchedMenu,   "RunPlugin(%s?action=moviePlaycount&imdb=%s&query=7)" % (sysaddon, imdb),))
                            meta.update({"playcount": 0, "overlay": 6})  # to zmienia ptaszki
                            pass
                    except Exception:
                        fflog_exc(1)
                        pass


                if traktCredentials:
                    cm.append((traktManagerMenu, "RunPlugin(%s?action=traktManager&name=%s&imdb=%s&content=movie)" % (sysaddon, sysname, imdb),))

                # autoodtwarzanie, albo zatrzymanie autoodtwarzania
                #cm.append((playbackMenu, "RunPlugin(%s?action=alterSources&url=%s&meta=%s)" % (sysaddon, sysurl, sysmeta),))  # w url jest już meta
                cm.append((playbackMenu, "RunPlugin(%s?action=alterSources&url=%s)" % (sysaddon, sysurl),))

                cm.append((addToLibrary,
                           "RunPlugin(%s?action=movieToLibrary&name=%s&title=%s&localtitle=%s&year=%s&imdb=%s&tmdb=%s)" % (
                               sysaddon, sysname, systitle, syslocaltitle, year or "", imdb, tmdb),))

                cm.append((addMultiToLibrary, f"RunPlugin({sysaddon}?action=moviesMultiToLibrary&select=multi_select)",))

                if isOld:
                    cm.append((control.lang2(19033), "Action(Info)"))  # "Informacje" ? Może w starszym Kodi nie dodawał automatycznie

                if fullpath:
                    cm.append(("[I]przygotuj do ulubionych[/I]", "Container.Update(%s?action=prepareItemForAddToLibrary)" % (sysaddon),))

                if downloads and not isFolder:
                    cm.append((downloadMenu, "RunPlugin(%s)" % (url + "&download=1"),))
                    #cm.append((downloadMenu, "RunPlugin(%s?action=download&name=%s&image=%s&source=%s&extrainfo=%s)" % (sysaddon, sysname, sysimage, syssource, quote_plus(extrainfo)  ), ))

                item = control.item(label=label, offscreen=True)  # create ListItem


                item.addContextMenuItems(cm)


                art = {}

                art.update({
                            "icon": icon,
                            "thumb": thumb,
                            "poster": poster,
                           })

                art["fanart"] = i["fanart"] if settingFanart == 'true' and has("fanart") else addonFanart

                art["landscape"] = i["landscape"] if has("landscape") else art["fanart"]

                art["banner"] = i["banner"] if has("banner") else addonBanner

                # for key in ("clearlogo", "clearart", "keyart", "discart", "banner", "landscape", "fanart"):
                for key in ("clearlogo", "clearart", "keyart", "discart"):
                    if has(key):
                        art[key] = i[key]

                # fflog(f'{art=}')
                item.setArt(art)


                vtag = item.getVideoInfoTag()

                # vtag.addVideoStream(VideoStreamDetail(codec="h264"))  # czemu tak? czy to coś przyspiesza, ułatwia?

                castwiththumb = i.get("castwiththumb")
                if castwiththumb:
                    castwiththumb = [Actor(**a) for a in castwiththumb]
                    vtag.setCast(castwiththumb)

                # ustawienie m.in. tytułu na podstawie meta
                item.setInfo(type="Video", infoLabels=control.metadataClean(meta))  # ten sposób będzie porzucony w którymś nowszym Kodi

                item.setProperty("meta", json.dumps(meta))

                # korekta pod standard ListItem (bo super_info.py inaczej generuje)
                # vtag.setOriginalTitle(meta.get("originalname"))  # nie wiem czy dopiero od Kodi 20
                item.setInfo(type="Video", infoLabels={'OriginalTitle': meta.get("originalname") or meta.get("originaltitle", "")})
                item.setProperty("EnglishTitle", meta.get("englishtitle") or meta.get("originaltitle", ""))

                item.setInfo(type="Video", infoLabels={'count': counter})  # do sortowania potrzebne

                # item.setInfo(type="Video", infoLabels={"sorttitle": meta.get("title")})  # do przetestowania, bo nie wiem, jak to wykorzystać

                try:  # bo nie wiem czy dostępne dopiero od Kodi 20 (choć ListItem.UniqueID() dostępne już od Kodi 19, więc może przez infoLabels trzeba ustawiać)
                    #vtag.setUniqueID(imdb, "imdb")
                    #vtag.setUniqueID(tmdb, "tmdb")
                    vtag.setUniqueIDs({'imdb': imdb, 'tmdb': tmdb})  # kilka na raz
                except:
                    #item.setInfo(type="Video", infoLabels={'UniqueID("imdb")': imdb, 'UniqueID("tmdb")': tmdb})  # wstawia tylko dla imdb
                    #item.setProperty("imdb_id", imdb)
                    #item.setProperty("tmdb_id", tmdb)
                    item.setProperties({'imdb_id': imdb, 'tmdb_id': tmdb})  # kilka na raz
                    pass

                if fullpath:
                    item.setProperty("fullpath", fullpath)

                if not isFolder and not dont_use_setResolvedUrl:
                    isPlayable = "true"  # umożliwi używanie setResolvedUrl nawet dla okienka (ale chyba w przypadku rezygnacji z odtwarzania pojawi się błąd Kodi "nieudane odtwarzanie")
                else:
                    isPlayable = "false"  # aby nie było komunikatów o nieudanym odtwarzaniu
                if isPlayable == "true":  # kiedyś nie warto było ustawiać "false"
                    item.setProperty("IsPlayable", isPlayable)
                #fflog(f'{isPlayable=}')

                control.addItem(handle=syshandle, url=url, listitem=item, isFolder=isFolder)

                counter += 1

            except Exception as exc:
                fflog_exc(1)
                import traceback
                # print(f'EXCEPTION: {exc!r}\n{traceback.format_exc()}', file=sys.stderr)  # stderr is logged as ERROR
                print(f'EXCEPTION: {exc!r}\n{traceback.format_exc()}')  # default (stdout) is logged as DEBUG
                pass

            multi_select.append({"title": i["originaltitle"], "title_multi": i["title"], "year": i["year"], "imdb": i["imdb"], "tmdb": i["tmdb"], })

        # następna strona
        try:
            url = items[0]["next"]
            if url:
                url = re.sub("(?<=api_key=)[^&]*", "", url)
                url = re.sub("(?<=session_id=)[^&]*", "", url)

                icon = control.addonNext()

                addonLandscape = control.addonLandscape()

                item = control.item(label=nextMenu)  # create ListItem

                item.setArt({
                            "icon": icon, 
                            "thumb": icon, 
                            "poster": icon,
                            "banner": icon,
                            "fanart": addonFanart, 
                            "landscape": addonLandscape,
                            })

                if generate_short_path:
                    page = dict(urllib.parse_qsl(url)).get("page", "")
                    # item.setProperty("url", url.replace(f"&page={page}", ""))
                    # item.setProperty("url", re.sub(f"(?<=[?&/])page[=/]{page}", "", url).replace("&&", "&").replace("?&", "?").rstrip("?&"))  # uniwersalniejsze
                    item.setProperty("url", re.sub(f"((?<=[?/])|&)page[=/]{page}", "", url).replace("?&", "?").rstrip("?&"))  # uniwersalniejsze
                    url = "{}?action=moviePage&page={}".format(sysaddon, page)
                else:
                    url = "{}?action=moviePage&url={}".format(sysaddon, urllib.quote_plus(url))

                # item.setInfo(type="Video", infoLabels={'count': counter})  # do sortowania potrzebne - tylko, że to nie jest element wideo, a inaczej nie można wstawić countera - głupie to

                control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)
        except Exception as exc:
            fflog_exc(1)
            import traceback
            # print(f'EXCEPTION: {exc!r}\n{traceback.format_exc()}', file=sys.stderr)  # stderr is logged as ERROR
            print(f'EXCEPTION: {exc!r}\n{traceback.format_exc()}')  # default (stdout) is logged as DEBUG
            pass

        control.content(syshandle, "movies")  # to chyba ważne dla Kodi i skórek

        updateListing = False
        """
        params = dict(urllib.parse_qsl(sys.argv[2].replace("?", "")))
        updateListing = False if params.get("name") or params.get("item") else True  # True może świadczyć, że po drodze było odświeżanie
        """
        updateListing = True if params.get("r") else False  # True świadczy, że po drodze było odświeżanie

        control.directory(syshandle, cacheToDisc=True, updateListing=updateListing)

        views.setView("movies")  # dodatkowa funkcja FanFilm

        if meta:  # dziwny warunek, zależny od ostatniego elementu z listy filmów
            cache.cache_insert("multi_select", repr(multi_select))


    ### FOLDER ###
    def addDirectory(self, items, queue=False, cacheToDisc=True, add_refresh=False):

        if items is None or len(items) == 0:
            sys.exit()

        sysaddon = sys.argv[0]
        syshandle = int(sys.argv[1])
        addonFanart, addonThumb, artPath = (control.addonFanart(), control.addonThumb(), control.artPath(),)
        queueMenu = control.lang(32065)
        playRandom = control.lang(32535)
        addToLibrary = control.lang(32551)
        generate_short_path = control.setting("generate_short_path") == "true"

        for i in items:
            try:
                label = i["name"]  # wyświetlana nazwa pozycji


                plot = i.get("plot") or "[CR]"


                if i["image"].startswith("http"):
                    thumb = i["image"]
                elif artPath is not None:
                    thumb = os.path.join(artPath, i["image"])
                else:
                    thumb = addonThumb


                i["url"] = re.sub("(?<=api_key=)[^&]*", "", i["url"])
                i["url"] = re.sub("(?<=session_id=)[^&]*", "", i["url"])


                # bulding context menu
                cm = [(playRandom, "RunPlugin(%s?action=random&rtype=movie&url=%s)" % (sysaddon, urllib.quote_plus(i["url"])),)]

                if queue:
                    cm.append((queueMenu, "RunPlugin(%s?action=queueItem)" % sysaddon))

                try:
                    cm.append((addToLibrary, "RunPlugin(%s?action=moviesToLibrary&url=%s)" % (sysaddon, urllib.quote_plus(i["context"])),))
                except Exception:
                    # fflog_exc(1)
                    pass


                item = control.item(label=label, offscreen=True)  # create ListItem


                item.setArt({
                            "icon": thumb, 
                            "thumb": thumb, 
                            "poster": thumb, 
                            "fanart": addonFanart, 
                            })


                vtag = item.getVideoInfoTag()

                vtag.setPlot(plot)


                url = "{}?action={}".format(sysaddon, i["action"])  # akcja, czyli co ma się wykonać po naciśnięciu ENTER na danej pozycji
                action = dict(urllib.parse_qsl("action="+i["action"]))
                #fflog(f'{i["action"]=}  {action=}')
                try:
                    #if not generate_short_path or i["action"] not in ["movies", "moviePage"]:  # zabezpieczenie, jakbym nie wszystko sprawdził
                    if not generate_short_path or action["action"] not in ["movies", "moviePage"] or not "item" in action:  # zabezpieczenie, jakbym nie wszystko sprawdził
                        url += "&url=%s" % urllib.quote_plus(i["url"])
                        url = re.sub(r"\bitem=[^&]*", "", url)
                    else:
                        item.setProperty("url", i["url"])
                except Exception:
                    #fflog_exc(1)
                    pass


                if add_refresh:
                    cm.append(("Odśwież teraz", "Container.Update(%s&refresh=1)" % url))


                item.addContextMenuItems(cm)


                control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)

            except Exception as exc:
                fflog_exc(1)
                import traceback
                # print(f'EXCEPTION: {exc!r}\n{traceback.format_exc()}', file=sys.stderr)  # stderr is logged as ERROR
                print(f'EXCEPTION: {exc!r}\n{traceback.format_exc()}')  # default (stdout) is logged as DEBUG
                pass

        control.content(syshandle, "addons")
        control.directory(syshandle, cacheToDisc=cacheToDisc)
        views.setView("addons")  # dodatkowa funkcja FanFilm
