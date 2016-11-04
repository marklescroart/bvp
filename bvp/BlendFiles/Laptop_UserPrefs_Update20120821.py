import bpy
import os

wm = bpy.context.window_manager
kc = wm.keyconfigs.new(os.path.splitext(os.path.basename(__file__))[0])

# Map 3D View
km = kc.keymaps.new('3D View', space_type='VIEW_3D', region_type='WINDOW', modal=False)

kmi = km.keymap_items.new('view3d.manipulator', 'LEFTMOUSE', 'PRESS', any=True)
kmi.properties.release_confirm = True
kmi = km.keymap_items.new('view3d.cursor3d', 'ACTIONMOUSE', 'PRESS')
kmi = km.keymap_items.new('view3d.rotate', 'MIDDLEMOUSE', 'PRESS')
kmi = km.keymap_items.new('view3d.move', 'MIDDLEMOUSE', 'PRESS', shift=True)
kmi = km.keymap_items.new('view3d.zoom', 'MIDDLEMOUSE', 'PRESS', ctrl=True)
kmi = km.keymap_items.new('view3d.dolly', 'MIDDLEMOUSE', 'PRESS', shift=True, ctrl=True)
kmi = km.keymap_items.new('view3d.view_selected', 'NUMPAD_PERIOD', 'PRESS')
kmi = km.keymap_items.new('view3d.view_center_cursor', 'NUMPAD_PERIOD', 'PRESS', ctrl=True)
kmi = km.keymap_items.new('view3d.fly', 'F', 'PRESS', shift=True)
kmi = km.keymap_items.new('view3d.smoothview', 'TIMER1', 'ANY', any=True)
kmi = km.keymap_items.new('view3d.rotate', 'TRACKPADPAN', 'ANY', alt=True)
kmi = km.keymap_items.new('view3d.rotate', 'MOUSEROTATE', 'ANY')
kmi = km.keymap_items.new('view3d.move', 'TRACKPADPAN', 'ANY')
kmi = km.keymap_items.new('view3d.zoom', 'TRACKPADZOOM', 'ANY')
kmi = km.keymap_items.new('view3d.zoom', 'NUMPAD_PLUS', 'PRESS')
kmi.properties.delta = 1
kmi = km.keymap_items.new('view3d.zoom', 'NUMPAD_MINUS', 'PRESS')
kmi.properties.delta = -1
kmi = km.keymap_items.new('view3d.zoom', 'EQUAL', 'PRESS', ctrl=True)
kmi.properties.delta = 1
kmi = km.keymap_items.new('view3d.zoom', 'MINUS', 'PRESS', ctrl=True)
kmi.properties.delta = -1
kmi = km.keymap_items.new('view3d.zoom', 'WHEELINMOUSE', 'PRESS')
kmi.properties.delta = 1
kmi = km.keymap_items.new('view3d.zoom', 'WHEELOUTMOUSE', 'PRESS')
kmi.properties.delta = -1
kmi = km.keymap_items.new('view3d.zoom_camera_1_to_1', 'NUMPAD_ENTER', 'PRESS', shift=True)
kmi = km.keymap_items.new('view3d.view_center_camera', 'HOME', 'PRESS')
kmi = km.keymap_items.new('view3d.view_all', 'HOME', 'PRESS')
kmi.properties.center = False
kmi = km.keymap_items.new('view3d.view_all', 'C', 'PRESS', shift=True)
kmi.properties.center = True
kmi = km.keymap_items.new('view3d.viewnumpad', 'ZERO', 'PRESS', shift=True, ctrl=True)
kmi.properties.type = 'CAMERA'
kmi = km.keymap_items.new('view3d.viewnumpad', 'ONE', 'PRESS', shift=True, ctrl=True)
kmi.properties.type = 'FRONT'
kmi = km.keymap_items.new('view3d.view_orbit', 'TWO', 'PRESS', shift=True, ctrl=True)
kmi.properties.type = 'ORBITDOWN'
kmi = km.keymap_items.new('view3d.viewnumpad', 'THREE', 'PRESS', shift=True, ctrl=True)
kmi.properties.type = 'RIGHT'
kmi = km.keymap_items.new('view3d.view_orbit', 'FOUR', 'PRESS', shift=True, ctrl=True)
kmi.properties.type = 'ORBITLEFT'
kmi = km.keymap_items.new('view3d.view_persportho', 'FIVE', 'PRESS', shift=True, ctrl=True)
kmi = km.keymap_items.new('view3d.view_orbit', 'SIX', 'PRESS', shift=True, ctrl=True)
kmi.properties.type = 'ORBITRIGHT'
kmi = km.keymap_items.new('view3d.viewnumpad', 'SEVEN', 'PRESS', shift=True, ctrl=True)
kmi.properties.type = 'TOP'
kmi = km.keymap_items.new('view3d.view_orbit', 'EIGHT', 'PRESS', shift=True, ctrl=True)
kmi.properties.type = 'ORBITUP'
kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_1', 'PRESS', ctrl=True)
kmi.properties.type = 'BACK'
kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_3', 'PRESS', ctrl=True)
kmi.properties.type = 'LEFT'
kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_7', 'PRESS', ctrl=True)
kmi.properties.type = 'BOTTOM'
kmi = km.keymap_items.new('view3d.view_pan', 'NUMPAD_2', 'PRESS', ctrl=True)
kmi.properties.type = 'PANDOWN'
kmi = km.keymap_items.new('view3d.view_pan', 'NUMPAD_4', 'PRESS', ctrl=True)
kmi.properties.type = 'PANLEFT'
kmi = km.keymap_items.new('view3d.view_pan', 'NUMPAD_6', 'PRESS', ctrl=True)
kmi.properties.type = 'PANRIGHT'
kmi = km.keymap_items.new('view3d.view_pan', 'NUMPAD_8', 'PRESS', ctrl=True)
kmi.properties.type = 'PANUP'
kmi = km.keymap_items.new('view3d.view_pan', 'WHEELUPMOUSE', 'PRESS', ctrl=True)
kmi.properties.type = 'PANRIGHT'
kmi = km.keymap_items.new('view3d.view_pan', 'WHEELDOWNMOUSE', 'PRESS', ctrl=True)
kmi.properties.type = 'PANLEFT'
kmi = km.keymap_items.new('view3d.view_pan', 'WHEELUPMOUSE', 'PRESS', shift=True)
kmi.properties.type = 'PANUP'
kmi = km.keymap_items.new('view3d.view_pan', 'WHEELDOWNMOUSE', 'PRESS', shift=True)
kmi.properties.type = 'PANDOWN'
kmi = km.keymap_items.new('view3d.view_orbit', 'WHEELUPMOUSE', 'PRESS', ctrl=True, alt=True)
kmi.properties.type = 'ORBITLEFT'
kmi = km.keymap_items.new('view3d.view_orbit', 'WHEELDOWNMOUSE', 'PRESS', ctrl=True, alt=True)
kmi.properties.type = 'ORBITRIGHT'
kmi = km.keymap_items.new('view3d.view_orbit', 'WHEELUPMOUSE', 'PRESS', shift=True, alt=True)
kmi.properties.type = 'ORBITUP'
kmi = km.keymap_items.new('view3d.view_orbit', 'WHEELDOWNMOUSE', 'PRESS', shift=True, alt=True)
kmi.properties.type = 'ORBITDOWN'
kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_1', 'PRESS', shift=True)
kmi.properties.type = 'FRONT'
kmi.properties.align_active = True
kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_3', 'PRESS', shift=True)
kmi.properties.type = 'RIGHT'
kmi.properties.align_active = True
kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_7', 'PRESS', shift=True)
kmi.properties.type = 'TOP'
kmi.properties.align_active = True
kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_1', 'PRESS', shift=True, ctrl=True)
kmi.properties.type = 'BACK'
kmi.properties.align_active = True
kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_3', 'PRESS', shift=True, ctrl=True)
kmi.properties.type = 'LEFT'
kmi.properties.align_active = True
kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_7', 'PRESS', shift=True, ctrl=True)
kmi.properties.type = 'BOTTOM'
kmi.properties.align_active = True
kmi = km.keymap_items.new('view3d.ndof_orbit', 'NDOF_BUTTON_MENU', 'ANY')
kmi = km.keymap_items.new('view3d.ndof_pan', 'NDOF_BUTTON_MENU', 'ANY', shift=True)
kmi = km.keymap_items.new('view3d.view_selected', 'NDOF_BUTTON_FIT', 'PRESS')
kmi = km.keymap_items.new('view3d.viewnumpad', 'NDOF_BUTTON_FRONT', 'PRESS')
kmi.properties.type = 'FRONT'
kmi = km.keymap_items.new('view3d.viewnumpad', 'NDOF_BUTTON_BACK', 'PRESS')
kmi.properties.type = 'BACK'
kmi = km.keymap_items.new('view3d.viewnumpad', 'NDOF_BUTTON_LEFT', 'PRESS')
kmi.properties.type = 'LEFT'
kmi = km.keymap_items.new('view3d.viewnumpad', 'NDOF_BUTTON_RIGHT', 'PRESS')
kmi.properties.type = 'RIGHT'
kmi = km.keymap_items.new('view3d.viewnumpad', 'NDOF_BUTTON_TOP', 'PRESS')
kmi.properties.type = 'TOP'
kmi = km.keymap_items.new('view3d.viewnumpad', 'NDOF_BUTTON_BOTTOM', 'PRESS')
kmi.properties.type = 'BOTTOM'
kmi = km.keymap_items.new('view3d.viewnumpad', 'NDOF_BUTTON_FRONT', 'PRESS', shift=True)
kmi.properties.type = 'FRONT'
kmi.properties.align_active = True
kmi = km.keymap_items.new('view3d.viewnumpad', 'NDOF_BUTTON_RIGHT', 'PRESS', shift=True)
kmi.properties.type = 'RIGHT'
kmi.properties.align_active = True
kmi = km.keymap_items.new('view3d.viewnumpad', 'NDOF_BUTTON_TOP', 'PRESS', shift=True)
kmi.properties.type = 'TOP'
kmi.properties.align_active = True
kmi = km.keymap_items.new('view3d.localview', 'NUMPAD_SLASH', 'PRESS')
kmi = km.keymap_items.new('view3d.layers', 'ACCENT_GRAVE', 'PRESS')
kmi.properties.nr = 0
kmi = km.keymap_items.new('view3d.layers', 'ONE', 'PRESS', any=True)
kmi.properties.nr = 1
kmi = km.keymap_items.new('view3d.layers', 'TWO', 'PRESS', any=True)
kmi.properties.nr = 2
kmi = km.keymap_items.new('view3d.layers', 'THREE', 'PRESS', any=True)
kmi.properties.nr = 3
kmi = km.keymap_items.new('view3d.layers', 'FOUR', 'PRESS', any=True)
kmi.properties.nr = 4
kmi = km.keymap_items.new('view3d.layers', 'FIVE', 'PRESS', any=True)
kmi.properties.nr = 5
kmi = km.keymap_items.new('view3d.layers', 'SIX', 'PRESS', any=True)
kmi.properties.nr = 6
kmi = km.keymap_items.new('view3d.layers', 'SEVEN', 'PRESS', any=True)
kmi.properties.nr = 7
kmi = km.keymap_items.new('view3d.layers', 'EIGHT', 'PRESS', any=True)
kmi.properties.nr = 8
kmi = km.keymap_items.new('view3d.layers', 'NINE', 'PRESS', any=True)
kmi.properties.nr = 9
kmi = km.keymap_items.new('view3d.layers', 'ZERO', 'PRESS', any=True)
kmi.properties.nr = 10
kmi = km.keymap_items.new('wm.context_toggle_enum', 'Z', 'PRESS')
kmi.properties.data_path = 'space_data.viewport_shade'
kmi.properties.value_1 = 'SOLID'
kmi.properties.value_2 = 'WIREFRAME'
kmi = km.keymap_items.new('wm.context_toggle_enum', 'Z', 'PRESS', alt=True)
kmi.properties.data_path = 'space_data.viewport_shade'
kmi.properties.value_1 = 'TEXTURED'
kmi.properties.value_2 = 'SOLID'
kmi = km.keymap_items.new('view3d.select', 'SELECTMOUSE', 'PRESS')
kmi = km.keymap_items.new('view3d.select', 'SELECTMOUSE', 'PRESS', shift=True)
kmi.properties.extend = True
kmi = km.keymap_items.new('view3d.select', 'SELECTMOUSE', 'PRESS', ctrl=True)
kmi.properties.center = True
kmi.properties.object = True
kmi = km.keymap_items.new('view3d.select', 'SELECTMOUSE', 'PRESS', alt=True)
kmi.properties.enumerate = True
kmi = km.keymap_items.new('view3d.select', 'SELECTMOUSE', 'PRESS', shift=True, ctrl=True)
kmi.properties.extend = True
kmi.properties.center = True
kmi = km.keymap_items.new('view3d.select', 'SELECTMOUSE', 'PRESS', ctrl=True, alt=True)
kmi.properties.center = True
kmi.properties.enumerate = True
kmi = km.keymap_items.new('view3d.select', 'SELECTMOUSE', 'PRESS', shift=True, alt=True)
kmi.properties.extend = True
kmi.properties.enumerate = True
kmi = km.keymap_items.new('view3d.select', 'SELECTMOUSE', 'PRESS', shift=True, ctrl=True, alt=True)
kmi.properties.extend = True
kmi.properties.center = True
kmi.properties.enumerate = True
kmi = km.keymap_items.new('view3d.select_border', 'B', 'PRESS')
kmi = km.keymap_items.new('view3d.select_lasso', 'EVT_TWEAK_A', 'ANY', ctrl=True)
kmi = km.keymap_items.new('view3d.select_lasso', 'EVT_TWEAK_A', 'ANY', shift=True, ctrl=True)
kmi.properties.deselect = True
kmi = km.keymap_items.new('view3d.select_circle', 'C', 'PRESS')
kmi = km.keymap_items.new('view3d.clip_border', 'B', 'PRESS', alt=True)
kmi = km.keymap_items.new('view3d.zoom_border', 'B', 'PRESS', shift=True)
kmi = km.keymap_items.new('view3d.render_border', 'B', 'PRESS', shift=True)
kmi = km.keymap_items.new('view3d.camera_to_view', 'NUMPAD_0', 'PRESS', ctrl=True, alt=True)
kmi = km.keymap_items.new('view3d.object_as_camera', 'NUMPAD_0', 'PRESS', ctrl=True)
kmi = km.keymap_items.new('wm.call_menu', 'S', 'PRESS', shift=True)
kmi.properties.name = 'VIEW3D_MT_snap'
kmi = km.keymap_items.new('wm.context_set_enum', 'COMMA', 'PRESS')
kmi.properties.data_path = 'space_data.pivot_point'
kmi.properties.value = 'BOUNDING_BOX_CENTER'
kmi = km.keymap_items.new('wm.context_set_enum', 'COMMA', 'PRESS', ctrl=True)
kmi.properties.data_path = 'space_data.pivot_point'
kmi.properties.value = 'MEDIAN_POINT'
kmi = km.keymap_items.new('wm.context_toggle', 'COMMA', 'PRESS', alt=True)
kmi.properties.data_path = 'space_data.use_pivot_point_align'
kmi = km.keymap_items.new('wm.context_toggle', 'SPACE', 'PRESS', ctrl=True)
kmi.properties.data_path = 'space_data.show_manipulator'
kmi = km.keymap_items.new('wm.context_set_enum', 'PERIOD', 'PRESS')
kmi.properties.data_path = 'space_data.pivot_point'
kmi.properties.value = 'CURSOR'
kmi = km.keymap_items.new('wm.context_set_enum', 'PERIOD', 'PRESS', ctrl=True)
kmi.properties.data_path = 'space_data.pivot_point'
kmi.properties.value = 'INDIVIDUAL_ORIGINS'
kmi = km.keymap_items.new('wm.context_set_enum', 'PERIOD', 'PRESS', alt=True)
kmi.properties.data_path = 'space_data.pivot_point'
kmi.properties.value = 'ACTIVE_ELEMENT'
kmi = km.keymap_items.new('transform.translate', 'G', 'PRESS')
kmi = km.keymap_items.new('transform.translate', 'EVT_TWEAK_S', 'ANY')
kmi = km.keymap_items.new('transform.rotate', 'R', 'PRESS')
kmi = km.keymap_items.new('transform.resize', 'S', 'PRESS')
kmi = km.keymap_items.new('transform.warp', 'W', 'PRESS', shift=True)
kmi = km.keymap_items.new('transform.tosphere', 'S', 'PRESS', shift=True, alt=True)
kmi = km.keymap_items.new('transform.shear', 'S', 'PRESS', shift=True, ctrl=True, alt=True)
kmi = km.keymap_items.new('transform.select_orientation', 'SPACE', 'PRESS', alt=True)
kmi = km.keymap_items.new('transform.create_orientation', 'SPACE', 'PRESS', ctrl=True, alt=True)
kmi.properties.use = True
kmi = km.keymap_items.new('transform.mirror', 'M', 'PRESS', ctrl=True)
kmi = km.keymap_items.new('wm.context_toggle', 'TAB', 'PRESS', shift=True)
kmi.properties.data_path = 'tool_settings.use_snap'
kmi = km.keymap_items.new('transform.snap_type', 'TAB', 'PRESS', shift=True, ctrl=True)
kmi = km.keymap_items.new('transform.translate', 'T', 'PRESS', shift=True)
kmi.properties.texture_space = True
kmi = km.keymap_items.new('transform.resize', 'T', 'PRESS', shift=True, alt=True)
kmi.properties.texture_space = True

