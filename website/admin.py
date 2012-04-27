from models import Server, Player, Round, RoundPlayer
from django.contrib import admin

class PlayerOptions(admin.ModelAdmin):
    list_filter = ('kit', 'faction', 'confirmed_cheater')
    search_fields = ['name']

admin.site.register(Server)
admin.site.register(Round)
admin.site.register(Player, PlayerOptions)
admin.site.register(RoundPlayer)
