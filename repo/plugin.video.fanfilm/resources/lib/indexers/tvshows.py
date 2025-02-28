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

import datetime
import json
import os
import re
import sys
import urllib
from urllib.parse import quote_plus, urlparse, parse_qsl, urlencode, urlsplit, quote
try:
    import urllib.parse as urllib
except:
    pass
import requests

from resources.lib.indexers import navigator
from ptw.libraries import cache
from ptw.libraries import cleangenre
from ptw.libraries import cleantitle
from ptw.libraries import client
from ptw.libraries import control
from ptw.libraries import playcount
from ptw.libraries import trakt
from ptw.libraries import utils
from ptw.libraries import views
from ptw.libraries import apis
from ptw.libraries import log_utils
from ptw.libraries.log_utils import log, fflog, _is_debugging
from ptw.debug import log_exception, fflog_exc

from ptw.libraries.utils import convert
from xbmcplugin import addSortMethod, SORT_METHOD_UNSORTED, SORT_METHOD_LABEL, SORT_METHOD_TITLE, SORT_METHOD_VIDEO_YEAR, SORT_METHOD_VIDEO_RATING


import six

params = (
    dict(parse_qsl(sys.argv[2].replace("?", "")))
    if len(sys.argv) > 1
    else dict()
)

action = params.get("action")


