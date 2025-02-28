"""
    FanFilm Project
"""

import re
from urllib.parse import quote

import requests
from ptw.libraries import cleantitle
from ptw.libraries import client
from ptw.libraries import source_utils, log_utils


class source:
    def __init__(self):
        self.type = None
        self.priority = 1
        self.language = ["pl"]
        self.domains = ["filmowo.club"]
        self.base_link = "https://filmowo.club/"
        self.search_link = "https://filmowo.club/search/{}"
        self.resolve_link = "https://filmowo.club/ajax/embed"
        self.session = requests.Session()
        self.headers = {'authority': 'filmowo.club',
                        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                        'accept-language': 'pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7', 'cache-control': 'max-age=0',
                        'dnt': '1', 'sec-ch-ua': '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
                        'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"', 'sec-fetch-dest': 'document',
                        'sec-fetch-mode': 'navigate', 'sec-fetch-site': 'none', 'sec-fetch-user': '?1',
                        'upgrade-insecure-requests': '1',
                        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36', }

    def search(self, title, localtitle, year, search_type):
        if not title:
            return
        try:
            url = self.do_search(cleantitle.query(title), title, localtitle, year, search_type)
            if not url:
                url = self.do_search(cleantitle.query(localtitle), title, localtitle, year, search_type)
            return url
        except:
            return

    def do_search(self, search_string, title, localtitle, year, search_type):
        titles = [cleantitle.normalize(cleantitle.getsearch(title)),
                  cleantitle.normalize(cleantitle.getsearch(localtitle)), ]
        self.type = search_type
        for title in titles:
            try:
                if not title:
                    continue
                r = self.session.get(self.search_link.format(quote(title)), headers=self.headers)
                r = client.parseDOM(r.text, "div", attrs={"class": "list-movie"})
                for row in r:
                    link = client.parseDOM(row, "a", ret="href")[0]
                    if not search_type in link:
                        continue
                    r1 = self.session.get(link, headers=self.headers)
                    if search_type == "/movie/":
                        attrs = client.parseDOM(r1.text, "div", attrs={"class": "video-attr"})
                    else:
                        attrs = client.parseDOM(r1.text, "div", attrs={"class": "featured-attr"})

                    found_year = [client.parseDOM(attr, "div", attrs={"class": "text"})[0]
                                  for attr in attrs
                                  if "Rok wydania" in client.parseDOM(attr, "div", attrs={"class": "attr"})[0]
                                 ]
                    if year == found_year[0]:
                        log_utils.fflog(f'pasuje {link=}')
                        return link
            except:
                continue

    def movie(self, imdb, title, localtitle, aliases, year):
        return self.search(title, localtitle, year, "/movie/")

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        return self.search(tvshowtitle, localtvshowtitle, year, "/serie/")

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            if url is None:
                return
            url = f"{url}-{season}-season-{episode}-episode"
            return url
        except:
            log_utils.log("filmowo - Exception", "sources")
            return

    def get_lang_by_type(self, lang_type):
        if isinstance(lang_type, list):
            lang_type = lang_type[0]
        # log_utils.fflog(f'{lang_type=}')
        if "Lektor" in lang_type:
            return "pl", "Lektor"
        if "Dubbing" in lang_type:
            return "pl", "Dubbing"
        if "Napisy" in lang_type:
            return "pl", "Napisy"
        if "PL" in lang_type:
            return "pl", None
        if "unknown" in lang_type:
            return "pl", None
        if "Oryginalna" in lang_type:
            return "en", None
        return "pl", None

    def sources(self, url, hostDict, hostprDict):
        try:
            sources = []

            if url is None:
                return sources

            host_dict = hostprDict + hostDict

            r = (self.session.get(url, timeout=10, headers=self.headers).text.replace("\r", "").replace("\n", ""))

            if self.type == "/movie/":
                s = re.search("Początek źródeł(.+?)Koniec źródeł", r).group(0)
                emb = client.parseDOM(s, "button", ret="data-embed")
                lang_list = client.parseDOM(s, "span", attrs={"class": "name"})
            else:
                emb = re.findall('href="#" data-embed="(.+?)" ', r)
                lang_list = ["unknown" for e in emb]

            # log_utils.fflog(f'{len(emb)=}')
            for e in emb:
                data = {"id": e}
                rl = self.session.post(self.resolve_link, data=data, headers=self.headers)
                link = client.parseDOM(rl.text, "iframe", ret="src")[0]
                valid, host = source_utils.is_host_valid(link, host_dict)
                if valid:
                    lang, info = self.get_lang_by_type(lang_list[emb.index(e)])
                    sources.append({"source": host,
                                    "quality": "HD",
                                    "language": lang,
                                    "url": link,
                                    "info": info,
                                    "direct": False,
                                    "debridonly": False,
                                    })
                else:
                    log_utils.fflog(f'{valid=} {host=}')
                    pass

            log_utils.fflog(f'przekazano źródeł: {len(sources)}')
            return sources
        except Exception as e:
            print("filmowo - Exception ")
            print(e)
            return sources

    def resolve(self, url):
        log_utils.fflog(f'{url=}')
        return url
