# Mathematicon database

База данных состоит из 5 основных частей:

- информация о текстах (серое)
- грамматическая разметка (зеленое)
- математическая база знаний (фиолетовое)
- математическая разметка (розовое)
- информация о пользователе (синий)
[![Full Database](https://app.eraser.io/workspace/izH6QFpxvKyc7AxHcMK7/preview?elements=2LQ7OPT9Sm82EqhgticnSA&type=embed)](https://app.eraser.io/workspace/izH6QFpxvKyc7AxHcMK7?elements=2LQ7OPT9Sm82EqhgticnSA)



## Информация о текстах
[![Text](https://app.eraser.io/workspace/izH6QFpxvKyc7AxHcMK7/preview?elements=8PIrHy3d8EO9S3388kw3xA&type=embed)](https://app.eraser.io/workspace/izH6QFpxvKyc7AxHcMK7?elements=8PIrHy3d8EO9S3388kw3xA)



**math_branches **- разделы математики (Enum)

**text_difficulty** - уровень сложности текста (Enum)

**annotation_status** - этапы разметки (Enum)

**texts** - тексты (уникально определяются по filename)

- title - название видео
- filename - имя файла, под которым хранятся все связанные файлы с разметкой
- youtube_link - ссылка на видео на ютубе
- timecode_start - таймкод начала записанного текста
- timecode_end - таймкод конца записанного текста
**sents **- предложения (уникально определяются по text_id и pos_in_text)

- sent - предложение целиком
- lemmatized - строка из лемм предложения записанных через пробел
- pos_in_text - порядковый номер предложения в тексте (начиная с 1)
- timecode - таймкод начала предложения в видео (чтобы давать ссылку на конкретное предложение в видео)
## Грамматическая разметка
[![Morphology](https://app.eraser.io/workspace/izH6QFpxvKyc7AxHcMK7/preview?elements=a61YMSCFiX6CFiXKYSyuLw&type=embed)](https://app.eraser.io/workspace/izH6QFpxvKyc7AxHcMK7?elements=a61YMSCFiX6CFiXKYSyuLw)



**morph_categories ** - грамматические категории (Enum)

**morph_values ** - грамматические значения (Enum)

**lemmas **- леммы (Enum)

**pos** - частеречные теги (Enum)

- name - сам тег
- descr_rus - значение тега на русском
- descr_en - значение тега на английском
- examples - примеры токенов, размечаемых этим тегом
- UD_link - уникальная часть ссылки на этот тег на сайте Universal Dependencies
**tokens** - токены (уникально определяется по sent_id и pos_in_sent)

- pos_in_sent - порядковый номер токена в предложении (начиная с 1)
- token - сам токен
- whitespace - есть ли в оригинальное строке предложения после этого токена пробел
- char_start - символьное начало токена в строке предложения
- char_end - символьный конец токена в строке предложения
## Математическая онтология
[![Math ontology](https://app.eraser.io/workspace/izH6QFpxvKyc7AxHcMK7/preview?elements=SFSiCoXjk632Roz3H_7l3g&type=embed)](https://app.eraser.io/workspace/izH6QFpxvKyc7AxHcMK7?elements=SFSiCoXjk632Roz3H_7l3g)



**kb_edge_types ** - типы связей между тегами (у нас в бд есть отношения SubClassOf и Instance)(Enum)

**math_tags** - сами теги (уникально определяются по inception_id)

- inception_id - длинный уникальный айдишник автоматически генерируемый инсепшеном
- parent_id - родитель этого тега в дереве тегов
- edge_type - как родитель и потомок связаны (как SubClassOf или как Instance)
**math_tag_info_types ** - что мы храним про теги (лейбл, комментарий) (Enum)

**math_tag_info **- вся информация о теге

- info_type_id - что за информация (лейбл/комментарий)
- text - сама информация
- lang_id - на каком языке (английский, русский, символы, формула, еще что
## Математическая разметка
[![Math annotation](https://app.eraser.io/workspace/izH6QFpxvKyc7AxHcMK7/preview?elements=BbryGvUl2_gDtAhCUdRpdw&type=embed)](https://app.eraser.io/workspace/izH6QFpxvKyc7AxHcMK7?elements=BbryGvUl2_gDtAhCUdRpdw)



**annot_fragment ** - кусочек аннотации, определяемый своим оффсетом (спэн выделяемый для последующей разметки в инсепшене на любом из слоев)

- sent_id - предложение, внутри которого выделенный фрагмент
- char_start - начало фрагмента в предложении
- char_end - конец фрагмента в предложении
**math_entities **- то, чему присваивается тег и что размечается на слое Math_entities

- math_tag_id - присвоенный тег
- name - (для переменных и цифр тут пишется реальное значение типа x, y, 12 и тд)
- frag_id - фрагмент аннотации
**fragment_tokens **- соответствия между токенами и фрагментами аннотаций (так как один фрагмент может заключать в себе несколько токенов)

- frag_id - фрагмент аннотации
- token_id - токен, принадлежащий этому фрагменту
**math_annotation **- вся размеченная аннотация со всех слоев 

- math_ent_id - математическая сущность, к которой относится фрагмент аннотации (так как все слои привязаны к слою Math_entities, где мы размечаем теги)
- annot_frag_id - фрагмент аннотации 
- role_id - как этот фрагмент связан с текущей математической сущностью (как ее аргумент, как сама эта сущность, как часть этой сущность, как ее спецификатор и тд)
**math_roles **- какие роли могу приписываться фрагментам аннотации

- layer - на каком слое задается эта роль
- role - сама роль (math_entity, specifier, arg1, arg2, part и тд)
- color - каким цветом обозначается в выдаче


## Информация о пользователях
[![users](https://app.eraser.io/workspace/izH6QFpxvKyc7AxHcMK7/preview?elements=BT_euqdGNbb_vf6qgtAPoQ&type=embed)](https://app.eraser.io/workspace/izH6QFpxvKyc7AxHcMK7?elements=BT_euqdGNbb_vf6qgtAPoQ)



**users **- обязательная информация о пользователях

- username - логин
- email - почта, указанная при регистрации
- password - (хэш) пароля, указанного пользователем
- salt - штука примешиваемая к паролю при хэшировании для более надежного хранения
**user_history **- история запросов пользователя

- user_id - пользователь
- query - строка аргументов гет запроса
- time - время запроса
**favoutites **- избранное пользователей

- query - текст запроса (или тег для поиска по тегу), которым было получено избранное предложение
- query_type - тип запроса, по которому было найдено это предложение
- sent_id - предложение, которые добавили в изрбанное


