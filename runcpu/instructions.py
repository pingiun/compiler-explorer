import sys


class Instruction(object):

    def __init__(self, condition):
        self.condition = condition

    def __str__(self):
        return 'NOP'

    def get_condition(self):
        return self.condition

    def execute(self, pc):
        pass


class Halt(Instruction):

    def __str__(self):
        if self.condition == 15:
            return 'HALT'
        return 'HALT.{}'.format(condition_by_name(self.condition))

    def execute(self, pc):
        pc.halt()


class Read(Instruction):

    def __init__(self, offset, reg_a, reg_d, condition):
        super(Read, self).__init__(condition)
        self.offset = sign_extend(offset, 10)
        self.reg_a = reg_a
        self.reg_d = reg_d

    def __str__(self):
        if self.condition == 15:
            base = 'READ'
        else:
            base = 'READ.{}'.format(condition_by_name(self.condition))

        if self.offset and self.reg_a:
            src = '[R{} + 0x{:x}]'.format(self.reg_a, 0xffffffff & self.offset)
        elif self.offset:
            src = '[0x{:x}]'.format(0xffffffff & self.offset)
        else:
            src = '[R{}]'.format(self.reg_a)
        return '{:<10}{}, R{}'.format(base, src, self.reg_d)

    def execute(self, pc):
        address = pc.get_reg(self.reg_a) + self.offset

        if address == -512:
            data = ord(sys.stdin.read(1))
        else:
            data = pc.read_memory(address)
        pc.set_reg(self.reg_d, data)


class Write(Instruction):

    def __init__(self, offset, reg_a, reg_b, condition):
        super(Write, self).__init__(condition)
        self.offset = sign_extend(offset, 10)
        self.reg_a = reg_a
        self.reg_b = reg_b

    def __str__(self):
        if self.condition == 15:
            base = 'WRITE'
        else:
            base = 'WRITE.{}'.format(condition_by_name(self.condition))

        if self.offset and self.reg_a:
            src = '[R{} + 0x{:x}]'.format(self.reg_a, 0xffffffff & self.offset)
        elif self.offset:
            src = '[0x{:x}]'.format(0xffffffff & self.offset)
        else:
            src = '[R{}]'.format(self.reg_a)
        return '{:<10}R{}, {}'.format(base, self.reg_b, src)

    def execute(self, pc):
        address = pc.get_reg(self.reg_a) + self.offset
        data = pc.get_reg(self.reg_b)

        if address == -512:
            if pc.is_verbose():
                print('\n[!] Output: {}\n'.format(chr(data)))
            else:
                sys.stdout.write(chr(data))
        else:
            pc.write_memory(address, data)


class Push(Instruction):

    def __init__(self, reg_a, condition):
        super(Push, self).__init__(condition)
        self.reg_a = reg_a

    def __str__(self):
        if self.condition == 15:
            base = 'PUSH'
        else:
            base = 'PUSH.{}'.format(condition_by_name(self.condition))

        return '{:<10}R{}'.format(base, self.reg_a)

    def execute(self, pc):
        data = pc.get_reg(self.reg_a)
        sp = pc.get_reg(14) - 4

        pc.write_memory(sp, data)
        pc.set_reg(14, sp)


class Pop(Instruction):

    def __init__(self, reg_d, condition):
        super(Pop, self).__init__(condition)
        self.reg_d = reg_d

    def __str__(self):
        if self.condition == 15:
            base = 'POP'
        else:
            base = 'POP.{}'.format(condition_by_name(self.condition))

        return '{:<10}R{}'.format(base, self.reg_d)

    def execute(self, pc):
        sp = pc.get_reg(14)
        data = pc.read_memory(sp)

        pc.set_reg(self.reg_d, data)
        pc.set_reg(14, sp + 4)


class LoadHi(Instruction):

    def __init__(self, constant, reg_d, condition):
        super(LoadHi, self).__init__(condition)
        self.constant = constant
        self.reg_d = reg_d

    def __str__(self):
        if self.condition == 15:
            base = 'LOADHI'
        else:
            base = 'LOADHI.{}'.format(condition_by_name(self.condition))

        return '{:<10}0x{:x}, R{}'.format(base, self.constant, self.reg_d)

    def execute(self, pc):
        data = self.constant << 10
        pc.set_reg(self.reg_d, data)


