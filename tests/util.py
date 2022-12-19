class OutputInspector:
    def __init__(self):
        self.output = []

    def say(self, text):
        self.output.append(text)

    def reset(self):
        self.output.clear()
