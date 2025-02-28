# -*- coding: utf-8 -*-

"""
    FanFilm Project
"""

import re
from urllib.parse import parse_qs, urlencode

from ptw.libraries import cleantitle
from ptw.libraries import client
from ptw.libraries import log_utils


class source:
    def __init__(self):
        self.priority = 1
        self.language = ["en"]
        self.domains = ["www.bnwmovies.com"]
        self.base_link = "https://bnwmovies.com"
        # self.search_link = '%s/search?q=bnwmovies.com+%s+%s'
        # self.goog = 'https://www.google.co.uk'
        self.search_link = "/?s=%s"

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            url = {"imdb": imdb, "title": title, "year": year}
            url = urlencode(url)
            return url
        except:
            log_utils.log("BNWM0 - Exception", "sources")
            return

    def sources(self, url, hostDict, hostprDict):
        sources = []
        try:
            if url is None:
                return sources

            data = parse_qs(url)
            data = dict([(i, data[i][0]) if data[i] else (i, "") for i in data])

            title = data["title"]
            year = data["year"]
            if int(year) > 1970:
                return sources

            scrape = title.lower().replace(" ", "+")

            # start_url = self.search_link %(self.goog,scrape,year)
            start_url = self.base_link + self.search_link % scrape

            html = client.request(start_url)
            posts = client.parseDOM(html, "div", attrs={"class": "post"})
            for post in posts:
                try:
                    url = client.parseDOM(post, "a", ret="href")[0]
                    if self.base_link in url:
                        if "webcache" in url:
                            continue
                        if cleantitle.geturl(title) in url:
                            html2 = client.request(url)
                            try:
                                chktitle = client.parseDOM(html2, "h1", attrs={"class": "mainh1"})[0]
                            except:
                                chktitle = re.compile("<title.+?>(.+?)</title>", re.DOTALL).findall(html2)[0]
                            if title in chktitle and year in chktitle:
                                links = client.parseDOM(html2, "source", ret="src")
                                for link in links:
                                    sources.append(
                                        {"source": "direct", "quality": "SD", "language": "en", "url": link, "info": "",
                                            "direct": True, "debridonly": False, })
                except:
                    pass
            return sources
        except:
            log_utils.log("BNWM1 - Exception", "sources")
            return sources

    def resolve(self, url):
        return url
