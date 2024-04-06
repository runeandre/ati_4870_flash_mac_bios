#!/usr/bin/python

class RawData:
  data = []
  def __init__(self, data, offset=0):
    """
    simply copies data
    """
    self.data = data[:]

  def __repr__(self):
    """
    represents the data as a string
    """
    return "RawData (size=%d)" % len(self.data)

  def dump(self):
    """
    simple passthrough
    """
    return ''.join(self.data)

  def fix(self):
    """
    do nothing
    """
    pass


class OpRom:
  data = []
  indicator_offset = 0
  next_rom = None

  def __init__(self, data, offset=0):
    """
    splits the data stream in a chained list of OpRom objects
    """
    if ord(data[0]) != 0x55 or ord(data[1]) != 0xaa:
      raise TypeError("OpRom at %d is not valid" % offset)

    rom_len = ord(data[2]) * 512
    if len(data) < rom_len:
      raise TypeError("OpRom at %d is too short" % offset)

    self.data = list(data[:rom_len])
    self.indicator_offset = ord(data[0x18]) + ord(data[0x19]) * 256 + 0x15

    if len(data) > rom_len:
      try:
        self.next_rom = OpRom(data[rom_len:], offset + rom_len)
      except TypeError:
        self.next_rom = RawData(data[rom_len:], offset + rom_len)

  def __repr__(self):
    """
    represents the OpRom list as a string
    """
    rom_repr = "OpRom (size=%d, indicator_offset=0x%x, "\
        "indicator=0x%x, checksum=0x%x)"\
        % (len(self.data), self.indicator_offset,
        ord(self.data[self.indicator_offset]), ord(self.data[-1]))
    if self.next_rom is not None:
      rom_repr = '\n'.join([rom_repr, repr(self.next_rom)])
    return rom_repr

  def dump(self):
    """
    dumps the list of OpRom objects
    """
    if self.next_rom is not None:
      return ''.join(self.data) + self.next_rom.dump()
    return ''.join(self.data)

  def fix(self):
    """
    fixes the last_rom_indicator and the checksum
    """
    # last_rom_indicator
    indicator = ord(self.data[self.indicator_offset])
    if self.next_rom is not None and isinstance(self.next_rom, OpRom):
      indicator &= 0x7F # force msb to 0
    else:
      indicator |= 0x80 # force msb to 1
    self.data[self.indicator_offset] = chr(indicator)
    # checksum
    sum = 0
    for i in self.data[:-1]:
      sum = (sum + ord(i)) % 0x100
    self.data[-1] = chr(0x100 - sum)

    if self.next_rom is not None:
      self.next_rom.fix()


if __name__ == "__main__":
  import sys

  if len(sys.argv) != 3:
    print "Usage: %s <infile> <outfile>\n" % sys.argv[0]
    sys.exit(1)

  f=file(sys.argv[1])
  op_rom = OpRom(f.read())
  f.close()

  print "Before:"
  print op_rom

  op_rom.fix()

  print "\nAfter:"
  print op_rom

  f=file(sys.argv[2], "w")
  f.write(op_rom.dump())
  f.close()
