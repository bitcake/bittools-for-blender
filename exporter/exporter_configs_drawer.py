def draw_panel(self, context):
    exporter_configs = context.scene.exporter_configs
    layout = self.layout

    layout.separator()
    layout.label(text='Export Configs')

    row = layout.row(align=True)
    row.prop(exporter_configs, 'origin_transform', toggle=1, icon_value=1, icon='OBJECT_ORIGIN')
    row.prop(exporter_configs, 'apply_transform', toggle=1, icon_value=1, icon='CHECKMARK')
    row.prop(exporter_configs, 'export_batch', toggle=1, icon_value=1, icon='FILE_NEW')

    if exporter_configs.export_batch:
        row = layout.row(align=True)
        row.prop(exporter_configs, 'collection_to_folder', toggle=1, icon_value=1, icon='FILEBROWSER')

    row = layout.row(align=True)
    row.prop(exporter_configs, 'export_nla_strips', toggle=1, icon_value=1, icon='NLA')

    row = layout.row(align=True)
    row.prop(exporter_configs, 'export_selected', toggle=1, icon='RESTRICT_SELECT_OFF')
    row.prop(exporter_configs, 'export_collection', toggle=1, icon='OUTLINER_COLLECTION')


    return

def register():
    pass

def unregister():
    pass