"""
    FanFilm Add-on
    TO CHYBA JEST DODATKOWA OPCJA W PRZEOWDNIKU TV EPG (tvguide, tvchannels, tvsearch), która pozwala wyszukać dany tytuł w FanFilm
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
from kover import autoinstall  # noqa: F401

import xbmc
import urllib.parse as urllib
import re
from ptw.libraries import control

title = xbmc.getInfoLabel('Listitem.Title')
titletv = re.sub(' season$', '', title)
year = xbmc.getInfoLabel('ListItem.Year')
episode = xbmc.getInfoLabel('Listitem.Episode')
"""
generate_short_path = control.setting("generate_short_path") == "true"
if generate_short_path:
    if not episode:
        # próba, nie wiem czy to zadziała
        control.execute('Container.Update("plugin://plugin.video.fanfilm/?action=movieSearchEPG&item=%s") % (counter)' )
    # problemy:
    # - zmiana okna na Videos
    # - czy przy ActivateWindow da się potem odczytać wybrany ListItem (title, year)
    # - skąd wziąść licznik (chociaż bez tego by działało - on tylko potrzebny do powrotu)
"""
if not episode:
    title = urllib.quote_plus(title)
    control.execute("ActivateWindow(Videos,plugin://plugin.video.fanfilm/?action=movieSearchEPG&name=%s&year=%s)" % (title, year))
else:
    titletv = urllib.quote_plus(titletv)
    control.execute("ActivateWindow(Videos,plugin://plugin.video.fanfilm/?action=tvSearchterm&name=%s)" % titletv)
