from django.core.validators import RegexValidator

# Username
UsernameValidator = RegexValidator(regex='^[a-zA-Z0-9_]{6,20}$', message="RegEx don't match: ^[a-zA-Z0-9_]{6,20}$ ", code='nomatch')

# Password
PasswordValidator = RegexValidator(regex='^.{8,32}$', message="RegEx don't match: ^.{8,32}$ ", code='nomatch')

# Contact
BodyContactValidator = RegexValidator(regex='^[\s\S]{8,5000}$', message="RegEx don't match: ^[\s\S]{8,5000}$ ", code='nomatch')
PhoneContactValidator = RegexValidator(regex='^.{0,100}$', message="RegEx don't match: ^.{0,100}$ ", code='nomatch')
NameContactValidator = RegexValidator(regex='^.{4,64}$', message="RegEx don't match: ^.{4,64}$ ", code='nomatch')
