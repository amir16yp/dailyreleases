# Daily Releases

## Installation and Usage
1. download the zip file/git clone the project
2. extract it
3. open a terminal (or command prompt on windows) in the project directory
4. on linux: `python3 setup.py install`. on windows: `py setup.py install`.
5. run it. on linux :`python3 -m dailyreleases`. on windows: `py -m dailyreleases`
6. edit the config file on linux: `nano ~/.dailyreleases/config.ini`. on windows: 'notepad.exe %USERPROFILE%\.dailyreleases\config.ini`. 
7. run it 24/7: on linux: create a systemd service. on windows: use task scheduler or use an infinite looping batch script.

### Systemd service
`sudo nano /etc/systemd/system/dailyreleases.service`

```
[Unit]
Description=Daily Releases Service
Wants=network-online.target
After=network-online.target

[Service]
# Change user as necessary 
User=root
ExecStart=/usr/bin/python3 -m dailyreleases
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl start dailyreleases
sudo systemctl enable dailyreleases
```

### Windows batch script
open notepad, type the following
```batch
@echo off
:a
py -m dailyreleases
goto a
pause
```
press CTRL + s and save as a .bat file
