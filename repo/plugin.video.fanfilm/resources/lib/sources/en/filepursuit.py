# -*- coding: utf-8 -*-

"""
    FanFilm Project
"""

import json
import re
from urllib.parse import parse_qs, urljoin, urlencode, quote_plus

from ptw.libraries import cleantitle
from ptw.libraries import client
from ptw.libraries import control
from ptw.libraries import source_utils


# from ptw.libraries import log_utils


class source:
    def __init__(self):
        self.title = None
        self.aliases = None
        self.hdlr = None
        self.year = None
        self.title = None
        self.priority = 1
        self.language = ["en"]
        self.base_link = "https://filepursuit.p.rapidapi.com"
        # 'https://rapidapi.com/azharxes/api/filepursuit' to obtain key
        self.search_link = "/?type=video&q=%s"

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            url = {"imdb": imdb, "title": title, "aliases": aliases, "year": year}
            url = urlencode(url)
            return url
        except:
            return

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            url = {"imdb": imdb, "tvdb": tvdb, "tvshowtitle": tvshowtitle, "aliases": aliases, "year": year, }
            url = urlencode(url)
            return url
        except:
            return

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            if url is None:
                return
            url = parse_qs(url)
            url = dict([(i, url[i][0]) if url[i] else (i, "") for i in url])
            url["title"], url["premiered"], url["season"], url["episode"] = (title, premiered, season, episode,)
            url = urlencode(url)
            return url
        except:
            return

    def sources(self, url, hostDict, hostprDict):
        sources = []
        try:
            api_key = control.setting("filepursuit.api")
            if api_key == "":
                return sources
            headers = {"x-rapidapi-host": "filepursuit.p.rapidapi.com", "x-rapidapi-key": api_key, }

            if url is None:
                return sources

            data = parse_qs(url)
            data = dict([(i, data[i][0]) if data[i] else (i, "") for i in data])

            self.title = data["tvshowtitle"] if "tvshowtitle" in data else data["title"]
            self.title = self.title.replace("&", "and").replace("Special Victims Unit", "SVU")
            self.aliases = data["aliases"]
            self.hdlr = (
                "S%02dE%02d" % (int(data["season"]), int(data["episode"])) if "tvshowtitle" in data else data["year"])
            self.year = data["year"]

            query = "%s %s" % (self.title, self.hdlr)
            query = re.sub("(\\\|/| -|:|;|\*|\?|\"|'|<|>|\|)", "", query)

            url = self.search_link % quote_plus(query)
            url = urljoin(self.base_link, url)

            r = client.request(url, headers=headers)
            r = json.loads(r)
            # log_utils.log('filepursuit resp: '+str(r))

            if "not_found" in r["status"]:
                return sources

            results = r["files_found"]
            for item in results:
                try:
                    dsize = float(item["file_size_bytes"]) / 1073741824
                    isize = "%.2f GB" % dsize
                except:
                    dsize = 0.0
                    isize = ""

                url = item["file_link"]

                try:
                    name = item["file_name"]
                except:
                    name = url.split("/")[-1]

                if any(x in name.lower() for x in ["trailer", "promo"]):
                    continue

                if not cleantitle.get(self.title) in cleantitle.get(name):
                    continue

                info = []

                quality, _ = source_utils.get_release_quality(name, url)

                info.insert(0, isize)

                info = " | ".join(info)

                sources.append(
                    {"source": "direct", "quality": quality, "language": "en", "url": url, "info": info, "direct": True,
                        "debridonly": False, "size": dsize, "name": name, })
            return sources
        except:
            return sources

    def resolve(self, url):
        return url
