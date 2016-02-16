from re import *
from setting import fixup_line

class Output:
    def __init__(s):
        s.output_string = ""
        s.noformat_depth = 0
        s.end_is_noformat = False
        s.konsole = False
        s.noformat_indent = False
        s.media_file = []

    def output (s, line):
        # handling of inline code tag
        if s.end_is_noformat:
            if len(line) > 0 and line[0] == ' ':
                line = line.lstrip(' ')
                line = '\n\n' + line
        s.output_string += line
        s.end_is_noformat = False

    def result(s):
        return s.output_string

    def noformat_start(s, line, by_indent = False):
        if by_indent:
            s.noformat_indent = True
        if s.noformat_depth == 0:
            # strip space remaining from tags within a line
            s.output_string = s.output_string.rstrip(' ')
            if len(s.output_string) > 0 and s.output_string[-1] != '\n':
                s.output_string += '\n'
            s.output_string += '{noformat}'
            if line[0] != '\n':
                s.output_string += '\n'
        s.noformat_depth += 1

    def noformat_end(s, line):
        s.noformat_depth -= 1
        if s.noformat_depth == 0:
            if line[-1] != '\n':
                s.output_string += '\n'
            s.output_string += '{noformat}'
        s.end_is_noformat = True
        s.noformat_indent = False
    def is_noformat(s):
        return s.noformat_depth > 0

    def toggle_konsole(s):
        s.konsole = not s.konsole

    def is_konsole(s):
        return s.konsole

    def is_noformat_indent(s):
        return s.noformat_indent

    def add_media(s, media):
        s.media_file.append(media)

    def get_media_file(s):
        return s.media_file

class Block:
    def __init__ (s, part):
        s.index = 0
        s.array = []
        line = ""
        newline_re = compile('\n')
        for char in part:
            line += char
            if char == '\n':
                s.array.append(line)
                line = ""
        if line != "":
            s.array.append(line)
    def __iter__(s):
        return s
    def __next__(s):
        if s.index < len(s.array):
            line = s.array[s.index]
            s.index += 1
            return line
        else:
            raise StopIteration

def segment_conversion(segment, output):
    """Conversion that occurs on parts of a line."""

    ## no formatting
    nowiki_segment = segment.split('%%')

    ## links
    # URL to other page
    segment = sub('\[\[(.*?)\]\]', handle_url , segment)

    # image
    segment = sub('{{(.*)}}', lambda m: handle_link(m, image, output) , segment)

    ## basic formatting
    segment = sub(r'\*\*(.*?)\*\*', '*\g<1>*', segment) # bold
    segment = sub('__(.*?)__', '+\g<1>+', segment) # underline
    segment = sub('//(.*?)//', '_\g<1>_', segment) # italic
    segment = process_monospace(segment)
    segment = sub('<del>(.*?)</del>', '-\g<1>-', segment) # deleted
    segment = sub('<sub>(.*?)</sub>', '~\g<1>~', segment) # subscript
    segment = sub('<sup>(.*?)</sup>', '^\g<1>^', segment) # supscript

    ## text conversion
    # text to image
    # the followings don't exist on Confluence: 8-) 8-O =) :-/ :-\
    # :-? :-O :-X :-| ^_^ :?: :!: LOL FIXME DELETEME

    segment = sub(':-\(', ':(', segment)
    segment = sub(':-\)', ':)', segment)

    segment = sub(':-D', ':D', segment)
    segment = sub(':-P', ':p', segment)
    segment = sub(';-\)', ';)', segment)

    # text to HTML (to unicode for Confluence)
    text_to_html = [[ '<->', '↔'], # before -> or it won't work
                    [ '->' , '→'],
                    [ '<-' , '←'],
                    [ '<=>' , '⇔'], # before => same reason
                    [ '=>' , '⇒'],
                    [ '<=' , '⇐'],
                    [ '<<' , '«'],
                    [ '--' , '–'],
                    [ '---' , '—'],
                    [ '\(c\)' , '©'],
                    [ '\(tm\)' , '™'],
                    [ '\(r\)' , '®'],
                    [ '\.\.\.' , '…']]
    for pair in text_to_html:
        segment = sub(pair[0], pair[1], segment)

    # protect quote mark at the beginning of a line
    m = match('(^>+)(.*)', segment)
    if m and segment[-1] == '\n':
        segment = m.group(1) + sub('>>', '»', m.group(2))
    else:
        segment = sub('>>', '»', segment)

    # No formatting
    if len(nowiki_segment) > 2:
        new_segment = segment.split('%%')
        # put back unformatted chunk of text that were saved at the beginning
        for index in range (1, len(nowiki_segment), 2):
            new_segment[index] = nowiki_segment[index]
        segment = ''.join(new_segment)

    return segment

