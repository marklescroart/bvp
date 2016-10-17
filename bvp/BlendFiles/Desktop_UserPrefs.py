import bpy
import os

def kmi_props_setattr(kmi_props, attr, value):
    try:
        setattr(kmi_props, attr, value)
    except AttributeError:
        print("Warning: property '%s' not found in keymap item '%s'" %
              (attr, kmi_props.__class__.__name__))
    except Exception as e:
        print("Warning: %r" % e)

wm = bpy.context.window_manager
kc = wm.keyconfigs.new(os.path.splitext(os.path.basename(__file__))[0])

# Map Console
km = kc.keymaps.new('Console', space_type='CONSOLE', region_type='WINDOW', modal=False)

kmi = km.keymap_items.new('console.move', 'LEFT_ARROW', 'PRESS', ctrl=True)
kmi_props_setattr(kmi.properties, 'type', 'PREVIOUS_WORD')
kmi = km.keymap_items.new('console.move', 'RIGHT_ARROW', 'PRESS', ctrl=True)
kmi_props_setattr(kmi.properties, 'type', 'NEXT_WORD')
kmi = km.keymap_items.new('console.move', 'HOME', 'PRESS')
kmi_props_setattr(kmi.properties, 'type', 'LINE_BEGIN')
kmi = km.keymap_items.new('console.move', 'END', 'PRESS')
kmi_props_setattr(kmi.properties, 'type', 'LINE_END')
kmi = km.keymap_items.new('wm.context_cycle_int', 'WHEELUPMOUSE', 'PRESS', ctrl=True)
kmi_props_setattr(kmi.properties, 'data_path', 'space_data.font_size')
kmi_props_setattr(kmi.properties, 'reverse', False)
kmi = km.keymap_items.new('wm.context_cycle_int', 'WHEELDOWNMOUSE', 'PRESS', ctrl=True)
kmi_props_setattr(kmi.properties, 'data_path', 'space_data.font_size')
kmi_props_setattr(kmi.properties, 'reverse', True)
kmi = km.keymap_items.new('wm.context_cycle_int', 'NUMPAD_PLUS', 'PRESS', ctrl=True)
kmi_props_setattr(kmi.properties, 'data_path', 'space_data.font_size')
kmi_props_setattr(kmi.properties, 'reverse', False)
kmi = km.keymap_items.new('wm.context_cycle_int', 'NUMPAD_MINUS', 'PRESS', ctrl=True)
kmi_props_setattr(kmi.properties, 'data_path', 'space_data.font_size')
kmi_props_setattr(kmi.properties, 'reverse', True)
kmi = km.keymap_items.new('console.move', 'LEFT_ARROW', 'PRESS')
kmi_props_setattr(kmi.properties, 'type', 'PREVIOUS_CHARACTER')
kmi = km.keymap_items.new('console.move', 'RIGHT_ARROW', 'PRESS')
kmi_props_setattr(kmi.properties, 'type', 'NEXT_CHARACTER')
kmi = km.keymap_items.new('console.history_cycle', 'UP_ARROW', 'PRESS')
kmi_props_setattr(kmi.properties, 'reverse', True)
kmi = km.keymap_items.new('console.history_cycle', 'DOWN_ARROW', 'PRESS')
kmi_props_setattr(kmi.properties, 'reverse', False)
kmi = km.keymap_items.new('console.delete', 'DEL', 'PRESS')
kmi_props_setattr(kmi.properties, 'type', 'NEXT_CHARACTER')
kmi = km.keymap_items.new('console.delete', 'BACK_SPACE', 'PRESS')
kmi_props_setattr(kmi.properties, 'type', 'PREVIOUS_CHARACTER')
kmi = km.keymap_items.new('console.delete', 'BACK_SPACE', 'PRESS', shift=True)
kmi_props_setattr(kmi.properties, 'type', 'PREVIOUS_CHARACTER')
kmi = km.keymap_items.new('console.delete', 'DEL', 'PRESS', ctrl=True)
kmi_props_setattr(kmi.properties, 'type', 'NEXT_WORD')
kmi = km.keymap_items.new('console.delete', 'BACK_SPACE', 'PRESS', ctrl=True)
kmi_props_setattr(kmi.properties, 'type', 'PREVIOUS_WORD')
kmi = km.keymap_items.new('console.clear_line', 'RET', 'PRESS', shift=True)
kmi = km.keymap_items.new('console.clear_line', 'NUMPAD_ENTER', 'PRESS', shift=True)
kmi = km.keymap_items.new('console.execute', 'RET', 'PRESS')
kmi_props_setattr(kmi.properties, 'interactive', True)
kmi = km.keymap_items.new('console.execute', 'NUMPAD_ENTER', 'PRESS')
kmi_props_setattr(kmi.properties, 'interactive', True)
kmi = km.keymap_items.new('console.autocomplete', 'TAB', 'PRESS')
kmi = km.keymap_items.new('console.copy_as_script', 'C', 'PRESS', shift=True, ctrl=True)
kmi = km.keymap_items.new('console.copy', 'C', 'PRESS', ctrl=True)
kmi = km.keymap_items.new('console.paste', 'V', 'PRESS', ctrl=True)
kmi = km.keymap_items.new('console.select_set', 'LEFTMOUSE', 'PRESS')
kmi = km.keymap_items.new('console.insert', 'TAB', 'PRESS', ctrl=True)
kmi_props_setattr(kmi.properties, 'text', '\t')
kmi = km.keymap_items.new('console.indent', 'TAB', 'PRESS')
kmi = km.keymap_items.new('console.unindent', 'TAB', 'PRESS', shift=True)
kmi = km.keymap_items.new('console.insert', 'TEXTINPUT', 'ANY', any=True)

