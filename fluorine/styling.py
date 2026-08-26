class Style:
    def __init__(self, **styles: str) -> None:
        self.styles: dict[str, str] = styles
    def __str__(self) -> str:
        return "; ".join(f"{key.replace('_', '-')}: {('rgb' + str(value)) if isinstance(value, tuple) and len(value) == 3 else value}" for key, value in self.styles.items()) + ";"