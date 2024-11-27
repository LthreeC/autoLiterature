import os
import logging
import re
from tqdm import tqdm
from .downloads import get_paper_info_from_paperid, get_paper_pdf_from_paperid

logging.basicConfig()
logger = logging.getLogger("utils")
logger.setLevel(logging.INFO)


class patternRecognizer(object):
    def __init__(self, regular_rule):
        self.pattern = re.compile(regular_rule)

    def match(self, string):
        return self.pattern.match(string)

    def findall(self, string):
        return self.pattern.findall(string)

    def multiple_replace(self, content, **replace_dict):
        def replace_(value):
            match = value.group()
            if match in replace_dict.keys():
                return replace_dict[match]
            else:
                return match + " **Not Correct, Check it**"

        replace_content = self.pattern.sub(replace_, content)

        return replace_content


def note_modified(pattern_recog, md_file, **replace_dict):
    with open(md_file, "r", encoding='utf-8') as f:
        content = f.read()

    replaced_content = pattern_recog.multiple_replace(content, **replace_dict)

    with open(md_file, "w", encoding='utf-8') as f:
        f.write("".join(replaced_content))


def get_pdf_paths(pdf_root):
    pdf_paths = []
    for root, _, files in os.walk(pdf_root):
        for file in files:
            if file.lower().endswith(".pdf"):
                pdf_paths.append(os.path.join(root, file))

    return pdf_paths


def get_pdf_paths_from_notes(md_root, reg):

    md_files = []
    for root, _, files in os.walk(md_root):
        for file in files:
            if file.lower().endswith("md") or file.lower().endswith("markdown"):
                md_files.append(os.path.join(root, file))

    pdf_paths_from_notes = []
    for md_file in md_files:
        with open(md_file, "r") as f:
            content = f.read()
        m = reg.findall(content)
        m = [i.split("(")[-1].split(")")[0] for i in m]
        pdf_paths_from_notes.extend(m)

    return pdf_paths_from_notes


def get_pdf_paths_from_notes_dict(md_root, reg):
    pdf_paths_from_notes_dict = {}
    if os.path.isdir(md_root):
        md_files = []
        for root, _, files in os.walk(md_root):
            for file in files:
                if file.lower().endswith("md") or file.lower().endswith("markdown"):
                    md_files.append(os.path.join(root, file))

        for md_file in md_files:
            with open(md_file, "r") as f:
                content = f.read()
            m = reg.findall(content)
            m = [i.split("(")[-1].split(")")[0] for i in m]
            pdf_paths_from_notes_dict[md_file] = m
    else:
        with open(md_root, "r") as f:
            content = f.read()
        m = reg.findall(content)
        m = [i.split("(")[-1].split(")")[0] for i in m]
        pdf_paths_from_notes_dict[md_root] = m

    return pdf_paths_from_notes_dict


def classify_identifier(identifier):
    """Not need to download PDF file"""
    if identifier.endswith("}}"):
        return True
    else:
        return False


def get_update_content(matchs, note_file, pdfs_path, proxy):

    replace_dict = dict()
    for literature in tqdm(matchs):
        pdf = classify_identifier(literature)

        literature_id = literature.split("{")[-1].split("}")[0]
        bib = get_paper_info_from_paperid(literature_id, proxy=proxy)
        # rep \n with ' ' in title
        bib["title"] = bib["title"].replace("\n", " ")

        try:
            pdf_name = literature_id + "__" +  "_".join(bib["title"].split(" ")) + ".pdf"
            # pdf_name = bib["title"] + ".pdf"
            # rep specific symbol with '_'
            pdf_name = re.sub(r"[<>:\"/\\|?*\n\r\x00-\x1F\x7F']", "_", pdf_name)
            pdf_path = os.path.join(pdfs_path, pdf_name)

            if pdf:
                if not os.path.exists(pdf_path):
                    # print("[DEBUG]----------:", "pdf_link", bib["pdf_link"])
                    get_paper_pdf_from_paperid(
                        literature_id, pdf_path, direct_url=bib["pdf_link"], proxy=proxy
                    )
                    if not os.path.exists(pdf_path):
                        get_paper_pdf_from_paperid(literature_id, pdf_path, proxy=proxy)

            if os.path.exists(pdf_path):
                # FIX 这里start需要是文件夹路径?
                # print("[DEBUG]----------: file!!", pdf_path, note_file, os.path.relpath(path=pdf_path, start=os.path.dirname(note_file)))
                replaced_literature = (
                    "- **{}** {} et al. **{}**, **{}**, ([Pdf]({}))([Link]({})) {{{{{}}}}}".format(
                        bib["title"],
                        bib["author"].split(" and ")[0],
                        bib["journal"],
                        bib["year"],
                        os.path.relpath(pdf_path, start=os.path.dirname(note_file)).split("/", 1)[-1],
                        bib["url"],
                        literature_id,
                    )
                )
            else:
                replaced_literature = (
                    "- **{}** {} et al. **{}**, **{}**, ([Link]({})) {{{{{}}}}}".format(
                        bib["title"],
                        bib["author"].split(" and ")[0],
                        bib["journal"],
                        bib["year"],
                        bib["url"],
                        literature_id,
                    )
                )
            replace_dict[literature] = replaced_literature
        except:
            logger.info("文献下载失败，已经跳过 {}".format(literature_id))

    return replace_dict
