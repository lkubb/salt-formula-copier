"""
Allows to link configuration values using :conf:`config:val`.
Allows to link states using :state:`state.id`.
"""


def setup(app):
    app.add_crossref_type(
        directivename="conf",
        rolename="conf",
        indextemplate="single: configuration; %s",
    )
    app.add_crossref_type(
        directivename="state",
        rolename="state",
        indextemplate="single: state; %s",
    )
    return {"parallel_read_safe": True, "parallel_write_safe": True}
