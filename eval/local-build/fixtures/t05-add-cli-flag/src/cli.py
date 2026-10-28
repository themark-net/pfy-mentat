import argparse


def build_parser():
    parser = argparse.ArgumentParser(prog="echoer")
    parser.add_argument("text")
    return parser


def main(argv):
    args = build_parser().parse_args(argv)
    return args.text
