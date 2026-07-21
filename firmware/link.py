"""Serial link abstraction — host MemoryLink + device StdioLink."""

from defaults import SERIAL_IN_BUDGET, SERIAL_LINE_MAX


class MemoryLink:
    """Host-test double: feed bytes in, collect lines out."""

    def __init__(self):
        self._in = bytearray()
        self.out = []
        self.closed = False

    def feed(self, data):
        if isinstance(data, str):
            data = data.encode("utf-8")
        self._in.extend(data)

    def feed_line(self, line):
        self.feed(line if line.endswith("\n") else (line + "\n"))

    def read_budget(self, n=None):
        if n is None:
            n = SERIAL_IN_BUDGET
        n = int(n)
        if n <= 0 or not self._in:
            return b""
        take = bytes(self._in[:n])
        del self._in[:n]
        return take

    def write_line(self, line):
        s = str(line)
        if len(s) > 200:
            s = s[:200]
        self.out.append(s)

    def close(self):
        self.closed = True


class LineAssembler:
    """Byte-budgeted line assembly; poison-to-newline discard."""

    def __init__(self, line_max=None):
        self.buf = bytearray()
        self.line_max = int(line_max if line_max is not None else SERIAL_LINE_MAX)
        self.poison = False

    def push(self, chunk):
        """Return list of decoded lines (without newline). None marks poison."""
        lines = []
        if not chunk:
            return lines
        for b in chunk:
            if b in (10, 13):  # \n \r
                if self.poison:
                    lines.append(None)
                    self.poison = False
                    self.buf = bytearray()
                    continue
                if self.buf:
                    try:
                        lines.append(self.buf.decode("utf-8"))
                    except Exception:
                        lines.append(None)
                    self.buf = bytearray()
                continue
            if self.poison:
                continue
            if len(self.buf) >= self.line_max:
                self.poison = True
                self.buf = bytearray()
                continue
            self.buf.append(b)
        return lines


def make_stdio_link():
    """Device-side nonblocking stdin/stdout. None if unavailable."""
    try:
        import sys
        import uselect
    except ImportError:
        return None

    # Ctrl-C is data on the product link (spec §6); restore on repl exit.
    try:
        import micropython

        micropython.kbd_intr(-1)
    except Exception:
        pass

    poll = uselect.poll()
    stream = getattr(sys.stdin, "buffer", sys.stdin)
    try:
        poll.register(stream, uselect.POLLIN)
    except Exception:
        try:
            poll.register(sys.stdin, uselect.POLLIN)
            stream = sys.stdin
        except Exception:
            return None

    class StdioLink:
        def read_budget(self, n=None):
            if n is None:
                n = SERIAL_IN_BUDGET
            n = int(n)
            if n <= 0:
                return b""
            out = bytearray()
            try:
                ready = poll.poll(0)
            except Exception:
                ready = True  # try a nonblocking read anyway
            if not ready:
                return b""
            for _ in range(n):
                try:
                    # Prefer 1-byte reads so we never block on a full line
                    ch = stream.read(1)
                except Exception:
                    break
                if not ch:
                    break
                if isinstance(ch, str):
                    if ch == "":
                        break
                    out.extend(ch.encode("utf-8"))
                elif isinstance(ch, (bytes, bytearray)):
                    if len(ch) == 0:
                        break
                    out.extend(ch)
                else:
                    out.append(int(ch) & 0xFF)
                # stop early if poll goes dry (when supported)
                try:
                    if not poll.poll(0):
                        break
                except Exception:
                    pass
            return bytes(out)

        def write_line(self, line):
            try:
                sys.stdout.write(str(line) + "\n")
                try:
                    sys.stdout.flush()
                except Exception:
                    pass
            except Exception:
                pass

    return StdioLink()
