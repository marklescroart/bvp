import os
try:
    import configparser
except ImportError:
    import ConfigParser as configparser
# Fancier way of finding appropriate directories for config files 
# in each OS (*nix, windows, whatever). Not done for now.
#from . import appdirs

cfg_dir = os.path.dirname(__file__)
usercfg = os.path.join(cfg_dir, "options.cfg")
# For fancy way:
# userdir = appdirs.user_data_dir("bvp", "MarkLescroart") #(not sure if args here are right)
# usercfg = os.path.join(userdir, "options.cfg")

config = configparser.ConfigParser()
config.readfp(open(os.path.join(cfg_dir, 'defaults.cfg')))

# the config.read(usercfg) call, even though it is an if statement,
# reads in user-specific configuration file and overwrites defaults
if len(config.read(usercfg)) == 0:
    # For fancy way:
    #os.makedirs(userdir)
    with open(usercfg, 'w') as fp:
        config.write(fp)