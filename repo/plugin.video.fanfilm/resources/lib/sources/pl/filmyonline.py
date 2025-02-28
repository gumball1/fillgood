"""
    FanFilm Add-on
    Copyright (C) 2025 :)

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


import json
import re
import requests
from ptw.libraries import source_utils, cleantitle, control

# from ptw.libraries.log_utils import fflog
from ptw.debug import fflog
# from ptw.debug import fflog_exc



class source:
    def __init__(self):
        self.priority = 1  # nie wiem do czego to, ale musi być
        self.language = ["pl"]  # określa przynależność do języka źródeł
        self.base_url = "https://filmyonline.cc"


    def get_data_from_website(self, url):
        """ pozyskuje obiekt JS ze strony internetowej """
        # fflog(f'{url}')
        html = requests.get(url)  # zapytanie do serwera
        if not html:
            fflog(f'{html=}')
            return
        html = html.text
        match = re.search(r"window\.bootstrapData = (.*?);\n", html, re.DOTALL)  # pozyskanie obiektu JS
        if match:
            data = json.loads(match[1])  # przekształcenie na słownik Pythona
            data = data.get("loaders",{})  # odfiltrowanie, co niepotrzebne
            return data
        else:
            fflog(f'jakiś błąd {html=}')


    def search(self, titles, imdb):
        """ przeszukuje listę wyników zwróconą przez wyszukiwarkę na stronie internetowej """
        titles = [t.lower() for t in titles]  # zamiana na małe litery (pomoże poniższej linijce)
        titles = list(dict.fromkeys(titles))  # pozbycie się duplikatów
        # fflog(f'{titles=}')
        # imdb = ""  # dla testów
        for title in titles:
            if not title:
                continue
            title_r = title.replace("#", "").replace("/", "／")
            url = f'{self.base_url}/search/{title_r}'
            # fflog(f'{url}')
            control.sleep(200)
            data = self.get_data_from_website(url)
            if data:
                results = data.get("searchPage",{}).get("results") or []
                # fflog(f'{len(results)=}  {title=}  {imdb=}')
                # fflog(f'{results=}')
                if imdb:
                    for r in results:
                        if r["imdb_id"] == imdb:
                            pasuje = f'{r["id"]}/{cleantitle.geturl(r["name"])}'  # czytelniejsze w logach
                            # pasuje = f'{r["id"]}/cokolwiek'  # też powinno zadzaiałać
                            # fflog(f'pasuje {self.base_url}/titles/{pasuje}')
                            return pasuje
                # imdb może być None w rekordach
                if True:
                    for r in results:
                        if r["name"].lower() in titles or r.get("original_title", "").lower() in titles:  # ewentualnie dodać szukanie w aliasach
                            pasuje = f'{r["id"]}/{cleantitle.geturl(r["name"])}'
                            fflog(f'pasuje {self.base_url}/titles/{pasuje}  (dopasowano na podstawie tytułów)')
                            return pasuje
                fflog('nie znaleziono pasujących')
            else:
                fflog(f'brak danych {data=}')



    def movie(self, imdb, title, localtitle, aliases, year):
        """ szuka filmu """
        # fflog(f'{imdb=} {title=} {localtitle=} {year=} {aliases=}')
        titles = [localtitle, self.get_originaltitle(aliases), title]
        # fflog(f'{titles=}')
        return self.search(titles, imdb)


    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        """ szuka serialu """
        # fflog(f'{tvshowtitle=} {localtvshowtitle=} {aliases=} {year=} {imdb=}')
        titles = [localtvshowtitle, self.get_originaltitle(aliases), tvshowtitle]
        return self.search(titles, imdb)


    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        """ tworzy adres do odcinka """
        # fflog(f'{url=} {imdb=} {title=} {premiered=} {season=} {episode=}')
        url += f"/season/{season}/episode/{episode}"
        return url


    def sources(self, url, hostDict, hostprDict):
        """ tworzy listę dostępnych źródeł """
        # fflog(f'{urls=}')
        sources = []
        if not url:
            fflog(f'brak źródeł')
            return sources
        url = f'{self.base_url}/titles/{url}'
        # fflog(f'{url}')
        data = self.get_data_from_website(url)
        if data:
            loaders = data  # zostało po starym kodzie (dla kompatybilności)
            if "titlePage" in loaders:
                videos = loaders.get("titlePage",{}).get("title",{}).get("videos") or []
            else:
                videos = loaders.get("episodePage",{}).get("episode",{}).get("videos") or []
            # fflog(f'{len(videos)=}  {videos=}')
            if not videos:
                # fflog('brak dostępnych źródeł')
                pass
            for u in videos:
                host = u['src'].split('//')[1].split('.')[0]
                if host != "youtube":
                    infofraza = ['LektorPL', 'DubbingPL', 'NapisyPL', 'NapisyENG', 'LektorENG']
                    info = u['name']
                    matched_frazy = []
                    for infof in infofraza:
                        if re.search(infof, info):
                            matched_frazy.append(infof)
                    if matched_frazy:
                        info = ', '.join(matched_frazy)
                    else:
                        info = ""
                    language_suffix = u['language'].upper()
                    if info.endswith(language_suffix):
                        info = info[:len(info) - len(language_suffix)]
                    # info = info.replace('  ', ' ')
                    sources.append({
                        "source": host,
                        "quality": u['quality'].upper(),
                        "language": u['language'],
                        "url": u['src'],
                        "info": info,
                        "filename": u['name'],
                        "direct": False,
                        # "direct": u['type'] != 'embed',
                        "debridonly": False,
                    })
        fflog(f'przekazano źródeł: {len(sources)}')
        return sources


    def prepare_aliases(self, aliases, year):
        """ może się przydać do dopasowywania tytułów """
        # fflog(f'{aliases=}')
        aliases1 = [
            (a.get("title") or a.get("originalname") or "")
            + " ("
            + a.get("country", "")
            + ")"
            for a in aliases
        ]
        aliases2 = [a.rpartition(" (")[0] for a in aliases1]  # country out
        aliases2 = [a.replace(year, "").replace("()", "").rstrip() for a in aliases2]  # year out
        aliases2 = [a for a in aliases2 if not source_utils.czy_litery_krzaczki(a)]  # krzaczki out
        aliases2 = [alias for i, alias in enumerate(aliases2) if alias.lower() not in [x.lower() for x in aliases2[:i]]]  # kolejne duplikaty są usuwane niezależnie od wielkości liter
        # fflog(f'{aliases2=}')
        return aliases2


    def get_originaltitle(self, aliases):
        """ wyłuskuje oryginalny tytuł z aliasów """
        if aliases:
            originalname = [a for a in aliases if "originalname" in a]
            originalname = originalname[0]["originalname"] if originalname else ""
            # fflog(f'{originalname=}')
            originalname = "" if source_utils.czy_litery_krzaczki(originalname) else originalname  # odrzuca, gdy tytuł oryginalny nie jest zapisany literami łacińskimi
            return originalname
        return ""


    def resolve(self, link):
        """ przekazuje link do odtwarzania (który przejdzie jeszcze przez Resolver'a) """
        # fflog(f'{link=}')
        return link
