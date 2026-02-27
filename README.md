# CECmate

**WiFi-connected HDMI CEC controller built on ESP32 + ESPHome.**

Control any CEC-capable TV's power and input switching from scripts, automations, voice assistants, or AI agent workflows — using $5 in hardware and a spare HDMI cable.

---

## Features

- Power on / off any HDMI CEC-compatible TV
- Input switching (HDMI 1, 2, 3, ...)
- Native Home Assistant integration via ESPHome auto-discovery
- Python CLI for scripting and automation (`cecmate.py`)
- OTA firmware updates — no re-flashing after initial setup
- Works with Samsung (Anynet+), LG (SimpLink), Sony (Bravia Sync), Panasonic (VIERA Link), and most other CEC implementations

---

## Hardware

### Bill of Materials

| Component | Qty | Notes |
|-----------|-----|-------|
| ESP32-WROOM-32 dev board | 1 | Any `esp32dev`-compatible board |
| Spare HDMI cable | 1 | Cut one end off — either end works, HDMI cables are not directional |
| 10kΩ resistor | 1 | ¼W, any tolerance |
| USB power supply | 1 | 5V micro-USB or USB-C — **the TV's own USB port works great** and keeps everything on one power switch |

**Total cost: ~$5–8**

---

### Wiring

HDMI CEC uses only two wires. Cut the HDMI cable and identify the following pins:

| HDMI Pin | Signal | Connect to |
|----------|--------|------------|
| **13** | CEC | ESP32 GPIO21 (see diagram) |
| **17** | GND | ESP32 GND |

> **Wire identification:** HDMI cable colors are not standardized.
> Use a multimeter in **continuity mode** — probe Pin 13 and Pin 17 on the connector
> while touching each exposed wire until it beeps.
>
> HDMI Type A pin layout (plug face, tab side down):
> ```
>  ___________________________________________
> |  1  3  5  7  9  11 [13] 15  17  19       |
> |   2  4  6  8  10  12  14  16  18         |
> |___________________________________________|
>                            ^ GND
> ```

### Wiring Diagram

```
  HDMI Cable (cut end)              ESP32-WROOM-32
                               ┌────────────────────┐
                               │                    │
  Pin 13 (CEC) ────────────────┤ GPIO21 (D21)       │
                       ┌───────┤                    │
                      10kΩ     │                    │
                       └───────┤ 3.3V               │
                               │                    │
  Pin 17 (GND) ────────────────┤ GND                │
                               │                    │
                               └────────────────────┘
```

> The 10kΩ resistor is a **pull-up** — one leg on GPIO21, other leg on 3.3V.
> Connect the CEC wire directly to GPIO21 (not in series through the resistor).

---

## Software Setup

### 1. Install ESPHome

```bash
python3 -m venv esphome-venv
source esphome-venv/bin/activate
pip install esphome
```

### 2. Configure

```bash
cp secrets.yaml.example secrets.yaml
# Edit secrets.yaml with your WiFi credentials and a generated API key:
#   esphome -q config generate-api-key
```

Edit `tv-cec.yaml` and make these per-device changes:

**1. Set a unique device name** — controls the hostname and Home Assistant entity IDs. If you deploy multiple CECmate devices, each must have a different name:
```yaml
esphome:
  name: bedroom-cec        # unique per device
  friendly_name: Bedroom TV CEC Controller
```

**2. Set `physical_address`** to match which HDMI port you plug into:

| HDMI Port | physical_address |
|-----------|-----------------|
| HDMI 1 | `0x1000` |
| HDMI 2 | `0x2000` |
| HDMI 3 | `0x3000` |

**3. Adjust the Power On opcode for non-Samsung TVs** — the default config uses `0x86` (Set Stream Path), which works best on Samsung. For LG, Sony, and Panasonic, change the Power On button's second send to use `0x82` (Active Source) instead. See the comment in `tv-cec.yaml` and [Known Issues](#known-issues--quirks) below.

### 3. Flash (first time, USB only)

Put the board in bootloader mode:
1. Hold **BOOT** button
2. Press and release **EN** (reset)
3. Release **BOOT**

Then flash:
```bash
esphome run tv-cec.yaml
```

All subsequent updates are OTA — no more USB required.

### 4. Enable CEC on your TV

| Brand | Setting |
|-------|---------|
| Samsung | Settings → General → External Device Manager → **Anynet+ (HDMI-CEC)** → On |
| LG | Settings → General → **SIMPLINK (HDMI-CEC)** → On |
| Sony | Settings → Watching TV → External inputs → **Bravia Sync** → On |
| Panasonic | Menu → Setup → **VIERA Link** → On |
| Other | Look for "HDMI-CEC", "Anynet", or "SimpLink" in the TV's settings |

---

## Python CLI

Install the dependency:

```bash
pip install aioesphomeapi
```

Run commands:

```bash
# Using hostname (set in ESPHome config)
python3 cecmate.py --host tv-cec.local on
python3 cecmate.py --host tv-cec.local off
python3 cecmate.py --host tv-cec.local hdmi2

# Using environment variable
export CECMATE_HOST=tv-cec.local
export CECMATE_KEY=your_api_encryption_key
python3 cecmate.py on
```

> **Note:** Use `cecmate.py` (native ESPHome API, port 6053) for scripting rather than
> the web server REST endpoints — the REST API can trigger a crash when CEC commands
> are sent from the HTTP handler context.

---

## Home Assistant

CECmate devices running ESPHome are **automatically discovered** by Home Assistant once both are on the same network. All buttons appear as entities ready to use in:

- Automations and scripts
- Google Assistant / Amazon Alexa / Apple HomeKit (via HA)
- AI agent workflows via HA REST API

---

## CECmate Hardware Module *(coming soon)*

We're designing a compact PCB that integrates an ESP32, onboard HDMI connector, and pull-up resistor in a single unit — **no soldering, no loose wires, just plug in and flash.**

If you'd like to be notified when it's available, **star this repo**.

---

## Known Issues / Quirks

- **ESPHome 2026.x — required one-time patch:** The `johnboiles/esphome-hdmi-cec` external
  component has a bug where `add_library()` passes `None` as the library name, which ESPHome
  2026.x rejects. Your first compile will fail. After it does, patch the cached file:
  ```bash
  # Find the file (the hash in the path varies per machine):
  find ~/.esphome/external_components -path "*/hdmi_cec/__init__.py"

  # Edit it — around line 107, change:
  #   cg.add_library(None, None, ...)
  # to:
  #   cg.add_library("CEC", None, ...)
  ```
  Then re-run `esphome run tv-cec.yaml`. Only needs doing once per machine.

- **Samsung power-on sequence:** Samsung TVs respond better to `Set Stream Path` (opcode
  `0x86`) than `Active Source` (`0x82`) for input switching after wake. The included
  config uses `0x86` for the Power On button.

- **Samsung Anynet+ must be enabled** — Samsung TVs silently ignore all CEC commands if
  Anynet+ is disabled in settings.

---

## License

MIT
