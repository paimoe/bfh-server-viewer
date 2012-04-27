import cron_header

from django.http import HttpResponse
from website.models import *

from socket import *
from hashlib import md5

from datetime import datetime, timedelta

import re

# Commands
COMMAND_SERVER = 'bf2cc si'
COMMAND_PLAYER = 'bf2cc pl'

def do(request):
    Update()
    return HttpResponse('fart')
    
def select_kit(s):
    if s == 'none':
        return None
    match = s.split('_')[1]
    for i in [('s', 'Soldier'), ('g', 'Gunner'), ('c', 'Commando')]:
        if match == i[1]:
            return i[0]

    
# Server is a django model instance
def _parse_server(data, server, log):
    log.write('Parsing server data ...')
    
    items = data.split("\t")    
    result = {
        'version'       : items[0],
        'status'        : items[1], # 1 = playing, 2 = map/game ended
        'max_players'   : items[2],
        'connected'     : items[3],
        'joining'       : items[4],
        'map_current'   : items[5],
        'map_next'      : items[6],
        'server_name'   : items[7],
        
        't2'            : items[8], # Nationals (boooo)
        't2_tickets'    : items[11],
        't1'            : items[13], # Royals (yaaaay)
        't1_tickets'    : items[16],
        
        'round_time'    : items[18],
        'time_left'     : items[19],
        
        'mode'          : items[20],
        'mod_dir'       : items[21],
        'time_limit'    : items[23],
        'ranked'        : items[25],
        
        't1_count'      : items[26],
        't2_count'      : items[27],
        
        'rounds_per_map': items[30][0].strip(),
        'current_round' : items[31][0].strip(),
    }
    
    log.write('Parsed result: %s' % result)
    log.write('Updating server object ...')
    
    # Check status man
    rotation = '%s/%s' % (result['current_round'], result['rounds_per_map'])
    
    # Update server object with relevant stuffs
    # NFI if this works
    try:
        current_round = server.round_set.get(rotation=rotation, running=True, map=result['map_current'])        
    except:
        current_round = Round(server=server, running=True)
        
        # Update start time based on time_played from response
        current_round.start = datetime.now() - timedelta(seconds=int(result['round_time']))
        
    # Update old round (lol how do i select that mang?
    try:
        old_round = server.round_set.filter(running=True).update(running=False, end=datetime.now())
        #old_round.running = False
        #old_round.end = datetime.now()
        #old_round.save()
    except:
        log.write('Failed to end old rounds for some reason')

    current_round.map       = result['map_current']
    current_round.next_map  = result['map_next']
    current_round.rotation  = rotation
    
    # Calculate times for cr.end, cr.current
    current_round.t1_score  = result['t1_tickets']
    current_round.t2_score  = result['t2_tickets']
    
    # Found these things! lol
    current_round.t1_count = result['t2_count']
    current_round.t2_count = result['t1_count']
    
    if result['status'] == 2:    
        current_round.running   = False
        current_round.end       = datetime.now()        
    else:
        current_round.running   = True
    
    current_round.player_count  = result['connected']
    current_round.joining_count = result['joining']
    
    # Yeah hopefully thats it... lol
    current_round.save()
    log.write('Saved server status')
    
    return current_round

# Round is the current round row (fuck hope this somehow works)
def _parse_player(data, server, round, log):
    
    err = data.split("\r") # Wtf is this lol
    log.write('%s players found' % len(err))
    max = 0
    pids = []
    
    # Select all players in round I guess, if player exists then update, otherwise add new
    
    for player in err:
        
        p = player.split("\t")
        #log.write('Player line: %s' % p)
        plen = len(p) # Apparently this is meant to be 47 for some reason. MORE LIKE AGENT 47
        
        if plen < 47:
            log.write('Something fucked up with this row')
            log.write(p)
            continue
        
        row = {
            'id'    : p[0], # Random server identifier
            'name'  : p[1],
            'team'  : p[2], # 1 = Nats, 2 = Royals
            'ping'  : p[3],
            'heroid': p[11], # Think this is right
            'ip'    : p[18],
            'kills' : p[31],
            'kit'   : select_kit(p[34]),
            'idle'  : p[35].split('.')[0],
            'deaths': p[36],
            'score' : p[37],
            'level' : p[39],
            'vip'   : p[46] == 1,
            'nucleus'   : p[47],
        }
        
        #log.write('Parsed data for %s: %s' % (row['name'], row))
        
        # Team switcheroo, because ROYALS ARE NUMBER ONE
        if row['team'] == '1':
            row['team'] = 2
        else:
            row['team'] = 1
            
        # Get player, since player might exist, just not round
        try:
            new_player = Player.objects.get(player_id=row['nucleus'], name=row['name'])
            
            new_player.level = row['level']
            
            if row['kit'] is not None:
                new_player.kit = row['kit']
            
            log.write('Old Player object for %s' % row['name'])
            
        except Player.DoesNotExist:
            new_player = Player(
                name        = row['name'],
                level       = row['level'],
                hero_id     = row['nucleus'], # Lol how do I get this, beh probably have to update later (sweep it with a cron every hour or so)
                player_id   = row['nucleus'],
                vip         = False, # This too, have to move it to the other table I guess, or separate
                kit         = row['kit'],
                nucleus     = row['nucleus'],
                faction     = row['team'],
            )
            if row['kit'] is None:
                new_player.kit = 's'
            log.write('New Player object for %s' % row['name'])
        
        new_player.hero_id = row['heroid']
        new_player.save()
        
        # Select from round aye
        try:
            in_round = RoundPlayer.objects.get(player__name=row['name'], round=round, left__isnull=True)
            pids.append(in_round.player_id)
        except RoundPlayer.DoesNotExist:
            
            in_round = RoundPlayer(player=new_player, round=round)
            pids.append(new_player.id)
            log.write('Created new RoundPlayer')

        # Update
        in_round.kills  = row['kills']
        in_round.deaths = row['deaths']
        in_round.score  = row['score']
        in_round.ping   = row['ping']
        in_round.idle   = row['idle']
        
        in_round.save()
        log.write('Saved RoundPlayer (fkn hopefully)')
        
        max += 1
        if max == 16:
            
            # Updayt
            x = RoundPlayer.objects.exclude(player__in=pids).filter(round=round).update(left=datetime.now())
            return
        
        # Update all players who are in this round, but not in player list too, as left=datetime.now()
    x = RoundPlayer.objects.exclude(player__in=pids).filter(round=round).update(left=datetime.now())
    
