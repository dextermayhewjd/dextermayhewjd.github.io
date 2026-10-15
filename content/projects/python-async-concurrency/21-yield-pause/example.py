def resource_steps():
    print("before yield")
    yield "sandbox"
    print("after yield")


def main():
    steps = resource_steps()
    print("generator created")
    value = next(steps)
    print("value", value)
    print("back in caller")


if __name__ == "__main__":
    main()
