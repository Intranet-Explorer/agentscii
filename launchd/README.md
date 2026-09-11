# launchd setup (AGENTSCII)

Same pattern as antfarm2-standalone: both the watchdog (supervising
harness.py) and the dashboard run as real macOS launchd agents, not ad-hoc
background shell processes, so they survive terminal sessions, crashes, and
reboots.

## Install
    cp launchd/com.agentscii.watchdog.plist ~/Library/LaunchAgents/
    cp launchd/com.agentscii.dashboard.plist ~/Library/LaunchAgents/
    launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.agentscii.watchdog.plist
    launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.agentscii.dashboard.plist

## Check status
    launchctl list | grep agentscii

## Stop supervision entirely (e.g. before manual debugging)
    launchctl bootout gui/$(id -u)/com.agentscii.watchdog
    launchctl bootout gui/$(id -u)/com.agentscii.dashboard

Normal stop/start/restart should go through the dashboard control panel
(/api/control/*) or `touch STOP` in ~/agentscii/ — launchd notices the clean
exit and, for the watchdog, respects the STOP flag exactly like antfarm2's
does. KeepAlive only restarts on non-clean exit, not after every stop.