# Map Console
km = kc.keymaps.new('Console', space_type='CONSOLE', region_type='WINDOW', modal=False)

kmi = km.keymap_items.new('console.move', 'LEFT_ARROW', 'PRESS', oskey=True)
kmi.properties.type = 'LINE_BEGIN'
kmi = km.keymap_items.new('console.move', 'RIGHT_ARROW', 'PRESS', oskey=True)
kmi.properties.type = 'LINE_END'
kmi = km.keymap_items.new('console.move', 'LEFT_ARROW', 'PRESS', ctrl=True)
kmi.properties.type = 'PREVIOUS_WORD'
kmi = km.keymap_items.new('console.move', 'RIGHT_ARROW', 'PRESS', ctrl=True)
kmi.properties.type = 'NEXT_WORD'
kmi = km.keymap_items.new('console.move', 'HOME', 'PRESS')
kmi.properties.type = 'LINE_BEGIN'
kmi = km.keymap_items.new('console.move', 'END', 'PRESS')
kmi.properties.type = 'LINE_END'
kmi = km.keymap_items.new('wm.context_cycle_int', 'WHEELUPMOUSE', 'PRESS', ctrl=True)
kmi.properties.data_path = 'space_data.font_size'
kmi.properties.reverse = False
kmi = km.keymap_items.new('wm.context_cycle_int', 'WHEELDOWNMOUSE', 'PRESS', ctrl=True)
kmi.properties.data_path = 'space_data.font_size'
kmi.properties.reverse = True
kmi = km.keymap_items.new('wm.context_cycle_int', 'NUMPAD_PLUS', 'PRESS', ctrl=True)
kmi.properties.data_path = 'space_data.font_size'
kmi.properties.reverse = False
kmi = km.keymap_items.new('wm.context_cycle_int', 'NUMPAD_MINUS', 'PRESS', ctrl=True)
kmi.properties.data_path = 'space_data.font_size'
kmi.properties.reverse = True
kmi = km.keymap_items.new('console.move', 'LEFT_ARROW', 'PRESS')
kmi.properties.type = 'PREVIOUS_CHARACTER'
kmi = km.keymap_items.new('console.move', 'RIGHT_ARROW', 'PRESS')
kmi.properties.type = 'NEXT_CHARACTER'
kmi = km.keymap_items.new('console.history_cycle', 'UP_ARROW', 'PRESS')
kmi.properties.reverse = True
kmi = km.keymap_items.new('console.history_cycle', 'DOWN_ARROW', 'PRESS')
kmi = km.keymap_items.new('console.delete', 'DEL', 'PRESS')
kmi.properties.type = 'NEXT_CHARACTER'
kmi = km.keymap_items.new('console.delete', 'BACK_SPACE', 'PRESS')
kmi.properties.type = 'PREVIOUS_CHARACTER'
kmi = km.keymap_items.new('console.delete', 'BACK_SPACE', 'PRESS', shift=True)
kmi.properties.type = 'PREVIOUS_CHARACTER'
kmi = km.keymap_items.new('console.execute', 'RET', 'PRESS')
kmi = km.keymap_items.new('console.execute', 'NUMPAD_ENTER', 'PRESS')
kmi = km.keymap_items.new('console.autocomplete', 'TAB', 'PRESS')
kmi = km.keymap_items.new('console.copy', 'C', 'PRESS', ctrl=True)
kmi = km.keymap_items.new('console.paste', 'V', 'PRESS', ctrl=True)
kmi = km.keymap_items.new('console.copy', 'C', 'PRESS', oskey=True)
kmi = km.keymap_items.new('console.paste', 'V', 'PRESS', oskey=True)
kmi = km.keymap_items.new('console.select_set', 'LEFTMOUSE', 'PRESS')
kmi = km.keymap_items.new('console.insert', 'TAB', 'PRESS')
kmi.properties.text = '\t'
kmi = km.keymap_items.new('console.insert', 'NONE', 'ANY', any=True)

