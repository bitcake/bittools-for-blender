keyconfig_data = \
[]


if __name__ == "__main__":
    import os
    from bl_keymap_utils.io import keyconfig_import_from_data
    keyconfig_import_from_data(os.path.splitext(os.path.basename(__file__))[0], keyconfig_data)
