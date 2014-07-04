'''
    tvScheduler XBMC Plugin
    Copyright (C) 2013 dmdsoftware

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


'''

import os
import re
import urllib, urllib2

import xbmc, xbmcaddon, xbmcgui, xbmcplugin

addon = xbmcaddon.Addon(id='plugin.video.tvScheduler')

def log(msg, err=False):
    if err:
        xbmc.log(addon.getAddonInfo('name') + ': ' + msg.encode('utf-8'), xbmc.LOGERROR)
    else:
        xbmc.log(addon.getAddonInfo('name') + ': ' + msg.encode('utf-8'), xbmc.LOGDEBUG)

class gSpreadsheets:


    def __init__(self, user, password, auth, user_agent):
        self.user = user
        self.password = password
        self.wise = auth
        self.user_agent = user_agent

        # if we have an authorization token set, try to use it
        if auth != '':
          log('using token')

          return
        log('logging in tvScheduler')
        self.login();

        return


    def login(self):

        url = 'https://www.google.com/accounts/ClientLogin'
        header = { 'User-Agent' : self.user_agent }
        values = {
          'Email' : self.user,
          'Passwd' : self.password,
          'accountType' : 'HOSTED_OR_GOOGLE',
          'source' : 'dmdtvScheduler',
          'service' : 'wise'
        }

        log('logging in tvScheduler')

#        log('username %s %s' % (user,urllib.urlencode(values)))
        req = urllib2.Request(url, urllib.urlencode(values), header)

        try:
            response = urllib2.urlopen(req)
        except urllib2.URLError, e:
            log(str(e), True)

        response_data = response.read()

        for r in re.finditer('SID=(.*).+?' +
                             'LSID=(.*).+?' +
                             'Auth=(.*).+?' ,
                             response_data, re.DOTALL):
            sid,lsid,auth = r.groups()

        log('parameters: %s %s %s' % (sid, lsid, auth))

        self.wise = auth

        return


    def returnHeaders(self):
        return urllib.urlencode({ 'User-Agent' : self.user_agent, 'Authorization' : 'GoogleLogin auth=%s' % self.wise, 'GData-Version' : '3.0' })


    #
    # returns a list of spreadsheets contained in the Google Docs account
    #
    def getSpreadsheetList(self):
        log('getting list of spreadsheets')

        url = 'https://spreadsheets.google.com/feeds/spreadsheets/private/full'
        header = { 'User-Agent' : self.user_agent, 'Authorization' : 'GoogleLogin auth=%s' % self.wise, 'GData-Version' : '3.0' }

        spreadsheets = {}
        while True:
            log('url = %s header = %s' % (url, header))
            req = urllib2.Request(url, None, header)

            log('loading ' + url)
            try:
                response = urllib2.urlopen(req)
            except urllib2.URLError, e:
                log(str(e), True)

            response_data = response.read()
            log('response %s' % response_data)
            log('info %s' % str(response.info()))


            log('parsing spreadsheet list')

            for r in re.finditer('<title>([^<]+)</title><content type=\'application/atom\+xml;type=feed\' src=\'([^\']+)\'' ,
                             response_data, re.DOTALL):
                title,url = r.groups()
                log('found spreadsheet %s %s' % (title, url))
                spreadsheets[title] = url

            nextURL = ''
            for r in re.finditer('<link rel=\'next\' type=\'[^\']+\' href=\'([^\']+)\'' ,
                             response_data, re.DOTALL):
                nextURL = r.groups()
                log('next URL url='+nextURL[0])

            response.close()

            if nextURL == '':
                break
            else:
                url = nextURL[0]


        return spreadsheets

    #
    # returns a list of worksheets contained in the Google Docs Spreadsheet
    #
    def getSpreadsheetWorksheets(self,url):
        log('getting list of worksheets')

        header = { 'User-Agent' : self.user_agent, 'Authorization' : 'GoogleLogin auth=%s' % self.wise, 'GData-Version' : '3.0' }

        worksheets = {}
        while True:
            log('url = %s header = %s' % (url, header))
            req = urllib2.Request(url, None, header)

            log('loading ' + url)
            try:
                response = urllib2.urlopen(req)
            except urllib2.URLError, e:
                log(str(e), True)

            response_data = response.read()
            log('response %s' % response_data)
            log('info %s' % str(response.info()))


            log('parsing worksheets list')

            for r in re.finditer('<title>([^<]+)</title><content type=\'application/atom\+xml;type=feed\' src=\'([^\']+)\'' ,
                             response_data, re.DOTALL):
                title,url = r.groups()
                log('found worksheets %s %s' % (title, url))
                worksheets[title] = url

            nextURL = ''
            for r in re.finditer('<link rel=\'next\' type=\'[^\']+\' href=\'([^\']+)\'' ,
                             response_data, re.DOTALL):
                nextURL = r.groups()
                log('next URL url='+nextURL[0])

            response.close()

            if nextURL == '':
                break
            else:
                url = nextURL[0]


        return worksheets

    def getShows(self,url,channel):
        log('getting list of shows')

        header = { 'User-Agent' : self.user_agent, 'Authorization' : 'GoogleLogin auth=%s' % self.wise, 'GData-Version' : '3.0' }

        params = urllib.urlencode({'channel': channel})
        url = url + '?sq=' + params


        shows = {}
        while True:
            log('url = %s header = %s' % (url, header))
            req = urllib2.Request(url, None, header)

            log('loading ' + url)
            try:
                response = urllib2.urlopen(req)
            except urllib2.URLError, e:
                log(str(e), True)

            response_data = response.read()
            log('response %s' % response_data)
            log('info %s' % str(response.info()))


            log('parsing query results')

            count=0;
            for r in re.finditer('<gsx:channel>([^<]*)</gsx:channel><gsx:month>([^<]*)</gsx:month><gsx:day>([^<]*)</gsx:day><gsx:weekday>([^<]*)</gsx:weekday><gsx:hour>([^<]*)</gsx:hour><gsx:minute>([^<]*)</gsx:minute><gsx:show>([^<]*)</gsx:show><gsx:order>([^<]*)</gsx:order><gsx:includewatched>([^<]*)</gsx:includewatched>' ,
                             response_data, re.DOTALL):
                shows[count] = r.groups()
