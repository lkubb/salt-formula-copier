import copy
import textwrap
from collections.abc import Mapping, Sequence

import yaml
from jinja2.ext import Extension


def represent_str(dumper, data):
    """
    Represent multiline strings using "|"
    """
    if len(data.splitlines()) > 1:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


class OpinionatedYamlDumper(yaml.SafeDumper):
    """
    Indent lists by two spaces
    """

    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow=flow, indentless=False)


OpinionatedYamlDumper.add_representer(str, represent_str)


class YamlDumper(Extension):
    def __init__(self, environment):
        super().__init__(environment)
        environment.filters["yaml"] = dump_yaml


def dump_yaml(data, flow_style=False, indent=0, sort_keys=False):
    ret = yaml.dump(
        data,
        Dumper=OpinionatedYamlDumper,
        indent=indent,
        default_flow_style=flow_style,
        canonical=False,
        sort_keys=sort_keys,
    )
    if ret.endswith("...\n"):
        ret = ret[:-4]
    return ret.strip()


class RecursiveData(Extension):
    def __init__(self, environment):
        super().__init__(environment)
        environment.filters["merge"] = merge
        environment.filters["traverse"] = traverse
        environment.filters["flatten_dict"] = flatten_dict
        environment.filters["describes"] = describes
        environment.filters["yaml_with_descriptions"] = yaml_with_descriptions
        environment.filters["myst_with_descriptions"] = myst_with_descriptions


def merge(base, *dicts, merge_lists=False):
    """
    Merge two or more dictionaries recursively.
    Does not modify in-place.
    """
    res = copy.deepcopy(base)
    for single in dicts:
        update(res, copy.deepcopy(single), merge_lists=merge_lists)
    return res


def update(dest, upd, recursive_update=True, merge_lists=False):
    """
    Recursive version of the default dict.update.

    Adapted from salt.utils.dictupdate.update.
    """
    if any(not isinstance(data, Mapping) for data in (dest, upd)):
        raise TypeError("Cannot update using non-dict types")
    updkeys = list(upd)
    if not set(list(dest)) & set(updkeys):
        recursive_update = False
    if recursive_update:
        for key in updkeys:
            val = upd[key]
            try:
                dest_subkey = dest.get(key, None)
            except AttributeError:
                dest_subkey = None
            if all(isinstance(dval, Mapping) for dval in (dest_subkey, val)):
                ret = update(dest_subkey, val, merge_lists=merge_lists)
                dest[key] = ret
            elif isinstance(dest_subkey, list) and isinstance(val, list):
                if merge_lists:
                    merged = copy.deepcopy(dest_subkey)
                    merged.extend([x for x in val if x not in merged])
                    dest[key] = merged
                else:
                    dest[key] = upd[key]
            else:
                dest[key] = upd[key]
        return dest
    for k in upd:
        dest[k] = upd[k]
    return dest


def traverse(data, key, default=None, *, delimiter=":"):
    """
    Recursively traverse into nested dictionaries and lists.
    """
    ptr = data
    if isinstance(key, str):
        parts = key.split(delimiter)
    elif not isinstance(key, Sequence):
        parts = [key]
    else:
        parts = key

    for item in parts:
        if isinstance(ptr, Sequence):
            try:
                idx = int(item)
                ptr = ptr[idx]
            except (IndexError, TypeError, ValueError):
                return default
        else:
            try:
                ptr = ptr[each]
            except (KeyError, TypeError):
                return default
    return ptr


def flatten_dict(
    data,
    *,
    delimiter=":",
    ignore_keys=(),
    stop_at_keys=(),
    stop_at_parent=False,
    include_stop_key=True,
    include_intermediates=False,
    prefix=None,
):
    """
    Take in a (recursive) mapping and transform it into a 1D mapping.

    delimiter
        The string to include between distinct subdict keys. Defaults to a colon (``:``).

    ignore_keys
        A list of key names to ignore when flattening subdicts.

    stop_at_keys
        A list of key names to not flatten further.

    stop_at_parent
        Apply ``stop_at_keys`` to the parent of the key instead of the key itself.
        Defaults to false.

    include_stop_key
        When stopping flattening because a key is in ``stop_at_keys``, include its name in the flattened path.
        Defaults to true.

    include_intermediates
        Include intermediate paths (which are mappings themselves) in the return dict keys (the values are None).
        Defaults to false.
    """
    res = {}
    prefix = prefix or []
    if not isinstance(data, Mapping):
        raise TypeError("Cannot flatten non-dict")
    if isinstance(ignore_keys, str):
        ignore_keys = (ignore_keys,)
    if isinstance(stop_at_keys, str):
        stop_at_keys = (stop_at_keys,)
    for key, val in data.items():
        if key in ignore_keys:
            continue
        if (
            isinstance(val, Mapping)
            and (not stop_at_parent and key not in stop_at_keys)
            and not (stop_at_parent and any(child in stop_at_keys for child in val))
        ):
            if include_intermediates:
                res[delimiter.join(prefix + [key])] = None
            res.update(
                flatten_dict(
                    val,
                    prefix=[*prefix, key],
                    delimiter=delimiter,
                    ignore_keys=ignore_keys,
                    stop_at_keys=stop_at_keys,
                    stop_at_parent=stop_at_parent,
                    include_stop_key=include_stop_key,
                    include_intermediates=include_intermediates,
                )
            )
            continue
        if isinstance(val, (list, dict)):
            val = copy.deepcopy(val)
        res[
            delimiter.join(
                prefix + ([key] if include_stop_key or key not in stop_at_keys else [])
            )
        ] = val
    return res


