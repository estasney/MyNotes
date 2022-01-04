from toolz import curry, compose_left
import unicodedata


@curry
def str_replace(s, old, new):
    return s.replace(old, new)


@curry
def str_split(on, s):
    return s.split(on)


@curry
def str_join(sep, s):
    return sep.join(s)


space_replace = str_replace(new=" ")
str_drop = str_replace(new="")
to_title = lambda s: s.title()


nb_display_name = compose_left(space_replace(old="_"), str_drop(old=".html"), to_title)
_category_name = compose_left(space_replace(old="_"), to_title)


def category_name(s):
    if "+" not in s:
        return _category_name(s)
    cats = str_split("+", s)
    head, tail = cats[:-1], cats[-1]
    head_tail = [*head, f"and {tail}"]
    head_tail = str_join(", ", head_tail)
    return _category_name(head_tail)
