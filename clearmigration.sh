# -*- coding: utf-8 -*-
#!/bin/sh

for entry in ./*
do
    if [ -d "$entry" ]
    then
        for subentry in "$entry"/*
        do
            filename=$(basename $subentry)
            if [ "$filename" = "__pycache__" ] 
            then
                rm -rf "$subentry"
            fi
            if [ "$filename" = "migrations" ] 
            then
                for subsubentry in "$subentry"/*
                do
                    subfilename=$(basename $subsubentry)
                    if [ "$subfilename" != "__init__.py" ]
                    then
                        rm -rf "$subsubentry"
                    fi
                done
            fi
        done
    fi
done

#python manage.py flush
#python manage.py createsuperuser --username=ndejax --email=nicolas.dejax@live.fr
#python manage.py makemigrations
#python manage.py migrate
#python manage.py runserver
