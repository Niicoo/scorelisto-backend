
INSTALLATION
============

## Apache (in production only)  
`sudo apt update`  
`sudo apt install apache2 apache2-dev`  

## PostgreSQL   
`sudo apt-get update`  
`sudo apt-get install postgresql postgresql-contrib`  

## WORKER AND BROKER: CELERY and RABBITMQ  
`sudo apt-get install rabbitmq-server`  

## VIRTUALENV  
**Mkae sure to have python3 installed in the system**  
`sudo apt install python3-venv python3-pip`  
`pip3 install -U pip`  
`pip install virtualenv`  

## Let's encrypt with Certbot (in production only)  
(<https://letsencrypt.org/getting-started/>)  
(<https://certbot.eff.org/lets-encrypt/ubuntubionic-apache>)  
`sudo apt-get update`  
`sudo apt-get install software-properties-common`  
`sudo add-apt-repository universe`  
`sudo add-apt-repository ppa:certbot/certbot`  
`sudo apt-get update`  
`sudo apt-get install certbot python-certbot-apache`  


CONFIGURATION
=============

## PostgreSQL
**=> Set a different password in production !!!**   
`sudo su - postgres`  
`psql`  
`CREATE USER username WITH PASSWORD 'dbpassword';`  
`ALTER ROLE username SET client_encoding TO 'utf8';`  
`ALTER ROLE username SET default_transaction_isolation TO 'read committed';`  
`ALTER ROLE username SET timezone TO 'UTC';`  
`CREATE DATABASE scorelistodb;`  
`GRANT ALL PRIVILEGES ON DATABASE scorelistodb TO username;`  

## VirtualEnv  
`virtualenv --python=/usr/bin/python3.6 /virtualenvs/djangoenv`  
`source /virtualenvs/djangoenv/bin/activate`  
`python -m  pip install numpy scipy lxml`   
`python -m  pip install django-oauth-toolkit django-cors-middleware celery Django psycopg2 djangorestframework celery SQLAlchemy`  

## ScoreListCopy scorelisto master to /root/scorelisto and go into it then: 
`cd /root`  
`git clone git@gitlab.com:Niicoo/scorelisto_lib.git .`  
`cd scorelisto_lib`  
`source /virtualenvs/djangoenv/bin/activate`  
`python setup.py install --record scorelisto_installed_files.txt`  

## MOD_WSGI  
(<https://docs.djangoproject.com/fr/2.1/howto/deployment/wsgi/modwsgi/>)  
(<https://modwsgi.readthedocs.io/en/develop/index.html>)  
**Install mod_wsgi**  
`./configure --with-python=/virtualenvs/djangoenv/bin/python`  
`make`  
`make install`  


## Apache/Certbot  
(<https://tutorials.ubuntu.com/tutorial/install-and-configure-apache#0>)  
**Create a folder "api" inside /var/www/**  
`mkdir /var/www/api`  
**Create a file named api.conf inside /etc/apache2/sites-available**  
`nano /etc/apache2/sites-available/api.conf`  
**[File content]**  
```
WSGIDaemonProcess api python-home=/pythonenvs/djangoenv python-path=/var/www/api
WSGIProcessGroup api
<VirtualHost *:80>
	ServerAdmin support@scorelisto.com
	DocumentRoot /var/www/api
	WSGIScriptAlias / /var/www/api/be_django_rest_api/wsgi.py
	WSGIPassAuthorization On

	<Directory /var/www/api/be_django_rest_api>
		<Files wsgi.py>
			Require all granted
		</Files>
	</Directory>

	Alias /static/ /var/www/api/be_django_rest_api/static/
	<Directory /var/www/api/be_django_rest_api/static>
		Require all granted
	</Directory>

	#LogLevel info ssl:warn
	ErrorLog ${APACHE_LOG_DIR}/error.log
	CustomLog ${APACHE_LOG_DIR}/access.log combined
ServerName api.scorelisto.com
RewriteEngine on
RewriteCond %{SERVER_NAME} =api.scorelisto.com
RewriteRule ^ https://%{SERVER_NAME}%{REQUEST_URI} [END,NE,R=permanent]
</VirtualHost>
```

**Edit/Add the following lines inside file: /etc/apache2/sites-available/000-default.conf**  
`nano /etc/apache2/sites-available/000-default.conf`  
**[Lines to edit]**  
```
ServerAdmin support@scorelisto.com
DocumentRoot /var/www/html
ServerName www.scorelisto.com
ServerAlias scorelisto.com
```

**Create ssl certificates (https)**  
`sudo certbot --apache -d api.scorelisto.com -d www.scorelisto.com`  


**Edit/Add the following line inside file: /etc/apache2/sites-available/000-default.conf**  
`nano /etc/apache2/sites-available/000-default.conf`  
**[Line to edit]**  
`RewriteRule ^ https://www.scorelisto.com%{REQUEST_URI} [END,NE,R=permanent]`  

**Edit/Add the following line inside file: /etc/apache2/sites-available/000-default-le-ssl.conf**  
`nano /etc/apache2/sites-available/000-default-le-ssl.conf`  
**[Line to edit]**  
```
RewriteEngine on
RewriteCond %{SERVER_NAME} =scorelisto.com
RewriteRule ^ https://www.scorelisto.com%{REQUEST_URI} [END,NE,R=permanent]
```    



**For the moment, I won't put scorelisto.com on this website, I configured it but I deactivate it**  
`sudo a2dissite 000-default-le-ssl 000-default`  
[In the .htaccess of the other server]
```  
RewriteEngine On
RewriteCond %{HTTPS} off [OR]
Rewritecond %{HTTP_HOST} !^www\.scorelisto\.com
RewriteRule (.*) https://www.scorelisto.com/$1 [R=301,L]

RewriteCond %{REQUEST_FILENAME} -f
RewriteRule .? - [L]

RewriteRule ^/css(/|$) - [L,NC]
RewriteRule ^/img(/|$) - [L,NC]
RewriteRule ^/js(/|$) - [L,NC]

# Rewrite all other queries to the front controller.
RewriteRule ^ index.html [L]
```  


## DJANGO/CELERY  
**Folder where data are stored**  
`mkdir -p /data/backend/media`  
**Create 'celery' user**  
`adduser celery`  
**Clone django backend into the api directory**   
`cd /var/www/api/`  
`git clone git@gitlab.com:Niicoo/scorelisto_backend.git .`  

**Create a package into the virtualenv containing the sensitive data**  
`mkdir /virtualenvs/djangoenv/lib/python3.6/site-packages/django_variables`  
`touch /virtualenvs/djangoenv/lib/python3.6/site-packages/django_variables/__init__.py`  
`nano /virtualenvs/djangoenv/lib/python3.6/site-packages/django_variables/api_variables.py`  
**[File content]**  
```
DJANGO_SETTINGS_MODULE = 'production'
DJANGO_PSQL_DB_PW =  ""
DJANGO_SECRET_KEY = ""
DJANGO_SUPPORT_EMAIL_PW = ""
```

**Create the celery service**  
`nano /etc/systemd/system/celery.service`  
**[file content]**  
```
[Unit]
Description=Celery Service
After=network.target

[Service]
Type=forking
User=celery
WorkingDirectory=/var/www/api
Environment=CELERYD_NODES="celeryworker"
Environment=CELERY_BIN="/virtualenvs/djangoenv/bin/celery"
Environment=CELERY_APP="be_django_rest_api"
Environment=CELERY_MULTI="multi"
Environment=CELERYD_LOG_FILE="/var/log/celery/%n%I.log"
Environment=CELERYD_PID_FILE="/var/run/celery/%n.pid"
Environment=CELERYD_LOG_LEVEL="INFO"
Environment=CELERYD_OPTS="--time-limit=300 --concurrency=8"
RuntimeDirectory=celery

ExecStart=/bin/sh -c '${CELERY_BIN} multi start ${CELERYD_NODES} \
  -A ${CELERY_APP} --pidfile=${CELERYD_PID_FILE} \
  --logfile=${CELERYD_LOG_FILE} --loglevel=${CELERYD_LOG_LEVEL} ${CELERYD_OPTS}'

ExecStop=/bin/sh -c '${CELERY_BIN} multi stopwait ${CELERYD_NODES} \
  --pidfile=${CELERYD_PID_FILE}'

ExecReload=/bin/sh -c '${CELERY_BIN} multi restart ${CELERYD_NODES} \
  -A ${CELERY_APP} --pidfile=${CELERYD_PID_FILE} \
  --logfile=${CELERYD_LOG_FILE} --loglevel=${CELERYD_LOG_LEVEL} ${CELERYD_OPTS}'

[Install]
WantedBy=multi-user.target
```


**Creating the required folders**  
```
mkdir /var/log/celery
mkdir /var/run/celery
mkdir -p /data/backend/media
sudo chown -R celery /var/log/celery/ /var/run/celery/
sudo chmod -R 770 /var/log/celery/ /var/run/celery/
sudo usermod -a -G celery www-data
sudo chown -R www-data /data/backend/media/
sudo chgrp -R celery /data/backend/media/
sudo chmod 2770 /data/backend/media
```

USAGE
=====

## In Development  
`source activate djangoenv`  
`python manage.py runserver --settings=be_django_rest_api.settings.local` 
**=> Se placer dans le dossier principal du backend !!!**  
`celery -A be_django_rest_api worker -B --loglevel=info`  

## In Production
`sudo systemctl reload apache2 celery`  
`sudo systemctl restart apache2 celery`  


## APACHE 
`apachectl -V`  
`sudo systemctl status apache2`  
`sudo systemctl reload apache2`  
`sudo systemctl restart apache2`  
`sudo a2ensite`  
`sudo a2dissite`  
`sudo a2enmod`  
`sudo a2dismod`  


## CREATING A DJANGO PROJECT
`django-admin startproject djangoproject`  
`python manage.py startapp myappname`  
`python manage.py makemigrations api_manage_users api_manage_projects api_manage_parameters`  
`python manage.py makemigrations`  
`python manage.py migrate`  
`python manage.py createsuperuser --username=name --email=mail@live.fr`  


## CREATING THE CLIENT ID AND CLIENT SECRET
1. Connect to the ADMIN DJANGO page  
2. CREATE APPLICATION  
   * CLIENT TYPE : CONFIDENTIAL  
   * AUTHORIZATION GRANT TYPE : RESSOURCE OWNER PASSWORD BASED  
   * NAME : ScoreListo Website  



## PostgreSQL  
**To enter into psql**  
`sudo su - postgres`  
`psql`  

**To delete a database**  
`DROP DATABASE scorelistodb;`  


## Inside OVH: to connect the server with the domain name  
add a "A" entrie in the domain with the server ipv4 adress  

# Checking https  
https://www.ssllabs.com/ssltest/analyze.html?d=scorelisto.com  

# Upgrade packages  
`sudo apt-get update`  
`sudo apt-get upgrade`  
`sudo apt-get dist-upgrade`  



TO DO LIST
==========

## MANDATORY

* Envoie des mails dans des tasks celery
* Bien verifier les blank = True null = True
* re bien definir les json renvoyer dans les requetes, virer les json inutiles quand c'est juste true false
* verifier CORS_ALLOW_HEADERS dans le settings.py
* Mettre a jour le ProjectFilenameValidator
* Faire en sorte que "state" et "task_id" se mettent automatiquement sur les sorties au lieu de le faire manuellement

## OPTIONAL

* Permettre d'autre format de fichier, automatiquement convertit avec ffmpeg ou bien une librairie python
* Rendre possible la connexions sans utilisateur/mot de passe mais plutot avec un id pour les applications android ( a voir si on peut mettre les 2)
* La manière dont mon backend est fait me permet assez facilement de modifier les resultats intermediaire en rajoutant des vues pour actualiser les results
* Gerer la reponse quand j'essaye de creer un compte avec un email d'un compte supprimer mais pas encore enlever
* Utiliser WebSocket pour la progress bar
* possibilité de lancer les conversions stepbystep avec les noms de parametres enregistrés aussi
* Task killed un peu brutalement => verifier impact memoire
* Suppression d'un compte premium : garder la date de fin premium + email de l'utilisateur
* faire la vue pour changer d'username
* faire la vue pour changer d'adresse email
* Compatibilité des waves super limités... juste certain format de dispo.. 
* faire une vue pour acquerir les valeurs par defaut pour chaque parametres
* Faire un check sur la robustesse des etapes