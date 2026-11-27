"""Syrian Warfare Configurator v0.7. Standard-library Python 3.10+.
Archive writes preserve unchanged local ZIP records, and encrypt replacements with ZipCrypto.
"""
import CameraWASD as NativeCamera
import binascii
import copy
import json
import math
import os
from pathlib import Path
import re
import shutil
import struct
import tempfile
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from xml.dom import minidom
from xml.sax.saxutils import escape
import zipfile
import zlib

Password = b'm,nw0rdk1s;ldscj'
Spreadsheet = 'urn:schemas-microsoft-com:office:spreadsheet'
CameraFile = 'scripts/species/cameras.xml'
KeysFile = 'scripts/species/hotkeys.xml'
Tables = {'Difficulty': 'scripts/difficulty_modes.xml', 'Experience': 'scripts/species/exp_levels.xml',
          'Deployment': 'scripts/species/spawns.xml', 'Infantry': 'scripts/species/humans.xml',
          'Squads': 'scripts/species/squads.xml', 'Weapons': 'scripts/species/guns.xml',
          'Ammunition': 'scripts/species/ammunition.xml', 'Tracked vehicles': 'scripts/species/tanks.xml',
          'Wheeled vehicles': 'scripts/species/cars.xml', 'Vehicle components': 'scripts/species/modules.xml'}
CameraInfo = {
    'min_zoom': ('Closest zoom', 1, 5000), 'max_zoom': ('Farthest zoom', 1, 5000),
    'min_roll': ('Lowest tilt (degrees)', 0, 89), 'max_roll': ('Highest tilt (degrees)', 0, 89),
    'min_dist_roll': ('Minimum distance roll (engine parameter)', 0, 5000),
    'fov': ('Field of view (degrees)', 10, 150), 'cam_near_clip_plane': ('Near clipping plane', .01, 100)}
Cinematic = dict(zip(CameraInfo, ['10', '600', '1', '89', '1', '60', '0.1']))
GraphicInfo = {
    'render.bloom': ('Bloom', 'bool'), 'render.hdr': ('HDR rendering', 'bool'),
    'render.shadows': ('Shadows', 'bool'), 'render.softShadows': ('Soft shadows', 'bool'),
    'render.particleShadows': ('Particle shadows', 'bool'), 'render.softParticles': ('Soft particles', 'bool'),
    'render.grass': ('Grass', 'bool'), 'render.grassDistance': ('Grass distance', 'number'),
    'render.shadowMapSize': ('Shadow map resolution', 'number'), 'render.multisamplingQuality': ('Multisampling quality (engine index)', 'number'),
    'render.skipMipsCount': ('Skipped texture mip levels', 'number'), 'render.forcedLowLOD': ('Force low detail', 'bool'),
    'render.rangeFog': ('Distance fog', 'bool'), 'render.vsync': ('VSync', 'bool'),
    'render.physicFragmentsPercentage': ('Physics fragments (%)', 'number'),
    'game.mouseMoveSpeed': ('Software cursor speed', 'number'), 'game.scrollSpeed': ('Camera movement speed', 'number')}
KeyNames = {'Button_attack':'Force attack','Button_stop':'Stop','Button_move':'Move until contact','Button_landing':'Land',
    'Button_cover':'Cover','Button_unload':'Unload / contextual','Button_behavior':'Engagement behaviour',
    'Button_pack':'Pack / contextual','Button_unpack':'Unpack / contextual','Button_unload_crew':'Disembark crew',
    'Button_attack_with_move':'Fire on the move','Button_self_repairing':'Self repair','Button_fight':'Assault',
    'Button_flare':'Smoke / flare','Button_close_hatches':'Close hatches','Button_open_hatches':'Open hatches',
    'Button_rotate':'Rotate','Button_mine':'Mine menu','Button_airstrike':'Air support menu','Button_formation':'Formation menu'}

LocaleFile = 'locale/strres.xml'
KeyMap = dict(zip(
    'Button_attack Button_stop Button_move Button_landing Button_cover Button_unload Button_behavior Button_pack Button_unpack Button_unload_crew Button_attack_with_move Button_self_repairing Button_fight Button_flare Button_close_hatches Button_open_hatches Button_rotate Button_mine Button_airstrike Button_formation infantry_mine tank_mine tnt rocket_strike bomb_strike missile_strike line line_extended mixed mixed_extended'.split(),
    'order_attack order_stop order_move order_landing order_cover order_unload order_behavior order_pack order_unpack order_unload_crew order_moving_fire order_self_repairing order_assault order_smoke order_close_hatch order_open_hatch order_rotate order_mine order_airstrike order_formation order_ap_mine order_at_mine order_c4 order_airstrike_nurs order_airstrike_bomb order_airstrike_atgm order_formation_line order_formation_wide_line order_formation_scatter order_formation_wide_scatter'.split()))
StockKeys = dict(zip('Button_attack Button_stop Button_move Button_landing Button_cover Button_unload Button_behavior Button_pack Button_unpack Button_unload_crew Button_attack_with_move Button_self_repairing Button_fight Button_flare Button_close_hatches Button_open_hatches Button_rotate Button_mine infantry_mine tank_mine tnt Mine_quit Button_airstrike rocket_strike bomb_strike missile_strike Airstrike_quit Button_formation line line_extended mixed mixed_extended Formation_quit'.split(), 'w r e a c z s a a v d c q x f f q z q w e z z q w e z f q w a s f'.split()))
KeyNames.update({'Mine_quit':'Close mine menu','Airstrike_quit':'Close air support menu','Formation_quit':'Close formation menu','Button_attach_trailer':'Attach trailer','Button_detach_trailer':'Detach trailer'})
KeyGroups = {Name: Group for Group, Names in {
    'Mine menu':'infantry_mine tank_mine tnt Mine_quit', 'Air support menu':'rocket_strike bomb_strike missile_strike Airstrike_quit',
    'Formation menu':'line line_extended mixed mixed_extended Formation_quit'}.items() for Name in Names.split()}

def KeyContext(Name): return KeyGroups.get(Name,'Main commands')

def KeyConflicts(Bindings):
    # Existing shared main-command defaults are intentional; other main overlaps are warnings, not proven conflicts.
    Result={}
    for Name, Key in Bindings.items():
        if not Key: continue
        Others=[N for N,K in Bindings.items() if N!=Name and K==Key and KeyContext(N)==KeyContext(Name)]
        if not Others: continue
        if KeyContext(Name)!='Main commands': Result[Name]='Conflict: same submenu'
        elif all(StockKeys.get(N)==StockKeys.get(Name) for N in Others): Result[Name]='Shared stock context'
        else: Result[Name]='Review: possible overlap'
    return Result

def SyncTooltips(Keys, Locale, Changes):
    Lookup={N:(I,F) for I,N,F in Locale.Rows}; Updates={}
    for I,N,F in Keys.Rows:
        if (I,'key') not in Changes or N not in KeyMap: continue
        Key=Changes[I,'key']; Loc=KeyMap[N]
        if Loc not in Lookup: raise ValueError('Missing localisation: '+Loc)
        R,Fields=Lookup[Loc]; Old=Fields['content'][0]
        Label=re.sub(r'\s*\([^()]*\)\s*$','',Old)
        Updates[R,'content']=Label+(' ('+Key.upper()+')' if Key else '')
    return Locale.Render(Updates)

# ZIP crypto is the legacy scheme used by the supplied game archive, not modern encryption.
CrcTable = tuple(zipfile._gen_crc(i) for i in range(256))
def EncryptZipCrypto(Data, Secret):
    K0, K1, K2 = 305419896, 591751049, 878082192
    def Update(Byte):
        nonlocal K0, K1, K2
        K0 = (K0 >> 8) ^ CrcTable[(K0 ^ Byte) & 255]
        K1 = ((K1 + (K0 & 255)) * 134775813 + 1) & 0xffffffff
        K2 = (K2 >> 8) ^ CrcTable[(K2 ^ (K1 >> 24)) & 255]
    for Byte in Secret: Update(Byte)
    Out = bytearray()
    for Byte in Data:
        T = K2 | 2
        Out.append(Byte ^ (((T * (T ^ 1)) >> 8) & 255))
        Update(Byte)
    return bytes(Out)