def describes(
    descriptions, settings, *, delimiter=":", meta_key="_meta", get_superfluous=False
):
    """
    Check whether a ``descriptions`` mapping is a subset of a ``settings`` mapping.
    """
    flat_settings = set(
        flatten_dict(settings, include_intermediates=True, delimiter=delimiter)
    )
    flat_descriptions = set(
        flatten_dict(
            descriptions,
            stop_at_keys=(meta_key,),
            include_stop_key=False,
            delimiter=delimiter,
        )
    )
    if get_superfluous:
        superfluous = flat_descriptions.difference(flat_settings)
        return superfluous
    return flat_settings.issuperset(flat_descriptions)


def yaml_with_descriptions(
    settings,
    descriptions,
    *,
    delimiter=":",
    indent=2,
    extra_comment_indent=0,
    comment_width=70,
    prefix=None,
):
    """
    Renders ``pillar.example`` files.

    settings
        The formula configuration.

    descriptions
        A mapping of formula settings to doc configuration. Unlike the nested ``settings`` dict,
        keys must be flattened (``{foo: {bar: {baz: false}}}`` => ``{foo:bar:baz: {}}``).

        Respected mapping values:

        desc
            Basic description. Can be a multiline string.

        width
            Override the default ``comment_width`` for this setting only.

    delimiter
        Specify the delimiter for the flattened settings keys. Defaults to ``:``.

    indent
        Specify the number of spaces nested settings are indented with.
        Defaults to ``2``.

    extra_comment_indent
        Add extra indentation to rendered comments for a configuration value.
        Defaults to ``0``, which means descriptions are on the same level as their parameters.

    comment_width
        When a description is a single line only, this function ensures it is at most
        <comment_width> long, breaking it into multiple lines if necessary.
        This is not applied to multiline strings since they might have formatting
        that would be broken by this behavior.

    prefix
        A list/tuple of prefixes. For internal use (rendering nested configuration needs recursion).
    """
    prefix = prefix or []
    lines = []

    def add_lines(*new_lines, cur_prefix):
        lines.extend(" " * indent * len(cur_prefix) + line for line in new_lines)

    for key, val in settings.items():
        path = delimiter.join(prefix + [key])
        meta = {}
        if path in descriptions:
            meta = descriptions[path]
            if not isinstance(meta, Mapping):
                raise TypeError(f"Wrong meta description at '{path}'")
            if "desc" in meta:
                item_lines = meta["desc"].strip().splitlines()
                if len(item_lines) == 1:
                    item_lines = textwrap.wrap(
                        meta["desc"].strip(),
                        meta.get("width", comment_width),
                        break_long_words=False,
                        break_on_hyphens=False,
                    )
                add_lines(
                    *(extra_comment_indent * " " + f"# {line}" for line in item_lines),
                    cur_prefix=prefix,
                )

        if not isinstance(val, Mapping) or not val:
            add_lines(*dump_yaml({key: val}).splitlines(), cur_prefix=prefix)
            if (
                "example" in meta
                and not val
                and isinstance(val, (Mapping, Sequence))
                and not isinstance(val, str)
            ):
                example_yaml = dump_yaml(meta["example"]).splitlines()
                cur_prefix = prefix + [key]
                add_lines(
                    *(f"# {line}" for line in example_yaml),
                    cur_prefix=cur_prefix,
                )
        else:
            add_lines(f"{key}:", cur_prefix=prefix)
            lines.extend(
                yaml_with_descriptions(
                    val,
                    descriptions,
                    delimiter=delimiter,
                    prefix=prefix + [key],
                    indent=indent,
                    extra_comment_indent=extra_comment_indent,
                )
            )

    if prefix:
        return lines
    return "\n".join(lines)


