#!/usr/bin/env python3

import sys
import json
from instructions import *

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def main():
    adresses = len(sys.argv) == 3
    lines = list()
    with open(sys.argv[1]) as f:
        for line in f:
            address, instruction = line.split(':')
            if adresses:
                line = {'opcodes': list(chunks(instruction.strip(), 2)), 'address': int(address, base=16), 'text': str(get_instruction(int(instruction, base=16)))}
            else:
                line = {'text': str(get_instruction(int(instruction, base=16)))}
            lines.append(json.dumps(line))
    print('[{}]'.format(','.join(lines)))

if __name__ == '__main__':
    main()
