#!/usr/bin/python
# coding:utf-8
import os
import sys
import argparse
import chardet
import re


def parse_input():
    parser = argparse.ArgumentParser(description='js zh to en')
    group = parser.add_mutually_exclusive_group(required=True)
    parser.add_argument('target', type=str,
                        help='specify the target javascript file')
    group.add_argument('-e', '--extract', action='store_true', default=False,
                       help='extract all lines contains chinese word')
    group.add_argument('-r', '--replace', action='store_true', default=False,
                       help='replace lines in a translated file specifed by the option -f')
    parser.add_argument('-f', '--translate-file', type=str,
                        help='specify the transalte file')
    parser.add_argument('-s', '--silent', action='store_true', default=False,
                        help='silent the outputs')
    parser.add_argument('-o', '--output', type=str,
                        help='write the output by the option -e to the file rather than to stdout')
    parser.add_argument('-d', '--diff', action='store_true', default=False,
                        help='show diff (not supported now)')

    # no input means show me the help
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()

    arg = parser.parse_args()
    if arg.replace and (not arg.translate_file):
        parser.print_help()
        sys.exit()

    return arg


def get_file_encoding(file_path):
    """ detect the file encoding """
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
        return result['encoding']


def convert2utf8(str, encoding):
    pass


def backup_file(file_path):
    """ copy only work in windows, in Unix/Linux is cp """
    os.popen('copy ' + file_path + ' ' + file_path + '.bak')


def is_single_line_comments(line):
    """ single line comment start with '//' or start with '/*' and end with '*/' in a single line. """
    l = line.strip()
    if l.startswith('//'):
        return True
    elif l.startswith('/*') and l.endswith('*/'):
        return True
    return False


def is_multi_line_comments_start(line):
    """ multi-line comments start with '/*' """
    return line.lstrip().startswith('/*')


def is_multi_line_comments_end(line):
    """ multi-line comments end with '*/' """
    return line.rstrip().endswith('*/')


def is_line_contains_comments(line):
    return any(['//' in line, '/*' in line, '*/' in line])


def remove_comments_in_line(line):
    if '//' in line:
        return line[:line.find('//')]
    if '/*' in line:
        return line[:line.find('/*')]
    return line


def str_has_cn(str):
    return re.search(r'[\u4e00-\u9fff]+', str)


def extract_zh_lines(file_path):
    cn_lines = {}

    with open(file_path, 'r', encoding=get_file_encoding(file_path)) as f:
        lines = f.readlines()

    is_multi_line_comments = False
    for index, line in enumerate(lines):
        line_ori = line

        # skip the comment lines
        if is_single_line_comments(line):
            continue
        if is_multi_line_comments_start(line):
            is_multi_line_comments = True
            continue
        if is_multi_line_comments and is_multi_line_comments_end(line):
            is_multi_line_comments = False
            continue
        if is_multi_line_comments:
            continue

        if is_line_contains_comments(line):
            line = remove_comments_in_line(line)
        if str_has_cn(line):
            cn_lines[index] = line_ori
    return cn_lines


def test():
    line = '   var a = 1; '
    assert is_single_line_comments(line) == False
    assert is_multi_line_comments_start(line) == False
    assert is_multi_line_comments_end(line) == False
    assert is_line_contains_comments(line) == False

    line = '   // var a = 1; '
    assert is_single_line_comments(line) == True
    assert is_multi_line_comments_start(line) == False
    assert is_multi_line_comments_end(line) == False
    assert is_line_contains_comments(line) == True

    line = '   /* var a = 1; */  '
    assert is_single_line_comments(line) == True
    assert is_multi_line_comments_start(line) == True
    assert is_multi_line_comments_end(line) == True
    assert is_line_contains_comments(line) == True

    line = '   var a = 1; /* comments */  '
    assert is_single_line_comments(line) == False
    assert is_multi_line_comments_start(line) == False
    assert is_multi_line_comments_end(line) == True
    assert is_line_contains_comments(line) == True
    assert remove_comments_in_line(line) == '   var a = 1; '

    line = '   var a = 1; // comments     '
    assert is_single_line_comments(line) == False
    assert is_multi_line_comments_start(line) == False
    assert is_multi_line_comments_end(line) == False
    assert is_line_contains_comments(line) == True
    assert remove_comments_in_line(line) == '   var a = 1; '

    line = '   /* multi line comments start     '
    assert is_single_line_comments(line) == False
    assert is_multi_line_comments_start(line) == True
    assert is_multi_line_comments_end(line) == False
    assert is_line_contains_comments(line) == True

    line = '   */ '
    assert is_single_line_comments(line) == False
    assert is_multi_line_comments_start(line) == False
    assert is_multi_line_comments_end(line) == True
    assert is_line_contains_comments(line) == True


def do_extract(target, output, silent=False):
    cn_lines_map = extract_zh_lines(arg.target)
    lines = []
    for k in cn_lines_map.keys():
        if not silent:
            print('line %s : %s' % (k, cn_lines_map[k]))
        lines.append(str(k) + ',' + cn_lines_map[k].strip() + '\n')
    if output:
        with open(output, 'w', encoding='utf-8') as f:
            f.writelines(lines)


def do_replace(target, translate_file, silent=False):
    backup_file(target)
    encoding_ori = get_file_encoding(target)
    with open(target, 'r', encoding=encoding_ori) as f:
        source_lines = f.readlines()
    with open(translate_file, 'r', encoding=get_file_encoding(translate_file)) as f:
        translate_lines = f.readlines()

    for l in translate_lines:
        line_number = int(l.split(',')[0].strip())
        line_translate = l.split(',', 1)[1].strip()
        if not silent:
            print("line %d : %s" % (line_number, line_translate))

        # get the indent of original line
        line_ori = source_lines[line_number]
        line_ori_s = line_ori.lstrip()
        indent = len(line_ori) - len(line_ori_s)

        source_lines[line_number] = ''.ljust(
            indent, ' ') + line_translate + '\n'

    with open(target, 'w+', encoding=encoding_ori) as f:
        f.writelines(source_lines)


def run(arg):
    if not os.path.exists(arg.target):
        print('file %s not exist' % (arg.target))
        return

    test()
    if arg.extract:
        do_extract(arg.target, arg.output, arg.silent)
    if arg.replace:
        do_replace(arg.target, arg.translate_file, arg.silent)


if __name__ == '__main__':
    arg = parse_input()
    run(arg)
