# Description: This file sets how Django loads the app. I modified it in order to support the signals.py module.

from django.apps import AppConfig

class MeowseumConfig(AppConfig):
    name = 'Meowseum'
    def ready(self):
        import Meowseum.signals
