from django.conf.urls.defaults import *
import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^bfh/', include('bfh.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^$', 'website.views.server_list'),
    
    (r'round/(?P<roundid>\d+)$', 'website.views.view_game'),
    (r'server/(?P<server_id>\d+)$', 'website.views.server_view'),
    (r'hero/(?P<hero_id>\d+)$', 'website.views.hero_view'),
    
    # For CleverCSS so i don't have to edit in the damn admin panel
    (r'^css/(?P<file>.+)$', 'website.views.render_css'),
    
    # Updater
    (r'^update/$', 'website.update.do'),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns('',
		(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT} ),
	)