class Log:
    
    def __init__(self, log):
        # Create log file I guess
        log = re.sub('\s', '-', log.lower())        
        self.log = log
        self.file = open('%s/%s.txt' % (cron_header.log_dir, self.log), 'a+')
    
    def write(self, text):
        now = datetime.now().isoformat(' ')
        self.file.write('[%s] %s\n' % (now, text))
        
    def close(self):
        self.file.close()

class Update:
    
    def __init__(self):
        self.socket = None
        self.update_servers()

    def update_servers(self):
        self.servers = Server.objects.all()
        for s in self.servers:
            
            self.update(s.p_host, s.p_user, s.p_pass, s.p_port, s)
            
        return 
        
    # Open socket to server, connect, download data. Also lock update for server
    def update(self, p_host, p_user, p_pass, p_port, server):
        
        self.log = Log(server.name)
        
        server.updating = False
        server.save()
        
        if server.updating == True:
            self.log.write('Skipping %s, currently updating' % server.name)
            return
        
        # "Lock"
        server.updating = True
        server.save()
        
        self.log.write('Locked %s, updating...' % server.name)
        
        # Open socket yo
        if self.socket is None:
            try:                
                self.socket = socket(AF_INET, SOCK_STREAM)
                self.socket.connect((p_host, p_port))
                self.socket.settimeout(10)
                self.connected = True # lolwhat
                
                self.log.write('Connected to socket with details %s:%s. Socket: %s' % (p_host, p_port, self.socket))
            except:
                self.log.write('Failed to connect to %s at %s:%s' % (server.name, p_host, p_port))
                self.socket = None
                return
        
        if self.socket:            
            # Connected, now lets go apparently
            
            digest = self.socket_receive(2)
            self.seed = self.compute_seed(digest)
            
            # This after tests on the other page... <seed><pass> only
            self.login = '%s%s' % (self.seed, p_pass)
            hash = md5(self.login).hexdigest()
            
            # Login            
            self.log.write('Attempting login ...')            
            result = self.send_and_receive("login %s" % hash)
            if re.match('Authentication successful', result):
                self.log.write('Logged in successfully. Returned result: %s' % result)
                
                # Logged in, get responses
                server_status = self.send_and_receive(COMMAND_SERVER)
                
                # Parse server status I guess
                # Returns the current round
                self.round = _parse_server(server_status, server, self.log)
                
                if self.round.player_count > 0:
                                    
                    # Player status
                    player_status = self.send_and_receive(COMMAND_PLAYER, 3)
                    
                    # Parse player data
                    _parse_player(player_status, server, self.round, self.log)
                    
                # --------------------- FIN ----------------------- #
                self.socket.close()
                self.log.write('Completed tasks for server %s' % server.name)
                self.log.close()
                
            else:
                self.log.write('Failed to login. Returned result: %s' % result)

        # "Unlock"
        server.updating = False
        server.save()
        
    def compute_login(self):
        pass

    def compute_seed(self, digest):
        s = digest.split('Digest seed:')[1:][0].strip()[0:17] # Yeah pretty much replicated I think
        return s
        
    def send_and_receive(self, command, loop=1):
        c = chr(002)
        cmd = "%s%s\n" % (c, command)
        if self.socket and self.connected:
            send = self.socket.send(cmd)
            if send:
                received = self.socket_receive(loop=loop)
                return received
            else:
                raise Exception, "Failed to send command %s" % cmd
        else:
            raise Exception, "Not connected to destination server"

    def socket_send(self):
        pass
    
    def socket_receive(self, loop=1, end_at_empty=True):
        m = ''
        i = 0
        while i < loop:
            try:
                b = self.socket.recv(8096)
                m += b
            except:
                return m
                
            #if b == '' and end_at_empty:
            #    return m
            #else:
            #    m += bs
                
            i += 1
        return m

if __name__ == '__main__':
    Update()
