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

from resources.lib import gSpreadsheets 
from resources.lib import CONSTANTS
import sys
import urllib
import cgi
import re
import datetime
import time

import xbmc, xbmcgui, xbmcplugin, xbmcaddon


        
def log(msg, err=False):
    if err:
        xbmc.log(addon.getAddonInfo('name') + ': ' + msg.encode('utf-8'), xbmc.LOGERROR)    
    else:
        xbmc.log(addon.getAddonInfo('name') + ': ' + msg.encode('utf-8'), xbmc.LOGDEBUG)    

def parse_query(query):
    queries = cgi.parse_qs(query)
    q = {}
    for key, value in queries.items():
        q[key] = value[0]
    q['mode'] = q.get('mode', 'main')
    return q

def addVideo(url, infolabels, img='', fanart='', total_items=0, 
                   cm=[], cm_replace=False):
    infolabels = decode_dict(infolabels)
    log('adding video: %s - %s' % (infolabels['title'].decode('utf-8','ignore'), url))
    listitem = xbmcgui.ListItem(infolabels['title'], iconImage=img, 
                                thumbnailImage=img)
    listitem.setInfo('video', infolabels)
    listitem.setProperty('IsPlayable', 'true')
    listitem.setProperty('fanart_image', fanart)
    if cm:
        listitem.addContextMenuItems(cm, cm_replace)
    xbmcplugin.addDirectoryItem(plugin_handle, url, listitem, 
                                isFolder=False, totalItems=total_items)

def addChannel(channel):
    url = plugin_url + '?mode=viewChannel&channel=' + channel
    log('adding channel: %s - %s' % (url,channel))
    listitem = xbmcgui.ListItem('channel - ' + channel, '', '')
    xbmcplugin.addDirectoryItem(plugin_handle, url, listitem, 
                                isFolder=True, totalItems=0)

def addShow(show):
    url = plugin_url + '?mode=viewShow&show=' + show
    log('adding show: %s - %s' % (url,show))
    listitem = xbmcgui.ListItem('show - ' + show, '', '')
    xbmcplugin.addDirectoryItem(plugin_handle, url, listitem, 
                                isFolder=True, totalItems=0)


#http://stackoverflow.com/questions/1208916/decoding-html-entities-with-python/1208931#1208931
def _callback(matches):
    id = matches.group(1)
    try:
        return unichr(int(id))
    except:
        return id

def decode(data):
    return re.sub("&#(\d+)(;|(?=\s))", _callback, data).strip()

def decode_dict(data):
    for k, v in data.items():
        if type(v) is str or type(v) is unicode:
            data[k] = decode(v)
    return data



plugin_url = sys.argv[0]
plugin_handle = int(sys.argv[1])
plugin_queries = parse_query(sys.argv[2][1:])

addon = xbmcaddon.Addon(id='plugin.video.tvScheduler')
#plugin_path = addon.getAddonInfo('path')

username = addon.getSetting('username')
password = addon.getSetting('password')
auth_token = addon.getSetting('auth_token')
user_agent = addon.getSetting('user_agent')
save_auth_token = addon.getSetting('save_auth_token')

# you need to have at least a username&password set or an authorization token
if ((username == '' or password == '') and auth_token == ''):
    xbmcgui.Dialog().ok(addon.getLocalizedString(30000), 'Set the Username and Password in addon settings before running.')
    log('Set the Username and Password in addon settings before running.', True)
    xbmcplugin.endOfDirectory(plugin_handle)


#let's log in
tvScheduler = gSpreadsheets.gSpreadsheets(username, password, auth_token, user_agent)

# if we don't have an authorization token set for the plugin, set it with the recent login.
#   auth_token will permit "quicker" login in future executions by reusing the existing login session (less HTTPS calls = quicker video transitions between clips)
log('save_auth_token' + save_auth_token)
if auth_token == '' and save_auth_token == 'true':
    log('saving authorization token')
    addon.setSetting('auth_token', tvScheduler.wise)  
    

log('plugin google authorization: ' + tvScheduler.returnHeaders())
log('plugin url: ' + plugin_url)
log('plugin queries: ' + str(plugin_queries))
log('plugin handle: ' + str(plugin_handle))

mode = plugin_queries['mode']


# dump a list of channels available to play
if mode == 'main':
    log(mode)

    spreadsheets = tvScheduler.getSpreadsheetList()

    channels = []
    for title in spreadsheets.iterkeys():
        if title == 'TVShows':
           worksheets = tvScheduler.getSpreadsheetWorksheets(spreadsheets[title])

           for worksheet in worksheets.iterkeys():
             if worksheet == 'schedule':
               channels = tvScheduler.getChannels(worksheets[worksheet])

#               for channel in channels:
#                 log('channel ' + str(channel))
#                 channels = tvScheduler.getChannels(worksheets[worksheet])
               
    for channel in channels:
        log('channel ' + str(channel))

        addChannel(str(channel))

# dump a list of shows available to play
elif mode == 'viewChannel':
    log(mode)
    channel = plugin_queries['channel']

    i = datetime.datetime.now() 
    log ('Current date and time ' + str(i))
    log ('Current month ' + time.strftime("%m"))
    log ('Current day ' + time.strftime("%d"))
    log ('Current weekday ' + time.strftime("%w"))
    log ('Current hour ' + time.strftime("%H"))
    log ('Current minute ' + time.strftime("%M"))
    log ('constant test ' + str(CONSTANTS.S_CHANNEL))

    spreadsheets = tvScheduler.getSpreadsheetList()

    shows = []
    for title in spreadsheets.iterkeys():
        if title == 'TVShows':
           worksheets = tvScheduler.getSpreadsheetWorksheets(spreadsheets[title])

           for worksheet in worksheets.iterkeys():
             if worksheet == 'schedule':
               shows = tvScheduler.getShows(worksheets[worksheet] ,channel)


    for show in shows:
        log('show ' + str(shows[show][CONSTANTS.S_SHOW]))

        addShow(str(shows[show][CONSTANTS.S_SHOW]))

