def decorate(func):
    print("decorator received function")
    return func


@decorate
def greet():
    print("greet called")


def main():
    saved = greet
    print("function saved")
    saved()


if __name__ == "__main__":
    main()
