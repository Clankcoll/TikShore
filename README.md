# TikShore
Automates uploading the latest YouTube Shorts to TikTok, ideal for influencers managing multiple platforms with minimal effort.

FFMPEG needs to be installed on the maschine running this script as we are seperatly downloading best audio and video and then combining it
On Windows
Download FFmpeg:

Go to the FFmpeg download page and navigate to the Windows section.
You can use third-party builds, such as Gyan.dev FFmpeg Builds.
Download the latest release of the "essentials" or "full" build (ZIP file).
Extract and Set PATH:

Extract the downloaded ZIP file to a location on your computer, for example, C:\ffmpeg.
Add the bin directory of ffmpeg to your system PATH:
Right-click on This PC or Computer and choose Properties.
Go to Advanced system settings.
Click on Environment Variables.
Under System variables, find and select the Path variable, then click Edit.
Add the path to the ffmpeg\bin directory, for example, C:\ffmpeg\bin, then click OK to close all dialogs.

#TODOS
Fix Best quality combination since it seems that it is not working

Add reupload functionality to TikTok

Rewrite better readme

Add requirmentsfile for easy installation

Make Docker Image from this for easy deployment