import argparse
from bluffinmuffin.AIClient import AIClient


def main():
    args = parse_arguments()
    client = AIClient(args.ai_type, args.server, args.port)
    client.identify()
    client.find_table()
    client.play()


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("server")
    parser.add_argument("port", type=int)
    parser.add_argument("-a", "--ai_type", choices=['Random', 'Raiser', 'Caller'], default="Random")

    return parser.parse_args()

if __name__ == "__main__":
    main()
