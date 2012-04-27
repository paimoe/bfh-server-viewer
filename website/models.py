from django.db import models
from datetime import datetime

# Create your models here.
ROUND_CHOICES = (
    ('heat', 'Riverside Rush'),
    ('lake', 'Buccaneer Bay'),
    ('seaside_skirmish', 'Seaside Skirmish'),
    ('village', 'Victory Village'),
    ('smack2', 'Coastal Clash'),
    ('mayhem', 'Sunset Showdown'),
    ('seaside_skirmish_night', 'Seaside Skirmish (Night)'),
    ('smack2_night', 'Coastal Clash (Night)'),
    ('lake_night', 'Buccaneer Bay (Night)'),
    ('ruin', 'Midnight Mayhem'),
)

FACTION_CHOICES = (
    ('1', 'Royal'),
    ('2', 'National'),
)

LOCATION_CHOICES = (
    ('EU', 'Europe'),
    ('NA', 'North America'),
    ('AS', 'Asia'),
    ('AU', 'Australia'),
)

KIT_CHOICES = (
    ('s', 'Soldier'), 
    ('g', 'Gunner'), 
    ('c', 'Commando')
)

# Players, rounds, servers, logs
class Server(models.Model):
    name = models.CharField(max_length=60)
    p_user = models.CharField(max_length=20)
    p_pass = models.CharField(max_length=50)
    p_host = models.CharField(max_length=100)
    p_port = models.IntegerField()
    contact_email = models.EmailField()
    updating = models.BooleanField(default=False)
    
    location = models.CharField(max_length=20, choices=LOCATION_CHOICES)
    description = models.CharField(blank=True, max_length=100)
    bookmark = models.URLField()
    
    class Meta:
        db_table = u'servers'
    
    def __unicode__(self):
        return u'Server: %s (%s)' % (self.name, self.p_host)
    
class Player(models.Model):
    name = models.CharField(max_length=50, unique=True)
    bfh_id = models.CharField(max_length=20, unique=True)
    kit = models.CharField(max_length=20, choices=KIT_CHOICES)
    faction = models.CharField(max_length=20, choices=FACTION_CHOICES)
    
    confirmed_cheater = models.BooleanField()
    
    class Meta:
        db_table = u'players'
    
    def __unicode__(self):
        return '%s (%s)' % (self.name, self.get_faction_display())
        
class Hero(models.Model):
    player = models.ForeignKey(Player)
    name = models.CharField(max_length=50, unique=True)
    bfh_id = models.CharField(max_length=20, unique=True)
    kit = models.CharField(max_length=1, choices=KIT_CHOICES)
    level = models.IntegerField()
    
    faction = models.CharField(max_length=20, choices=FACTION_CHOICES)
    
    class Meta:
        db_table = u'heroes'
        
    def __unicode__(self):
        return '%s (Player %s)' % (self.name, self.player.name)
        
class HeroStats(models.Model):
    hero = models.ForeignKey(Hero)
    
    # Err, all the stats we track LE SIGH
    
    def __unicode__(self):
        return 'Stats for %s' % self.hero.name
        
class HeroPB(models.Model):
    hero = models.ForeignKey(Hero)
    ss_id = models.CharField(max_length=20)
        
class Round(models.Model):
    server = models.ForeignKey(Server)
    
    map = models.CharField(max_length=50, choices=ROUND_CHOICES)
    next_map = models.CharField(max_length=50, choices=ROUND_CHOICES)
    
    start = models.DateTimeField(auto_now_add=True)
    end = models.DateTimeField(null=True, blank=True)
    current = models.DateTimeField(auto_now=True)
    
    t1_score = models.IntegerField(default=50)
    t2_score = models.IntegerField(default=50)
    running = models.BooleanField()
    
    player_count = models.SmallIntegerField()
    joining_count = models.SmallIntegerField()
    
    t1_count = models.IntegerField(default=0)
    t2_count = models.IntegerField(default=0)
    
    # For verifying the exact round
    rotation = models.CharField(max_length=20)
    
    class Meta:
        db_table = u'rounds'  
        ordering = ('-start',)
    
    def __unicode__(self):
        if self.end is None:
            time = 'Currently Running'
        else:
            time = '[%s - %s]' % (self.start, self.end)
        return '%s on %s (%s) - %s' % (self.get_map_display(), self.server.name, self.rotation, time)
    
class RoundPlayer(models.Model):
    round = models.ForeignKey(Round, related_name="rplayers")
    player = models.ForeignKey(Player)
    kills = models.IntegerField(default=0)
    deaths = models.IntegerField(default=0)
    score = models.IntegerField(default=0)
    
    joined = models.DateTimeField(auto_now_add=True)
    left = models.DateTimeField(blank=True, null=True)
    
    ping = models.IntegerField()
    idle = models.IntegerField(default=0)
    
    class Meta:
        db_table = u'rounds_players'
    
    def __unicode__(self):
        return '%s at %s' % (unicode(self.player), unicode(self.round))
        
    def __str__(self):
        return '%s at %s' % (unicode(self.player), unicode(self.round))
