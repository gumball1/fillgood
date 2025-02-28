# -*- coding: utf-8 -*-


"""
    FanFilm Project
"""

import re
from urllib.parse import parse_qs, urlencode

import requests
from ptw.libraries import client
from ptw.libraries import source_utils, log_utils


class source:
    def __init__(self):
        self.priority = 1
        self.language = ["en"]
        self.domains = ["myflixer.to"]
        self.base_link = "https://myflixer.to"
        self.search_link = "https://myflixer.to/search/{}"
        self.movie_servers = "https://myflixer.to/ajax/movie/episodes/{}"
        self.tv_seas_link = "https://myflixer.to/ajax/v2/tv/seasons/{}"
        self.tv_ep_link = "https://myflixer.to/ajax/v2/season/episodes/{}"
        self.tv_severs = "https://myflixer.to/ajax/v2/episode/servers/{}"
        self.sources_link = "https://sflix.to/ajax/get_link/{}?_token="

        self.session = requests.Session()

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            r = self.session.get(self.search_link.format(title.replace(" ", "-")))
            rlist = client.parseDOM(r.text, "div", attrs={"class": "flw-item"})
            for ritem in rlist:
                rtype = client.parseDOM(ritem, "span", attrs={"class": r".+?" + "fdi-type"})[0]
                ryear = client.parseDOM(ritem, "span", attrs={"class": "fdi-item"})[0]
                if (ryear == year) and (rtype == "Movie"):
                    ID = client.parseDOM(ritem, "a", ret="href")[0].split("-")[-1]
                    rser = self.session.get(self.movie_servers.format(ID))
                    servers = client.parseDOM(rser.text, "a", ret="data-linkid")
                    url = {"imdb": imdb, "title": title, "year": year, "servers": servers, }
                    url = urlencode(url)
                    return url
            return
        except:
            log_utils.log("myflixer - Exception", "sources")
            return

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            r = self.session.get(self.search_link.format(tvshowtitle.replace(" ", "-")))
            rlist = client.parseDOM(r.text, "div", attrs={"class": "flw-item"})
            for ritem in rlist:
                rtype = client.parseDOM(ritem, "span", attrs={"class": r".+?" + "fdi-type"})[0]
                if rtype == "TV":
                    rurl = self.base_link + client.parseDOM(ritem, "a", ret="href")[0]
                    rr = self.session.get(rurl)
                    ryear = \
                    [i for i in client.parseDOM(rr.text, "div", attrs={"class": "row-line"}) if "Released" in i][0]
                    ryear = re.search(r"[1-2][0-9]{3}", ryear).group(0)
                    if ryear == year:
                        ID = rurl.split("-")[-1]
                        url = {"imdb": imdb, "tvdb": tvdb, "tvshowtitle": tvshowtitle, "year": year, "ID": ID, }
                        url = urlencode(url)
                        return url
            return
        except:
            log_utils.log("myflixer - Exception", "sources")
            return

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            if url is None:
                return

            url = parse_qs(url)
            url = dict([(i, url[i][0]) if url[i] else (i, "") for i in url])
            url["title"], url["premiered"], url["season"], url["episode"] = (title, premiered, season, episode,)
            r = self.session.get(self.tv_seas_link.format(url["ID"]))
            seasons = client.parseDOM(r.text, "a")
            for season in seasons:
                if re.search(rf'(Series |Season ){url["season"]}', season):
                    index = seasons.index(season)
                    seasonID = client.parseDOM(r.text, "a", ret="data-id")[index]
                    rep = self.session.get(self.tv_ep_link.format(seasonID))
                    episodes = client.parseDOM(rep.text, "li")
                    for ep in episodes:
                        if re.search(f'Episode #{url["season"]}\.{url["episode"]}',
                                client.parseDOM(ep, "a", ret="title")[0], ):
                            epID = client.parseDOM(ep, "a", ret="data-id")[0]
                            rser = self.session.get(self.tv_severs.format(epID))
                            url["servers"] = client.parseDOM(rser.text, "a", ret="data-id")

            url = urlencode(url)
            return url
        except:
            log_utils.log("myflixer - Exception", "sources")
            return

    def sources(self, url, hostDict, hostprDict):
        try:
            sources = []

            if url is None:
                return sources

            host_dict = hostprDict + hostDict

            data = parse_qs(url)
            data = dict([(i, data[i][0]) if data[i] else (i, "") for i in data])

            servers = re.sub("['\[\] ]", "", data["servers"]).split(",")

            for server in servers:
                try:
                    r = self.session.get(self.sources_link.format(server)).json()
                    print(r["link"])
                    valid, host = source_utils.is_host_valid(r["link"], hostDict)
                    if valid:
                        sources.append(
                            {"source": host, "quality": "1080p", "language": "en", "info": "", "url": r["link"],
                                "direct": False, "debridonly": False, })
                except:

                    pass

            return sources
        except Exception as e:
            log_utils.log(f"myflixer - Exception {repr(e)}", "sources")

            return sources

    def resolve(self, url):
        return url