def konsole_line_by_line (line, output):
    """Handle konsole plugin: https://www.dokuwiki.org/plugin:konsole"""
    if output.is_konsole():
        if match('</konsole>', line):
            output.toggle_konsole()
            output.noformat_end(line)
            line = '\n'
        else:
            # remove basic formatting
            line = sub(r'\*\*(.*?)\*\*', '\g<1>', line) # bold
            line = sub('__(.*?)__', '\g<1>', line) # underline
            line = sub('//(.*?)//', '\g<1>', line) # italic
            line = sub("''(.*?)''", '\g<1>', line) # monospace
    elif match('<konsole.*>', line):
        m = match('<konsole.*?>(.*)', line)
        if output.is_noformat():
            output.noformat_end(line)
        output.toggle_konsole()
        output.noformat_start(line)
        if m.group(1).strip() == '':
            line = ''
        else:
            line = m.group(1) + '\n'
    return line

def noformat_line_by_line (line, output):
    """Line by line handling of noformat."""
    if match ('^  ', line):
        if output.is_noformat_indent():
            return line.lstrip(' ')
        # check that we are not in a list
        elif not match(r'^  +(\*|\-).*', line):
            output.noformat_start(line, True)
            return line.lstrip(' ')
    elif output.is_noformat_indent():
        output.noformat_end(line)
        output.output('\n')
    line = conversion_line_by_line(line)
    return line

def shield_monospace (match):
    """Shield hyphen and star within monospace"""
    part = match.group(1)
    part = sub(r'\*', '\*', part)
    part = sub('-', '\-', part)
    return '{{' + part + '}}'

def process_monospace (line):
    return sub("''(.*?)''", shield_monospace, line)

def line_fixup (content):
    """Fix border line cases"""
    output = ""

    for line in content.split('\n'):
        try:
            if fixup_line[line]:
                output += fixup_line[line]
            else:
                output += line
        except KeyError:
            output += line
        output += '\n'
    return output

def conversion_line_by_line (line):
    """Line by line conversion."""

    # shield all of the {} single instances. Confluence treats them as macro
    line = sub('([^\{])\{([^\{])', '\g<1>\{\g<2>', line)
    line = sub('([^\}])\}([^\}])', '\g<1>\}\g<2>', line)

    ## lists
    # ordered
    m = match(r'^(  +)\*(.*)', line)
    line = confluence_list(m, '*', line)

    # unordered
    m = match(r'^(  +)\-(.*)', line)
    line = confluence_list(m, '#', line)

    ## quoting
    # quoting is poorly supported on Confluence. Degrade to block
    # quote. Unfortunately nested quote won't work. It needs to be
    # handled before text to HTML because '>>' will be munged.
    line = sub('^>+ (.*)', 'bq. \g<1>', line)

    ## Smart quote
    line = sub('"(.*?)"', '“\g<1>”', line)

    ## tables
    # heading
    if len(line.split('^')) > 2:
        line = sub('\^', '||', line)
    # content
    if len(line.split('|')) > 2:
        # change front heading
        line = sub('^\^', '||', line)


    ## sectioning
    for level in range (6, 0, -1):
        re = '^\s*' + '=' * level + '([^=]*)'
        if level == 1:
            re += '='
        else:
            re += '==+'
        re += '\s*$'
        header = 'h' + str (7 - level) + '. '
        line = sub(re, lambda m: header + m.group(1).strip() + '\n' , line)

    return line

# type of verbatim_block
(verbatim_nowiki, verbatim_code, verbatim_file) = range (1,4)

