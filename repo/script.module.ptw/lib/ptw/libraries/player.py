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

import base64
import codecs
import gzip
import json
import os
import re
import sys
from urllib.parse import quote_plus, unquote_plus, parse_qsl

import six
import xbmc

from ptw.libraries import bookmarks
from ptw.libraries import cleantitle
from ptw.libraries import control
from ptw.libraries import playcount
from ptw.libraries import trakt
from ptw.libraries.source_utils import get_kodi_version

from ptw.libraries.log_utils import log, fflog
from ptw.debug import log_exception, fflog_exc


class player(xbmc.Player):
    def __init__(self):
        super().__init__()
        self.currentTime = None
        self.totalTime = None
        self.runtime = None  # traktowy totaltime
        self.content = None
        self.title = None
        self.localtitle = None
        self.englishtitle = None
        self.originaltitle = None
        self.tvshowtitle = None
        self.year = None
        self.name = None
        self.season = None
        self.episode = None
        self.DBID = None
        self.imdb = None
        self.tvdb = None
        self.tmdb = None
        self.ids = None
        self.offset = None
        self.is_active = True
        self.playback_started = None


    # większość wywowałań tej funkcji wstawia zamiast tmdb "tvdb"
    def run(self, title, year, season, episode, imdb, tvdb, tmdb, url, subs=None, meta=None, handle=None, hosting=None):
        try:
            control.execute('Dialog.Close(notification,true)')
            control.sleep0(100)
            fflog("przygotowywanie do odtwarzania")
            control.dialog.notification('FanFilm', 'uruchamianie odtwarzania ...', time=1500, sound=False)
            control.sleep(500)

            self.currentTime = 0
            self.totalTime = 0
            self.runtime = 0
            self.playback_started = None

            self.content = "movie" if season is None or episode is None else "episode"

            localtitle = originalname = tvshowtitle = ""
            if isinstance(title, tuple):
                title, localtitle, originalname, tvshowtitle = title
            self.englishtitle = title  # angielski
            self.localtitle = localtitle
            self.originaltitle = originalname
            self.tvshowtitle = tvshowtitle
            self.title = title = localtitle or title
            self.year = year
            self.name = (
                quote_plus(title) + quote_plus(" (%s)" % year)
                if self.content == "movie"
                else quote_plus(title) + quote_plus(" S%01dE%01d" % (int(season), int(episode)))
            )
            self.name = unquote_plus(self.name)  # to jakieś awaryjne do wyszukania informacji z bilioteki, ale jak tytuł jest w meta, to do playera idzie z meta

            self.season = "%01d" % int(season) if self.content == "episode" else None
            self.episode = "%01d" % int(episode) if self.content == "episode" else None

            self.DBID = None  # jakiś reset zmiennej chyba

            self.imdb = imdb if not imdb is None else "0"
            self.tmdb = tmdb if not tmdb is None else "0"
            self.tvdb = tvdb if not tvdb is None else "0"

            #self.ids = {"imdb": self.imdb, "tmdb": self.tmdb}  # brak tvdb
            self.ids = {"imdb": self.imdb, "tvdb": self.tvdb, "tmdb": self.tmdb}
            self.ids = dict((k, v) for k, v in self.ids.items() if not v == "0")  # znacznik dla wtyczki script.trakt, aby mogła rozpoznawać filmy

            self.offset, self.runtime = bookmarks.get(self.content, imdb, season, episode)

            #fflog(f"{self.imdb=} {self.tmdb=} {self.ids=} {self.offset=}", 1)
            fflog(f"{self.ids=}   {self.offset=}   {self.content=}  {imdb=}  {season=}  {episode=}", 1)


            poster, thumb, fanart, clearlogo, clearart, discart, keyart, landscape, banner, icon, characterart, meta = self.getMeta(meta)
            # fflog(f'\n   {poster=} \n    {thumb=} \n   {fanart=} \n{clearlogo=} \n {clearart=} \n  {discart=} \n   {keyart=} \n{landscape=} \n   {banner=} \n     {icon=} \n{characterart=} \n{meta=}', 1)

            if isinstance(url, tuple):
                url, subs = url

            fflog(f'{control.setting("player.strip_headers_from_link")=}', 0)  # to jakby też (patrz komentarz poniżej)
            if control.setting("player.strip_headers_from_link") == "true":
                url = url.split("|")[0]

            fflog(f'{url=}', 0)  # dziwne, ale to pomaga uzwględnić zmianę powyższego ustawienia bez konieczności ponownego szukania źródeł (tylko musi być chyba zmienna w logu)

            # Create a playable item with a path to play.
            item = control.item(path=url, offscreen=True)  # offscreen=True means that the item is not meant for displaying (only to pass info to the Kodi player)

            if subs:
                fflog(f'{subs.keys()=}', 1)
                fflog(f'{subs=}', 0)
                item.setSubtitles(list(subs.values()))

            if self.content == "movie":
                item.setArt(
                    {
                        "icon": icon,
                        "thumb": thumb,
                        "poster": poster,
                        "fanart": fanart,
                        "clearlogo": clearlogo,
                        "clearart": clearart,
                        "discart": discart,
                        "keyart": keyart,
                        "landscape": landscape,
                        "banner": banner,
                    }
                )
            else:
                poster1 = poster2 = poster
                if isinstance(poster, tuple):
                    poster1, poster2 = poster
                    poster = poster2

                banner1 = banner2 = banner
                if isinstance(banner, tuple):
                    banner1, banner2 = banner
                    # banner = banner2 if banner1 == banner2 else banner1
                    banner = banner2

                landscape1 = landscape2 = landscape
                if isinstance(landscape, tuple):
                    landscape1, landscape2 = landscape
                    # landscape = landscape2 if landscape1 == landscape2 else landscape1
                    landscape = landscape2

                fanart1 = fanart2 = fanart
                if isinstance(fanart, tuple):
                    fanart1, fanart2 = fanart
                    # fanart = fanart2 if fanart1 == fanart2 else fanart1
                    fanart = fanart2

                # fflog(f'\n   {icon=} \n    {thumb=} \n  {poster1=} \n  {poster2=} \n   {fanart=} \n  {fanart1=} \n  {fanart2=} \n{clearlogo=} \n {clearart=} \n   {keyart=} \n{landscape=} \n{landscape1=} \n{landscape2=} \n   {banner=} \n  {banner1=} \n  {banner2=} \n     {icon=} \n{characterart=}', 1)
                item.setArt(
                    {
                        "icon": icon,
                        "thumb": thumb,
                        "tvshow.poster": poster1,
                        "season.poster": poster2,
                        "fanart": fanart,
                        "clearlogo": clearlogo,
                        # "tvshow.clearlogo": clearlogo,  # opcjonalnie (jak nie będzie poprzednie wystarczało)
                        "clearart": clearart,
                        "keyart": keyart,
                        "landscape": landscape,
                        "banner": banner,
                        # nie wiem, czy podział tu (w odtwarzaczu) na season i tvshow ma sens
                        "season.banner": banner2,
                        "season.landscape": landscape2,
                        "season.fanart": fanart2,
                        "tvshow.banner": banner1,
                        "tvshow.landscape": landscape1,
                        "tvshow.fanart": fanart1,
                    }
                )
                # fflog(f'{characterart=}')  # z ciekawości
                if characterart:
                    if isinstance(characterart, list):
                        for an in range(0, len(characterart)):
                            item.setArt({f"characterart{an+1}": characterart[an]})
                            item.setArt({f"tvshow.characterart{an+1}": characterart[an]})  # nie wiem, czy to działa i czy to w ogóle potrzebne
                            pass
                    else:
                        item.setArt({"characterart": characterart})
                        item.setArt({"tvshow.characterart": characterart})  # nie wiem, czy to działa i czy to w ogóle potrzebne
                        pass

            try:
                if ":" in str(meta.get("duration") or ""):
                    meta["duration"] = time_to_seconds(meta["duration"])
                item.setInfo(type="video", infoLabels=control.metadataClean(meta))
            except Exception:
                fflog_exc(1)
                fflog(f'{control.metadataClean(meta)=}')
                pass

            vtag = item.getVideoInfoTag()
            castwiththumb = meta.get("castwiththumb")
            if castwiththumb:
                castwiththumb = [xbmc.Actor(**a) for a in castwiththumb]
                vtag.setCast(castwiththumb)

            if not hosting:
                params2 = dict(parse_qsl(sys.argv[2][1:]))
                # fflog(f'{params2=}', 1)
                source = params2.get("source")
                try:
                    source = json.loads(source)[0]  # to się tylko sprawdzi, gdy źródła w folderze (nie w okienku)
                    # provider = source.get("provider")
                    hosting = source.get("source")
                except Exception:
                    fflog_exc(1)
                    # provider = ""
                    hosting = ""
            # fflog(f'{provider=} {hosting=}', 1)
            fflog(f'{hosting=}', 1)

            ia = False
            # if params2.get("ia"):  # źródła z okienka tego nie ma
            if "&ia=1" in sys.argv[2]:
                ia = True
            fflog(f'{url=}', 0)
            if url.startswith('ia://'):
                ia = True
                url = url[5:]
            if not ia and control.setting("player.ia") == "true":
                if url.startswith("http") and ".m3u8" in url:  # czy nie dodać także ".m3u" ?
                    ia = True
                else:
                    fflog('IA nie będzie, bo brak ".m3u8" w adresie {url=}', 0)
                    pass
            if "&ia=0" in sys.argv[2]:
                ia = False

            if ia:
                disallowed_words = control.setting('player.ia_not_for')
                # fflog(f'{disallowed_words=}', 0)
                disallowed_words = disallowed_words.split(',')  # string into list
                disallowed_words = [w.strip().replace('"', '') for w in disallowed_words]  # clean a little
                disallowed_words = list(filter(None, disallowed_words))  # eliminate empty
                disallowed_words = list(dict.fromkeys(disallowed_words))  # eliminate duplicates
                fflog(f'{disallowed_words=}', 0)
                if disallowed_words and hosting and hosting.lower() in disallowed_words:
                    if "&ia=1" in sys.argv[2]:
                        fflog(f'nie zostanie zastosowany wyjątek dla {hosting=}')
                    else:
                        ia = False
                        fflog(f'IA nie zostanie użyte, bo {hosting=} jest na liście wyjątków  {disallowed_words}', 1)

            if ia:
                fflog('using Inputstream Adaptive to play stream')
                kodiver = get_kodi_version().major
                # fflog(f'{kodiver=}')
                listitem = item
                stream_url = url
                ia = True
                if kodiver > 16 and ('.mpd' in stream_url or ia):
                    if kodiver < 19:
                        listitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
                    else:
                        listitem.setProperty('inputstream', 'inputstream.adaptive')
                    if '.mpd' in stream_url:
                        if kodiver < 21:
                            listitem.setProperty('inputstream.adaptive.manifest_type', 'mpd')
                        listitem.setMimeType('application/dash+xml')
                    else:
                        if kodiver < 21:
                            listitem.setProperty('inputstream.adaptive.manifest_type', 'hls')
                        listitem.setMimeType('application/x-mpegURL')
                    listitem.setContentLookup(False)
                    if '|' in stream_url:
                        stream_url, strhdr = stream_url.split('|')
                        listitem.setProperty('inputstream.adaptive.stream_headers', strhdr)
                        if kodiver > 19:
                            listitem.setProperty('inputstream.adaptive.manifest_headers', strhdr)
                        listitem.setPath(stream_url)
                    # item = listitem  # nie wiem, czy potrzeba


            fflog("trying to start playback")

            handle = int(sys.argv[1]) if not handle else handle
            handle = handle if isinstance(handle, int) else -1
            #if "plugin" in control.infoLabel("Container.PluginName") and control.setting("hosts.mode") != "1" or int(sys.argv[1]) < 0:
            if handle < 0 or control.setting("player.dont_use_setResolvedUrl") == "true":
                fflog(f'{handle=}')
                fflog(f'not setResolved method')
                control.player.play(url, item)
            else:
                fflog(f'setResolvedUrl method')
                control.resolve(handle, True, item)

            # control.sleep(100)
            control.busy()
            control.sleep(100)
            fflog(f'waiting for player to start')
            monitor = control.monitor
            for i in (r := list(range(0, 10*90))):  # 90 sekund na rozpoczęcie odtwarzania
                if monitor.abortRequested():
                    # fflog('Kodi exit signal appeared')
                    return sys.exit()
                if self.isPlayingVideo() or not self.is_active:
                    break
                control.sleep(100)  # delay if loop
                if self.playback_started:
                    self.playback_started = None
                    if i > 0:
                        fflog(f'{i=}')
                        # fflog(f'{r=}')
                        pass
                    r += range(r[-1]+1, r[-1]+1+i)
                    if i > 0:
                        # fflog(f'{r=}')
                        pass
                    # control.busy()
                #fflog(f'waiting ... {i=}')
            # fflog(f'{i=}' + (f' (waited {round((i+1)/10,1)} sec.)' if i else ''))
            fflog(f'{i=}')
            control.idle(2)
            if not self.isPlayingVideo():
                fflog(f'nie udało się rozpocząć odtwarzania')
                import xbmcgui
                control.dialog.notification('FanFilm', 'nie udało się rozpocząć odtwarzania', xbmcgui.NOTIFICATION_ERROR, time=3000, sound=True)
                # self.stop()
                self.is_active = False
                fflog(f'exit from player script')
                return

            # if control.condVisibility('System.AddonIsEnabled(script.trakt)'):
            control.window.setProperty("script.trakt.ids", json.dumps(self.ids))  # znacznik dla wtyczki script.trakt, aby mogła rozpoznawać filmy

            self.keepPlaybackAlive()  # podtrzymywanie, aby skrypt się nie zakończył

            control.sleep(100)
            control.window.clearProperty("script.trakt.ids")

            if self.is_active:
                self.onPlayBackStopped()  # bo czasami się nie odpala (jak się za szybko klika), a ważne gdy trakt

            fflog(f'end of player script')

        except Exception:
            control.infoDialog('wystąpił jakiś błąd', heading="FanFilm Player", icon="ERROR", time=2900)
            # log("player_fail", "module")
            # fflog("player fail")
            #from ptw.debug import log_exception, fflog_exc
            fflog_exc(1)
            #return


    def getMeta(self, meta):

        if control.infoLabel('ListItem.DBID'):

            if self.content == "movie":
                meta1 = meta
                try:
                    fflog(f'[getMeta] case 2f', 1)

                    meta = control.jsonrpc(
                        '{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": {"filter":{"or": [{"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}]}, "properties" : ["title", "originaltitle", "year", "genre", "studio", "country", "runtime", "rating", "votes", "mpaa", "director", "writer", "plot", "plotoutline", "tagline", "thumbnail", "art", "file"]}, "id": 1}'
                        % (self.year, str(int(self.year) + 1), str(int(self.year) - 1))
                    )
                    # fflog(f'{meta=}')
                    meta = six.ensure_text(meta, errors="ignore")
                    meta = json.loads(meta)["result"]["movies"]
                    # fflog(f'{meta=}')
                    t1 = cleantitle.get(self.title)
                    t2 = cleantitle.get(self.originaltitle)
                    t3 = cleantitle.get(self.englishtitle)
                    # fflog(f'{t1=} {t2=} {t3=}')
                    meta = [
                        i
                        for i in meta
                        if self.year == str(i["year"])
                        and (
                            cleantitle.get(i["title"]) in [t1, t2, t3]
                            or cleantitle.get(i["originaltitle"]) in [t1, t2, t3]
                            )
                    ]
                    meta = meta[0] if meta else {}

                    for k, v in meta.items():
                        if type(v) == list:
                            try:
                                meta[k] = str(" / ".join([six.ensure_str(i) for i in v]))
                            except:
                                meta[k] = ""
                        else:
                            try:
                                meta[k] = str(six.ensure_str(v))
                            except:
                                meta[k] = str(v)

                    if not "plugin" in control.infoLabel("Container.PluginName"):
                        self.DBID = meta["movieid"]

                    #poster = thumb = meta["thumbnail"]
                    #poster = thumb = eval(meta["art"])["poster"]
                    poster = eval(meta["art"]).get("poster", "")
                    thumb = eval(meta["art"]).get("thumb", "") or poster  # or meta["thumbnail"]
                    fanart = eval(meta["art"]).get("fanart", "")
                    clearlogo = eval(meta["art"]).get("clearlogo", "")
                    clearart = eval(meta["art"]).get("clearart", "")
                    discart = eval(meta["art"]).get("discart", "")
                    keyart = eval(meta["art"]).get("keyart", "")
                    landscape = eval(meta["art"]).get("landscape", "")
                    banner = eval(meta["art"]).get("banner", "")
                    icon = eval(meta["art"]).get("icon", "") or poster

                    #return poster, thumb, "", "", "", "", "", "", "", meta
                    return poster, thumb, fanart, clearlogo, clearart, discart, keyart, landscape, banner, icon, "", meta
                except Exception:
                    fflog_exc(1)
                    meta = meta1
                    pass

            elif self.content == "episode":
                meta1 = meta
                try:
                    fflog(f'[getMeta] case 2s', 1)

                    meta = control.jsonrpc(
                        '{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "params": {"filter":{"or": [{"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}]}, "properties" : ["title", "year", "thumbnail", "art", "file"]}, "id": 1}'
                        % (self.year, str(int(self.year) + 1), str(int(self.year) - 1))
                    )
                    meta = six.ensure_text(meta, errors="ignore")
                    meta = json.loads(meta)["result"]["tvshows"]
                    # fflog(f'{meta=}')
                    t = cleantitle.get(self.title)
                    # fflog(f'{t=}')
                    t1 = cleantitle.get(self.title)
                    t2 = cleantitle.get(self.originaltitle)
                    t3 = cleantitle.get(self.englishtitle)
                    t4 = cleantitle.get(self.tvshowtitle)
                    # fflog(f'{t1=} {t2=} {t3=} {t4=}')
                    meta = [
                        i
                        for i in meta
                        if( self.year == str(i["year"])
                            and t == cleantitle.get(i["title"])
                            or cleantitle.get(i["title"]) in [t1, t2, t3, t4]
                            #or cleantitle.get(i["originaltitle"]) in [t1, t2, t3, t4]
                        )
                    ][0]

                    # fflog(f'{meta=}')
                    tvshowid = meta["tvshowid"]
                    #poster = meta["thumbnail"]  # nie wiem, czy to dobrze
                    #poster = meta["art"].get("tvshow.poster", "")
                    poster1 = meta["art"].get("poster", "")
                    fanart1 = meta["art"].get("fanart", "")
                    clearlogo1 = meta["art"].get("clearlogo", "")
                    clearart1 = meta["art"].get("clearart", "")
                    keyart1 = meta["art"].get("keyart", "")
                    landscape1 = meta["art"].get("landscape", "")
                    banner1 = meta["art"].get("banner", "")
                    icon1 = meta["art"].get("icon", "") or poster1
                    characterart1 = meta["art"].get("characterart", "")

                    meta = control.jsonrpc(
                        '{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params":{ "tvshowid": %d, "filter":{"and": [{"field": "season", "operator": "is", "value": "%s"}, {"field": "episode", "operator": "is", "value": "%s"}]}, "properties": ["title", "season", "episode", "showtitle", "firstaired", "runtime", "rating", "director", "writer", "plot", "thumbnail", "art", "file"]}, "id": 1}'
                        % (tvshowid, self.season, self.episode)
                    )
                    meta = six.ensure_text(meta, errors="ignore")
                    meta = json.loads(meta)["result"]["episodes"][0]
                    # fflog(f'{meta=}')
                    for k, v in meta.items():
                        if type(v) == list:
                            try:
                                meta[k] = str(" / ".join([six.ensure_str(i) for i in v]))
                            except:
                                meta[k] = ""
                        else:
                            try:
                                meta[k] = str(six.ensure_str(v))
                            except:
                                meta[k] = str(v)

                    if not "plugin" in control.infoLabel("Container.PluginName"):
                        self.DBID = meta["episodeid"]
                    # fflog(f'{meta=}')
                    # fflog(f'{eval(meta["art"])=}')
                    #thumb = meta["thumbnail"]
                    poster = eval(meta["art"]).get("season.poster", "") or poster1
                    thumb = eval(meta["art"]).get("thumb", "") or poster
                    fanart = eval(meta["art"]).get("season.fanart", "") or fanart1
                    clearlogo = eval(meta["art"]).get("season.clearlogo", "") or clearlogo1
                    clearart = eval(meta["art"]).get("season.clearart", "") or clearart1
                    keyart = eval(meta["art"]).get("season.keyart", "") or keyart1
                    landscape = eval(meta["art"]).get("season.landscape", "") or landscape1
                    banner = eval(meta["art"]).get("season.banner", "") or banner1
                    icon = eval(meta["art"]).get("season.icon", "") or icon1
                    characterart = eval(meta["art"]).get("season.characterart", "") or characterart1

                    #return poster, thumb, "", "", "", "", "", "", "", meta
                    # return (poster1, poster), thumb, fanart, clearlogo, clearart, "", keyart, landscape, banner, icon, characterart, meta
                    return (poster1,poster), thumb, (fanart1,fanart), clearlogo, clearart, "", keyart, (landscape1,landscape), (banner1,banner), icon, characterart, meta
                except Exception:
                    fflog_exc(1)
                    meta = meta1
                    pass

        if meta:
            try:
                fflog(f'[getMeta] case 1', 1)
                poster = meta["poster"] if "poster" in meta.keys() else ""
                poster1 = meta["tvshow.poster"] if "tvshow.poster" in meta.keys() else ""
                poster2 = meta["season.poster"] if "season.poster" in meta.keys() else ""
                thumb = meta["thumb"] if "thumb" in meta.keys() else "" or poster
                fanart = meta["fanart"] if "fanart" in meta.keys() else ""
                clearlogo = meta["clearlogo"] if "clearlogo" in meta.keys() else ""
                clearart = meta["clearart"] if "clearart" in meta.keys() else ""
                discart = meta["discart"] if "discart" in meta.keys() else ""
                keyart = meta["keyart"] if "keyart" in meta.keys() else ""
                landscape = meta["landscape"] if "landscape" in meta.keys() else ""
                banner = meta["banner"] if "banner" in meta.keys() else ""
                icon = meta["icon"] if "icon" in meta.keys() else "" or thumb
                characterart = meta["characterart"] if "characterart" in meta.keys() else ""
                if not "plugin" in control.infoLabel("Container.PluginName"):  # tylko dla zewnętrznych ?
                    # pomaga, bo jak są źle ustawione, to FF sobie je jakoś sam dobiera (pytanie, czy to tylko tak w Kodi 21 ?)
                    meta.pop("poster", None);  meta.pop("thumb", None);
                    poster = thumb = ""  # a może wszystkie czyścić ?
                if poster2:
                    poster = (poster1 or poster, poster2)
                # fflog(f'\n   {poster=} \n    {thumb=} \n   {fanart=} \n{clearlogo=} \n {clearart=} \n  {discart=} \n   {keyart=} \n{landscape=} \n   {banner=} \n     {icon=} \n{meta=}', 1)
                return poster, thumb, fanart, clearlogo, clearart, discart, keyart, landscape, banner, icon, characterart, meta
            except Exception:
                fflog_exc(1)
                meta = {}
                pass

        # fallback
        fflog(f'[getMeta] case 3', 1)
        poster, thumb, fanart, clearlogo, clearart, discart, keyart, landscape, banner, icon, characterart = (
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            #{"title": self.name},
        )
        if not meta:
            meta = {}
        if not meta.get("title"):
            meta.update({"title": self.name})

        return poster, thumb, fanart, clearlogo, clearart, discart, keyart, landscape, banner, icon, characterart, meta


    def keepPlaybackAlive(self):
        fflog('start keepPlaybackAlive method')

        pname = "%s.player.overlay" % control.addonInfo("id")
        control.window.clearProperty(pname)

        if self.content == "movie":
            overlay = playcount.getMovieOverlay(playcount.getMovieIndicators(), self.imdb)
        elif self.content == "episode":
            overlay = playcount.getEpisodeOverlay(
                                                playcount.getTVShowIndicators(),
                                                self.imdb,
                                                self.tmdb,
                                                self.season,
                                                self.episode,
                                                )
        else:
            overlay = "6"  # 6 to w trakcie (7 to obejrzany)


        if overlay == "7":  # obejrzany do konca już wcześniej był (a co jak user cofnie film?)
            while self.isPlayingVideo():
                try:
                    self.currentTime = self.getTime()
                    self.totalTime = self.getTotalTime()
                except:
                    pass
                xbmc.sleep(2000)

        elif self.content == "movie":
            while self.isPlayingVideo():
                try:
                    self.currentTime = self.getTime()
                    self.totalTime = self.getTotalTime()

                    watched = self.currentTime / self.totalTime >= 0.92  # sprawdzenie, czy "obejrzany" (jak powyżej 92%)
                    pvalue = control.window.getProperty(pname)  # odczytanie ostatniego znacznika

                    if watched == True and not pvalue == "7":
                        control.window.setProperty(pname, "7")
                        playcount.markMovieDuringPlayback(self.imdb, "7")  # ustawienie znacznika

                    elif watched == False and not pvalue == "6":
                        control.window.setProperty(pname, "6")  # ustawienie znacznika
                        playcount.markMovieDuringPlayback(self.imdb, "6")
                except:
                    pass
                xbmc.sleep(2000)

        elif self.content == "episode":
            while self.isPlayingVideo():
                try:
                    self.currentTime = self.getTime()
                    self.totalTime = self.getTotalTime()

                    watched = self.currentTime / self.totalTime >= 0.92
                    pvalue = control.window.getProperty(pname)

                    if watched == True and not pvalue == "7":
                        control.window.setProperty(pname, "7")
                        playcount.markEpisodeDuringPlayback(
                            self.imdb, None, self.season, self.episode, "7"
                        )

                    elif watched == False and not pvalue == "6":
                        control.window.setProperty(pname, "6")
                        playcount.markEpisodeDuringPlayback(
                            self.imdb, None, self.season, self.episode, "6"
                        )
                except:
                    pass
                xbmc.sleep(2000)

        fflog('end of keepPlaybackAlive method')
        control.window.clearProperty(pname)


    def libForPlayback(self):
        try:
            if self.DBID is None:
                raise Exception()

            if self.content == "movie":
                rpc = (
                    '{"jsonrpc": "2.0", "method": "VideoLibrary.SetMovieDetails", "params": {"movieid" : %s, "playcount" : 1 }, "id": 1 }'
                    % str(self.DBID)
                )
            elif self.content == "episode":
                rpc = (
                    '{"jsonrpc": "2.0", "method": "VideoLibrary.SetEpisodeDetails", "params": {"episodeid" : %s, "playcount" : 1 }, "id": 1 }'
                    % str(self.DBID)
                )
            else:
                return

            control.jsonrpc(rpc)

            if control.setting("crefresh") == "true":
                control.refresh()
        except:
            pass


    def onPlayBackStarted(self):
        fflog('playback started')
        self.playback_started = True
        #control.execute("Dialog.Close(notification,true)")
        if True:
            try:
                fflog( "# file " + self.getPlayingFile(), 0)
                # self.is_active = True  # nie wiem, czy to tu potrzebne
            except Exception:
                fflog( "# failed get what I'm playing #", 0)


    def onAVStarted(self):  # czasami dopiero po ponad 1 sekundzie odpala
        fflog('player has video and audiostream')
        #fflog(f"{self.getTotalTime()=}", 1)

        if (
            control.setting("bookmarks") == "true"
            and int(self.offset) > 120
            and self.isPlayingVideo()
            and abs(int(self.offset) - self.getTime()) > 10 # 10 sekund tolerancji
        ):
            """
            if control.setting("bookmarks.auto") == "true":  # nie ma takiego settingsu
                self.seekTime(float(self.offset))
            else:
            """
            control.execute("Dialog.Close(all,true)")
            control.sleep0(200)

            self.pause()
            control.sleep0(100)

            minutes, seconds = divmod(float(self.offset), 60)
            hours, minutes = divmod(minutes, 60)
            label = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

            label = control.lang2(12022).format(label)
            fflog('waiting for decision if continue from last point or start from begin')
            if (
                #control.setting("resume.source") == "1"  # nie ma takiego settingsu
                trakt.getTraktIndicatorsInfo()
                and trakt.getTraktCredentialsInfo() == True
            ):
                yes = control.yesnoDialog(
                    label + "[CR]  (Trakt scrobble)",
                    yeslabel=control.lang2(13404),
                    nolabel=control.lang2(12021),
                )
            else:
                yes = control.yesnoDialog(
                    label,
                    yeslabel=control.lang2(13404),
                    nolabel=control.lang2(12021),
                )

            if yes:
                minutes, seconds = divmod(float(self.offset), 60)
                hours, minutes = divmod(minutes, 60)
                #fflog(f'user decided jump to {float(self.offset)=} sec. ({(float(self.offset)/60)} min.)')
                fflog(f"user decided jump to {int(hours):02}:{int(minutes):02}:{int(seconds):02}  |  {float(self.offset)=} sec.")
                self.seekTime(float(self.offset))
                control.sleep0(200)
            self.pause()

        else:
            if self.isPlayingVideo():
                if (
                    trakt.getTraktCredentialsInfo()
                    #and control.setting("trakt.scrobble") == "true"
                    and trakt.getTraktIndicatorsInfo()
                    and self.external_scrobble_is_disabled()
                ):
                    #self.currentTime = self.getTime()
                    #self.totalTime = self.getTotalTime()
                    #fflog(f'bookmarks set_scrobble (trakt)')
                    bookmarks.set_scrobble(
                        self.currentTime,
                        #self.totalTime,
                        self.runtime or self.totalTime,
                        self.content,
                        self.imdb,
                        None,
                        self.season,
                        self.episode,
                        self.offset,
                        action="start",
                    )            
        #self.idleForPlayback()  # nie ma takiej funkcji tu


    def onPlayBackStopped(self):
        fflog('player has been stopped')  # czasami się nie chce pojawiać
        self.is_active = False

        """
        if (self.totalTime == 0
            or self.currentTime == 0
           ):
            fflog(f'nie rejestruję czasu')
            #control.sleep(1000)  # czemu taki długi czas ?
            control.sleep(100)  # eksperyment
            return  # a co z trakt ? Czy nie trzeda dać sygnału stop ? trzeba
        """
        if self.currentTime > 120:  # 2 minuty
            #fflog(f'bookmarks (re)set | {self.imdb=} {self.currentTime=}')
            bookmarks.reset(
                self.currentTime,
                self.totalTime,  # tylko do ustalenia, czy obejrzany (od 92%)
                self.content,
                self.imdb,
                self.season,
                self.episode,
            )

        # dla trakt musi pójść sygnał pause albo stop, dlatego dalsza część kodu musi być wykonana

        # rejestrację czasu w trakt wykonuje też wtyczka z repo Kodi script.trakt i może ona nadpisywać to co tu jest wysyłane (chociaż zależy od ustawień tam) 
        if (
            trakt.getTraktCredentialsInfo()
            #and control.setting("trakt.scrobble") == "true"
            and trakt.getTraktIndicatorsInfo()
            # można ewentualnie zrobić wykrywanie aktywnej takiej wtyczki i jej ustawień (tam też jest offset od ilu rejestrować), tylko wówczas jak coś zmieni się w tamtej wtyczce to tu może przestać działać, więc może lepiej niezależnie zapisywać
            #and (not external_script_trakt_enabled or int(external_scrobble_start_offset)*60 > self.currentTime and external_scrobble_movie != "true" if self.content == "movie" else external_scrobble_episode != "true") 
            and self.external_scrobble_is_disabled()
        ):
            fflog(f'\n{self.currentTime=}\n  {self.runtime=}\n{self.totalTime=}')
            #fflog(f'bookmarks set_scrobble (trakt)')
            bookmarks.set_scrobble(
                self.currentTime,
                #self.totalTime,
                self.runtime or self.totalTime,
                self.content,
                self.imdb,
                None,
                self.season,
                self.episode,
                self.offset,
            )

        if self.totalTime and float(self.currentTime / self.totalTime) >= 0.92:
            fflog(f'mark as watched (more than 92%)')
            self.libForPlayback()


    def onPlayBackEnded(self):  # materiał doszedł do końca
        fflog('playback Ended')
        self.libForPlayback()
        self.onPlayBackStopped()
        if control.setting("crefresh") == "true":
            control.refresh()


    def onPlayBackError(self):  # nie wiem, kiedy to się pojawia  # Will be called when playback stops due to an error. 
        fflog('playback ERROR')
        self.is_active = False
        #self.onPlayBackStopped()  # nie wiem, czy trzeba to ręcznie, czy Kodi sam trigernie ten callback


    def onPlayBackSeek(self, time, offset):
        fflog('playback Seek')
        if self.isPlayingVideo():
            if (
                trakt.getTraktCredentialsInfo()
                #and control.setting("trakt.scrobble") == "true"
                and trakt.getTraktIndicatorsInfo()
                and self.external_scrobble_is_disabled()
            ):
                #self.currentTime = self.getTime()  # ewentualnie (time / 1000)
                self.currentTime = time / 1000
                #self.totalTime = self.getTotalTime()
                #fflog(f'{time=} {offset=}')
                #fflog(f'{self.totalTime=} {self.currentTime=}')
                #fflog(f'bookmarks set_scrobble (trakt)')
                bookmarks.set_scrobble(
                    self.currentTime,
                    #self.totalTime,
                    self.runtime or self.totalTime,
                    self.content,
                    self.imdb,
                    None,
                    self.season,
                    self.episode,
                    self.offset,
                    action="start",
                )


    def onPlayBackResumed(self):
        fflog('playback Resumed')
        if self.isPlayingVideo():
            if (
                trakt.getTraktCredentialsInfo()
                #and control.setting("trakt.scrobble") == "true"
                and trakt.getTraktIndicatorsInfo()
                and self.external_scrobble_is_disabled()
            ):
                #self.currentTime = self.getTime()
                #self.totalTime = self.getTotalTime()
                #fflog(f'{self.totalTime=} {self.currentTime=}')
                #fflog(f'bookmarks set_scrobble (trakt)')
                bookmarks.set_scrobble(
                    self.currentTime,
                    #self.totalTime,
                    self.runtime or self.totalTime,
                    self.content,
                    self.imdb,
                    None,
                    self.season,
                    self.episode,
                    self.offset,
                    action="start",
                )


    def onPlayBackPaused(self):
        fflog('playback Paused')
        if self.isPlayingVideo():
            if (
                trakt.getTraktCredentialsInfo()
                #and control.setting("trakt.scrobble") == "true"
                and trakt.getTraktIndicatorsInfo()
                and self.external_scrobble_is_disabled()
            ):
                #self.currentTime = self.getTime()
                #self.totalTime = self.getTotalTime()
                #fflog(f'{self.totalTime=} {self.currentTime=}')
                #if self.currentTime > 
                #fflog(f'bookmarks set_scrobble (trakt)')
                bookmarks.set_scrobble(
                    self.currentTime,
                    #self.totalTime,
                    self.runtime or self.totalTime,
                    self.content,
                    self.imdb,
                    None,
                    self.season,
                    self.episode,
                    self.offset,
                )


    def external_scrobble_is_disabled(self):
        external_scrobble_is_disabled = not(trakt.getTraktAddonMovieInfo() if self.content == "movie" else trakt.getTraktAddonEpisodeInfo())
        """ bo okazało się, że już taka funkcja jest
        external_script_trakt_id = "script.trakt"
        #fflog(f'sprawdzam, cz zewnętrzna wtyczka "{external_script_trakt_id}" jest aktywna')
        #control.sleep(100)
        #external_script_trakt_exists = control.condVisibility(f"System.HasAddon({external_script_trakt_id})")
        #if external_script_trakt_exists:
        external_script_trakt_enabled = control.condVisibility(f"System.AddonIsEnabled({external_script_trakt_id})")
        if external_script_trakt_enabled:
            external_scrobble_movie = control.addon(external_script_trakt_id).getSetting("scrobble_movie")
            external_scrobble_episode = control.addon(external_script_trakt_id).getSetting("scrobble_episode")

        external_scrobble_is_disabled = (
                #not (external_script_trakt_exists and external_script_trakt_enabled)
                not external_script_trakt_enabled
                or (
                    external_scrobble_movie != "true" if self.content == "movie"
                    else external_scrobble_episode != "true"
                   )
            )
        """
        #fflog(f'{external_scrobble_is_disabled=}')
        return external_scrobble_is_disabled


    # def get_host_name(self, url):
        # """ chyba jednak nie będę używał """
        # m = re.search('https?://([A-Za-z_0-9.-]+).*', url)
        # if m:
            # return m.group(1).split('.')[-2]
        # else:
            # return ""


def time_to_seconds(time_str):
    if ':' in str(time_str):
        time_parts = time_str.split(':')
        if len(time_parts) == 3:
            hours, minutes, seconds = map(int, time_parts)
            return hours * 3600 + minutes * 60 + seconds
        elif len(time_parts) == 2:
            minutes, seconds = map(int, time_parts)
            return minutes * 60 + seconds
        else:
            raise ValueError("Nieprawidłowy format czasu.")
    else:
        # raise ValueError("Czas musi zawierać dwukropek.")
        return time_str
