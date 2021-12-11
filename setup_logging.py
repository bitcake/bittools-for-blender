import logging

logging.basicConfig(filename='bitlogs.log', level=logging.DEBUG,
                    format='%(asctime)-15s %(levelname)8s %(name)s %(message)s')

for name in ('bitcake_exporter', 'collider_tools', 'addon_prefs', 'menu_side'):
    logging.getLogger(name).setLevel(logging.DEBUG)

def register():
    pass