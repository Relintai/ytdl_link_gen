# YTDL Link Gen

A little python script that helps archiving youtube (and other) channels using yt-dlp.

## Features

- Generates a simple batch file that you can use to get everything.
- Skips downloading all video metadata, unlike vanilla yt-dlp.
- Keeps track the videos you have without needing to keep the videos accessible, and only dowloads missing stuff.
- Numbers each video, also remembers old numbering (meaning: deleted videos will not screw it up).
- Backs up it's own data before an update.

## Usage

### Python

First make sure that you have python 3 installed.

#### Without python virtual environments (global install)

Install yt-dlp:

` sudo pip install yt-dlp  `

#### Using python virtual environments

create a new virtual environment in the current folder:

` python -m venv venv `

This will create a new venv folder.

Activate it:

POSIX:

bash/zsh ` $ source venv/bin/activate `\
fish ` $ source venv/bin/activate.fish `\
csh/tcsh ` $ source venv/bin/activate.csh `\
PowerShell ` $ venv/bin/Activate.ps1 `\
bash (alternate) ` $ . ./venv/bin/activate `

Windows:
	
cmd.exe ` C:\> venv\Scripts\activate.bat `\
PowerShell ` PS C:\> venv\Scripts\Activate.ps1 `
	
Install the newest yt-dlp (Recommended, as sites change a lot.):

` pip install yt-dlp  `

Or install the last tested version (In case the newest doesn't work):

` pip install -r requirements.txt  `

Here are the [full python virtualenv docs](https://docs.python.org/3/library/venv.html) if needed.

### Script

Set up your config file:

` cp config.txt.example config.txt `

Add all channels that you want to grab to your new config.txt.

Run the script:

` python ytdl_link_gen.py `

If you run into any issue you can safely run the script again, it will continue where it left off.

Once this is finished you can (and should, if you want to update videos again) delete the new `temp` directory which got created. It contains channel data,
so if an error occurs it won't have to re-download channel lists again.

You should have a ` dl.sh ` now. Containing yt-dlp commands to all videos since the previous run.

Run it single threaded:

``` 
chmod +x dl.sh 
./dl.sh
```

Or for example using parallel:

` parallel -j4 -a dl.sh --progress `

### Note

If you get an error conplaining about a null object being unindexable check the .json for that channel in the temp directory.
if it only has a null in in delete it. That should solve the issue.
