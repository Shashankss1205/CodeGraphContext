class A:
    def greet(self): pass

class B(A):
    def greet(self):
        super().greet()

class MCP:
    def greet(self): pass
