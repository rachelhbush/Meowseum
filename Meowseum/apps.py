# apps_v0_0_2.py by Rachel Bush. Date finished: 12/26/2016 6:33AM
# PROGRAM ID: apps.py (_v0_0_2) / App page
# REMARKS: This file sets how Django loads the app. I modified it in order to support the signals.py module.

from django.apps import AppConfig

class MeowseumConfig(AppConfig):
    name = 'Meowseum'
    def ready(self):
        import Meowseum.signals
