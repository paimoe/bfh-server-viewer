# Create your views here.
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect as redirect
from django.template.loader import get_template

from models import *
from datetime import datetime, timedelta

import settings
import clevercss        

def render_css(request, file):
    
    o = get_template(file)
    r = o.render({})
    x = clevercss.convert(r)
    
    return HttpResponse(x, mimetype="text/css")
    

def server_list(request, restrict=None, map=None, exclude_empty=False, exclude_full=False):
    
    # Get servers
    servers = Server.objects.all()
    server_list = []
    
    for s in servers:
        blah = s.round_set.all().order_by('-running', '-start')[:1]
        
        x = {
            'id': s.id,
            'name': s.name,
            'location': s.location,
            'description': s.description,
            'bookmark': s.bookmark
        }
        
        try:
            blah = blah[0]       
            
            x['map'] = blah.get_map_display()
            
            if blah.map == 'ruin':
                x['t1_score'] = ':'.join( str(timedelta(seconds=blah.t1_score)).split(':')[1:] )
                x['t2_score'] = ':'.join( str(timedelta(seconds=blah.t2_score)).split(':')[1:] )
            else:            
                x['t1_score'] = blah.t1_score
                x['t2_score'] = blah.t2_score
                
            x['current_royals'] = blah.t1_count
            x['current_nationals'] = blah.t2_count
            x['started'] = blah.start
            
            x['roundid'] = blah.id
            
        except IndexError:
            x['no_current_round'] = True
            
        server_list.append(x)
        
    # Compute order string
    order = 'default'
    
    return render_to_response('server_list.html', {'servers': server_list, 'order': order, 'do_refresh': 'true'})
    
def server_view(request, server_id=0):
    try:
        server = Server.objects.get(id=server_id)
    except Server.DoesNotExist:
        return redirect('/')
        
    # Latest 20 games
    games_total = Round.objects.filter(server=server)
    roundsplayed = len(games_total)
    games = games_total[:20]
    
    for game in games:
        game.map = game.get_map_display()
        
        if game.running:
            game.time = 'In Progress'
        else:
            game.time_title = '%s - %s' % (game.start.isoformat(' '), game.end.isoformat(' '))
            game.time = '%s' % (game.end - game.start)
            
        game.player_count = game.t1_count + game.t2_count
        
    return render_to_response('server_view.html', {
        'server': server,
        'games': games,
        'roundsplayed': roundsplayed,
    })
    
def hero_view(request, hero_id=0):
    try:
        hero = Player.objects.get(id=hero_id)
    except Player.DoesNotExist:
        return redirect('/')
    
    hero.faction = hero.get_faction_display()
    hero.kit = hero.get_kit_display()
    
    # 20 Latest games
    try:
        games = RoundPlayer.objects.filter(player=hero)[:20]
        
        # Loop and stuff
        for game in games:
            game.map = game.round.get_map_display()
        
        latest = games
        
    except RoundPlayer.DoesNotExist:
        latest = False
    
    return render_to_response('hero.html', {
        'site_title' : '%s - ' % hero.name,
        'hero' : hero,
        'latest': latest
    })

def view_game(request, roundid):
    data = {}
    
    # Get current game
    try:
        current = Round.objects.get(pk=roundid)
    except Round.DoesNotExist:
        try: 
            current = Round.objects.order_by('-id')[0]
        except:
            current = False
    
    if current is not False:
        data['team1'] = { 'score' : current.t1_score }
        data['team2'] = { 'score' : current.t2_score }
        
        data['team1']['players'] = RoundPlayer.objects.filter(round=current, player__faction=1).exclude(left__isnull=False).order_by('-score')
        data['team2']['players'] = RoundPlayer.objects.filter(round=current, player__faction=2).exclude(left__isnull=False).order_by('-score')
        
        t1 = len(data['team1']['players'])
        t2 = len(data['team2']['players'])
        
        
        data['info'] = {
            'map': current.get_map_display(),
            'running': current.running,
            'start_time': current.start,
            'server': current.server.name,
            'archived': current.running == False,
            'start': current.start.strftime('%A %b %d at %H:%M'),
        }
        
        if current.running == True:
            data['do_refresh'] = 'true'
        
        data['last_updated'] = current.current.strftime('%a %b %d %Y %H:%M:%S GMT')
    
    return render_to_response('index.html', data)

def update(request):
    "Ze big request updater"
    
    response = '' # will bel ike idk fetch_data()
