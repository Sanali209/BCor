class Greeter:
    def __init__(self, default_name: str, style: str):
        self.default_name = default_name
        self.style = style

    def generate_greeting(self, name: str | None) -> str:
        target = name.strip() if name and name.strip() else self.default_name
        if self.style == "enthusiastic":
            return f"HELLO, {target.upper()}!!! Welcome to BCor!"
        elif self.style == "formal":
            return f"Greetings, {target}. It is a pleasure to meet you."
        else:
            return f"Hello, {target}."