class tvshows:
    def __init__(self):
        # fflog("inicjalizacja klasy tvshows")

        # fix for not always current value
        global params, action
        params = dict(urllib.parse_qsl(sys.argv[2].replace("?", ""))) if len(sys.argv) > 1 else dict()
        action = params.get("action")

        ### BASE ###
        self.list = []
        self.idx = True
        self.session = requests.Session()
        self.tvdb_jwt_token = None
        self.imdb_link   = "http://www.imdb.com"
        self.trakt_link  = "https://api.trakt.tv"
        self.tvmaze_link = "http://www.tvmaze.com"
        self.logo_link   = "https://i.imgur.com/"
        self.tmdb_link   = 'https://api.themoviedb.org'


        ### SETTINGS ###

        self.tvshowssort = control.setting("tvshows.sort")
        if self.tvshowssort == "0":
            self.tvshowssort = "popularity.desc"
        elif self.tvshowssort == "1":
            self.tvshowssort = "first_air_date.desc"

        self.tmdbvote = control.setting("tmdbtv.vote")

        self.fanart_tv_user = control.setting("fanart.tv.user") or apis.fanarttv_client_key
        self.fanart_tv_API_key = control.setting("fanart.tv.dev") or apis.fanarttv_API_key
        self.fanart_tv_headers = {"api-key": self.fanart_tv_API_key, "client-key": self.fanart_tv_user}
        self.user = control.setting("fanart.tv.user") + str("")

        self.trakt_user = control.setting("trakt.user").strip()

        self.imdb_user = control.setting("imdb.user").replace("ur", "")

        self.tm_user = control.setting("tm.user") or apis.tmdb_API
        self.tmdbuser = control.setting("tmdb.username") or "me"
        self.tmdb_sessionid = control.setting("tmdb.sessionid") or ""

        self.lang = control.apiLanguage()["tmdb"]  # iso 639-1 | daje 'pl' (ciekawe, czy wielkość liter ma znaczenie, bo wg Wiki to "PL"
        self.language = f"{self.lang}-{self.lang.upper()}"  # ISO_3166_1 | wg doc api z tmdb to "language-COUNTRY", czyli np. "pl-PL" (z wyjątkiem obrazków?)
        self.region = self.lang.upper()  # filter to search for and display matching release date information. This parameter is expected to be an ISO 3166-1 code


        ### DATY ###
        self.datetime = datetime.datetime.utcnow() - datetime.timedelta(hours=5)
        self.today_date = self.datetime.strftime("%Y-%m-%d")
        #self.today_date = ""  # bo domyślnie tmdb i tak bierze dzisiejszą, a ścieżki będą uniwersalniejsze


        ### LINKI API DO TMDB ###
        self.metasearch = (self.tm_user, self.lang, self.today_date,)  # TODO dodatkowe ustawienia

        self.tmdb_api_link = 'https://api.themoviedb.org/3/tv/%s?api_key=%s&language=%s&append_to_response=credits,external_ids' % ('%s', self.tm_user, self.lang)

        self.tmdb_tv_search = (
            "https://api.themoviedb.org/3/search/tv?api_key=%s&language=%s&sort_by=popularity.desc&query=%%s&page=1" % (
                self.tm_user, self.lang))

        self.tmbd_airing_link = ("https://api.themoviedb.org/3/tv/airing_today?api_key=%s&language=%s&sort_by=popularity.desc&vote_count.gte=%s&include_adult=false&include_video=false&page=1" % (
                self.tm_user, self.language, self.tmdbvote))
        self.tmbd_airing_link =  "https://api.themoviedb.org/3/tv/airing_today?api_key=%s&language=%s&page=1" % (self.tm_user, self.language)

        self.tmdb_premiere_link = (
            "https://api.themoviedb.org/3/discover/tv?api_key=%s&language=%s&sort_by=primary_release_date.desc&first_air_date.lte=%s&vote_count.gte=%s&include_adult=false&include_video=false&page=1" % (
                self.tm_user, self.lang, self.today_date, self.tmdbvote))
        self.tmdb_premiere_link = "https://api.themoviedb.org/3/tv/on_the_air?api_key=%s&language=%s&page=1" % (self.tm_user, self.language)

        self.tmdb_discover = (
            "https://api.themoviedb.org/3/discover/tv?api_key=%s&language=%s&sort_by=%s&first_air_date.lte=%s&vote_count.gte=%s&include_adult=false&include_video=false&%%s&page=1" % (
                self.tm_user, self.lang, self.tvshowssort, self.today_date, self.tmdbvote))

        self.tmdb_language = (
            "https://api.themoviedb.org/3/discover/tv?api_key=%s&language=%s&sort_by=%s&first_air_date.lte=%s&include_adult=false&include_video=false&%%s&page=1" % (
                self.tm_user, self.lang, self.tvshowssort, self.today_date))

        self.tmdb_discover_year = (
            "https://api.themoviedb.org/3/discover/tv?api_key=%s&language=%s&sort_by=primary_release_date.asc&include_adult=false&include_video=false&first_air_date.gte=%%s-01-01&first_air_date.lte=%%s-12-31&vote_count.gte=100&page=1" % (
                self.tm_user, self.lang))

        self.tmdb_discover_years = (
            "https://api.themoviedb.org/3/discover/tv?api_key=%s&language=%s&sort_by=popularity.desc&include_adult=false&include_video=false&first_air_date.gte=%%s-01-01&first_air_date.lte=%%s-12-31&vote_count.gte=100&page=1" % (
                self.tm_user, self.lang))

        self.tmdb_by_imdb = 'https://api.themoviedb.org/3/find/%s?api_key=%s&external_source=imdb_id' % ('%s', self.tm_user)

        self.tmdb_personid_link = (
            "https://api.themoviedb.org/3/search/person?api_key=%s&language=%s&query=%%s&include_adult=false&page=1" % (
                self.tm_user, self.lang))

        self.tmdb_person_link = (
            "https://api.themoviedb.org/3/person/%%s/tv_credits?api_key=%s&language=%s&include_adult=false&page=1" % (
                self.tm_user, self.lang))

        self.tmdb_networks_link = self.tmdb_link + '/3/discover/tv?api_key=%s&with_networks=%s&language=pl-PL&page=1' % (self.tm_user, '%s')

        #self.tmdb_popular_link = ("https://api.themoviedb.org/3/tv/popular?api_key=%s&language=%s&primary_release_date.lte=%s&include_adult=false&vote_count.gte=200&include_video=false&page=1" % self.metasearch)
        self.tmdb_popular_link =  "https://api.themoviedb.org/3/tv/popular?api_key=%s&language=%s&page=1" % (self.tm_user, self.language)

        self.tmdb_top_rated_link = "https://api.themoviedb.org/3/tv/top_rated?api_key=%s&language=%s&page=1" % (self.tm_user, self.language)


        ### TMDB USER ###
        self.tmdb_user_lists = (
            "https://api.themoviedb.org/3/account/%s/lists?api_key=%s&language=%s&session_id=%s&page=1" % (
                self.tmdbuser, self.tm_user, self.lang, self.tmdb_sessionid))

        self.tmdb_lists_link = (
            "https://api.themoviedb.org/3/list/%%s?api_key=%s&language=%s&include_adult=false&page=1" % (
                self.tm_user, self.lang))

        self.tmdbuserwatchlist_link = (
            "https://api.themoviedb.org/3/account/%s/watchlist/tv?api_key=%s&language=%s&session_id=%s&sort_by=created_at.desc&page=1" % (
                self.tmdbuser, self.tm_user, self.lang, self.tmdb_sessionid))

        self.tmdbuserfavourite_link = (
            "https://api.themoviedb.org/3/account/%s/favorite/tv?api_key=%s&language=%s&session_id=%s&sort_by=created_at.desc&page=1" % (
                self.tmdbuser, self.tm_user, self.lang, self.tmdb_sessionid))

        self.tmdb_arts   = 'https://api.themoviedb.org/3/tv/%s/images?api_key=%s&include_image_language=pl,en' % ('%s', self.tm_user)
        self.tm_img_link = 'https://image.tmdb.org/t/p/w%s%s'


        ### LINKI API TRAKT ###
        self.search_link          = "https://api.trakt.tv/search/show?limit=20&page=1&query="
        self.trending_link        = "http://api.trakt.tv/shows/trending?limit=40&page=1"
        self.traktlists_link      = "https://api.trakt.tv/users/me/lists"
        self.traktlikedlists_link = "https://api.trakt.tv/users/likes/lists?limit=1000000"
        self.traktlist_link       = "https://api.trakt.tv/users/%s/lists/%s/items"
        self.traktcollection_link = "https://api.trakt.tv/users/me/collection/shows"
        self.traktwatchlist_link  = "https://api.trakt.tv/users/me/watchlist/shows"
        self.traktfeatured_link   = "https://api.trakt.tv/recommendations/shows?limit=40"


        ### LINKI API INNE ###
        self.fanart_tv_art_link   = "http://webservice.fanart.tv/v3/tv/%s"
        self.fanart_tv_level_link = "http://webservice.fanart.tv/v3/level"


        ### LINKI IMDB ###
        # self.persons_link        = "https://www.imdb.com/search/name?count=100&name="  # nieużywane
        # self.personlist_link     = "https://www.imdb.com/search/name?count=100&gender=male,female"  # nieużywane

        # self.imdbUserLists_link = "https://www.imdb.com/list/%s/?view=detail&sort=alpha,asc&title_type=tvSeries,miniSeries&count=100&start=1"  # nigdzie nie używane w kodzie
        self.imdblist1_link      = "https://www.imdb.com/list/%s/?view=detail&sort=alpha,asc&title_type=tvSeries,miniSeries&start=1"
        self.imdblist2_link      = "https://www.imdb.com/list/%s/?view=detail&sort=date_added,desc&title_type=tvSeries,miniSeries&start=1"

        self.imdblists_link      = "https://www.imdb.com/user/ur%s/lists?tab=all&sort=mdfd&order=desc&filter=titles" % self.imdb_user

        self.imdbwatchlist_link  = "https://www.imdb.com/user/ur%s/watchlist" % self.imdb_user
        self.imdbwatchlist1_link = "https://www.imdb.com/user/ur%s/watchlist?sort=alpha,asc" % self.imdb_user
        self.imdbwatchlist2_link = "https://www.imdb.com/user/ur%s/watchlist?sort=date_added,desc" % self.imdb_user



    ### KATALOGI SERIALI ###

    ## Języki ##
    def languages(self):
        languages = [
            ("Polski", "pl"),
            ("Afrykanerski", "af"), ("Albański", "sq"), ("Angielski", "en"), ("Arabski", "ar"),
            ("Bośniacki", "bs"), ("Bułgarski", "bg"), ("Chiński", "zh"), ("Chorwacki", "hr"),
            ("Czeski", "cs"), ("Duński", "da"), ("Estoński", "et"), ("Fiński", "fi"), ("Francuski", "fr"),
            ("Grecki", "el"), ("Gruziński", "ka"), ("Hebrajski", "he"), ("Hindi ", "hi"), ("Hiszpański", "es"),
            ("Holenderski", "nl"), ("Irlandzki", "ga"), ("Islandzki", "is"), ("Japoński", "ja"), ("Koreański", "ko"),
            ("Litewski", "lt"), ("Łotewski", "lv"), ("Macedoński", "mk"), ("Niemiecki", "de"), ("Norweski", "no"),
            ("Pendżabski", "pa"), ("Perski", "fa"), ("Portugalski", "pt"), ("Rosyjski", "ru"), ("Rumuński", "ro"),
            ("Serbski", "sr"), ("Serbsko-chorwacki", "sh"), ("Słowacki", "sk"), ("Słoweński", "sl"),
            ("Szwedzki", "sv"), ("Turecki", "tr"), ("Ukraiński", "uk"), ("Węgierski", "hu"), ("Włoski", "it"),
        ]
        for i in languages:
            self.list.append({
                "name": i[0],
                "url": self.tmdb_language % ("with_original_language=" + i[1]),
                "image": "languages.png",
                "action": "tvshows" + f"&item={str(i[1])}",
            })
        self.addDirectory(self.list)
        return self.list


    ## Certyfikaty ##
    def certifications(self, country):
        if not country:
            navigator.navigator().addDirectoryItem("amerykańskie", "tvCertificates&certification_country=US", "certificates.png", "DefaultMovies.png")
            navigator.navigator().addDirectoryItem("polskie", "tvCertificates&certification_country=PL", "certificates.png", "DefaultMovies.png")
            navigator.navigator().endDirectory()
        else:
            if country == "US":
                #certificates = ["G", "PG", "PG-13", "R", "NC-17"]  # to dla filmów
                #certificates = ["TV-G", "TV-PG", "TV-14", "TV-MA"]
                certificates = ["TV-Y", "TV-Y7", "TV-G", "TV-PG", "TV-14", "TV-MA", "NR"]
            elif country == "PL":
                certificates = ["0", "7", "12", "16", "18"]  # w Polsce - sprawdzić, czy ma sens, czy pozostać przy US
            else:
                navigator.navigator().addDirectoryItem("nieznana zmienna kraju: "+country, "", "certificates.png", "DefaultMovies.png")
                country = ""

            if country:
                for i in certificates:
                    self.list.append({
                                     "name": str(i),
                                     "url": self.tmdb_discover % (f"certification_country={country}&certification=" + str(i)),
                                     #"url": self.tmdb_discover % (f"certification_country=PL&certification=" + str(i)),
                                     "image": "certificates.png",
                                     "action": "tvshows" + f"&item={str(i)}",
                                    })
            self.addDirectory(self.list)

        return self.list


    ## Lata ##
    def years(self):
        navigator.navigator().addDirectoryItem(32630, "tvYearsTop", "years.png", "DefaultMovies.png")

        year = self.datetime.strftime("%Y")
        for i in range(int(year) - 0, 1935, -1):
            self.list.append({
                              "name": str(i),
                              "url": self.tmdb_discover_year % (str(i), str(i)),
                              "image": "years.png",
                              "action": "tvshows" + f"&item={str(i)}",
                            })

        self.addDirectory(self.list)
        return self.list


    ## Lata TOP (zakres lat) ##
    def years_top(self):
        year = self.datetime.strftime("%Y")
        dec = int(year[:3]) * 10
        for i in range(dec, 1920, -10):  # od 1930
            self.list.append({
                              "name": str(i) + "-" + str(i + 9),
                              #"url": self.tmdb_discover_years % (str(i), str(i + 9)),
                              "url": self.tmdb_discover_years % (str(i)+"-01-01", str(i + 9)+"-12-31"),
                              "image": "years.png",
                              "action": "tvshows" + f'&item={str(i) + "-" + str(i + 9)}',
                            })
        self.addDirectory(self.list)
        return self.list


    def networks(self):
        networks = [
            ("54", "Disney Channel", "https://i.imgur.com/ZCgEkp6.png"),
            ("44", "Disney XD", "https://i.imgur.com/PAJJoqQ.png"),
            ("2", "ABC", "https://i.imgur.com/qePLxos.png"),
            ("493", "BBC America", "https://i.imgur.com/TUHDjfl.png"),
            ("6", "NBC", "https://i.imgur.com/yPRirQZ.png"),
            ("13", "Nickelodeon", "https://i.imgur.com/OUVoqYc.png"),
            ("14", "PBS", "https://i.imgur.com/r9qeDJY.png"),
            ("16", "CBS", "https://i.imgur.com/8OT8igR.png"),
            ("19", "FOX", "https://i.imgur.com/6vc0Iov.png"),
            ("21", "The WB", "https://i.imgur.com/rzfVME6.png"),
            ("24", "BET", "https://i.imgur.com/ZpGJ5UQ.png"),
            ("30", "USA Network", "https://i.imgur.com/Doccw9E.png"),
            ("32", "CBC", "https://i.imgur.com/unQ7WCZ.png"),
            ("33", "MTV", "https://i.imgur.com/QM6DpNW.png"),
            ("34", "Lifetime", "https://i.imgur.com/tvYbhen.png"),
            ("35", "Nick Junior", "https://i.imgur.com/leuCWYt.png"),
            ("41", "TNT", "https://i.imgur.com/WnzpAGj.png"),
            ("43", "National Geographic", "https://i.imgur.com/XCGNKVQ.png"),
            ("47", "Comedy Central", "https://i.imgur.com/ko6XN77.png"),
            ("49", "HBO", "https://i.imgur.com/Hyu8ZGq.png"),
            ("55", "Spike", "https://i.imgur.com/BhXYytR.png"),
            ("67", "Showtime", "https://i.imgur.com/SawAYkO.png"),
            ("56", "Cartoon Network", "https://i.imgur.com/zmOLbbI.png"),
            ("65", "History Channel", "https://i.imgur.com/LEMgy6n.png"),
            ("84", "TLC", "https://i.imgur.com/c24MxaB.png"),
            ("68", "TBS", "https://i.imgur.com/RVCtt4Z.png"),
            ("71", "The CW", "https://i.imgur.com/Q8tooeM.png"),
            ("74", "Bravo", "https://i.imgur.com/TmEO3Tn.png"),
            ("76", "E!", "https://i.imgur.com/3Delf9f.png"),
            ("77", "Syfy", "https://i.imgur.com/9yCq37i.png"),
            ("80", "Adult Swim", "https://i.imgur.com/jCqbRcS.png"),
            ("91", "Animal Planet", "https://i.imgur.com/olKc4RP.png"),
            ("110", "CTV", "https://i.imgur.com/qUlyVHz.png"),
            ("129", "A&E", "https://i.imgur.com/xLDfHjH.png"),
            ("158", "VH1", "https://i.imgur.com/IUtHYzA.png"),
            ("174", "AMC", "https://i.imgur.com/ndorJxi.png"),
            ("928", "Crackle", "https://i.imgur.com/53kqZSY.png"),
            ("202", "WGN America", "https://i.imgur.com/TL6MzgO.png"),
            ("209", "Travel Channel", "https://i.imgur.com/mWXv7SF.png"),
            ("213", "Netflix", "https://i.imgur.com/jI5c3bw.png"),
            ("251", "Audience", "https://i.imgur.com/5Q3mo5A.png"),
            ("270", "SundanceTV", "https://i.imgur.com/qldG5p2.png"),
            ("318", "Starz", "https://i.imgur.com/Z0ep2Ru.png"),
            ("359", "Cinemax", "https://i.imgur.com/zWypFNI.png"),
            ("364", "truTV", "https://i.imgur.com/HnB3zfc.png"),
            ("384", "Hallmark Channel", "https://i.imgur.com/zXS64I8.png"),
            ("397", "TV Land", "https://i.imgur.com/1nIeDA5.png"),
            ("1024", "Amazon", "https://i.imgur.com/ru9DDlL.png"),
            ("1267", "Freeform", "https://i.imgur.com/f9AqoHE.png"),
            ("4", "BBC One", "https://i.imgur.com/u8x26te.png"),
            ("332", "BBC Two", "https://i.imgur.com/SKeGH1a.png"),
            ("3", "BBC Three", "https://i.imgur.com/SDLeLcn.png"),
            ("100", "BBC Four", "https://i.imgur.com/PNDalgw.png"),
            ("214", "Sky One", "https://i.imgur.com/xbgzhPU.png"),
            ("9", "ITV", "https://i.imgur.com/5Hxp5eA.png"),
            ("26", "Channel 4", "https://i.imgur.com/6ZA9UHR.png"),
            ("99", "Channel 5", "https://i.imgur.com/5ubnvOh.png"),
            ("136", "E4", "https://i.imgur.com/frpunK8.png"),
            ("210", "HGTV", "https://i.imgur.com/INnmgLT.png"),
            ("453", "Hulu", "https://i.imgur.com/uSD2Cdw.png"),
            ("1436", "YouTube Red", "https://i.imgur.com/ZfewP1Y.png"),
            ("64", "Discovery Channel", "https://i.imgur.com/8UrXnAB.png"),
            ("2739", "Disney+", "https://i.imgur.com/DVrPgbM.png"),
            ("2552", "Apple TV +", "https://i.imgur.com/fAQMVNp.png"),
            ("2697", "Acorn TV", "https://i.imgur.com/fSWB5gB.png"),
            ("1709", "CBS All Access", "https://i.imgur.com/ZvaWMuU.png"),
            ("3186", "HBO Max", "https://i.imgur.com/mmRMG75.png"),
            ("2243", "DC Universe", "https://i.imgur.com/bhWIubn.png"),
            ("2076", "Paramount Network", "https://i.imgur.com/ez3U6NV.png"),
            ("4330", "Paramount+", "https://i.imgur.com/dmUjWmU.png"),
            ("3353", "Peacock", "https://imgur.com/1JXFkSM.png"),
            ("504", "TVN", "https://i.imgur.com/yA8TJ4o.png"),
            ("483", "TVP1", "https://i.imgur.com/as4ipbu.png"),
            ("466", "TVP2", "https://i.imgur.com/qj1Ta1Q.png"),
            ("315", "Polsat", "https://i.imgur.com/knnmJG5.png")
        ]
        for i in networks:
            self.list.append(
                {
                    "name": i[1],
                    "url": self.tmdb_networks_link % i[0],
                    "image": i[2],
                    "action": "tvshows" + f"&item={str(i[1])}",
                }
            )
        self.list = sorted(self.list, key=lambda k: utils.title_key(k["name"]))
        self.addDirectory(self.list)
        return self.list


    def genres(self):
        genres = [
                    ("10759", "Akcja i przygoda", "Action and Adventure.png"),
                    ("16", "Animacja", "Animation.png"),
                    ("10762", "Dla dzieci", "Kids.png"),
                    ("35", "Komedia", "Comedy.png"),
                    ("80", "Kryminał", "Crime.png"),
                    ("99", "Dokumentalny", "Documentary.png"),
                    ("18", "Dramat", "Drama.png"),
                    ("10751", "Familijny", "Family.png"),
                    ("9648", "Tajemnica", "Mystery.png"),
                    ("10764", "Reality TV", "Reality_show.png"),
                    ("10766", "Romans", "Romance.png"),
                    ("10765", "Sci-Fi i Fantazja", "Sci_fi_and_fantasy.png"),
                    ("10767", "Talk Shows", "Television.png"),
                    ("10768", "Wojna i polityka", "Historical.png"),
                    ("37", "Western", "Western.png"),
                ]
        for i in genres:
            self.list.append({
                                "name": i[1],
                                "url": self.tmdb_discover % ("with_genres=" + i[0]),
                                "image": i[2],
                                "action": "tvshows" + f"&item={str(i[1])}",
                            })
        self.addDirectory(self.list)
        return self.list


    def search(self):
        navigator.navigator().addDirectoryItem("[LIGHT][B]["+control.lang(32603)+"][/B][/LIGHT]", "tvSearchnew", "search.png", "DefaultTVShows.png")

        generate_short_path = control.setting("generate_short_path") == "true"

        from sqlite3 import dbapi2 as database
        dbcon = database.connect(control.searchFile)
        dbcur = dbcon.cursor()
        try:
            dbcur.executescript("CREATE TABLE IF NOT EXISTS tvshow (ID Integer PRIMARY KEY AUTOINCREMENT, term);")
        except:
            pass
        dbcur.execute("SELECT * FROM tvshow ORDER BY ID DESC")

        lst = []
        delete_option = False
        for (id, term) in dbcur.fetchall():
            if term not in str(lst):
                lst += [term]
                delete_option = True
                navigator.navigator().addDirectoryItem(
                    term,
                    # "tvSearchterm&name=%s" % term,
                    # "tvSearchterm",  # nie powraca focus na wywoływaną pozycję
                    # "tvSearchterm&item=%s" % len(lst),  # aby po powrocie focus ustawiał się na poprzedniej pozycji
                    "tvSearchterm&item=%s" % len(lst) if generate_short_path else "tvSearchterm&name=%s" % term,
                    "search.png",
                    "DefaultTVShows.png",
                    context=("Usuń z historii wyszukiwania", "removeFromSearchHistory&term=%s&content=tvshow" % urllib.quote_plus(term),),
                )
        dbcur.close()

        if delete_option:
            navigator.navigator().addDirectoryItem("[LIGHT][I]["+control.lang(32605)+"][/I][/LIGHT]", "clearCacheSearch&content=tvshow", "tools.png", "DefaultAddonProgram.png", isFolder=False)

        syshandle = int(sys.argv[1])
        addSortMethod(syshandle, sortMethod=SORT_METHOD_UNSORTED)
        addSortMethod(syshandle, sortMethod=SORT_METHOD_LABEL)

        navigator.navigator().endDirectory(cacheToDisc=False)


    ### WYSZUKIWANIE NOWE ###
    def search_new(self):
        """
        folderpath = control.infoLabel('Container.FolderPath')
        params1 = dict(urllib.parse_qsl(folderpath.split('?')[-1]))
        action1 = params1.get('action')  # może być też puste
        if action1 == "tvSearchterm":
            # taki hack na Kodi, bo inaczej wywala do głównego menu Kodi
            control.directory(int(sys.argv[1]), cacheToDisc=True)
            url = "{}?action={}".format(sys.argv[0], "tvSearch")
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

        dbcur.execute("SELECT * FROM tvshow WHERE term=?", (q,))
        if dbcur.fetchone():
            dbcur.execute("DELETE FROM tvshow WHERE term=?", (q,))
        dbcur.execute("INSERT INTO tvshow VALUES (?,?)", (None, q))

        dbcon.commit()
        dbcur.close()
        """
        if not control.condVisibility('Window.IsActive(busydialog)'):
            navigator.navigator().addDirectoryItem('... proszę czekać, trwa wyszukiwanie ...', "tvSearch", "search.png", "DefaultTVShows.png")
            control.directory(int(sys.argv[1]), cacheToDisc=False)
            url = "{}?action={}".format(sys.argv[0], "tvSearchterm&name=%s" % urllib.quote_plus(q))
            control.execute('Container.Update("%s")' % url)
            return
        """
        control.busy()
        tvshows.get(self, self.tmdb_tv_search % quote_plus(q))
        control.idle()


    def search_term(self, name):
        # log_utils.fflog(f"{name=}")
        if name and name != "..":
            tvshows.get(self, self.tmdb_tv_search % quote_plus(name))
        else:
            import xbmcgui
            xbmcgui.Dialog().notification('FanFilm', 'szukanie niemożliwe z powodu błędnego parametru', xbmcgui.NOTIFICATION_ERROR)
            navigator.navigator().endDirectory()
            log_utils.fflog(f'szukanie niemożliwe z powodu błędnego parametru {name=}')
            control.execute('Action(Back)')


    ## Osoby - wyszukiwanie##
    def persons(self, url):
        # fflog(f'{url=}',1,1)
        tmdb_results = requests.get(url, timeout=30).json()
        # page = tmdb_results.get("page", 0)
        # total = tmdb_results.get("total_pages", 0)
        # if page < total and "page=" in url:
        #     next = re.sub(r"page=\d+", f"page={page + 1}", url)
        # else:
        #     next = ""
        for item in tmdb_results["results"]:
            if item.get("known_for_department") == "Acting":
                if item.get("profile_path"):
                    photo = str("http://www.themoviedb.org/t/p/w300_and_h450_bestv2" + item.get("profile_path", ""))
                else:
                    photo = "people.png"
                self.list.append(
                    {"name": item.get("name"), "url": self.tmdb_person_link % str(item.get("id")), "image": photo,
                     "action": "tvshows", })

        self.list = sorted(self.list, key=lambda k: utils.title_key(k["name"]))
        self.addDirectory(self.list)
        return self.list

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
            # url = '%s?action=tvPersons&url=%s' % (sys.argv[0], urllib.quote_plus(url))
            tvshows.persons(self, self.tmdb_personid_link % urllib.quote_plus(q))

        except:
            return



    ### SCRAPERY API/STRON ###

    ### TMDB ###
    def tmdb_list(self, url):
        # fflog(f'{params=}', 1, 1)
        # fflog(f'{url=}', 1, 1)

        url = re.sub("(?<=api_key=)[^&]*", self.tm_user, url)
        url = re.sub("(?<=session_id=)[^&]*", self.tmdb_sessionid, url)
        # fflog(f'{url=}', 1, 1)
        tmdb_results = requests.get(url, timeout=30).json()

        page = tmdb_results.get("page", 0)
        total = tmdb_results.get("total_pages", 0)
        if page < total and "page=" in url:
            next_page = re.sub(r"page=\d+", f"page={page + 1}", url)
        else:
            next_page = ""
        # next_page = re.sub("(?<=api_key=)[^&]*", "", next_page)
        # next_page = re.sub("(?<=session_id=)[^&]*", "", next_page)
        # fflog(f'{next_page=}')
        # next = next_page

        if not self.idx:
            # fflog(f'{self.idx=}',1,1)
            if ("/watchlist/" in url or "/favorite/" in url):  # a favorite ?
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
            try:
                # fflog(f'item={json.dumps(item, indent=2)}')

                if 'media_type' in item and not item['media_type'] == 'tv':
                    #raise Exception()
                    continue

                tmdb = str(item.get('id'))

                try:
                    title = item['name']
                except:
                    title = ''
                title = six.ensure_str(title)

                try:
                    originaltitle = item['original_name']
                except:
                    originaltitle = ''
                originaltitle = six.ensure_str(originaltitle)
                if not originaltitle:
                    originaltitle = title

                try:
                    premiered = item['first_air_date']
                except:
                    premiered = ''
                if not premiered:
                    premiered = '0'

                try:
                    plot = item['overview']
                except:
                    plot = ''
                if not plot:
                    plot = ''

                try:
                    year = re.findall(r'(\d{4})', premiered)[0]
                except:
                    year = ''
                if not year:
                    year = '0'


                self.list.append({'title': title,
                                  'originaltitle': originaltitle,
                                  'premiered': premiered,
                                  'year': year,
                                  'imdb': '0',
                                  'tmdb': tmdb,
                                  'tvdb': '0',
                                  'plot': plot,
                                  'poster': '0',
                                  'next': next_page})
            except Exception:
                fflog_exc(1)
                pass
        # fflog(f'self.list={json.dumps(self.list, indent=2)}',1,1)
        return self.list


    ### TRAKT ###
    def trakt_list(self, url, user):
        try:
            dupes = []

            q = dict(parse_qsl(urlsplit(url).query))
            q.update({"extended": "full"})
            q = (urlencode(q)).replace("%2C", ",")
            u = url.replace("?" + urlparse(url).query, "") + "?" + q

            result = trakt.getTraktAsJson(u)
            result = convert(result)

            items = []
            for i in result:
                try:
                    items.append(i["show"])
                except:
                    pass
            if len(items) == 0:
                items = result
        except Exception:
            fflog_exc(1)
            return

        try:
            q = dict(parse_qsl(urlsplit(url).query))
            if not int(q["limit"]) == len(items):
                raise Exception()
            q.update({"page": str(int(q["page"]) + 1)})
            q = (urlencode(q)).replace("%2C", ",")
            next = url.replace("?" + urlparse(url).query, "") + "?" + q
            # next = next
        except:
            next = ""

        for item in items:
            try:
                title = item["title"]
                title = re.sub(r"\s(|[(])(UK|US|AU|\d{4})(|[)])$", "", title)
                title = client.replaceHTMLCodes(title)

                year = item["year"]
                year = re.sub("[^0-9]", "", str(year))

                if int(year) > int((self.datetime).strftime("%Y")):
                    #raise Exception()
                    continue

                imdb = item["ids"]["imdb"]
                if imdb is None or imdb == "":
                    imdb = "0"
                else:
                    imdb = "tt" + re.sub("[^0-9]", "", str(imdb))

                tvdb = item["ids"]["tvdb"]
                if tvdb is None or tvdb == "":
                    tvdb = "0"
                else:
                    tvdb = re.sub("[^0-9]", "", str(tvdb))
                    dupes.append(tvdb)

                tmdb = item["ids"]["tmdb"]
                if tmdb is None or tmdb == "":
                    tmdb = "0"
                else:
                    tmdb = re.sub("[^0-9]", "", str(tmdb))
                    dupes.append(tmdb)

                try:
                    premiered = item["first_aired"]
                except:
                    premiered = "0"
                try:
                    premiered = re.compile(r"(\d{4}-\d{2}-\d{2})").findall(premiered)[0]
                except:
                    premiered = "0"

                try:
                    studio = item["network"]
                except:
                    studio = "0"
                if studio is None:
                    studio = "0"

                try:
                    genre = item["genres"]
                except:
                    genre = "0"
                genre = [i.title() for i in genre]
                if genre == []:
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

                self.list.append(
                    {
                        "title": title,
                        "originaltitle": title,
                        "year": year,
                        "premiered": premiered,
                        "studio": studio,
                        "genre": genre,
                        "duration": duration,
                        "rating": rating,
                        "votes": votes,
                        "mpaa": mpaa,
                        "plot": plot,
                        "imdb": imdb,
                        "tvdb": tvdb,
                        "tmdb": tmdb,
                        "poster": "0",
                        "next": next,
                    }
                )
            except Exception:
                fflog_exc(1)
                pass

        return self.list


    ### IMDB ###
    def imdb_list(self, url):
        media_list = []

        # headers = {'Accept-Language': 'pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7'}
        headers = {"Accept-Language": self.lang}
        dupes = []

        for i in re.findall(r"date\[(\d+)\]", url):
            url = url.replace(
                "date[%s]" % i,
                (self.datetime - datetime.timedelta(days=int(i))).strftime("%Y-%m-%d"),
            )

        def imdb_watchlist_id(url):  # już chyba niepotrzebne
            return client.parseDOM(
                client.request(url, headers=headers),
                "meta",
                ret="content",
                attrs={"property": "pageId"},
            )[0]

        # coś się zmieniło na stronie IMDb - może to już niepotrzebne
        if url == self.imdbwatchlist_link:
            pass
        elif url == self.imdbwatchlist1_link:
            # url = cache.get(imdb_watchlist_id, 8640, url)
            # url = self.imdblist1_link % url
            pass
        elif url == self.imdbwatchlist2_link:
            # url = cache.get(imdb_watchlist_id, 8640, url)
            # url = self.imdblist2_link % url
            pass

        result = client.request(url, headers=headers)

        # result = result.replace("\n", " ")

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
                    title = client.parseDOM(item, "a")[1]
                    title = client.parseDOM(title, "h3", attrs={"class": "ipc-title__text"})[0]
                    title = client.replaceHTMLCodes(title)
                    title = re.sub(r"^\d+\. ", "", title)
                    originaltitle = title
                # fflog(f'{title=}',1,1)  # debug

                # potrzebne, bo na watchliscie są zmieszane pozycje
                if items is js_items:
                    if "/user/" in url or "/list/" in url:
                        # content_type = item['listItem']['titleType']['id']  # "tvSeries" lub "tvMiniSeries" i inne
                        content_type = item['listItem']['titleType']['text']  # "TV Series" lub "TV Mini Series" i inne
                    else:
                        # content_type = item['titleType']['id']
                        content_type = item['titleType']['text']
                else:
                    content_type = client.parseDOM(item, "span", attrs={"class": ".+? dli-title-type-data"})
                    content_type = content_type[0] if content_type else ""
                    # fflog(f'[imdb_list] {content_type=}')
                if not content_type or content_type.lower() == "movie":  # oczekiwane "TV Series" lub "TV Mini Series" dla seriali
                    # fflog(f'to nie jest serial {title=}  {content_type=}',1,1)
                    continue

                if items is js_items:
                    if "/user/" in url or "/list/" in url:
                        year = item['listItem']['releaseYear']['year']
                    else:
                        year = item['releaseYear']
                    year = str(year)
                else:
                    # year = client.parseDOM(item, "span", attrs={"class": "lister-item-year.+?"})
                    year = client.parseDOM(item, "span", attrs={"class": ".+? dli-title-metadata-item"})
                    # year += client.parseDOM(item, "span", attrs={"class": "year_type"})
                    # year = re.findall(r"(\d{4})", year[0])[0]
                    try:
                        if type(year) == list:
                            year = year[0]
                        year = re.compile(r"(\d{4})").findall(year)[0]
                    except:
                        year = "0"
                if int(year) > int((self.datetime).strftime("%Y")):  # to coś pomija, ale dlaczego?
                    fflog(f' {int(year)=}  >  {int(self.datetime.strftime("%Y"))=}  | {title=}')
                    #raise Exception()
                    # continue
                    pass

                if items is js_items:
                    if "/user/" in url or "/list/" in url:
                        premiered = item['listItem']['releaseDate']
                    else:
                        premiered = item['releaseDate']
                    premiered = f"{premiered['year']}-{premiered['month']:02d}-{premiered['day']:02d}"
                else:
                    premiered = "0"

                if items is js_items:
                    if "/user/" in url or "/list/" in url:
                        imdb = item['listItem']['id']
                    else:
                        imdb = item['titleId']
                else:
                    imdb = client.parseDOM(item, "a", ret="href")[0]
                    imdb = re.findall(r"(tt\d*)", imdb)[0]

                if imdb in dupes:  # może przydatne, jak pozycje zbierane są z kilku list
                    continue
                dupes.append(imdb)

                poster = rating = votes = plot = mpaa = genre = "0"

                # czy reszty nie można pociągnąć z super_info? ale może lepiej mieć niektóre dane z imdb
                if True:
                # if items is not js_items:  # potem dorobię i dla js_items
                    if items is js_items:
                        if "/user/" in url or "/list/" in url:
                            poster = item['listItem']['primaryImage']['url']
                        else:
                            poster = item['primaryImage']['url']
                    else:
                        try:
                            poster = client.parseDOM(item, "img", ret="loadlate")[0]
                        except:
                            poster = "0"
                        if "/nopicture/" in poster or '/sash/':
                            poster = "0"
                        poster = re.sub(r"(?:_SX|_SY|_UX|_UY|_CR|_AL)(?:\d+|_).+?\.", "_SX500.", poster)
                        poster = client.replaceHTMLCodes(poster)

                    rating = "0"
                    if items is js_items:
                        if "/user/" in url or "/list/" in url:
                            rating = item['listItem']['ratingsSummary']['aggregateRating']
                        else:
                            rating = item['ratingsSummary']['aggregateRating']
                        rating = str(rating)
                        # fflog(f'{title=}  {rating=}')
                    else:
                        # te class są nieaktualne
                        try:
                            rating = client.parseDOM(item, "span", attrs={"class": "ipc-rating-star--rating"})[0]
                        except:
                            pass
                        if rating == "0":
                            try:
                                rating = client.parseDOM(item, "span", attrs={"class": "rating-rating"})[0]
                            except:
                                pass
                            try:
                                rating = client.parseDOM(rating, "span", attrs={"class": "value"})[0]
                            except:
                                rating = "0"
                        if rating == "0":
                            try:
                                rating = client.parseDOM(item, "div", ret="data-value", attrs={"class": ".*?imdb-rating"})[0]
                            except:
                                pass
                            if rating == "" or rating == "-":
                                rating = "0"
                        rating = client.replaceHTMLCodes(rating)

                    if items is js_items:
                        if "/user/" in url or "/list/" in url:
                            votes = item['listItem']['ratingsSummary']['voteCount']
                        else:
                            votes = item['ratingsSummary']['voteCount']
                        votes = str(votes)
                        # fflog(f'{title=}  {voteCount=}')

                    plot = "0"
                    if items is js_items:
                        if "/user/" in url or "/list/" in url:
                            plot = item['listItem']['plot']['plotText']['plainText']
                        else:
                            plot = item['plot']
                        # fflog(f'{title=}  {plot=}')
                    else:
                        try:
                            plot = client.parseDOM(item, "p", attrs={"class": "text-muted"})[0]
                        except:
                            pass
                        if plot == "0":
                            try:
                                plot = client.parseDOM(item, "div", attrs={"class": "item_description"})[0]
                            except:
                                pass
                        plot = plot.rsplit("<span>", 1)[0].strip()
                        plot = re.sub("<.+?>|</.+?>", "", plot)
                        if not plot:
                            plot = "0"
                        plot = client.replaceHTMLCodes(plot)

                if items is js_items:
                    try:
                        if "/user/" in url or "/list/" in url:
                            mpaa = item['listItem']['certificate']['rating']
                        else:
                            mpaa = item['certificate']
                    except:
                        # mpaa = ""
                        pass

                if items is js_items:
                    try:
                        if "/user/" in url or "/list/" in url:
                            genres = item['listItem']['titleGenres']['genres']
                            genre = " / ".join([g['genre']['text'] for g in genres]) if genres else ""
                        else:
                            genres = item['genres']
                            genre = " / ".join([g for g in genres]) if genres else ""
                    except Exception:
                        fflog_exc(1)
                        # genre = ""
                        pass

                # self.list.append(
                item_el = (  # bo potrzebuję do debugu
                    {
                     "title": title,
                     "originaltitle": originaltitle,
                     "year": year,
                     "premiered": premiered,
                     "rating": rating,
                     "votes": votes,
                     "plot": plot,  # opisy są po angielsku
                     "poster": poster,
                     "mpaa": mpaa,
                     "genre": genre,
                     "imdb": imdb,
                     "tmdb": "0",
                     "tvdb": "0",
                     "next": next_page,
                    }
                )
                # fflog(f'item_el={json.dumps(item_el, indent=2)}',1,1)
                self.list.append(item_el)
            except Exception:
                fflog_exc(1)
                pass

        if items is not js_items:
            # self.list = self.worker(self.list)  # uzupełnienie danych z super_info
            pass

        return self.list


    ### MOJE FILMY - LISTY FILMÓW ###
    ## Listy Użytkownika (TRAKT + IMDB + TMDB)
    def userlists(self):
        fflog(f'{params=}', 1, 1)
        try:
            userlists = []
            if trakt.getTraktCredentialsInfo() is False:
                raise Exception()
            activity = trakt.getActivity()
            #fflog(f'{activity=}')
        except Exception:
            #fflog_exc(1)
            pass

        try:
            if trakt.getTraktCredentialsInfo() is False:
                raise Exception()
            try:
                if activity > cache.timeout(self.trakt_user_list, self.traktlists_link, self.trakt_user):
                    raise Exception()
                #fflog(f'z cache')
                userlists += cache.get(self.trakt_user_list, 720, self.traktlists_link, self.trakt_user)
            except:
                #fflog(f'odświeżam')
                userlists += cache.get(self.trakt_user_list, 0, self.traktlists_link, self.trakt_user)
        except Exception:
            #fflog_exc(1)
            pass

        try:
            self.list = []
            if self.tmdb_sessionid == "":
                raise Exception()
            #fflog(f'z cache')
            userlists += cache.get(self.tmdblist, 24, self.tmdb_user_lists)
        except Exception:
            #fflog_exc(1)
            pass

        try:
            self.list = []
            if not self.imdb_user:
                raise Exception()
            #fflog(f'biorę świeżą')
            userlists += cache.get(self.imdb_user_list, 0, self.imdblists_link)
        except Exception:
            #fflog_exc(1)
            pass

        try:
            self.list = []
            if trakt.getTraktCredentialsInfo() is False:
                raise Exception()
            try:
                if activity > cache.timeout(self.trakt_user_list, self.traktlikedlists_link, self.trakt_user):
                    raise Exception()
                #fflog(f'z cache')
                userlists += cache.get(self.trakt_user_list, 720, self.traktlikedlists_link, self.trakt_user)
            except:
                #fflog(f'odświeżam')
                userlists += cache.get(self.trakt_user_list, 0, self.traktlikedlists_link, self.trakt_user)
        except Exception:
            #fflog_exc(1)
            pass

        self.list = userlists
        for i in range(0, len(self.list)):
            self.list[i].update({
                "action": "tvshows",
                "image": "userlists.png" if not (img:=self.list[i].get("image")) else img,
                })
            #fflog(f'{self.list[i]=}')
        # fflog(f'{self.list=}')
        # fflog(f'self.list={json.dumps(self.list, indent=2)}')
        self.addDirectory(self.list, add_refresh=True)
        return self.list


    ### TRAKT ###
    def trakt_user_list(self, url, user):
        #fflog(f'{url=} {user=}')
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
                    url = (trakt.slug(item["list"]["user"]["username"]), item["list"]["ids"]["slug"])
                except:
                    url = ("me", item["ids"]["slug"])
                url = self.traktlist_link % url
                # url = url

                self.list.append({"name": name, "url": url, "context": url, "image": "trakt.png",})
            except Exception:
                fflog_exc(1)
                pass

        self.list = sorted(self.list, key=lambda k: utils.title_key(k["name"]))
        return self.list


    ## TMDB##
    def tmdblist(self, url):
        # fflog(f'{url=}', 1, 1)
        # url = self.tmdb_user_lists
        tmdb_results = requests.get(url, timeout=30).json()
        # `next` nie jest nigdzie użyte (rysson)  # może to niepotrzebne wcale?
        # page = tmdb_results.get("page", 0)
        # total = tmdb_results.get("total_pages", 0)
        # if page < total and "page=" in url:
        #     next = re.sub(r"page=\d+", f"page={page + 1}", url)
        # else:
        #     next = ""

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
            self.list.append({"name": item.get("name"), "url": self.tmdb_lists_link % str(item.get("id")),
                              "context": self.tmdb_lists_link % str(item.get("id")), "image": "tmdb.png", })
        # self.addDirectory(self.list)
        self.list = sorted(self.list, key=lambda k: utils.title_key(k["name"]))

        return self.list


    ### IMDB ###
    def imdb_user_list(self, url):
        try:
            result = client.request(url)
            items = client.parseDOM(result, "li", attrs={"class": "ipc-metadata-list-summary-item"})
        except Exception:
            fflog_exc(1)
            pass

        for item in items:
            try:
                name = client.parseDOM(item, "a", attrs={"class": "ipc-metadata-list-summary-item__t"})[0]
                name = client.replaceHTMLCodes(name)
                # name = name  # to już niepotrzebne

                url = client.parseDOM(item, "a", ret="href")[0]
                url = url = url.split("/list/", 1)[-1].strip("/")
                url = self.imdblist1_link % url
                url = client.replaceHTMLCodes(url)
                # url = url

                self.list.append({"name": name, "url": url, "context": url, "image": "imdb.png",})
            except Exception:
                fflog_exc(1)
                pass

        self.list = sorted(self.list, key=lambda k: utils.title_key(k["name"]))
        return self.list


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

        # import sys
        # sys.path.append("D:\PyCharm 2022.1.4\debug-eggs\pydevd-pycharm.egg")
        # import pydevd_pycharm
        # pydevd_pycharm.settrace('localhost', port=5678, stdoutToServer=True, stderrToServer=True)
        try:
            # url = re.sub("(?<=api_key=)[^&]*", self.tm_user, url)
            # url = re.sub("(?<=session_id=)[^&]*", self.tmdb_sessionid, url)

            # fflog(f' z {url=}')
            try:
                url = getattr(self, url + "_link")  # szuka atrybutu (np. zmiennej) klasy (self, czyli tvshow)
            except Exception:
                # fflog_exc(1)
                # fflog(f'nie dopasowano _link do url-a , bo {url=}')
                pass
            # fflog(f'na {url=}')

            u = urlparse(url).netloc.lower()  # np. "api.themoviedb.org"
            # fflog(f'{u=}')

            cache_timeout = from_cache = True

            self.idx = idx

            if u in self.tmdb_link and ('/list/' in url or '/collection/' in url or '/discover/' in url or '/airing_today' in url):
                # fflog(f'   wariant1 {url=}')
                cache_timeout = 0 if refresh or not idx else 1
                self.list = cache.get(self.tmdb_list, cache_timeout, url, output_type="tuple")
                if isinstance(self.list, tuple):
                    self.list, from_cache = self.list
                if idx is True:
                    self.worker(from_cache=from_cache)

            elif u in self.tmdb_link and self.tmdb_tv_search in url:
                # fflog(f'   wariant2 {url=}')
                cache_timeout = 0 if refresh or not idx else 1
                self.list = cache.get(self.tmdb_list, cache_timeout, url, output_type="tuple")
                if isinstance(self.list, tuple):
                    self.list, from_cache = self.list
                if idx is True:
                    self.worker(from_cache=from_cache)

            elif u in self.tmdb_link:
                # fflog(f'   wariant3 {url=}')  # wszystkie pozostałe - tu są m.in. watchlisty i ulubione
                cache_timeout = 0 if refresh or not idx else 1
                self.list = cache.get(self.tmdb_list, cache_timeout, url, output_type="tuple")  # lista tytułów
                if isinstance(self.list, tuple):
                    self.list, from_cache = self.list
                    # fflog(f'list {from_cache=}')
                if idx is True:
                    self.worker(from_cache=cache_timeout)  # uszczegółowienie każdego tytułu z listy

            elif u in self.trakt_link and "/users/" in url:
                try:
                    if not "/users/me/" in url:
                        raise Exception()
                    if trakt.getActivity() > cache.timeout(self.trakt_list, url, self.trakt_user):
                        raise Exception()
                    self.list = cache.get(self.trakt_list, 720, url, self.trakt_user, output_type="tuple")
                except:
                    self.list = cache.get(self.trakt_list, 0, url, self.trakt_user)
                if isinstance(self.list, tuple):
                    self.list, from_cache = self.list
                if "/users/me/" in url and "/collection/" in url:
                    if self.list:
                        self.list = sorted(self.list, key=lambda k: utils.title_key(k["title"]))
                if idx is True:
                    self.worker(from_cache=from_cache)

            elif u in self.trakt_link and self.search_link in url:
                self.list = cache.get(self.trakt_list, 1, url, self.trakt_user, output_type="tuple")
                if isinstance(self.list, tuple):
                    self.list, from_cache = self.list
                if idx is True:
                    self.worker(level=0, from_cache=from_cache)

            elif u in self.trakt_link:
                self.list = cache.get(self.trakt_list, 24, url, self.trakt_user, output_type="tuple")
                if isinstance(self.list, tuple):
                    self.list, from_cache = self.list
                if idx is True:
                    self.worker(from_cache=from_cache)

            elif u in self.imdb_link and ("/user/" in url or "/list/" in url):
                cache_timeout = 0 if refresh else 1
                self.list = cache.get(self.imdb_list, cache_timeout, url)
                if isinstance(self.list, tuple):
                    self.list, from_cache = self.list
                if idx is True:
                    self.worker(from_cache=from_cache)

            elif u in self.imdb_link:
                self.list = cache.get(self.imdb_list, 24, url, output_type="tuple")
                if isinstance(self.list, tuple):
                    self.list, from_cache = self.list
                if idx is True:
                    self.worker(from_cache=from_cache)

            elif u in self.tvmaze_link:
                self.list = cache.get(self.tvmaze_list, 168, url, output_type="tuple")
                if isinstance(self.list, tuple):
                    self.list, from_cache = self.list
                if idx is True:
                    self.worker(from_cache=from_cache)


            if self.list:
                #fflog(f'{len(self.list)=}')
                self.list = [i for n, i in enumerate(self.list) if i not in self.list[n + 1:]]  # eliminacja dubli
                #fflog(f'{len(self.list)=}')


            if idx is True and create_directory is True:
                if self.list:
                    self.tvshowDirectory(self.list)
                else:
                    import xbmcgui
                    xbmcgui.Dialog().notification('Błąd', 'Nic nie znaleziono', xbmcgui.NOTIFICATION_ERROR)
                    navigator.navigator().endDirectory()
                    control.execute('Action(Back)')


            return self.list

        except Exception as e:
            fflog_exc(1)
            print(e)
            pass



    def worker(self, media_list=None, level=1, from_cache=None):  # do czego miał służyć "level" ?
        """ pobieranie informacji o tytułach z tmdb"""
        from threading import Thread
        from resources.lib.indexers.super_info import SuperInfo

        # self.meta = []

        if not media_list:
            media_list = self.list  # mutowanie listy będzie następowało

        total = len(media_list) if media_list else 0

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

        super_info_media_list = []  # do zwrócenia wyniku

        for r in range(0, total, 20):

            threads = {super_info_obj: Thread(target=super_info_obj.get_info, args=(i,from_cache,)) for i in
                       range(r, min(total, r + 20)) for super_info_obj in
                       (SuperInfo(media_list, self.session, self.lang, 'tvshow'),)}

            [i.start() for i in threads.values()]
            [i.join() for i in threads.values()]

            for super_info_obj in threads:
                if super_info_obj.meta:
                    super_info_media_list.append( super_info_obj.meta[0].get('item') )  # jak ma być zwrócony wynik

            # if self.meta:  #     metacache.insert(self.meta)

        return super_info_media_list  # opcjonalnie, gdy wyniki są zwracane poprzez zmutowanie self.list, no chyba, że została zadana jakaś konkretna lista (jako argument tej funkcji)

#        self.list = [i for i in self.list if not i["tvdb"] == "0"]
#
#        if self.fanart_tv_user == "":
#            for i in self.list:
#                i.update({"clearlogo": "0", "clearart": "0"})


    def tvshowDirectory(self, items):
        # fflog(f'[tvshowDirectory]')
        if items is None or len(items) == 0:
            sys.exit()

        sysaddon = sys.argv[0]
        syshandle = int(sys.argv[1])

        if control.setting("zastepcze_grafiki") == "true":
            addonPoster = control.addonPoster()
            addonFanart = control.addonFanart()
            addonBanner = control.addonBanner()
        else:
            addonPoster = addonFanart = addonBanner = ""

        settingFanart = control.setting("fanart")

        traktCredentials = trakt.getTraktCredentialsInfo()

        try:
            isOld = False
            control.item().getArt("type")
        except:
            isOld = True

        indicators = (
            playcount.getTVShowIndicators(refresh=True)
            if action == "tvshows"
            else playcount.getTVShowIndicators()
        )

        flatten = True if control.setting("flatten.tvshows") == "true" else False

        watchedMenu = (
            control.lang(32068)
            if trakt.getTraktIndicatorsInfo() is True
            else control.lang(32066)
        )

        unwatchedMenu = (
            control.lang(32069)
            if trakt.getTraktIndicatorsInfo() is True
            else control.lang(32067)
        )

        queueMenu = control.lang(32065)
        traktManagerMenu = control.lang(32070)
        nextMenu = control.lang(32053)
        playRandom = control.lang(32535)
        addToLibrary = control.lang(32551)
        generate_short_path = control.setting("generate_short_path") == "true"

        addSortMethod(syshandle, sortMethod=SORT_METHOD_UNSORTED, labelMask="%L")
        addSortMethod(syshandle, sortMethod=SORT_METHOD_VIDEO_YEAR, labelMask="%L")
        addSortMethod(syshandle, sortMethod=SORT_METHOD_TITLE, labelMask="%L")
        addSortMethod(syshandle, sortMethod=SORT_METHOD_VIDEO_RATING, labelMask="%L")

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

        add_year = control.setting("titles.add_year") == "true"

        counter = 1
        for i in items:
            try:
                # log_utils.fflog(f'{i=}')
                # fflog(f'i={json.dumps(i, indent=2)}')

                def has(key):
                    val = i.get(key)
                    return val and val != "0"

                if "label" in i.keys():
                    label = i["label"]
                else:
                    label = i["title"]

                if not label:
                    continue

                systitle = sysname = quote_plus(i["originaltitle"])
                syslocaltitle = quote_plus(i["title"])

                if "imdb" in i.keys():
                    imdb = str(i["imdb"])
                else:
                    imdb = None

                if "tvdb" in i.keys():
                    tvdb = str(i["tvdb"])
                else:
                    tvdb = None

                if "tmdb" in i.keys():
                    tmdb = str(i["tmdb"])
                else:
                    tmdb = None

                if "year" in i.keys():
                    year = str(i["year"])
                else:
                    year = None

                if add_year and year and year != "0":
                    if year not in label:
                        label += f' ({i["year"]}) '

                meta = dict((k, v) for k, v in i.items() if not v == "0")
                # log_utils.fflog(f'{meta=}')

                meta.pop("next", None)

                meta.update({"code": imdb, "imdbnumber": imdb, "imdb_id": imdb})
                # meta.update({"imdb_id": imdb})
                meta.update({"tvdb_id": tvdb})
                meta.update({"tmdb_id": tmdb})

                meta.update({"mediatype": "tvshow"})

                meta.update({"trailer": "%s?action=trailer&name=%s&url=%s" % (sysaddon, quote_plus(label), quote_plus(meta.get("trailer") or ""))})

                if not "duration" in i:
                    # meta.update({"duration": "60"})
                    pass
                elif i["duration"] == "0":
                    # meta.update({"duration": "60"})
                    pass
                try:
                    if meta.get("duration") and meta.get("duration") != "0":
                        meta.update({"duration": str(int(meta["duration"]) * 60)})
                except:
                    pass

                # try:
                    # meta.update({"genre": cleangenre.lang(meta["genre"], self.lang)})
                # except:
                    # pass

                premiered = meta.get("premiered", 0)
                if not premiered or int(re.sub("[^0-9]", "", str(premiered))) > int(re.sub("[^0-9]", "", str(self.today_date))):
                    label = f"[COLOR {unpremiered_color}][I]%s[/I][/COLOR]" % label

                episodes = i.get("episodes") or 0
                try:
                    overlay = int(playcount.getTVShowOverlay(indicators, imdb, tmdb, episodes))
                    # fflog(f'{overlay=}  {imdb=}  {tmdb=}  {label=} ')
                    if overlay == 7:
                        meta.update({"playcount": 1, "overlay": 7})  # to zmienia ptaszki
                    else:
                        meta.update({"playcount": 0, "overlay": 6})  # to zmienia ptaszki
                except Exception:
                    fflog_exc(1)
                    pass


                cm = []  # prepare context menu

                cm.append(
                    (
                        "Znajdź podobne",
                        "ActivateWindow(10025,%s?action=tvshows&url=https://api.trakt.tv/shows/%s/related,return)"
                        % (sysaddon, imdb),
                    )
                )
                cm.append(
                    (
                        playRandom,
                        "RunPlugin(%s?action=random&rtype=season&tvshowtitle=%s&year=%s&imdb=%s&tvdb=%s)"
                        % (
                            sysaddon,
                            quote_plus(systitle),
                            quote_plus(year),
                            quote_plus(imdb),
                            quote_plus(tvdb),
                        ),
                    )
                )

                if not generate_short_path:  # bo inaczej źle dodaje (dodaje te same odcinki kilka razy w zależności od ilości sezonów)
                    cm.append((queueMenu, "RunPlugin(%s?action=queueItem)" % sysaddon))


                if True:
                    cm.append(
                        (
                            watchedMenu,
                            "RunPlugin(%s?action=tvPlaycount&name=%s&imdb=%s&tmdb=%s&query=7)"
                            % (sysaddon, systitle, imdb, tmdb),
                        )
                    )

                    cm.append(
                        (
                            unwatchedMenu,
                            "RunPlugin(%s?action=tvPlaycount&name=%s&imdb=%s&tmdb=%s&query=6)"
                            % (sysaddon, systitle, imdb, tmdb),
                        )
                    )

                if traktCredentials is True:
                    cm.append(
                        (
                            traktManagerMenu,
                            "RunPlugin(%s?action=traktManager&name=%s&tmdb=%s&content=tvshow)"
                            % (sysaddon, sysname, tmdb),
                        )
                    )

                if isOld is True:
                    cm.append((control.lang2(19033), "Action(Info)"))

                cm.append(
                    (
                        addToLibrary,
                        "RunPlugin(%s?action=tvshowToLibrary&tvshowtitle=%s&localtvshowtitle=%s&year=%s&imdb=%s&tvdb=%s)"
                        % (sysaddon, systitle, syslocaltitle, year, imdb, tvdb),
                    )
                )

                if generate_short_path:
                    cm.append(("[I]przygotuj do ulubionych[/I]", "Container.Update(%s?action=prepareItemForAddToLibrary)" % (sysaddon),))


                item = control.item(label=label, offscreen=True)  # create ListItem


                item.addContextMenuItems(cm)


                art = {}

                poster = i['poster'] if has("poster") else addonPoster
                # poster = i['poster'] if has("poster") else ""

                art.update({
                    "icon": poster,
                    "thumb": poster,
                    "poster": poster,
                    # poniższych chyba nie trzeba (to się raczej wykorzystuje na kolejnych poziomach: sezonach i odcinkach)
                    # "tvshow.poster": poster,
                    # "season.poster": poster,
                    })

                fanart = art["fanart"] = i["fanart"] if settingFanart == 'true' and has("fanart") else addonFanart

                landscape = art["landscape"] = i["landscape"] if has("landscape") else fanart

                banner = art["banner"] = i["banner"] if has("banner") else addonBanner

                for key in ("clearlogo", "clearart", "keyart"):
                    if has(key):
                        art[key] = i[key]
                        #art[f"{key}"] = i[key]
                        #art[f"tvshow.{key}"] = i[key]

                if has("characterart"):
                    characterart = i["characterart"]
                    if isinstance(characterart, list):
                        for an in range(0, len(characterart)):
                            if an == 0:
                                art["characterart"] = characterart[an]
                            else:
                                art[f"characterart{an+1}"] = characterart[an]
                    else:
                        art["characterart"] = characterart


                # fflog(f'{label=}  {art=}')
                item.setArt(art)

                # control.sleep(1000)
                # item.setArt({"dupa":"test"})

                item.setProperty("Fanart_Image", fanart)


                castwiththumb = i.get('castwiththumb')
                if castwiththumb:
                    item.setCast(castwiththumb)


                seasons_meta = {
                    'poster': poster,
                    'fanart': fanart,
                    'banner': banner,
                    'clearlogo': i.get('clearlogo') or '0',
                    'clearart': i.get('clearart') or '0',
                    'keyart': i.get('keyart') or '0',
                    'characterart': i.get('characterart') or '0',
                    'landscape': landscape,
                    'seasons_posters': i.get('seasons_posters') or {},
                    'seasons_banners': i.get('seasons_banners') or {},
                    'seasons_landscapes': i.get('seasons_landscapes') or {},
                    'seasons_fanarts': i.get('seasons_fanarts') or {},
                }

                episodes_meta = {
                    **seasons_meta,
                    'duration': i.get('duration', '0'),
                    'status': i.get('status', '0')
                }

                sysmeta = quote_plus(json.dumps(seasons_meta))
                epmeta = quote_plus(json.dumps(episodes_meta))


                fullpath = ""
                if flatten is True:
                    url = "%s?action=episodes&tvshowtitle=%s&year=%s&imdb=%s&tmdb=%s&tvdb=%s&meta=%s" % (sysaddon, systitle, year, imdb, tmdb, tvdb, epmeta)
                    if generate_short_path:
                        fullpath = url
                        url = "{}?action=episodes&item={}".format(sysaddon, counter)
                        item.setProperty("meta", json.dumps(episodes_meta))
                else:
                    url = "%s?action=seasons&tvshowtitle=%s&year=%s&imdb=%s&tmdb=%s&tvdb=%s&meta=%s" % (sysaddon, systitle, year, imdb, tmdb, tvdb, sysmeta)
                    if generate_short_path:
                        fullpath = url
                        url = "{}?action=seasons&item={}".format(sysaddon, counter)
                        item.setProperty("meta", json.dumps(seasons_meta))


                item.setInfo(type="video", infoLabels=control.metadataClean(meta))


                # korekta pod standard ListItem (bo super_info.py inaczej generuje)
                # vtag.setOriginalTitle(meta.get("originalname") or meta.get("originaltitle", ""))  # nie wiem czy dopiero od Kodi 20
                item.setInfo(type="Video", infoLabels={'OriginalTitle': meta.get("originalname") or meta.get("originaltitle", "")})
                item.setProperty("EnglishTitle", meta.get("englishtitle") or meta.get("originaltitle", ""))

                if generate_short_path:
                    try:
                        vtag = item.getVideoInfoTag()
                        vtag.setUniqueIDs({'imdb': imdb, 'tmdb' : tmdb, 'tvdb' : tvdb})
                    except Exception:
                        item.setProperty("imdb_id", imdb)
                        item.setProperty("tmdb_id", tmdb)
                        item.setProperty("tvdb_id", tvdb)


                if fullpath:
                    item.setProperty("fullpath", fullpath)


                # item.addStreamInfo("video", {"codec": "h264"})  # czy to konieczne?


                control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)

                counter += 1

            except Exception as exc:
                fflog_exc(1)
                import traceback
                # print(f'EXCEPTION: {exc!r}\n{traceback.format_exc()}', file=sys.stderr)  # stderr is logged as ERROR
                print(f'EXCEPTION: {exc!r}\n{traceback.format_exc()}')  # default (stdout) is logged as DEBUG
                pass


        # następna strona
        try:
            url = items[0]["next"]
            if url:
                url = re.sub("(?<=api_key=)[^&]*", "", url)
                url = re.sub("(?<=session_id=)[^&]*", "", url)

                icon = control.addonNext()
                addonLandscape = control.addonLandscape()

                item = control.item(label=nextMenu)  # create ListItem

                item.setArt({"icon": icon, "thumb": icon, "poster": icon, "banner": icon, "landscape": addonLandscape})
                if addonFanart is not None:
                    item.setProperty("Fanart_Image", addonFanart)

                if generate_short_path:
                    page = dict(urllib.parse_qsl(url)).get("page", "")
                    item.setProperty("url", re.sub(f"((?<=[?/])|&)page[=/]{page}", "", url).replace("?&", "?").rstrip("?&"))  # uniwersalniejsze
                    url = "{}?action=tvshowPage&page={}".format(sysaddon, page)
                else:
                    url = "%s?action=tvshowPage&url=%s" % (sysaddon, quote_plus(url))

                refresh = params.get("refresh")
                if refresh:
                    url += "&refresh="+refresh

                control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)
        except Exception as exc:
            fflog_exc(1)
            import traceback
            # print(f'EXCEPTION: {exc!r}\n{traceback.format_exc()}', file=sys.stderr)  # stderr is logged as ERROR
            print(f'EXCEPTION: {exc!r}\n{traceback.format_exc()}')  # default (stdout) is logged as DEBUG
            pass

        control.content(syshandle, "tvshows")
        control.directory(syshandle, cacheToDisc=True)
        views.setView("tvshows")


    def addDirectory(self, items, queue=False, cacheToDisc=True, add_refresh=False):
        # fflog(f'[addDirectory]')
        if items is None or len(items) == 0:
            sys.exit()

        sysaddon = sys.argv[0]
        syshandle = int(sys.argv[1])

        addonFanart, addonThumb, artPath = (
            control.addonFanart(),
            control.addonThumb(),
            control.artPath(),
        )

        queueMenu = control.lang(32065)
        playRandom = control.lang(32535)
        addToLibrary = control.lang(32551)
        generate_short_path = control.setting("generate_short_path") == "true"

        for i in items:
            try:
                name = i["name"]

                if i["image"].startswith("http"):
                    thumb = i["image"]
                elif artPath is not None:
                    thumb = os.path.join(artPath, i["image"])
                else:
                    thumb = addonThumb

                i["url"] = re.sub("(?<=api_key=)[^&]*", "", i["url"])
                i["url"] = re.sub("(?<=session_id=)[^&]*", "", i["url"])

                cm = []  # preparing to buld context menu
                cm.append(
                    (
                        playRandom,
                        "RunPlugin(%s?action=random&rtype=show&url=%s)"
                        % (sysaddon, quote_plus(i["url"])),
                    )
                )
                if queue is True:
                    cm.append((queueMenu, "RunPlugin(%s?action=queueItem)" % sysaddon))
                try:
                    cm.append(
                        (
                            addToLibrary,
                            "RunPlugin(%s?action=tvshowsToLibrary&url=%s)"
                            % (sysaddon, quote_plus(i["context"])),
                        )
                    )
                except:
                    pass


                item = control.item(label=name)  # create ListItem

                item.setArt({"icon": thumb, "thumb": thumb, "poster": thumb,})
                if addonFanart is not None:
                    item.setProperty("Fanart_Image", addonFanart)


                url = "%s?action=%s" % (sysaddon, i["action"])  # akcja, czyli co ma się wykonać po naciśnięciu ENTER na danej pozycji
                action = dict(urllib.parse_qsl("action="+i["action"]))
                try:
                    #if not generate_short_path or i["action"] not in ["tvshows", "tvshowPage"]:  # zabezpieczenie, jakbym nie wszystko sprawdził
                    if not generate_short_path or action["action"] not in ["tvshows", "tvshowPage"] or not "item" in action:  # zabezpieczenie, jakbym nie wszystko sprawdził
                        url += "&url=%s" % quote_plus(i["url"])
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
