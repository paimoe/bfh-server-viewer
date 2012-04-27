import sys
sys.path = ['C:/Documents and Settings/paimoe/Desktop/Python/bfh', 'C:/Documents and Settings/paimoe/Desktop/Python/website'] + sys.path

# Import django crapola
from django.core.management import setup_environ
import settings
setup_environ(settings)
#

log_dir = 'website/logs'
