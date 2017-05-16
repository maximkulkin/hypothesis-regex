import six.moves
import string
import sre_parse as sre
import hypothesis.strategies as hs
from hypothesis.searchstrategy.reprwrapper import ReprWrapperStrategy

__all__ = ['regex']


_CATEGORIES = {
    sre.CATEGORY_DIGIT: string.digits,
    sre.CATEGORY_NOT_DIGIT: string.ascii_letters + string.punctuation,
    sre.CATEGORY_SPACE: string.whitespace,
    sre.CATEGORY_NOT_SPACE: string.printable.strip(),
    sre.CATEGORY_WORD: string.ascii_letters + string.digits + '_',
    sre.CATEGORY_NOT_WORD: ''.join(
        set(string.printable).difference(
            string.ascii_letters + string.digits + '_'
        )
    )
}


@hs.defines_strategy
def regex(regex):
    """Return strategy that generates strings that match given regex."""
    if hasattr(regex, 'pattern'):
        regex = regex.pattern

    codes = sre.parse(regex)

    return ReprWrapperStrategy(_strategy(codes, {}), 'regex(%s)' % repr(regex))


def _strategy(codes, cache):
    if not isinstance(codes, tuple):
        return hs.tuples(*[_strategy(x, cache) for x in codes]).map(''.join)
    else:
        code, value = codes
        if code == sre.LITERAL:
            return hs.just(chr(value))
        elif code == sre.NOT_LITERAL:
            return hs.characters(blacklist_characters=[chr(value)])
        elif code == sre.IN:
            charsets = value

            chars = []
            for charset_code, charset_value in charsets:
                if charset_code == sre.NEGATE:
                    pass
                elif charset_code == sre.LITERAL:
                    chars.append(chr(charset_value))
                elif charset_code == sre.RANGE:
                    low, high = charset_value
                    chars.extend([
                        chr(x) for x in six.moves.range(low, high+1)
                    ])
                elif charset_code == sre.CATEGORY:
                    if charset_value not in _CATEGORIES:
                        raise NotImplementedError(
                            'Unknown char category: %s' % charset_value
                        )
                    chars.extend(_CATEGORIES[charset_value])
                else:
                    raise NotImplementedError(
                        'Unknown charset code: %s' % charset_code
                    )

            if charsets[0][0] == sre.NEGATE:
                return hs.characters(blacklist_characters=chars)
            else:
                return hs.text(alphabet=chars, min_size=1, max_size=1)

        elif code == sre.ANY:
            # TODO: consider checking MULTILINE flag
            return hs.characters(blacklist_characters="\n")
        elif code == sre.AT:
            return hs.just('')
        elif code == sre.SUBPATTERN:
            strat = hs.tuples(*[_strategy(part, cache)
                                for part in value[-1]]).map(''.join)
            if value[0]:
                cache[value[0]] = strat
                strat = hs.shared(strat, key=value[0])
            return strat
        elif code == sre.GROUPREF:
            return hs.shared(cache[value], key=value)
        elif code == sre.ASSERT:
            return _strategy(value[1], cache)
        elif code == sre.ASSERT_NOT:
            return hs.just('')
        elif code == sre.BRANCH:
            return hs.one_of([_strategy(branch, cache) for branch in value[1]])
        elif code in [sre.MIN_REPEAT, sre.MAX_REPEAT]:
            at_least, at_most, regex = value
            if at_most == 4294967295:
                at_most = None
            return hs.lists(_strategy(regex, cache),
                            min_size=at_least,
                            max_size=at_most).map(''.join)
        else:
            raise NotImplementedError('Unknown code point: %s' % repr(code))
