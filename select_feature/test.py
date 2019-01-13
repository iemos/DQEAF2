class Parent:
    def f(self, a):
        print("aaaa")


class Child(Parent):
    def f(self):
        print("bbb")

x = Child()
x.f()
