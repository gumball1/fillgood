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
import random
import re
import sys
import time
import xbmc  # do aktorów potrzebne
import xbmcgui
import xbmcplugin  # do sortowania potrzebne
#import xbmcaddon
from functools import reduce
from urllib.parse import quote_plus, parse_qsl, unquote, urlencode
from html import unescape, escape
from ast import literal_eval

from ptw.libraries import trakt
from ptw.libraries import control
from ptw.libraries import cleantitle
from ptw.libraries import client
from ptw.libraries import debrid
from ptw.libraries import source_utils
from ptw.libraries import log_utils
from ptw.libraries import PTN
from ptw.libraries import cache
from ptw.libraries import views
from ptw.libraries.log_utils import log, fflog
# from ptw.debug import log, fflog
from ptw.debug import log_exception, fflog_exc

from sqlite3 import dbapi2 as database

try:
    import resolveurl
except Exception as e:
    print(e)
    pass


class sources:
    def __init__(self):
        self.sourceFile = None
        self.url = None
        self.selectedSource = None
        self.itemProperty = None
        self.itemRejected = None
        self.metaProperty = None
        self.sourceDict = None
        self.hostDict = None
        self.hostprDict = None
        self.hostcapDict = None
        self.hosthqDict = None
        self.hostblockDict = None
        self.getConstants()
        self.sources = []
        self.blocked_sources_extend = None
        #self.test = {}
        #self.sources_thrown_out = []
        #control.setting = xbmcaddon.Addon().getSetting
        #control.setSetting = xbmcaddon.Addon().setSetting


    def play(
            self,
            title,
            localtitle,
            year,
            imdb,
            tvdb,
            tmdb,
            season,
            episode,
            tvshowtitle,
            premiered,
            meta,
            select,
            customTitles=None,
            originalname="",
            epimdb="",
        ):
        fflog(f'[play] start', 0)
        # fflog(f'\n{title=} \n{localtitle=} \n{year=} \n{imdb=} \n{tvdb=} \n{tmdb=} \n{season=} \n{episode=} \n{tvshowtitle=} \n{premiered=} \n{meta=} \n{select=} \n{customTitles=} \n{originalname=}  \n{epimdb=}')

        meta1 = None

        if not originalname and meta: 
            try:
                if isinstance(meta, str):
                    meta1 = json.loads(meta)
                originalname = meta1.get("originalname", "")
                #fflog(f'1A {originalname=}')
            except Exception:
                originalname = ""
                pass

        if not originalname:
            try:
                meta1 = cache.cache_get("superinfo" + f"_{tmdb or imdb}")  # zrobiłem to kiedyś dla odcinków głównie
                if meta1:
                    meta1 = meta1["value"]
                    meta1 = literal_eval(meta1)
                    #if imdb == meta1.get("imdb", "") or tmdb == meta1.get("tmdb", ""):  # tu chyba niepotrzebna ta weryfikacja, bo pobrany plik z cache musi pasować
                    originalname = meta1.get("originalname", "")
                    #fflog(f'1B {originalname=}')
                else:
                    if episode:
                        from resources.lib.indexers import episodes
                        meta1 = episodes.episodes().get_meta_for_tvshow(imdb=imdb, tmdb=tmdb)
                    else:
                        from resources.lib.indexers import movies
                        meta1 = movies.movies().get_meta_for_movie(imdb=imdb, tmdb=tmdb)
                    originalname = meta1.get("originalname", "")
                    #fflog(f'1C {originalname=}')
            except Exception:
                pass
            # meta = meta1 if not meta else meta  # tylko, że to jest trochę inna meta, bo po superinfo jest poprawianie

        # przydatne szczególnie dla krótkich linków
        if not tvshowtitle and episode and (tmdb or imdb):
            # czy brać jeszcze wariant pod uwagę, że jest przekazana meta jako argument funkcji ?
            """
            if meta:
                if isinstance(meta, str):
                    meta1 = json.loads(meta)
            else:
            """
            fflog(f'próba pobrania metadanych z bazy cache dla odcinka, bo brakuje {tvshowtitle=}')
            if season or season == 0:
                meta1 = cache.cache_get("episodes" + f"_{tmdb or imdb}_s{season}")
            else:
                meta1 = cache.cache_get("episodes" + f"_{tmdb or imdb}")
            if not meta1:
                fflog("trzeba pobrać dane odcinka z serwisu tmdb.org")
                from resources.lib.indexers import episodes
                meta1 = episodes.episodes().tmdb_list(imdb=imdb, tmdb=tmdb, season=season)
            else:
                #from ast import literal_eval
                fflog(f'dane odcinka są w bazie')
                meta1 = meta1["value"]
                meta1 = literal_eval(meta1)
            meta1 = meta1[int(episode)-1]
            # uzupełniene brakujących danych
            tvshowtitle = meta1.get("tvshowtitle")
            title = meta1.get("title")  # tytuł odcinka ? Czy może być pusty ?
            #localtitle = meta1.get("localtvshowtitle")  # ? a może label? a może nie ważne jaki
            localtitle = meta1.get("label")
            originalname = meta1.get("originaltvshowtitle", "") or originalname
            year = meta1.get("year")
            premiered = meta1.get("premiered")
            # meta = meta1 if not meta else meta  # nie wszystko może pasować

        if not title and not episode and (tmdb or imdb):  # dla filmów
            fflog(f'próba pobrania metadanych z cache dla filmu, bo brakuje albo {title=}')
            meta1 = cache.cache_get("superinfo" + f"_{tmdb or imdb}")  # sprawdzenie, czy nie ma już w cache
            if not meta1:
                fflog('potrzeba jednak pobrać informacje o filmie przez super_info.py')
                from resources.lib.indexers.super_info import SuperInfo
                media_list = [{'tmdb': tmdb, 'imdb': imdb}]
                import requests
                session = requests.Session()
                lang = control.apiLanguage()["tmdb"]
                super_info_obj = SuperInfo(media_list, session, lang)
                super_info_obj.get_info(0)
                meta1 = cache.cache_get("superinfo" + f"_{tmdb or imdb}")
            if meta1:
                meta1 = meta1["value"]
                meta1 = literal_eval(meta1)
            # uzupełniene brakujących danych
            title = meta1.get("originaltitle")
            localtitle = meta1.get("title")
            originalname = meta1.get("originalname", "") or originalname
            year = meta1.get("year")
            # meta = meta1 if not meta else meta  # nie wszystko musi pasować

        if not title and not tvshowtitle:
            fflog(f'Błąd - brak zmiennej {title=} lub {tvshowtitle=}')
            control.dialog.notification('FanFilm', 'błąd: brak zmiennej "title" lub "tvshowtitle"', xbmcgui.NOTIFICATION_ERROR)
            return

        if not meta and meta1:
            # meta = json.dumps(meta1)  # lepiej nie (przynajmniej dla seriali, bo gubi rekordy np. tvshowtitle), bo to trochę inna meta, bo po superinfo jest przerabiane potem
            pass
        meta1 = None

        # to z default.py
        FFlastpath = control.window.getProperty('FanFilm.var.lastpath')  # z pamięci
        FFlastpath = eval(FFlastpath) if FFlastpath else {}  # tylko jak Kodi wczytuje folder z cachu, to ta zmienna się nie zmienia (bo plugin nie jest wywoływany)
        fflog(f'{FFlastpath=}', 0)

        folderpath = control.infoLabel('Container.FolderPath')  # może być też puste i nie zawsze okazuje się, że jest poprzednim, np. gdy odpalamy widżety
        # fflog(f'{folderpath=}')
        imdb_curr = ''

        params1 = dict(parse_qsl(folderpath.split('?')[-1]))
        fflog(f'{params1=}', 0)

        action1 = params1.get('action')  # może być też puste

        params2 = dict(parse_qsl(sys.argv[2][1:]))
        fflog(f'{params2=}', 0)
        if params2.get("r"):
            if (params1 := control.window.getProperty('FanFilm.var.before_r')) or (params1 := dict(parse_qsl(folderpath.split('?')[-1]))) and not params1.get("r"):
                params1 = eval(params1) if isinstance(params1, str) else params1
                # fflog(f'{params1=}')
                params2.update(params1)
        fflog(f'{params2=}', 0)

        action2 = params2.get('action')

        # referer = folderpath if action1 != action2 else ''  # niepotrzebna ta zmienna
        # log(f'{referer=}')

        fflog(f'\n{params1=}  \n{params2=}', 0)
        fflog(f'{action1=}  {action2=}', 0)
        # if action1 not in ["play", "alterSources"]:
        # fflog(f'{control.setting("crefresh_always")=}')
        if action1 != action2 and action1 != "showItems" or control.setting("crefresh_always")=="true":
            fflog(f'wymuszenie odświeżenia listy źródeł', 1)
            control.window.clearProperty('imdb_id')  # aby odświeżyć listę źródeł

        # params = None
        if (url := params2.get('url')):  # gdy z menu kontekstowego
            fflog(f'{url=}', 0)
            # params = params2  # nie wiem, czy to potrzebne
            params2 = dict(parse_qsl(url.split('?')[-1]))  # czy to nie zepsuje użycia params2 w dalszej części, już po zdecydowaniu, czy odświeżać czy nie?
            fflog(f'{params2=}', 0)

        items = None

        if control.setting("crefresh") != "true":

            # imdb_curr = params2.get('imdb', '')
            imdb_curr = params2.get('imdb', imdb)  # gdy krótkie ścieżki, to nie będzie takich danych w adresie
            # fflog(f'{imdb_curr=}')
            # imdb_curr = imdb_curr if imdb_curr else imdb if imdb else ''  # zastanowić się nad tym
            # fflog(f'{imdb_curr=}')
            if episode and imdb_curr is not None:
                # imdb_curr += "|" + params2.get('epimdb', '') + "|s" + params2.get('season', '') + "|e" + params2.get('episode', '')
                # imdb_curr += "|" + params2.get('epimdb', epimdb) + "|s" + params2.get('season', season) + "|e" + params2.get('episode', episode)
                imdb_curr += "|" + epimdb + "|s" + str(season) + "|e" + str(episode)  # ważne, jak modyfikowane do wyszukiwarki
            fflog(f'{imdb_curr=}', 0)

            imdb_last = control.window.getProperty('imdb_id')  # jeśli nie zostanie wyczyszczone
            fflog(f'{imdb_last=}', 0)
            #imdb_last = None if control.setting("crefresh") == "true" else imdb_last  # uwzględnienie ustawień wtyczki (ale czy to nie jest już zbędne?)
            if imdb_last:
                if (
                    imdb_curr == imdb_last  # to byłoby najlepsze, ale czasami coś gubił i mimo, że nie musiał, to odświeżał
                    # or customTitles is not None and imdb_curr.split("|")[0] == imdb_last.split("|")[0]
                    # or action1 == action2  # czy to nie będzie kolidowało, gdy kotś wyświetla w okienku?
                    # or params1 == params2  # or customTitles is not None  # dodałem ostatnio - tylko, że to coś koliduje, gdy odpala się z widżetu - nie odświeża źródeł, jak jest inny film
                    # or (params1 == params2 and params1 == FFlastpath)  # chyba nie zaszkodzi
                    or FFlastpath.get("action") == "playItem"  # nie odświeżamy po odtwarzaniu
                ):
                    fflog(f'{FFlastpath.get("action")=}', 0) if imdb_curr != imdb_last else ''
                    imdb_curr = imdb_last if imdb_curr != imdb_last else imdb_curr  # pomaga w przypadku modyfikowanych danych do wyszukiwarki
                    fflog(f'[play] próba pobrania wyników z poprzedniego wyszukiwania', 1)
                    items = control.window.getProperty(self.itemProperty)
                    if items:
                        # fflog(f'[play] coś odczytano', 1)
                        # fflog(f'[play] {items=}', 1)
                        items = json.loads(items)
                        fflog(f'[play] {len(items)=}', 1)
                    else:
                        fflog(f'[play] brak zapamiętanych', 1)
                else:
                    fflog(f'[play] nie zostaną wzięte wyniki z ostatniego wyszukiwania źródeł', 0)
                    fflog(f'{imdb_curr=}  !=  {imdb_last=}  |  {customTitles=}', 1)
                    # fflog(f'\n   {params1=}\n   {params2=}\n{FFlastpath=}', 1)
                    pass

        # params2 = params if params else params2  # nie wiem, czy to dobrze
        # params = None

        try:
            meta = json.loads(meta)
        except Exception:
            meta = {}

        #if control.window.getProperty("TMDbHelper.ServiceStarted") == "True":
        if not meta:
            props = ["title", "localtitle", "originaltitle", "year", "genre", "country", "rating", "votes", "mpaa", "director", "writer", "studio", "Tagline", "thumb", "Art(poster)", "poster", "trailer", "plot", "label", "duration"]
            #if "tmdb_type=tv" in folderpath:
            if tvshowtitle:
                # meta.update({'mediatype': 'episode'})
                props += ["season", "episode", "tvshowtitle", "localtvshowtitle", "premiered", "Art(season.poster)"]
            props = set(props)

            #can_get_from_tmdbhelper = False
            # if folderpath.startswith("plugin://plugin.video.themoviedb.helper/") and control.infoLabel("ListItem.Property(IMDb_ID)") in [imdb, epimdb]:
            if "plugin.video.fanfilm" not in control.infoLabel("Container.PluginName") and control.infoLabel("ListItem.Property(IMDb_ID)") in [imdb, epimdb]:
                #can_get_from_tmdbhelper = True
                fflog('próba pobrania danych meta z ListItemu wybranej pozycji')
                for p in props:
                    if (val := control.infoLabel('ListItem.'+p.capitalize())) and val != 'ListItem.'+p.capitalize():
                        meta.update({p: val})
                        pass
                if (val := control.infoLabel("ListItem.Property(original_language)")):
                    meta.update({"original_language": val})
            else:
                fflog('próba pobrania danych meta z adresu wywołania url')
                """
                params2 = dict(parse_qsl(sys.argv[2][1:]))
                if params2.get("r"):
                    if (params1 := control.window.getProperty('FanFilm.var.before_r')) or (params1 := dict(parse_qsl(folderpath.split('?')[-1]))) and not params1.get("r"):
                        params1 = eval(params1) if isinstance(params1, str) else params1
                        # fflog(f'{params1=}')
                        params2.update(params1)
                """
                for p in props:
                    if (val := params2.get(p, "")):
                        meta.update({p: val})
                # korekty na potrzeby FanFilm
                if (val := meta.get("localtitle")):
                    meta.update({"title": val});  meta.pop('localtitle')
                if (val := meta.get("localtvshowtitle")):
                    meta.update({"tvshowtitle": val});  meta.pop('localtvshowtitle')

            # pozostałe korekty na potrzeby FanFilm
            #fflog(f"{meta.get('thumb')=}")
            if not (thumb := meta.get('thumb')) or thumb == "None" or ".strm/" in thumb:
                meta.pop("thumb", None)
            if not (poster := meta.get('poster')) or poster == "ListItem.Poster" or ".strm/" in poster:
                meta.pop("poster", None)
                #if not (poster := control.infoLabel('ListItem.Icon')) or not can_get_from_tmdbhelper:
                if not (poster := control.infoLabel('ListItem.Icon')) or params2.get("poster"):
                    poster = params2.get("poster", "")
                if poster and ".strm/" not in poster:  # a co jak będzie ".mkv/" ?
                    # fflog(f'{poster=}')
                    meta.update({'poster': poster})
            if tvshowtitle:
                if (poster := meta.get("Art(season.poster)")):
                    meta.update({'poster': poster});  meta.pop("Art(season.poster)", None)
            else:
                if (poster := meta.get("Art(poster)")):
                    meta.update({'poster': poster});  meta.pop("Art(poster)", None)
            #fflog(f'{meta=}')
        # bo indexer z FF też daje angielski zamiast polskiego
        if (val := meta.get("localtvshowtitle")):
            meta.update({"tvshowtitle": val});  meta.pop('localtvshowtitle')
            pass

        # control.window.clearProperty(self.metaProperty)  # po co to ?
        control.window.setProperty(self.metaProperty, json.dumps(meta))


        if not items:
            # pobranie źródeł (wyszukiwanie)
            fflog(f'[play] potrzeba wyszukania źródeł', 1)
            control.window.clearProperty(self.itemProperty)  # wyczyszczenie poprzednich wyników
            fflog(f'[play] {title=} {localtitle=} {year=} {imdb=} {tvdb=} {tmdb=} {season=} {episode=} {tvshowtitle=} {premiered=} {originalname=} {customTitles=}', 1)
            items = self.getSources(title, localtitle, year, imdb, tvdb, tmdb, season, episode, tvshowtitle, premiered, originalname)
            fflog(f'[play] otrzymano jakieś wyniki', 0)
            fflog(f'{len(items)=}')  # może być zero, ale mogą być "w koszu"
            if customTitles is not None:
                control.window.setProperty('clear_SourceCache_for', 'all')  # jak ktoś używa enableSourceCache
        else:
            fflog(f'[play] nie będzie procesu wyszukiwania źródeł', 0)
            pass


        select = control.setting("hosts.mode") if select is None else select
        # fflog(f'{select=}')
        # if select == "1" and folderpath.startswith("plugin://plugin.video.themoviedb.helper/"):
        # if select == "1" and not control.infoLabel("Container.PluginName"):  # próba uniwersalności
        if select == "1" and "plugin.video.fanfilm" not in control.infoLabel("Container.PluginName"):  # próba uniwersalności
            select = "0"
            fflog(f'zmieniono na {select=} (z 1)')
        #elif (select == "0" or select == "2") and int(sys.argv[1]) > 0 and not folderpath.startswith("plugin://plugin.video.themoviedb.helper/"):
        #elif select == "0" and int(sys.argv[1]) > 0 and control.infoLabel("Container.PluginName") and not control.infoLabel("ListItem.FolderPath"):  # nie mogą być przekierowania
        elif (select == "0" or select == "2") and int(sys.argv[1]) >= 0 and control.infoLabel("Container.PluginName") and not control.infoLabel("ListItem.FolderPath"):  # nie mogą być przekierowania
            select = "1"  # pomaga wyświetlać katalogi, gdy user ustawił okienko  # nie wiem jak przy 1 zrobić automatyczne odtwarzanie
            fflog(f'zmieniono na {select=} (z 0)')
            pass
        # fflog(f'{select=}')
        title = tvshowtitle if tvshowtitle is not None else title


        if control.window.getProperty("PseudoTVRunning") == "True":
            # autoplay
            control.resolve( int(sys.argv[1]), True, control.item(path=str(self.sourcesDirect(items))) )
            return

        url = None
        subs = None

        if items or ( json.loads(control.window.getProperty(self.itemRejected)) and (select == "1" or select == "0") ):

            if params2.get("download"):
                fflog(f'odrzucenie lokalnych źródeł, bo z nich nie można pobierać', 1)
                def remove_some_sources_and_numbers(items):
                    #fflog(f'{items=}')
                    items = [i for i in items if i.get('provider') not in['pobrane', 'library', 'biblioteka', 'plex', 'external']]
                    # można jeszce ewentualnie numery usunąć z labela (jak są) aby nie było ewentualnych dziur
                    # fflog(f'{items=}')
                    # [i.update({'label': re.sub(r'\[LIGHT\]\d+\[/LIGHT\]\s*\|\s*', '', i.get('label'))}) for i in items]
                    [i.update({'label': re.sub(r'^(\D*)\d+(\D*?)[| ]\s*', r'\1\2', i.get('label'))}) for i in items]
                    return items
                items = remove_some_sources_and_numbers(items)
                itemRejected = json.loads(control.window.getProperty(self.itemRejected))
                if itemRejected:
                    itemRejected = remove_some_sources_and_numbers(itemRejected)
                    control.window.setProperty(self.itemRejected, json.dumps(itemRejected))

            #params2 = dict(parse_qsl(sys.argv[2][1:]))
            fflog(f'[play] {select=} {params2.get("r")=}', 0)

            if select == "1" and "plugin" in control.infoLabel("Container.PluginName") or params2.get("r"):  # directory
                control.window.setProperty('imdb_id', imdb_curr)
                
                # fflog(f'{len(items)=}')
                control.window.setProperty(self.itemProperty, json.dumps(items))

                #control.sleep(200)  # nie pamiętam do czego potrzebne
                if control.setting("hosts.mode") != "2":
                    fflog(f'[play] przygotowanie do wypisywania pozycji w katalogu', 0)
                    #sources().showItems(quote_plus(title), items)
                    # sources().showItems(title, items)
                    self.showItems(title, items, None, season, episode)
                    return  # dalej kod już nie idzie
                else:  # próba autoplay, gdy Kodi wymaga wyświetlienia katalogu
                    fflog(f'[play] próba autoplay, gdy Kodi wymaga wyświetlienia katalogu', 0)
                    handle = int(sys.argv[1])
                    updateListing = True if params2.get("r") else False  # True świadczy, że po drodze było odświeżanie
                    ret_item = True 
                    url = self.sourcesDirect(items, ret_item=ret_item)
                    if isinstance(url, tuple):
                        url, subs = url
                    if url and not url.startswith('close://'):
                        control.addItem(handle, sys.argv[0]+"?action=nothing", control.item("autoodtwarzanie"), False)  # warto dać, bo inaczej Kodi nie zapisuje chyba do cachu i próbuje odświeżyć i ponownie włącza odtwarzanie
                        control.directory(handle, updateListing=updateListing)
                        from ptw.libraries.player import player
                        #player().play(url)
                        player().run((title, localtitle, originalname, meta.get("tvshowtitle", "")), year, season, episode, imdb, tvdb, tmdb, url, subs, meta, -1)
                    else:
                        self.errorForSources()
                        control.directory(handle, updateListing=updateListing)
                    fflog('akcja wstecz', 1)
                    control.execute('Action(Back)')
                    return

            elif select == "0" or select == "1":  # popup window (Dialog typu Select) lub pliki strm
                # czy to ma tu sens ? Bo chyba nigdy nie zajdzie taki przypadek
                # bo okno potem znika, i aby pojawiło się nowe, to trzeba zrobić wyszukiwanie, a te "wymusza" szukanie od nowa
                if control.setting("crefresh") != "true":
                    control.window.setProperty('imdb_id', imdb_curr)
                    control.window.clearProperty(self.itemProperty)
                    control.window.setProperty(self.itemProperty, json.dumps(items))

                ret_item = True
                # ret_item = True if params2.get("download") else False
                url = self.sourcesDialog(items, ret_item=ret_item)  # dialog aby wybrać źródło

            else:  # select ==2 (autoplay)
                ret_item = True
                # ret_item = True if params2.get("download") else False
                url = self.sourcesDirect(items, ret_item=ret_item)  # zwraca pierwszą pozycję z listy

        if select == "0":
            control.idle(2)
            pass

        fflog(f'{url=}', 0)

        if isinstance(url, list):
            url, item = url
        else:
            item = {}
            pass

        # fflog(f' {url=}', 1)

        if params2.get("download"):
            if url:
                if isinstance(url, tuple):
                    url = url[0]
                    # napisów nie pobieramy
                if not url.startswith('plugin://') and not url.startswith('close://'):

                    TvShowYear = control.infoLabel('ListItem.Property(TvShowYear)') or meta.get("tvshowyear")
                    localtvshowtitle = control.infoLabel('ListItem.Property(localTvShowTitle)') or meta.get("tvshowtitle") or title
                    #localtitle = control.infoLabel('ListItem.Property(localTitle)') or meta.get("title") or title
                    if "tvshowtitle" in meta and "season" in meta and "episode" in meta:
                        sysname = (localtvshowtitle)
                        if TvShowYear:
                            sysname += (" (%s)" % TvShowYear)  # to musi być rok serialu, nie odcinka
                        sysname += (" S%02dE%02d" % (int(meta["season"]), int(meta["episode"])))
                    elif "year" in meta:
                        sysname = (localtitle)
                        sysname += (" (%s)" % meta["year"])

                    allow_extrainfo_to_download = control.setting("download.extrainfo") == "true"
                    if allow_extrainfo_to_download:
                        extrainfo = (item.get("quality") or "") if item.get("quality") not in ["SD", ""] else ""
                        extrainfo += " " + item.get("extrainfo", "") or ""
                        extrainfo = extrainfo.replace(" | AVI", "")
                        extrainfo += " " + (item.get("info") or "")  # lektor, napisy, ale i rozmiar na końcu
                        extrainfo = re.sub(r"(?:^|\s*\|)\s*(\d+(?:[.,]\d+)?)\s*([GMK]B)\b\s*(?:\||$)", "", extrainfo, flags=re.I,)  # pozbycie się rozmmiaru
                        extrainfo += " " + (item.get("language") or "").upper()
                        extrainfo = extrainfo.replace(" | ", " ").replace(" / ", " ").strip()
                        extrainfo = re.sub(r"\s{2,}", " ", extrainfo).strip()  # nadmiarowe spacje
                        extrainfo = f"[{extrainfo}]" if extrainfo else ""
                    else:
                        extrainfo = ""

                    from ptw.libraries import downloader
                    downloader.download(name=sysname, image="", url=url, extrainfo=extrainfo)
            else:
                self.errorForSources()  # komunikat o błędzie
            return  # zakładam, że wywołanie tego będzie tylko z handle -1, czyli poprzez RunPlugin z context menu

        if url:  # only when popup window (dialog) or autoplay (select 0 or 2)
            if isinstance(url, tuple):
                url, subs = url
            if url.startswith('plugin://') and "plugin" in control.infoLabel("Container.PluginName"):  # nie wiem kiedy to zachodzi (może dla źródeł external?)
                fflog(f'[play] wywołanie odtwarzacza mając tylko {url=}', 1)
                from ptw.libraries.player import player
                player().play(url)
            elif not url.startswith('close://'):  # przeważnie jest to
                # fflog(f'[play] wywołanie odtwarzacza z większą ilością parametrów', 1)
                from ptw.libraries.player import player
                player().run( (title, localtitle, originalname, meta.get("tvshowtitle", "")), year, season, episode, imdb, tvdb, tmdb, url, subs, meta, hosting=item.get("source") )
            elif url.startswith('close://'):
                pass
        else:
            self.errorForSources()  # komunikat o błędzie

        handle = int(sys.argv[1])

        if not url or url.startswith('close://'):
        # if url and url.startswith('close://'):  # tylko dla akcji Anuluj
            # fflog(f'nieudane odtwarzanie, bo {url=}  {handle=}  {control.infoLabel("Container.PluginName")=}')
            # próba odtwarzania jakiegoś fejkowego wideo, aby Kodi nie rzucał komunikatem o nieudanym odtwarzaniu
            # plik powinien być trochę dłuższy, bo trzeba przerwać odtwarzanie, aby Kodi nie zakwalifikował pozycji jako obejrzana, a przy wznowieniu powinien być jeszcze dłuższy
            # (nie wiem, czy ten komunikat nie pojawia się tylko w przypadku próby odtwarzanie plików z poza wtyczki FanFilm)
            # if "plugin.video.fanfilm" not in control.infoLabel("Container.PluginName") and url:  # tylko dla akcji Anuluj
            # if url:  # tylko, gdy są źródła (nie robimy, gdy nie ma źródeł)
            if True:  # zawsze
            #if False:  # bo odtworzenie powoduje zmianę długości w informacjach o filmie, także lepiej jednak nie
                if handle >= 0:
                    # control.resolve(handle, False, control.item())  # ale czy to w czymś pomaga? Bo komunikat i tak co jakiś czas się pojawia
                    pass
                    """
                    fflog('próba odtworzenia fragmenciku fejkowego wideo')  # ciekawe, czy playcount się zmienia
                    #url = ""
                    #from ptw.libraries.player import PlayerHacks
                    #PlayerHacks().resolve_to_dummy_hack(url)
                    # url = "special://home/addons/script.module.ptw/resources/dummy.mp4"
                    url = "special://home/addons/script.module.ptw/resources/empty.m3u8"  # nie działa
                    fflog(f'{url=}', 1)
                    control.resolve(handle, True, control.item(path=url, offscreen=True))  # start
                    # control.sleep(20)  # nie wiem, czy potrzebne
                    control.player.stop()  # stop
                    #control.sleep(20)  # extra time for callback can execute
                    fflog('koniec odtwarzenia fejkowego wideo', 1)
                    """

        control.sleep0(250)
        if handle > -1:
            #params2 = dict(parse_qsl(sys.argv[2][1:]))
            fflog('dodanie pustego katalogu', 1),1
            updateListing = True if params2.get("r") else False  # True świadczy, że po drodze było odświeżanie
            control.directory(handle, updateListing=updateListing)
            #fflog(f'zrobić akcję wstecz czy nie ? {select=} {control.infoLabel("Container.PluginName")=} \n{params2=} \n{params1=}')
            if select == "1" and "plugin" in control.infoLabel("Container.PluginName"):
                fflog('akcja wstecz', 1)
                control.execute('Action(Back)')


    def showItems(self, title="", items=None, trash=None, season=None, episode=None):
        
        def sourcesDirMeta(metadata):
            if not metadata:
                return metadata
            allowed = [
                "icon",
                "poster",
                "fanart",
                "thumb",
                "clearlogo",
                "clearart",
                "discart",
                "banner",
                "title",
                "year",
                "tvshowtitle",
                "season",
                "episode",
                "rating",
                "plot",
                "trailer",
                "mediatype",
                "imdb",
                "tvdb",
                "tmdb",
                "votes",
                "originaltitle",
                "genre",
                # "country",
                "director",
                "mpaa",  # kategoria wiekowa
                "duration",
                "castwiththumb",  # obsada
                "premiered",  # nie wiem czy potrzebny
            ]
            return {k: v for k, v in metadata.items() if k in allowed}

        control.playlist.clear()  # ciekawe, czy można to wykorzystać do zniwelowania informacji o błędzie odtwarzania, jak zrezygnujemy ("skip unplayable item")

        #if name == "odrzucone":
        if trash:
            items = control.window.getProperty(self.itemRejected)
            try:
                items = json.loads(items)
            except:
                control.dialog.notification('FanFilm', 'wystąpił jakiś błąd', xbmcgui.NOTIFICATION_ERROR)
                fflog_exc()
                return
            #items = self.sortSources(items)
            #items = self.renumberSources(items)  # nie ma jeszcze takiej funkcji
        elif not items:
            items = control.window.getProperty(self.itemProperty)
            try:
                items = json.loads(items)
            except:
                control.dialog.notification('FanFilm', 'wystąpił jakiś błąd', xbmcgui.NOTIFICATION_ERROR)
                fflog_exc()
                return

        meta = control.window.getProperty(self.metaProperty)
        try:
            meta = json.loads(meta)
        except Exception:
            fflog_exc()
            meta = {}

        if not title:
            title = meta.get("title", "")
        if not title:
            control.dialog.notification('FanFilm', 'błędny parametr', xbmcgui.NOTIFICATION_ERROR)
            fflog(f"{title=}")
            return
        # fflog(f'{meta=}')

        originalname = meta.get("originalname", "")
        TvShowYear = control.infoLabel('ListItem.Property(TvShowYear)') or meta.get("tvshowyear")
        localtvshowtitle = control.infoLabel('ListItem.Property(localTvShowTitle)') or meta.get("tvshowtitle") or title
        localtitle = control.infoLabel('ListItem.Property(localTitle)') or meta.get("title") or title

        meta = sourcesDirMeta(meta)  # usuwa niestandardowe rekordy

        # (Kodi bug?) [name,role] is incredibly slow on this directory,
        #             [name] is barely tolerable, so just nuke it for speed!
        #        if "cast" in meta:  # "cast" czy "castwiththumb" ?
        #            del meta["cast"]

        sysaddon = sys.argv[0]
        syshandle = int(sys.argv[1])

        downloads = (
            control.setting("downloads") == "true"
            and not (
                control.setting("movie.download.path") == ""
                or control.setting("tv.download.path") == ""
            )
        )

        systitle = quote_plus(title)

        # potrzebne dla schematu nazywania pobranego pliku
        if "tvshowtitle" in meta and "season" in meta and "episode" in meta:
            sysname = quote_plus(localtvshowtitle)
            if TvShowYear:
                sysname += quote_plus(" (%s)" % TvShowYear)  # to musi być rok serialu, nie odcinka
            sysname += quote_plus(" S%02dE%02d" % (int(meta["season"]), int(meta["episode"])))
        elif "year" in meta:
            sysname = quote_plus(localtitle)
            sysname += quote_plus(" (%s)" % meta["year"])

        poster = meta["poster"] if "poster" in meta else "0"
        fanart = meta["fanart"] if "fanart" in meta else "0"
        thumb = meta["thumb"] if "thumb" in meta else "0"
        if thumb == "0":
            thumb = poster
        if thumb == "0":
            thumb = fanart
        banner = meta["banner"] if "banner" in meta else "0"
        if banner == "0":
            banner = poster
        if poster == "0":
            poster = control.addonPoster()
        if banner == "0":
            banner = control.addonBanner()
        if not control.setting("fanart") == "true":
            fanart = "0"
        if fanart == "0":
            fanart = control.addonFanart()
        if thumb == "0":
            thumb = control.addonFanart()

        sysimage = quote_plus(poster.encode("utf-8"))

        downloadMenu = control.lang(32403)

        list_of_items = []
        providers = []
        list_of_sources = []
        
        sysmeta = meta.copy()
        sysmeta.pop("rating", None)
        sysmeta.pop("votes", None)
        # sysmeta.pop("next", None)  # tego i tak nie ma w meta po jej przefiltrowaniu
        sysmeta = quote_plus(json.dumps(sysmeta))

        dont_use_setResolvedUrl = control.setting("player.dont_use_setResolvedUrl") == "true"

        generate_short_path = control.setting("generate_short_path") == "true"
        # generate_short_path = False  # bo taka pozycja dodana do ulubionych nie zadziała
        # tylko zmienianie raz tak raz tak będzie powodować, że Kodi nie będzie rozpoznawało czy dane źródło obejrzane, czy nie - dlatego dobrze byłoby się zdecydować na coś i trzymać się tego

        allow_extrainfo_to_download = control.setting("download.extrainfo") == "true"

        ia = control.setting("player.ia") == "true"
        
        auto_select_next_item_to_play = control.setting("auto.select.next.item.to.play") == "true"

        for i in range(len(items)):
            # fflog(f'{i=} {items[i]=}')
            label = items[i].get("label")
            if not label:
                continue

            if downloads and allow_extrainfo_to_download:
                extrainfo = (items[i].get("quality") or "") if items[i].get("quality") not in ["SD", ""] else ""
                extrainfo += " " + items[i].get("extrainfo", "") or ""
                extrainfo = extrainfo.replace(" | AVI", "")
                extrainfo += " " + (items[i].get("info") or "")  # lektor, napisy, ale i rozmiar na końcu
                extrainfo = re.sub(r"(?:^|\s*\|)\s*(\d+(?:[.,]\d+)?)\s*([GMK]B)\b\s*(?:\||$)", "", extrainfo, flags=re.I,)  # pozbycie się rozmmiaru
                extrainfo += " " + (items[i].get("language") or "").upper()
                extrainfo = extrainfo.replace(" | ", " ").replace(" / ", " ").strip()
                extrainfo = re.sub(r"\s{2,}", " ", extrainfo).strip()  # nadmiarowe spacje
                extrainfo = f"[{extrainfo}]" if extrainfo else ""
            else:
                extrainfo = ""

            # próba wyeliminowanie zmiennych elementów, które przeszkadzają, aby Kodi precyzyjnie oznaczał status wznowienia i obejrzania
            # del items[i]["label"]  # bo m.in dużo znaczników formatujących
            items[i] = {k:v for k,v in items[i].items() if k not in ["label", "on_account", "on_account_link", "on_account_expires", "info2", "trash", "unsure", "extrainfo"]}

            syssource = quote_plus(json.dumps([items[i]]))

            sysurl = "%s?action=playItem&title=%s&source=%s&meta=%s" % (sysaddon, systitle, syssource, sysmeta)
            # sysurl = "%s?action=playItem&source=%s&meta=%s" % (sysaddon, syssource, sysmeta)  # wyeliminowałem title z adresu, bo jest on w meta
            # eksperyment
            if generate_short_path:
                sysurl = "%s?action=playItem&title=%s&source=%s&imdb=%s&tmdb=%s" % (sysaddon, systitle, syssource, meta.get("imdb",""), meta.get("tmdb",""))
                # sysurl = "%s?action=playItem&source=%s&imdb=%s&tmdb=%s" % (sysaddon, syssource, meta.get("imdb",""), meta.get("tmdb",""))
                # if meta.get("mediatype") == "tvshow":  # nie zawsze działa np. nie działa dla źródeł odcinka
                # problem ulubionych jest to, że nie są zapamiętywane dane obiektu ListItem, a tylko label, icon oraz path
                # ale tu w sumie nie ma aż tak o co walczyć, bo to się nie wyświetla w oknie, choć w bazie MyVideos zapisują się długie ścieżki

            if "tvshowtitle" in meta and "season" in meta and "episode" in meta:  # to jest obowiązkowo potrzebne dla krótkich adresów, ale także przydaje się, gdy były modyfikowane parametry do wyszukiwarki
                # sysurl = "%s?action=playItem&source=%s&imdb=%s&tmdb=%s&season=%s&episode=%s" % (sysaddon, syssource, meta.get("imdb",""), meta.get("tmdb",""), meta.get("season"), meta.get("episode"))
                sysurl += "&season=%s&episode=%s" % ( season or meta.get("season"), episode or meta.get("episode") )
            # fflog(f'{sysurl=}')

            # context menu
            cm = []

            not_library_and_not_downloaded = items[i]["provider"]!='pobrane' and items[i]["provider"]!='library' and items[i]["provider"]!='biblioteka'
            if downloads and not_library_and_not_downloaded:
                cm.append(
                    (
                        downloadMenu,
                        "RunPlugin(%s?action=download&name=%s&image=%s&source=%s&extrainfo=%s)"
                        % (sysaddon, sysname, sysimage, syssource, quote_plus(extrainfo)  ),
                    )
                )

            if items[i]["provider"]=='tb7' or items[i]["provider"]=='xt7':
                cm.append(
                    (
                        "Ponownie wykorzystaj transfer",
                        "RunPlugin(%s?action=buyItemAgain&title=%s&source=%s)"
                        % (sysaddon, systitle, syssource),
                    )
                )

            if not ia and not_library_and_not_downloaded:  # ponieważ rozwiązanie adresu odbywa się przeważnie dopiero przed samym odtwarzaniem, więc nie da się w tym miejscu wykrywać frazy m3u8 w adresie url źródła
                cm.append(
                    (
                        "Odtwórz przez Inputstream Adaptive",
                        "PlayMedia(%s&ia=1)"
                        % (sysurl),
                    )
                )
            if ia and not_library_and_not_downloaded:
                cm.append(
                    (
                        "Nie odtwarzaj przez IA",
                        "PlayMedia(%s&ia=0)"
                        % (sysurl),
                    )
                )

            item = control.item(label=label, offscreen=True)  # create ListItem

            item.addContextMenuItems(cm)  # dodanie menu kontekstowego do pozycji

            item.setArt({"icon": thumb, "thumb": thumb, "poster": poster, "banner": banner})
            # if meta.get("mediatype") == "tvshow":  # nie zawsze działa np. nie działa dla źródeł odcinka
            if "tvshowtitle" in meta and "season" in meta and "episode" in meta:
                item.setArt({"season.poster": poster})

            # item.setProperty("Fanart_Image", fanart)

            vtag = item.getVideoInfoTag()

            castwiththumb = meta.get("castwiththumb")
            if castwiththumb:
                castwiththumb = [xbmc.Actor(**a) for a in castwiththumb]
                vtag.setCast(castwiththumb)

            # vtag.addVideoStream(xbmc.VideoStreamDetail(codec="h264"))  # czy to potrzebne ? przecież nie każdy plik ma taki kodek

            # nie wiem do czego to było
            # meta.pop("imdb", None)
            # meta.pop("tmdb_id", None)
            # meta.pop("imdb_id", None)
            # meta.pop("poster", None)
            # meta.pop("clearlogo", None)
            # meta.pop("clearart", None)
            # meta.pop("fanart", None)
            # meta.pop("fanart2", None)
            # meta.pop("imdb", None)
            # meta.pop("tmdb", None)
            # meta.pop("metacache", None)
            # meta.pop("poster2", None)
            # meta.pop("poster3", None)
            # meta.pop("banner", None)
            # meta.pop("next", None)
            
            if meta:
                infoLabels = control.metadataClean(meta)
            else:
                infoLabels = {}

            infoLabels.update({"OriginalTitle": originalname or title})  # oryginalny zamiast angielskiego tłumaczenia
            infoLabels.update({"title": label})  # musi być, gdy chcemy sortować w jakikolwiek sposób
            # infoLabels.update({"sorttitle": label})  # do przetestowania
            infoLabels.update({"count": i})  # potrzebne do powrotu do pierwotnej kolejności
            infoLabels.update({"size": source_utils.convert_size_to_bytes(items[i].get("size", ""))})
            infoLabels.update({"country": items[i].get("language", "")})

            duration_item = items[i].get("duration")
            # duration_meta = meta.get("duration")
            # fflog(f'{duration_item=} {duration_meta=}')
            if duration_item:
                infoLabels.update({"duration": str(duration_item)})

            item.setInfo(type="Video", infoLabels=infoLabels)

            if generate_short_path:
                item.setProperty("source", json.dumps([items[i]]))
                item.setProperty("meta", json.dumps(meta))
                # item.setProperty("mediatype", meta.get("mediatype",""))
                # item.setProperty("url", items[i].get("url"))
                pass

            # if control.setting("player.dont_use_setResolvedUrl") != "true":
            if not dont_use_setResolvedUrl:
                item.setProperty('IsPlayable', 'true')  # ważne, gdy używamy metody xbmcplugin.setResolvedUrl (ma nadzieję, że nie powinno przeszkadzać, gdy używamy xbmc.Player().play)
            
            #control.addItem(handle=syshandle, url=sysurl, listitem=item, isFolder=False)  # dodanie pojedynczego elementu przez Kodi do wirualnego folderu
            list_of_items.append((sysurl, item, False,))  # dodanie elementu do listy, aby poźniej Kodi dodał je zbiorczo (lepsza wydajność w przypadku większej ilości pozyji)

            providers.append(items[i]["provider"])  # później do sprawdzenia, jakie wystąpiły (do wyjątku)

            if auto_select_next_item_to_play:
                list_of_sources.append(dict(items[i], label=label))

        control.addItems(syshandle, list_of_items)  # dodanie zbiorcze

        # if control.setting("auto.select.next.item.to.play") == "true":
        if auto_select_next_item_to_play:
            control.window.setProperty("plugin.video.fanfilm.container.list_of_sources", json.dumps(list_of_sources))
            pass

        #control.content(syshandle, "videos")  # nie za bardzo się sprawdza, skórki nie mają chyba tego dobrze zaimplementowanego, poza tym, to raczej zarezerwowane dla różnych wideo, a tu są wszystkie takie same
        control.content(syshandle, "files")

        #if name != "odrzucone" and json.loads(control.window.getProperty(self.itemRejected)):
        if not trash and json.loads(control.window.getProperty(self.itemRejected)):
            #name = "odrzucone"
            trash = True  # potrzebne niżej jako znacznik
            label = "[I]Zobacz odrzucone źródła (przez filtry)[/I]"
            item = control.item(label, offscreen=True)
            infoLabels = {}
            #infoLabels.update({"Title": label})  # musi być, gdy chcemy sortować w jakikolwiek sposób Uwaga: Title zarezerwowałem (patrz default.py)
            #infoLabels.update({"OriginalTitle": title})  # przekazuje parametr "title" do rekurencyjnego wywołania funkcji showItems (choć uniwersalniej byłoby wybrać item.setProperty)
            item.setProperty('title', title)
            infoLabels.update({"count": 1999})  # potrzebne do powrotu do pierwotnej kolejności
            item.setInfo("Video", infoLabels)
            icon = control.addonNext()
            addonFanart = control.addonFanart()
            addonLandscape = control.addonLandscape()
            item.setArt({"icon": icon, "thumb": icon, "poster": icon, "banner": icon, "fanart": addonFanart, "landscape": addonLandscape})
            if not control.setting("generate_short_path") == "true":
                sysurl = f"{sysaddon}?action=showItems&title={systitle}&trash=1"
            else:
                sysurl = f"{sysaddon}?action=showItems&trash=1"
            if "tvshowtitle" in meta and "season" in meta and "episode" in meta:
                sysurl += "&season=%s&episode=%s" % (season, episode)
            control.addItem(syshandle, sysurl, item, isFolder=True)


        # xbmcplugin.addSortMethod(syshandle, xbmcplugin.SORT_METHOD_UNSORTED)  # pokazuje napis "Domyślny", ale nie sortuje
        control.sortMethod(syshandle, xbmcplugin.SORT_METHOD_PLAYLIST_ORDER)
        control.sortMethod(syshandle, xbmcplugin.SORT_METHOD_SIZE)
        control.sortMethod(syshandle, xbmcplugin.SORT_METHOD_COUNTRY)
        control.sortMethod(syshandle, xbmcplugin.SORT_METHOD_LASTPLAYED)
        control.sortMethod(syshandle, xbmcplugin.SORT_METHOD_PLAYCOUNT)
        # xbmcplugin.addSortMethod(syshandle, xbmcplugin.SORT_METHOD_BITRATE)  # to podobnie jak rozmiar - Kodi jakoś to sobie sam przelicza
        
        cacheToDisc = False  # mam większą kontrolę wówczas
        if control.setting("crefresh") != "true":  # można zrobić wyjątek
            pr_with_biblio = ['tb7', 'xt7', 'rapideo', 'nopremium', 'twojlimit']
            if not any(pr in pb for pr in providers for pb in pr_with_biblio):  # dla niektórych
                cacheToDisc = True  # tylko, że True czasami blokuje wymuszenie odświeżenia, gdy potrzeba, bo Kodi wczytuje sobie z cache i nie wiem, jak to zmienić (np. z Ulubionych przechodząc dalej)
        # fflog(f'{cacheToDisc=}')
        #if name:
        if trash:
            cacheToDisc = True

        # updateListing = False
        # params = dict(parse_qsl(sys.argv[2].replace("?", "")))
        params = dict(parse_qsl(sys.argv[2][1:]))
        # updateListing = False if params.get("trash") or params.get("item") else True  # True może świadczyć, że po drodze było odświeżanie
        updateListing = True if params.get("r") else False  # True świadczy, że po drodze było odświeżanie
        if updateListing:
            cacheToDisc = True  # nie wiem czy to potrzebne
            pass

        control.directory(syshandle, cacheToDisc=cacheToDisc, updateListing=updateListing)  # zamknięcie folderu
        fflog(f'[showItems] koniec wypisywania pozycji w katalogu', 0)

        views.setView("files")  # wymuszenie widoku (na w zależności od ustawień wtyczki)


    # def playItem(self, title, source, meta=None, **kwargs):
    def playItem(self, title="", source=None, meta=None, imdb=None, tmdb=None, season=None, episode=None, **kwargs):
        if not source:
            fflog(f'Błąd - brak ważnej zmiennej {source=}')
            control.dialog.notification('FanFilm', 'błąd: brak zmiennej "source"', xbmcgui.NOTIFICATION_ERROR)
            return
        
        fflog("sprawdzanie linku do odtwarzania")
        #xbmcgui.Dialog().notification('', ('sprawdzam link ...'), sound=False)
        control.dialog.notification('', ('sprawdzam link ...'), sound=False)

        #try:
        if not meta:
            meta = control.window.getProperty(self.metaProperty)
            if meta:
                meta = json.loads(meta)
                if tmdb or imdb:
                    if not(imdb == meta.get("imdb", "") or tmdb == meta.get("tmdb", "")):
                        meta = {}
            if not meta and (tmdb or imdb):
                try:
                    if not episode:
                        fflog(f'próba pobrania metadanych z bazy dla filmu')
                        meta = cache.cache_get("superinfo" + f"_{tmdb or imdb}")
                        if not meta:
                            fflog('potrzeba pobrania informacji o filmie przez super_info.py')
                            from resources.lib.indexers.super_info import SuperInfo
                            media_list = [{'tmdb': tmdb, 'imdb': imdb}]
                            import requests
                            session = requests.Session()
                            lang = control.apiLanguage()["tmdb"]
                            super_info_obj = SuperInfo(media_list, session, lang)
                            super_info_obj.get_info(0)
                            meta = cache.cache_get("superinfo" + f"_{tmdb or imdb}")
                    else:
                        fflog(f'próba pobrania metadanych z bazy dla odcinka')
                        if season or season == 0:
                            meta = cache.cache_get("episodes" + f"_{tmdb or imdb}_s{season}")
                        else:
                            meta = cache.cache_get("episodes" + f"_{tmdb or imdb}")
                        if not meta:
                            fflog("trzeba pobrać dane odcinka z serwisu z internetu")
                            from resources.lib.indexers import episodes
                            meta = episodes.episodes().tmdb_list(imdb=imdb, tmdb=tmdb, season=season)
                            # meta = repr(meta)
                        else:
                            #from ast import literal_eval
                            fflog(f'dane odcinka powinny być w bazie cache')
                            #meta = meta["value"]
                            #meta = literal_eval(meta)
                    if meta:
                        if "value" in meta:
                            meta = meta["value"]
                            meta = literal_eval(meta)
                    else:
                        meta = {}
                except Exception:
                    meta = {}
                    fflog_exc(1)
            else:
                meta = {}
        else:
            if isinstance(meta, str):
                meta = json.loads(meta)

        if not title:
            title = meta.get("title", "")

        year = meta["year"] if "year" in meta else None

        if not season:
            season = meta["season"] if "season" in meta else None
        if not episode:
            episode = meta["episode"] if "episode" in meta else None

        imdb = meta["imdb"] if "imdb" in meta else None
        tvdb = meta["tvdb"] if "tvdb" in meta else None  # to chyba w przypadku traktu jest wykorzystywane
        tmdb = meta["tmdb"] if "tmdb" in meta else None  # dziwne, ale niewykorzystywane tu
        # self.test = {'Nazwa': title, 'Rok': year, 'Sezon': season, 'Odcinek': episode}

        s = json.loads(source)[0]

        if s["source"] == "pobrane" or s["provider"] == "pobrane":
            from ptw.libraries.player import player
            player().run(title, year, season, episode, imdb, tvdb, tmdb, s["url"], meta=meta, hosting=s.get("source"))
            return

        if s["provider"] in ['tb7', 'xt7']:
            if not 'for_sourcesResolve' in kwargs:
                kwargs['for_sourcesResolve'] = {'for_resolve': {}}
            kwargs['for_sourcesResolve']['for_resolve'].update({'specific_source_data': s})

        if "for_resolve" in s:
            if not 'for_sourcesResolve' in kwargs:
                kwargs['for_sourcesResolve'] = {'for_resolve': {}}
            kwargs['for_sourcesResolve']['for_resolve'].update(s['for_resolve'])

        def _singleplay_playItem():
            if 'for_sourcesResolve' in kwargs:
                url = self.sourcesResolve(s, **kwargs['for_sourcesResolve'])
            else:
                url = self.sourcesResolve(s)
            
            if url:
                from ptw.libraries.player import player
                player().run(title, year, season, episode, imdb, tvdb, tmdb, url, meta=meta, hosting=s.get("source"))
            else:
                if url is not False:
                    c = 0
                    while control.condVisibility('Window.IsActive(notification)') and c < (5 * 2):
                        c += 1
                        control.sleep(200)
                    control.sleep(200)
                    # control.dialog.notification('', ('źródło nie działa'), xbmcgui.NOTIFICATION_WARNING)
                    control.infoDialog('źródło nie działa', '', "WARNING")
                    control.sleep(500)
                else:  # False coś miało oznaczać, nie pamiętam, może anulowanie przez użytkownika?
                    if control.condVisibility('Window.IsActive(notification)'):
                        control.execute('Dialog.Close(notification,true)')

        if control.setting("auto.select.next.item.to.play") != "true":
            _singleplay_playItem()
        else:
            # czy to ma tu sens? bo coś nie pobiera większej ilości pozycji z katalogu - zawsze jest tylko ta 1 wybrana enterem

            next = []
            prev = []
            total = []
            for i in range(1, 1000):
                try:
                    # następny od wybranego
                    u = control.infoLabel("ListItem(%s).FolderPath" % str(i))  # to teraz nie działa (przestało działać)
                    if u in total:
                        raise Exception()
                    total.append(u)
                    u = dict(parse_qsl(u.replace("?", "")))
                    u = json.loads(u["source"])[0]
                    next.append(u)
                except Exception:
                    # fflog_exc(1)
                    break
            for i in range(-1000, 0)[::-1]:
                try:
                    # poprzedni od wybranego
                    u = control.infoLabel("ListItem(%s).FolderPath" % str(i))
                    if u in total:
                        raise Exception()
                    total.append(u)
                    u = dict(parse_qsl(u.replace("?", "")))
                    u = json.loads(u["source"])[0]
                    prev.append(u)
                except Exception:
                    # fflog_exc(1)
                    break
            total = list(filter(None, total))  # usunięcie pustych
            # fflog(f'{total=}  {next=}  {prev=}')

            if not total:
                # fflog(f'{control.infoLabel("Container().CurrentItem")=}')
                # fflog(f'{control.infoLabel("Container().NumItems")=}')
                CurrentItem = int(control.infoLabel("Container().CurrentItem"))
                # NumItems = int(control.infoLabel("Container().NumItems"))
                # wczytanie z pamięci
                list_of_sources = control.window.getProperty("plugin.video.fanfilm.container.list_of_sources")
                list_of_sources = json.loads(list_of_sources)
                # fflog(f'{len(list_of_sources)=}')
                # fflog(f'{list_of_sources=}')
                # uzupełnienie reszty
                next = list_of_sources[CurrentItem:]
                prev = list_of_sources[:CurrentItem-1]
                # fflog(f'{len(next)=}  {len(prev)=}')
                # fflog(f'\n{next=} \n{prev=}')

            items = json.loads(source)  # wybrany
            # fflog(f'wybrany {len(items)=}')
            # fflog(f'wybrany {items=}')
            items[0].update({"label": control.infoLabel("ListItem.Label")})
            # fflog(f'{control.infoLabel("ListItem.Label")=}')
            # fflog(f'wybrany {items=}')

            items = [i for i in items + next + prev][:40]
            # fflog(f'{len(items)=}')
            # fflog(f'{items=}')


            if len(items) == 1:
                fflog(f'[playItem] {control.setting("auto.select.next.item.to.play")=} but {len(items)=} -> back to single play', 0)
                return _singleplay_playItem()

            header = control.addonInfo("name")
            header2 = header.upper()

            progressDialog = (
                control.progressDialog
                if control.setting("progress.dialog") == "0"
                else control.progressDialogBG
            )
            progressDialog.create(header, "")
            progressDialog.update(0)

            block = None
            monitor = control.monitor
            import threading

            fflog(f'auto play  {len(items)=}')
            # fflog(f'{json.dumps(items, indent=2)}')
            for i in range(len(items)):
                try:
                    # fflog(f'{i=}  {items[i].get("provider")=}  {items[i].get("source")=} ')
                    if items[i].get("source") == "pobrane" or items[i].get("provider") == "pobrane":
                        continue
                    else:
                        try:
                            if progressDialog.iscanceled():
                                break
                            if len(items) == 1:
                                label = control.infoLabel("ListItem.Label")
                                # fflog(f'{i=}  {label=} (pojedynczy)')
                            else:
                                label = items[i].get("label", items[i].get("filename", ""))
                                # fflog(f'{i=}  {label=}')
                            progressDialog.update(
                                int((100 / float(len(items))) * i),
                                str(label) + "\n" + str(" "),
                            )
                        except Exception:
                            fflog_exc(0)
                            progressDialog.update(
                                int((100 / float(len(items))) * i),
                                str(header2) + "\n" + str(label),
                            )

                        if items[i].get("source") == block:
                            raise Exception()
                        if 'for_sourcesResolve' in kwargs and i == 0:
                            w = threading.Thread(
                                target=self.sourcesResolve, args=(items[i],), kwargs=kwargs['for_sourcesResolve']
                            )
                        else:
                            w = threading.Thread(
                                target=self.sourcesResolve, args=(items[i],)
                            )
                        w.start()

                        offset = (
                            60 * 2
                            if items[i].get("source") in self.hostcapDict
                            else 0
                        )

                        m = ""

                        for x in range(3600):
                            try:
                                if monitor.abortRequested():
                                    return sys.exit()
                                if progressDialog.iscanceled():
                                    return progressDialog.close()
                            except Exception:
                                pass

                            k = control.condVisibility("Window.IsActive(virtualkeyboard)")
                            if k:
                                m += "1"
                                m = m[-1]
                            if (not w.is_alive() or x > 30 + offset) and not k:
                                break
                            k = control.condVisibility("Window.IsActive(yesnoDialog)")
                            if k:
                                m += "1"
                                m = m[-1]
                            if (not w.is_alive() or x > 30 + offset) and not k:
                                break
                            # time.sleep(1.5)
                            control.sleep(1500)

                        for x in range(30):
                            try:
                                if monitor.abortRequested():
                                    return sys.exit()
                                if progressDialog.iscanceled():
                                    return progressDialog.close()
                            except Exception:
                                pass

                            if m == "":
                                break
                            if not w.is_alive():
                                break
                            time.sleep(0.5)

                        if w.is_alive():
                            block = items[i].get("source")

                        if self.url is None:
                            # raise Exception(f'{self.url=}')
                            raise Exception()

                        try:
                            progressDialog.close()
                        except Exception:
                            pass

                        control.sleep(200)
                        control.execute("Dialog.Close(virtualkeyboard)")
                        control.execute("Dialog.Close(yesnoDialog)")

                        meta.update({"link1": items[i].get("url"), "link2": str(self.url)})  # do czego 2 linki?
                        
                        from ptw.libraries.player import player
                        player().run(title, year, season, episode, imdb, tvdb, tmdb, self.url, meta=meta, hosting=items[i].get("source"))

                        return self.url
                except Exception as e:
                    print(e)
                    if str(e):
                        self.errorForSources(str(e))                        
                    pass

            try:
                progressDialog.close()
            except Exception:
                pass

            self.errorForSources()  # to chyba jednak musi tu być
        """
        except Exception as e:
            print(e)
            if str(e):
                log(f'[playItem] {e!r}')
            xbmcgui.Dialog().notification('Problem', (f'Wystąpił jakiś błąd: \n{str(e)!r}'), xbmcgui.NOTIFICATION_ERROR)
            pass
        """


    def getSources(
            self,
            title,
            localtitle,
            year,
            imdb,
            tvdb,
            tmdb,
            season,
            episode,
            tvshowtitle,
            premiered,
            originalname='',
            quality="HD",
            timeout=30,
        ):



        progressDialog = (
            control.progressDialog
            if control.setting("progress.dialog") == "0"
            else control.progressDialogBG
        )

        progressDialog.create(control.addonInfo("name"), "")

        self.prepareSources()  # prepare database



        line2 = control.lang(32600)

        progressDialog.update(0, line2)


        language = self.getLanguage()
        # fflog(f'{language=}')

        if not self.sourceDict:
            self.getScrapers('', language)
        sourceDict = self.sourceDict
        # fflog(f'{len(sourceDict)=}')
        # fflog(f'{len(sourceDict)=}  {sourceDict=}', 1)

        # start sources reduction
        # wartość -1 oznacza wyłączenie, więc out
        sourceDict = [i for i in sourceDict if i[1].priority != -1]
        # fflog(f'{len(sourceDict)=}')

        content = "movie" if tvshowtitle is None else "episode"
        if content == "movie":
            sourceDict = [(i[0], i[1], getattr(i[1], "movie", None)) for i in sourceDict]
            genres = trakt.getGenre("movie", "imdb", imdb)
        else:
            sourceDict = [(i[0], i[1], getattr(i[1], "tvshow", None)) for i in sourceDict]
            genres = trakt.getGenre("show", "tvdb", tvdb)
        # fflog(f'{genres=}')
        # fflog(f'{len(sourceDict)=} {sourceDict=}')
        sourceDict = [
            (i[0], i[1], i[2])
            for i in sourceDict
            if (not hasattr(i[1], "genre_filter")
                or not i[1].genre_filter
                or any(x in i[1].genre_filter for x in genres))
        ]
        # fflog(f'{len(sourceDict)=} {sourceDict=}')
        sourceDict = [(i[0], i[1]) for i in sourceDict if not i[2] is None]
        # fflog(f'{len(sourceDict)=} {sourceDict=}')

        sourceDict = [(i[0], i[1], i[1].language) for i in sourceDict]
        # fflog(f'{len(sourceDict)=} {sourceDict=}')
        sourceDict = [(i[0], i[1]) for i in sourceDict if any(x in i[2] for x in language)]
        # fflog(f'{len(sourceDict)=} {sourceDict=}')

        try:
            sourceDict = [(i[0], i[1], control.setting("provider." + i[0])) for i in sourceDict]
        except Exception:
            fflog_exc(1)
            sourceDict = [(i[0], i[1], "true") for i in sourceDict]
        # fflog(f'{len(sourceDict)=} {sourceDict=}')
        
        sourceDict = [(i[0], i[1]) for i in sourceDict if not i[2] == "false"]
        # fflog(f'{len(sourceDict)=} {sourceDict=}')

        sourceDict = [(i[0], i[1], i[1].priority) for i in sourceDict]
        # fflog(f'{len(sourceDict)=} {sourceDict=}')

        random.shuffle(sourceDict)
        sourceDict = sorted(sourceDict, key=lambda i: i[2])

        fflog(f'{len(sourceDict)=} {sourceDict=}', 0)
        
        self.sourceDict = sourceDict


        threads = []
        import threading

        control.window.clearProperty("blocked_sources_extend")
        self.blocked_sources_extend = False

        if content == "movie":
            # title = self.getTitle(title)  # niszczy polskie znaki diakrytyczne
            # localtitle = self.getTitle(localtitle)  # niszczy polskie znaki diakrytyczne
            # originalname = self.getTitle(originalname)  # niszczy polskie znaki diakrytyczne
            aliases = self.getAliasTitles(imdb, localtitle, content)
            if originalname:
                aliases.append({"originalname": originalname, 'country': 'original' })
            for i in sourceDict:
                threads.append(
                    threading.Thread(
                        target=self.getMovieSource,
                        args=(title, localtitle, aliases, year, imdb, i[0], i[1], False),
                        kwargs={"premiered":premiered},
                    )
                )
        else:
            # tvshowtitle = self.getTitle(tvshowtitle)  # niszczy polskie znaki diakrytyczne
            localtvshowtitle = self.getLocalTitle(tvshowtitle, imdb, tvdb, content)
            aliases = self.getAliasTitles(imdb, localtvshowtitle, content)
            if originalname:
                aliases.append({"originalname": originalname, 'country': 'original' })            
            # Disabled on 11/11/17 due to hang. Should be checked in the future and possible enabled again.
            # season, episode = thexem.get_scene_episode_number(tvdb, season, episode)
            # import threading  # to jest już wyżej
            for i in sourceDict:
                threads.append(
                    threading.Thread(
                        target=self.getEpisodeSource,
                        args=(
                            title,
                            year,
                            imdb,
                            tvdb,
                            season,
                            episode,
                            tvshowtitle,
                            localtvshowtitle,
                            aliases,
                            premiered,
                            i[0],
                            i[1],
                        ),
                    )
                )

        s = [i[0] + (i[1],) for i in zip(sourceDict, threads)]
        s = [(i[3].getName(), i[0], i[2]) for i in s]

        mainsourceDict = [i[0] for i in s if i[2] == 0]
        sourcelabelDict = dict([(i[0], i[1].upper()) for i in s])

        [i.start() for i in threads]

        # string1 = control.lang(32404)  -- NOT USED
        # string2 = control.lang(32405)  -- NOT USED
        string3 = control.lang(32406)
        string4 = control.lang(32601)
        # string5 = control.lang(32602)  -- NOT USED
        string6 = control.lang(32606)
        string7 = control.lang(32607)

        try:
            timeout = int(control.setting("scrapers.timeout.1"))
            #timeout = 3  # test
        except Exception:
            pass

        quality = control.setting("hosts.quality")
        if quality == "":
            quality = "0"
        qmax = int(quality)
        qmin = int(control.setting("hosts.quality.min"))
        #quality = "3"
        #qmax = 3  # test
        #qmin = 3  # test

        line1 = line2 = line3 = ""
        # debrid_only = control.setting("debrid.only")  -- NOT USED

        pre_emp = str(control.setting("preemptive.termination")) == 'true'
        pre_emp_limit = int(control.setting("preemptive.limit"))
        #pre_emp = True  # test
        #pre_emp_limit = 2  # test

        source_4k = d_source_4k = 0
        source_1440 = d_source_1440 = 0
        source_1080 = d_source_1080 = 0
        source_720 = d_source_720 = 0
        source_sd = d_source_sd = 0
        total = d_total = 0

        debrid_list = debrid.debrid_resolvers
        debrid_status = debrid.status()

        total_format = "[COLOR %s][B]%s[/B][/COLOR]"
        
        pdiag_tot_format = " %s: %s "
        pdiag_format = " 4K: %s | 2k: %s | FullHD: %s | HD: %s | SD: %s ".split("|")
        if debrid_status:
            pdiag_format = " 4K: %s | 1080p: %s | 720p: %s | SD: %s | %s: %s".split("|")
        
        pdiag_bg_tot_format = "T:%s(%s)"
        pdiag_bg_format = "4K:%s(%s)|2k:%s(%s)|FullHD:%s(%s)|HD:%s(%s)|SD:%s(%s)".split("|")
        if debrid_status:
            pdiag_bg_format = "4K:%s(%s)|1080p:%s(%s)|720p:%s(%s)|SD:%s(%s)|T:%s(%s)".split("|")

        monitor = control.monitor

        for i in range(0, 4 * timeout):
        
            if pre_emp:
                if (
                    source_4k
                    + d_source_4k
                    + source_1440
                    + d_source_1440
                    + source_1080
                    + d_source_1080
                    + source_720
                    + d_source_720
                    + source_sd
                    + d_source_sd
                ) >= pre_emp_limit:
                    line2 = f'Osiągnięto założony limit źródeł'
                    percent = int(100 * float(i) / (2 * timeout) + 0.5)
                    progressDialog.update(max(1, percent), line1 + "\n[B]" + line2 + "[/B]")
                    log(f'[getSources] {line2} ({pre_emp_limit})')
                    break

            try:
                if monitor.abortRequested():
                    return sys.exit()

                try:
                    if progressDialog.iscanceled():
                        break
                except Exception:
                    pass

                if len(self.sources) > 0:
                    #if quality in ["0"]:
                    if True:
                        source_4k = len(
                            [
                                e
                                for e in self.sources
                                if e["quality"] == "4K" and not e["debridonly"]
                            ]
                        ) if qmax == 0 else 0
                        source_1440 = len(
                            [
                                e
                                for e in self.sources
                                if e["quality"] in ["1440p"] and not e["debridonly"]
                            ]
                        ) if qmax <= 1 and qmin >=1 else 0
                        source_1080 = len(
                            [
                                e
                                for e in self.sources
                                if e["quality"] in ["1080p", "1080i"] and not e["debridonly"]
                            ]
                        ) if qmax <= 2 and qmin >=2 else 0
                        source_720 = len(
                            [
                                e
                                for e in self.sources
                                if e["quality"] in ["720p", "HD"] and not e["debridonly"]
                            ]
                        ) if qmax <= 3 and qmin >=3 else 0
                        source_sd = len(
                            [
                                e
                                for e in self.sources
                                if e["quality"] == "SD" and not e["debridonly"]
                            ]
                        ) if qmax <= 4 and qmin >=4 else 0
                    """
                    elif quality in ["1"]:
                        source_1080 = len(
                            [
                                e
                                for e in self.sources
                                if e["quality"] in ["1440p", "1080p", "1080i"] and not e["debridonly"]
                            ]
                        )
                        source_720 = len(
                            [
                                e
                                for e in self.sources
                                if e["quality"] in ["720p", "HD"] and not e["debridonly"]
                            ]
                        )
                        source_sd = len(
                            [
                                e
                                for e in self.sources
                                if e["quality"] == "SD" and not e["debridonly"]
                            ]
                        )
                    elif quality in ["2"]:
                        source_1080 = len(
                            [
                                e
                                for e in self.sources
                                if e["quality"] in ["1080p", "1080i"] and not e["debridonly"]
                            ]
                        )
                        source_720 = len(
                            [
                                e
                                for e in self.sources
                                if e["quality"] in ["720p", "HD"] and not e["debridonly"]
                            ]
                        )
                        source_sd = len(
                            [
                                e
                                for e in self.sources
                                if e["quality"] == "SD" and not e["debridonly"]
                            ]
                        )
                    elif quality in ["3"]:
                        source_720 = len(
                            [
                                e
                                for e in self.sources
                                if e["quality"] in ["720p", "HD"] and not e["debridonly"]
                            ]
                        )
                        source_sd = len(
                            [
                                e
                                for e in self.sources
                                if e["quality"] == "SD" and not e["debridonly"]
                            ]
                        )
                    else:
                        source_sd = len(
                            [
                                e
                                for e in self.sources
                                if e["quality"] == "SD" and not e["debridonly"]
                            ]
                        )
                    """
                    total = source_4k + source_1440 + source_1080 + source_720 + source_sd
                    
                    if debrid_status:
                        if quality in ["0"]:
                            for d in debrid_list:
                                d_source_4k = len(
                                    [
                                        e
                                        for e in self.sources
                                        if e["quality"] == "4K" and d.valid_url("", e["source"])
                                    ]
                                )
                                d_source_1080 = len(
                                    [
                                        e
                                        for e in self.sources
                                        if e["quality"] in ["1440p", "1080p", "1080i"] and d.valid_url("", e["source"])
                                    ]
                                )
                                d_source_720 = len(
                                    [
                                        e
                                        for e in self.sources
                                        if e["quality"] in ["720p", "HD"] and d.valid_url("", e["source"])
                                    ]
                                )
                                d_source_sd = len(
                                    [
                                        e
                                        for e in self.sources
                                        if e["quality"] == "SD" and d.valid_url("", e["source"])
                                    ]
                                )
                        elif quality in ["1"]:
                            for d in debrid_list:
                                d_source_1080 = len(
                                    [
                                        e
                                        for e in self.sources
                                        if e["quality"] in ["1440p", "1080p", "1080i"] and d.valid_url("", e["source"])
                                    ]
                                )
                                d_source_720 = len(
                                    [
                                        e
                                        for e in self.sources
                                        if e["quality"] in ["720p", "HD"] and d.valid_url("", e["source"])
                                    ]
                                )
                                d_source_sd = len(
                                    [
                                        e
                                        for e in self.sources
                                        if e["quality"] == "SD" and d.valid_url("", e["source"])
                                    ]
                                )
                        elif quality in ["2"]:
                            for d in debrid_list:
                                d_source_1080 = len(
                                    [
                                        e
                                        for e in self.sources
                                        if e["quality"] in ["1080p", "1080i"] and d.valid_url("", e["source"])
                                    ]
                                )
                                d_source_720 = len(
                                    [
                                        e
                                        for e in self.sources
                                        if e["quality"] in ["720p", "HD"] and d.valid_url("", e["source"])
                                    ]
                                )
                                d_source_sd = len(
                                    [
                                        e
                                        for e in self.sources
                                        if e["quality"] == "SD" and d.valid_url("", e["source"])
                                    ]
                                )
                        elif quality in ["3"]:
                            for d in debrid_list:
                                d_source_720 = len(
                                    [
                                        e
                                        for e in self.sources
                                        if e["quality"] in ["720p", "HD"] and d.valid_url("", e["source"])
                                    ]
                                )
                                d_source_sd = len(
                                    [
                                        e
                                        for e in self.sources
                                        if e["quality"] == "SD" and d.valid_url("", e["source"])
                                    ]
                                )
                        else:
                            for d in debrid_list:
                                d_source_sd = len(
                                    [
                                        e
                                        for e in self.sources
                                        if e["quality"] == "SD" and d.valid_url("", e["source"])
                                    ]
                                )

                        d_total = d_source_4k + d_source_1080 + d_source_720 + d_source_sd

                if debrid_status:
                    d_4k_label = (
                        total_format % ("red", d_source_4k)
                        if d_source_4k == 0
                        else total_format % ("lime", d_source_4k)
                    )
                    d_1080_label = (
                        total_format % ("red", d_source_1080)
                        if d_source_1080 == 0
                        else total_format % ("lime", d_source_1080)
                    )
                    d_720_label = (
                        total_format % ("red", d_source_720)
                        if d_source_720 == 0
                        else total_format % ("lime", d_source_720)
                    )
                    d_sd_label = (
                        total_format % ("red", d_source_sd)
                        if d_source_sd == 0
                        else total_format % ("lime", d_source_sd)
                    )
                    d_total_label = (
                        total_format % ("red", d_total)
                        if d_total == 0
                        else total_format % ("lime", d_total)
                    )

                source_4k_label = (
                    total_format % ("red", source_4k)
                    if source_4k == 0
                    else total_format % ("lime", source_4k)
                )
                source_1440_label = (
                    total_format % ("red", source_1440)
                    if source_1440 == 0
                    else total_format % ("lime", source_1440)
                )
                source_1080_label = (
                    total_format % ("red", source_1080)
                    if source_1080 == 0
                    else total_format % ("lime", source_1080)
                )
                source_720_label = (
                    total_format % ("red", source_720)
                    if source_720 == 0
                    else total_format % ("lime", source_720)
                )
                source_sd_label = (
                    total_format % ("red", source_sd)
                    if source_sd == 0
                    else total_format % ("lime", source_sd)
                )
                source_total_label = (
                    total_format % ("red", total)
                    if total == 0
                    else total_format % ("lime", total)
                )

                if (i / 2) < timeout:
                    try:
                        mainleft = [
                            sourcelabelDict[x.getName()]
                            for x in threads
                            if x.is_alive() and x.getName() in mainsourceDict
                        ]
                        info = [
                            sourcelabelDict[x.getName()]
                            for x in threads
                            if x.is_alive()
                        ]
                        """ # nie pamiętam po co to
                        if (
                                # i >= timeout
                                and len(mainleft) == 0
                                and len(self.sources) >= 100 * len(info)
                        ):
                            break  # improve responsiveness
                        """
                        if debrid_status:
                            if quality in ["0"]:
                                if not progressDialog == control.progressDialogBG:
                                    line1 = ("%s:" + "|".join(pdiag_format)) % (
                                        string6,
                                        d_4k_label,
                                        d_1080_label,
                                        d_720_label,
                                        d_sd_label,
                                        str(string4),
                                        d_total_label,
                                    )
                                    line2 = ("%s:" + "|".join(pdiag_format)) % (
                                        string7,
                                        source_4k_label,
                                        source_1080_label,
                                        source_720_label,
                                        source_sd_label,
                                        str(string4),
                                        source_total_label,
                                    )
                                    print(line1, line2)
                                else:
                                    line1 = "|".join(pdiag_bg_format[:-1]) % (
                                        source_4k_label,
                                        d_4k_label,
                                        source_1080_label,
                                        d_1080_label,
                                        source_720_label,
                                        d_720_label,
                                        source_sd_label,
                                        d_sd_label,
                                    )
                            elif quality in ["1"]:
                                if not progressDialog == control.progressDialogBG:
                                    line1 = ("%s:" + "|".join(pdiag_format[1:])) % (
                                        string6,
                                        d_1080_label,
                                        d_720_label,
                                        d_sd_label,
                                        str(string4),
                                        d_total_label,
                                    )
                                    line2 = ("%s:" + "|".join(pdiag_format[1:])) % (
                                        string7,
                                        source_1080_label,
                                        source_720_label,
                                        source_sd_label,
                                        str(string4),
                                        source_total_label,
                                    )
                                else:
                                    line1 = "|".join(pdiag_bg_format[1:]) % (
                                        source_1080_label,
                                        d_1080_label,
                                        source_720_label,
                                        d_720_label,
                                        source_sd_label,
                                        d_sd_label,
                                        source_total_label,
                                        d_total_label,
                                    )
                            elif quality in ["2"]:
                                if not progressDialog == control.progressDialogBG:
                                    line1 = ("%s:" + "|".join(pdiag_format[1:])) % (
                                        string6,
                                        d_1080_label,
                                        d_720_label,
                                        d_sd_label,
                                        str(string4),
                                        d_total_label,
                                    )
                                    line2 = ("%s:" + "|".join(pdiag_format[1:])) % (
                                        string7,
                                        source_1080_label,
                                        source_720_label,
                                        source_sd_label,
                                        str(string4),
                                        source_total_label,
                                    )
                                else:
                                    line1 = "|".join(pdiag_bg_format[1:]) % (
                                        source_1080_label,
                                        d_1080_label,
                                        source_720_label,
                                        d_720_label,
                                        source_sd_label,
                                        d_sd_label,
                                        source_total_label,
                                        d_total_label,
                                    )
                            elif quality in ["3"]:
                                if not progressDialog == control.progressDialogBG:
                                    line1 = ("%s:" + "|".join(pdiag_format[2:])) % (
                                        string6,
                                        d_720_label,
                                        d_sd_label,
                                        str(string4),
                                        d_total_label,
                                    )
                                    line2 = ("%s:" + "|".join(pdiag_format[2:])) % (
                                        string7,
                                        source_720_label,
                                        source_sd_label,
                                        str(string4),
                                        source_total_label,
                                    )
                                else:
                                    line1 = "|".join(pdiag_bg_format[2:]) % (
                                        source_720_label,
                                        d_720_label,
                                        source_sd_label,
                                        d_sd_label,
                                        source_total_label,
                                        d_total_label,
                                    )
                            else:
                                if not progressDialog == control.progressDialogBG:
                                    line1 = ("%s:" + "|".join(pdiag_format[3:])) % (
                                        string6,
                                        d_sd_label,
                                        str(string4),
                                        d_total_label,
                                    )
                                    line2 = ("%s:" + "|".join(pdiag_format[3:])) % (
                                        string7,
                                        source_sd_label,
                                        str(string4),
                                        source_total_label,
                                    )
                                else:
                                    line1 = "|".join(pdiag_bg_format[3:]) % (
                                        source_sd_label,
                                        d_sd_label,
                                        source_total_label,
                                        d_total_label,
                                    )
                        else:
                            #if quality in ["0"]:
                            if True:
                                line1 = "|".join(pdiag_format[qmax:qmin+1]) % (
                                    source_4k_label,
                                    source_1440_label,
                                    source_1080_label,
                                    source_720_label,
                                    source_sd_label,
                                    #str(string4),
                                    #source_total_label,
                                )[qmax:qmin+1]
                            """
                            elif quality in ["1"]:
                                line1 = "|".join(pdiag_format[1:]) % (
                                    source_1080_label,
                                    source_720_label,
                                    source_sd_label,
                                    str(string4),
                                    source_total_label,
                                )
                            elif quality in ["2"]:
                                line1 = "|".join(pdiag_format[1:]) % (
                                    source_1080_label,
                                    source_720_label,
                                    source_sd_label,
                                    str(string4),
                                    source_total_label,
                                )
                            elif quality in ["3"]:
                                line1 = "|".join(pdiag_format[2:]) % (
                                    source_720_label,
                                    source_sd_label,
                                    str(string4),
                                    source_total_label,
                                )
                            else:
                                line1 = "|".join(pdiag_format[3:]) % (
                                    source_sd_label,
                                    str(string4),
                                    source_total_label,
                                )
                            """
                            if pre_emp:
                                line1 += "\n" + (pdiag_tot_format) % ( str(string4), source_total_label)  # TOTAL
                            
                        if debrid_status:
                            if len(info) > 6:
                                line3 = string3 % (str(len(info)))
                            elif len(info) > 0:
                                line3 = string3 % (", ".join(info))
                            else:
                                break
                            percent = int(100 * float(i) / (2 * timeout) + 0.5)
                            if not progressDialog == control.progressDialogBG:
                                progressDialog.update(max(1, percent), line1 + "\n" + line2 + "\n" + line3)
                            else:
                                progressDialog.update(max(1, percent), line1 + "\n" + line3)
                        else:
                            if len(info) > 16:
                                line2 = string3 % (str(len(info)))
                            elif len(info) > 0:
                                line2 = string3 % (", ".join(info))
                            else:
                                #break
                                line2 = ""
                            percent = int(100 * float(i) / (2 * timeout) + 0.5)
                            progressDialog.update(max(1, percent), line1 + "\n" + line2)
                            if len(info) == 0:
                                break                            
                    except Exception as e:
                        print("Exception Raised: %s" % str(e), log_utils.LOGERROR)
                        log("Exception Raised: %s" % str(e), log_utils.LOGERROR)
                else:
                    log(f'[getSources] przerwanie wyszukiwania - przekroczenie ustalonego czasu ({int(i/2)} s.)')
                    try:
                        mainleft = [
                            sourcelabelDict[x.getName()]
                            for x in threads
                            if x.is_alive() and x.getName() in mainsourceDict
                        ]
                        info = mainleft
                        if debrid_status:
                            if len(info) > 6:
                                line3 = "Waiting for: %s" % (str(len(info)))
                            elif len(info) > 0:
                                line3 = "Waiting for: %s" % (", ".join(info))
                            else:
                                break
                            percent = int(100 * float(i) / (2 * timeout) + 0.5)
                            if not progressDialog == control.progressDialogBG:
                                progressDialog.update(max(1, percent), line1 + "\n" + line2 + "\n" + line3)
                            else:
                                progressDialog.update(max(1, percent), line1 + "\n" + line3)
                        else:
                            if len(info) > 6:
                                line2 = "Waiting for: %s" % (str(len(info)))
                            elif len(info) > 0:
                                line2 = "Waiting for: %s" % (", ".join(info))
                            else:
                                #break
                                line2 = 'Przerwanie wyszukiwania - przekroczenie czasu'
                            percent = int(100 * float(i) / (2 * timeout) + 0.5)
                            progressDialog.update(max(1, percent), line1 + "\n[B]" + line2 + "[/B]")
                            if len(info) == 0:
                                break
                    except Exception:
                        break

                time.sleep(0.5)  # potrzebne dla pętli for, aby prawidłowo odliczać czas

            except Exception:
                pass

        if line2:
        # if True:
            fflog(f'sygnał przerwania dalszej pracy scraperów')
            control.window.setProperty("blocked_sources_extend", "break")
            control.sleep(1000)

        # próba odzyskania choć części wyników dla wybranych serwisów, gdy minie czas
        # if int(i / 2) >= timeout  or  int(i / 2) > 10:
        if line2 and int(i / 2) > 20:
            # fflog(f'{s=}')
            ii = [s for s in sourceDict if s[0] in ['tb7', 'xt7'] and s[2]]  # s[2] to sprawdzenie, czy scraper włączony chyba
            # fflog(f'{len(ii)=} {ii=}')
            for i in ii:
                if not any(s for s in self.sources if s["provider"]==i[0]):  # sprawdzenie, czy nie ma w wynikach już jakiś źródeł od tb7 czy xt7
                    fflog(f'próba ewentualnego odzyskania wyników dla {i[0]}')
                    #xbmcgui.Dialog().notification('FanFilm', (f'Próba ewentualnego odzyskania wyników dla {i[0]}'), xbmcgui.NOTIFICATION_INFO, 1500, sound=False)
                    if content == "movie":
                        self.getMovieSource(title, localtitle, aliases, year, imdb, i[0], i[1], True)
                    else:
                        self.getEpisodeSource(title, year, imdb, tvdb, season, episode, tvshowtitle, localtvshowtitle, aliases, premiered, i[0], i[1], True)
                    # log(f'[getSources] zakończono ratunkowy odczyt źródeł dla {i[0]}')
                    #if xbmc.getCondVisibility('Window.IsActive(notification)'):
                        #xbmc.executebuiltin('Dialog.Close(notification,true)')
                        #pass

        self.blocked_sources_extend = True
        # self.sources = self.sortSources(self.sources)  # jakbym chciał, aby najpierw była biblioteka a potem pobrane
        self.sourcesFilter(year=year)  # filtrowanie wg różnych kryteriów

        if line2:
            control.sleep(1000-800)
        else:
            control.sleep(250)

        try:
            progressDialog.close()
            control.sleep0(100)
        except Exception:
            pass

        control.window.clearProperty('clear_SourceCache_for')

        return self.sources


    def prepareSources(self):
        control.window.setProperty(self.itemRejected, json.dumps([]))
        try:
            control.makeFile(control.dataPath)

            if control.setting("enableSourceCache") == "true":
                self.sourceFile = control.providercacheFile

                dbcon = database.connect(self.sourceFile)
                dbcur = dbcon.cursor()
                dbcur.execute(
                    "CREATE TABLE IF NOT EXISTS rel_url ("
                    "source TEXT, "
                    "imdb_id TEXT, "
                    "season TEXT, "
                    "episode TEXT, "
                    "rel_url TEXT, "
                    "UNIQUE(source, imdb_id, season, episode)"
                    ");"
                )
                dbcur.execute(
                    "CREATE TABLE IF NOT EXISTS rel_src ("
                    "source TEXT, "
                    "imdb_id TEXT, "
                    "season TEXT, "
                    "episode TEXT, "
                    "hosts TEXT, "
                    "added TEXT, "
                    "UNIQUE(source, imdb_id, season, episode)"
                    ");"
                )

        except Exception:
            pass
        finally:
            if "dbcon" in locals():
                dbcon.close()


    def getMovieSource(self, title, localtitle, aliases, year, imdb, source, call, from_cache=False, **kwargs):
        try:
            dbcon = database.connect(self.sourceFile)
            dbcur = dbcon.cursor()
        except Exception:
            pass

        # jak ktoś używa cache źródeł, to aby dla plików "wypożyczonych" na innych urządzeniach zawsze sprawdzał
        control.window.setProperty('clear_SourceCache_for', control.window.getProperty('clear_SourceCache_for') + ',tb7,xt7,rapideo,nopremium,twojlimit')
        # chyba, ża dać jakiś krótki czas, np. tylko 5 minut (lub mniej, np. 1-2 minuty)

        """ Fix to stop items passed with a 0 IMDB id pulling old unrelated sources from the database. """
        cSCf = control.window.getProperty('clear_SourceCache_for').strip(',').split(',')
        if imdb == "0" or source in cSCf or "all" in cSCf:
            # wyczyszczenie cache dla danego źródła
            try:
                dbcur.execute(
                    "DELETE FROM rel_src WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'"
                    % (source, imdb, "", "")
                )
                dbcur.execute(
                    "DELETE FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'"
                    % (source, imdb, "", "")
                )
                dbcon.commit()
            except Exception:
                pass
        """ END """

        sources = []
        try:
            dbcur.execute(
                "SELECT * FROM rel_src WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'"
                % (source, imdb, "", "")
            )
            match = dbcur.fetchone()
            t1 = int(re.sub("[^0-9]", "", str(match[5])))
            t2 = int(datetime.datetime.now().strftime("%Y%m%d%H%M"))
            t1 = datetime.datetime.strptime(str(t1), "%Y%m%d%H%M").timestamp()
            t2 = datetime.datetime.strptime(str(t2), "%Y%m%d%H%M").timestamp()
            cache_timeout = int(control.setting("SourceCache_timeout"))
            # fflog(f'{cache_timeout=}')
            # expire_time = 30 if source not in ['tb7','xt7','rapideo','nopremium','twojlimit'] else 5  # albo mniej jeszcze
            update = int((t2-t1)/60) > cache_timeout
            if not update:
                fflog(f'pobranie źródeł z cache  {source=}')
                sources = eval(match[4].encode("utf-8"))
                if sources:
                    dbcon.close()
                    if not self.blocked_sources_extend:
                        self.sources.extend(sources)
                    else:
                        fflog(f'{self.blocked_sources_extend=}')
                        pass
                    return
                else:
                    fflog(f'brak źródeł w cache  {source=}')
        except Exception:
            pass

        url = None
        try:
            dbcur.execute(
                "SELECT * FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'"
                % (source, imdb, "", "")
            )
            url = dbcur.fetchone()
            url = eval(url[4].encode("utf-8"))
        except Exception:
            pass

        try:
            if not url and not from_cache:
                if source in ["shinden"]:
                    # fflog(f'{source=} {kwargs=}')
                    url = call.movie(imdb, title, localtitle, aliases, year, **kwargs)
                else:
                    url = call.movie(imdb, title, localtitle, aliases, year)
            if not url and from_cache:
                results_cache = cache.cache_get(f'{source}_results')
                if results_cache and results_cache['value']:  # może w ogóle nie być
                    results_cache = literal_eval(results_cache['value'])
                    if results_cache:  # może być pusty
                        url = [results_cache[k] for k in results_cache][0]
                        fflog(f'dla {source} odczytano z cache rekordów: {len(url)}')
        except Exception as e:
            #if str(e):
                #fflog(f'Error: {e}')
            log_exception(1)

        try:
            if not url:
                raise Exception()
            dbcur.execute(
                "DELETE FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'"
                % (source, imdb, "", "")
            )
            dbcur.execute(
                "INSERT INTO rel_url Values (?, ?, ?, ?, ?)",
                (source, imdb, "", "", repr(url)),
            )
            dbcon.commit()
        except Exception:
            pass

        try:
            if from_cache:
                sources = call.sources(url, self.hostDict, self.hostprDict, from_cache=from_cache)            
            else:
                sources = call.sources(url, self.hostDict, self.hostprDict)
        except Exception:
            log_exception(1)

        try:
            if not sources:
                raise Exception()

            sources = [json.loads(t) for t in set(json.dumps(d, sort_keys=True) for d in sources)]
            for i in sources:
                provider = i.get("provider") or ""
                if provider:
                    if provider[0] == " ":
                        provider = source + provider
                else:
                    provider = source
                i.update({"provider": provider})
            if not self.blocked_sources_extend:
                self.sources.extend(sources)
            else:
                fflog(f'{self.blocked_sources_extend=}')
                pass

            dbcur.execute(
                "DELETE FROM rel_src WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'"
                % (source, imdb, "", "")
            )
            dbcur.execute(
                "INSERT INTO rel_src Values (?, ?, ?, ?, ?, ?)",
                (
                    source,
                    imdb,
                    "",
                    "",
                    repr(sources),
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                ),
            )
            dbcon.commit()
        except Exception:
            pass

        if "dbcon" in locals():
            dbcon.close()


    def getEpisodeSource(
            self,
            title,
            year,
            imdb,
            tvdb,
            season,
            episode,
            tvshowtitle,
            localtvshowtitle,
            aliases,
            premiered,
            source,
            call,
            from_cache=False
    ):
        try:
            dbcon = database.connect(self.sourceFile)
            dbcur = dbcon.cursor()
        except Exception:
            pass

        # jak ktoś używa cache źródeł, to aby dla plików "wypożyczonych" na innych urządzeniach zawsze sprawdzał
        control.window.setProperty('clear_SourceCache_for', control.window.getProperty('clear_SourceCache_for') + ',tb7,xt7,rapideo,nopremium,twojlimit')
        # chyba, ża dać jakiś krótki czas, np. tylko 5 minut (lub mniej, np. 1-2 minuty)

        """ Clear if needed """
        cSCf = control.window.getProperty('clear_SourceCache_for').strip(',').split(',')
        if source in cSCf or "all" in cSCf:
            try:
                dbcur.execute(
                    "DELETE FROM rel_src WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'"
                    % (source, imdb, "", "")
                )
                dbcur.execute(
                    "DELETE FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'"
                    % (source, imdb, "", "")
                )
                dbcon.commit()
            except Exception:
                pass
        """ END """

        try:
            sources = []
            dbcur.execute(
                "SELECT * FROM rel_src WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'"
                % (source, imdb, season, episode)
            )
            match = dbcur.fetchone()
            t1 = int(re.sub("[^0-9]", "", str(match[5])))
            t2 = int(datetime.datetime.now().strftime("%Y%m%d%H%M"))
            t1 = datetime.datetime.strptime(str(t1), "%Y%m%d%H%M").timestamp()
            t2 = datetime.datetime.strptime(str(t2), "%Y%m%d%H%M").timestamp()
            cache_timeout = int(control.setting("SourceCache_timeout"))
            # fflog(f'{cache_timeout=}')
            # expire_time = 30 if source not in ['tb7','xt7','rapideo','nopremium','twojlimit'] else 5  # albo mniej jeszcze
            update = int((t2-t1)/60) > cache_timeout
            if not update:
                fflog(f'pobranie źródeł z cache  {source=}')
                sources = eval(match[4].encode("utf-8"))
                if sources:
                    dbcon.close()
                    if not self.blocked_sources_extend:
                        self.sources.extend(sources)
                    else:
                        fflog(f'{self.blocked_sources_extend=}')
                        pass
                    return
                else:
                    fflog(f'brak źródeł w cache  {source=}')
        except Exception:
            pass

        url = None
        try:
            dbcur.execute(
                "SELECT * FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'"
                % (source, imdb, "", "")
            )
            url = dbcur.fetchone()
            url = eval(url[4].encode("utf-8"))
        except Exception:
            pass

        try:
            if not url:
                url = call.tvshow(imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year)
        except Exception:
            log_exception(1)

        try:
            if not url:
                raise Exception()
            dbcur.execute(
                "DELETE FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'"
                % (source, imdb, "", "")
            )
            dbcur.execute(
                "INSERT INTO rel_url Values (?, ?, ?, ?, ?)",
                (source, imdb, "", "", repr(url)),
            )
            dbcon.commit()
        except Exception:
            pass

        ep_url = None
        try:
            dbcur.execute(
                "SELECT * FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'"
                % (source, imdb, season, episode)
            )
            ep_url = dbcur.fetchone()
            ep_url = eval(ep_url[4].encode("utf-8"))
        except Exception:
            pass

        try:
            if not ep_url and not from_cache and url:
                ep_url = call.episode(url, imdb, tvdb, title, premiered, season, episode)
            if not ep_url and from_cache:
                results_cache = cache.cache_get(f'{source}_results')
                if results_cache and results_cache['value']:  # może w ogóle nie być
                    results_cache = literal_eval(results_cache['value'])
                    if results_cache:  # może być pusty
                        ep_url = [results_cache[k] for k in results_cache][0]
                        fflog(f'dla {source} odczytano z cache rekordów: {len(ep_url)}')
        except Exception:
            log_exception(1)

        try:
            if not ep_url:
                raise Exception()
            dbcur.execute(
                "DELETE FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'"
                % (source, imdb, season, episode)
            )
            dbcur.execute(
                "INSERT INTO rel_url Values (?, ?, ?, ?, ?)",
                (source, imdb, season, episode, repr(ep_url)),
            )
            dbcon.commit()
        except Exception:
            pass

        sources = []
        try:
            if from_cache:
                sources = call.sources(ep_url, self.hostDict, self.hostprDict, from_cache=from_cache)
            else:
                sources = call.sources(ep_url, self.hostDict, self.hostprDict)
        except Exception:
            log_exception(1)

        try:
            if not sources:
                raise Exception()

            sources = [json.loads(t) for t in set(json.dumps(d, sort_keys=True) for d in sources)]
            for i in sources:
                provider = i.get("provider") or ""
                if provider:
                    if provider[0] == " ":
                        provider = source + provider
                else:
                    provider = source
                i.update({"provider": provider})
            if not self.blocked_sources_extend:
                self.sources.extend(sources)
            else:
                fflog(f'{self.blocked_sources_extend=}')
                pass

            dbcur.execute(
                "DELETE FROM rel_src WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'"
                % (source, imdb, season, episode)
            )
            dbcur.execute(
                "INSERT INTO rel_src Values (?, ?, ?, ?, ?, ?)",
                (
                    source,
                    imdb,
                    season,
                    episode,
                    repr(sources),
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                ),
            )
            dbcon.commit()
        except Exception:
            pass

        if "dbcon" in locals():
            dbcon.close()


    def alterSources(self, url, meta=None):
        try:
            # log(f"{url=!r}")
            # log(f"{meta=!r}")
            # log(f"{sys.argv=!r}")

            if isinstance(url, str):
                url = url.split("?")
                q = dict(parse_qsl(url[-1]))
                # log(f"{q=!r}")
            else:
                q = url

            # aby nie pojawiały się drugi raz pytania
            # poprzedni url
            folderpath = control.infoLabel('Container.FolderPath')
            params1 = dict(parse_qsl(folderpath.split('?')[-1]))
            action1 = params1.get('action')
            # bieżący url
            params2 = dict(parse_qsl(sys.argv[2][1:]))
            action2 = params2.get('action')
            # jak polecenia były te same, to traktujemy to jako odświeżenie widoku
            referer = folderpath if action1 != action2 else ''
            fflog(f"{referer=} , bo {folderpath=} {action1=} {action2=}", 0)
            if not referer:  # odświeżenie
                # q.pop('customTitles', '')
                q.update({"customTitles": 0})
                pass

            if "customTitles" in q and q["customTitles"]:
                if (p := q.get('tvshowtitle')) and p != "None":
                    # seriale
                    if (s := xbmcgui.Dialog().input("Główny tytuł serialu [CR][LIGHT](anglojęzyczny lub oryginalny)[/LIGHT]", p)):
                        q.update({"tvshowtitle": s})
                    else:
                        return sys.exit()

                    if (p := q.get('season')) and p != "None":
                        while True:
                            s = xbmcgui.Dialog().input("Numer sezonu \n(maks 2 cyfry)", "", type=xbmcgui.INPUT_NUMERIC)
                            if s == "0" or s == "00":
                                s = "1"
                                break
                            if not s or re.match(r"^[\d]{1,2}$", s):
                                break
                            if not xbmcgui.Dialog().yesno('Niepoprawna wartość', (f"Wartość [B]{s}[/B] jest nieprawidłowa. \nCzy chcesz poprawić?")):
                                s = ''
                                break
                        if s:
                            q.update({"season": s})

                    if (p := q.get('episode')) and p != "None":
                        while True:
                            s = xbmcgui.Dialog().input("Numer odcinka \n(maks. 4 cyfry)", "", type=xbmcgui.INPUT_NUMERIC)
                            if s == "0" or s == "00" or s == "000" or s == "0000":
                                s = "1"
                                break
                            if not s or re.match(r"^[\d]{1,4}$", s):
                                break
                            if not xbmcgui.Dialog().yesno('Niepoprawna wartość', (f"Wartość [B]{s}[/B] jest nieprawidłowa. \nCzy chcesz poprawić?")):
                                s = ''
                                break
                        if s:
                            q.update({"episode": s})

                    if (p := q.get('year')) and p != "None":
                        while True:
                            s = xbmcgui.Dialog().input("Rok premiery", p, type=xbmcgui.INPUT_NUMERIC)
                            if not s or re.match(r"^(19|20)[\d]{2,2}$", s):
                                break
                            if not xbmcgui.Dialog().yesno('Niepoprawna wartość', (f"Wpisana wartość [B]{s}[/B] jest nieprawidłowa. \nCzy chcesz poprawić? \n[COLOR gray]dozwolony zakres to [1900-2099][/COLOR]")):
                                s = ''
                                break
                        if s:
                            q.update({"year": s})
                            q.update({"premiered": ""})  # bo źródła premium mogą odrzucić jak w nazwie będzie rok kolejnego sezonu inny niż rok premiery

                    xbmcgui.Dialog().notification(f"s{q.get('season').zfill(2)}e{q.get('episode').zfill(2)}", (f"{q.get('tvshowtitle')} ({q.get('year')})"))
                else:
                    # filmy
                    if (p := q.get('title')) and p != "None":
                        if (s := xbmcgui.Dialog().input("Główny tytuł [CR][LIGHT](anglojęzyczny lub oryginalny)[/LIGHT]", p)):
                            q.update({"title": s})
                        else:
                            return sys.exit()

                    if (p := q.get('localtitle')) and p != "None":
                        if (s := xbmcgui.Dialog().input("polskie tłumaczenie tytułu", p)):
                            q.update({"localtitle": s})

                    if (p := q.get('year')) and p != "None":
                        while True:
                            s = xbmcgui.Dialog().input("Rok premiery", p, type=xbmcgui.INPUT_NUMERIC)
                            if not s or re.match(r"^(19|20)[\d]{2,2}$", s):
                                break
                            if not xbmcgui.Dialog().yesno('Niepoprawna wartość', (f"Wpisana wartość [B]{s}[/B] jest nieprawidłowa. \nCzy chcesz poprawić? \n[COLOR gray]dozwolony zakres to [1900-2099][/COLOR]")):
                                s = ''
                                break
                        if s:
                            q.update({"year": s})

                    xbmcgui.Dialog().notification(f"{q.get('year')}", (f"{q.get('title')} \n{q.get('localtitle')}"))

            elif "customTitles" in q and not q["customTitles"]:  # np. gdy nie zadawał pytań
                q.update({"select": "1"})
                pass

            else:
                # nie rozumiem tego
                if control.setting("hosts.mode") == "2":  # autoplay
                    #url += "&select=1"
                    q.update({"select": "1"})  # directory
                else:
                    #url += "&select=2"
                    q.update({"select": "2"})  # autoplay

            q.pop('action', None)  # musi być ewentualnie "play"

            #self.play(**q)  # ale może niektórych zmiennych brakować
            #return

            """
            xbmcgui.Dialog().notification('', (f'czekaj ...'))
            url = url[0] + "?" + urlencode(q)
            control.execute("RunPlugin(%s)" % url + "&handle="+meta)  # gubi "handle"
            control.execute("Container.Update(%s)" % url)  # czemuś nie działa - nie wyszukuje źródeł
            control.directory(addon_handle, cacheToDisc=True)  # może tego brakowało? sprawdzić
            return
            """

            title = q.get('title')
            localtitle = q.get('localtitle')
            year = q.get('year')
            imdb = q.get('imdb')
            tvdb = q.get('tvdb')
            tmdb = q.get('tmdb')
            season = q.get('season')
            episode = q.get('episode')
            tvshowtitle = q.get('tvshowtitle')
            premiered = q.get('premiered')
            meta = q.get('meta') if meta is None else meta
            select = q.get('select')
            customTitles = q.get('customTitles', '')  # aby nie zadawał pytań ponownie
            originalname = q.get("originalname", "")
            epimdb = q.get("epimdb", "")
            # log(f'{title=!r} \n{localtitle=!r} \n{year=!r} \n{imdb=!r} \n{tvdb=!r} \n{tmdb=!r} \n{season=!r} \n{episode=!r} \n{tvshowtitle=!r} \n{premiered=!r} \n{meta=!r} \n{select=!r} ')
            if control.setting("generate_short_path") == "true":
                zmienne = { "title":title, "localtitle":localtitle, "year":year, "imdb":imdb, "tvdb":tvdb, "tmdb":tmdb,
                            "season":season, "episode":episode, "tvshowtitle":tvshowtitle, "premiered":premiered,
                            "meta":meta, "select":select,
                            "originalname":originalname, "epimdb":epimdb,
                            "customTitles":customTitles,
                            }
                control.window.setProperty('FanFilm.var.curr_item_p', repr(zmienne))  # do pamięci
                self.play(**zmienne)
            else:
                self.play(title, localtitle, year, imdb, tvdb, tmdb, season, episode, tvshowtitle, premiered, meta, select, customTitles=customTitles)
                # self.play(title, localtitle, year, imdb, tvdb, tmdb, season, episode, tvshowtitle, premiered, meta, select, customTitles=customTitles, originalname=originalname, epimdb=epimdb)
                # może jednak to włączyć?
        except Exception:
            fflog_exc(1)
            pass


    def clearSources(self):
        try:
            #
            yes = control.yesnoDialog(control.lang(32407))
            if not yes:
                return

            control.makeFile(control.dataPath)
            dbcon = database.connect(control.providercacheFile)
            dbcur = dbcon.cursor()
            dbcur.execute("DROP TABLE IF EXISTS rel_src")
            dbcur.execute("DROP TABLE IF EXISTS rel_url")
            dbcur.execute("VACUUM")
            dbcon.commit()

            control.infoDialog(control.lang(32408), sound=True, icon="INFO")
        except Exception:
            pass


    def sortSources(self, sources, silent=False):

        # muszą być wszystkie pozycje, które zwraca source_utils.check_sd_url() i które zostały "zassane" przez zmienną filtered
        #my_quality_order = ["4K", "1440p", "1080p", "1080i", "720p", "SD", "SCR", "CAM"]
        my_quality_order = ["4K", "2160p", "2K", "1440p", "1080p", "1080i", "720p", "HD", "SD", "480p", "360p", "SCR", "CAM"]
        quality_order = {key: i for i, key in enumerate(my_quality_order)}
        
        # muszą być wszystkie możliwości wypisane jakie chcemy obsługiwać
        my_language_order = ["pl", "mul", "multi", "en", "de", "fr", "it", "es", "pt", "ko", "ru", "ja", '-', '']
        language_order = {key: i for i, key in enumerate(my_language_order)}
        
        # ustalenie kolejności dla nazw serwisów
        my_provider_order = ["1", "2", "3", "4", "5", "6", "cdapremium", "ekinotv premium", "nopremium", "rapideo", "twojlimit", "tb7", "xt7", "0", ""]
        provider_order = {key: i for i, key in enumerate(my_provider_order)}

        # wybór wariantu sortowania
        sort_source = control.setting("hosts.sort")
        sort_source = str(sort_source)
        if sort_source == "0":  # by providers
            silent or fflog("Sortuję wg dostawców")
            try:
                sources = sorted(
                    sources,
                    key=lambda d: (
                        not d["provider"].startswith("library"),
                        not d["provider"].startswith("biblioteka"),
                        not d["provider"].startswith("plex"),
                        not d["provider"].startswith("pobrane"),
                        not d["provider"].startswith("external"),
                        not d["on_account"] if "on_account" in d else 1,
                        # not d["provider"].startswith("cdapremium"),
                        # not d["provider"].startswith("nopremium"),
                        # not d["provider"].startswith("rapideo") if not control.setting("rapideo.sort.order") else True,
                        # not d["provider"].startswith("tb7") if not control.setting("tb7.sort.order") else True,
                        # not d["provider"].startswith("twojlimit"),
                        # not d["provider"].startswith("xt7"),
                        provider_order[(control.setting(d["provider"]+".sort.order") if control.setting(d["provider"]+".sort.order") and control.setting(d["provider"]+".sort.order") != "0" else d["provider"] if d["provider"] in my_provider_order else "")],
                        language_order.get(d["language"]),
                        quality_order.get(d["quality"]),
                        d["provider"],  # provider (serwis internetowy www)
                        source_utils.convert_size_to_bytes( d["size"] if "size" in d  else  d["info"].rsplit('|')[-1] if "info" in d and d["info"]  else '')*-1,
                    ),
                )
            except Exception:
                fflog_exc(1)
                fflog(f'sources={json.dumps(sources, indent=2)}', 0)
                pass

        if sort_source == "1":  # by sources (hosting, server)
            silent or fflog("Sortuję wg źródeł (hostingów)")
            try:
                sources = sorted(
                    sources,
                    key=lambda d: (
                        not d["provider"].startswith("library"),
                        not d["provider"].startswith("biblioteka"),
                        not d["provider"].startswith("plex"),
                        not d["provider"].startswith("pobrane"),
                        not d["provider"].startswith("external"),
                        not d["on_account"] if "on_account" in d else 1,
                        # not d["provider"].startswith("cdapremium"),
                        # not d["provider"].startswith("nopremium"),
                        # not d["provider"].startswith("rapideo"),
                        # not d["provider"].startswith("tb7"),
                        # not d["provider"].startswith("twojlimit"),
                        # not d["provider"].startswith("xt7"),
                        provider_order[(control.setting(d["provider"]+".sort.order") if control.setting(d["provider"]+".sort.order") and control.setting(d["provider"]+".sort.order") != "0" else d["provider"] if d["provider"] in my_provider_order else "")],
                        language_order.get(d["language"]),
                        quality_order.get(d["quality"]),
                        d["source"],  # source (serwer, hosting)
                        source_utils.convert_size_to_bytes( d["size"] if "size" in d  else  d["info"].rsplit('|')[-1] if "info" in d and d["info"]  else '')*-1,
                    ),
                )
            except Exception:
                fflog_exc(1)
                fflog(f'sources={json.dumps(sources, indent=2)}', 0)
                pass

        if sort_source == "2":  # by size
            silent or fflog("Sortuję wg rozmiaru")
            try:
                sources = sorted(
                    sources,
                    key=lambda d: (
                        not d["provider"].startswith("library"),
                        not d["provider"].startswith("biblioteka"),
                        not d["provider"].startswith("plex"),
                        not d["provider"].startswith("pobrane"),
                        not d["provider"].startswith("external"),
                        not d["on_account"] if "on_account" in d else 1,
                        provider_order[(control.setting(d["provider"]+".sort.order") if control.setting(d["provider"]+".sort.order") and control.setting(d["provider"]+".sort.order") != "0" else d["provider"] if d["provider"] in my_provider_order else "")],
                        # language_order.get(d["language"]),
                        # quality_order.get(d["quality"]),
                        # d["provider"],  # provider (serwis internetowy www)
                        # d["source"],  # source (serwer, hosting)
                        source_utils.convert_size_to_bytes( d["size"] if "size" in d  else  d["info"].rsplit('|')[-1] if "info" in d and d["info"]  else '')*-1,
                    ),
                )
            except Exception:
                fflog_exc(1)
                fflog(f'sources={json.dumps(sources, indent=2)}', 0)
                pass

        if sort_source == "3":
            custom_criterion = (control.setting("hosts.sort.elem1"), control.setting("hosts.sort.elem2"), control.setting("hosts.sort.elem3"), control.setting("hosts.sort.elem4"))
            silent or fflog(f'Sortuję wg ustawień użytkownika: {" -> ".join(custom_criterion)}')
            # funkcja pomocnicza
            def choose_criterium(d,x):
                crit = control.setting(f"hosts.sort.elem{x}")
                return (
                    provider_order[(control.setting(d["provider"]+".sort.order") if control.setting(d["provider"]+".sort.order") and control.setting(d["provider"]+".sort.order") != "0" else d["provider"] if d["provider"] in my_provider_order else "")] if(crit.lower() in ("serwis", "provider"))
                    else language_order.get(d["language"]) if(crit.lower() in ("język", "language"))
                    else quality_order.get(d["quality"]) if(crit.lower() in ("jakość", "quality"))
                    else source_utils.convert_size_to_bytes( d["size"] if "size" in d  else  d["info"].rsplit('|')[-1] if "info" in d and d["info"]  else '')*-1  if(crit.lower() in ("rozmiar", "size"))
                    else ''
                )
            # sortowanie
            try:
                sources = sorted(
                    sources,
                    key=lambda d: (
                        # zawsze na początku
                        not d["provider"].startswith("library"),
                        not d["provider"].startswith("biblioteka"),
                        not d["provider"].startswith("plex"),
                        not d["provider"].startswith("pobrane"),
                        not d["provider"].startswith("external"),
                        # czy na koncie online
                        not d["on_account"] if "on_account" in d else True,
                        # kryteria użytkownika
                        choose_criterium(d,0),  # 1 kryterium
                        choose_criterium(d,1),  # 2 kryterium
                        choose_criterium(d,2),  # 3 kryterium
                        choose_criterium(d,3),  # 4 kryterium
                    ),
                )
            except Exception:
                fflog_exc(1)
                fflog(f'sources={json.dumps(sources, indent=2)}', 0)
                pass

        return sources


    def sourcesFilter(self, **kwargs):
        fflog('Filtrowanie')
        # fflog(f'{kwargs=}')

        if control.setting("filter.duplicates") == "true":
            self.sources = self.filter_duplicates()  # usunięcie duplikatów
            pass

        debrid_only = control.setting("debrid.only")
        if debrid_only == "":
            debrid_only = "false"
        
        quality = control.setting("hosts.quality")
        if quality == "":
            quality = "0"
        #quality = "1"  # test
        # qmax = int(quality)  # niewykorzystywany
        qmin = int(control.setting("hosts.quality.min"))
        #qmin = 1  # test

        captcha = control.setting("hosts.captcha")
        if captcha == "":
            captcha = "true"

        numbering = ""
        numbering = control.setting("sources.numbering")
        if numbering == "":
            numbering = "true"
        numbering = False if numbering != "true" else True


        # ograniczenie maksymalnej ilości źródeł
        self.sources = self.sources[:1998]


        # random.shuffle(self.sources)  # po co to ?

        # [ s.update({"language": l.lower()})  for s in self.sources  if (l := s.get("language")) ]  # zmiana kodu języka na małe litery (nie wiem, czy potrzeba)

        sources_before_filtered = (self.sources).copy()  # kopia


        # coś z plikami lokalnymi (biblioteka Kodi może?)
        local = [i for i in self.sources if "local" in i and i["local"]]
        for i in local:
            i.update({"language": self._getPrimaryLang() or "en"})  # aktualizacja języka dla plików lokalnych

        # oddzielenie internetowych od lokalnych
        self.sources = [i for i in self.sources if i not in local]  # tylko internetowe


        # na początek listy źródła z linkami bezpośrednimi, czyli takimi, których nie trzeba dodatkowo wyszukiwać przez resolvera
        filtered = []
        filtered += [i for i in self.sources if i["direct"]]
        filtered += [i for i in self.sources if not i["direct"]]
        self.sources = filtered


        # coś ze źródłami debrid
        filtered = []
        for d in debrid.debrid_resolvers:
            valid_hoster = set([i["source"] for i in self.sources])
            valid_hoster = [i for i in valid_hoster if d.valid_url("", i)]
            filtered += [
                dict(list(i.items()) + [("debrid", d.name)])
                for i in self.sources
                if i["source"] in valid_hoster
            ]
        if debrid_only == "false" or not debrid.status():
            filtered += [
                i
                for i in self.sources
                if not i["source"].lower() in self.hostprDict and not i["debridonly"]
            ]
        self.sources = filtered


        # kilkanaście linijek poniżej, to sprawdzanie jakości
        for i in self.sources:
            if "checkquality" in i and i["checkquality"]:
                if not i["source"].lower() in self.hosthqDict and i["quality"] not in ["SD", "SCR", "CAM"]:
                    i.update({"quality": "SD"})

        # ewentualne korekty oznaczeń jakości na stosowane tu przy przetwarzaniu
        for i in range(len(self.sources)):
            q = self.sources[i]["quality"]
            if q and (q[-1]=="P" or q[-1]=="I"):
                q = q.lower()
                self.sources[i].update({"quality": q})
            if q == "HD":
                self.sources[i].update({"quality": "720p"})
            elif q == "2K":
                self.sources[i].update({"quality": "1440p"})
            elif q == "2160p":
                self.sources[i].update({"quality": "4K"})
            elif q == "480p" or q == "360p":
                self.sources[i].update({"quality": "SD"})


        filtered = []
        filtered += local
        sources_before_filtered_quality = (self.sources).copy()

        if quality in ["0"]:
            filtered += [i for i in self.sources if i["quality"] == "4K" and "debrid" in i]
        if quality in ["0"]:
            filtered += [i for i in self.sources if i["quality"] == "4K" and "debrid" not in i and "memberonly" in i]
        if quality in ["0"]:
            filtered += [i for i in self.sources if i["quality"] == "4K" and "debrid" not in i and "memberonly" not in i]

        if quality in ["0", "1"]:
            filtered += [i for i in self.sources if i["quality"] == "1440p" and "debrid" in i]
        if quality in ["0", "1"] and qmin >= 1:
            filtered += [i for i in self.sources if i["quality"] == "1440p" and "debrid" not in i and "memberonly" in i]
        if quality in ["0", "1"] and qmin >= 1:
            filtered += [i for i in self.sources if i["quality"] == "1440p" and "debrid" not in i and "memberonly" not in i]

        if quality in ["0", "1", "2"]:
            filtered += [i for i in self.sources if (i["quality"] == "1080p" or i["quality"] == "1080i") and "debrid" in i]
        if quality in ["0", "1", "2"] and qmin >= 2:
            filtered += [i for i in self.sources if (i["quality"] == "1080p" or i["quality"] == "1080i") and "debrid" not in i and "memberonly" in i]
        if quality in ["0", "1", "2"] and qmin >= 2:
            filtered += [i for i in self.sources if (i["quality"] == "1080p" or i["quality"] == "1080i") and "debrid" not in i and "memberonly" not in i]

        if quality in ["0", "1", "2", "3"]:
            filtered += [i for i in self.sources if i["quality"] == "720p" and "debrid" in i]
        if quality in ["0", "1", "2", "3"] and qmin >= 3:
            filtered += [i for i in self.sources if i["quality"] == "720p" and "debrid" not in i and "memberonly" in i]
        if quality in ["0", "1", "2", "3"] and qmin >= 3:
            filtered += [i for i in self.sources if i["quality"] == "720p" and "debrid" not in i and "memberonly" not in i]

        #CAM_disallowed = control.setting("CAM.disallowed")  # później to filtruje
        CAM_disallowed = False
        if qmin >= 4:
            if CAM_disallowed == "true":
                filtered += [i for i in self.sources if i["quality"] in ["SD", "SCR"]]  # czy HDTS też zaliczać jako CAM ?
            else:
                filtered += [i for i in self.sources if i["quality"] in ["SD", "SCR", "CAM"]]

        self.sources = filtered

        # aby móc potem zaznaczyć dlaczego poszło out
        for s in sources_before_filtered:
            if s in sources_before_filtered_quality:
                if s not in self.sources:
                    s["trash"] = s.get("quality")
        sources_before_filtered_quality = None

        # coś z captcha
        if not captcha == "true":
            filtered = [i for i in self.sources if i["source"].lower() in self.hostcapDict and "debrid" not in i]
            self.sources = [i for i in self.sources if i not in filtered]

        # coś z domenami, które chyba są z jakiegoś powodu wykluczone
        filtered = [i for i in self.sources if i["source"].lower() in self.hostblockDict and "debrid" not in i]
        self.sources = [i for i in self.sources if i not in filtered]

        # chyba angielskie źródła na koniec listy
        multi = [i["language"] for i in self.sources]
        multi = [x for y, x in enumerate(multi) if x not in multi[:y]]
        multi = True if len(multi) > 1 else False
        if multi:
            self.sources = [i for i in self.sources if not i["language"] == "en"] + [i for i in self.sources if i["language"] == "en"]


        EXTS = ("avi", "mkv", "mp4", ".ts", "mpg", "mov", "vob", "mts", "2ts")  # dozwolone rozszerzenia filmów ("2ts" to od "m2ts", ale tylko 3 znakowe rozszerzenie do tablicy ze względu na kompatybilność starszego kodu)
        extrainfo = control.setting("sources.extrainfo") == "true"
        filename_in_2nd_line = control.setting("sources.filename_in_2nd_line")
        remove_verticals_on_list = control.setting("sources.remove_verticals_on_list") == "true"
        fix_for_scroll_long_text_with_second_line = control.setting("fix_for_scroll_long_text_with_second_line") == "true"
        url2 = ""

        def _makeLabel(source, offset=None):
            url2 = ""
            if extrainfo:
                try:
                    if "filename" in source and source["filename"]:
                        url2 = source["filename"]
                    else:
                        url2 = source["url"].replace(' / ', ' ').replace('_/_', '_').rstrip("/").split("/")[-1]
                        url2 = url2.rstrip("\\").split("\\")[-1]  # dla plików z własnej biblioteki na dysku lokalnym
                        # fflog(f' {[i]} {url2=}')
                        url2 = re.sub(r"(\.(html?|php))+$", "", url2, flags=re.I)  # na przypadki typu "filmik.mkv.htm"
                        if url2.lower()[-3:] not in EXTS:
                            # próba pozyskanie nazwy z 2-giej linijki lub opisu
                            #if "info2" in source and source["info2"] and source["info2"].lower()[-3:] in EXTS:
                            # if source.get("info2", "").lower()[-3:] in EXTS:  # czasami są opisy "kamerdyner-cam-2018-pl"
                            if source.get("info2"):
                                url2 = source["info2"]
                            else:
                                """
                                # to raczej nie będzie już wykorzystywane, bo okazało się, że info może mieć juz swoje oznaczenia, więc mogą się dublować
                                url2 = source["info"] if source["info"] else ''
                                # próba odfiltrowania nazwy
                                url2 = url2.split("|")[-1].strip().lstrip("(").rstrip(")")
                                """
                                url2 = ""
                    # fflog(f' {[i]} {url2=}')
                    url2 = unquote(url2)  # zamiana takich tworów jak %nn (np. %21 to nawias)
                    url2 = unescape(url2)  # pozbycie się encji html-owych
                    # fflog(f' {url2=}')
                    if "year" in kwargs:
                        url3 = url2.partition( kwargs["year"] )[-1]
                        if not url3:
                            url3 = url2.partition( str(int(kwargs["year"])-1) )[-1]
                        url3 = url3 if url3 else url2
                    else:
                        url3 = url2
                    # fflog(f' {url3=}')
                    t = PTN.parse(url3)  # proces rozpoznawania
                    # fflog(f' {t=}')

                    t3d = t["3d"] if "3d" in t else ''  # zapamiętanie informacji pod inną zmienną czy wersja 3D
                    textended = t["extended"] if "extended" in t else ''  # informacja o wersji rozszerzonej
                    tremastered = t["remastered"] if "remastered" in t else ''  # informacja o wersji zremasterowanej

                    # poniżej korekty wizualne
                    if "audio" in t:
                        t["audio"] = re.sub(r"(?<!\d)([57]\.[124](?:\.[24])?)\.(ATMOS)\b", r"\1 \2", t["audio"], flags=re.I)
                        t["audio"] = re.sub(r"(?<=[DSPXAC3M])[.-]?([57261]\.[102])\b", r" \1", t["audio"], flags=re.I)
                        t["audio"] = re.sub(r"\b(DTS)[.-]?(HD|ES|EX|X(?!26))[. ]?(MA)?", r"\1-\2 \3", t["audio"], flags=re.I).rstrip()
                        t["audio"] = re.sub(r"(TRUEHD|DDP)\.(ATMOS)\b", r"\1 \2", t["audio"], flags=re.I)
                        t["audio"] = re.sub(r"(custom|dual)\.(audio)", r"\1 \2", t["audio"], flags=re.I)
                        t["audio"] = re.sub("ddp(?!l)", "DD+", t["audio"], flags=re.I)
                    if "codec" in t:
                        t["codec"] = re.sub(r"(\d{2,3})(fps)", r"\1 \2", t["codec"], flags=re.I)
                        t["codec"] = re.sub("plus", "+", t["codec"], flags=re.I)  # z myślą o HDR10Plus -> HDR10+
                        t["codec"] = re.sub(r"\bDoVi\b", "DV", t["codec"], flags=re.I)
                        if "DolbyVision".lower() in t["codec"].lower():  # DolbyVision -> DV
                            if "DV".lower() in t["codec"].lower():
                                t["codec"] = re.sub(r"\s*/\s*DolbyVision", "", t["codec"], flags=re.I)
                            else:
                                t["codec"] = re.sub("DolbyVision", "DV", t["codec"], flags=re.I)
                    if "quality" in t:
                        t["quality"] = re.sub(r"\b(\w+)\.(\w+)\b", r"\1-\2", t["quality"], flags=re.I)

                    t = [t[j] for j in t if "quality" in j or "codec" in j or "audio" in j]
                    t = " | ".join(t)
                    """
                    if not t:
                        log(f'fallback dla PTN.parse {url2=}')
                        t = source_utils.getFileType(url2)  # taki fallback dla PTN.parse()
                        t = t.strip()
                        log(f' {t=}')
                    """
                    """
                    # pozbycie się tych samych oznaczeń ze zmiennej info
                    if t:
                        source["info"] = re.sub(fr'(\b|[ ._|/]+)({"|".join(t.split(" / "))})\b', '', (source.get("info") or ""), flags=re.I)
                    """
                    
                    # dodanie dodatkowych informacji (moim zdaniem ważnych)
                    if t3d:
                        if "3d" in url2.lower() and "3d" not in t.lower():
                            t = f"[3D] | {t}"
                        else:
                            t = t.replace("3D", "[3D]")

                    # dodatkowe oznaczenie pliku z wieloma sciezkami audio
                    if ( re.search(r"\bMULTI\b", url2, re.I)  # szukam w adresie, który powinien zawierać nazwę pliku
                         and "mul" not in source["language"].lower()
                         # and "PL" not in source["language"].upper()  # założenie, że jak wykryto język PL, to nie ma potrzeby o dodatkowym ozaczeniu
                         and "multi" not in (source.get("info") or "").lower()  # sprawdzenie, czy przypadkiem już nie zostało przekazane przez plik źródła
                         and "multi" not in t.lower()  # sprawdzenie, czy nie ma tej frazy już w opisie
                       ):
                        t += " | MULTI"

                    if ("multi" in t.lower() or "multi" in (source.get("info") or "").lower()) and source["language"] != "pl":
                        source["language"] = "multi"  # wymiana języka
                        t = re.sub(r'[/| ]*multi\b', '' , t, flags=re.I)  # wywalenie z opisu, aby nie było dubli
                        source["info"] = re.sub(r'[/| ]*multi\b', '' , (source.get("info") or ""), flags=re.I)  # wywalenie z opisu, aby nie było dubli

                    if textended:
                        if textended is True:
                            t += " | EXTENDED"
                        else:
                            textended = re.sub("(directors|alternat(?:iv)?e).(cut)", r"\1 \2", textended, flags=re.I)
                            t += f" | {textended}"

                    # długi napis i czy aż tak istotny?
                    if tremastered:
                        if tremastered is True:
                            t += " | REMASTERED"
                        else:
                            if "rekonstrukcja" not in t.lower():
                                tremastered = re.sub("(Rekonstrukcja).(cyfrowa)", r"\1 \2", tremastered, flags=re.I)
                                t += f" | {tremastered}"

                    if "imax" in url2.lower() and "imax" not in t.lower():  # sprawdzenie czy dodać info IMAX
                        t += " | [IMAX]"

                    if "avi" in url2.lower()[-3:] and "avi" not in t.lower():  # aby nie bylo zdublowań
                        t += " | AVI"  # oznaczenie tego typu pliku, bo nie zawsze dobrze odtwarza sie "w locie"

                    t = t.lstrip(" | ")  # przydaje się, jak ani PTN.parse() ani getFileType() nic nie znalazły
                    t += " " if t else ""
                    # t = t.strip()
                    # fflog(f'{t=}')

                except Exception:
                    fflog_exc(1)
                    t = None
            else:
                t = None
            #log(f' {t=} {url2=}')

            # u = source["url"]  -- NOT USED

            p = source["provider"]  # serwis internetowy, strona www

            lng = source["language"]

            s = source["source"]  # hosting (serwer hostujący źródło)
            source["source"] = source["source"].replace("*", "").replace("~", "")  # w tb7/xt7 dodaje * jak nie wiadomo jaki serwer konkretnie (dotyczy plików z bilbioteki)

            q = source["quality"]  # rozdzielczość pionowa

            s = s.rsplit(".", 1)[0]  # wyrzucenie ostatniego człona domeny (np. ".pl", ".com")

            if p.lower() == "library":
                if control.setting("api.language") == "Polish":
                    p = "biblioteka"

            try:  # f to info (tu może być też rozmiar pliku na końcu)
                f = " | ".join(
                    [
                        "[I]%s [/I]" % info.strip()  # ta spacja chyba jest ważna
                        for info in source["info"].split("|")
                    ]
                )
            except Exception:
                f = ""

            try:
                d = source["debrid"]
            except Exception:
                d = source["debrid"] = ""

            if d.lower() == "real-debrid":
                d = "RD"

            # tworzenie LABELa
            if not d == "":  # debrid
                if numbering:
                    #label = "%02d | [B]%s | %s[/B] | " % (int(i + 1 + offset), d, p)
                    label = "{} |[B]%s[/B]| %s | " % (d, p)
                else:
                    label = "[B]%s[/B] | %s | " % (d, p)
            else:
                if numbering:
                    #label = "[LIGHT]%02d[/LIGHT] | [LIGHT][B]%s[/B][/LIGHT] | " % (int(i + 1 + offset), p)
                    label = "[LIGHT]{}[/LIGHT] |%s| " % (p)
                else:
                    label = "%s | " % (p)

            if source.get("on_account") and numbering:
                #label = re.sub(r'(\d{2,})', r'[I]\1[/I]', label, 1)
                label = re.sub(r'(\{\})', r'[I]\1[/I]', label, 1)
                pass

            if numbering and offset is not None:
                label = label.format("%02d" % (i + 1 + offset))

                    
            # oznaczenie języka
            if lng:
                if (
                    multi and lng != "en"  # nie rozumiem, kiedy ten warunek zachodzi
                    or not multi and lng != "en"  # dałem ten warunek
                   ):
                    if extrainfo:
                        label += "[B]%s[/B] | " % lng
                    else:
                        f = ("[B]%s[/B] | " % lng) + f  # inny wariant
                r"""
                else:
                    if "mul" in lng or re.search(r"\bMULTI\b", t, re.I):
                        label += "[B]multi[/B] | "
                        # usunięcie z opisu, aby nie było zdublowań
                        if re.search(r"\bMULTI\b", t, re.I):
                            t = re.sub(r"\s*\bMULTI\b(\s[/|])?", "", t, flags=re.I)
                            t = re.sub(r"(\s[/|])(?=\s*$)", "", t, flags=re.I)
                """                


            # oznaczenie, czy źródło jest w tzw. bibliotece danego serwisu
            if "on_account" in source and source["on_account"]:
                if source.get("on_account_expires"):
                    label += f'[I][LIGHT]konto[/LIGHT] ({source["on_account_expires"]})[/I] | '
                else:
                    label += '[I]konto[/I] | '


            trash = source.get("trash")

            if t:  # extrainfo
                source["extrainfo"] = t  # potrzebne do downloadera
                if remove_verticals_on_list:
                    t = t.replace(" |", ",")
                    t = f"({t.strip()})"
                if q in ["4K", "1440p", "1080p", "1080i", "720p"] or trash == q:
                    label += "%s |[B][I]%s[/I][/B] |[I]%s[/I]| %s" % (s, q, t, f)
                elif q == "SD":
                    # label += "%s | %s | [I]%s[/I]" % (s, f, t)
                    # moja propozycja (wielkość pliku na końcu - dla spójności)
                    label += "%s |[I]%s[/I]| %s" % (s, t, f)
                else:
                    # label += "%s | %s | [I]%s [/I] | [I]%s[/I]" % (s, f, q, t)
                    # moja propozycja (wielkość pliku na końcu - dla spójności)
                    # label += "[LIGHT]%s | [B][I]%s [/I][/B] | [I]%s[/I] | %s[/LIGHT]" % (s, q, t, f)
                    label += "[LIGHT]%s |[I]%s[/I]| %s[/LIGHT]" % (s, t, f)
            else:
                if q in ["4K", "1440p", "1080p", "1080i", "720p"] or trash == q:
                    label += "%s |[B][I]%s[/I][/B] | %s" % (s, q, f)
                elif q == "SD":
                    label += "%s | %s" % (s, f)
                else:
                    # label += "%s | %s | [I]%s [/I]" % (s, f, q)
                    # moja propozycja (wielkość pliku na końcu - dla spójności)
                    # label += "[LIGHT]%s | [B][I]%s [/I][/B] | %s[/LIGHT]" % (s, q, f)
                    label += "[LIGHT]%s | %s[/LIGHT]" % (s, f)

            # korekty wizualne
            label = label.replace("| 0 |", "|").replace(" | [I]0 [/I]", "")
            label = re.sub(r"\[I\]\s+\[/I\]", " ", label)
            label = re.sub(r"\|\s+\|", "|", label)
            label = re.sub(r"\|\s+\|", "|", label)  # w pewnych okolicznościach ponowne wykonanie takiej samej linijki kodu jak wyżej pomaga
            label = re.sub(r"\|(?:\s+|)$", "", label)
            label = re.sub(r"\[I\](\d+(?:[.,]\d+)?\s*[GMK]B) ?\[/I\]", r"[B]\1[/B]", label, flags=re.I)  # wyróżnienie rozmiaru pliku
            label = re.sub(r"(?<=\d)\s+(?=[GMK]B\b)", "\u00A0", label, flags=re.I)  # aby nie rodzielal cyfr od jednostek
            label = re.sub("((?:1080|720|1440)[pi])", r"[LOWERCASE]\1[/LOWERCASE]", label, flags=re.I)  # aby np. 1080i było bardziej widoczne
            if (p.lower() == "external"
                # or p.lower() == "pobrane"
                or "quality" in (source.get("unsure") or "")
               ):
                label = re.sub("(4K|(?:1080|720|1440)[pi])", r"\1*", label, flags=re.I)  # dołączenie gwiazdki
            # log(f'{label=}')  # kontrola
            """
            if control.setting("sources.remove_spaces_on_list") == "true":
                # label = label.replace(" | ", "|")  # zmniejszenie odstępów
                label = label.replace(" |", "|").replace("| ", "|")  # zmniejszenie odstępów
            """
            if remove_verticals_on_list:
                label = label.replace("|", " ")
                label = label.replace("   ", "  ")
                # label = label.replace("  ", " ")
                label = label.replace(" [/I]  ", " [/I] ")
                pass

            label = label.upper()
            # fflog(f'{trash=} {label=}')  # na tym etapie nie ma jeszcze 2 linii
            if trash and isinstance(trash, str):
                label = re.sub(f"({re.escape(trash)})", r"[COLOR darkred]\1[/COLOR]", label, flags=re.I)

            # wdrożenie LABELa
            if (
                (d or p.lower() == "pobrane")
                or (d or p.lower() == "external")
                or (d or p.lower() == "plex")
                or (d or p.lower() == "rapideo")
                or (d or p.lower() == "twojlimit")
                or (d or p.lower() == "nopremium")
                or (d or p.lower() == "tb7")
                or (d or p.lower() == "xt7")
                or (d or p.lower() == "cdapremium")
                or (d or p.lower() == "ekinotv premium")
                or (d or p.lower() == "library")
                or (d or p.lower() == "biblioteka")
            ):
                clib = control.setting(f"{p.lower()}.library.color.identify")
                clib = int(clib) if clib else 10
                if clib < 10 and source.get("on_account"):
                    color = source_utils.getPremColor(str(clib))
                    source["label"] = f'[COLOR {color}]{label}[/COLOR]'  # wdrożenie LABELa
                else:
                    prem_identify = source_utils.getPremColor()
                    cp = control.setting(f"{p.lower()}.color.identify")
                    cp = int(cp) if cp else 10
                    if cp < 10:
                        color = source_utils.getPremColor(str(cp))
                        source["label"] = f'[COLOR {color}]{label}[/COLOR]'  # wdrożenie LABELa
                    elif not prem_identify == "nocolor":
                        source["label"] = (("[COLOR %s]" % prem_identify) + label + "[/COLOR]")  # wdrożenie LABELa
                    else:
                        source["label"] = label  # wdrożenie LABELa
            else:
                source["label"] = label  # wdrożenie LABELa

            # dorzucenie ewentualnie drugiej linii
            if (filename_in_2nd_line == "true" or source.get("trash")) and "info2" not in source:
                # if url2 and url2.lower()[-3:] in EXTS:
                if url2:
                    source["info2"] = url2
                if source.get("filename"):
                    source["info2"] = source["filename"]
            if (
                source.get("info2")
                and (filename_in_2nd_line == "true" or source.get("trash"))  # zastanawiam się, czy info2 to tylko dla nazwy pliku
                ):
                source["info2"] = unescape(unquote(source["info2"]))
                if source.get("on_account"):
                    source["info2"] = '[I]' + source["info2"] + '[/I]'  # opcjonalnie, aby trochę bardziej odróżnić
                # sprawdzenie, czy wyróżnić jakiś fragment w tej 2 linii
                if trash and isinstance(trash, str):
                    source["info2"] = re.sub(f"({re.escape(trash)})", r"[COLOR darkred]\1[/COLOR]", source["info2"], flags=re.I)
                # dodanie do labela dodatkowych spacji, bo przy przesuwaniu tekstu Kodi ucina 2 linijkę, jeśli ta jest dłuższa od górnej
                if fix_for_scroll_long_text_with_second_line:
                    dlugosc1 = len(re.sub(f'\[.*?\]', '', source["label"]))
                    dlugosc2 = len(source["info2"])
                    roznica = dlugosc2 - dlugosc1
                    if roznica > 5:  # jakiś próg zadziałania
                        source["label"] += " " * int(roznica * 1.84)
                source["label"] += '[CR][LIGHT] ' + source["info2"] + '[/LIGHT]'  # dodanie 2 linii do labela

            return source


        # LABELOWANIE
        for i in range(len(self.sources)):
            #self.sources[i]["label"] = _makeLabel(self.sources[i])["label"]
            self.sources[i] = _makeLabel(self.sources[i])

        # odrzucenie tych, które się nie załapały czemuś (nie dostały labela)
        self.sources = [i for i in self.sources if "label" in i]

        # odrzucenie tych, które mają oznaczenie "kosza" (przeważnie to odrzucone przez filtr dopasowujący tytuły)
        for i in self.sources[:]:
            if i.get("trash"):
                if isinstance(i.get("trash"), bool):
                    i["label"] = i["label"].replace("[CR]", "[CR][COLOR brown]") + "[/COLOR]"
                self.sources.remove(i)
        """
        self.sources = [
            i
            for i in self.sources
            if not i.get("trash")
        ]
        """

        # i jeszcze odfiltrowania, które wykorzystują nadany już label

        # odrzucenie wersji 3D
        if control.setting("3D.disallowed") == "true":
            for i in self.sources[:]:
                if re.search(r"\b3D\b", i["label"], re.I):
                    i["label"] = re.sub(r"\b(3D)\b", r"[COLOR darkred]\1[/COLOR]", i["label"], flags=re.I)
                    self.sources.remove(i)

        # odrzucenie kodeka HEVC (przydatne dla starszych urządzeń)
        if not control.setting("HEVC") == "true":
            HEVC_pat = r"\b(HEVC|[xh]265)\b"
            for i in self.sources[:]:
                if re.search(HEVC_pat, i["label"], re.I):
                    i["label"] = re.sub(HEVC_pat, r"[COLOR darkred]\1[/COLOR]", i["label"], flags=re.I)
                    self.sources.remove(i)
            HEVC_pat = None
            """
            self.sources = [
                i
                for i in self.sources
                if "HEVC" not in i["label"] or "265" not in i["label"]
            ]
            """

        # odrzucenie nagrywanego kamerą
        CAM_disallowed = control.setting("CAM.disallowed")
        if CAM_disallowed == "true":
            CAM_format = ["camrip", "hdcam", "hqcam", "dvdcam", "cam"]
            if control.setting("telesync.disallowed") == "true":
                CAM_format += ["hdts", "hd-ts", "telesync", " ts ", "tsrip", "dvdts"]
            CAM_format_re = re.compile(rf"\b({'|'.join(CAM_format)})(v[1-4])?\b", flags=re.I)
            for i in self.sources[:]:
                if CAM_format_re.search(i["label"]):
                    i["label"] = CAM_format_re.sub(r"[COLOR darkred]\1\2[/COLOR]", i["label"])
                    self.sources.remove(i)
            CAM_format_re = None
            """
            self.sources = [
                i
                for i in self.sources
                # if "CAM" not in i["label"]
                if not any(x in i["label"].lower().replace("]", " ").replace("[", " ") for x in CAM_format)
            ]
            """

        # odrzucenie dźwięku z kina
        if control.setting("MD.sound.disallowed") == "true":
            for i in self.sources[:]:
                """
                if re.search(r"\b(md|dubbing[ _.-]kino)\b", i["label"], re.I):
                    i["label"] = re.sub(r"\b(md|dubbing[ _.-]kino)\b", r"[COLOR darkred]\1[/COLOR]", i["label"], flags=re.I)
                """
                label = re.sub(r"\b(md|(dubbing|audio)[ _.-]kino)\b", r"[COLOR darkred]\1[/COLOR]", i["label"], flags=re.I)
                if label != i["label"]:
                    i["label"] = label
                    self.sources.remove(i)
            label = None
            """
            self.sources = [
                i
                for i in self.sources
                if not re.search(r"\b(md|dubbing[ _.-]kino)\b", i["label"], re.I)
            ]
            """

        # tylko wersja z PL
        if control.setting("lang.onlyPL") == "true":
            #lang_allowed = ["pl"]
            if control.setting("MULTI.allowed") == "true":
                #lang_allowed += ["multi"]
                MULTI_allowed = True
                # MULTI_format_re = re.compile(rf"\b({'|'.join(['MULTI'])})\b", flags=re.I)
            else:
                MULTI_allowed = False
            for i in self.sources[:]:
                #fflog(f'{i.get("language")=}')
                if i.get("language") != "pl":
                    #fflog(f'{i.get("language")=}')
                    # if MULTI_allowed and MULTI_format_re.search(i["label"]):
                    if MULTI_allowed and i.get("language") == "multi":
                        continue
                    else:
                        #i["label"] = i["label"].replace(" | ", " | [COLOR darkred]brak PL[/COLOR] | ", 1)
                        i["label"] = re.sub(r"(\|[^|]*)|$", r"\1 | [COLOR darkred]brak PL[/COLOR] ", i["label"], 1).rstrip(" |").replace("  ", " ")
                        self.sources.remove(i)
            """
            self.sources = [
                i
                for i in self.sources
                if i.get("language") == "pl"
            ]
            """

        # tylko nie większe niż
        if (maxSourceSize := int(control.setting("maxSourceSize"))) > 0:
            maxSourceSize = maxSourceSize * 1024 * 1024 * 1024 + 0
            for i in self.sources[:]:
                if source_utils.convert_size_to_bytes(i.get("size", "")) > maxSourceSize:
                    i["label"] = re.sub(r"\b(\d+([.,]\d+)?\s?[GMK]B)\b", r"[COLOR darkred]\1[/COLOR]", i["label"])
                    self.sources.remove(i)
            """
            self.sources = [
                i
                for i in self.sources
                if source_utils.convert_size_to_bytes(i.get("size", "")) < maxSourceSize
            ]
            """

        # odrzucenie wersji z napisami
        if control.setting("subtitles.disallowed") == "true":
            for i in self.sources[:]:
                if re.search(r"\bnapisy\b", i["label"], re.I):
                    i["label"] = re.sub(r"\b(napisy)\b", r"[COLOR darkred]\1[/COLOR]", i["label"], flags=re.I)
                    self.sources.remove(i)

        # do wykorzystania przez inne filtry
        def is_in_text(src, disallowed_rx, disallowed_rx1=None, color="darkred"):
            """ może być uniwersalną funkcją, trzeba tylko ustawić zmienną disallowed_rx """
            if not disallowed_rx:
                #return True
                return
            label, num = disallowed_rx.subn(rf"[COLOR {color}]\1[/COLOR]", src["label"])
            if num:
                if f"[COLOR {color}][/COLOR]" in label and disallowed_rx1:
                    is_in_text(src, disallowed_rx1, color=color)
                else:
                    src["label"] = label
            #return num == 0
            #return not num
            return bool(num)

        # odrzucenie HDR i DolbyVision
        try:
            HDR_disallowed = control.setting("HDR.disallowed") == "true"
        except:
            HDR_disallowed = False
        if HDR_disallowed:
            # disallowed_words = ['HDR', 'DV', 'DoVi', 'DolbyVision', 'Dolby Vision']
            # disallowed_pat = "|".join(re.escape(w) for w in disallowed_words)
            # disallowed_pat = "HDR|\bDV\b|\bDoVi\b|Dolby ?Vision"
            # disallowed_pat = "HDR|\bD(?P<g1>o)?(?P<g2>lby)?(?(g2) ?)V(?(g1)i)(sion)?\b"
            disallowed_pat = "HDR|\bD(?:V|oVi|olby ?Vision)\b"
            # disallowed_rx = re.compile(fr"\b({disallowed_pat})\b", flags=re.I)
            disallowed_rx = re.compile(fr"({disallowed_pat})", flags=re.I)
            self.sources = [src for src in self.sources if not is_in_text(src, disallowed_rx)]

        # zakazane słowa
        disallowed_words = control.setting('words.disallowed')
        fflog(f'{disallowed_words=}', 0)
        #if disallowed_words:
        def make_patterns(disallowed_words):
            if isinstance(disallowed_words, str):
                disallowed_words = disallowed_words.split(',')  # string into list
                disallowed_words = [w.strip().replace('"', '') for w in disallowed_words]  # clean a little
                disallowed_words = list(filter(None, disallowed_words))  # eliminate empty
                disallowed_words = list(dict.fromkeys(disallowed_words))  # eliminate duplicates

            if disallowed_words:
                # fflog(f'{disallowed_words=}')

                disallowed_words2 = []
                for dw in disallowed_words:
                    if "+" in dw:
                        dw2 = dw.split('+')  # string into list
                        dw2 = [w.strip().replace('"', '') for w in dw2]  # clean a little
                        dw2 = list(filter(None, dw2))  # eliminate empty
                        if dw2:
                            disallowed_words2.append(dw2)
                            disallowed_words = [w for w in disallowed_words if w != dw]

                # fflog(f'{disallowed_words=}')
                # fflog(f'{disallowed_words2=}')
                if disallowed_words:
                    disallowed_pat = "|".join(re.escape(w) for w in disallowed_words)
                    disallowed_rx = re.compile(fr"\b({disallowed_pat})\b", flags=re.I)
                else:
                    disallowed_rx = None

                if disallowed_words2:
                    disallowed_pat2 = []
                    for dw2 in disallowed_words2:
                        pattern2 = ''.join([fr"(?=.*\b{re.escape(word)}\b)" for word in dw2])
                        disallowed_pat2.append(pattern2)
                    disallowed_pat2 = "|".join(w for w in disallowed_pat2)
                    disallowed2_rx = re.compile(fr"({disallowed_pat2})", flags=re.I)

                    disallowed_pat1 = []
                    for dw2 in disallowed_words2:
                        disallowed_pat1 += dw2
                    disallowed_pat1 = list(dict.fromkeys(disallowed_pat1))  # eliminate duplicates
                    disallowed_pat1 = "|".join(re.escape(w) for w in disallowed_pat1)
                    disallowed1_rx = re.compile(fr"\b({disallowed_pat1})\b", flags=re.I)
                else:
                    disallowed2_rx = disallowed1_rx = None

            else:
                disallowed_rx = disallowed2_rx = disallowed1_rx = None
            return disallowed_rx, disallowed2_rx, disallowed1_rx

        def rozdziel_na_priorytet(disallowed_words):
            disallowed_words = disallowed_words.split(',')  # string into list
            disallowed_words = [w.strip().replace('"', '') for w in disallowed_words]  # clean a little
            disallowed_words = list(filter(None, disallowed_words))  # eliminate empty
            disallowed_words = list(dict.fromkeys(disallowed_words))  # eliminate duplicates
            if disallowed_words:
                zwykla = [w for w in disallowed_words if w[-1]!="!"]
                priorytetowa = [w[:-1].strip() for w in disallowed_words if w[-1]=="!"]
                return zwykla, priorytetowa
            else:
                return [], []

        def sprawdz_czy_jest(src, disallowed_rx, disallowed2_rx, disallowed1_rx, color="darkred"):
            d1 = is_in_text(src, disallowed_rx, color=color)
            d2 = is_in_text(src, disallowed2_rx, disallowed1_rx, color=color)
            return d1 or d2

        if disallowed_words:
            zwykla, priorytetowa = rozdziel_na_priorytet(disallowed_words)
            nonrejectable_phrases = control.setting('nonrejectable_phrases')
            fflog(f'{nonrejectable_phrases=}', 0)
            # zwykla1, priorytetowa1 = rozdziel_na_priorytet(nonrejectable_phrases)

            self.sources = [src for src in self.sources
                            if not sprawdz_czy_jest(src, *make_patterns(priorytetowa), color="ffcc0000") and (
                               not sprawdz_czy_jest(src, *make_patterns(zwykla))
                                or sprawdz_czy_jest(src, *make_patterns(nonrejectable_phrases), color="green")
                                # or sprawdz_czy_jest(src, *make_patterns(zwykla1), color="green")
                               )
                           ]
            if False:
                pass
                """
                nonrejectable_phrases = control.setting('nonrejectable_phrases')
                fflog(f'{nonrejectable_phrases=}')
                nonrejectable_phrases = nonrejectable_phrases.split(',')  # string into list
                nonrejectable_phrases = [w.strip().replace('"', '') for w in nonrejectable_phrases]  # clean a little
                nonrejectable_phrases = list(filter(None, nonrejectable_phrases))  # eliminate empty
                nonrejectable_phrases = list(dict.fromkeys(nonrejectable_phrases))  # eliminate duplicates
                if nonrejectable_phrases:
                    nonrejectable_pat = "|".join(re.escape(w) for w in nonrejectable_phrases)
                    nonrejectable_rx = re.compile(fr"\b({nonrejectable_pat})\b", flags=re.I)
                    # fflog(f'{nonrejectable_rx=}')
                    # self.sources = [src for src in self.sources if is_not in_text(src) or nonrejectable_rx.search(src["label"])]
                    self.sources = [src for src in self.sources if not is_in_text(src, disallowed_rx) and not is_in_text(src, disallowed2_rx, disallowed1_rx) or nonrejectable_rx.search(src["label"])]
                else:
                    # nonrejectable_rx = None
                    # self.sources = [src for src in self.sources if not is_in_text(src)]
                    self.sources = [src for src in self.sources if not is_in_text(src, disallowed_rx) and not is_in_text(src, disallowed2_rx, disallowed1_rx)]
                """
                r"""
                for i in self.sources[:]:
                    for x in disallowed_words:
                        #if re.search(fr"\b{re.escape(x)}\b" , re.sub(r"\[/?(LIGHT|CR|B|I)\]" , "", i["label"]), re.I):
                        if (m := re.search(fr"\b{re.escape(x)}\b" , i["label"], re.I)):
                            m = (m.span()[0], m.span()[1], m.group())
                            #i["label"] = re.sub(fr"\b({re.escape(x)})\b", r"[COLOR red][LOWERCASE]\1[/LOWERCASE][/COLOR]", i["label"], flags=re.I)
                            i["label"] = i["label"][:m[0]] + f"[COLOR darkred][LOWERCASE]{m[2]}[/LOWERCASE][/COLOR]" + i["label"][m[1]:]
                            self.sources.remove(i)
                            break
                i = x = m = disallowed_words = None  # opcjonalnie
                """
                r"""
                self.sources = [
                    i
                    for i in self.sources
                    if not any(x in re.sub(r"\[/?(LIGHT|CR|B|I)\]" , "", i["label"]).lower() for x in disallowed_words)
                ]
                """

        # SORTOWANIE
        self.sources = self.sortSources(self.sources)

        # numerowanie
        if numbering:
            for i in range(len(self.sources)):
                # fflog(f'{i=}  {self.sources[i]=}')
                self.sources[i]["label"] = self.sources[i]["label"].replace("{}", f"{i + 1:02d}", 1)


        # na KONIEC lista ODRZUCONYCH
        # fflog(f'len:{len(sources_before_filtered)} {sources_before_filtered=}')
        # fflog(f'len:{len(self.sources)} {self.sources=}')
        s = [{s.get("provider"): s.get("url")} for s in self.sources]  # lista pomocnicza
        sources_thrown_out = [x for x in sources_before_filtered if {x.get("provider"): x.get("url")} not in s]
        # fflog(f'len:{len(sources_thrown_out)} {sources_thrown_out=}')

        sources_thrown_out = self.sortSources(sources_thrown_out, silent=True)  # sortowanie

        offset = len(self.sources)  # aby kontynuować numerację
        for i in range(len(sources_thrown_out)):
            if "label" not in sources_thrown_out[i]:
                sources_thrown_out[i] = _makeLabel(sources_thrown_out[i], offset)
            if numbering:
                # przenumerowanie
                sources_thrown_out[i]["label"] = re.sub(r'^([^|]*?)(\d{2,})(.*?\|)', r'\1{}\3', sources_thrown_out[i]["label"], 1)  # usunięcie starego numeru
                sources_thrown_out[i]["label"] = sources_thrown_out[i]["label"].replace("{}", f"{offset + i + 1:02d}", 1)

        # wrzucenie do pamięci RAM
        control.window.setProperty(self.itemRejected, json.dumps(sources_thrown_out))


        # w tb7/xt7 dodaje * jak nie wiadomo jaki serwer konkretnie (dotyczy plików z bilbioteki)
        """ przeniosłem wyżej
        for i in range(len(self.sources)):
            if "source" in self.sources[i]:
                self.sources[i]["source"] = self.sources[i]["source"].replace("*", "").replace("~", "")
        """
        return self.sources


    def filter_duplicates(self):
        filtered = []
        append = filtered.append
        remove = filtered.remove
        for i in self.sources:
            # fflog(f'{i=}')
            if i.get("provider", "").lower() in ['tb7', 'xt7', 'rapideo', 'nopremium', 'twojlimit', 'library', 'biblioteka']:  # te serwisy same usuwają swoje duplikaty
                append(i)  # filtered.append
                # fflog(f'1) dodaję {i.get("provider")=}')
                continue
            larger = False
            if not isinstance(i["url"], str):
                append(i)
                continue
            a = i["url"].lower()
            for sublist in filtered:
                try:
                    # fflog(f'\nanaliza {i["provider"]=}        {i["source"]=} \n  {sublist["provider"]=}  {sublist["source"]=}')
                    if i["source"] == "cloud":
                    # if i["source"] == "cloud" or i["provider"] == "library" or i["provider"] == "biblioteka":  # czy to ok ?
                        # fflog(f'5) {i["provider"]=} {i["source"]=}')
                        break
                    b = sublist["url"].lower()
                    if "magnet:" in a:  # to dla torentów ?
                        if i["hash"].lower() in b:
                            # keep matching hash with longer name, possible more file info
                            if len(sublist["name"]) > len(i["name"]):
                                larger = True
                                break
                            remove(sublist)  # filtered.remove
                            # fflog(f'3) remove {sublist.get("provider")=}', 1)
                            break
                    elif a == b:
                        # fflog(f'\nA==B  {i.get("provider")=}  \n{sublist.get("provider")=}')
                        # fflog(f'\nA==B  {i.get("url")=}  \n{sublist.get("url")=}')
                        if sublist.get("provider") == "library" or sublist.get("provider") == "biblioteka":  # z biblioteki nie usuwamy (ok jak plik, a jak w pobranych jest plik a bibliotece strm ?) Pliki strm nie są uwzględniane, więc ok
                            pass
                            larger = True
                            break
                        remove(sublist)  # filtered.remove
                        # fflog(f'4) remove {sublist.get("provider")=}', 1)
                        break
                except Exception:
                    # fflog_exc(1)
                    pass
            if not larger:  # sublist['name'] len() was larger so do not append
                # fflog(f'2) dodaję {i.get("provider")=}')
                append(i)  # filtered.append

        # log_utils.log("Removed %s duplicate sources from list" % (len(self.sources) - len(filtered)), "module")
        fflog("Removed %s duplicate sources from list" % (len(self.sources) - len(filtered)))
        return filtered


    def sourcesResolve(self, item, info=False, for_resolve=None):
        # fflog(f'{for_resolve=}')
        try:
            self.url = url = sub = None
            u = url = item["url"]
            d = item["debrid"]
            direct = item["direct"]
            local = item.get("local", False)
            provider = item["provider"]
            provider = provider.split(" ")[0]
            fflog(f'{provider=}', 0)

            if not self.sourceDict or not any(provider in p for p in self.sourceDict):
                fflog(f'muszę pobrać scraper dla {provider=}', 0)
                self.getScrapers(provider)
            fflog(f'{self.sourceDict=}', 0)

            call = [i[1] for i in self.sourceDict if i[0] == provider]
            # fflog(f'{call=}')
            if call:
                call = call[0]
            else:
                raise Exception(f'brak wymaganego {provider=}  |  {call=}')

            fflog(f'wywołanie funkcji resolve od scrapera {provider}', 0)
            if for_resolve:
                u = url = call.resolve(url, **for_resolve)
            else:
                u = url = call.resolve(url)

            if url is False:
                return False
            
            if url is None or (not "://" in str(url) and not local):
                # if provider == 'netflix':
                #    return url
                # if provider == 'external':
                #    return url
                return None
                #raise Exception()

            if not local:
                url = url[8:] if url.startswith("stack:") else url
                urls = []
                subs = []
                fflog(f'{url=}', 0)
                fflog(f'{url.split(" , ")=}', 0)
                for part in url.split(" , "):
                    u = part
                    if not d == "":
                        part = debrid.resolver(part, d)
                    elif not direct:
                        fflog(f'do rozwiązania {u=}', 1)
                        # ewentualne dodatkowe przekształcenie
                        if "|" in u and "$$" not in u and (referer:=dict(parse_qsl(u.rsplit("|", 1)[1])).get("Referer")):
                            u = f'{u.split("|")[0]}$${referer}'
                            fflog(f'link to resolve {u=}', 0)
                        # checking url
                        subtitle = "$$subs" in u
                        fflog(f'check for {subtitle=}', 0)
                        hmf = resolveurl.HostedMediaFile(url=u, include_disabled=True, include_universal=False, subs=subtitle)
                        # fflog(f'{hmf=}', 1)
                        # result
                        if hmf.valid_url():
                            part = hmf.resolve()
                            fflog(f'{part=}', 0)  # może być False, jak resolver nie otworzy adresu
                            if isinstance(part, dict):
                                sub = part.get('subs')
                                fflog(f'    {sub=}', 0)
                                resolved = part.get('url')
                                fflog(f'    {resolved=}', 0)
                                part = resolved
                            else:
                                sub = ""
                            # part = None if part is False else part
                            if not part:
                                komunikat = f'Resolver nie otrzymał prawidłowego adresu docelowego'
                                fflog(f'{komunikat}')
                                komunikat = komunikat.replace("Resolver", "")
                                control.infoDialog(komunikat, heading="Resolver", icon="WARNING", time=2900, sound=False)
                                control.sleep(2700)
                                return  # przydaje się szczególnie, gdy jest włączone autoodtwarzanie                            
                        else:
                            hosting = re.search(r"^https?://((\w+\.)*(\w+)(\.\w+))/", u)
                            komunikat = f'Resolver nie rozpoznał domeny "{hosting[1] if hosting else u}"'
                            # fflog(f'{komunikat} (odtwarzanie może być niemożliwe)')
                            fflog(f'{komunikat}')
                            fflog('odtwarzanie tego źródła nie będzie realizowane')
                            komunikat = komunikat.replace("Resolver", "").replace("domeny ", "domeny \n")
                            control.infoDialog(komunikat, heading="Resolver", icon="WARNING", time=2900, sound=False)
                            control.sleep(2700)
                            return  # przydaje się szczególnie, gdy jest włączone autoodtwarzanie

                    urls.append(part)
                    subs.append(sub)

                url = "stack://" + " , ".join(urls) if len(urls) > 1 else urls[0]  # co to robi? jakaś kolejka?
                sub = "stack://" + " , ".join(subs) if len(subs) > 1 else subs[0] if subs else "" # co to robi? jakaś kolejka?
                fflog(f' {url=}', 0)
                fflog(f' {sub=}', 0)

            if not url:
                fflog(f'{url=}')
                raise Exception(f'{url=}')

            ext = (
                url.split("?")[0]
                .split("&")[0]
                .split("|")[0]
                .rsplit(".")[-1]
                .replace("/", "")
                .lower()
            )
            if ext == "rar":
                fflog(f'{ext=}')
                raise Exception(f'{ext=}')

            # to może być próba sprawdzenia, czy to jest stream hls?
            try:
                headers = url.rsplit("|", 1)[1]
            except Exception:
                headers = ""
            headers = quote_plus(headers).replace("%3D", "=") if " " in headers else headers
            headers = dict(parse_qsl(headers))
            if url.startswith("http") and ".m3u8" in url:  # nie wiem, po co to?
                # fflog(f'dodatkowy test, bo ".m3u8" w nazwie {url=}', 1)
                result = True
                # result = client.request(url.split("|")[0], headers=headers, output="geturl", timeout="20")  # test
                # fflog(f'{result=}', 1)
                if result is None:  # coś poszło nie tak
                    fflog(f'jakiś test dla ".m3u8" w nazwie negatywny')  # tylko co to ostatecznie oznacza?
                    # może to oznacza, że trzeba przez IA odtwarzać?
                    # raise Exception()  # na razie wyłączam to
                    pass
            elif url.startswith("http"):
                pass  # bo poniższe, to dubel
                # self.url = url
                # return url
            else:  # tak sobie dodałem
                pass

            if sub:
                url = (url, sub)

            self.url = url
            return url

        except Exception as e:
            # fflog_exc(1)  # nie włączać tego na produkcję, bo pokazuje błędy resolvera
            # fflog(f'{e=}')
            print(e)
            #err = str(repr(e))  # tak nie było - sam to wymyśliłem, ale to chyba nie wszędzie pasuje
            err = str(e)
            # fflog(f'{err=}')
            if info or err:
                if err:
                    # self.errorForSources(str(repr(e)))  # tak bylo
                    self.errorForSources(err)
                # log(f'[sourcesResolve] {e!r}')  # tak bylo
                # fflog(f'[sourcesResolve] {err}')
            control.sleep(500)
            url = None if url is False else url  # dalej są warunki na is None, a jak pojawia się False, to się coś psuje (szczególnie przy autoodtwarzaniu)
            if url is False:
                return False
            else:
                return
            # czy poniższe, to warunkowe zwrócenie adresu? A może to wywalić?
            """
            # if "ResolverError".lower() not in err.lower():  # tak bylo
            if(
                "ResolverError".lower() not in str(repr(e)).lower()
                and "HTTPError".lower() not in str(repr(e)).lower()
                # and False  # zastanowić się
               ):
                # self.url = url  # czy to może się przydać? czy przeszkodzić? bo jak kod trafił tu, to może oznaczać, że coś poszło nie tak, więc raczej tego nie powinno tu być
                return url  # ale z kolei to po co tu jest zwrócenie adresu zamiast False lub None ? Coś tu nie współgra ze sobą!
                # a co z napisami wówczas ?
            else:
                if err:
                    # control.infoDialog("[CR]" + err, heading="Resolver", icon="ERROR", time=2900, sound=False)
                    pass
            """


    def sourcesDialog(self, items, trash=None, ret_item=False):
        try:
            labels = [i["label"] for i in items]
            
            if not trash:
                rejected_items = json.loads(control.window.getProperty(self.itemRejected))
                if rejected_items:
                    labels += ["[COLOR darkorange][I] *   Źródła odrzucone (przez filtry)  --->[/I][/COLOR]"] 

            control.sleep0(100)
            fflog('open dialog select')
            selected = control.selectDialog(labels)
            fflog(f'{selected=} (number of position from list)')

            if selected == -1:
                fflog('anulowanie')
                return "close://"

            if not trash and rejected_items:
                if selected == len(labels)-1:
                    url = self.sourcesDialog(rejected_items, trash=True, ret_item=ret_item)  # rekurencja
                    if url == "close://":
                        return self.sourcesDialog(items, ret_item=ret_item)
                    return url

            next = [y for x, y in enumerate(items) if x > selected]  # następne od wybranego
            prev = [y for x, y in enumerate(items) if x < selected][::-1]  # poprzednie od wybranego

            items = [items[selected]]  # jeden (wybrany)
            if control.setting("auto.select.next.item.to.play") == "true":
                items = [i for i in items + next + prev][:40]  # wybrany plus poprzednie i następne
                # fflog(f'{len(items)}  {items=}')
            else:
                return self.sourcesDirect(items, ret_item=ret_item)  # tylko wybrany

            header = control.addonInfo("name")
            header2 = header.upper()
            progressDialog = (
                control.progressDialog
                if control.setting("progress.dialog") == "0"
                else control.progressDialogBG
            )
            progressDialog.create(header, "")
            progressDialog.update(0)

            block = None
            import threading
            monitor = control.monitor

            for i in range(len(items)):
                try:
                    if items[i]["source"] == block:
                        raise Exception()

                    w = threading.Thread(target=self.sourcesResolve, args=(items[i],))
                    w.start()

                    try:
                        if progressDialog.iscanceled():
                            break
                        progressDialog.update(
                            int((100 / float(len(items))) * i),
                            str(items[i]["label"]) + "\n" + str(" "),
                        )
                    except Exception:
                        progressDialog.update(
                            int((100 / float(len(items))) * i),
                            str(header2) + "\n" + str(items[i]["label"]),
                        )

                    m = ""

                    for x in range(3600):
                        try:
                            if monitor.abortRequested():
                                return sys.exit()
                            if progressDialog.iscanceled():
                                return progressDialog.close()
                        except Exception:
                            pass

                        k = control.condVisibility("Window.IsActive(virtualkeyboard)")
                        if k:
                            m += "1"
                            m = m[-1]
                        if (not w.is_alive() or x > 60) and not k:
                            break
                        k = control.condVisibility("Window.IsActive(yesnoDialog)")
                        if k:
                            m += "1"
                            m = m[-1]
                        if (not w.is_alive() or x > 60) and not k:
                            break
                        time.sleep(0.5)

                    for x in range(10):
                        try:
                            if monitor.abortRequested():
                                return sys.exit()
                            if progressDialog.iscanceled():
                                return progressDialog.close()
                        except Exception:
                            pass

                        if m == "":
                            break
                        if not w.is_alive():
                            break
                        time.sleep(0.5)

                    if w.is_alive():
                        block = items[i]["source"]

                    if self.url is None:
                        raise Exception()

                    self.selectedSource = items[i]["label"]

                    try:
                        progressDialog.close()
                    except Exception:
                        pass

                    control.execute("Dialog.Close(virtualkeyboard)")
                    control.execute("Dialog.Close(yesnoDialog)")
                    # time.sleep(0.1)
                    control.sleep(100)
                    if not ret_item:
                        return self.url
                    else:
                        return [self.url, items[i]]

                except Exception:
                    pass

            try:
                progressDialog.close()
            except Exception:
                pass

        except Exception as e:
            try:
                progressDialog.close()
            except Exception:
                pass
            print("Error %s" % str(e), log_utils.LOGINFO)


    def sourcesDirect(self, items, ret_item=False):
        
        filtered = [i  for i in items  if i["source"].lower() in self.hostcapDict and i["debrid"] == ""]
        items = [i for i in items if i not in filtered]

        filtered = [i  for i in items  if i["source"].lower() in self.hostblockDict and i["debrid"] == ""]
        items = [i for i in items if i not in filtered]

        items = [i  for i in items  if ("autoplay" in i and i["autoplay"]) or "autoplay" not in i]

        if control.setting("autoplay.sd") == "true":
            items = [i  for i in items  if i["quality"] not in ["4K", "1440p", "1080p", "1080i", "HD", "720p"]]

        header = control.addonInfo("name")
        header2 = header.upper()
        try:
            control.sleep(1000)
            progressDialog = (
                control.progressDialog
                if control.setting("progress.dialog") == "0"
                else control.progressDialogBG
            )
            progressDialog.create(header, "")
            progressDialog.update(0)
        except Exception:
            pass

        monitor = control.monitor

        u = None
        for i in range(len(items)):
            try:
                if progressDialog.iscanceled():
                    break
                progressDialog.update(
                    int((100 / float(len(items))) * i),
                    str(items[i]["label"]) + "\n" + str(" "),
                )
            except Exception:
                progressDialog.update(
                    int((100 / float(len(items))) * i),
                    str(header2) + "\n" + str(items[i]["label"]),
                )
            try:
                if monitor.abortRequested():
                    return sys.exit()
                # fflog(f'{items[i]=}')
                if items[i].get("provider") == "pobrane" or items[i].get("source") == "pobrane":
                    url = items[i].get("url") or None
                else:
                    url = self.sourcesResolve(items[i])  # sprawdzenie adresu url
                fflog(f'{u=} {url=}', 0)
                """ tak było, ale wówczas pobiera niepotrzebnie następne źródło
                if u is None:
                    u = url
                else:
                    break
                """
                # if url is None:  # a jeszcze może być False
                if not url:
                    if (i+1) < len(items):
                        control.sleep(500)
                        control.infoDialog(f"próbuję następne źródło ({i+2})", icon="INFO", sound=False)
                        fflog(f"próbuję następne źródło ({i+2}/{len(items)})")
                        control.sleep(500)
                    continue
                else:
                    u = url
                    break
            except Exception:
                pass

        try:
            progressDialog.close()
        except Exception:
            pass

        if not u:
            i = -1

        if not ret_item:
            return u  # adres url źródła
        else:
            return [u, items[i]]


    def errorForSources(self, err=""):
        # fflog(f'pojawił się jakiś problem przy wywołaniu elementu do odtwarzania (nie określono adresu url streamu, ale mogło też nastąpić anulowanie akcji) {err=}')
        err = "[CR]" + str(err) if err else ""
        c = 0
        while control.condVisibility('Window.IsActive(notification)') and c < (5 * 2):
            c += 1
            control.sleep(200)
        control.infoDialog(control.lang(32401) + err, sound=False, icon="INFO")  # Brak źródeł
        fflog(control.lang(32401) + err.replace("[CR]", " - "))
        control.sleep(2800)


    def getLanguage(self):
        langDict = {
            "English": ["en"],
            "German": ["de"],
            "German+English": ["de", "en"],
            "French": ["fr"],
            "French+English": ["fr", "en"],
            "Portuguese": ["pt"],
            "Portuguese+English": ["pt", "en"],
            "Polish": ["pl"],
            "Polish+English": ["pl", "en"],
            "Korean": ["ko"],
            "Korean+English": ["ko", "en"],
            "Russian": ["ru"],
            "Russian+English": ["ru", "en"],
            "Spanish": ["es"],
            "Spanish+English": ["es", "en"],
            "Greek": ["gr"],
            "Italian": ["it"],
            "Italian+English": ["it", "en"],
            "Greek+English": ["gr", "en"],
        }
        name = control.setting("providers.lang")
        return langDict.get(name, ["pl"])


    def getLocalTitle(self, title, imdb, tvdb, content):
        lang = self._getPrimaryLang()
        if not lang:
            return title

        if content == "movie":
            t = trakt.getMovieTranslation(imdb, lang)
        else:
            t = trakt.getTVShowTranslation(imdb, lang)

        return t or title


    def getAliasTitles(self, imdb, localtitle, content):
        lang = self._getPrimaryLang()
        try:
            t = trakt.getMovieAliases(imdb) if content == "movie" else trakt.getTVShowAliases(imdb)

            if not t:
                t = []
            else:
                t = [
                     i
                     for i in t
                     if (
                         # i.get("country", "").lower() in [lang, "", "us", "en", "uk", "gb", "au", "pl", "original"]
                         not self.czy_litery_krzaczki(i.get("title", ""))
                         and i.get("title", "").lower() != localtitle.lower()
                        )
                ]

            fflog("\nALIASY (z Trakt):\n "+("\n"+chr(32)).join(map(repr, t)), 0)
            return t
        except Exception:
            return []


    def _getPrimaryLang(self):
        langDict = {
            "English": "en",
            "German": "de",
            "German+English": "de",
            "French": "fr",
            "French+English": "fr",
            "Portuguese": "pt",
            "Portuguese+English": "pt",
            "Polish": "pl",
            "Polish+English": "pl",
            "Korean": "ko",
            "Korean+English": "ko",
            "Russian": "ru",
            "Russian+English": "ru",
            "Spanish": "es",
            "Spanish+English": "es",
            "Italian": "it",
            "Italian+English": "it",
            "Greek": "gr",
            "Greek+English": "gr",
        }
        name = control.setting("providers.lang")
        lang = langDict.get(name)
        return lang


    def getTitle(self, title):
        title = cleantitle.normalize(title)
        return title


    def getScrapers(self, provider="", language=None):
        if not provider:
            fflog(f'pobieranie listy dostępnych scraperów', 0)  # na podstawie plików na dysku (folder pl i en)
        else:
            fflog(f'wczytanie scrapera {provider}', 0)
        from resources.lib.sources import sources
        self.sourceDict = sources(provider, language)
        fflog(f'{len(self.sourceDict)=}', 0)


    def getConstants(self):
        self.itemProperty = "plugin.video.fanfilm.container.items"
        self.itemRejected = "plugin.video.fanfilm.container.itemsRejected"
        self.metaProperty = "plugin.video.fanfilm.container.meta"

        try:
            self.hostDict = resolveurl.relevant_resolvers(order_matters=True)
            self.hostDict = [i.domains for i in self.hostDict if "*" not in i.domains]
            self.hostDict = [i.lower() for i in reduce(lambda x, y: x + y, self.hostDict)]
            self.hostDict = [x for y, x in enumerate(self.hostDict) if x not in self.hostDict[:y]]
        except Exception:
            self.hostDict = []

        self.hostprDict = [
            "1fichier.com",
            "oboom.com",
            "rapidgator.net",
            "rg.to",
            "uploaded.net",
            "uploaded.to",
            "ul.to",
            "filefactory.com",
            "nitroflare.com",
            "turbobit.net",
            "uploadrocket.net",
        ]

        self.hostcapDict = [
            "hugefiles.net",
            "kingfiles.net",
            "openload",
            "openload.io",
            "openload.co",
            "oload.tv",
            "thevideo.me",
            "vidup.me",
            "streamin.to",
            "torba.se",
            "flashx",
            "flashx.tv",
        ]

        self.hosthqDict = [
            "gvideo",
            "google.com",
            "openload.io",
            "openload.co",
            "oload.tv",
            "thevideo.me",
            "rapidvideo.com",
            "raptu.com",
            "filez.tv",
            "uptobox.com",
            "uptobox.com",
            "uptostream.com",
            "xvidstage.com",
            "streamango.com",
        ]

        self.hostblockDict = []


    def czy_litery_krzaczki(self, s, mode=0):
        from unicodedata import category

        def _czy_krzaczek(c):
            v = ord(c or ' ')
            # print(c, hex(v), v, (category(c)))  # debug
            if not (c and category(c)[0] == 'L'):  # if not a letter
                return ""
            if 0x20 <= v < 0x370:
                return False
            if 0x370 <= v <= 0x3ff:
                return 'gr'
            if 0x400 <= v <= 0x52f:
                return "rus"
            return True

        s = s.strip()
        if not len(s):
            return None

        if mode == 0:  # whole text (only letters)
            r = [_czy_krzaczek(l) for l in s if category(l)[0] == 'L']
        elif mode == 2:
            r = [_czy_krzaczek(s[i]) for i in [0, -1]]  # first and last letter
        if r.count("gr"):
            return "gr"
        if r.count("rus"):
            return "rus"
        return any(r)