def doku_to_confluence(doku_file):
    """Load the redmine wiki page in Doku format and converts it to
confluence markup. Returns content as a string."""
    o = Output()
    verbatim_start_re = compile('(<nowiki>|<(?:(file|code).*?)>)', flags = DOTALL | MULTILINE)
    verbatim_nowiki_end_re = compile('</nowiki>', flags = DOTALL | MULTILINE)
    verbatim_file_end_re = compile('</file>', flags = DOTALL | MULTILINE)
    verbatim_code_end_re = compile('</code>', flags = DOTALL | MULTILINE)

    if is_table_of_content (doku_file):
        o.output ('{toc}\n')

    with open (doku_file) as f:
        content = f.read()
        verbatim = False

        verbatim_position = 0
        verbatim_part = []
        verbatim_re = verbatim_start_re
        what = False
        while True:
            m = verbatim_re.search (content, verbatim_position)
            if m:
                span = m.span()
                part = content[verbatim_position:span[0]]
                verbatim_part.append([part, what])
                verbatim_position = span[1]
                if m.group(0)[0:2] == '</':
                    verbatim_re = verbatim_start_re
                    what = False
                elif m.group(0)[1:5] == 'code':
                    verbatim_re = verbatim_code_end_re
                    what = verbatim_code
                elif m.group(0)[1:5] == 'file':
                    verbatim_re = verbatim_file_end_re
                    what = verbatim_file
                elif m.group(0)[1:7] == 'nowiki':
                    verbatim_re = verbatim_nowiki_end_re
                    what = verbatim_nowiki
                else:
                    print (m.group(0) + " is not handled.")
                    exit(1)
            else:
                verbatim_part.append([content[verbatim_position:], what])
                break

        for (part, what) in verbatim_part:
            if what == verbatim_code or what == verbatim_file:
                o.noformat_start(part)
                o.output(part)
                o.noformat_end(part)
            elif what == verbatim_nowiki:
                if not o.is_konsole():
                    if part[0] == '\n':
                        part = part[1:]
                    if part[-1] == '\n':
                        part = part[:-1]
                o.output(part)
            else:
                for line in Block(part):
                    # remove next line characters
                    line = konsole_line_by_line(line, o)
                    if not o.is_konsole():
                        line = noformat_line_by_line(line, o)
                        line = segment_conversion(line, o)
                    o.output (line)

        content = line_fixup(o.result())
        return [content, o.get_media_file()]


def is_table_of_content(doku_file):
    """If you have more than three headlines, a table of contents is generated
    automatically - this can be disabled by including the string ~~NOTOC~~ in
    the document."""

    with open (doku_file) as f:
        section_count = 0
        notoc = False
        for line in f:
            # sectioning
            m = match('(=+) .* (=+)', line)
            if m:
                # check that equals are balanced
                if m.group(1) == m.group(2):
                    section_count += 1
            if match('~~NOTOC~~', line):
                notoc = True
    return (section_count > 3 and notoc == False)

def confluence_list (m, marker, line):
    if m:
        space_number = len(m.group(1))
        # check we have at least two spaces and that they are even
        if space_number >= 2 and space_number % 2 == 0:
            line = marker * (int (((space_number - 2) / 2)) + 1)
            line += m.group(2) + '\n'
    return line


(image, url) = range (0, 2)

def handle_url(m):
    return handle_link(m, url)

def remove_doku_markup (link, what):
    # do not mess http link
    if not match ('^https?:', link):
        link = sub ('.*:(.*)', '\g<1>', link)
    if what == image:
        # all the option after the question mark are not supported in
        # Confluence
        link = sub ('(.+?)\?.*', '\g<1>',  link)
    return link

def handle_link (m, what, output=False):
    if m:
        link = m.group(1)
        m = match('^(.+?)\|(.*)', link)
        if m:
            group1 = m.group(1).strip()
            group2 = m.group(2).strip()
            if group2 == '':
                link = remove_doku_markup(group1, what)
            else:
                link = group2 + '|' + remove_doku_markup(group1, what)
        else:
            link = remove_doku_markup(link, what)
        if what == image:
            output.add_media (link)
            return '!' + link + '!'
        elif what == url:
            return '[' + link + ']'

if __name__ == "__main__":
    from os import system
#    print (doku_to_confluence("foo.txt"))
#    exit(0)
    input_file = "doku-input.txt"
    output_file = "doku-output.txt"
    oracle_file = "expected-output.txt"
    fixup_line = {
        r'Copy {{\\foo\scripts\\*}} to the new machine':
        r'Copy {{\\foo\scripts\*}} to the new machine'
    }
    output = doku_to_confluence(input_file)

    assert output[1] == ['lingsrv.png', 'lvm_snapshot_part1.png']

    with open (output_file, 'w') as f:
        f.write(output[0])

    if system('diff -u ' + oracle_file + ' ' + output_file) != 0:
        print ("Test failed")
        exit(1)
    else:
        print ("Test passed")


# Local Variables:
# compile-command: "python3 doku.py"
# End:
