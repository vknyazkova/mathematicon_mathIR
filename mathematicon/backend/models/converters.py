import os
import re
from pathlib import Path
from typing import Iterable, Dict, Any, Callable, Union

import yaml
from yaml.parser import ParserError
from spacy import Language
from spacy_conll.parser import ConllParser

from database import TextDBHandler
from custom_dataclasses import DatabaseText


class YamlConverter:
    def __init__(self,
                 filepaths: Iterable[Union[str, os.PathLike]],
                 text_preprocess: Callable[[str], str] = None):
        if not text_preprocess:
            text_preprocess = self.remove_double_spaces
        self.yaml_contents = self.load_yamls(filepaths, text_preprocess)
        self.parsed_docs = None

    @staticmethod
    def remove_double_spaces(text: str) -> str:
        return re.sub(r"\s+", " ", text)

    @staticmethod
    def load_yamls(filepaths: Iterable[str, os.PathLike],
                   preprocess: Callable[[str], str]) -> Dict[Path, Dict[str, Any]]:
        """
        Reads texts that are stored in yaml files
        Args:
            filepaths: iterable of paths to yaml files
            preprocess: callable that preprocesses text field from the yaml file

        Returns: {filepath: {field: values}}

        """
        files_info = {}
        for p in filepaths:
            p = Path(p).resolve()
            with open(p, encoding='utf-8') as f:
                try:
                    read_data = yaml.load(f, Loader=yaml.FullLoader)
                    read_data["text"] = preprocess(read_data["text"])
                    files_info[p] = read_data
                except ParserError as e:
                    print(e)
                    print()
                    print(f'Some problems with file {f}')
                finally:
                    continue
        return files_info

    def to_conllu(self,
                  nlp: Language,
                  dest_folder: Union[str, os.PathLike]) -> Iterable[Path]:
        dest_folder = Path(dest_folder).resolve()
        dest_folder.mkdir(parents=True, exist_ok=True)

        nlp.add_pipe("conll_formatter", last=True)

        written_files = []
        for file, info in self.yaml_contents.items():
            doc = nlp(info['text'])
            result_path = Path(dest_folder, file.with_suffix(".conllu").name)
            with open(result_path, "w", encoding="utf-8") as f:
                f.write(doc._.conll_str)
            written_files.append(result_path)
        return written_files

    def to_database(self,
                    nlp: Language,
                    db: TextDBHandler):
        for file, info in self.yaml_contents.items():
            db_text_info = {k: v for k, v in info.items() if k not in ['timecode_start', 'timecode_end', 'text']}
            doc = nlp(info['text'])
            db_text = DatabaseText(doc, filename=file.stem, **db_text_info)

            db.add_text(db_text)
            for sent in db_text:
                db.add_sentence(sent)
                db.add_sentence_tokens(sent)


def update_ud_annot(conllu_file: Union[str, os.PathLike],
                    db: TextDBHandler,
                    nlp: Language):
    conllu_file = Path(conllu_file).resolve()
    filename = conllu_file.stem
    conllu_nlp = ConllParser(nlp)
    conllu_doc = conllu_nlp.parse_conll_file_as_spacy(conllu_file)
    for sent in DatabaseText(conllu_doc, filename=filename):
        db.update_sentence_tokens_info(sent)