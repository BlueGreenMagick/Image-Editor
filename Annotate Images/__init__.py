from anki import version

assert version.startswith("2.1.")
minor_ver = int(version.split(".")[-1])

COMPAT = {
    # backend.find_and_replace
    "find_replace": minor_ver >= 27,
    # media.write_data()
    "write_data": minor_ver >= 22,
    # find_and_replace returns OpChangesWithCount
    "find_replace_cnt": minor_ver >= 45
    
}



from . import editor
