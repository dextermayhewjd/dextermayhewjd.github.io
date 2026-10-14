def main():
    with open("message.txt", encoding="utf-8") as file:
        text = file.read()
        print("content", text)
        print("inside closed", file.closed)

    print("outside closed", file.closed)


if __name__ == "__main__":
    main()