def myst_with_descriptions(
    settings,
    descriptions,
    *,
    delimiter=":",
    config_role="conf",
    increase_heading=1,
    dlist_breakpoint=5,
    maxdepth=7,
    prefix=None,
):
    """
    Function that tries to auto-generate a configuration reference in MyST using
    the provided data. It's pretty hacky, but works for the moment.

    Probably should have been a Jinja template.

    settings
        The formula configuration.

    descriptions
        A mapping of formula settings to doc configuration. Unlike the nested ``settings`` dict,
        keys must be flattened (``{foo: {bar: {baz: false}}}`` => ``{foo:bar:baz: {}}``).

        Respected mapping values:

        myst
            Highest priority for defining the description.

        docs
            Alternative to ``myst``, might be read by a future ``rst_with_descriptions`` or similar as well.

        desc
            Basic description, which is also rendered into the example pillar by ``yaml_with_descriptions``.
            Used when both ``myst`` and ``docs`` are unspecified.

        dlist
            Render children of this configuration value as a definition list instead of their own headings.

        maxdepth
            Override the default ``maxdepth`` relative to this configuration value.
            Setting this to ``0`` means no children are rendered, ``1`` only direct children etc.

    delimiter
        Specify the delimiter for the flattened settings keys. Defaults to ``:``.

    config_role
        Specify the role individual settings are tagged with. Defaults to ``conf``.
        Set this to a falsy value to skip.

    increase_heading
        This function maps the depth of a setting value to a markdown header one. This value decides
        the header level of the base layer settings. Defaults to 1, which means the first level keys
        are mapped to a second-level heading (``## <conf>``).

    dlist_breakpoint
        Define the depth at which setting values do not receive their own heading, but are rather
        rendered as a definition list. Defaults to ``5``. Cannot be larger than ``7`` since MyST
        only supports headings up to 6 levels deep.

    maxdepth
        Render nested settings up to this maximum depth, drop everything below. Defaults to ``7``.

    prefix
        A list/tuple of prefixes. For internal use (rendering nested configuration needs recursion).
    """
    prefix = prefix or []
    ret = []
    # MyST only supports headings up to 6 levels deep
    dlist_breakpoint = min(dlist_breakpoint, 7)
    dlist_breakpoint = max(dlist_breakpoint, increase_heading + 1)

    for key, val in settings.items():
        path = delimiter.join(prefix + [key])
        lines = [""]
        # effectively the number of # in front of the heading
        depth = len(prefix) + 1 + increase_heading
        if depth > maxdepth:
            continue
        use_heading = depth < dlist_breakpoint
        indent = 0 if use_heading else (depth - dlist_breakpoint) * 4

        desc_lines = []
        meta = {}
        if path in descriptions:
            meta = descriptions[path]
            if not isinstance(meta, Mapping):
                raise TypeError(f"Wrong meta description at '{path}'")
            if "myst" in meta:
                desc_lines = meta["myst"].strip().splitlines()
            elif "docs" in meta:
                desc_lines = meta["docs"].strip().splitlines()
            elif "desc" in meta:
                desc_lines = meta["desc"].strip().splitlines()
            if len(desc_lines) == 1:
                desc_lines = textwrap.wrap(
                    desc_lines[0], 120, break_long_words=False, break_on_hyphens=False
                )
            if not desc_lines and val and not use_heading:
                # We need some content for the definition list
                desc_lines = ["(no description)"]
            if not use_heading and desc_lines:
                desc_lines = [(indent + 4) * " " + line for line in desc_lines]
                desc_lines[0] = (
                    desc_lines[0][:indent] + ":" + desc_lines[0][indent + 1 :]
                )

        if config_role and (use_heading or desc_lines or val):
            lines.extend(
                [indent * " " + f":::{{{config_role}}} {path}", indent * " " + ":::"]
            )
            lines.extend([indent * " " + f":::{{cssclass}} conf", indent * " " + ":::"])
        if use_heading:
            lines.append((len(prefix) + 1 + increase_heading) * "#" + f" `{key}`")
        elif desc_lines or val:
            lines.append(indent * " " + f"`{key}`")
        else:
            lines = []

        lines.extend(desc_lines)

        if val and isinstance(val, Mapping):
            dlist_bp_param = dlist_breakpoint
            maxdepth_param = maxdepth
            if meta.get("dlist"):
                dlist_bp_param = depth + 1
            if "maxdepth" in meta:
                maxdepth_param = depth + meta["maxdepth"]
            sub = myst_with_descriptions(
                val,
                descriptions,
                delimiter=delimiter,
                prefix=prefix + [key],
                config_role=config_role,
                increase_heading=increase_heading,
                dlist_breakpoint=dlist_bp_param,
                maxdepth=maxdepth_param,
            )
            if sub:
                lines.append(sub)
        ret += lines
    return "\n".join(ret)
