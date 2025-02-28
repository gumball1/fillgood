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
try:
    import urllib.parse as urllib
except:
    pass

import re

import requests
from bs4 import BeautifulSoup

from resources.lib.indexers import navigator

from ptw.libraries import control

filmweb_url = "http://www.filmweb.pl"
result = requests.get("http://www.filmweb.pl/program-tv").content
soup = BeautifulSoup(result, "html.parser")

class channels:

    def get(self):
        generate_short_path = control.setting("generate_short_path") == "true"
        counter = 1
        for movief in soup.find_all("div", attrs={"class": "area"}):
            try:
                linkrf = movief.find("a").get("href")
                titlef = movief.find("img").get("alt").replace("plakat filmu ", "")
                yearf = linkrf.split('-')
                tvh = movief.find("div", attrs={"class": "top-5 maxlines-2 cap"}).text
                img = re.sub(r".\.jpg", "2.jpg", movief.find("img").get("src"))
                navigator.navigator().addDirectoryItem(
                    titlef + " [LIGHT][COLOR grey][I]("+str(yearf[1])+"r.)[/I][/COLOR][/LIGHT]  |  [B]"+tvh+"[/B]",
                    #"movieSearchEPG&name=%s&year=%s" % (titlef, str(yearf[1])),
                    "movieSearchEPG&item=%s" % (counter) if generate_short_path else "movieSearchEPG&name=%s&year=%s" % (titlef, str(yearf[1])),
                    img, img, )
                counter += 1
            except:
                continue

        navigator.navigator().endDirectory()
