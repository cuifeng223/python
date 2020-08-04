from lxml import etree
import re


def str_has_cn(str):
    return re.compile(r'[\u4e00-\u9fff]+').search(str)


def open_file(filename, encoding="utf-8"):
    with open(filename, "r", encoding=encoding) as f:
        return f.read().splitlines()


def save_file(filename, contents, encoding="utf-8"):
    with open(filename, "w", encoding=encoding) as f:
        f.writelines(contents)


def do_extract(file_name, xpath_out_file_name, cn_text_out_file_name, sort=False):
    parser = etree.HTMLParser(remove_comments=True)
    tree = etree.parse(file_name, parser)
    root = tree.getroot()
    all_cn_text = []
    all_cn_xpath = []
    for e in root.iter():
        xpath = tree.getpath(e)
        text = e.text
        tag = e.tag

        # scripts
        if tag == "script" and text:
            pattern = re.compile(r">.*[\u4e00-\u9fff]+.*<")
            cns = pattern.findall(text)
            for cn in cns:
                cn = cn.replace(">", "").replace("<", "").strip()
                cn = cn.replace("&nbsp;", " ")
                all_cn_text.append(cn + "\n")
                all_cn_xpath.append(xpath + "\n")
            continue

        # attributes
        attributes = e.attrib
        for attr in attributes:
            attr_text = attributes[attr]
            if str_has_cn(attr_text):
                all_cn_text.append(str(attr_text).strip() + "\n")
                all_cn_xpath.append(xpath + "/@" + attr + "\n")

        # elements
        if text and str_has_cn(text):
            #print(xpath + "," + str(text).strip())
            all_cn_text.append(str(text).strip() + "\n")
            all_cn_xpath.append(xpath + "\n")

    save_file(xpath_out_file_name, all_cn_xpath)
    if sort:
        all_cn_text.sort(key=lambda s: len(s), reverse=True)
        save_file(cn_text_out_file_name, all_cn_text)


def do_replace_use_lxml(file_name, xpath_out_file_name, translated_file_name):
    ''' not workd beautifully '''

    '''    
    parser = etree.HTMLParser(remove_comments=True)
    tree = etree.parse(file_name, parser)
    '''
    with open(file_name, encoding="utf-8") as f:
        contents = f.read()
    doc = etree.HTML(contents)
    tree = doc.getroottree()

    xpath_lines = open_file(xpath_out_file_name)
    translated_lines = open_file(translated_file_name)

    assert(len(xpath_lines) == len(translated_lines))

    for index, xpath in enumerate(xpath_lines):
        r = tree.xpath(xpath)
        tl = translated_lines[index]
        if len(r) > 0:
            try:
                if r[0].is_attribute:
                    # this is a attritute
                    attr_name = xpath[xpath.find("@") + 1:]
                    r[0].getparent().set(attr_name, tl)
            except(AttributeError):
                # this is a element
                r[0].text = tl
    tree.write(file_name.split('.')[0] + "_new" +
               ".html", pretty_print=True, encoding="utf-8")


def do_replace(file_name, out_file_name, translated_file_name):
    origin_texts = open_file(out_file_name)
    translated_texts = open_file(translated_file_name)
    assert(len(origin_texts) == len(translated_texts))

    with open(file_name, encoding="utf-8") as f:
        contents = f.read()

    s1 = "(?:&nbsp;|\\\s+&nbsp;|&nbsp;\\\s+)+"
    s2 = "(?:&nbsp;|\s+&nbsp;|&nbsp;\s+)*"
    for index, text in enumerate(origin_texts):
        pattern = re.compile(r"\s+")
        text = text.replace("*", "\*").replace(".", "\.") \
                   .replace("[", "\[").replace("]", "\]") \
                   .replace("{", "\{").replace("}", "\}")
        pattern_exp = pattern.sub(s1, text)
        pattern_exp = s2 + pattern_exp + s2
        print(pattern_exp)
        pattern = re.compile(r''+pattern_exp+'')
        contents = pattern.sub(translated_texts[index], contents)

    with open(file_name.split('.')[0] + "_new" + ".html", "w", encoding="utf-8") as f:
        f.write(contents)


if __name__ == "__main__":
    #do_extract("main.html", "xpath.txt", "out.txt", True)
    do_replace("main.html", "out.txt", "translated.txt")
