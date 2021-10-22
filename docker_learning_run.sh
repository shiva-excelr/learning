#!/bin/sh


git checkout master
git pull origin master



echo "\n\n === Sleeping for 5 sec(s) ==="
sudo docker build -t learning .


docker run --name learning learning


