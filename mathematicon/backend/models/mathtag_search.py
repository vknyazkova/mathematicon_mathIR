from typing import Iterable, Tuple, List, Dict

import networkx as nx

from ..models.database import WebDBHandler
from ..models.html_models import HTMLSentence, HTMLWord, HTMLSpan


class MathtagSearch:
    def __init__(self, db: WebDBHandler):
        self.db = db

    def find_tag_descendants(self, tag_id: int):
        descendants = {tag_id}
        math_ontology = self.db.get_math_ontology()
        mathtag_tree = nx.DiGraph(math_ontology[1:])
        descendants = descendants.union(nx.descendants(mathtag_tree, tag_id))
        return descendants

    @staticmethod
    def group_annotation_fragments(annotation_fragments):
        groups = []
        current_group = []

        for fragment in annotation_fragments:
            if not current_group:
                current_group.append(fragment)
            else:
                # Check if the fragment belongs to the current group
                last_fragment = current_group[-1]

                if fragment[0] == last_fragment[0] and fragment[4] >= last_fragment[5]:
                    current_group.append(fragment)
                else:
                    # Start a new group
                    groups.append(current_group)
                    current_group = [fragment]

        if current_group:
            groups.append(current_group)

        return groups

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
        colored_tokens = []
        for t in tokens:
            if str(t['id']) in tokens_with_colors:
                t['color'] = 'green'
            else:
                t['color'] = 'black'
            colored_tokens.append(t)
        return colored_tokens

    def color_sentence_tokens(self, sent_id, colormap: Dict[str, str]):
        tokens = self.db.sent_token_info(sent_id)
        colored_tokes = []
        for t in tokens:
            t['color'] = colormap.get(str(t['id']), 'black')
            colored_tokes.append(t)
        return colored_tokes

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
            colored_tokens = {token: color for sent in sent_groups for token, color in zip(sent[2].split(','), sent[3].split(','))}
            sent_id = sent_groups[0][0]
            sent_info = self.db.sent_info(sent_id)
            left, right = self.db.sent_context(sent_info["text_id"], sent_info["pos_in_text"])
            html_sentence = HTMLSentence(
                id=sent_id,
                left=left,
                right=right,
                yb_link=self.create_yb_link(sent_info["youtube_link"], sent_info["timecode"]),
                star="true" if sent_id in user_favs else "false",
            )
            tokens_info = self.color_sentence_tokens(sent_id, colored_tokens)
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
        groups = self.group_annotation_fragments(annotations)
        res = self.create_html_sent(userid, groups)
        return None, res


if __name__ == '__main__':
    from mathematicon import DB_PATH

    math_db = WebDBHandler(DB_PATH)
    tag_search = MathtagSearch(math_db)

    available_tags = math_db.get_available_tags()

    tag_search.search('a7357b05d4f14e2cad12d6491fd6616b46', 2)