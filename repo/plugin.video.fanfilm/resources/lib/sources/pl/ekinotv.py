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
import json
import re
import requests
import urllib.parse as urlparse
import urllib.request, urllib.error, urllib.parse
from html import unescape
from ptw.libraries import cleantitle, source_utils, client, cache, control
from ptw.debug import log_exception, fflog_exc, fflog



class source:
    def __init__(self):
        self.priority = 1
        self.language = ["pl"]
        # self.domains = ["ekino-tv.pl"]  # to chyba nie jest nigdzie wykorzystywane 

        self.base_link = "https://ekino-tv.pl"
        # self.base_link = "https://ekino.ws"  # alternatywny adres
        self.search_link = "/search/qf/?q=%s"
        self.resolve_link = "/watch/f/%s/%s"

        self.year = None
        self.anime = False

        self.title_query = ""
        self.divs = ""
        self.words = []

        if control.setting("ekinotv.premium_mode") == "true":
            ekino_id = 'plugin.video.ekino-tv'
            if control.condVisibility(f"System.AddonIsEnabled({ekino_id})"):
                self.api_key = control.addon(ekino_id).getSetting("client_key")
            else:
                self.api_key = ""
            if control.setting("ekinotv.api_from_ext") == "false":
                self.api_key = ""
                if control.setting("ekinotv.client_key"):
                    self.api_key = control.setting("ekinotv.client_key")
        else:
            self.api_key = ""

    def api_connect(self, path):
        BASEURL = 'https://ekino-tv.net/api'
        url = BASEURL + path
        TIMEOUT = 40
        UA = 'kodi-agent/1.1'

        header = {'User-Agent': UA, 'API-KEY': self.api_key}
        req = urllib.request.Request(url, None, headers=header)
        control.sleep(2.1 * 1000)

        try:
            response = urllib.request.urlopen(req, timeout=TIMEOUT)
            output = response.read()
            response.close()
            return output

        except urllib.error.HTTPError as e:
            fflog(f"Wystapił jakiś problem przy pobieraniu danych  {e=}  {url=}")


    def pair_scraper(self):
        control.busy()
        control.sleep(500)
        if control.setting('ekinotv.client_key'):
            ans = control.dialog.yesnocustom(
                "UWAGA - Wykryto zapisany klucz autoryzacyjny", "\nCzy chcesz go zastąpić (wygenerować nowy),\n czy wymazać (skasować)?",
                customlabel="Skasuj",
                yeslabel="Zastąp",
                nolabel="Anuluj",
            )
            if ans < 1:
                control.idle(2)
                return
            elif ans == 2:
                control.setSetting('ekinotv.pair_status', '')
                control.setSetting('ekinotv.client_key', '')
                fflog('wymazano klucz autoryzacyjny')
                control.infoDialog('wymazano klucz autoryzacyjny od ekino')
                control.idle(2)
                return
        control.sleep(500)
        control.dialog.ok('UWAGA', f"W kolejnym oknie wprowadź [B]swój[/B] 6 cyfrowy kod \nze strony [I]po uprzednim zalogowaniu[/I] \n{self.base_link}/kodi")
        d = control.dialog.numeric(0, 'Kod ze strony')
        if d:
            api = self.api_connect("/autorize/" + d.strip())
            try:
                data = json.loads(api)
            except Exception:
                fflog(f'wystąpił jakiś błąd: {api=}')
                data = {}
            # fflog(f'{data=}', 0)
            if 'error' in data:
                control.dialog.ok('Błąd', data["error"])
                # control.setSetting('ekinotv.pair_status', '')
            else:
                control.setSetting('ekinotv.pair_status', 'sparowano')
                control.setSetting('ekinotv.client_key', data['apikey'])
                control.dialog.ok('Gotowe!', "Scraper ekinotv został sparowany z kontem.")
                control.idle(2)
                return True
        else:
            fflog('rezygnacja z parowania')
            pass
        control.idle(2)


    def contains_all_words(self, str_to_check, words):
        words = list(filter(None, words))  # usunięcie pustych elementów z listy
        if not words or not str_to_check:
            fflog(f'{words=} {str_to_check=}')
            raise Exception("Błąd", "zmienne nie mogą być puste")
        if self.anime:
            words_to_check = str_to_check.split(" ")
            for word in words_to_check:
                try:
                    liczba = int(word)
                    for word2 in words:
                        try:
                            liczba2 = int(word2)
                            if liczba != liczba2 and liczba2 != self.year and liczba != self.year:
                                return False
                        except:
                            continue
                except:
                    continue

        str_to_check = cleantitle.get_title(str_to_check).split()  # zamiana na listę
        for word in words:
            word = cleantitle.get_title(word)
            if not word:
                continue
            if not word in str_to_check:
                return False
        return True


    def contains_all_words_v2(self, str_to_check, words):
        if isinstance(words, tuple):
            for wds in words:
                ret = self.contains_all_words(str_to_check, wds)
                if ret:
                    break
        else:
            ret = self.contains_all_words(str_to_check, words)
        return ret


    def get_originaltitle(self, aliases):
        if aliases:
            originalname = [a for a in aliases if "originalname" in a]
            originalname = originalname[0]["originalname"] if originalname else ""
            # fflog(f'{originalname=}')
            originalname = "" if source_utils.czy_litery_krzaczki(originalname) else originalname
            return originalname
        return ""


    def movie(self, imdb, title, localtitle, aliases, year):
        # fflog(f'szukanie filmu {title=} {localtitle=} {year=} {aliases=}')
        return self.search(title, localtitle, self.get_originaltitle(aliases), year, "/movie/")


    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        # fflog(f'szukanie serialu {tvshowtitle=} {localtvshowtitle=} {year=} {aliases=}')
        return self.search(tvshowtitle, localtvshowtitle, self.get_originaltitle(aliases), year, "/serie/")


    def search(self, title, localtitle, originaltitle, year, search_type):
        # fflog(f'{title=} {localtitle=} {originaltitle=} {year=} {search_type=}')

        titles = [localtitle, originaltitle, title]  # ustalenie kolejności
        titles = list(filter(None, titles))  # usunięcie pustych
        titles = [t.lower() for t in titles]  # może pomóc pozbyć się duplikatów
        #titles = [t.replace("&", "&amp;") for t in titles]  # zweryfikowac, czy potrzebne
        titles = list(dict.fromkeys(titles))  # pozbycie się duplikatów

        url = None

        for title in titles:
            # fflog(f'{title=}')
            # title = cleantitle.query(title)  # tylko, że to powoduje "mufasa: król lew" na "mufasa" tylko
            # fflog(f'{title=}')
            url = self.do_search(title, year, search_type, titles)
            if url:
                break

        # czyszczenie pamięci (czy warto?)
        self.title_query = ""
        self.divs = ""  # to najwięcej zajmuje
        self.words = []

        # zwrócenie wyników
        if not url:
            # fflog("poszukiwania zakończone niepowodzeniem")
            pass
        return url


    def do_search(self, search_string, year, search_type, all_titles=None):
        if all_titles is None:
            all_titles = []

        all_titles = [cleantitle.normalize(cleantitle.getsearch(t)) for t in all_titles]
        # all_titles = list(dict.fromkeys(all_titles))  # pozbycie się duplikatów

        titles_like_link = cleantitle.geturl("-".join(all_titles))
        # titles_like_link += f"-{year}"  # bo może się różnić, jak np. dla Nocne graffiti
        titles_like_link = titles_like_link.replace("⁄", "")
        titles_like_link = titles_like_link.replace("-", "")  # bardziej uniwersalne (szczególnie dla ułamków)

        if not self.api_key:
            try:
                cookies = client.request(self.base_link, output="cookie")  # to nie psuje resolvera
                cache.cache_insert("ekino_cookie", cookies)
            except Exception:
                fflog_exc(1)

        search_titles = [ cleantitle.normalize( cleantitle.getsearch(search_string) ) ]
        # fflog(f'{search_titles=}')

        all_titles = search_titles + all_titles
        all_titles = list(dict.fromkeys(all_titles))  # ważne jest pozbycie się duplikatów
        words = []
        for title in all_titles:
            if title:
                words += [title.split(" ")]
        words = tuple(words)
        if len(words) == 1:
            words = words[0]

        dopiski_do_usuniecia = "(HD|(HD)?(CAM|TS)|DUBBING( KINO(WY)?)?|lektor|pl|eng|napisy|translator!?|IVO|(DOBRA )?(KOPIA|JAKOSC)|4K|V[2-4])"

        links = []
        for title in search_titles:  # pętla niepotrzebna, bo jest tylko 1 tytuł
            try:
                if not title:
                    continue

                if not words:
                    words = title.split(" ")

                if words == self.words:
                    continue
                self.words = words

                title_query = title
                title_query = cleantitle.query(title_query)  # czy to potrzebne?
                title_query = str.lower(urlparse.quote_plus(title_query))
                # fflog(f'{title_query=}')

                divs = []
                if not self.api_key:
                    if title_query != self.title_query:  # aby nie robić ponownego requestu jak nie trzeba
                        self.title_query = title_query
                        search_link = urlparse.urljoin(self.base_link, self.search_link) % title_query
                        # fflog(f'{search_link=}')

                        resp = requests.get(search_link, headers={"Cookie": cookies}, )  # zapytanie do serwera
                        if resp:
                            resp = resp.text
                        else:
                            fflog(f'{resp=}')
                            return

                        if "<title>Just a moment...</title>" in resp:
                            fflog(f'strona schowana obecnie za Cloudflare')
                            return

                        divs = client.parseDOM(resp, "div", attrs={"class": "movies-list-item"})
                        # fflog(f'{div=}')
                        self.divs = divs
                    else:
                        divs = self.divs  # przywrócenie poprzednio zapamiętanego
                else:
                    # search_type = search_type.replace("/", "")
                    title_query = urlparse.unquote(title_query.replace("+", " "))
                    divs = self.api_search(title_query, search_type.replace("/", ""))

                if divs is None:
                    divs = []

                # fflog(f'\n')
                for row in divs:
                    # fflog(f'{row=}')
                    # row = client.parseDOM(row, 'div', attrs={'class': 'movieDesc'})[0]  # to już chyba nieaktualne

                    if not self.api_key:
                        link = client.parseDOM(row, "a", ret="href")[0]
                        # fflog(f'{link=}')
                        if not search_type in link:
                            # fflog(f'\n')
                            continue

                        titles_found = client.parseDOM(row, "a")
                        # fflog(f'{titles_found=}')
                        title1_found = titles_found[1]
                        title2_found = titles_found[2] if len(titles_found) > 2 else ""  # jak jest, to przeważnie tytuł angielski

                    else:
                        if row.get("type") != search_type.replace("/", ""):
                            continue

                        titles_found = row.get("title")
                        titles_found = titles_found.partition(" | ")[-1].strip()

                        link = titles_found.replace(" / ", " ").replace(" ", "-")
                        if row.get("type") == "movie":
                            link += f'-{row.get("year")}' + f'-{row.get("lang")}'
                        link += f'/{row.get("id")}'
                        link = re.sub(r'-{2,}', "-", link)  # ewentualne sprzątanie
                        link = link.replace("(", "").replace(")", "")
                        link = link.translate(str.maketrans("", "", ":*?\"'\\.<>|&!,"))  # mam nadzieję, że to nie zaszkodzi
                        link = link.lower()
                        link = cleantitle.normalize(link)

                        titles_found = titles_found.split("/")
                        title1_found = titles_found[0]
                        title2_found = titles_found[-1]
                        if title2_found == title1_found:
                            title2_found = ""


                    #title1_found = title1_found.replace("&nbsp;", "")
                    title1_found = unescape(title1_found).strip()
                    title1_found = cleantitle.normalize(cleantitle.getsearch(title1_found))

                    title2_found = unescape(title2_found).strip()
                    title2_found = cleantitle.normalize(cleantitle.getsearch(title2_found))
                    
                    link_for_compare = link.split("/")[-2]
                    link_for_compare = re.sub(f"-{dopiski_do_usuniecia}", "", link_for_compare, flags=re.I)

                    # link_for_compare = re.sub(r"\d{4}-\d{4}$", "", link_for_compare)  # czy tu, czy po czyszczeniu z zadanego roku?
                    # link_for_compare = link_for_compare.replace(f"-{year}", "", 1).replace(f"-{(int(year)-1)}", "", 1) if year else link_for_compare
                    link_for_compare = re.sub(rf"-{year}(-\d{{4}})?", "", link_for_compare) if year else link_for_compare
                    link_for_compare = re.sub(rf"-{int(year)-1}(-\d{{4}})?", "", link_for_compare) if year else link_for_compare

                    link_for_compare = link_for_compare.replace("frac", "")  # ułamki
                    link_for_compare = link_for_compare.replace("-", "")
                    # fflog(f'\n  {titles_like_link=}\n  {link_for_compare=}')

                    # fflog(f' {title=}  {words=}  {title1_found=}  {title2_found=}  zadany {year=}  {search_type=}  {link=}')
                    if (
                        (
                          self.contains_all_words_v2(title1_found, words)
                          or title2_found and self.contains_all_words_v2(title2_found, words)
                        )
                        and
                        ( # dokładniejsze sprawdzenie tytułu
                          re.search(f'^{re.escape(title)}( [(-]? ?{dopiski_do_usuniecia}[,)]?)*$', title1_found, flags=re.I)
                          or title2_found and re.search(f'( / |^){re.escape(title)}( / |$)', title2_found)
                        )
                        and
                        (
                          ( year in link  or  str(int(year)-1) in link )  # dla filmów głównie
                          or search_type == "/serie/"  # seriale nie mają roku w linku
                        )
                        or link_for_compare == titles_like_link  # to pomaga, gdy wcześniejsze zawodzą (a może dać go jako pierwszy warunek?)
                       ):
                    #if link_for_compare == titles_like_link:
                        if self.api_key:
                            link = search_type + link
                        fflog(f'  pasuje {link=}')
                        # jak brak pewności, to można dodać ustaloną frazę
                        # link += "(dokosza?)"
                        if search_type == "/serie/":
                            return link  # dla seriali tylko 1
                        links.append(link)
                    
                    # fflog(f'\n')
            except Exception:
                fflog_exc(1)
                continue
        # fflog(f'{links=}')
        if not links:
            fflog(f"nic nie znaleziono dla {search_string=}")
            pass
        return links


    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        # fflog(f'szukanie odcinka {url=} {season=} {episode=}')
        if isinstance(url, list):  # na razie tak
            url = url[0]
        if not url:
            return

        if self.api_key:
            # link = url + f"+season[{season}]" + f"+episode[{episode}]"
            link = url + f"/{season}" + f"/{episode}"
            return link

        try:
            cookies = client.request(self.base_link, output="cookie")
            cache.cache_insert("ekino_cookie", cookies)

            url = urlparse.urljoin(self.base_link, url)
            # fflog(f'{url=}')
            r = requests.get(url, headers={"Cookie": cookies})  # zapytanie do serwera
            if r:
                r = r.text
            else:
                fflog(f'{r=}')
                return

            r = client.parseDOM(r, "div", attrs={"id": "list-series"})
            if r:
                r = r[0]
            else:
                return

            p = client.parseDOM(r, "p")
            try:
                index = p.index("Sezon " + season)
            except:
                fflog(f'brak sezonu {season} (może nie ten serial? bo nie informacji o roku)')
                return

            r = client.parseDOM(r, "ul")[index]
            r = client.parseDOM(r, "li")
            # fflog(f'{len(r)}')
            for row in r:
                ep_no = client.parseDOM(row, "div")[0]
                if ep_no == episode:
                    link = client.parseDOM(row, "a", ret="href")[0]
                    fflog(f' pasujący {link=}')
                    return link  # link
            fflog(f'nic nie pasuje')
            return None
        except Exception:
            fflog_exc(1)


    def api_search(self, d, mode):
        d = urlparse.quote(d)
       
        if mode == "movie":
            api = self.api_connect("/search/m/" + d.strip())
        elif mode == "serie":
            api = self.api_connect("/search/s/" + d.strip())
        else:
            api = self.api_connect("/search/" + d.strip())

        try:
            data = json.loads(api)
        except Exception:
            fflog(f'błąd: {api=}')
            data = {}

        if 'error' in data:
            fflog(f'wystąpił błąd: {data["error"]}')
        else:
            return data

    """
    def get_lang_by_type(self, lang_type):
        if lang_type:
            lang_type = lang_type[0]
            if "Lektor" in lang_type:
                return "pl", "Lektor"
            if "Dubbing" in lang_type:
                return "pl", "Dubbing"
            if "Napisy" in lang_type:
                return "pl", "Napisy"
            if "PL" in lang_type:
                return "pl", None
        return "en", None
    """

    def sources(self, links, hostDict, hostprDict):
        # fflog(f'{links=}')

        sources = []

        if links is None or not links:
            # return sources
            pass

        if links:
            if isinstance(links, str):
                links = [links]
            else:
                links = list(dict.fromkeys(links))  # pozbycie się duplikatów
            # fflog(f'{links=}')
        else:
            links = []

        #url = links[0]  # już nieaktualne
        try:
            for url in links:
                # fflog(f'{url=}')

                if not self.api_key:

                    cookies = cache.cache_get("ekino_cookie")["value"]

                    trash = url.rsplit("(dokosza?)")
                    url = trash[0]
                    trash = not trash[-1]

                    # fflog(f'{urlparse.urljoin(self.base_link, url)=}')
                    resp = requests.get(urlparse.urljoin(self.base_link, url), allow_redirects=False, headers={"Cookie": cookies}, )  # zapytanie do serwera
                    if resp:
                        resp = resp.text
                    else:
                        fflog(f'{resp=}')
                        continue

                    try:
                        rows = client.parseDOM(resp, "ul", attrs={"class": "players"})[0]
                        rows = client.parseDOM(rows, "li")
                        rows.pop()
                        rows2 = client.parseDOM(resp, "div", attrs={"role": "tabpanel"})
                    except:
                        rows = []
                        if (brak_linkow := "Ten materiał nie posiada żadnych linków") in resp:
                            fflog('brak_linkow')
                        elif (brak_linkow := " usunięty") in resp:
                            fflog('materiał usunięty')
                    # fflog(f'{len(rows)=}  {len(rows2)=}')
                    for i in range(len(rows)):
                        try:
                            row = rows[i]

                            unsure = None
                            qual = client.parseDOM(row, "img ", ret="title")
                            q = "SD"
                            if qual and "Wysoka" in qual[0]:
                                q = "HD"
                                unsure = ["quality"]
                            if qual and "4k" in qual[0]:
                                q = "4k"

                            lang_type = client.parseDOM(row, "i ", ret="title")
                            # fflog(f'{lang_type=}')
                            lang_type = lang_type[0] if lang_type else ""
                            lang, info = source_utils.get_lang_by_type(lang_type)

                            data = client.parseDOM(row, "a")[0]
                            host = data.splitlines()[0].strip()

                            trash1 = trash

                            if host.lower() == 'upzone':  # odrzucenie serwera UPZONE
                                trash1 = 'upzone'  # potrzebne do oznaczenia powodu odrzucenia
                                if trash1:
                                    # fflog(f'odrzucono źródło od UPZONE')  # resolver nie rozpoznaje domeny, bo chyba nigdy nic z tego źródła już nie działa
                                    # continue  # bo bardzo często (jak nie zawsze) "Transfer dla darmowych użytkowników został wyczerpany i jest dostępny dla użytkowników PREMIUM"
                                    pass
                                pass

                            ident = client.parseDOM(row, "a", ret="href")[0]
                            ident = ident[1:]
                            ident = ident.rsplit("-")
                            #row2 = rows2[i]  # źle gdy len(rows) != len(rows2)
                            #link = client.parseDOM(row2, "a", ret="onClick")[0]
                            links = client.parseDOM(rows2, "a", ret="onClick")
                            for link in links:
                                # if ident[0] in link and ident[1] in link:
                                if all(x in link for x in (ident[0], ident[1])):
                                    break

                            info2 = url.rsplit("/")
                            info2 = info2[-2] if "movie" in url else info2[-1]
                            # opcjonalnie
                            info2 = re.sub(rf"[.([_-]?\b(pl|napisy|dubbing|lektor)\b[.)\]_]?", "", info2, flags=re.I)
                            info2 = re.sub(r" {2,}", " ", info2).strip()

                            sources.append({"source": host,
                                            "quality": q,
                                            "language": lang,
                                            "url": link,
                                            "info": info,
                                            "direct": False,  # False oznacza, że link musi być dodatkowo wyszukany przez resolveurl
                                            "debridonly": False,  # nie jest tzw. typu "premium"
                                            "info2": info2,
                                            # "trash": trash1,
                                            })
                            if trash1:
                                sources[-1].update({"trash": trash1})
                                pass
                            if unsure:
                                sources[-1].update({"unsure": unsure})
                                pass

                        except Exception:
                            fflog_exc(1)
                            continue

                else:
                    urlp = url.strip("/").rsplit("/")

                    video_type = urlp[0]

                    if video_type == "movie":
                        video_id = urlp[-1]                        
                    else:
                        video_id = urlp[-3]
                        season = urlp[-2]
                        episode = urlp[-1]

                    if video_type == "movie":
                        api = self.api_connect("/movies/links/" + video_id)
                    else:
                        api = self.api_connect("/series/links/" + video_id + '/' + season + '/' + episode)

                    try:
                        data = json.loads(api)
                    except Exception:
                        fflog(f'wystąpił jakiś błąd: {api=}')
                        data = None
                        pass
                    # fflog(f'{data=}', 1)
                    if not isinstance(data, list):
                        continue

                    for d in data:

                        host = d.get("title")
                        lang, info = source_utils.get_lang_by_type(d.get("lang") or "")
                        link = d.get("source")

                        q = "HD"
                        if "CAM" in host:
                            q = "CAM"  # zgaduję
                        if "4K" in host:
                            q = "4K"
                        host = host.replace(f"[{q}]", "").strip()  # mało doświadczenia z tym

                        info2 = url.rsplit("/")
                        info2 = info2[-2] if "movie" in url else info2[-4] + f"-s{int(season):02}-e{int(episode):02}"

                        sources.append({"source": host,
                                        "quality": q,
                                        "language": lang,
                                        "url": link,
                                        "info": info,
                                        "direct": True,
                                        "debridonly": False,
                                        "info2": info2,
                                        "provider": " premium",
                                        })

            # fflog(f'{sources=}')
            fflog(f'przekazano źródeł: {len(sources)}')
            return sources

        except Exception:
            fflog_exc(1)
            return sources


    def resolve(self, url):
        if self.api_key:
            return url
        try:
            # fflog(f'{url=}')
            splitted = url.split("'")
            host = splitted[1]
            video_id = splitted[3]
            transl_url = urlparse.urljoin(self.base_link, self.resolve_link) % (host, video_id,)
            # fflog(f'{transl_url=}')
            cookies = cache.cache_get("ekino_cookie")
            if cookies:
                cookies = cookies.get("value") or ""
            else:
                cookies = ""
            result = requests.get(transl_url, allow_redirects=False, headers={"Cookie": cookies + "; prch=true"})  # zapytanie do serwera
            if result:
                result = result.text
            else:
                fflog(f'{result=}')
                pass
            streams = re.findall(r'href="([^"]+)"\s*target=".+?"\s*class=".+?"', result, re.DOTALL)
            if streams:
                stream = streams[0]
                stream = stream.replace("player.ekino-tv.link", "hqq.to")  # to już nieaktualne
                if "//play.ekino.link/" in stream:
                    control.sleep(100)
                    # fflog(f'{stream=}')
                    # resp = requests.get(stream, allow_redirects=True, headers={"Cookie": cookies}, )  # dodatkowe zapytanie do serwera
                    # resp = requests.get(stream)
                    resp = client.request(stream)
                    if resp:
                        # resp = resp.text
                        src = client.parseDOM(resp, "iframe", ret="src")
                        if src:
                            return src[0] + f"$${self.base_link}"
                            """
                            control.sleep(100)
                            stream = src[0]
                            resp = client.request(stream)
                            if resp:
                                src = client.parseDOM(resp, "iframe", ret="src")
                                if src:
                                    # fflog(f'{src[0]=}')
                                    return src[0] + f"$${self.base_link}"
                                else:
                                    fflog(f'brak kolejnego iframe')
                                    pass
                            else:
                                fflog(f'{resp=}')
                                pass
                            """
                    else:
                        fflog(f'{resp=}')
                        return  # a może resolver kiedyś to będzie ogarniał
                        pass
                    return
                # fflog(f'{stream=}')
                if "streamsilk." in stream:
                    # stream += f"|Referer={urlparse.quote(self.base_link)}"
                    stream += f"$${self.base_link}"
                return stream
            else:
                fflog(f'wystąpił jakiś błąd (może zabezpieczenie captcha)')
                # fflog(f'{result=}')
                pass
        except Exception:
            fflog_exc(1)
            return None
