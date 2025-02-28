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
import os
import re
import shutil
import zipfile

import requests

import urllib3  # potrzebne, aby poniższa linijka zadziałała
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs


class PtwModuleChecker:
    def __init__(self):
        self.addonName = "script.module.ptw"
        self.LocalVersion = self.getInstalledPtwModuleVersion()
        self.ptwModuleLink = "https://raw.githubusercontent.com/fanfilm/repository.fanfilm/master/zips19/addons.xml"
        self.OfficialVersion = self.getOfficialPtwModuleVersion()
        self.ptwModuleLinkZip = f"https://github.com/fanfilm/repository.fanfilm/raw/master/zips19/{self.addonName}/{self.addonName}-{self.OfficialVersion}.zip"

    def getOfficialPtwModuleVersion(self):
        try:
            content = requests.get(self.ptwModuleLink, verify=False, timeout=10).text
            ptwModuleUrlVersion = re.findall(r"PTW Module\" version=\"(.*?)\"", content)[0]
            xbmc.log(f"[checker]   {ptwModuleUrlVersion=}")
            return ptwModuleUrlVersion
        except Exception as e:
            xbmc.log(f"[checker] {e}", 0)
            xbmc.log( "[checker] Can't get PTW version from official repo", xbmc.LOGERROR, )
            return

    def getInstalledPtwModuleVersion(self):
        try:
            self.setPtwModule(enabled=True)
            ptwModuleAddon = xbmcaddon.Addon(self.addonName)
            ptwModuleAddonVersion = ptwModuleAddon.getAddonInfo("version")
            xbmc.log(f"[checker] {ptwModuleAddonVersion=}")
            return ptwModuleAddonVersion
        except Exception as e:
            xbmc.log(f"[checker] {e}", 0)
            xbmc.log( "[checker] Can't get PTW version from kodi installation", xbmc.LOGERROR, )
            return "0.0.0"

    def checkVersion(self):
        if self.OfficialVersion and tuple(self.LocalVersion.split(".")) < tuple(self.OfficialVersion.split(".")):
            dialog = xbmcgui.Dialog()
            ret = dialog.yesno("Niekompatybilna wersja zależności",
                "Czy chcesz zaktualizować zależność PTW Module do najnowszej wersji? Aktualna wersja jest niezbędna do prawidłowego działania FanFilm. Będzie to wymagać ponownego uruchomienia Kodi", )
            if ret:
                self.installPtwModule()

    def removePtwModule(self):
        addonPath = xbmcvfs.translatePath("special://home/addons/script.module.ptw")
        if os.path.isdir(addonPath):
            self.setPtwModule(enabled=False)
            xbmc.log("[checker] Usunięcie obecnego dodatku script.module.ptw z dysku")
            shutil.rmtree(addonPath, ignore_errors=True)

    def installPtwModule(self):
        xbmc.log("[checker] Przygotowanie do instalacji nowego dodatku script.module.ptw")
        unzipPath = xbmcvfs.translatePath("special://home/addons/")
        zipPath = self.download_file(self.ptwModuleLinkZip)
        if zipPath:
            self.removePtwModule()
            self.unzip_addon(zipPath, unzipPath)
            self.closeKodi()

    def download_file(self, url):
        xbmc.log("[checker] Pobieranie pliku instalacyjnego dodatku script.module.ptw")
        try:
            localFileName = url.split("/")[-1]
            addonsDirectory = xbmcvfs.translatePath("special://home/addons/")
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(os.path.join(addonsDirectory, localFileName), "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            return os.path.join(addonsDirectory, localFileName)
        except Exception as e:
            xbmc.log(f"[checker] {e}", xbmc.LOGERROR)
            xbmc.log( "[checker] Downloading addon fails", 1)
            return False

    def unzip_addon(self, path_to_zip_file, directory_to_extract_to):
        xbmc.log("[checker] Rozpakowanie pobranego pliku zip dodatku script.module.ptw")
        try:
            if not os.path.exists(directory_to_extract_to):
                os.makedirs(directory_to_extract_to)
            with zipfile.ZipFile(path_to_zip_file, "r") as zip_ref:
                zip_ref.extractall(directory_to_extract_to)
            self.removeZipFile()
        except Exception as e:
            xbmc.log(f"[checker] {e}", xbmc.LOGERROR)
            xbmc.log( "[checker] Unpacking addon fails", 1)
            return False

    def removeZipFile(self):
        xbmc.log("[checker] Usunięcie pobranego pliku instalacyjnego dodatku script.module.ptw", 1)
        zipFilePath = xbmcvfs.translatePath(f"special://home/addons/script.module.ptw-{self.OfficialVersion}.zip")
        os.remove(zipFilePath)

    def closeKodi(self):
        xbmc.sleep(200)
        try:
            self.setPtwModule(enabled=True)
        except Exception:
            pass
        choice = xbmcgui.Dialog().ok("Zamknięcie", "Teraz Kodi zostanie zamknięte, aby zatwierdzić zmiany")
        if choice == 1:
            xbmc.log("[checker] Kodi zostanie zamknięte (PtwModuleChecker)")
            os._exit(1)
        else:
            xbmc.executebuiltin("Action(Close)")

    def setPtwModule(self, enabled=True):
        if enabled:
            xbmc.log("[checker] Włączenie (jeśli nie włączony) dodatku script.module.ptw")
            xbmc.executeJSONRPC(
                f'{{"jsonrpc":"2.0","method":"Addons.SetAddonEnabled","id":7,"params":{{"addonid": "{self.addonName}","enabled":true}}}}')
        else:
            xbmc.log("[checker] WYłączenie dodatku script.module.ptw")
            xbmc.executeJSONRPC(
                f'{{"jsonrpc":"2.0","method":"Addons.SetAddonEnabled","id":7,"params":{{"addonid": "{self.addonName}","enabled":false}}}}')


class ResolveUrlChecker:
    def __init__(self):
        self.addonName = "script.module.resolveurl"
        self.LocalVersion = self.getInstalledResolveUrlVersion()
        self.resolveUrlLink = ("https://raw.githubusercontent.com/Gujal00/smrzips/master/addons.xml")
        self.OfficialVersion = self.getOfficialResolveUrlVersion()
        self.resolveUrlLinkZip = f"https://raw.githubusercontent.com/Gujal00/smrzips/master/zips/{self.addonName}/{self.addonName}-{self.OfficialVersion}.zip"

    def getOfficialResolveUrlVersion(self):
        try:
            content = requests.get(self.resolveUrlLink, verify=False, timeout=10).text
            resolveUrlVersion = re.findall(r"ResolveURL\" version=\"(.*?)\"", content)[0]
            xbmc.log(f"[checker]      {resolveUrlVersion=}")
            return resolveUrlVersion
        except Exception as e:
            xbmc.log(f"[checker] {e}", 0)
            xbmc.log( "[checker] Can't get resolveUrl version from official repo", xbmc.LOGERROR, )
            return

    def getInstalledResolveUrlVersion(self):
        try:
            self.setResolveUrl(enabled=True)
            resolveUrlAddon = xbmcaddon.Addon(self.addonName)
            resolveUrlAddonVersion = resolveUrlAddon.getAddonInfo("version")
            xbmc.log(f"[checker] {resolveUrlAddonVersion=}")
            return resolveUrlAddonVersion
        except Exception as e:
            xbmc.log(f"[checker] {e}", 0)
            xbmc.log( "[checker] Can't get resolveUrl version from kodi installation", xbmc.LOGERROR, )
            return "0.0.0"

    def checkVersion(self):
        if self.OfficialVersion and self.LocalVersion != self.OfficialVersion:
            dialog = xbmcgui.Dialog()
            ret = dialog.yesno("Niekompatybilna wersja zależności",
                "Chcesz zaktulizować zależność ResolveURL do najnowszej wersji? Będzie to wymagać ponownego uruchomienia Kodi", )
            if ret:
                self.installResolveUrl()

    def removeResolveUrl(self):
        addonPath = xbmcvfs.translatePath("special://home/addons/script.module.resolveurl")
        if os.path.isdir(addonPath):
            self.setResolveUrl(enabled=False)
            xbmc.log("[checker] Usunięcie obecnego dodatku script.module.resolveurl z dysku")
            shutil.rmtree(addonPath, ignore_errors=True)

    def installResolveUrl(self):
        xbmc.log("[checker] Przygotowanie do instalacji nowego dodatku script.module.resolveurl")
        unzipPath = xbmcvfs.translatePath("special://home/addons/")
        zipPath = self.download_file(self.resolveUrlLinkZip)
        if zipPath:
            self.removeResolveUrl()
            stat = self.unzip_addon(zipPath, unzipPath)
            self.closeKodi()

    def download_file(self, url):
        xbmc.log("[checker] Pobieranie pliku instalacyjnego dodatku script.module.resolveurl")
        try:
            localFileName = url.split("/")[-1]
            addonsDirectory = xbmcvfs.translatePath("special://home/addons/")
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(os.path.join(addonsDirectory, localFileName), "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            return os.path.join(addonsDirectory, localFileName)
        except Exception as e:
            xbmc.log(f"[checker] {e}", xbmc.LOGERROR)
            xbmc.log( "[checker] Downloading addon fails", 1)
            return False

    def unzip_addon(self, path_to_zip_file, directory_to_extract_to):
        xbmc.log("[checker] Rozpakowanie pobranego pliku zip dodatku script.module.resolveurl")
        try:
            if not os.path.exists(directory_to_extract_to):
                os.makedirs(directory_to_extract_to)
            with zipfile.ZipFile(path_to_zip_file, "r") as zip_ref:
                zip_ref.extractall(directory_to_extract_to)
            self.removeZipFile()
        except Exception as e:
            xbmc.log(f"[checker] {e}", xbmc.LOGERROR)
            xbmc.log("[checker] Unpacking addon fails", 1)
            return False

    def removeZipFile(self):
        xbmc.log("[checker] Usunięcie pobranego pliku instalacyjnego dodatku script.module.resolveurl", 1)
        zipFilePath = xbmcvfs.translatePath(f"special://home/addons/script.module.resolveurl-{self.OfficialVersion}.zip")
        os.remove(zipFilePath)

    def closeKodi(self):
        xbmc.sleep(200)
        try:
            self.setResolveUrl(enabled=True)
        except Exception:
            pass
        choice = xbmcgui.Dialog().ok("Zamknięcie", "Teraz Kodi zostanie zamknięte, aby zatwierdzić zmiany")
        if choice == 1:
            xbmc.log("[checker] Kodi zostanie zamknięte (ResolveUrlChecker)")
            os._exit(1)
        else:
            xbmc.executebuiltin("Action(Close)")

    def setResolveUrl(self, enabled=True):
        if enabled:
            xbmc.log("[checker] Włączenie (jeśli nie włączony) dodatku script.module.resolveurl")
            xbmc.executeJSONRPC(
                f'{{"jsonrpc":"2.0","method":"Addons.SetAddonEnabled","id":7,"params":{{"addonid": "{self.addonName}","enabled":true}}}}')
        else:
            xbmc.log("[checker] WYłączenie dodatku script.module.resolveurl")
            xbmc.executeJSONRPC(
                f'{{"jsonrpc":"2.0","method":"Addons.SetAddonEnabled","id":7,"params":{{"addonid": "{self.addonName}","enabled":false}}}}')
