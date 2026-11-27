# Syrian Warfare Configurator

An unofficial, open-source configuration utility for Syrian Warfare that expands the game's customisation options beyond those available in the original settings menu.

Designed to modernise the game's controls, improve accessibility and provide greater control over the gameplay experience.

**No AutoHotkey, external overlays or background applications are required during gameplay.**

## Download

[Download the latest release](../../releases/latest)

## Features

### Controls
- Native WASD camera movement.
- Optional traditional arrow key movement.
- Enable or disable edge scrolling.
- Customisable contextual keybindings.
- Automatic synchronisation of command tooltips.
- Keybinding conflict detection.
- Dedicated WASD control preset.

### Camera
- Adjustable minimum and maximum zoom.
- Adjustable camera tilt.
- Configurable field of view.
- Adjustable near clipping plane.
- Cinematic camera preset.
- Camera conversion for existing tactical saves.

### Graphics
- Expanded graphics settings.
- Shadow quality and distance settings.
- Grass rendering distance.
- Camera movement and cursor speed adjustments.

### Advanced Customisation
- Difficulty settings.
- Experience progression.
- Infantry and squad properties.
- Weapon and ammunition properties.
- Vehicle properties.
- Import and export configuration presets.

### General
- Automatic Steam installation detection.
- Support for custom Steam library locations.
- Automatic game profile detection.
- Persistent preferences.
- Dark and light interface themes.
- Automatic backups.
- Reversible native camera modifications.

## Requirements

- Windows.
- Syrian Warfare v1.2.1.53.
- Python 3.10 or newer with Tkinter.

[Download Python](https://www.python.org/downloads/)

## Installation

1. Download the latest release from GitHub.
2. Extract the ZIP into any writable folder.
3. Close Syrian Warfare.
4. Double-click `Run.bat`.
5. Locate your game installation if automatic detection fails.
6. Customise your settings and select **Apply changes**.
7. Launch Syrian Warfare normally.

The configurator does not need to remain open while playing.

## Restoring Original Settings

Native camera modifications are reversible through the configurator.

To restore the original camera controls, select **Arrows**, enable edge scrolling and apply your changes.

Contextual keybindings can be restored separately using the **Restore stock bindings** option.

Backups are automatically created when modifying existing files. Refer to the included [README.txt](README.txt) for detailed restoration and troubleshooting instructions.

## Compatibility and Limitations

- Native camera modifications currently support game version 1.2.1.53.
- Unsupported or unrecognised game binaries are rejected.
- Tooltip synchronisation has been developed using English localisation resources.
- Some contextual keybinding conflict warnings are advisory.
- Automatic installation and profile detection may vary between systems.
- A runtime HUD visibility toggle is not currently available.

Game updates or Steam file verification may restore modified game binaries.

## Support and Feedback

Bug reports, suggestions and compatibility feedback are welcome.

Please use the [Issues](../../issues) section and include your game version, configurator version and a description of the problem.

## Disclaimer

This is an unofficial community project and is not affiliated with the developers or publishers of Syrian Warfare.

No original or modified game binaries are distributed. All modifications are applied locally to the user's existing installation.

## Licence

This project is released under the [MIT License](LICENSE).
