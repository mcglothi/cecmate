#!/usr/bin/env python3
"""
cecmate.py — CLI and Python API for CECmate HDMI CEC controllers

Usage:
  cecmate.py [--host HOST] [--key KEY] <command>

Commands:
  on      Power on TV and switch to HDMI1
  off     Power off TV (standby)
  hdmi1   Switch to HDMI1
  hdmi2   Switch to HDMI2
  hdmi3   Switch to HDMI3

Environment variables:
  CECMATE_HOST   Device hostname or IP (default: tv-cec.local)
  CECMATE_KEY    ESPHome API encryption key (default: none)

Examples:
  cecmate.py on
  cecmate.py --host baird.home.example.net off
  CECMATE_HOST=192.168.1.100 cecmate.py hdmi2

Requires: pip install aioesphomeapi
"""
import asyncio
import argparse
import os
import sys
import aioesphomeapi

BUTTON_MAP = {
    "on":    "TV Power On",
    "off":   "TV Power Off",
    "hdmi1": "Switch to HDMI1",
    "hdmi2": "Switch to HDMI2",
    "hdmi3": "Switch to HDMI3",
}


async def press_button(host: str, key: str, button_name: str):
    cli = aioesphomeapi.APIClient(host, 6053, "", noise_psk=key or None)
    await cli.connect(login=True)
    entities, _ = await cli.list_entities_services()
    for entity in entities:
        if isinstance(entity, aioesphomeapi.ButtonInfo) and entity.name == button_name:
            cli.button_command(entity.key)
            await asyncio.sleep(0.5)  # allow command to transmit before disconnect
            await cli.disconnect()
            return True
    await cli.disconnect()
    return False


def main():
    parser = argparse.ArgumentParser(
        description="Control a CECmate HDMI CEC controller",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="\n".join(f"  {k:6}  {v}" for k, v in BUTTON_MAP.items()),
    )
    parser.add_argument("command", choices=BUTTON_MAP.keys())
    parser.add_argument("--host", default=os.environ.get("CECMATE_HOST", "tv-cec.local"),
                        help="Device hostname or IP (env: CECMATE_HOST)")
    parser.add_argument("--key", default=os.environ.get("CECMATE_KEY", ""),
                        help="ESPHome API encryption key (env: CECMATE_KEY)")
    args = parser.parse_args()

    button = BUTTON_MAP[args.command]
    ok = asyncio.run(press_button(args.host, args.key, button))
    if ok:
        print(f"OK: {button}")
    else:
        print(f"Error: button '{button}' not found on {args.host}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
