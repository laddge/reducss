import glob
import os
import re

from bs4 import BeautifulSoup


def parse(cssstr):
    """parse.

    Parameters
    ----------
    cssstr :
        cssstr
    """
    csr = 0
    d = {}
    while True:
        if "{" not in cssstr[csr:]:
            break
        pos = csr + cssstr[csr:].find("{")
        sel_start_inv = cssstr[csr:pos][::-1].find("}")
        if sel_start_inv != -1:
            sel_start = pos - sel_start_inv
        else:
            sel_start = csr
        sels = cssstr[sel_start:pos].strip()
        points = [sel_start]
        depth = 0
        for i in range(len(cssstr[pos:])):
            c = cssstr[pos + i]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            if depth == 0:
                points.append(pos + i)
                csr = pos + 1
                break
        if sels in d.keys():
            d[sels].append(points)
        else:
            d[sels] = [points]
    return d


def get_unused(htmlstr, cssstr, whitelist=[]):
    """get_unused.

    Parameters
    ----------
    htmlstr :
        htmlstr
    cssstr :
        cssstr
    whitelist :
        whitelist
    """
    cssstr = "".join([line.strip() for line in cssstr.split("\n")])
    cssstr = re.sub(r"/\*.*?\*/", "", cssstr)
    cssstr = re.sub(r" *, *", ",", cssstr)
    cssstr = re.sub(r" *: *", ":", cssstr)
    cssstr = re.sub(r" *! *", "!", cssstr)
    cssstr = re.sub(r" *\> *", ">", cssstr)
    cssstr = re.sub(r" *\+(?=[^}]*?{) *", "+", cssstr)
    cssstr = re.sub(r" *\*(?=[^}]*?{) *", "*", cssstr)
    cssstr = re.sub(r" *(?=[(){}]) *", "", cssstr)
    cssstr = cssstr.replace("0.", ".")
    d = parse(cssstr)
    soup = BeautifulSoup(htmlstr, "html.parser")
    unused = {}
    for sel, points in d.items():
        if sel[0] == "@":
            continue
        if sel in whitelist:
            continue
        _sel = sel
        sel = sel.replace(">:last-child", "")
        sel = re.sub(r":.*?(?=([,+>]|$))", "", sel)
        sel = sel.strip(",")
        if not sel:
            continue
        els = soup.select(sel)
        if not els:
            unused[_sel] = points
    return unused, cssstr


def reduce(htmlstr, cssstr, whitelist=[]):
    """reduce.

    Parameters
    ----------
    htmlstr :
        htmlstr
    cssstr :
        cssstr
    whitelist :
        whitelist
    """
    unused, cssstr = get_unused(htmlstr, cssstr, whitelist)
    cut = []
    for _, points in unused.items():
        for p in points:
            cut.append(p)
    sorted_cut = sorted(cut)
    cut = []
    for c in sorted_cut:
        if not cut:
            cut.append(c)
        elif c[0] > cut[-1][1] + 1:
            cut.append(c)
        elif c[1] <= cut[-1][1]:
            continue
        else:
            cut[-1][1] = c[1]
    cutted = 0
    for c in cut:
        cssstr = cssstr[: c[0] - cutted] + cssstr[1 + c[1] - cutted :]
        cutted += 1 - c[0] + c[1]
    cssstr = re.sub(r"}{.*?(?=[{}])", "", cssstr[::-1])[::-1]
    return cssstr


def auto(dirname, whitelist=[]):
    """auto.

    Parameters
    ----------
    dirname :
        dirname
    whitelist :
        whitelist
    """
    htmlstr = ""
    for htmlpath in glob.glob(os.path.join(dirname, "**/*.html"), recursive=True):
        with open(htmlpath) as f:
            htmlstr += f.read()
    for csspath in glob.glob(os.path.join(dirname, "**/*.css"), recursive=True):
        with open(csspath) as f:
            reduced = reduce(htmlstr, f.read())
        with open(csspath, "w") as f:
            f.write(reduced)
