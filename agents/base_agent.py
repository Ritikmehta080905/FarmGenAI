class BaseAgent:
    def __init__(self, name):
        self.name = name

    def respond(self, *args, **kwargs):
        raise NotImplementedError("Subclasses must implement respond method")
