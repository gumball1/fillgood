"""
    FanFilm Add-on
    Copyright (C) 2024 :)

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

import re
import math
from html import unescape
from urllib.parse import unquote
from datetime import datetime
import unicodedata
import requests
import xbmcgui

from ptw.libraries import cache, cleantitle, control, source_utils, PTN
from ptw.libraries.log_utils import fflog
from ptw.debug import fflog_exc

class source:
    def __init__(self):
        self.authtoken = None
        self.anime = None
        self.priority = 1
        self.language = ["pl"]
        self.domains = ["rapideo.pl"]
        self.login_url = "https://www.rapideo.pl/api/rest/login"
        self.search_url = "https://www.rapideo.pl/api/rest/search"
        self.check_url = "https://www.rapideo.pl/api/rest/files/check"
        self.files_url = "https://www.rapideo.pl/api/rest/files/get"
        self.download_url = "https://www.rapideo.pl/api/rest/files/download"
        self.req = requests
        self.user_name = control.settings.getString("rapideo.username")
        self.user_pass = control.settings.getString("rapideo.password")
        self.trash = []
        #self.trash2 = []
        self.titles = []
        self.tit_val_filt_for_one_title = None

    def login(self):
        """ logowanie w serwisie """
        self.authtoken = ""
        get_auth = cache.cache_get("rapideo_authtoken", control.sourcescacheFile)
        if get_auth is not None:
            self.authtoken = get_auth["value"]
        if self.authtoken == "":
            if self.user_name and self.user_pass:
                req = self.req.post(
                    self.login_url,
                    data={"login": self.user_name, "password": self.user_pass},
                )
                response = req.json()
                if "authtoken" in response:
                    self.authtoken = response["authtoken"]
                    cache.cache_insert("rapideo_authtoken", self.authtoken, control.sourcescacheFile)
                    return True
                if "error" in response and response["message"] != "":
                    xbmcgui.Dialog().notification("Rapideo - Błąd", str(response["message"]), xbmcgui.NOTIFICATION_ERROR)
            else:
                xbmcgui.Dialog().notification("Rapideo - Błąd", "Brak danych logowania - sprawdź ustawienia", xbmcgui.NOTIFICATION_ERROR)
        return False

    def movie(self, imdb, title, localtitle, aliases, year):
        """ szukanie filmu """
        # fflog(f'{imdb=!r} {title=!r} {localtitle=!r} {year=!r} {aliases=!r}')
        return self.search(title, localtitle, year, aliases=aliases)

    def tvshow(self, imdb, tmdb, tvshowtitle, localtvshowtitle, aliases, year):
        """ jakaś proteza pomocnicza przed szukaniem odcinka """
        # fflog(f'{imdb=!r} {tvshowtitle=!r} {localtvshowtitle=!r} {year=!r} {aliases=!r}')
        return (tvshowtitle, localtvshowtitle, aliases), year

    def episode(self, url, imdb, tmdb, title, premiered, season, episode):
        """ szukanie odcinka """
        # fflog(f'{url=!r} {imdb=!r} {tmdb=!r} {title=!r} {premiered=!r} {season=!r} {episode=!r}')
        ep_number = ("s" + season.zfill(2) + "e" + episode.zfill(2))
        return self.search(url[0][0], url[0][1], aliases=url[0][2], year=url[1], episode=ep_number, premiered=premiered)

    def search(self, title, localtitle, year="", episode="", premiered="", aliases=None, recurrency=None):
        """ pobiera wyniki z API serwisu rapideo """
        try:
            title1 = title  # przechowanie zmiennej pod inną nazwą
            year = str(year)  # dla kompatybilności, gdy zmienna jest innego typu niż string

            # ustalenie bieżącego roku - a co jak ktoś ma złą datę na urządzeniu?
            current_year = datetime.now().year
            fflog(f'{current_year=}', 0)

            if not recurrency:

                self.login()

                if aliases:
                    aliases1 = [
                                (a.get('title') or a.get('originalname') or '')+' ('+a.get('country','')+')'
                                for a in aliases
                                # if a.get('country') in ('us', 'en', 'uk', 'gb', 'au', 'pl', 'original')
                               ]
                    # fflog(f'{aliases1=!r}')
                    aliases2 = [a.rpartition(' (')[0] for a in aliases1]
                    aliases2 = [a.replace(year, "").replace("()", "").rstrip() for a in aliases2]  # year out
                    # aliases2 = [a for a in aliases2 if re.search(r"[a-z0-9]", a, flags=re.I)]  # krzaczki out
                    aliases2 = [a for a in aliases2 if not source_utils.czy_litery_krzaczki(a)]  # krzaczki out
                    aliases2 = list(dict.fromkeys(aliases2))  # pozbycie się duplikatów
                    # fflog(f'{aliases2=!r}')
                    # fflog("\nALIASY:\n "+("\n"+chr(32)).join(map(repr,aliases1))) if aliases else ''

                    self.titles = aliases2 + self.titles  # dodanie do późniejszego porównywania z nazwami plików
                    # self.titles = [cleantitle.normalize(cleantitle.getsearch(t)) for t in aliases2] + self.titles
                    self.titles = [unicodedata.normalize("NFKC", t) for t in aliases2] + self.titles  # pozwala zrobić z ⅓ -> 1⁄3
                    self.titles = [re.sub(r' ?(\d)⁄', r' \1 ', t) for t in self.titles]  # ułamki (⅓ -> 1⁄3 -> 1/3 -> "1 3")
                    self.titles = list(dict.fromkeys(self.titles))  # duplikaty out

                    # jak brak opisu polskiego, a powinien być, to by nie odrzucało filmów co w nazwie mają polski tytuł
                    self.tit_val_filt_for_one_title = (title == localtitle)

            titles = [title, localtitle]

            if not recurrency:
                self.titles = titles + self.titles
                self.titles = list(filter(None, self.titles))  # usunięcie pustych
                self.titles = list(dict.fromkeys(self.titles))  # duplikaty out

            # titles = [cleantitle.normalize(cleantitle.getsearch(t)) for t in titles]
            titles = [cleantitle.normalize(cleantitle.getsearch(t, preserve=(":"))) for t in titles]
            #titles = [unicodedata.normalize("NFKD", cleantitle.getsearch(t, preserve=(":"))) for t in titles]  # źle konwertuje
            titles = [re.sub(r' ?(\d)⁄', r' \1 ', t) for t in titles]  # na przypadek "Naga Broń 2 i 1/2"
            titles = [t.replace("&", "and") for t in titles]  # na przypadek "Dungeons & Dragons: Złodziejski honor"

            titles = list(filter(None, titles))
            titles = list(dict.fromkeys(titles))

            # dodanie do późniejszego porównywania z nazwami plików
            self.titles = titles + self.titles
            self.titles = list(dict.fromkeys(self.titles))
            # fflog(f'\n {titles=!r}')
            # fflog("\nself.titles:\n "+("\n"+chr(32)).join(map(repr,self.titles)))

            # "spirited away: w krainie bogów" -> "w krainie bogów - spirited away"
            tmp = []
            for t in self.titles:
                if ": " in t and "-" not in t:
                    temp1 = " - ".join(t.split(": ")[::-1])
                    if temp1 not in self.titles:
                        tmp += [temp1]
            self.titles += tmp

            if control.settings.getBool("sources.title_validation_filter") and control.settings.getBool("sources.title_validation_filter.rap-noprem-twlim"):
                title_validation_filter = True
            else:
                title_validation_filter = False

            # gdy wysyłany jest do api tylko numer sezonu
            episode_r = re.sub(r"(?<=\*).*", "", episode)
            episode = episode.replace("*", "")

            year_r = year if not episode else ""

            results = []

            for title in titles:
                title = title.replace(":", "")  # bo wcześniej zachowałem dwukropek przed usunięciem
                title = cleantitle.normalize(title)  # m.in. diakrytyczne na zwykłe
                zapytanie = f"{title} {year_r} {episode_r}".replace("  ", " ").strip()
                fflog(f"WYSŁANIE zapytania: {zapytanie!r}")
                data = {
                    "authtoken": self.authtoken,
                    "keyword": zapytanie,
                    "display": 100,
                    "video": True,
                    "mode": "ff",
                }
                res = self.req.post(self.search_url, data=data)
                search = res.json()
                # fflog(f'{search=!r}')

                if "error" in search and search["message"] != "":
                    cache.cache_insert("rapideo_authtoken", "", control.sourcescacheFile)
                    fflog("wystąpił błąd: " + search["message"])
                    return False

                if "search" in search:
                    search = search["search"]
                    # fflog(f'{search=!r}')
                    fflog(f'otrzymano rekordów: {len(search["search_result"])}')

                    if "search_result" in search and search["search_result"]:

                        title0 = title0_pat = ""  # na potrzeby nonlocal (patrz poniższą funkcję)

                        def _tit_pat_epis(title):
                            nonlocal title0, title0_pat

                            title0 = title
                            title0 = title0.replace(". ", " ").replace(".", " ")  # pomogło dla "Mr. Robot"
                            title0 = title0.strip()

                            title0_pat = re.escape(title0)
                            title0_pat = re.sub(r'(\d\\ )(\d\\ \d(\\ )?)', r'\1(i\\ )?\2', title0_pat)  # "Naga broń 2 i 1-2"
                            title0_pat = re.sub(r'(\d)(:?\\ )([a-zA-Z])', r'\1\2?\3', title0_pat)  # np."2 The" -> "2The"
                            title0_pat = title0_pat.replace(r"\ \-\ ", "[ ._-]+")  # ciekawe, czy to nic nie popsuje
                            title0_pat = title0_pat.replace(r"\ ", "[ ._–-]+")  # pomogło dla "Obi-Wan Kenobi"
                            title0_pat = title0_pat.replace(':', '[ _]?[:–-]?')
                            # title0_pat = title0_pat.replace(r'\&', r'(\&|and)')  # "Dungeons & Dragons: Złodziejski honor"
                            # title0_pat = source_utils.numbers_in_pattern(title0_pat)  # cyfry na słowa lub odwrotnie
                            title0_pat = source_utils.diacritics_in_pattern(title0_pat, mode=1)  # ą -> [ąa]

                            return title0_pat

                        # kolejność ważna
                        if "title2_pat" not in locals():
                            title2_pat = "(" + "|".join([_tit_pat_epis(t) for t in list(dict.fromkeys(map(str.lower,self.titles)))]) + ")"
                            # fflog("titles2_pat:\n"+"\n".join(list(dict.fromkeys(map(str.lower, self.titles)))))
                            # fflog(f"{title2_pat=!r}")
                        _tit_pat_epis(title)

                        #if not year:  # TV series (episode)
                        if episode:

                            episode_pat = re.sub(
                                r"(s\d{2})(e(\d{2,3}))",
                                r"\1[.,-]?e(\\d{2,3}-?)?e?0?\3(?!\\d)",
                                episode,
                                flags=re.I)

                            epn = int(re.search(r"e(\d{2,3})", episode).group(1)) if "e" in episode else 0
                            sn = int(re.search(r"s(\d{2})", episode).group(1)) if "s" in episode else 0
                            rang_pat = r"(?:s([\dO]{2})-?)?e(\d{2,3})-e?(\d{2,3})"
                            rang_re = re.compile(rang_pat, flags=re.I)

                            def ep_is_in_range(filename):
                                rang = rang_re.search(filename)
                                if rang:
                                    if not rang.group(1) and sn==1 or rang.group(1) and int(rang.group(1).replace('O','0'))==sn:
                                        return epn in range(int(rang.group(2)), int(rang.group(3)))
                                return None

                            # sprawdzenie, czy tytuł serialu zawiera w sobię rok
                            year_in_title = re.search(r"\b\d{4}\b", title)
                            year_in_title = year_in_title[0] if year_in_title else ""

                            def _check_base_or_premiered_year_in_filename(filename):
                                if not premiered and not year:
                                    return
                                filename = filename.replace(year_in_title, "")
                                #year_in_filename = re.findall(r"\b\d{4}\b", filename)  # też może być
                                year_in_filename = re.search(r"\b\d{4}\b", filename)
                                if year_in_filename:
                                    year_in_filename = year_in_filename[0]
                                    if 1900 <= int(year_in_filename) <= int(current_year) + 1:
                                        if premiered and (premiered.startswith(year_in_filename) or premiered.endswith(year_in_filename)) or year and str(year) == year_in_filename:
                                            return True
                                        else:
                                            return False

                            for s in search["search_result"]:

                                size = s["filesize"]

                                # jeśli w nazwie jest rok, to kontrola z datą premiery sezonu 
                                if premiered and re.search(r"\b\d{4}\b", s["filename"]):
                                    if _check_base_or_premiered_year_in_filename(s["filename"]) is False:
                                        if (
                                            #s["filename"] not in self.trash2
                                            s["filename"] not in self.trash
                                            # and not any(s["filename"] in r["filename"] for r in results)
                                           ):
                                            #self.trash2.append(s["filename"])
                                            self.trash.append(s["filename"])
                                            fflog(f'  - odrzucono z powodu niepasującego roku ({year=} {premiered=}) w nazwie {unescape(unquote(s["filename"]))!r} {size}', 0)
                                        # s.update({"trash": True})
                                        # results.append(s)
                                        continue

                                if "*" in episode_r:
                                    if re.search(episode_pat, s["filename"], flags=re.I) or ep_is_in_range(s["filename"]):
                                        # fflog(f'odcinek pasuje: {unquote(s["filename"])!r}')
                                        s["filename"] = re.sub(episode_pat+"-?e?\\d{0,3}", episode, s["filename"], flags=re.I)
                                    else:
                                        # fflog(f'niepasujący odcinek {unquote(s["filename"])!r}')
                                        continue
                                        # pass

                                # na przypadek, gdy np. szukamy e01, a otrzymaliśmy np. e010 (chodzi o cyfrę za numerem odcinka)
                                # if re.search(rf'({episode}|{episode.replace("s01","")})\d', unquote(s["filename"]), flags=re.I):
                                if not re.search(rf'\b({episode}|{episode.replace("s01","")})\b', unquote(s["filename"]), flags=re.I):
                                    # fflog(f'to nie ten odcinek! {unquote(s["filename"])!r} {episode=!r}')
                                    continue

                                if title_validation_filter:

                                    # tytuł pozyskany z nazwy pliku (jest to część przed numerem odcinka)
                                    # file_title = cleantitle.get_title(s["filename"]).rpartition(episode)[0].strip()  # wycina dużo znaków, m.in. hashe i wówczas nie szuka tytułu "#BringBackAlice"
                                    # to co wyżej, tylko za pomocą regex
                                    # if not re.search(r"s(\d{2})e(\d{2,3})", episode):
                                    if "s" not in episode:  # bez numeru sezonu
                                        file_title = (
                                            unquote(s["filename"])
                                            .replace(". ", " ")
                                            .replace(".", " ")
                                            .replace(", ", " ")
                                            .replace(",", " ")
                                            .replace("_", " ")  # choć raczej takich wyników api nie zwraca
                                            # .replace("  ", " ")  # czasami tłumaczenie jest po 2 spacjach
                                            .lower()
                                            .partition(episode)
                                        )
                                        # [0].rstrip(" /-([")
                                    else:
                                        file_title = re.split(
                                            r"\bs\d{2}[ .-]?e\d{2,3}\b",
                                            unquote(s["filename"])
                                            .replace(". ", " ")
                                            .replace(".", " ")
                                            .replace(", ", " ")
                                            .replace(",", " ")
                                            .replace("_", " ")  # choć raczej takich wyników api nie zwraca
                                            # .replace("  ", " ")  # czasami tłumaczenie jest po 2 spacjach
                                            .lower(),
                                            1
                                        )
                                        # [0].strip(" /-()")  # to samo co wyżej
                                    if file_title[0].strip(" /-()[]"):
                                        file_title = file_title[0].rstrip(" /-([")
                                    else:  # numer przed tytułem
                                        file_title = file_title[1][:-4].lstrip(" -)]")
                                    # fflog(f" {file_title=!r} ")

                                    # wycięcie rozdzielczości
                                    file_title = re.sub(
                                        r" *\b(SD|HD|UHD|2k|4k|480p?|540p?|576p?|720p?|1080[pi]?|1440p?|2160p?)\b",
                                        "",
                                        file_title)

                                    # wycięcie roku
                                    if not re.search(r" *(?<!\d)(19\d[\dOo]|[2-9][\dOo]{3})(?!\d)", title0):  # sprawdzenie, czy nie ma roku w tytule
                                        file_title = re.sub(
                                            r" *(?<!\d)(19\d[\dOo]|[2-9][\dOo]{3})(?!\d)",
                                            "",
                                            file_title,
                                            1)
                                    else:
                                        file_title = re.sub(
                                            rf"({title0_pat})(.*?)(?<!\d)(19\d[\dOo]|[2-9][\dOo]{{3}})(?!\d)",
                                            r"\1\2",
                                            file_title,
                                            1)

                                    # wycięcie pewnych fraz
                                    # (trudność polega na przewidzeniu wszystkich możliwości)
                                    file_title = re.sub(
                                        r" *\b(lektor|subbed|napisy|dubbing|polish|po?l(dub|sub)?|us|fr|de|dual|multi|p2p|web[.-]?dl|remux|3d|imax)\b",
                                        # "",
                                        lambda x: x[0] if re.search(fr"\b{re.escape(x[0])}\b", title, flags=re.I) else "",  # aby nie usuwać tych fraz, które są w tytule (np. serial Office.PL)
                                        file_title,
                                        flags=re.I)

                                    # wycięcie fraz, które są informacjami technicznymi
                                    if False:  # na razie wyłączone
                                        keywords = PTN.parse(file_title + ".fake")
                                        # fflog(f'{keywords=!r} {file_title=!r} ')
                                        keywords = [keywords[x] for x in keywords if x not in ["container", "title", "group", "episodeName", "excess", "season", "episode", "year"]]
                                        if keywords:
                                            keywords = [(x if isinstance(x, str) else "|".join(str(x))) for x in keywords]
                                            keywords = "|".join(keywords)
                                            keywords = re.sub(r"(^|\|).(?=\||$)", "", keywords).strip("| ")  # usunięcie pojedyńczych
                                            if keywords:
                                                file_title = re.sub(rf" *\b({keywords})\b", "", file_title, flags=re.I)

                                    # wycięcie nazwy jakiejś grupy uploaderów/fanów, która chyba jak jest, to na początku i w nawiasach kwadratowych
                                    file_title = re.sub(
                                        r"\[[^[\]]{3,}\]",
                                        "",
                                        file_title).lstrip(" -")

                                    # czyszczenie z nawiasów
                                    file_title = re.sub(r"\(|\[|\]|\)", "", file_title).strip()
                                    # wyczyszczenie z dziwnych znaków jak akcenty udające znaki diakrytyczne
                                    file_title = cleantitle.clean_from_unicategories(file_title)
                                    # fflog(f"{file_title=!r}")

                                # kontrola, czy dopuścić, czy odrzucić
                                if (
                                    not title_validation_filter
                                    or re.search(
                                        rf"^\d{{0,2}}\.?\W?({title2_pat}[ /-]{{0,3}})+[ -]?[0-9]?$",
                                        file_title
                                        )  # wszystkie tytuły (z aliasami włącznie)
                                    or self.tit_val_filt_for_one_title and re.search(
                                        rf"(^|[/-]|  |\d{{1,2}})\W?{title0_pat}[1-9]?$",
                                        file_title
                                        )  # tylko bieżący tytuł
                                    or re.search(
                                        rf"^\W?{title0_pat}[ -]?[0-9]?($| [/-]|  )",  # dalej może być tłumaczenie
                                        file_title
                                        )
                                    or re.search(
                                        rf"^\W?{re.escape(file_title.strip())}$",
                                        title0
                                        )  # wariant "BringBackAlice"(plik) w "#BringBackAlice"(tytuł)
                                ):
                                    if s["filename"] in self.trash:
                                        fflog(f'+Przywrócono {unescape(unquote(s["filename"]))!r} {size}')
                                        self.trash.remove(s["filename"])
                                    else:
                                        # fflog(f'Zatwierdzono {unescape(unquote(s["filename"]))!r} {size}')
                                        pass
                                    """
                                    for r in results[:]:
                                        if s == r:
                                            results.remove(r)
                                            s.pop("trash", None)
                                            break
                                    """
                                    results.append(s)

                                else:
                                    if (  # to może zaciemniać, gdy analizujemy dewelopersko
                                        s["filename"] not in self.trash
                                        and not any(s["filename"] in r["filename"] for r in results)
                                       ):
                                        self.trash.append(s["filename"])
                                        fflog(f' - odrzucono {unescape(unquote(s["filename"]))!r} {size}')
                                        # fflog(f' bo: {title0=!r}  {file_title=!r}\n')

                                    s.update({"trash": True})
                                    results.append(s)

                        else:  # movie

                            # wzorzec przydatny do sprawdzania, czy to odcinek serialu
                            # episode_pat = r"((S\d{1,2})?[.,-]?E\d{2,3}|\bcz\.|\bodc\.|\bep\.|episode|odcinek|[\(\[]\d{2,3}[\)\]]|\- \d{2,3} [([-]|\bs\d{2}\b|\b\dx\d{2}\b)"  # łapał 'Tesciowie.2.2023.PL.1080p.WEB-DL.x264.AC3-S78.mp4'
                            episode_pat = r"((S\d{1,2})?[.,-]?E\d{2,3}|\bcz\.|\bodc\.|\bep\.|episode|odcinek|[\(\[]\d{2,3}[\)\]]|\- \d{2,3} [([-]|\b\dx\d{2}\b)"
                            episode_pat = episode_pat.replace(r"\d", r"[\dO]").replace("0", "[0O]")  # czasami zamiast 0 wstawiane jest O
                            episode_uni_re = re.compile(episode_pat, flags=re.I)

                            for s in search["search_result"]:

                                size = s["filesize"]

                                if title_validation_filter:

                                    file_title = unquote(s["filename"])
                                    
                                    # sprawdzanie czy to nie odcinek serialu
                                    if re.search(r"\bs\d{2}.?e\d{2,3}\b", file_title, flags=re.I):
                                        # tego pewniaka nie warto rejestrować
                                        continue
                                    if episode_uni_re.search(file_title):
                                        fflog(f' - podejrzenie, że to serial {unescape(unquote(s["filename"]))!r} {size}')
                                        s.update({"trash": True})
                                        results.append(s)
                                        continue

                                    # tytuł pozyskany z nazwy pliku (jest to część przed rokiem)
                                    # file_title = cleantitle.get_title(s['filename']).rpartition(year)[0]
                                    # ale powyższe wycina za dużo znaków, m.in. hashe i wówczas nie szuka tytułu "#BringBackAlice"
                                    file_title = (
                                        unquote(s["filename"])
                                        .replace(". ", " ")
                                        .replace(".", " ")
                                        .replace(", ", " ")
                                        .replace(",", " ")
                                        .replace("_", " ")  # choć raczej takich wyników api nie zwraca
                                        # .replace("  ", " ")  # czasami tłumaczenie jest po 2 spacjach
                                        .replace("́", "")  # taka kreseczka ́  stosowana do polskich akcentów kiedyś
                                        .lower()
                                        .rpartition(year)
                                        # .partition(year)[0]  # założenie, że rok jest po tytule
                                        # .rstrip(" /-([")
                                        )
                                    if file_title[1]:
                                        if file_title[0].strip(" /-()[]"):
                                            file_title = file_title[0].rstrip(" /-([")
                                        else:  # rok na początku w nazwie pliku
                                            file_title = file_title[2][:-3].lstrip(" -)]").rstrip(".")
                                    else:  # brak roku w nazwie pliku (choć wyszukiwarka nie zwróci takich rekordów)
                                        file_title = file_title[0][:-3].rstrip(".")  # aby także ".ts" usuwało
                                    # fflog(f"{file_title=!r}")

                                    # wycięcie pewnych fraz
                                    # (trudność polega na przewidzeniu wszystkich możliwości)
                                    file_title = re.sub(
                                        r" *\b(lektor|subbed|napisy|dubbing|polish|po?l(dub|sub)?|us|fr|de|dual|multi|p2p|web[.-]?dl|remux|3d|imax)\b",
                                        # "",
                                        lambda x: x[0] if re.search(fr"\b{re.escape(x[0])}\b", title, flags=re.I) else "",  # aby nie usuwać tych fraz, które są w tytule (np. serial Office.PL)
                                        file_title,
                                        flags=re.I)

                                    # wycięcie fraz, które są informacjami technicznymi
                                    if False:  # na razie wyłączone
                                        keywords = PTN.parse(file_title + ".fake")
                                        # fflog(f'{keywords=!r} {file_title=!r} ')
                                        keywords = [keywords[x] for x in keywords if x not in ["container", "title", "group", "episodeName", "excess", "season", "episode", "year"]]
                                        if keywords:
                                            keywords = [(x if isinstance(x, str) else "|".join(str(x))) for x in keywords]
                                            keywords = "|".join(keywords)
                                            keywords = re.sub(r"(^|\|).(?=\||$)", "", keywords).strip("| ")  # usunięcie pojedyńczych
                                            if keywords:
                                                file_title = re.sub(rf" *\b({keywords})\b", "", file_title, flags=re.I)

                                    # wycięcie nazwy jakiejś grupy uploaderów/fanów, która chyba jak jest, to na początku i w nawiasach kwadratowych
                                    file_title = re.sub(
                                        r"\[[^[\]]{3,}\]",
                                        "",
                                        file_title).lstrip(" -")

                                    # tu jest wycinany myślnik i przecinek i znaki diakrytyczne
                                    file_title1 = cleantitle.normalize(cleantitle.getsearch(file_title))
                                    # wyczyszczenie z dziwnych znaków jak akcenty udające znaki diakrytyczne
                                    file_title = cleantitle.clean_from_unicategories(file_title)

                                # kontrola, czy dopuścić, czy odrzucić
                                if (
                                    not title_validation_filter
                                    or re.search(
                                        # rf"^\W?{title2_pat}([ /-]{title2_pat})?$",
                                        rf"^\d{{0,2}}\.?\W?({title2_pat}[ ()/-]{{0,4}})+[ -]?\d?$",
                                        file_title
                                        )
                                    or self.tit_val_filt_for_one_title and (
                                        False  # aby było łatwiej wyłączać poniższe warunki
                                        # or re.search(
                                        #     rf"^\W?{title2_pat}([ /-]{title2_pat})?$",  # tłumaczenie po spacji, slashu lub myślniku
                                        #     # rf"^\d{{0,2}}\.?\W?({title2_pat}[ /-]{{0,3}})+[ -]?[0-9]?$",
                                        #     file_title
                                        #     )
                                        or re.search(
                                            rf"(^|[/-]|  |\d{{1,2}})\W?{title0_pat}[ -]?[0-9]?$",
                                            file_title
                                            )
                                        or re.search(
                                            rf"^\W?{title0_pat}[ -]?[0-9]?($| [/-]|  )",  # dalej może być tłumaczenie
                                            file_title
                                            )
                                        or re.search(
                                            rf"^\W?{title0_pat} ?[0-9]?$",
                                            file_title1  # tu wersja z wyciętym myślnikiem i znakami diakrytycznymi
                                            )
                                        or re.search(
                                            rf"^\W?{re.escape(file_title1)}$",
                                            title0
                                            )  # wariant "BringBackAlice"(plik) w "#BringBackAlice"(tytuł)
                                        )
                                    ):
                                    if s["filename"] in self.trash:
                                        fflog(f'+Przywrócono {unescape(unquote(s["filename"]))!r} {size}')
                                        self.trash.remove(s["filename"])
                                    """
                                    for r in results[:]:
                                        if s == r:
                                            results.remove(r)
                                            s.pop("trash", None)
                                            break
                                    """
                                    results.append(s)

                                    # fflog(f' przyjęte, bo: {title0=!r}  {file_title=!r} {file_title1=!r} {title0_pat=!r}\n')
                                else:
                                    if (  # to może zaciemniać, gdy analizujemy dewelopersko
                                        s["filename"] not in self.trash
                                        and not any(s["filename"] in r["filename"] for r in results)
                                       ):
                                        self.trash.append(s["filename"])
                                        fflog(f' - odrzucono {unescape(unquote(s["filename"]))!r} {size}')
                                        # fflog(f' bo: {title0=!r}  {file_title=!r} {title2_pat=!r} {title0_pat=!r}\n')

                                    s.update({"trash": True})
                                    results.append(s)

                        # fflog(f' zatwierdzono rekordów: {len(results)} ')

                    else:
                        fflog(" Brak wyników")

            # dodatkowe akcje, jak nie ma wyników dla podstawowych zapytań
            if not recurrency:

                # wykluczania pewnych fraz
                ex_list = [re.escape(e) for e in source_utils.antifalse_filter_exceptions]
                ex_pat = f'(?:{"|".join(ex_list)})'
                if not results and re.search(ex_pat, " ".join([title1, localtitle])):
                    title2 = localtitle2 = ""
                    if re.search(rf"([_\W]+{ex_pat})", title1, flags=re.I):
                        # UWAGA: modyfikacja zmiennej "title1" - czy to dobrze?
                        title1 = title2 = re.sub(rf"([_\W]+{ex_pat})", "", title1, flags=re.I)
                    if re.search(rf"([_\W]+{ex_pat})", localtitle, flags=re.I):
                        # UWAGA: modyfikacja zmiennej "localtitle" - czy to dobrze?
                        localtitle = localtitle2 = re.sub(rf"([_\W]+{ex_pat})", "", localtitle, flags=re.I)
                    fflog("szukam ponownie po wycięciu pewnych fraz")
                    results = self.search(title2, localtitle2, year, episode, premiered, recurrency=True)

                episode0 = episode  # bo będzie modyfikowane

                # wywalenie s01, bo niektóre odcinki nie mają sezonu w nazwie
                if not results and re.search("s01", episode):
                    fflog("!Podjęcie ponownej próby z pominięciem sezonu")
                    episode = re.sub("s01", "", episode)
                    title = title1
                    results = self.search(title, localtitle, year, episode, premiered, recurrency=True)

                # przekształcenie na 3-cyfrowy numer odcinka
                if not results and re.search(r"e\d{2}(?!\d)", episode):
                    fflog("!Sprawdzenie, czy może numer odcinka jest zapisany jako 3-cyfrowy")
                    episode = re.sub(r"(s\d\d)?(e(\d\d))", r"\1e0\3", episode)
                    title = title1
                    results = self.search(title, localtitle, year, episode, premiered, recurrency=True)

                    if not results and not re.search(r"s\d{2}e\d{2,3}", episode):
                        results = self.search(title, localtitle, year, "s01"+episode, premiered, recurrency=True)

                # niektóre odcinki są łączone
                if not results and episode and "*" not in episode:
                    fflog("!Sprawdzenie, czy może odcinek jest złączony z innym")
                    episode = re.sub(r"(s\d{2})(e(\d{2,3}))", r"\1*\2", episode0)
                    title = title1
                    results = self.search(title, localtitle, year, episode, premiered, recurrency=True)

                # a może to specficzne anime
                if not results and episode and "*" in episode:
                    fflog("!Sprawdzenie, czy może odcinek nie ma E, tylko sam numer")
                    episode = re.sub("s01e", "", episode0)
                    title = title1
                    results = self.search(title, localtitle, year, episode, premiered, recurrency=True)

                if not results:

                    # próba z tytułem nieanglojęzycznym
                    originalname = [a for a in aliases if "originalname" in a]
                    originalname = originalname[0]["originalname"] if originalname else ""
                    if (
                        originalname
                        and originalname != title1
                        and originalname != localtitle
                        # and re.search(r"[a-z0-9]", originalname, flags=re.I)  # aby wykluczyć japońskie znaki
                        and not source_utils.czy_litery_krzaczki(originalname)  # aby wykluczyć japońskie znaki
                    ):
                        fflog("sprawdzenie po tytule nieanglojęzycznym")
                        episode = re.sub(r"(s\d{2})(e(\d{2,3}))", r"\1*\2", episode0)  # nie wiem, który wariant wybrać
                        results = self.search(originalname, "", year, episode, premiered, recurrency=True)

                    if year and not episode:
                        # próba z rokiem o 1 mniejszym
                        #if control.settings.getBool("sources.allow_year_less_than_base"):
                        if True:
                            fflog(f"!Podjęcie ponownej próby, lecz tym razem dla roku '{int(year)-1}' (choć wyniki mogą być błędne)")
                            results = self.search(title1, localtitle, str(int(year) - 1), episode, premiered, recurrency=True)

            if not results:
                fflog("Nie znaleziono źródeł.")
            else:
                fflog(f'Zatwierdzono rekordów: {len(results)} ')

            # wbrem pozorom warto, żeby ten fragment tu został
            if self.trash:
                self.trash = list(dict.fromkeys(self.trash))
                for item in self.trash[:]:
                    if any(item in r["filename"] and not r.get("trash") for r in results):
                        # główny cel tego fragmentu kodu
                        fflog(f"+Przywrócono {unescape(unquote(item))!r}")
                        self.trash.remove(item)

            return results
        except Exception:
            fflog_exc(1)

    def sources(self, rows, hostDict, hostprDict):
        """ przekazanie źródeł do sources.py """

        if not rows:
            fflog("Brak źródeł do przekazania")
            return None

        rows.sort(key=lambda k: bool(k.get('on_account')), reverse=True)  # aby te na koncie były najwcześniej

        filter_duplicates = control.settings.getBool("filter.duplicates")

        ilosc_smieci = 0
        sources = []
        for row in rows:
            # fflog(f'{row=}')
            try:
                size = row["filesize"]
                hosting = row["hosting"]
                filename = row["filename_long"]
                quality = source_utils.check_sd_url(filename)
                info = " | " + row["translation"]["description"]
                info = info.rstrip(" |")
                info = info + " | " + size

                # pomijanie niektórych, aby nie było dubli

                # if any(info == s["info"] and hosting == s["source"] and quality == s["quality"] for s in sources):

                # s = [s for s in sources if info == s["info"] and hosting == s["source"] and quality == s["quality"]][0]
                # fflog(f'dubel - {filename}{info} ({quality}) TEGO: {s["filename"]} {s["info"]} ({s["quality"]})')
                # fflog(f'dubel - {filename}{info} ({quality})')
                
                reject = False
                for s in sources[:]:
                    if( filter_duplicates and info == s["info"] and hosting == s["source"] and quality == s["quality"]
                        or row["url"] == s["url"]
                    ):
                        reject = True
                        if row.get("on_account") and not s.get("on_account"):
                            sources.remove(s)
                            reject = False
                        elif not row.get("trash") and s.get("trash"):
                            s.pop("trash", None)
                            ilosc_smieci -= 1
                if reject:
                    continue

                if row.get("trash"):
                    ilosc_smieci += 1

                sources.append(
                    {
                        "source": hosting,
                        "quality": quality,
                        "language": row["translation"]["language"],
                        "url": row["url"],
                        "info": info,
                        "size": size,
                        "direct": True,
                        "debridonly": False,
                        "filename": filename,
                        "on_account": row["on_account"],
                        "on_account_expires": row["on_account_expire_date"],
                        "trash": row.get("trash"),
                    }
                )
            except (KeyError, NameError) as err:
                fflog(repr(err) + f' {row=}')
                continue
        dubli = len(rows) - len(sources)
        fflog(f'wykryto dubli: {dubli}') if dubli > 0 else ""
        fflog(f'Przekazano źródeł: {len(sources)}')
        fflog(f'(W tym śmieci: {ilosc_smieci})') if ilosc_smieci > 0 else ""
        return sources

    def recalculate(self, bytes):
        """ change bytes to higher units """
        if bytes == 0:
            return "0 B"
        system = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = int(math.floor(math.log(bytes, 1024)))
        p = math.pow(1024, i)
        s = round(bytes / p, 2)
        return f"{s} {system[i]}"

    def resolve(self, url):
        """ TODO: docstring """
        try:
            # fflog(f'{url=!r}')
            self.login()
            data = {"authtoken": self.authtoken, "url": url, "mode": "ff"}
            req = self.req.post(self.files_url, data=data)
            get_files = req.json()

            if "files" in get_files:
                for file in get_files["files"]:
                    if ("url" in file and file["url"] == url and "download_url" in file and file["download_url"] != ""):
                        return str(file["download_url"])

            autorapideo = control.settings.getBool("autorapideo")

            # sprawdzenie, czy można "zakupić" (czy aktywny, czy user ma odpowiedni transfer)
            data = {"authtoken": self.authtoken, "url": url}
            req = self.req.post(self.check_url, data=data)
            check_file = req.json()
            if "file" in check_file:
                if (
                    "filesize" in check_file["file"]
                    and "filename" in check_file["file"]
                ):
                    if not autorapideo:
                        confirm = xbmcgui.Dialog().yesno(
                            "Pobieranie pliku",
                            "Pobieranie pliku "
                            + check_file["file"]["filename_full"]
                            + "\n\nOd transferu zostanie odliczone "
                            + self.recalculate(check_file["file"]["chargeuser"]),
                            yeslabel="Pobierz",
                            nolabel="Anuluj",
                        )
                        if not confirm:
                            raise Exception("Informacja", "Anulowano pobieranie pliku")
                elif "error" in check_file["file"] and "message" in check_file["file"]:
                    raise Exception("Błąd", check_file["file"]["message"])
            elif "error" in check_file and check_file["message"] != "":
                cache.cache_insert("rapideo_authtoken", "", control.sourcescacheFile)
                raise Exception("Błąd", check_file["message"])

            # próba "wypożyczenia"
            data = {"authtoken": self.authtoken, "hash": check_file["file"]["hash"], "mode": "ff", }
            add_file = self.req.post(self.download_url, data=data)
            response = add_file.json()
            if "file" in response:
                file = response["file"]
                if "url" in file:
                    # control.window.clearProperty('imdb_id')  # aby odświeżyć listę źródeł
                    control.window.setProperty('clear_SourceCache_for', control.window.getProperty('clear_SourceCache_for') + ',rapideo')  # jak ktoś używa cache źródeł
                    return str(file["url"])  # zwraca link do odtwarzania
                elif "error" in file and "message" in file:
                    raise Exception("Błąd", file["message"])
            elif "error" in check_file and check_file["message"] != "":
                cache.cache_insert("rapideo_authtoken", "", control.sourcescacheFile)
                raise Exception("Błąd", check_file["message"])

        except Exception as err:
            error, message = err.args
            xbmcgui.Dialog().notification(f"Rapideo - {error}", message, xbmcgui.NOTIFICATION_ERROR)
            # return "https://www.rapideo.pl/error.mp4"
            return None