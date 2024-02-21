import json, asyncio, subprocess, os

if not os.path.exists("logger.py"): 
    print("Missing logger.py! RoWhoIs will not be able to initialize.")
    exit(-1)
from logger import AsyncLogCollector

for folder in ["logs", "cache", "cache/clothing"]:
    if not os.path.exists(folder): os.makedirs(folder)
logCollector = AsyncLogCollector("logs/Server.log")

def sync_logging(errorLevel, errorContent):
    log_functions = {"fatal": logCollector.fatal,"error": logCollector.error,"warn": logCollector.warn,"info": logCollector.info}
    asyncio.new_event_loop().run_until_complete(log_functions[errorLevel](errorContent))

def get_version():
    try:
        short_commit_id = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).strip()
        return short_commit_id.decode('utf-8')
    except subprocess.CalledProcessError as e: return 0 # Assume not git workspace
    
shortHash = get_version()
sync_logging("info", f"Initializing RoWhoIs on version {shortHash}...")

for file in ["secret.py", "Roquest.py", "RoWhoIs.py", "config.json"]:
    if not os.path.exists(file):
        sync_logging("fatal", f"Missing {file}! RoWhoIs will not be able to initialize.")
        exit(-1)

def load_runtime(shortHash):
    optOut, userBlocklist, staffIds, proxyUrls = [], [], [], []
    try:
        # RoWhoIs
        with open('config.json', 'r') as file: config = json.load(file)
        testingMode = config.get("RoWhoIs", {}).get("testing", False)
        if testingMode: sync_logging("warn", "Currently running in testing mode.")
        else: sync_logging("warn", "Currently running in production mode.")
        verboseLogging = config.get("RoWhoIs", {}).get("log_config_updates", False)
        if not verboseLogging: sync_logging("info", "In config.json: log_config_updates set to False. Successful configuration updates will not be logged.")
        optOut.extend([id for module_data in config.values() if 'opt_out' in module_data for id in module_data['opt_out']])
        if verboseLogging: sync_logging("info", "Opt-out IDs updated successfully.")
        userBlocklist.extend([id for module_data in config.values() if 'banned_users' in module_data for id in module_data['banned_users']])
        if verboseLogging: sync_logging("info", "User blocklist updated successfully.")
        staffIds.extend([id for module_data in config.values() if 'admin_ids' in module_data for id in module_data['admin_ids']])
        # Roquest
        proxyingEnabled = config.get("Proxy", {}).get("proxying_enabled", False)
        logProxying = config.get("Roquest", {}).get("log_proxying", False)
        username = config.get("Proxy", {}).get("username", False)
        password = config.get("Proxy", {}).get("password", False)
        if password == "": password = None
        proxyUrls.extend([id for module_data in config.values() if 'proxy_urls' in module_data for id in module_data['proxy_urls']])
        try:
            import RoWhoIs, Roquest
            Roquest.set_configs(proxyingEnabled, proxyUrls, username, password, logProxying)
            RoWhoIs.main(testingMode, staffIds, optOut, userBlocklist, verboseLogging, shortHash)
        except Exception as e: sync_logging("fatal", f"A fatal error occurred during runtime: {e}")
    except Exception as e: sync_logging("fatal", f"Failed to initialize! Invalid config? {e}")

load_runtime(shortHash)