SYRIAN WARFARE CONFIGURATOR v0.7
Supported game build: 1.2.1.53 (Windows, original bin/game.dll)

GETTING STARTED
1. Install Python 3.10 or newer with Tkinter (the standard Windows Python installer
   includes Tcl/Tk by default). https://www.python.org/downloads/
2. Extract every file in this ZIP to any writable folder. Keep Configurator.py,
   CameraWASD.py and Run.bat together. No DLLs are distributed.
3. Close Syrian Warfare and double-click Run.bat. The tool attempts to detect Steam
   and its libraries, including non-default library drives. If it cannot find a
   unique installation, click Browse game and select the Syrian Warfare folder.
   In Steam: Library > Syrian Warfare > Manage > Browse local files.
4. Profile settings are detected separately in Documents (including redirected
   Documents/OneDrive). If needed, select gameoptions.xml manually. Run the game
   at least once to create a profile.
5. Stage your changes and click Apply changes. Then launch the game normally.
   The configurator does not need to remain open. No AutoHotkey is required.

UPGRADING
Close the game and configurator. Replace the files from the previous release.
Existing preferences, overrides and supported native patches are detected. CameraWASD.py is a required internal module, not a separate launcher.
Preferences are stored in LOCALAPPDATA/SyrianWarfareConfigurator/preferences.json.
No preconfigured installation path or user profile is distributed.

CONTROLS
Choose Arrows or WASD, and independently enable or disable edge scrolling.
Changes are staged until Apply. The WASD + free conflicting keys preset moves
contextual W/A/S/D bindings to T/G/H/B. Review overlaps before applying.
Double-click a command to change its binding: A-Z or the verified up token.
Contextual bindings and mapped tooltips use loose overrides:
  basis/scripts/species/hotkeys.xml
  basis_loc/locale/strres.xml
There are 30 mapped tooltips; 33 editable existing bindings; two trailer rows
without a key field. Original pressed flags are preserved. Main-command overlap
warnings are advisory; submenu overlaps are flagged. Other keyboard tokens,
compound expressions and arbitrary camera bindings are not supported.

RESTORATION AND BACKUPS
Choose Arrows and tick Enable edge scrolling, then Apply to restore the exact
stock DLL. Contextual bindings are independent: use Restore stock bindings and
Apply to restore default keys/tooltips. This does not remove loose override files.
A verified original DLL is retained as bin/game.dll.wasd-original.bak. Additional
backups of existing modified files are created in SWConfiguratorBackups folders
beside the affected files. To restore a prior custom override, copy its backup
back with the game closed. If the override was newly created, deleting just that
file restores archive behaviour. Never delete pre-existing custom overrides.
Restore backup supports main.pak and gameoptions.xml. Steam file verification
may restore stock binaries and archives, but does not necessarily remove loose
files. Keep your backups. If Windows denies write access, choose a writable game
installation or run the tool with the necessary permissions.

OTHER FEATURES
Camera and advanced table changes retain the archive editing workflow; graphics
settings edit the chosen profile. Existing tactical saves can be converted to the
supported cinematic or stock camera using Save converter, with backup and known
record validation. Controls alone do not repack the archives or touch saves.
Presets can export/import staged settings, including native controls.

COMPATIBILITY AND LIMITATIONS
Native patches are limited to the exact supported original DLL and its four known
states (Arrows/WASD, edge scrolling on/off). Unknown or partially patched DLLs are
refused. No support is claimed for bin2 or other executable builds. Localisation
synchronisation was developed against English resources; other languages are not
verified.
Automatic game detection and profile discovery on Windows require further testing. Python is required; this
is not a standalone compiled executable.

TESTING
The native WASD and edge scrolling patches were individually verified in-game.
The v0.7 integration was tested with real original game.dll and archives in a
simulated installation with spaces and a custom Steam library: all four binary
states, migration, exact restoration, unknown DLL rejection, GUI apply/discard,
combined contextual preset, and archive integrity. Windows in-game testing of
v0.7 itself remains pending.