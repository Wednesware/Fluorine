class Site:
    def __init__(self, pages: list[Page]) -> None:
        self.pages: list[Page] = pages
    def __iter__(self):
        return iter(self.pages)

class Page:
    def __init__(self) -> None: