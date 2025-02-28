# -*- coding: utf-8 -*-
"""
    FanFilm Project
"""

import re
from urllib.parse import parse_qs, urljoin, urlencode

import requests
from ptw.libraries import client
from ptw.libraries import source_utils


class source:
    def __init__(self):
        self.priority = 1
        self.language = ["en"]
        self.domains = ["2embed.ru"]
        self.base_link = "https://www.2embed.ru"
        self.search_link = "/embed/imdb/movie?id=%s"
        self.search_link2 = "/embed/imdb/tv?id=%s"

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            url = {"imdb": imdb, "title": title, "year": year}
            url = urlencode(url)
            return url
        except:
            return

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            url = {"imdb": imdb, "tvdb": tvdb, "tvshowtitle": tvshowtitle, "year": year}
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
            if url is None:
                return sources

            hostDict = hostprDict + hostDict

            data = parse_qs(url)
            data = dict([(i, data[i][0]) if data[i] else (i, "") for i in data])

            query = (
                "%s&s=%s&e=%s" % (data["imdb"], data["season"], data["episode"]) if "tvshowtitle" in data else "%s" % (
                data["imdb"]))
            query = re.sub("(\\\|/| -|:|\.|;|\*|\?|\"|'|<|>|\|)", " ", query)

            if "tvshowtitle" in data:
                url = self.search_link2 % query
            else:
                url = self.search_link % query
            url = urljoin(self.base_link, url)

            r = requests.get(url, headers={"User-Agent": client.agent(), "Referer": url}).text
            items = re.compile('data-id="(.+?)">.+?</a>').findall(r)

            for item in items:
                try:
                    item = "https://www.2embed.ru/ajax/embed/play?id=%s&_token=" % item
                    r2 = requests.get(item, headers={"User-Agent": client.agent(), "Referer": item}).text
                    urls = re.findall('"link":"(.+?)","sources"', r2)
                    for url in urls:

                        valid, host = source_utils.is_host_valid(url, hostDict)
                        if valid:
                            sources.append({"source": host, "quality": "720p", "language": "en", "info": "", "url": url,
                                "direct": False, "debridonly": False, })
                except:

                    pass

            return sources
        except:

            return sources

    def resolve(self, url):
        return url