#source,nfo,show,season,episode,part,watched,duration
#channel,month,day,weekday,hour,minute,show,order,includeWatched
                log('found show %s, %s' % (shows[count][0], shows[count][1]))
                count = count + 1

            nextURL = ''
            for r in re.finditer('<link rel=\'next\' type=\'[^\']+\' href=\'([^\']+)\'' ,
                             response_data, re.DOTALL):
                nextURL = r.groups()
                log('next URL url='+nextURL[0])

            response.close()

            if nextURL == '':
                break
            else:
                url = nextURL[0]


        return shows

    def getVideo(self,url,show):
        log('getting list of shows')

        header = { 'User-Agent' : self.user_agent, 'Authorization' : 'GoogleLogin auth=%s' % self.wise, 'GData-Version' : '3.0' }

        params = urllib.urlencode({'show': show})
        url = url + '?sq=' + params + '%20and%20watched=0'


        shows = {}
        while True:
            log('url = %s header = %s' % (url, header))
            req = urllib2.Request(url, None, header)

            log('loading ' + url)
            try:
                response = urllib2.urlopen(req)
            except urllib2.URLError, e:
                log(str(e), True)

            response_data = response.read()
            log('response %s' % response_data)
            log('info %s' % str(response.info()))


            log('parsing query results')

            count=0;
            for r in re.finditer('<entry [^\>]+>.*?<gsx:source>([^<]*)</gsx:source><gsx:nfo>([^<]*)</gsx:nfo><gsx:show>([^<]*)</gsx:show><gsx:season>([^<]*)</gsx:season><gsx:episode>([^<]*)</gsx:episode><gsx:part>([^<]*)</gsx:part><gsx:watched>([^<]*)</gsx:watched><gsx:duration>([^<]*)</gsx:duration></entry>' ,
                             response_data, re.DOTALL):
                shows[count] = r.groups()
                #source,nfo,show,season,episode,part,watched,duration
                log('found video %s, %s' % (shows[count][1], shows[count][2]))
                count = count + 1

            nextURL = ''
            for r in re.finditer('<link rel=\'next\' type=\'[^\']+\' href=\'([^\']+)\'' ,
                             response_data, re.DOTALL):
                nextURL = r.groups()
                log('next URL url='+nextURL[0])

            response.close()

            if nextURL == '':
                break
            else:

                url = nextURL[0]

        return shows


    def setVideoWatched(self,url,source):
        log('need to update to watched')

#        import urllib
#        from cookielib import CookieJar

#        cj = CookieJar()
#        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
#        urllib2.install_opener(opener)


        header = { 'User-Agent' : self.user_agent, 'Authorization' : 'GoogleLogin auth=%s' % self.wise, 'GData-Version' : '3.0' }

        source = re.sub(' ', '%20', source)
#        params = urllib.urlencode(source)
        url = url + '?sq=source="' + source +'"'

        log('url = %s header = %s' % (url, header))
        req = urllib2.Request(url, None, header)

        log('loading ' + url)
        try:
            response = urllib2.urlopen(req)
#            response = opener.open(url, None,urllib.urlencode(header))
        except urllib2.URLError, e:
            log(str(e), True)

        response_data = response.read()
        log('response %s' % response_data)
        log('info %s' % str(response.info()))


        log('updating watched status')

        editURL=''
        for r in re.finditer('<link rel=\'(edit)\' type=\'application/atom\+xml\' href=\'([^\']+)\'/>' ,
                             response_data, re.DOTALL):
            (x,editURL) = r.groups(1)
            log('editURL '  +editURL)

        for r in re.finditer('(.*?)(<entry .*?</entry>)' ,
                             response_data, re.DOTALL):
            (x,entry) = r.groups(1)
            log('entry '  +entry)

        response.close()

