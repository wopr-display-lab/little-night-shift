#!/usr/bin/env python3
"""Install/remove only Moonwake's own desktop startup entry; run as normal user."""
import argparse
import os
from pathlib import Path
import shlex

root = Path(__file__).resolve().parent
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--remove',action='store_true')
p.add_argument('--desktop',choices=['auto','labwc','xdg'],default='auto')
args=p.parse_args()
if hasattr(os,'geteuid') and os.geteuid()==0:
    p.error('Run this as your desktop user, without sudo.')
config=Path.home()/'.config'
labwc=config/'labwc/autostart'
desktop=config/'autostart/moonwake-manor.desktop'
marker='# Moonwake Manor (managed by autostart.py)'
old=labwc.read_text() if labwc.exists() else ''
lines=old.splitlines(keepends=True)
clean=''.join(line for line in lines if marker not in line)
if clean!=old:
    labwc.write_text(clean)
if desktop.exists():
    desktop.unlink()
if args.remove:
    print('Moonwake autostart removed. Other startup entries preserved.')
else:
    mode=args.desktop
    if mode=='auto':
        mode='labwc' if 'labwc' in os.environ.get('XDG_CURRENT_DESKTOP','').lower() or labwc.parent.exists() or Path('/usr/bin/labwc').exists() else 'xdg'
    state=Path.home()/'.local/state/moonwake'
    state.mkdir(parents=True,exist_ok=True)
    command='/bin/sh '+shlex.quote(str(root/'start.sh'))+' >>'+shlex.quote(str(state/'display.log'))+' 2>&1'
    if mode=='labwc':
        labwc.parent.mkdir(parents=True,exist_ok=True)
        # Retain distribution startup defaults when creating the user override.
        if not labwc.exists():
            system=Path('/etc/xdg/labwc/autostart')
            clean=system.read_text() if system.exists() else ''
        labwc.write_text(clean.rstrip()+'\n'+command+' & '+marker+'\n')
    else:
        desktop.parent.mkdir(parents=True,exist_ok=True)
        # Desktop Exec quoting is not shell quoting. Use an intermediate launcher.
        launcher=state/'launch.sh'
        launcher.write_text('#!/bin/sh\nexec '+command+'\n')
        quoted=str(launcher).replace('\\','\\\\').replace('"','\\"').replace('`','\\`').replace('$','\\$').replace('%','%%')
        desktop.write_text('[Desktop Entry]\nType=Application\nName=Moonwake Manor\nExec=/bin/sh "'+quoted+'"\nTerminal=false\n')
    print('Installed '+mode+' startup. Enable desktop auto-login and disable screen blanking, then reboot.')