def Repack(Source, Destination, Changes):
    """Copy original local records verbatim except changed files; regenerate central directory."""
    with zipfile.ZipFile(Source) as Original, open(Source, 'rb') as Raw, zipfile.ZipFile(Destination, 'w', allowZip64=False) as Result:
        Entries = sorted(Original.infolist(), key=lambda Item: Item.header_offset)
        if len({Item.filename for Item in Entries}) != len(Entries): raise ValueError('Duplicate archive names are unsupported.')
        if not set(Changes).issubset(Original.namelist()): raise ValueError('Unknown archive member.')
        if not Entries: raise ValueError('Empty archive.')
        Raw.seek(0); Result.fp.write(Raw.read(Entries[0].header_offset))
        Result.comment = Original.comment
        NewEntries = {}
        for Index, Old in enumerate(Entries):
            New = copy.copy(Old); New.header_offset = Result.fp.tell()
            if Old.filename not in Changes:
                End = Entries[Index+1].header_offset if Index+1 < len(Entries) else Original.start_dir
                Raw.seek(Old.header_offset); Result.fp.write(Raw.read(End-Old.header_offset))
            else:
                Data = Changes[Old.filename]
                New.CRC = binascii.crc32(Data) & 0xffffffff; New.file_size = len(Data)
                if Old.compress_type == zipfile.ZIP_DEFLATED:
                    Compressor = zlib.compressobj(6, zlib.DEFLATED, -15)
                    Packed = Compressor.compress(Data) + Compressor.flush()
                elif Old.compress_type == zipfile.ZIP_STORED: Packed = Data
                else: raise ValueError('Unsupported compression method for ' + Old.filename)
                New.flag_bits &= ~8  # no data descriptor; CRC known up front
                if New.flag_bits & 1:
                    Packed = EncryptZipCrypto(os.urandom(11) + bytes([New.CRC >> 24]) + Packed, Password)
                New.compress_size = len(Packed)
                Result.fp.write(New.FileHeader(False)); Result.fp.write(Packed)
            NewEntries[Old.filename] = New
        Result.filelist = [NewEntries[Old.filename] for Old in Original.infolist()]
        Result.NameToInfo = NewEntries
        Result.start_dir = Result.fp.tell(); Result._didModify = True
    # Check the directory plus actual bytes of every replacement before installation.
    with zipfile.ZipFile(Source) as Original, zipfile.ZipFile(Destination) as Check:
        if Original.namelist() != Check.namelist(): raise ValueError('Archive member list changed.')
        for Old, New in zip(Original.infolist(), Check.infolist()):
            if Old.filename in Changes:
                if Check.read(New, pwd=Password) != Changes[Old.filename] or (Old.flag_bits & 1) != (New.flag_bits & 1):
                    raise ValueError('Replacement verification failed: ' + Old.filename)
            elif (Old.CRC, Old.file_size, Old.compress_size, Old.flag_bits) != (New.CRC, New.file_size, New.compress_size, New.flag_bits):
                raise ValueError('Unchanged entry metadata differs: ' + Old.filename)

def Children(Node, Name):
    return [Child for Child in Node.childNodes if Child.nodeType == Child.ELEMENT_NODE and Child.localName == Name]
def NodeText(Node):
    return ''.join(Child.data for Child in Node.childNodes if Child.nodeType in (Child.TEXT_NODE, Child.CDATA_SECTION_NODE))

class Sheet:
    """Read SpreadsheetML, respecting sparse ss:Index columns. Edit only existing Data text."""
    def __init__(self, Raw):
        self.Raw = Raw
        self.Text = Raw.decode('utf-8-sig')
        self.Bom = Raw.startswith(b'\xef\xbb\xbf')
        self.Doc = minidom.parseString(Raw)
        self.Rows = []
        # Map DOM Data nodes to original text spans in document order. This preserves all non-edited XML bytes.
        Nodes = list(self.Doc.getElementsByTagNameNS(Spreadsheet, 'Data'))
        Matches = list(re.finditer(r'<(?:ss:)?Data\b[^>]*>(.*?)</(?:ss:)?Data\s*>', self.Text, re.S))
        if len(Nodes) != len(Matches): raise ValueError('Unsupported Data element layout.')
        Spans = {id(Node): Match.span(1) for Node, Match in zip(Nodes, Matches)}
        for TableIndex, Table in enumerate(self.Doc.getElementsByTagNameNS(Spreadsheet, 'Table')):
            Headers = None
            for RowIndex, Row in enumerate(Children(Table,'Row')):
                Col = 0; Cells = {}
                for Cell in Children(Row,'Cell'):
                    Col = int(Cell.getAttributeNS(Spreadsheet,'Index') or Col+1)
                    Data = Children(Cell,'Data')
                    if Data: Cells[Col] = Data[0]
                if Headers is None:
                    Headers = {Col: NodeText(Node).strip() for Col,Node in Cells.items() if NodeText(Node).strip()}
                    continue
                if Headers.get(1) != 'sysname' or 1 not in Cells: continue
                Name = NodeText(Cells[1]); Fields = {}
                if not Name or Name.startswith('#'): continue
                for Col,Node in Cells.items():
                    Field = Headers.get(Col)
                    if Col == 1 or not Field: continue
                    Fields[Field] = (NodeText(Node), Node.getAttributeNS(Spreadsheet,'Type'), Spans[id(Node)])
                self.Rows.append((f'{TableIndex}:{RowIndex}', Name, Fields))
    def Get(self, Row, Field):
        return next(Fields[Field] for Id,Name,Fields in self.Rows if Id==Row)
    def Render(self, Changes):
        Patches = []
        for (Row, Field), Value in Changes.items():
            Old, Kind, (Start,End) = self.Get(Row,Field)
            if Value == Old: continue
            if Kind == 'Number':
                if not math.isfinite(float(Value)): raise ValueError('Expected finite number: '+Field)
            elif Kind == 'Boolean' and Value not in ('0','1'): raise ValueError('Expected 0 or 1: '+Field)
            Patches.append((Start,End,escape(Value)))
        Text = self.Text
        for Start,End,Value in sorted(Patches,reverse=True): Text=Text[:Start]+Value+Text[End:]
        Raw = Text.encode('utf-8-sig' if self.Bom else 'utf-8')
        minidom.parseString(Raw)
        return Raw

def Backup(PathToFile):
    Folder = PathToFile.parent / 'SWConfiguratorBackups'; Folder.mkdir(exist_ok=True)
    Stamp = time.strftime('%Y%m%d-%H%M%S') + '-' + str(time.time_ns()%1000000000)
    Target = Folder / (PathToFile.name + '.' + Stamp + '.bak')
    shutil.copy2(PathToFile,Target)
    return Target

def TempPath(Target):
    Handle, Name = tempfile.mkstemp(prefix='.swconfig-',suffix='.tmp',dir=Target.parent); os.close(Handle)
    return Path(Name)

def GameRunning():
    if os.name!='nt': return False
    import subprocess
    Result=subprocess.run(['tasklist','/FI','IMAGENAME eq SyrianWarfare.exe','/FO','CSV','/NH'],capture_output=True,text=True,errors='replace',creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if Result.returncode: raise OSError('Could not check whether the game is running. Close the game and retry.')
    return 'syrianwarfare.exe' in Result.stdout.lower()

def FindGames():
    """Discover Steam installations and libraries; never scan entire drives."""
    SteamRoots=[]
    if os.name=='nt':
        import winreg
        for Hive, Key in ((winreg.HKEY_CURRENT_USER,r'Software\Valve\Steam'),(winreg.HKEY_LOCAL_MACHINE,r'SOFTWARE\WOW6432Node\Valve\Steam'),(winreg.HKEY_LOCAL_MACHINE,r'SOFTWARE\Valve\Steam')):
            try:
                with winreg.OpenKey(Hive,Key) as Handle:
                    for Name in ('SteamPath','InstallPath'):
                        try: SteamRoots.append(Path(winreg.QueryValueEx(Handle,Name)[0]))
                        except OSError: pass
            except OSError: pass
    for Name in ('ProgramFiles(x86)','ProgramFiles'):
        if os.environ.get(Name): SteamRoots.append(Path(os.environ[Name])/'Steam')
    SteamRoots.extend([Path.home()/'.steam'/'steam',Path.home()/'.local'/'share'/'Steam'])
    Libraries=list(SteamRoots)
    for Root in SteamRoots:
        try:
            Raw=(Root/'steamapps'/'libraryfolders.vdf').read_text(encoding='utf-8-sig')
            for Match in re.finditer(r'"(?:path|[0-9]+)"\s+"([^"\r\n]+)"',Raw,re.I):
                Value=Match.group(1).replace('\\\\','\\')
                if Path(Value).is_absolute(): Libraries.append(Path(Value))
        except (OSError,UnicodeError): pass
    Candidates=[Path(__file__).resolve().parent,Path.cwd()]
    Candidates+=list(Path(__file__).resolve().parents)
    Candidates += [Root/'steamapps'/'common'/'Syrian Warfare' for Root in Libraries]
    Found={}
    for Root in Candidates:
        try:
            if (Root/'main.pak').is_file() and (Root/'lang.pak').is_file() and (Root/'bin'/'SyrianWarfare.exe').is_file():
                Pak=(Root/'main.pak').resolve(); Found[os.path.normcase(str(Pak))]=Pak
        except OSError: pass
    return sorted(Found.values(),key=str)

def FindProfiles():
    """Find profile XML files without choosing between multiple profiles."""
    Roots = [Path.home() / 'Documents']
    if os.name == 'nt':
        try:
            import ctypes
            Buffer = ctypes.create_unicode_buffer(32768)
            if ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, Buffer) == 0:
                Roots.insert(0, Path(Buffer.value))
        except (OSError, AttributeError):
            pass
    for Name in ('OneDrive', 'OneDriveConsumer', 'OneDriveCommercial'):
        if os.environ.get(Name): Roots.append(Path(os.environ[Name]) / 'Documents')
    Found = {}
    for Root in Roots:
        try:
            for File in (Root / 'SyrianWarfare' / 'profiles').glob('*/gameoptions.xml'):
                if File.is_file(): Found[os.path.normcase(str(File.resolve()))] = File.resolve()
        except OSError:
            continue
    return sorted(Found.values(), key=lambda File: str(File).lower())

