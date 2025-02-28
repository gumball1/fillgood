# -*- coding: utf-8 -*-

"""
    FanFilm Project
"""

import json
from urllib.parse import urlencode, parse_qs

from ptw.libraries import cleantitle, control, source_utils, log_utils
from ptw.debug import log_exception, fflog_exc, fflog
from six import ensure_str, ensure_text


class source:
    def __init__(self):
        self.priority = 1
        self.language = ["en", "de", "fr", "gr", "ko", "pl", "pt", "ru"]
        self.domains = []


    def movie(self, imdb, title, localtitle, aliases, year):
        # fflog(f'{imdb=} {title=} {localtitle=} {year=} {aliases=}')
        try:
            originalname = [a for a in aliases if "originalname" in a]
            originalname = originalname[0]["originalname"] if originalname else ""
            return urlencode({"imdb": imdb, "title": title, "localtitle": localtitle, "originalname": originalname, "year": year})
        except Exception:
            return


    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        # fflog(f'{imdb=} {tvdb=} {tvshowtitle=} {localtvshowtitle=} {year=} {aliases=}')
        try:
            originalname = [a for a in aliases if "originalname" in a]
            originalname = originalname[0]["originalname"] if originalname else ""
            return urlencode({"imdb": imdb, "tvdb": tvdb, "tvshowtitle": tvshowtitle, "localtvshowtitle": localtvshowtitle, "originalname": originalname, "year": year, })
        except Exception:
            return


    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        # fflog(f'{url=} {imdb=} {tvdb=} {title=} {premiered=} {season=} {episode=}')
        try:
            if url is None:
                return
            url = parse_qs(url)
            url = dict([(i, url[i][0]) if url[i] else (i, "") for i in url])
            url.update({"premiered": premiered, "season": season, "episode": episode})
            # fflog(f'{url=}')
            return urlencode(url)
        except Exception:
            return


    def sources(self, url, hostDict, hostprDict):
        sources = []
        #log_utils.log(f'[library/biblioteka.py] {url=!r}', 1)
        # fflog(f'{url=}')
        try:
            if url is None:
                return sources

            data = parse_qs(url)
            data = dict([(i, data[i][0]) if data[i] else (i, "") for i in data])
            # fflog(f'{data=}')

            content_type = "episode" if "tvshowtitle" in data else "movie"

            if data.get("year"):
                years = (data["year"], str(int(data["year"]) + 1), str(int(data["year"]) - 1),)  # tuple
            else:
                fflog(f'szukanie niemożliwe z powodu braku roku')
                return sources
                # years = ("","","",)  # nie wiem, co wstawić
                
            # fflog(f'{years=}')

            if content_type == "movie":

                title = cleantitle.get(data["title"])
                localtitle = cleantitle.get(data["localtitle"])
                originalname = cleantitle.get(data.get("originalname", ""))
                # fflog(f'{title=} {localtitle=} {originalname=}')

                ids = [data["imdb"]]

                r = control.jsonrpc('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": {"filter":{"or": [{"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}]}, "properties": ["uniqueid", "imdbnumber", "title", "originaltitle", "file"]}, "id": 1}' % years)
                #fflog(f'{r=}')
                r = ensure_text(r, "utf-8", errors="ignore")
                r = json.loads(r)["result"]["movies"]
                #fflog(f'{r=}')
                r = [i
                     for i in r
                     if ((
                          str(i["imdbnumber"]) in ids  # teraz to przeważnie numer tmdb
                          or str(i.get("uniqueid",{}).get("imdb")) in ids
                          or str(i.get("uniqueid",{}).get("tmdb")) in ids
                         )
                        or (
                            localtitle in [cleantitle.get(ensure_str(i["title"])), cleantitle.get(ensure_str(i["originaltitle"])), ]
                              or title in [cleantitle.get(ensure_str(i["title"])), cleantitle.get(ensure_str(i["originaltitle"])), ]
                            or originalname and originalname in [cleantitle.get(ensure_str(i["title"])), cleantitle.get(ensure_str(i["originaltitle"])), ]
                           )
                        ) 
                    ]
                #fflog(f'{r=}')
                r = [i for i in r if not ensure_str(i["file"]).endswith(".strm")]  # nie uwzględniamy plików strm
                if r:
                    r = r[0]
                    r = control.jsonrpc('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovieDetails", "params": {'
                                        '"properties": ["streamdetails", "file"], "movieid": %s }, "id": 1}' % r["movieid"])
                    r = ensure_text(r, "utf-8", errors="ignore")
                    r = json.loads(r)["result"]["moviedetails"]
                    #fflog(f'{r=}')

            elif content_type == "episode":

                title = data["tvshowtitle"]
                localtitle = data["localtvshowtitle"]
                originalname = data.get("originalname", "")
                # fflog(f'{title=} {localtitle=} {originalname=}')

                season, episode = data["season"], data["episode"]
                # fflog(f'{season=} {episode=}')

                r = control.jsonrpc('{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "params": {"filter":{"or": [{"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}]}, "properties": ["uniqueid", "imdbnumber", "title", "originaltitle"]}, "id": 1}' % years)
                r = ensure_text(r, "utf-8", errors="ignore")
                r = json.loads(r)["result"]["tvshows"]
                # fflog(f'{r=}')
                r = [i
                    for i in r 
                    if (
                        title in (ensure_str(i["title"]))
                        or localtitle in (ensure_str(i["title"]))
                        or originalname and originalname in (ensure_str(i["originaltitle"]))
                       )
                    ]
                # fflog(f'{r=}')
                if r:
                    r = r[0]  # jest w bibliotece serial
                    # sprawdzamy, czy jest odcinek
                    r = control.jsonrpc(
                        '{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": {"filter":{"and": [{"field": "season", "operator": "is", "value": "%s"}, {"field": "episode", "operator": "is", "value": "%s"}]}, "properties": ["file"], "tvshowid": %s }, "id": 1}' % (
                            str(season), str(episode), str(r["tvshowid"])))
                    r = ensure_text(r, "utf-8", errors="ignore")
                    r = json.loads(r)["result"]["episodes"]
                    # fflog(f'{r=}')
                    r = [i for i in r if not ensure_str(i["file"]).endswith(".strm")]  # nie uwzględniamy plików strm
                    if r:
                        r = r[0]

                        r = control.jsonrpc('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodeDetails",'
                                            ' "params": {"properties": ["streamdetails", "file"],'
                                            ' "episodeid": %s }, "id": 1}' % r["episodeid"])
                        r = ensure_text(r, "utf-8", errors="ignore")
                        r = json.loads(r)["result"]["episodedetails"]
                        # fflog(f'{r=}')

            # fflog(f'{r=}')
            if r:
                url = ensure_str(r["file"])

                try:
                    qual = int(r["streamdetails"]["video"][0]["width"])
                except Exception:
                    qual = -1

                if qual >= 2160:
                    quality = "4K"
                elif 1920 <= qual < 2000:
                    quality = "1080p"
                elif 1280 <= qual < 1900:
                    quality = "720p"
                elif qual < 1280:
                    quality = "SD"

                info = []

                # odczyt pliku z dysku
                try:
                    f = control.openFile(url)
                    s = f.size()
                    f.close()
                    s = source_utils.convert_size(s)
                    # info.append(s)  # dołączane jest na końcu kodu
                except Exception:
                    pass

                try:
                    c = r["streamdetails"]["video"][0]["codec"]
                    if c == "avc1":
                        c = "h264"
                    if c == "h265":
                        c = "hevc"
                    info.append(c)
                except Exception:
                    pass

                try:
                    ac = r["streamdetails"]["audio"][0]["codec"]
                    if ac == "eac3":
                        ac = "dd+"
                    if ac == "dca":
                        ac = "dts"
                    if ac == "dtshd_ma":
                        ac = "dts-hd ma"
                    info.append(ac)
                except Exception:
                    pass

                try:
                    ach = r["streamdetails"]["audio"][0]["channels"]
                    if ach == 1:
                        ach = "mono"
                    if ach == 2:
                        ach = "2.0"
                    if ach == 6:
                        ach = "5.1"
                    if ach == 7:
                        ach = "6.1"
                    if ach == 8:
                        ach = "7.1"
                    info.append(ach)
                except Exception:
                    pass

                info = " / ".join(info)
                info = f"[{info}]"
                # info = f'{s} | [ {info} ]'  # tu dołączany jest rozmiar pliku
                info += f' | {s}'

                size = s
                
                #lang = "en"  # tak było przed zmianami
                lang = source_utils.get_lang_by_type(url)[0]  # ja dodałem detekcję

                filename = url.rpartition("/")[-1]
                filename = filename.rpartition("\\")[-1]

                sources.append({
                    "source": "",
                    "quality": quality,
                    "language": lang,
                    "url": url,
                    "info": info,
                    "size": size,
                    "local": True,
                    "direct": True,
                    "debridonly": False,
                    "filename": filename,  # opcjonalnie
                    })

            log_utils.fflog(f'przekazano źródeł: {len(sources)}')
            return sources
        except Exception:
            # log_utils.log('lib_scraper_fail', 1)
            fflog_exc(1)
            return sources


    def resolve(self, url):
        # fflog(f'{url=}')
        return url
