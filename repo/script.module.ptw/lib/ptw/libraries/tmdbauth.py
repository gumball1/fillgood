# -*- coding: utf-8 -*-


import requests
from ptw.libraries import control
from ptw.libraries import apis
from ptw.libraries import log_utils

class Auth:
    def __init__(self):
        self.auth_base_link = 'https://api.themoviedb.org/3/authentication'
        self.tm_user = control.setting("tm.user") or apis.tmdb_API

    def create_session_id(self):
            if control.setting('tmdb.username') == '' or control.setting('tmdb.password') == '':
                return control.notification(title='default', message=32683, icon='ERROR')
            url = self.auth_base_link + '/token/new?api_key=%s' % self.tm_user
            result = requests.get(url).json()
            token = result.get('request_token')
            url2 = self.auth_base_link + '/token/validate_with_login?api_key=%s' % self.tm_user
            username = control.setting('tmdb.username')
            password = control.setting('tmdb.password')
            post2 = {"username": "%s" % username,
                     "password": "%s" % password,
                     "request_token": "%s" % token}
            result2 = requests.post(url2, data=post2).json()
            url3 = self.auth_base_link + '/session/new?api_key=%s' % self.tm_user
            post3 = {"request_token": "%s" % token}
            result3 = requests.post(url3, data=post3).json()
            if result3.get('success') is True:
                session_id = result3.get('session_id')
                # msg = '%s' % ('login =' + username + '[CR]hasło =' + password + '[CR]token = ' + token + '[CR]Potwierdzasz?')
                # msg = '%s' % ('login =' + username + '[CR]hasło =' + (len(password) * "*") + '[CR]token = ' + token + '[CR]Potwierdzasz?')
                msg = '%s' % ('login =' + username + '[CR]hasło =' + (len(password) * "*") + '[CR][CR]Potwierdzasz?')
                if control.yesnoDialog(msg, heading='FanFilm autoryzacja TMDB'):
                    control.setSetting('tmdb.sessionid', session_id)
                    control.infoDialog('FanFilm autoryzacja TMDB', "Autoryzacja udana", 'default')
                else:
                    control.infoDialog('FanFilm autoryzacja TMDB', "Błąd", 'ERROR')

    def revoke_session_id(self):
            if control.setting('tmdb.sessionid') == '':
                return
            url = self.auth_base_link + '/session?api_key=%s' % self.tm_user
            post = {"session_id": "%s" % control.setting('tmdb.sessionid')}
            result = requests.delete(url, data=post).json()
            if result.get('success') is True:
                control.setSetting('tmdb.sessionid', '')
                control.infoDialog('FanFilm autoryzacja TMDB', "Usunięto dane", 'default')
            else:
                control.infoDialog('FanFilm autoryzacja TMDB', "Wystąpił błąd", 'ERROR')