# dump a list of episodes available to play
elif mode == 'viewShow':
    log(mode)
    show = plugin_queries['show']

    i = datetime.datetime.now() 
    log ('Current date and time ' + str(i))
    log ('Current month ' + time.strftime("%m"))
    log ('Current day ' + time.strftime("%d"))
    log ('Current weekday ' + time.strftime("%w"))
    log ('Current hour ' + time.strftime("%H"))
    log ('Current minute ' + time.strftime("%M"))


    spreadsheets = tvScheduler.getSpreadsheetList()

    episodes = []
    for title in spreadsheets.iterkeys():
        if title == 'TVShows':
           worksheets = tvScheduler.getSpreadsheetWorksheets(spreadsheets[title])

           for worksheet in worksheets.iterkeys():
             if worksheet == 'data':
               episodes = tvScheduler.getVideo(worksheets[worksheet] ,show)


    for video in episodes:
        log('video ' + str(episodes[video][CONSTANTS.D_SOURCE]) + ',' + str(episodes[video][CONSTANTS.D_SHOW]))

        addVideo('plugin://plugin.video.gdrive?mode=playvideo&amp;title='+episodes[video][0],
                             { 'title' : str(episodes[video][CONSTANTS.D_SHOW]) + ' - S' + str(episodes[video][CONSTANTS.D_SEASON]) + 'xE' + str(episodes[video][CONSTANTS.D_EPISODE]) + ' ' + str(episodes[video][CONSTANTS.D_PART])  , 'plot' : episodes[video][CONSTANTS.D_SHOW] },
                             img='None')


elif mode == 'watchShow':
    show = plugin_queries['show']
    instance = int(plugin_queries['instance'])
    log('mode = ' + mode + ' show = ' + str(show) + ' instance = ' + str(instance) + ' mod ' + str(0 % int(instance)))

    i = datetime.datetime.now() 
    log ('Current date and time ' + str(i))
    log ('Current month ' + time.strftime("%m"))
    log ('Current day ' + time.strftime("%d"))
    log ('Current weekday ' + time.strftime("%w"))
    log ('Current hour ' + time.strftime("%H"))
    log ('Current minute ' + time.strftime("%M"))


    spreadsheets = tvScheduler.getSpreadsheetList()

    episodes = []
    for title in spreadsheets.iterkeys():
        if title == 'TVShows':
           worksheets = tvScheduler.getSpreadsheetWorksheets(spreadsheets[title])

           for worksheet in worksheets.iterkeys():
             if worksheet == 'data':
               episodes = tvScheduler.getVideo(worksheets[worksheet] ,show)

    
    count = 1
    isPlaying = False
    while not isPlaying and count < 20:
      for video in episodes:
        if ((count % instance) == 0 and not isPlaying):
          item = xbmcgui.ListItem(path='plugin://plugin.video.gdrive?mode=playvideo&amp;title='+episodes[video][0])
          log('play url: ' + episodes[video][0])
          xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
          tvScheduler.setVideoWatched(worksheets[worksheet], episodes[video][0])
          isPlaying = True   
          count = count + 1
        else:
          count = count + 1
 

# dump a list of shows available to play
elif mode == 'watchChannel':
    log(mode)
    channel = plugin_queries['channel']
    instance = int(plugin_queries['instance'])

    i = datetime.datetime.now() 
    log ('Current date and time ' + str(i))
    log ('Current month ' + time.strftime("%m"))
    log ('Current day ' + time.strftime("%d"))
    log ('Current weekday ' + time.strftime("%w"))
    log ('Current hour ' + time.strftime("%H"))
    log ('Current minute ' + time.strftime("%M"))
    log ('constant test ' + str(CONSTANTS.S_CHANNEL))

    spreadsheets = tvScheduler.getSpreadsheetList()

    channels = []
    shows = []
    for title in spreadsheets.iterkeys():
        if title == 'TVShows':
           worksheets = tvScheduler.getSpreadsheetWorksheets(spreadsheets[title])

           for worksheet in worksheets.iterkeys():
             if worksheet == 'schedule':
               shows = tvScheduler.getShows(worksheets[worksheet] ,channel)

    showCount = 0
#    for show in shows:
#        if int(shows[show][CONSTANTS.S_DAY]) == int(time.strftime("%d")):
#          showCount = show


    episodes = []
    for title in spreadsheets.iterkeys():
        if title == 'TVShows':
           worksheets = tvScheduler.getSpreadsheetWorksheets(spreadsheets[title])

           for worksheet in worksheets.iterkeys():
             if worksheet == 'data':
               episodes = tvScheduler.getVideo(worksheets[worksheet] ,str(shows[0][CONSTANTS.S_SHOW]))
    

    count = 1
    maxCount=0
    isPlaying = False
    while not isPlaying and maxCount < 20:
      for video in episodes:
        if ((count % instance) == 0 and not isPlaying):
          item = xbmcgui.ListItem(path='plugin://plugin.video.gdrive?mode=playvideo&amp;title='+episodes[video][0])
          log('play url: ' + episodes[video][0])
          xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
          tvScheduler.setVideoWatched(worksheets['data'], episodes[video][0])
          isPlaying = True   
        count = count + 1
      maxCount = maxCount + 1


#clear the authorization token
elif mode == 'clearauth':
    addon.setSetting('auth_token', '')
     
xbmcplugin.endOfDirectory(plugin_handle)

