from constants import PRESETS

def apply_preset(self, preset_name):
    preset = PRESETS.get(preset_name)
    if preset:
        for attr, value in preset.items():
            getattr(self, attr).set(value)

def set_covid_params(self):
    self.apply_preset("COVID-19")

def set_spanish_flu_params(self):
    self.apply_preset("Grippe espagnole")