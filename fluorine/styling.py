class Style:
    def __init__(self, **styles):
        self.styles = dict(styles)

    def __str__(self):
        return '; '.join(f'{k.replace("_", "-")}: {"rgb" + str(v) if isinstance(v, tuple) and len(v) == 3 else v}' for k, v in self.styles.items()) + (';' if self.styles else '')


class _Look:
    """Style modifier: element @ look(color='red') or @ look.color('red')."""
    def __call__(self, **styles):
        return Style(**styles)

    def __getattr__(self, name):
        return lambda value: Style(**{name: value})


look = _Look()
