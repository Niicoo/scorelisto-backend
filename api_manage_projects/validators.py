from django.core.validators import RegexValidator

# Project name
ProjectNameValidator = RegexValidator(regex='^[a-zA-Z0-9][a-zA-Z0-9 ]{3,32}(?<! )$', message="RegEx don't match: ^[a-zA-Z0-9][a-zA-Z0-9 ]{3,32}(?<! )$ ", code='nomatch')

# Project filename
ProjectFilenameValidator = RegexValidator(regex='^.{1,255}$', message="RegEx don't match: ^.{1,255}$ ", code='nomatch')

# Project instrument
ProjectInstrumentValidator = RegexValidator(regex='^[a-zA-Z0-9][a-zA-Z0-9 ]{3,32}(?<! )$', message="RegEx don't match: ^[a-zA-Z0-9][a-zA-Z0-9 ]{3,32}(?<! )$ ", code='nomatch')
