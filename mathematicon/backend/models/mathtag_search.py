from typing import Iterable, Tuple

import networkx as nx

from ..models.database import WebDBHandler
from ..models.html_models import HTMLsentence, HTMLWord, HTMLSpan


class MathtagSearch:
    def __init__(self, db: WebDBHandler):
        self.db = db

    def find_tag_descendants(self, tag_id: int):
        descendants = {tag_id}
        math_ontology = self.db.get_math_ontology()
        mathtag_tree = nx.DiGraph(math_ontology[1:])
        descendants.union(nx.descendants(mathtag_tree, tag_id))
        return descendants

    @staticmethod
    def intersect(offsets1, offsets2):
        start1, end1 = offsets1
        start2, end2 = offsets2
        return start1 <= end2 and end1 >= start2

    @staticmethod
    def find_intersecting_annotations(annotations):
        """
        Find intersecting annotations and group by sentence, splitting groups if offsets intersect.
    
        Parameters:
        - annotations (list of tuples): List of annotations, where each annotation is represented as a tuple of (sent_id, char_start, char_end).
    
        Returns:
        - list of lists: A list of lists where each inner list represents a group of non-intersecting annotations within the same sentence.
        """
        grouped_annotations = []
    
        for annotation in annotations:
            sent_id = annotation[0]
            char_start = annotation[4]
            char_end = annotation[5]
            intersecting_group = None
    
            # Check for intersection with existing groups
            for group in grouped_annotations:
                for existing_annotation in group:
                    existing_sent_id = existing_annotation[0]
                    existing_start = existing_annotation[4]
                    existing_end = existing_annotation[5]
                    if sent_id == existing_sent_id and MathtagSearch.intersect((char_start, char_end), (existing_start, existing_end)):
                        intersecting_group = group
                        break

            if intersecting_group is not None:
                intersecting_group.append(annotation)
            else:
                grouped_annotations.append([annotation])
        return grouped_annotations

    def sort_sents_by_favourites(self,
                                 userid: int,
                                 sentence_groups: Iterable[Iterable[tuple]]) -> Tuple[Iterable[int], Iterable[Iterable[tuple]]]:
        if userid:
            user_favs = self.db.get_user_favourites(userid)
            sorted_sents = sorted(
                sentence_groups, key=lambda x: 1 if x[0][0] in user_favs else 0, reverse=True
            )
        else:
            user_favs = []
            sorted_sents = sentence_groups
        return user_favs, sorted_sents

    @staticmethod
    def create_yb_link(video_link: str,
                       timecode: str):
        if timecode:
            start = timecode.split(' ')[0]
            return video_link + '&t=' + start + 's'
        return video_link

    def vanilla_coloring(self, sent):
        tokens = self.db.sent_token_info(sent[0])
        tokens_with_colors = sent[2].split(',')
        # colors = sent[3].split(',')
        colored_tokens = []
        for t in tokens:
            if str(t['id']) in tokens_with_colors:
                # idx = tokens_with_colors.index(str(t['id']))
                t['color'] = 'green'
            else:
                t['color'] = 'black'
            colored_tokens.append(t)
        return colored_tokens

    def color_sentence_tokens(self, sent):
        tokens = self.db.sent_token_info(sent[0])
        tokens_with_colors = sent[2].split(',')
        colors = sent[3].split(',')
        colored_tokens = []
        for t in tokens:
            if str(t['id']) in tokens_with_colors:
                idx = tokens_with_colors.index(str(t['id']))
                t['color'] = colors[idx]
            else:
                t['color'] = 'black'
            colored_tokens.append(t)
        return colored_tokens

    def html_tokens_generator(self,
                              tokens: Iterable[dict]):
        plain_token = HTMLSpan('')
        for token in tokens:
            if not token['pos'] == 'PUNCT':
                if plain_token.text:
                    yield plain_token
                    plain_token = HTMLSpan('')
                yield HTMLWord(text=token['token'],
                               pos=token['pos'],
                               lemma=token['lemma'],
                               char_start_=token['char_start'],
                               char_end_=token['char_end'],
                               color=token['color'])
            else:
                plain_token.text += token['token']
            whitespace = ' ' if token['whitespace'] else ''
            plain_token.text += whitespace

    def create_html_sent(self,
                         userid,
                         sentence_groups):
        html_sentences = []
        user_favs, selected_sents = self.sort_sents_by_favourites(userid, sentence_groups)
        for sent_groups in selected_sents:
            for sent in sent_groups:
                sent_info = self.db.sent_info(sent[0])
                left, right = self.db.sent_context(sent_info["text_id"], sent_info["pos_in_text"])
                html_sentence = HTMLsentence(
                    id=sent[0],
                    left=left,
                    right=right,
                    yb_link=self.create_yb_link(sent_info["youtube_link"], sent_info["timecode"]),
                    star="true" if sent[0] in user_favs else "false",
                )
                tokens_info = self.vanilla_coloring(sent)
                for html_token in self.html_tokens_generator(tokens_info):
                    html_sentence.tokens.append(html_token)
                html_sentences.append(html_sentence)
        return html_sentences

    def search(self,
               query_math_tag_id: str,
               userid: int):
        bd_id = self.db.math_tag_id(query_math_tag_id)
        tags_to_search = self.find_tag_descendants(bd_id)
        found_math_ent = self.db.get_math_entities(list(tags_to_search))
        annotations = self.db.get_html_math_annotation(found_math_ent)
        intersec = self.find_intersecting_annotations(annotations)
        res = self.create_html_sent(userid, intersec)
        return None, res


if __name__ == '__main__':
    from mathematicon import DB_PATH

    math_db = WebDBHandler(DB_PATH)
    tag_search = MathtagSearch(math_db)

    available_tags = math_db.get_available_tags()

    tag_search.search('a7357b05d4f14e2cad12d6491fd6616b46', 2)