def PreferencesPath():
    Root = Path(os.environ.get('LOCALAPPDATA') or Path.home() / '.config')
    return Root / 'SyrianWarfareConfigurator' / 'preferences.json'

def ReadPreferences():
    try:
        Data = json.loads(PreferencesPath().read_text(encoding='utf-8'))
        return Data if isinstance(Data, dict) else {}
    except (OSError, ValueError):
        return {}

# Known camera record anchors from the supplied tactical saves.
SavePrefixes = tuple(bytes.fromhex(X) for X in (
    '00000000000000000000404400004044000000000000704200007042000031440000314401',
    '000000000000000000000044000000440000000000003442000034420080e9430080e94301',
    '000000000000000000000044000000440000000000002042000020420000ec430000ec4301'))
SaveSuffix = bytes.fromhex('e4cb16c000009643')
SaveStock = (210.,370.,39.,89.,60.)
SaveCinematic = (10.,600.,1.,89.,1.)

def CameraSaveRecords(Data):
    Hits=[]
    for Prefix in SavePrefixes:
        Pos=0
        while True:
            Index=Data.find(Prefix,Pos)
            if Index<0: break
            Pos=Index+len(Prefix)
            if Data[Pos+26:Pos+34]!=SaveSuffix: continue
            Values=struct.unpack_from('<6f',Data,Pos)
            if Values[:5] not in (SaveStock,SaveCinematic):
                raise ValueError('Unknown camera values; refusing to patch an unverified record.')
            if Data[Pos+20:Pos+26] not in (bytes.fromhex('0000f1402e3f'),bytes.fromhex('00009a99193f')): continue
            Hits.append((Pos,Values[:5],Data[Pos+20:Pos+26]))
    if len(Hits)!=2 or Hits[0][1:]!=Hits[1][1:]:
        raise ValueError('Expected two matching camera records. No changes made.')
    return sorted(Hits)

def ConvertCameraSave(Data, CinematicMode=True):
    Hits=CameraSaveRecords(Data)
    Values=SaveCinematic if CinematicMode else SaveStock
    # Preserve the exact additional byte changes used in the validated patch.
    # Its engine meaning is not established; only revert a known cinematic record.
    Result=bytearray(Data)
    for Pos,Old,Extra in Hits:
        Result[Pos:Pos+20]=struct.pack('<5f',*Values)
        if CinematicMode: Result[Pos+20:Pos+26]=bytes.fromhex('00009a99193f')
        elif Old==SaveCinematic: Result[Pos+20:Pos+26]=bytes.fromhex('0000f1402e3f')
    Output=bytes(Result)
    CameraSaveRecords(Output)
    return Output

