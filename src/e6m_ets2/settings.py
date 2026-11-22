"""Local build locations; game assets and tool downloads stay outside Git."""
from pathlib import Path
import os

PROJECT = Path(__file__).resolve().parent
ROOT = Path(os.environ.get('E6M_WORKSPACE', PROJECT.parents[1]/'work/e6m_ets2')).resolve()
BUS = Path(os.environ.get('E6M_OMSI_BUS', r'A:\SteamLibrary\steamapps\common\OMSI 2\Vehicles\ADL_E500MMC_KMB_E6M'))
GAME_HOME = Path(os.environ.get('E6M_ETS2_HOME', Path.home()/'Documents/Euro Truck Simulator 2'))
VERSION = '0.3.0'
