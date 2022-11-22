from django.core.validators import RegexValidator
from django.core.validators import MinValueValidator, MaxValueValidator

# Project name
ParameterNameValidator = RegexValidator(regex='^[a-zA-Z0-9][a-zA-Z0-9 ]{3,32}(?<! )$', message="RegEx don't match: ^[a-zA-Z0-9][a-zA-Z0-9 ]{3,32}(?<! )$ ", code='nomatch')

# Parameters validators

# PITCH
validators_windowtimesize_s = [MinValueValidator(1e-4), MaxValueValidator(1)]
validators_sonogramperiod_s = [MinValueValidator(1e-6), MaxValueValidator(1)]
validators_f0_hz = [MinValueValidator(1e-6), MaxValueValidator(1e6)]
validators_freqmin_hz = [MinValueValidator(1e-3), MaxValueValidator(1e6)]
validators_freqmax_hz = [MinValueValidator(1e-3), MaxValueValidator(1e6)]
validators_cutoff = [MinValueValidator(0), MaxValueValidator(1)]
validators_smallcutoff = [MinValueValidator(0), MaxValueValidator(1)]
# Optionals
validators_timestart_s = [MinValueValidator(0), MaxValueValidator(1000)]
validators_timestop_s = [MinValueValidator(0), MaxValueValidator(1000)]

# STEP
validators_medianfiltersize_s = [MinValueValidator(1e-3), MaxValueValidator(1)]
validators_thresholdenergyon_db = [MinValueValidator(0.1), MaxValueValidator(200)]
validators_thresholdenergyoff_db = [MinValueValidator(0.1), MaxValueValidator(200)]
validators_maxpitchvariation_st = [MinValueValidator(0.01), MaxValueValidator(12)]
validators_minimumtimesize_s = [MinValueValidator(1e-3), MaxValueValidator(1)]
validators_minnotesize_s = [MinValueValidator(1e-3), MaxValueValidator(1)]
validators_minnotediff_st = [MinValueValidator(1e-3), MaxValueValidator(12)]
validators_lmhgaussian_st = [MinValueValidator(1e-3), MaxValueValidator(12)]

# RYTHM
validators_delaymin_s = [MinValueValidator(0.29), MaxValueValidator(1.51)]
validators_delaymax_s = [MinValueValidator(0.29), MaxValueValidator(1.51)]
validators_maxdelayvar = [MinValueValidator(1e-3), MaxValueValidator(1)]
validators_errormax = [MinValueValidator(1e-3), MaxValueValidator(100)]