#        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
#        urllib2.install_opener(opener)

#        req = urllib2.Request(editURL, None, header)

#        log('loading ' + url)
#        try:
#            response = urllib2.urlopen(req)
#            response = opener.open(url, None,urllib.urlencode(header))
#        except urllib2.URLError, e:
#            log(str(e), True)

#        response_data = response.read()
#        log('response %s' % response_data)
#        log('info %s' % str(response.info()))

#        response.close()

#        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

       # data_encoded = urllib.urlencode(formdata)
#        urllib2.install_opener(opener)

        entry = re.sub('<gsx:watched>([^\<]*)</gsx:watched>', '<gsx:watched>1</gsx:watched>', entry)
        #editURL = re.sub('https', 'http', editURL)

        header = { 'User-Agent' : self.user_agent, 'Authorization' : 'GoogleLogin auth=%s' % self.wise, 'GData-Version' : '3.0', "If-Match" : '*', "Content-Type": 'application/atom+xml' }


        entry = re.sub(' gd\:etag[^\>]+>', ' xmlns="http://www.w3.org/2005/Atom" xmlns:gs="http://schemas.google.com/spreadsheets/2006" xmlns:gsx="http://schemas.google.com/spreadsheets/2006/extended">', entry)
#        entry = "<?xml version='1.0' encoding='UTF-8'?>"+entry
#        entry = '<feed xmlns="http://www.w3.org/2005/Atom" xmlns:openSearch="http://a9.com/-/spec/opensearch/1.1/" xmlns:gsx="http://schemas.google.com/spreadsheets/2006/extended" xmlns:gd="http://schemas.google.com/g/2005" gd:etag=\'W/"D0cERnk-eip7ImA9WBBXGEg."\'><entry>  <id>    https://spreadsheets.google.com/feeds/worksheets/key/private/full/worksheetId  </id>  <updated>2007-07-30T18:51:30.666Z</updated>  <category scheme="http://schemas.google.com/spreadsheets/2006"    term="http://schemas.google.com/spreadsheets/2006#worksheet"/>  <title type="text">Income</title>  <content type="text">Expenses</content>  <link rel="http://schemas.google.com/spreadsheets/2006#listfeed"    type="application/atom+xml" href="https://spreadsheets.google.com/feeds/list/key/worksheetId/private/full"/>  <link rel="http://schemas.google.com/spreadsheets/2006#cellsfeed"    type="application/atom+xml" href="https://spreadsheets.google.com/feeds/cells/key/worksheetId/private/full"/>  <link rel="self" type="application/atom+xml"    href="https://spreadsheets.google.com/feeds/worksheets/key/private/full/worksheetId"/>  <link rel="edit" type="application/atom+xml"    href="https://spreadsheets.google.com/feeds/worksheets/key/private/full/worksheetId/version"/>  <gs:rowCount>45</gs:rowCount>  <gs:colCount>15</gs:colCount></entry>'
        log('url = %s header = %s, %s' % (editURL, header, entry))

        req = urllib2.Request(editURL, entry, header)
#        urllib2.HTTPHandler(debuglevel=1)
        req.get_method = lambda: 'PUT'


        log('loading ' + editURL)
        try:
            response = urllib2.urlopen(req)
        except urllib2.URLError, e:
            log(str(e.read()), True)

        response_data = response.read()
        log('response %s' % response_data)
        log('info %s' % str(response.info()))

        response.close()


    def getChannels(self,url):
        log('getting list of channels')

        header = { 'User-Agent' : self.user_agent, 'Authorization' : 'GoogleLogin auth=%s' % self.wise, 'GData-Version' : '3.0' }

        params = urllib.urlencode({'orderby': 'channel'})
        url = url + '?' + params


        channels = []
        count=0

        while True:
            log('url = %s header = %s' % (url, header))
            req = urllib2.Request(url, None, header)

            log('loading ' + url)
            try:
                response = urllib2.urlopen(req)
            except urllib2.URLError, e:
                log(str(e), True)

            response_data = response.read()
            log('response %s' % response_data)
            log('info %s' % str(response.info()))


            log('parsing query results')

            for r in re.finditer('<gsx:channel>([^<]*)</gsx:channel>' ,
                             response_data, re.DOTALL):
                (channel) = r.groups()
#channel,month,day,weekday,hour,minute,show,order,includeWatched
                log('found channel %s' % (channel))
                if not channels.__contains__(channel[0]):
                  channels.append(channel[0])
                  count = count + 1

            nextURL = ''
            for r in re.finditer('<link rel=\'next\' type=\'[^\']+\' href=\'([^\']+)\'' ,
                             response_data, re.DOTALL):
                nextURL = r.groups()
                log('next URL url='+nextURL[0])

            response.close()

            if nextURL == '':
                break
            else:
                url = nextURL[0]

        return channels






