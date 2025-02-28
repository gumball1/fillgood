# -*- coding: UTF-8 -*-
import re
from ptw.libraries.client import parseDOM
from ptw.libraries import log_utils
from ptw.libraries import source_utils
from ptw.libraries import control
from ptw.debug import log_exception, fflog_exc, fflog
from requests.compat import urlparse
from urllib.parse import quote_plus
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class source:
    def __init__(self):
        self.priority = 1
        self.language = ["pl"]
        # self.domains = ["zaluknij.cc"]  # nie uzywane nigdzie
        self.base_link =   "https://zaluknij.cc"
        self.search_link = "https://zaluknij.cc/wyszukiwarka?phrase="
        self.useragent =  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        self.headers2 = {
            'Referer': 'https://zaluknij.cc/',
            # "Host": "zaluknij.cc",
            'user-agent': self.useragent,
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'accept-language': 'pl,en-US;q=0.7,en;q=0.3',
            # "DNT": "1",
            # "Upgrade-Insecure-Requests": "1",
            }
        self.headers2 = {}
        self.sess = requests.Session()


    def movie(self, imdb, title, localtitle, aliases, year):
        # fflog(f'{title=} {localtitle=} {year=}')
        return self.search(title, localtitle, year, 'movie', aliases)


    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        # fflog(f'{tvshowtitle=} {localtvshowtitle=} {year=}')
        return self.search(tvshowtitle, localtvshowtitle, year, 'tvshow', aliases)


    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        # fflog(f'{url=} {season=} {episode=}')
        return self.search_ep(url, season, episode)


    def search(self, title, localtitle, year, type_, aliases=None):
        try:
            if not title:
                return

            # przeważnie jest tylko polski tytuł, więc zamianka
            title, localtitle = localtitle, title

            title = title.lower()
            localtitle = localtitle.lower()

            if title == localtitle and aliases:
                originalname = [a for a in aliases if "originalname" in a]
                originalname = originalname[0]["originalname"] if originalname else ""
                originalname = "" if source_utils.czy_litery_krzaczki(originalname) else originalname
                if originalname:
                    title = originalname


            # pierwsze szukanie
            url = self.do_search(title, year, type_)

            # kolejne szukanie, jeśli poprzednie nie przyniosło rezultatu
            if not url and localtitle and localtitle != title:
                control.sleep(500)
                url = self.do_search(localtitle, year, type_)


            # i kolejne szukania, jeśli dalej brak wyniku
            # '.' na ':'
            if not url and "." in title:
                title1 = title.replace(".", ":")
                control.sleep(500)
                url = self.do_search(title1, year, type_, True)
            if not url and "." in localtitle and localtitle != title:
                localtitle1 = localtitle.replace(".", ":")
                control.sleep(500)
                url = self.do_search(localtitle1, year, type_, True)

            # "–" na "-"  i  '-' na ''
            if not url and any(m in title for m in ["–", "-"]):
                title1 = title.replace("–", "-").replace(" - ", " ")
                control.sleep(500)
                url = self.do_search(title1, year, type_, True)
            if not url and any(m in localtitle for m in ["–", "-"]) and localtitle != title:
                localtitle1 = localtitle.replace("–", "-").replace(" - ", " ")
                control.sleep(500)
                url = self.do_search(localtitle1, year, type_, True)

            # i kolejne szukania, jeśli dalej brak wyniku
            # '.' na ''
            if not url and "." in title:
                title1 = title.replace(".", "")
                control.sleep(500)
                url = self.do_search(title1, year, type_, True)
            if not url and "." in localtitle and localtitle != title:
                localtitle1 = localtitle.replace(".", "")
                control.sleep(500)
                url = self.do_search(localtitle1, year, type_, True)


            # PONIŻSZE MOGĄ DAWAĆ NIEPRAWDZIWE WYNIKI, bo nie jest sprawdzany tytuł
            if not control.settings.getBool("zaluknijcc.validate_full_title"):
                # Fix if end of title char makes a search problem
                if not url:
                    title1 = title[:-1]
                    if len(title1) > 1:
                        control.sleep(500)
                        url = self.do_search(title1, year, type_, False)
                        if url:
                            fflog('Uwaga! znaleziona pozycja może nie być tą, którą chcemy')
                            pass
                if not url and localtitle and localtitle != title:
                    localtitle1 = localtitle[:-1]
                    if len(localtitle1) > 1:
                        control.sleep(500)
                        url = self.do_search(localtitle1, year, type_, False)
                        if url:
                            fflog('Uwaga! znaleziona pozycja może nie być tą, którą chcemy')
                            pass

                # Search title phrase before ':'
                if not url and ":" in title:
                    split_title = title.split(":")[0]
                    control.sleep(500)
                    url = self.do_search(split_title, year, type_, False)
                    if url:
                        fflog('Uwaga! znaleziona pozycja może nie być tą, którą chcemy')
                        pass
                if not url and ":" in localtitle and localtitle != title:
                    split_title = localtitle.split(":")[0]
                    control.sleep(500)
                    url = self.do_search(split_title, year, type_, False)
                    if url:
                        fflog('Uwaga! znaleziona pozycja może nie być tą, którą chcemy')
                        pass


            return url
        except Exception:
            #log_exception(1)
            fflog_exc(1)
            pass


    def do_search(self, title, year, type_, validate_full_title=True):
        # print("[ZaluknijCC.py] search_title: ", title)
        fflog(f"search_title: {title!r} {type_=}")

        if not title:
            return

        fout = []
        sout = []
        results = []
        out_url = ''

        search_url = f'{self.search_link}{quote_plus(title)}'
        # fflog(f'{search_url=}')

        req = self.sess.get(search_url, headers=self.headers2, timeout=35, verify=False)
        #fflog(f'{req=} {req.status_code=}')

        if req.status_code != 200:
            fflog(f'otrzymano niestandardowy kod odpowiedzi z serwera: {req.status_code}')
            if req.status_code == 403:
                fflog(f'prawdopodobnie włączona weryfikacja cloudflare')
                # fflog(f'{req.text=}')
                return

        html = req.text

        links = parseDOM(html, 'div', attrs={'id': 'advanced-search'})
        if links:
            links = links[0]
        else:
            if "<body" not in html:
                fflog(f'{html=}', 1)
            else:
                fflog('wystąpił jakiś problem')
                fflog(f'{html=}', 0)               
            # html='Database connection could not be established.'  # też trafiłem na taki komunikat
            return

        links = parseDOM(links, 'div', attrs={'class': r'col-sm-\d+'})
        # fflog(f'{len(links)=}')

        for link in links:
            # fflog(f'{link=}')
            if 'href' in link:
                href = parseDOM(link, 'a', ret='href')[0]
                tytul = parseDOM(link, 'div', attrs={'class': 'title'})[0]
                # fflog(f'{tytul=} {href=}')

                if not validate_full_title or re.search(f'( / |^){re.escape(title)}( / |$)', tytul.lower()):
                    # pasuje tytuł
                    if 'serial-online' in href or 'seasons' in href:
                        sout.append({'title': tytul, 'url': href})
                    else:
                        fout.append({'title': tytul, 'url': href})

        if type_ == 'movie':
            results = fout
        elif type_ == 'tvshow':
            results = sout
        # fflog(f'{results=}')

        results.sort(key=lambda k: len(k['title']), reverse=True)  # najdłuższe tytuły na początek listy?
        # fflog(f'{results=}')

        if year:
            year = int(year)
            years = [year]
            if type_ == 'movie':  # czy dla seriali też trzeba ?
                years += [year-1]

        for url in results:
            if type_ == 'movie':
                date = str(url['url'])[-4:]
            elif type_ == 'tvshow':
                control.sleep(500)
                html = self.sess.get(url['url'], headers=self.headers2, timeout=35, verify=False).text
                try:
                    date = parseDOM(html, 'div', attrs={'class': 'info'})
                    date = (parseDOM(date, 'li')[-1:])[0]
                except:
                    date = "0"
            # fflog(f'{year=} {date=}')
            if year and date.isnumeric() and int(date):
                #if int(date) == int(year):
                if int(date) in years:
                    # fflog(f'pasuje {url=}')
                    out_url = url['url']
                    break
                else:
                    fflog(f'odrzucone z powodu braku dopasowania daty i roku dla {url=}')
            else:
                out_url = url['url']
                break

        fflog(f'{out_url=}') if out_url else ""
        if not validate_full_title and out_url:
            tytul = url['title']
            if date.isnumeric() and int(date):
                tytul += f" ({date})"
            return (out_url, tytul)
        return out_url


    def search_ep(self, url, season, episode):
        # fflog(f'{url=} {season=} {episode=}')
        if not url:
            return

        html = self.sess.get(url, headers=self.headers2, timeout=35, verify=False)

        if html.status_code != 200:
            fflog(f'otrzymano niestandardowy kod odpowiedzi z serwera: {html.status_code}')
            if html.status_code == 403:
                fflog(f'prawdopodobnie włączona weryfikacja cloudflare')
                # fflog(f'{req.text=}')
                return

        html = html.text

        sesres = parseDOM(html, 'ul', attrs={'id': 'episode-list'})
        if sesres:
            sesres = sesres[0]
        else:
            return

        sezony = re.findall(r'(<span>.*?</ul>)', sesres, re.DOTALL)

        episode_url = ''
        for sezon in sezony:
            sesx = parseDOM(sezon, 'span')
            ses = ''
            if sesx:
                mch = re.search(r'(\d+)', sesx[0], re.DOTALL)
                ses = mch[1] if mch else '0'
            eps = parseDOM(sezon, 'li')
            for ep in eps:
                href = parseDOM(ep, 'a', ret='href')[0]
                tyt2 = parseDOM(ep, 'a')[0]
                epis = re.findall(r's\d+e(\d+)', tyt2)[0]
                if int(ses) == int(season) and int(epis) == int(episode):
                    episode_url = href
                    break
        # fflog(f'{episode_url=}')
        return episode_url


    def sources(self, url, hostDict, hostprDict):
        # fflog(f'{url=}')
        sources = []

        if not url:
            fflog('brak źródeł do przekazania')
            return sources

        info2 = ''
        if isinstance(url, tuple):
            info2 = url[1]
            url = url[0]

        out = []
        # fflog(f'{url=}')
        control.sleep(500)
        html = self.sess.get(url, headers=self.headers2, timeout=35, verify=False).text
        result = parseDOM(html, 'tbody')
        if result:
            result = result[0]
            videos = parseDOM(result, 'tr')
            for vid in videos:
                hosthrefquallang = re.findall(r'href\s*=\s*"([^"]+).*?<td>([^<]+).*?<td>([^<]+)', vid, re.DOTALL)
                for href, lang, qual in hosthrefquallang:
                    host = urlparse(href).netloc
                    out.append({'href': href, 'host': host, 'lang': lang, 'qual': qual})
            if out:
                for x in out:
                    if (link:= x.get('href')):
                        host = x.get('host')
                        lang = x.get('lang')
                        qual = x.get('qual').lower()
                        # fflog(f'{link=}')
                        sources.append({'source': host,
                                        'quality': '720p' if qual=='wysoka' else 'CAM' if qual=='niska' else 'SD',
                                        'language': 'pl',
                                        'url': link,
                                        'info': lang,
                                        'direct': False,
                                        'debridonly': False,
                                        'info2': info2,
                                        })
        fflog(f'przekazano źródeł: {len(sources)}')
        return sources


    def resolve(self, url):
        link = str(url).replace('\\/', '/')
        link = link.replace("//", "/").replace(":/", "://")
        fflog(f'{link=}')
        return link
