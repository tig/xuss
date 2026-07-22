"""ASCII line protocol (spec §6–§7).

Commands: identity, get, set, save, defaults, repl, reboot,
          sing, run, route, rpm, stop.
Telemetry: key=value fields, space-separated lines.
Ctrl-C is data (not a soft break for this parser).
"""

from config import PARAM_KEYS
from edge import get_profile, profile_names
from version import FW_NAME, FW_VERSION


class Protocol:
    def __init__(self, app):
        """app provides handlers and state accessors."""
        self.app = app
        self._rx = ""

    def feed(self, data, out_budget):
        """Feed raw bytes/str; return list of response strings (each without \\n).

        Poison-to-newline: on oversized line, discard to newline and error once.
        """
        if not data:
            return []
        if isinstance(data, bytes):
            try:
                data = data.decode("utf-8", "replace")
            except Exception:
                data = str(data)
        # Ctrl-C is data
        self._rx += data
        responses = []
        while True:
            nl = self._rx.find("\n")
            if nl < 0:
                # Cap pending line length (poison)
                if len(self._rx) > 200:
                    self._rx = ""
                    responses.append(self._cap_err("err=line_too_long", out_budget))
                break
            line = self._rx[:nl].rstrip("\r")
            self._rx = self._rx[nl + 1 :]
            if not line.strip():
                continue
            resp = self.handle_line(line.strip())
            if resp is not None:
                responses.append(self._cap_err(resp, out_budget))
        return responses

    def _cap_err(self, s, budget):
        if budget is None or budget <= 0:
            return s
        if len(s) > budget:
            return s[: max(0, budget - 1)]
        return s

    def handle_line(self, line):
        parts = line.split()
        if not parts:
            return None
        cmd = parts[0].lower()
        args = parts[1:]

        if cmd == "identity":
            return "fw_name=%s fw_version=%s" % (FW_NAME, FW_VERSION)

        if cmd == "get":
            if not args:
                # dump all
                fields = []
                for k, v in self.app.config.all_items():
                    fields.append("%s=%s" % (k, v))
                return " ".join(fields)
            key = args[0]
            if key not in PARAM_KEYS:
                return "err=unknown_param key=%s" % key
            return "%s=%s" % (key, self.app.config.get(key))

        if cmd == "set":
            if len(args) < 2:
                return "err=usage set=<key> <value>"
            key = args[0]
            value = args[1]
            ok, norm = self.app.config.set(key, value)
            if not ok:
                return "err=set key=%s why=%s" % (key, norm)
            # Live apply side effects for engine-driving params
            self.app.on_param_set(key, norm)
            return "ok %s=%s" % (key, norm)

        if cmd == "save":
            img = self.app.config.save()
            return "ok save cs_len=%d" % len(img)

        if cmd == "defaults":
            self.app.config.defaults()
            self.app.on_defaults()
            return "ok defaults"

        if cmd == "repl":
            self.app.request_repl()
            return "ok repl"

        if cmd == "reboot":
            self.app.request_reboot()
            return "ok reboot"

        if cmd == "sing":
            if not args:
                return "err=usage sing=<profile>"
            return self.app.start_profile(args[0], route_force="voice")

        if cmd == "run":
            if not args:
                return "err=usage run=<profile>"
            return self.app.start_profile(args[0], route_force="tach")

        if cmd == "route":
            if not args:
                return "route=%s" % self.app.config.get("route")
            ok, norm = self.app.config.set("route", args[0])
            if not ok:
                return "err=set key=route why=%s" % norm
            self.app.on_param_set("route", norm)
            return "ok route=%s" % norm

        if cmd == "rpm":
            if not args:
                return "rpm=%s" % self.app.config.get("rpm")
            ok, norm = self.app.config.set("rpm", args[0])
            if not ok:
                return "err=set key=rpm why=%s" % norm
            self.app.stop_profile()
            self.app.on_param_set("rpm", norm)
            return "ok rpm=%s" % norm

        if cmd == "stop":
            self.app.stop_all()
            return "ok stop"

        if cmd == "profiles":
            return "profiles=%s" % ",".join(profile_names())

        if cmd == "help":
            return (
                "cmds=identity,get,set,save,defaults,repl,reboot,"
                "sing,run,route,rpm,stop,profiles,help"
            )

        return "err=unknown_cmd cmd=%s" % cmd


def identity_line():
    return "fw_name=%s fw_version=%s" % (FW_NAME, FW_VERSION)
