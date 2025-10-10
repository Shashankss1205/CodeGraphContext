class A:
    def greet(self):
        return "A's greeting"

class B(A):
    def greet(self):
        return super().greet()
