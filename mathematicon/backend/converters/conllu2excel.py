import os
from pathlib import Path
from typing import Iterable, Union


def combine_conllu_to_tsv(conllu_files: Iterable[Union[str, os.PathLike]],
                          tsv_path: Union[str, os.PathLike]):
    with open(tsv_path, 'w', encoding='utf-8') as newf:
        for filepath in conllu_files:
            filename = Path(filepath).name
            newf.write(f'## {filename}\n')
            with open(filepath, 'r', encoding='utf-8') as f:
                newf.write(f.read())
                newf.write('\n\n')


def split_tsv_into_conllu(combined_tsv: Union[str, os.PathLike],
                          conllu_folder: Union[str, os.PathLike]):
    with open(combined_tsv, 'r', encoding='utf-8') as f:
        conllu_text = ''
        filename = None
        for line in f.readlines():
            if line.startswith('##'):
                if conllu_text and filename:
                    with open(Path(conllu_folder, filename).resolve(), 'w', encoding='utf-8') as newf:
                        newf.write(conllu_text.strip())
                filename = line[3:].strip()
                conllu_text = ''
            else:
                conllu_text += line


if __name__ == '__main__':
    mode = input('Select mode (combine, split): ')
    conllu_folder = input('Path to folder with conllu files: ')
    path_to_combined_file = input('Path to combined file: ')
    if mode == 'combine':
        combine_conllu_to_tsv((
            f for f in Path(conllu_folder).resolve().iterdir() if f.suffix == '.conllu'
        ),
                              path_to_combined_file)
    elif mode == 'split':
        split_tsv_into_conllu(path_to_combined_file, conllu_folder)