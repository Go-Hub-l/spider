import re

title = 'fgadfadsga;afd/adf\afds|ad||afd"dfad:asdf*?afd<fdsaf>fdsa,fa"'
# 过滤不合法的字符\ /:*?",<>|


def filter_illegal_character(title):
    title = title.replace('"', '')

    chararter = re.compile(r'[\/:*?,;<>|]', re.I)
    chararter = chararter.findall(title)
    for ch in chararter:
        title = title.replace(ch, '-')

    return title


title = filter_illegal_character(title)
print(title)
