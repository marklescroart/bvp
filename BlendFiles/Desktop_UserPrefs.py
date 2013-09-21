import bpy
import os

wm = bpy.context.window_manager
kc = wm.keyconfigs.new(os.path.splitext(os.path.basename(__file__))[0])

# Map Console
km = kc.keymaps.new('Console', space_type='CONSOLE', region_type='WINDOW', modal=False)

kmi = km.keymap_items.new('console.move', 'LEFT_ARROW', 'PRESS', ctrl=True)
