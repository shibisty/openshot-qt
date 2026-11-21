"""
 @file
 @brief Minimal external plugin loader for OpenShot (installed by openshot-autodub/install.py).

 A plugin is a folder containing `openshot_plugin.json`:
     {"name": "AutoDub", "module": "openshot_autodub", "entry": "register"}
 The folder is put on sys.path, `module` is imported and `entry(main_window)` is called
 once the main window has created its docks and menus.

 Plugin folders are listed in:
   * ~/.openshot_qt/plugins.json   {"paths": ["C:/path/to/plugin", ...]}
   * env OPENSHOT_PLUGIN_PATH      (os.pathsep separated)
 A broken plugin is logged and skipped; it never prevents OpenShot from starting.
"""

import importlib
import json
import os
import sys

from classes import info
from classes.logger import log

PLUGINS_FILE = os.path.join(info.USER_PATH, "plugins.json")
LOADED = {}


def plugin_paths():
    paths = []
    try:
        if os.path.isfile(PLUGINS_FILE):
            with open(PLUGINS_FILE, "r", encoding="utf-8") as fh:
                paths.extend((json.load(fh) or {}).get("paths") or [])
    except Exception:
        log.warning("Plugins: cannot read %s", PLUGINS_FILE, exc_info=True)
    env = os.environ.get("OPENSHOT_PLUGIN_PATH", "")
    paths.extend(p for p in env.split(os.pathsep) if p.strip())
    seen, result = set(), []
    for path in paths:
        norm = os.path.normcase(os.path.abspath(os.path.expanduser(path)))
        if norm not in seen:
            seen.add(norm)
            result.append(os.path.abspath(os.path.expanduser(path)))
    return result


def load_plugins(window):
    for folder in plugin_paths():
        manifest_path = os.path.join(folder, "openshot_plugin.json")
        if not os.path.isfile(manifest_path):
            log.warning("Plugins: %s has no openshot_plugin.json, skipped", folder)
            continue
        try:
            with open(manifest_path, "r", encoding="utf-8") as fh:
                manifest = json.load(fh)
            module_name = manifest["module"]
            if folder not in sys.path:
                sys.path.insert(0, folder)
            module = importlib.import_module(module_name)
            entry = getattr(module, manifest.get("entry", "register"))
            LOADED[manifest.get("name", module_name)] = entry(window)
            log.info("Plugins: loaded %s from %s", manifest.get("name", module_name), folder)
        except Exception:
            log.error("Plugins: failed to load %s", folder, exc_info=True)
