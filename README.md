# printlist
Displays the print queue of Berkeley OCF printers on a web page for easy viewing.

dependencies: redis, flask, gunicorn

useful links: https://github.com/ocf/labmap/blob/master/Dockerfile

useful command: `sudo docker run -d -it -p 8000:8000 --name printlist-gunicorn print-disp`

Developer Mode: `python3 main.py --dev` *Sends a "Print" every 5 seconds*