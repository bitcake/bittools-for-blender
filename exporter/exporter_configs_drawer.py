def draw_panel(self, context):
    panel_prefs = context.scene.exporter_configs
    layout = self.layout
    layout.separator()
    layout.label(text='Export Configs')
    row = layout.row(align=True)
    row.prop(panel_prefs, 'origin_transform', toggle=1, icon_value=1, icon='OBJECT_ORIGIN')
    row.prop(panel_prefs, 'apply_transform', toggle=1, icon_value=1, icon='CHECKMARK')
    row.prop(panel_prefs, 'export_batch', toggle=1, icon_value=1, icon='FILE_NEW')

    row = layout.row(align=True)
    row.prop(panel_prefs, 'export_nla_strips', toggle=1, icon_value=1, icon='NLA')

    row = layout.row(align=True)
    row.prop(panel_prefs, 'export_selected', toggle=1, icon='RESTRICT_SELECT_OFF')
    row.prop(panel_prefs, 'export_collection', toggle=1, icon='OUTLINER_COLLECTION')
    row = layout.row()
    row.operator('bitcake.toggle_all_colliders_visibility', text='Toggle Colliders Visibility', icon='HIDE_OFF')

    return

def register():
    pass

def unregister():
    pass