class Configurator(tk.Tk):
    def __init__(self):
        super().__init__(); self.title('Syrian Warfare Configurator | 0.7'); self.geometry('1060x800'); self.minsize(860,620)
        self.EdgeEnabled=tk.BooleanVar(value=True); self.EdgeOriginal=True; self.NativeMode=tk.StringVar(value="Unavailable"); self.NativeOriginalMode="Unavailable"; self.NativeSnapshot=None; self.NativeStock=None; self.NativeTarget=None
        self.SyncKeys=False; self.KeyTargets={}; self.KeySnapshots={}; self.Locale=None; self.Pak = None; self.Options = None; self.Sheets = {}; self.Pending = {}; self.Graphics = {}; self.GraphOriginal = {}; self.GraphVars = {}; self.CameraVars = {}; self.CameraId = None
        self.Preferences = ReadPreferences()
        self.Style = ttk.Style(self); self.Style.theme_use('clam')
        self.DarkMode=tk.BooleanVar(value=self.Preferences.get("dark_mode", True) is not False); self.ApplyTheme(); self.Style.configure('.',font=('Segoe UI',10)); self.Style.configure('TButton',padding=6); self.Style.configure('Treeview',rowheight=26); self.Style.configure('Title.TLabel',font=('Segoe UI',18,'bold'))
        Header = ttk.Frame(self,padding=(16,12)); Header.pack(fill='x')
        ttk.Label(Header,text='SYRIAN WARFARE  /  CONFIGURATOR',style='Title.TLabel').pack(anchor='w')
        ttk.Label(Header,text='Local configuration editor • changes are staged until Apply • close the game before writing').pack(anchor='w',pady=(3,10))
        Bar=ttk.Frame(Header); Bar.pack(fill='x'); ttk.Button(Bar,text='Browse game…',command=self.BrowseGame).pack(side='left'); ttk.Button(Bar,text='Open gameoptions.xml',command=self.OpenOptions).pack(side='left',padx=5)
        ttk.Button(Bar,text='Detect game',command=lambda:self.DetectGame(True)).pack(side='left',padx=5)
        ttk.Checkbutton(Bar,text='Dark mode',variable=self.DarkMode,command=self.ChangeTheme).pack(side='right')
        ttk.Button(Bar,text='Detect profile',command=lambda:self.DetectOptions(True)).pack(side='left',padx=5)
        self.PathLabel=ttk.Label(Header,text='No archive selected'); self.PathLabel.pack(anchor='w',pady=(6,0))
        self.OptionsLabel=ttk.Label(Header,text='No profile selected',wraplength=990); self.OptionsLabel.pack(anchor='w',pady=(3,0))
        self.Notebook=ttk.Notebook(self); self.Notebook.pack(fill='both',expand=True,padx=16,pady=(0,8))
        self.CameraTab=ttk.Frame(self.Notebook,padding=16); self.KeysTab=ttk.Frame(self.Notebook,padding=12); self.GraphicsTab=ttk.Frame(self.Notebook,padding=12); self.AdvTab=ttk.Frame(self.Notebook,padding=12)
        for Tab,Name in [(self.CameraTab,'Camera'),(self.KeysTab,'Controls'),(self.GraphicsTab,'Graphics & cursor'),(self.AdvTab,'Advanced tables')]: self.Notebook.add(Tab,text=Name)
        self.BuildCamera(); self.BuildKeys(); self.BuildGraphics(); self.BuildAdvanced(); self.BuildDiagnostics(); self.BuildSaveConverter()
        Foot=ttk.Frame(self,padding=(16,6)); Foot.pack(fill='x')
        for Label,Command in [('Export preset',self.Export),('Import preset',self.Import),('Discard edits',self.Discard),('Restore backup',self.Restore)]: ttk.Button(Foot,text=Label,command=Command).pack(side='left',padx=(0,5))
        ttk.Button(Foot,text='Apply changes',command=self.Apply).pack(side='right')
        self.Status=tk.StringVar(value='Open your game files to begin.'); ttk.Label(self,textvariable=self.Status,padding=(16,8)).pack(fill='x')
        self.after(100, self.LoadRememberedFiles)
    def SavePreferences(self):
        try:
            Target = PreferencesPath()
            Target.parent.mkdir(parents=True, exist_ok=True)
            Temp = Target.with_suffix('.tmp')
            Temp.write_text(json.dumps(self.Preferences, indent=2), encoding='utf-8')
            os.replace(Temp, Target)
        except OSError as Error:
            messagebox.showwarning('Preferences not saved', str(Error))
    def ChangeTheme(self):
        self.ApplyTheme()
        self.Preferences['dark_mode'] = self.DarkMode.get()
        self.SavePreferences()
    def RememberFile(self, Key, File):
        # Backup files may be opened for inspection, but must not become startup targets.
        Expected = 'main.pak' if Key == 'pak' else 'gameoptions.xml'
        if File.name.lower() != Expected: return
        Value = str(File.resolve())
        if self.Preferences.get(Key) != Value:
            self.Preferences[Key] = Value
            self.SavePreferences()
    def LoadRememberedFiles(self):
        Errors = []
        for Key, Loader in [('pak', self.LoadPak), ('options', self.LoadOptions)]:
            Value = self.Preferences.get(Key)
            if not isinstance(Value, str) or not Value: continue
            try:
                Loader(Path(Value))
            except Exception as Error:
                Errors.append(f'{Key}: {Error}')
        if not self.Pak: self.DetectGame()
        if not self.Options: self.DetectOptions()
        if Errors:
            self.Status.set('Some saved paths could not be loaded. Select the files again.')
            messagebox.showwarning('Saved paths unavailable', '\n'.join(Errors))
        elif self.Pak and self.Options:
            self.Status.set('Remembered archive and profile loaded. No changes staged.')
    def ApplyTheme(self):
        Dark = self.DarkMode.get()
        Bg, Panel, Field, Text, Muted, Border, Accent = ('#202327','#292d32','#171a1e','#e7e9ec','#929aa4','#414851','#365c7d') if Dark else ('#efefed','#e2e4e5','#ffffff','#202327','#656b70','#b9bec3','#c4ddf3')
        self.configure(background=Bg)
        self.Style.configure('.', background=Bg, foreground=Text, fieldbackground=Field, bordercolor=Border, lightcolor=Border, darkcolor=Border, troughcolor=Panel, selectbackground=Accent, selectforeground=Text, insertcolor=Text, arrowcolor=Text)
        self.Style.configure('TButton',background=Panel,foreground=Text)
        self.Style.map('TButton',background=[('pressed',Accent),('active',Border)],foreground=[('disabled',Muted)])
        self.Style.configure('TNotebook',background=Bg,bordercolor=Border)
        self.Style.configure('TNotebook.Tab',background=Panel,foreground=Muted,padding=(12,6))
        self.Style.map('TNotebook.Tab',background=[('selected',Field),('active',Border)],foreground=[('selected',Text)])
        for Name in ('TEntry','TSpinbox','TCombobox'):
            self.Style.configure(Name,fieldbackground=Field,foreground=Text,insertcolor=Text,background=Panel)
            self.Style.map(Name,fieldbackground=[('readonly',Field),('disabled',Panel)],foreground=[('disabled',Muted),('readonly',Text)])
        self.Style.configure('Treeview',background=Field,fieldbackground=Field,foreground=Text)
        self.Style.map('Treeview',background=[('selected',Accent)],foreground=[('selected',Text)])
        self.Style.configure('Treeview.Heading',background=Panel,foreground=Text)
        self.Style.map('Treeview.Heading',background=[('active',Border)])
        self.Style.configure('TCheckbutton',background=Bg,foreground=Text,indicatorbackground=Field,indicatorforeground=Text)
        self.Style.map('TCheckbutton',background=[('active',Bg)],indicatorbackground=[('selected',Accent)])
        self.Style.configure('TScrollbar',background=Panel,troughcolor=Field,arrowcolor=Text)
        self.Style.map('TScrollbar',background=[('active',Border)])
        self.option_add('*TCombobox*Listbox.background',Field)
        self.option_add('*TCombobox*Listbox.foreground',Text)
        self.option_add('*TCombobox*Listbox.selectBackground',Accent)
        self.option_add('*TCombobox*Listbox.selectForeground',Text)

    def DetectOptions(self, Interactive=False):
        if self.Options and not Interactive: return
        if self.Options and any(V.get()!=self.GraphOriginal.get(K,'') for K,V in self.GraphVars.items()):
            if not messagebox.askyesno('Detect profile','Discard staged profile changes?'): return
        Found=FindProfiles()
        if not Found:
            if Interactive: self.OpenOptions()
            else: self.OptionsLabel.configure(text='Profile not detected. Use Open gameoptions.xml to select it manually.')
            return
        if len(Found)==1: Selected=Found[0]
        else:
            if not Interactive:
                self.OptionsLabel.configure(text=f'{len(Found)} profiles detected. Click Detect profile to choose one.')
                return
            Choice=filedialog.askopenfilename(title='Multiple profiles found: choose your gameoptions.xml',initialdir=str(Found[0].parent.parent),filetypes=[('Profile XML','gameoptions.xml'),('XML settings','*.xml')])
            if not Choice: return
            Selected=Path(Choice)
        try: self.LoadOptions(Selected)
        except Exception as E:
            self.OptionsLabel.configure(text='Profile detected but could not be loaded.')
            if Interactive: messagebox.showerror('Cannot load profile',str(E))

    def BuildCamera(self):
        ttk.Label(self.CameraTab,text='Tactical camera',style='Title.TLabel').grid(row=0,column=0,columnspan=3,sticky='w')
        ttk.Label(self.CameraTab,text='Camera settings apply to new tactical sessions. To update existing tactical saves, use the Save converter tab.',wraplength=850).grid(row=1,column=0,columnspan=3,sticky='w',pady=(4,12))
        ttk.Label(self.CameraTab,text='Parameter').grid(row=2,column=0,sticky='w'); ttk.Label(self.CameraTab,text='Current / edited').grid(row=2,column=1); ttk.Label(self.CameraTab,text='Stock (supported build)').grid(row=2,column=2,padx=15)
        Stock=['210','370','39','89','60','60','1']
        for I,(Field,(Label,Min,Max)) in enumerate(CameraInfo.items(),3):
            ttk.Label(self.CameraTab,text=Label).grid(row=I,column=0,sticky='w',pady=5)
            Var=tk.StringVar(); self.CameraVars[Field]=Var; ttk.Spinbox(self.CameraTab,from_=Min,to=Max,textvariable=Var,width=18,increment=.1 if Field=='cam_near_clip_plane' else 1).grid(row=I,column=1,padx=15,sticky='ew')
            ttk.Label(self.CameraTab,text=Stock[I-3]).grid(row=I,column=2)
        Buttons=ttk.Frame(self.CameraTab); Buttons.grid(row=11,column=0,columnspan=3,sticky='w',pady=15)
        ttk.Button(Buttons,text='Cinematic preset',command=lambda:self.CameraPreset(Cinematic)).pack(side='left')
        ttk.Button(Buttons,text='Stock preset',command=lambda:self.CameraPreset(dict(zip(CameraInfo,Stock)))).pack(side='left',padx=6)
        ttk.Button(Buttons,text='Reset to loaded archive',command=self.RefreshCamera).pack(side='left')
        ttk.Label(self.CameraTab,text='Cinematic preset: close zoom, near-horizontal angle and expanded zoom-out. Experimental; terrain clipping or visibility artefacts are possible.',wraplength=850).grid(row=12,column=0,columnspan=3,sticky='w')
    def BuildKeys(self):
        ttk.Label(self.KeysTab,text='Native contextual controls',style='Title.TLabel').pack(anchor='w')
        ttk.Label(self.KeysTab,text='Double-click a command to rebind. Loose XML overrides update functional keys and matching English tooltips. Camera movement can now use native WASD. Main-command overlaps are advisory.',wraplength=950).pack(anchor='w',pady=6)
        Native=ttk.LabelFrame(self.KeysTab,text='Native camera movement',padding=8); Native.pack(fill='x',pady=(0,6))
        self.NativeLabel=ttk.Label(Native,text='Open installed main.pak to detect game.dll'); self.NativeLabel.pack(anchor='w')
        Choices=ttk.Frame(Native); Choices.pack(fill='x')
        self.NativeChoices=[]
        for Mode in ('Arrows','WASD'):
            Button=ttk.Radiobutton(Choices,text=Mode,value=Mode,variable=self.NativeMode,command=self.RefreshKeys,state='disabled'); Button.pack(side='left',padx=(0,12)); self.NativeChoices.append(Button)
        self.NativePresetButton=ttk.Button(Choices,text='WASD + free conflicting keys',command=self.NativePreset,state='disabled'); self.NativePresetButton.pack(side='left')
        self.EdgeCheck=ttk.Checkbutton(Native,text='Enable edge scrolling',variable=self.EdgeEnabled,state='disabled'); self.EdgeCheck.pack(anchor='w')
        ttk.Label(Native,text='Camera mode and edge scrolling are independent. Close AutoHotkey before using native WASD.').pack(anchor='w')
        Bar=ttk.Frame(self.KeysTab); Bar.pack(fill='x')
        ttk.Button(Bar,text='Restore stock bindings',command=self.KeyPreset).pack(side='left')
        ttk.Button(Bar,text='Synchronise tooltips',command=self.StageTooltipSync).pack(side='left',padx=6)
        ttk.Button(Bar,text='Export legacy AHK helper',command=self.ExportAHK).pack(side='left',padx=6)
        self.KeyTree=self.MakeTree(self.KeysTab,('Command','Context','Key','Stock','Conflict / status'),(300,135,55,55,200)); self.KeyTree.bind('<Double-1>',self.EditKey)
    def BuildGraphics(self):
        ttk.Label(self.GraphicsTab,text='Graphics & cursor',style='Title.TLabel').pack(anchor='w')
        ttk.Label(self.GraphicsTab,text='These settings live in your profile gameoptions.xml, not main.pak. Values beyond the menu range are experimental.',wraplength=950).pack(anchor='w',pady=5)
        Area=ttk.Frame(self.GraphicsTab); Area.pack(fill='both',expand=True)
        for I,(Key,(Label,Kind)) in enumerate(GraphicInfo.items()):
            Block=ttk.Frame(Area,padding=(0,4)); Block.grid(row=I%9,column=I//9,sticky='ew',padx=(0,25)); Area.columnconfigure(I//9,weight=1)
            Var=tk.StringVar(); self.GraphVars[Key]=Var
            ttk.Label(Block,text=Label).pack(side='left')
            if Kind=='bool': ttk.Checkbutton(Block,variable=Var,onvalue='1',offvalue='0').pack(side='right')
            else: ttk.Entry(Block,textvariable=Var,width=12).pack(side='right')
        ttk.Button(self.GraphicsTab,text='Experimental visual preset',command=self.VisualPreset).pack(anchor='w',pady=8)
        ttk.Label(self.GraphicsTab,text='Preset enables bloom, increases grass distance to 1000, shadow map to 4096 and multisampling index to 4. Engine support is not confirmed.',wraplength=950).pack(anchor='w')
    def BuildAdvanced(self):
        ttk.Label(self.AdvTab,text='Advanced archive tables',style='Title.TLabel').pack(anchor='w')
        ttk.Button(self.AdvTab,text='Open archive file…',command=self.OpenPak).pack(anchor='w',pady=(0,4))
        ttk.Label(self.AdvTab,text='Experimental gameplay editing. Raw engine values, including shared player/enemy definitions. No balance changes are applied automatically.',wraplength=950).pack(anchor='w',pady=6)
        Bar=ttk.Frame(self.AdvTab); Bar.pack(fill='x'); self.TableName=tk.StringVar(value='Difficulty'); Combo=ttk.Combobox(Bar,textvariable=self.TableName,values=list(Tables),state='readonly',width=22); Combo.pack(side='left'); Combo.bind('<<ComboboxSelected>>',lambda E:self.RefreshRows())
        self.Search=tk.StringVar(); ttk.Label(Bar,text='Filter rows:').pack(side='left',padx=8); ttk.Entry(Bar,textvariable=self.Search).pack(side='left',fill='x',expand=True); self.Search.trace_add('write',lambda *_:self.RefreshRows())
        Split=ttk.Panedwindow(self.AdvTab,orient='horizontal'); Split.pack(fill='both',expand=True,pady=8)
        Left=ttk.Frame(Split); Right=ttk.Frame(Split); Split.add(Left,weight=1); Split.add(Right,weight=3)
        self.RowTree=self.MakeTree(Left,('Record',),(250,)); self.RowTree.bind('<<TreeviewSelect>>',lambda E:self.RefreshFields())
        self.FieldTree=self.MakeTree(Right,('Field','Value','Loaded value'),(180,230,200)); self.FieldTree.bind('<Double-1>',self.EditField); self.FieldTree.bind('<<TreeviewSelect>>',self.DescribeField)
        ttk.Label(self.AdvTab,text='Select a record, then double-click a field to edit it. Blank or absent XML cells are not created. Numbers must remain numeric.').pack(anchor='w')
        self.FieldHelp=tk.StringVar(value='Select a field for its interpretation and verification status.')
        ttk.Label(self.AdvTab,textvariable=self.FieldHelp,wraplength=900).pack(anchor='w',pady=5)
    def DescribeField(self,Event=None):
        Sel=self.FieldTree.selection()
        if not Sel:return
        Field=Sel[0]
        Notes={'health':'Component or entity health; raw engine units, scale unverified.', 'vision_radius':'Observation radius; likely map distance, exact units unverified.', 'detection_radius_stay':'Detection radius while stationary; likely distance at which this unit is detected, not confirmed.', 'detection_radius_move':'Detection radius while moving; direction of detection unverified.', 'detection_radius_shoot':'Detection radius while firing; direction of detection unverified.', 'cost_of_dead':'Likely command-point penalty for a casualty; unverified.', 'command_points':'Command-point field; exact accounting context unverified.', 'ammunition':'Ammunition identifiers and quantities; preserve token syntax.', 'module_function':'Engine component-function tokens; changing these may break vehicle behaviour.', 'boxes':'Model component names; preserve existing identifiers.', 'link_to_gui':'Interface component identifier; not a balance setting.'}
        Note=Notes.get(Field,'Raw engine field. Meaning, units and runtime effects not verified.')
        if Field.endswith('_armor_layers'):Note='Directional armour material and thickness/value pairs; exact units and penetration model unverified.'
        self.FieldHelp.set(Field+': '+Note)
    def BuildDiagnostics(self):
        Tab=ttk.Frame(self.Notebook,padding=16); self.Notebook.add(Tab,text='Diagnostics')
        ttk.Label(Tab,text='Compatibility & investigation',style='Title.TLabel').pack(anchor='w')
        ttk.Label(Tab,text='Diagnostics are read-only. Native camera and edge scrolling require the supported game DLL. HUD toggle is not implemented.',wraplength=900).pack(anchor='w',pady=8)
        Bar=ttk.Frame(Tab);Bar.pack(fill='x')
        ttk.Button(Bar,text='Inspect save file',command=self.InspectSave).pack(side='left')
        ttk.Button(Bar,text='Inspect archive overrides',command=self.InspectOverrides).pack(side='left',padx=8)
        ttk.Button(Bar,text='Export diagnostic report',command=self.ExportDiagnostics).pack(side='left')
        self.DiagnosticText=tk.StringVar(value='Select an investigation. No save files are modified.')
        ttk.Label(Tab,textvariable=self.DiagnosticText,wraplength=900,justify='left').pack(anchor='w',pady=12)
    def BuildSaveConverter(self):
        Tab=ttk.Frame(self.Notebook,padding=16); self.Notebook.add(Tab,text='Save converter')
        ttk.Label(Tab,text='Existing campaign camera',style='Title.TLabel').pack(anchor='w')
        ttk.Label(Tab,text='Apply the tested cinematic camera to an existing tactical save without restarting the campaign. Close the game first. Only recognised camera records are changed; other gameplay settings are not converted.',wraplength=860).pack(anchor='w',pady=10)
        self.SaveMode=tk.StringVar(value='cinematic')
        ttk.Radiobutton(Tab,text='Cinematic preset (10–600 zoom, 1–89° tilt)',variable=self.SaveMode,value='cinematic').pack(anchor='w',pady=4)
        ttk.Radiobutton(Tab,text='Restore stock camera (210–370 zoom, 39–89° tilt)',variable=self.SaveMode,value='stock').pack(anchor='w',pady=4)
        ttk.Button(Tab,text='Select and convert tactical save…',command=self.ConvertSelectedSave).pack(anchor='w',pady=12)
        self.SaveResult=tk.StringVar(value='Original save is backed up before any replacement. Unsupported formats are refused.')
        ttk.Label(Tab,textvariable=self.SaveResult,wraplength=860,justify='left').pack(anchor='w',pady=8)
    def ConvertSelectedSave(self):
        File=filedialog.askopenfilename(initialdir=str(self.Options.parent/'saves' if self.Options else Path.home()),filetypes=[('Tactical saves','*.sav')])
        if not File:return
        P=Path(File); Temp=None
        try:
            Original=P.read_bytes(); Converted=ConvertCameraSave(Original,self.SaveMode.get()=='cinematic')
            if Converted==Original:self.SaveResult.set('Already using the selected camera. Nothing written.');return
            Count=sum(A!=B for A,B in zip(Original,Converted))
            if not messagebox.askyesno('Convert save',f'{P.name}\n{Count} bytes will change. A backup will be created. Is the game closed?'):return
            if GameRunning():raise ValueError("Close Syrian Warfare before converting a save.")
            Back=Backup(P); Temp=TempPath(P); Temp.write_bytes(Converted)
            if Temp.read_bytes()!=Converted or P.read_bytes()!=Original:raise ValueError('Verification failed or source changed during conversion.')
            os.replace(Temp,P)
            self.SaveResult.set(f'Converted {P.name}\nChanged {Count} bytes; size unchanged.\nBackup: {Back}')
        except Exception as E:messagebox.showerror('Save conversion refused',str(E))
        finally:
            if Temp is not None:Temp.unlink(missing_ok=True)
    def InspectSave(self):
        File=filedialog.askopenfilename(initialdir=str(self.Options.parent/'saves' if self.Options else Path.home()),title='Select a backed-up save file')
        if not File:return
        try:
            P=Path(File)
            with P.open('rb') as F: Head=F.read(1024*1024)
            Lines=[f'File: {P.name}',f'Size: {P.stat().st_size:,} bytes','Header (hex): '+Head[:32].hex(' ')]
            if zipfile.is_zipfile(P):
                with zipfile.ZipFile(P) as Z:
                    Names=Z.namelist(); Lines.append(f'ZIP container: {len(Names)} members');Lines.extend(Names[:20])
            else:Lines.append('Not recognised as a ZIP container; may use a proprietary or compressed format.')
            for Key in ('min_zoom','max_zoom','min_roll','hotkeys','cameras.xml'):
                Lines.append(f'{Key}: '+('found in first MiB' if Key.encode() in Head or Key.encode('utf-16le') in Head else 'not found in first MiB'))
            Lines.append('No save modifications attempted. Absence of strings does not rule out binary serialisation.')
            self.DiagnosticText.set('\n'.join(Lines))
        except Exception as E:messagebox.showerror('Inspection failed',str(E))
    def InspectOverrides(self):
        if not self.Pak:messagebox.showinfo('Open archive','Select main.pak first.');return
        Lines=['Sibling PAK files containing matching configuration paths (case-insensitive):']
        Targets={CameraFile.lower(),KeysFile.lower(),'scripts/ui/main.txt','scripts/ui/gamemenu.txt'}
        for P in sorted(self.Pak.parent.glob('*.pak')):
            try:
                with zipfile.ZipFile(P) as Z: Hits=[N for N in Z.namelist() if N.lower() in Targets]
                if Hits:Lines.append(P.name+': '+', '.join(Hits))
            except Exception as E:Lines.append(P.name+': unreadable ('+str(E)+')')
        Lines.append('Matching entries are candidates only; archive load order is unknown.')
        self.DiagnosticText.set('\n'.join(Lines))
    def ExportDiagnostics(self):
        File=filedialog.asksaveasfilename(defaultextension='.txt',initialfile='SWDiagnostics.txt')
        if File:Path(File).write_text(self.DiagnosticText.get(),encoding='utf-8')
    def MakeTree(self,Parent,Columns,Widths):
        Frame=ttk.Frame(Parent); Frame.pack(fill='both',expand=True,pady=5); Tree=ttk.Treeview(Frame,columns=Columns,show='headings',selectmode='browse'); Y=ttk.Scrollbar(Frame,orient='vertical',command=Tree.yview); X=ttk.Scrollbar(Frame,orient='horizontal',command=Tree.xview); Tree.configure(yscrollcommand=Y.set,xscrollcommand=X.set)
        Tree.grid(row=0,column=0,sticky='nsew'); Y.grid(row=0,column=1,sticky='ns'); X.grid(row=1,column=0,sticky='ew'); Frame.rowconfigure(0,weight=1); Frame.columnconfigure(0,weight=1)
        for C,W in zip(Columns,Widths): Tree.heading(C,text=C); Tree.column(C,width=W,minwidth=65,stretch=True)
        return Tree
    def DetectGame(self, Interactive=False):
        Found=FindGames()
        if len(Found)!=1:
            if Interactive: self.BrowseGame()
            elif not self.Pak: self.PathLabel.configure(text='Game not uniquely detected. Click Browse game… and select the installation folder.')
            return
        if self.Pak and not messagebox.askyesno('Detect game','Discard staged game edits and open the detected installation?'):return
        try: self.LoadPak(Found[0])
        except Exception as Error:
            self.Status.set('Game detected but could not be loaded.')
            if Interactive: messagebox.showerror('Cannot load game',str(Error))

    def BrowseGame(self):
        Folder=filedialog.askdirectory(title='Select the Syrian Warfare installation folder (contains main.pak)',initialdir=str(self.Pak.parent if self.Pak else Path.home()),mustexist=True)
        if not Folder:return
        Root=Path(Folder)
        if not all((Root/F).is_file() for F in ('main.pak','lang.pak','bin/SyrianWarfare.exe')):
            messagebox.showerror('Game not found','Select the folder containing main.pak, lang.pak and bin/SyrianWarfare.exe. In Steam: Library → Syrian Warfare → Manage → Browse local files.');return
        if self.Pak and not messagebox.askyesno('Change game','Discard staged game edits and open the selected installation?'):return
        try: self.LoadPak(Root/'main.pak'); self.DetectOptions()
        except Exception as Error: messagebox.showerror('Cannot open game',str(Error))

    def OpenPak(self):
        File=filedialog.askopenfilename(title='Select Syrian Warfare main.pak',initialdir=str(self.Pak.parent if self.Pak else Path(self.Preferences.get('pak') or Path.home()).parent if self.Preferences.get('pak') else Path.home()),filetypes=[('Game archive','*.pak *.bak'),('All files','*')]);
        if not File: return
        if self.Pak and not messagebox.askyesno('Open archive','Discard staged archive edits and open the selected file?'): return
        try:
            self.LoadPak(Path(File))
            self.DetectOptions()
        except Exception as E: messagebox.showerror('Cannot open archive',str(E))
    def LoadPak(self,PathToPak):
        Sheets={}; Failures=[]
        with zipfile.ZipFile(PathToPak) as Z:
            for File in [CameraFile,KeysFile,*Tables.values()]:
                try: Sheets[File]=Sheet(Z.read(File,pwd=Password))
                except Exception as E:
                    if File in (CameraFile,KeysFile): raise
                    Failures.append(File+': '+str(E))
        self.SyncKeys=False; self.KeyTargets={}; self.KeySnapshots={}; self.Locale=None
        if PathToPak.name.lower()=='main.pak' and (PathToPak.parent/'bin'/'SyrianWarfare.exe').is_file():
            Root=PathToPak.parent
            self.KeyTargets={KeysFile:Root/'basis'/KeysFile,LocaleFile:Root/'basis_loc'/LocaleFile}
            self.KeySnapshots={F:P.read_bytes() if P.exists() else None for F,P in self.KeyTargets.items()}
            if self.KeySnapshots[KeysFile] is not None: Sheets[KeysFile]=Sheet(self.KeySnapshots[KeysFile])
            try:
                if self.KeySnapshots[LocaleFile] is not None: Raw=self.KeySnapshots[LocaleFile]
                else:
                    with zipfile.ZipFile(Root/'lang.pak') as Z: Raw=Z.read(LocaleFile,pwd=Password)
                self.Locale=Sheet(Raw)
            except Exception as E: Failures.append('Tooltip localisation: '+str(E))
        self.Pak=PathToPak; self.PakStat=(PathToPak.stat().st_size,PathToPak.stat().st_mtime_ns); self.Sheets=Sheets; self.Pending={}; self.LoadNative()
        self.PathLabel.configure(text=str(PathToPak)); self.RefreshCamera(); self.RefreshKeys(); self.RefreshRows(); self.RememberFile('pak', PathToPak); self.Status.set(f'Loaded {len(Sheets)} editable tables. '+('Some tables unavailable: '+', '.join(Failures) if Failures else 'No archive changes staged.'))
    def OpenOptions(self):
        File=filedialog.askopenfilename(title='Select profile gameoptions.xml',initialdir=str(self.Options.parent if self.Options else Path.home()/'Documents'),filetypes=[('XML settings','*.xml *.bak'),('All files','*')]);
        if not File:return
        try: self.LoadOptions(Path(File))
        except Exception as E: messagebox.showerror('Cannot open options',str(E))
    def LoadOptions(self,PathToOptions):
        Raw=PathToOptions.read_bytes(); Doc=minidom.parseString(Raw)
        if Doc.documentElement.tagName!='GameOptions': raise ValueError('Not a GameOptions XML file.')
        Original={N.tagName:NodeText(N) for N in Doc.documentElement.childNodes if N.nodeType==N.ELEMENT_NODE and N.tagName in GraphicInfo}
        self.Options=PathToOptions; self.OptionsRaw=Raw; self.GraphOriginal=Original
        for K,V in self.GraphVars.items(): V.set(Original.get(K,''))
        self.OptionsLabel.configure(text='Profile: '+str(PathToOptions))
        self.Status.set('Loaded profile: '+str(PathToOptions))
        self.RememberFile('options', PathToOptions)
    def RefreshCamera(self):
        if CameraFile not in self.Sheets:return
        self.CameraId,_,Fields=next(Row for Row in self.Sheets[CameraFile].Rows if Row[1]=='tactical')
        for K,V in self.CameraVars.items(): V.set(Fields[K][0])
    def CameraPreset(self,Values):
        if not self.Pak: messagebox.showinfo('Open archive','Select main.pak first.'); return
        for K,V in Values.items():self.CameraVars[K].set(V)
    def Value(self,File,Row,Field): return self.Pending.get(File,{}).get((Row,Field),self.Sheets[File].Get(Row,Field)[0])
    def Stage(self,File,Row,Field,Value):
        Old=self.Sheets[File].Get(Row,Field)[0]
        if Value==Old:self.Pending.get(File,{}).pop((Row,Field),None)
        else:self.Pending.setdefault(File,{})[(Row,Field)]=Value
    def LoadNative(self):
        self.NativeTarget=None; self.NativeSnapshot=None; self.NativeStock=None
        self.NativeOriginalMode='Unavailable'; self.EdgeOriginal=True; Detail='Open installed main.pak to detect game.dll.'
        try:
            if self.Pak and self.Pak.name.lower()=='main.pak' and (self.Pak.parent/'bin'/'SyrianWarfare.exe').is_file():
                Target=self.Pak.parent/'bin'/'game.dll'; Current=Target.read_bytes()
                BackupFile=Target.with_name('game.dll.wasd-original.bak')
                Stock, Wasd, EdgeEnabled=NativeCamera.Detect(Current)
                if BackupFile.exists() and BackupFile.read_bytes()!=Stock:raise ValueError('Existing original backup does not match the supported DLL.')
                self.NativeTarget=Target; self.NativeSnapshot=Current; self.NativeStock=Stock
                self.NativeOriginalMode='WASD' if Wasd else 'Arrows'; self.EdgeOriginal=EdgeEnabled
                Detail='Installed: '+self.NativeOriginalMode+' | Edge scrolling: '+('On' if EdgeEnabled else 'Off')+' | Supported DLL (1.2.1.53)'
        except (OSError,ValueError) as Error: Detail='Native controls unavailable: '+str(Error)
        self.NativeMode.set(self.NativeOriginalMode); self.EdgeEnabled.set(self.EdgeOriginal if self.NativeTarget else True); self.NativeLabel.configure(text=Detail,wraplength=900)
        for Button in self.NativeChoices:Button.configure(state='normal' if self.NativeTarget else 'disabled')
        self.EdgeCheck.configure(state='normal' if self.NativeTarget else 'disabled')
        self.NativePresetButton.configure(state='normal' if self.NativeTarget and self.Locale is not None else 'disabled')
    def NativeConflicts(self,Bindings):
        Reserved={'w','a','s','d'} if self.NativeMode.get()=='WASD' else {'up','down','left','right'} if self.NativeMode.get()=='Arrows' else set()
        return {N for N,K in Bindings.items() if K.lower() in Reserved}
    def NativePreset(self):
        if not self.NativeTarget or not self.Locale:return
        Mapping={'w':'t','a':'g','s':'h','d':'b'}
        if not messagebox.askyesno('WASD preset','Stage native WASD and move current contextual W/A/S/D bindings to T/G/H/B? Other bindings are retained. Review any overlaps before Apply.'):return
        self.NativeMode.set('WASD')
        for Id,Name,Fields in self.Sheets[KeysFile].Rows:
            if 'key' in Fields:
                Key=self.Value(KeysFile,Id,'key')
                if Key in Mapping:self.Stage(KeysFile,Id,'key',Mapping[Key])
        self.RefreshKeys(); self.Status.set('Native WASD and contextual changes staged. Apply to install.')
    def RefreshKeys(self):
        self.KeyTree.delete(*self.KeyTree.get_children())
        if KeysFile not in self.Sheets:return
        Bindings={N:self.Value(KeysFile,I,'key') for I,N,F in self.Sheets[KeysFile].Rows if 'key' in F}
        Conflicts=KeyConflicts(Bindings); NativeOverlaps=self.NativeConflicts(Bindings)
        Labels={N:F['content'][0] for I,N,F in self.Locale.Rows if 'content' in F} if self.Locale else {}
        for Id,Name,Fields in self.Sheets[KeysFile].Rows:
            Label=re.sub(r'\s*\([^()]*\)\s*$','',Labels.get(KeyMap.get(Name),KeyNames.get(Name,Name)))
            Key=Bindings.get(Name,''); Status=Conflicts.get(Name,'')
            if Name in NativeOverlaps:Status='Camera overlap'+('; '+Status if Status else '')
            if 'key' not in Fields: Status='No existing key field'
            elif Name not in KeyMap: Status=(Status+'; ' if Status else '')+'Tooltip unmapped'
            self.KeyTree.insert('', 'end',iid=Id,values=(Label,KeyContext(Name),Key.upper(),StockKeys.get(Name,'').upper(),Status))
    def EditKey(self,Event):
        Id=self.KeyTree.identify_row(Event.y)
        if not Id:return
        if not self.KeyTargets or self.Locale is None:messagebox.showerror('Controls unavailable','Open the installed main.pak beside lang.pak (or a valid loose localisation file).');return
        if not any(I==Id and 'key' in F for I,N,F in self.Sheets[KeysFile].Rows):return
        Value=simpledialog.askstring('Binding','Enter one letter A–Z or up (verified). Other tokens are not yet verified.',initialvalue=self.Value(KeysFile,Id,'key'),parent=self)
        if Value is None:return
        if not re.fullmatch('[a-zA-Z]|up',Value,re.IGNORECASE):messagebox.showerror('Invalid key','Use one letter or up.');return
        self.Stage(KeysFile,Id,'key',Value.lower()); self.RefreshKeys()
    def KeyPreset(self):
        if not self.KeyTargets or self.Locale is None:messagebox.showinfo('Open archive','Open installed main.pak and localisation first.');return
        for Id,Name,Fields in self.Sheets[KeysFile].Rows:
            if 'key' in Fields and Name in StockKeys:self.Stage(KeysFile,Id,'key',StockKeys[Name])
        self.SyncKeys=True; self.RefreshKeys(); self.Status.set('Stock bindings staged. Apply to write loose overrides.')
    def StageTooltipSync(self):
        if not self.KeyTargets or self.Locale is None:messagebox.showinfo('Open archive','Open installed main.pak and localisation first.');return
        self.SyncKeys=True; self.Status.set('Tooltip synchronisation staged. Apply to install.')
    def ExportAHK(self):
        if 'WASD' in (self.NativeMode.get(),self.NativeOriginalMode):messagebox.showwarning('Native WASD','Restore arrow camera controls before using the legacy AHK helper.');return
        File=filedialog.asksaveasfilename(defaultextension='.ahk',initialfile='SyrianWarfareCamera.ahk',filetypes=[('AutoHotkey v2','*.ahk')]);
        if File:Path(File).write_text('#Requires AutoHotkey v2.0\n#SingleInstance Force\nSetTitleMatchMode 2\n#SuspendExempt True\n^F9::Reload()\n^F10::{\n    Suspend(-1)\n    SoundBeep(A_IsSuspended ? 400 : 800, 150)\n}\n#SuspendExempt False\n#HotIf WinActive("Syrian Warfare") || WinActive("SyrianWarfare")\nw::Up\na::Left\ns::Down\nd::Right\nt::w\ng::a\nh::s\nb::d\n#HotIf\n',encoding='utf-8'); messagebox.showinfo('Saved','Requires AutoHotkey v2. Use only with stock native bindings; custom bindings may conflict. Close any previous AHK helper. Ctrl+F10 toggles. Ctrl+F9 reloads. Window matching is untested.')
    def VisualPreset(self):
        if not self.Options:messagebox.showinfo('Open profile','Select gameoptions.xml first.');return
        for K,V in {'render.bloom':'1','render.grassDistance':'1000','render.shadowMapSize':'4096','render.multisamplingQuality':'4'}.items():
            if K in self.GraphOriginal:self.GraphVars[K].set(V)
    def RefreshRows(self):
        self.RowTree.delete(*self.RowTree.get_children()); self.FieldTree.delete(*self.FieldTree.get_children()); File=Tables[self.TableName.get()]
        if File not in self.Sheets:return
        Query=self.Search.get().lower()
        for Id,Name,Fields in self.Sheets[File].Rows:
            if Query in Name.lower(): self.RowTree.insert('','end',iid=Id,values=(Name,))
    def RefreshFields(self):
        self.FieldTree.delete(*self.FieldTree.get_children()); Selection=self.RowTree.selection(); File=Tables[self.TableName.get()]
        if not Selection or File not in self.Sheets:return
        Id=Selection[0]; Fields=next(Fields for Row,Name,Fields in self.Sheets[File].Rows if Row==Id)
        for Field,(Old,Kind,Span) in Fields.items(): self.FieldTree.insert('','end',iid=Field,values=(Field,self.Value(File,Id,Field),Old))
    def EditField(self,Event):
        Field=self.FieldTree.identify_row(Event.y); Sel=self.RowTree.selection(); File=Tables[self.TableName.get()]
        if not Field or not Sel:return
        Id=Sel[0]; Old,Kind,_=self.Sheets[File].Get(Id,Field)
        Value=simpledialog.askstring(Field,'Engine value ('+Kind+'). Change cautiously.',initialvalue=self.Value(File,Id,Field),parent=self)
        if Value is None:return
        try:self.Sheets[File].Render({(Id,Field):Value})
        except Exception as E:messagebox.showerror('Invalid value',str(E));return
        self.Stage(File,Id,Field,Value);self.RefreshFields()
    def Collect(self):
        if self.Pak:
            Values={K:V.get().strip() for K,V in self.CameraVars.items()}
            for K,V in Values.items():
                Num=float(V); _,Low,High=CameraInfo[K]
                # Preserve original values even if a different build uses a wider range.
                if V!=self.Sheets[CameraFile].Get(self.CameraId,K)[0] and (not math.isfinite(Num) or not Low<=Num<=High):raise ValueError(K+' outside the editor safety range.')
            if float(Values['min_zoom'])>float(Values['max_zoom']) or float(Values['min_roll'])>float(Values['max_roll']):raise ValueError('Camera minimum must not exceed maximum.')
            for K,V in Values.items():self.Stage(CameraFile,self.CameraId,K,V)
        Graph={}
        if self.Options:
            for K,Old in self.GraphOriginal.items():
                V=self.GraphVars[K].get().strip()
                if V==Old:continue
                if GraphicInfo[K][1]=='bool' and V not in ('0','1'):raise ValueError(K+' must be 0 or 1.')
                if not math.isfinite(float(V)) or float(V)<0:raise ValueError(K+' must be a non-negative number.')
                Graph[K]=V
        return {F:C for F,C in self.Pending.items() if C},Graph
    def Export(self):
        try:
            Pending,Graph=self.Collect(); Entries=[]
            for F,Changes in Pending.items():
                for (Row,Field),Value in Changes.items():
                    Name=next(N for R,N,_ in self.Sheets[F].Rows if R==Row); Entries.append({'file':F,'row':Row,'name':Name,'field':Field,'value':Value})
            File=filedialog.asksaveasfilename(defaultextension='.json',initialfile='SWPreset.json',filetypes=[('JSON preset','*.json')]);
            if File:Path(File).write_text(json.dumps({'version':1,'archive':Entries,'graphics':Graph, 'native_camera':self.NativeMode.get() if self.NativeMode.get()!=self.NativeOriginalMode else None, 'edge_scrolling':self.EdgeEnabled.get() if self.EdgeEnabled.get()!=self.EdgeOriginal else None},indent=2),encoding='utf-8'); self.Status.set('Preset exported.')
        except Exception as E:messagebox.showerror('Export failed',str(E))
    def Import(self):
        File=filedialog.askopenfilename(filetypes=[('JSON preset','*.json')]);
        if not File:return
        try:
            Data=json.loads(Path(File).read_text(encoding='utf-8')); Changes=[]
            if Data['version']!=1:raise ValueError('Unknown preset version.')
            Mode=Data.get('native_camera'); Edge=Data.get('edge_scrolling')
            if Edge is not None and (type(Edge) is not bool or not self.NativeTarget):raise ValueError('Preset edge scrolling requires a recognised installed game.dll.')
            if Mode is not None and (Mode not in ('Arrows','WASD') or not self.NativeTarget):raise ValueError('Preset camera mode requires a recognised installed game.dll.')
            for Entry in Data['archive']:
                F,R,N,K,V=(Entry[X] for X in ('file','row','name','field','value'))
                if not isinstance(V,str) or not any(Row==R and Name==N and K in Fields for Row,Name,Fields in self.Sheets[F].Rows):raise ValueError('Preset record not present: '+N)
                
                if F==KeysFile and (K!='key' or not re.fullmatch('[a-z]|up',V)):raise ValueError('Invalid contextual key in preset.')
                self.Sheets[F].Render({(R,K):V}); Changes.append((F,R,K,V))
            for K,V in Data['graphics'].items():
                if K not in self.GraphOriginal or not isinstance(V,str):raise ValueError('Open the matching graphics profile before importing.')
            for F,R,K,V in Changes:
                if F==CameraFile and R==self.CameraId and K in self.CameraVars:self.CameraVars[K].set(V)
                else:self.Stage(F,R,K,V)
            for K,V in Data['graphics'].items():self.GraphVars[K].set(V)
            if Mode is not None:self.NativeMode.set(Mode)
            if Edge is not None:self.EdgeEnabled.set(Edge)
            self.RefreshKeys();self.RefreshFields();self.Status.set('Preset imported and staged. Review before applying.')
        except Exception as E:messagebox.showerror('Import failed',str(E))
    def Discard(self):
        self.SyncKeys=False;self.Pending={};self.NativeMode.set(self.NativeOriginalMode);self.EdgeEnabled.set(self.EdgeOriginal);self.RefreshCamera();self.RefreshKeys();self.RefreshFields()
        for K,V in self.GraphVars.items():V.set(self.GraphOriginal.get(K,''))
        self.Status.set('Staged changes discarded.')
    def Apply(self):
        Temps=[]; Installed=[]; Backups=[]
        try:
            Pending,Graph=self.Collect()
            NativeChange=self.NativeMode.get()!=self.NativeOriginalMode or self.EdgeEnabled.get()!=self.EdgeOriginal
            if not Pending and not Graph and not self.SyncKeys and not NativeChange:messagebox.showinfo('No changes','Nothing to apply.');return
            if not messagebox.askyesno('Apply changes','Close Syrian Warfare before proceeding.\n\n'+str(sum(map(len,Pending.values())))+' table cells and '+str(len(Graph))+' profile settings will change. '+('Camera: '+self.NativeMode.get()+', edge scrolling: '+('on' if self.EdgeEnabled.get() else 'off')+'. ' if NativeChange else '')+'Existing files will be backed up; new loose files can be removed to revert. Continue?'):return
            if GameRunning():raise ValueError("Syrian Warfare is running. Close it before applying changes.")
            KeyChanges=Pending.pop(KeysFile,{})
            if KeysFile in self.Sheets and (NativeChange or KeyChanges):
                Bindings={N:self.Value(KeysFile,I,'key') for I,N,F in self.Sheets[KeysFile].Rows if 'key' in F}
                Overlaps=self.NativeConflicts(Bindings)
                if Overlaps and not messagebox.askyesno('Camera binding overlaps',str(len(Overlaps))+' contextual commands share camera keys. Both actions may trigger. Apply anyway?'):return
            if NativeChange:
                Target=self.NativeTarget
                if Target is None or Target.read_bytes()!=self.NativeSnapshot:raise ValueError('game.dll changed on disk. Reopen main.pak.')
                Stock=self.NativeStock
                OriginalBackup=Target.with_name('game.dll.wasd-original.bak')
                if not OriginalBackup.exists():
                    with OriginalBackup.open('xb') as File:File.write(Stock)
                if OriginalBackup.read_bytes()!=Stock:raise ValueError('Original DLL backup verification failed.')
                Raw=NativeCamera.BuildState(Stock,self.NativeMode.get()=='WASD',self.EdgeEnabled.get())
                Temp=TempPath(Target); Temps.append((Target,Temp)); Temp.write_bytes(Raw)
                if Temp.read_bytes()!=Raw:raise ValueError('Staged DLL verification failed.')
            if KeyChanges or self.SyncKeys:
                if not self.KeyTargets or self.Locale is None:raise ValueError('Installed archive and localisation required.')
                Keys=self.Sheets[KeysFile]
                if any(K!='key' or not re.fullmatch('[a-z]|up',V) for (R,K),V in KeyChanges.items()):raise ValueError('Only existing letter or verified up bindings can be edited.')
                Bindings={N:self.Value(KeysFile,I,'key') for I,N,F in Keys.Rows if 'key' in F}
                Warnings=KeyConflicts(Bindings)
                ChangedNames={N for I,N,F in Keys.Rows if (I,'key') in KeyChanges}
                if any(N in ChangedNames and not V.startswith('Shared stock') for N,V in Warnings.items()):
                    if not messagebox.askyesno('Binding overlaps','Potential overlapping commands detected. Review Controls if unsure. Apply anyway?'):return
                AllKeys={(I,'key'):Bindings[N] for I,N,F in Keys.Rows if N in Bindings}
                Outputs={KeysFile:Keys.Render(KeyChanges),LocaleFile:SyncTooltips(Keys,self.Locale,AllKeys)}
                for F,Raw in Outputs.items():
                    Target=self.KeyTargets[F]
                    if (Target.read_bytes() if Target.exists() else None)!=self.KeySnapshots[F]:raise ValueError('Loose override changed on disk. Reopen main.pak.')
                    Target.parent.mkdir(parents=True,exist_ok=True); Temp=TempPath(Target); Temps.append((Target,Temp));Temp.write_bytes(Raw)
            if Pending:
                if (self.Pak.stat().st_size,self.Pak.stat().st_mtime_ns)!=self.PakStat:raise ValueError('Archive changed on disk. Reopen it first.')
                Output={F:self.Sheets[F].Render(C) for F,C in Pending.items()}; Temp=TempPath(self.Pak); Temps.append((self.Pak,Temp)); Repack(self.Pak,Temp,Output)
            if Graph:
                if self.Options.read_bytes()!=self.OptionsRaw:raise ValueError('Profile changed on disk. Reopen it first.')
                Text=self.OptionsRaw.decode('utf-8-sig')
                for K,V in Graph.items():
                    Pattern=r'(<'+re.escape(K)+r'>)[^<]*(</'+re.escape(K)+r'>)'; Text,Count=re.subn(Pattern,lambda M:M[1]+escape(V)+M[2],Text)
                    if Count!=1:raise ValueError('Unexpected profile layout: '+K)
                Raw=Text.encode('utf-8-sig' if self.OptionsRaw.startswith(b'\xef\xbb\xbf') else 'utf-8');minidom.parseString(Raw)
                Temp=TempPath(self.Options); Temps.append((self.Options,Temp));Temp.write_bytes(Raw)
            Backups=[(Target,Backup(Target)) for Target,Temp in Temps if Target.exists()]
            for Target,Temp in Temps:os.replace(Temp,Target);Installed.append(Target)
            if Pending or KeyChanges or self.SyncKeys:self.LoadPak(self.Pak)
            if NativeChange:
                self.LoadNative(); self.RefreshKeys()
            if Graph:self.LoadOptions(self.Options)
            self.Status.set('Applied. Existing files backed up.');messagebox.showinfo('Applied','Changes installed.\n\nBackups:\n'+'\n'.join(str(B) for T,B in Backups)+'\n\nContextual keys use loose overrides. Native camera mode: '+self.NativeMode.get()+'. Edge scrolling: '+('on' if self.EdgeEnabled.get() else 'off')+'.')
        except Exception as E:
            Failures=[]; Saved=dict(Backups)
            for Target in reversed(Installed):
                try:
                    if Target in Saved:
                        Rollback=TempPath(Target)
                        try:shutil.copy2(Saved[Target],Rollback);os.replace(Rollback,Target)
                        finally:Rollback.unlink(missing_ok=True)
                    else:Target.unlink(missing_ok=True)
                except OSError as Error:Failures.append(str(Target)+': '+str(Error))
            messagebox.showerror('Apply failed',str(E)+('\nRollback failed: '+ '; '.join(Failures) if Failures else '\nNo target changes remain.'))
        finally:
            for Target,Temp in Temps:Temp.unlink(missing_ok=True)
    def Restore(self):
        Choice=messagebox.askyesnocancel('Restore','Restore an archive backup?\nYes = main.pak; No = gameoptions.xml; Cancel = neither.')
        if Choice is None:return
        Target=self.Pak if Choice else self.Options
        if not Target:messagebox.showinfo('Open file','Open the target file first.');return
        File=filedialog.askopenfilename(initialdir=str(Target.parent/'SWConfiguratorBackups'),filetypes=[('Backup','*.bak'),('All files','*')]);
        if not File:return
        try:
            if Path(File).resolve()==Target.resolve():raise ValueError('Select a different backup file.')
            if Choice:
                with zipfile.ZipFile(File) as Z:Sheet(Z.read(CameraFile,pwd=Password));Sheet(Z.read(KeysFile,pwd=Password))
            else:
                if minidom.parse(str(File)).documentElement.tagName!='GameOptions':raise ValueError('Not a profile backup.')
            if not messagebox.askyesno('Restore backup','Close the game. Replace '+str(Target)+' with the selected backup? Current file will also be backed up.'):return
            if GameRunning():raise ValueError("Close Syrian Warfare before restoring a backup.")
            Backup(Target);Temp=TempPath(Target)
            try:shutil.copyfile(File,Temp);os.replace(Temp,Target)
            finally:Temp.unlink(missing_ok=True)
            if Choice:self.LoadPak(Target)
            else:self.LoadOptions(Target)
            self.Status.set('Backup restored.')
        except Exception as E:messagebox.showerror('Restore failed',str(E))

if __name__=='__main__':Configurator().mainloop()
