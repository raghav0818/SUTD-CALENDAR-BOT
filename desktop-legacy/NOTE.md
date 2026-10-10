# Superseded

This is the original desktop version: a Python app that drove Chrome with Selenium.

**It has been replaced by the browser extension in [`../extension`](../extension).**

The extension does the same job without any of this version's friction. It runs inside the
portal tab you are already logged into, so there is no second Chrome window, no logging in
and doing 2FA a second time, no Python to install, and it works in whatever browser you
normally use.

This folder is kept only because the extension's parser was ported from
`sutd_calendar_bot.py` and it is useful to be able to read the original. It still runs
(double-click `Start SUTD Bot.bat` on Windows or `Start SUTD Bot.command` on macOS) but it
is no longer maintained, and fixes land in the extension instead.
