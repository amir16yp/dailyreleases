# Daily Releases

### Installation
The easiest way to install the bot is to use pip:

```bash
pip3 install --upgrade https://git.caspervk.net/caspervk/dailyreleases/archive/master.tar.gz
```

**It requires Python 3.7 or later.**

### Usage
The bot can be started by running `dailyreleases` or `python3 -m dailyreleases` depending on system configuration.

### Configuration
The default configuration file will be copied to `~/.dailyreleases/config.ini` on the first run. All fields under the
`[reddit]` and `[google]` sections need to be filled out before the bot can be initialized.

To append content to the generated post, add a file `~/.dailyreleases/epilogue.txt`.