class Arith(Instruction):

    names = ('OR', 'XOR', 'AND', 'BIC', '???', 'ROL', 'ADD', 'SUB')

    def __init__(self, opc, flg, nc, constant, reg_a, reg_b, reg_d, condition):
        super(Arith, self).__init__(condition)
        self.opcode = opc
        self.flag = flg
        self.no_constant = nc
        self.constant = sign_extend(constant, 10)
        self.reg_a = reg_a
        self.reg_b = reg_b
        self.reg_d = reg_d

    def __str__(self):
        base = self.names[self.opcode]
        if self.flag:
            base += 'f'
        if self.condition != 15:
            base += '.' + condition_by_name(self.condition)

        if self.no_constant:
            src = 'R{}'.format(self.reg_a)
        else:
            src = '0x{:x}'.format(0xffffffff & self.constant)

        return '{:<10}{}, R{}, R{}'.format(base, src, self.reg_b, self.reg_d)

    def execute(self, pc):
        c, o = False, False

        if self.no_constant:
            op_a = pc.get_reg(self.reg_a)
        else:
            op_a = self.constant

        op_b = pc.get_reg(self.reg_b)

        if self.opcode == 0:
            result = op_a | op_b
        elif self.opcode == 1:
            result = op_a ^ op_b
        elif self.opcode == 2:
            result = op_a & op_b
        elif self.opcode == 3:
            result = op_a & ~op_b
        elif self.opcode == 5:
            rol = op_a & 0b11111
            overflow = (op_b >> (32-rol)) & ((1 << rol) - 1)
            result = ((op_b << rol) & (2**32 - 1)) + overflow

            c = bool(result & 1)
            o = (op_b >> 31) != (result >> 31)
        elif self.opcode == 7:
            neg = ~op_b
            tmp = op_a + neg + 1
            result = tmp & (2 ** 32 - 1)

            c = bool(tmp & 2**32)
            o = (op_a >> 31) == (neg >> 31) and (op_a >> 31) != (result >> 31)
        else:
            tmp = op_a + op_b
            result = tmp & (2 ** 32 - 1)

            c = bool(tmp & 2**32)
            o = (op_a >> 31) == (op_b >> 31) and (op_a >> 31) != (result >> 31)

        if self.flag:
            n = bool(result & (1 << 31))
            z = result == 0
            pc.set_flags(n, z, c, o)

        pc.set_reg(self.reg_d, result)


def get_instruction(machinecode):
    if not (machinecode & (1 << 31)):
        # Arithmetic instruction
        opc = (machinecode >> 28) & 0b111
        flg = (machinecode >> 27) & 0b1
        nc = (machinecode >> 26) & 0b1
        constant = (machinecode >> 16) & 0x3ff
        reg_a = (machinecode >> 12) & 0xf
        reg_b = (machinecode >> 8) & 0xf
        reg_d = (machinecode >> 4) & 0xf
        cond = machinecode & 0xf

        return Arith(opc, flg, nc, constant, reg_a, reg_b, reg_d, cond)

    elif not (machinecode & (1 << 30)):
        # LoadHi
        const = ((machinecode >> 8) & 0x2fffff)
        reg_d = (machinecode >> 4) & 0xf
        dest = machinecode & 0xf

        return LoadHi(const, reg_d, dest)

    elif (machinecode >> 26) & 0b1111 == 0:
        # Read
        offset = (machinecode >> 16) & 0x3ff
        reg_a = (machinecode >> 8) & 0xf
        reg_d = (machinecode >> 4) & 0xf
        cond = machinecode & 0xf

        return Read(offset, reg_a, reg_d, cond)

    elif (machinecode >> 26) & 0b1111 == 0b1000:
        # Write
        offset = (machinecode >> 16) & 0x3ff
        reg_a = (machinecode >> 8) & 0xf
        reg_b = (machinecode >> 12) & 0xf
        reg_d = (machinecode >> 4) & 0xf
        cond = machinecode & 0xf

        if reg_d == 14:
            return Push(reg_b, cond)
        else:
            return Write(offset, reg_a, reg_b, cond)

    elif (machinecode >> 26) & 0b1111 == 1:
        # Push
        reg_a = (machinecode >> 12) & 0xf
        cond = machinecode & 0xf

        return Push(reg_a, cond)

    elif (machinecode >> 26) & 0b1111 == 0b100:
        # Pop
        reg_d = (machinecode >> 4) & 0xf
        cond = machinecode & 0xf

        return Pop(reg_d, cond)

    else:
        # Halt
        cond = machinecode & 0xf
        return Halt(cond)


def condition_by_name(condition):
    return ('E', 'NE', 'GEU', 'LU', 'N', 'NN', 'O', 'NO',
            'GU', 'LEU', 'GE', 'L', 'G', 'LE', 'F', 'T')[condition]


def sign_extend(value, bits):
    sign_bit = 1 << (bits - 1)
    return (value & (sign_bit - 1)) - (value & sign_bit)
