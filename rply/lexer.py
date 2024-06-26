from rply.errors import LexingError
from rply.token import SourcePosition, Token


class Lexer(object):
    def __init__(self, rules, ignore_rules):
        self.rules = rules
        self.ignore_rules = ignore_rules

    def lex(self, s):
        return LexerStream(self, s)


class LexerStream(object):
    def __init__(self, lexer, s):
        self.lexer = lexer
        self.s = s
        self.idx = 0

        self._lineno = 1
        self._colno = 1
        self._states = []

    def __iter__(self):
        return self

    def _update_pos(self, match):
        self.idx = match.end
        self._lineno += self.s.count("\n", match.start, match.end)
        last_nl = self.s.rfind("\n", 0, match.start)
        if last_nl < 0:
            return match.start + 1
        else:
            return match.start - last_nl

    def _state_check(self, rule):
        return not rule.state or (len(self._states) and rule.state is self._states[-1])

    def _update_states(self, rule):
        if rule.pop:
            self._states.pop()
        if rule.push:
            self._states.extend(rule.push)

    def next(self):
        while True:
            if self.idx >= len(self.s):
                raise StopIteration
            for rule in self.lexer.ignore_rules:
                if not self._state_check(rule):
                    continue
                match = rule.matches(self.s, self.idx)
                if match:
                    self._update_states(rule)
                    self._update_pos(match)
                    break
            else:
                break

        for rule in self.lexer.rules:
            if not self._state_check(rule):
                continue
            match = rule.matches(self.s, self.idx)
            if match:
                self._update_states(rule)
                lineno = self._lineno
                self._colno = self._update_pos(match)
                source_pos = SourcePosition(match.start, lineno, self._colno)
                token = Token(
                    rule.name, self.s[match.start:match.end], source_pos
                )
                return token
        else:
            raise LexingError(None, SourcePosition(
                self.idx, self._lineno, self._colno))

    def __next__(self):
        return self.next()
