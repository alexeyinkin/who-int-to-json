import argparse
import csv
import json
import re

Code_column                     = 'Code'
BlockId_column                  = 'BlockId'
Title_column                    = 'Title'
ClassKind_column                = 'ClassKind'
DepthInKind_column              = 'DepthInKind'
IsResidual_column               = 'IsResidual'
PrimaryLocation_column          = 'PrimaryLocation'
ChapterNo_column                = 'ChapterNo'
isLeaf_column                   = 'isLeaf'
noOfNonResidualChildren_column  = 'noOfNonResidualChildren'
Grouping1_column                = 'Grouping1'
Grouping2_column                = 'Grouping2'
Grouping3_column                = 'Grouping3'
Grouping4_column                = 'Grouping4'
Grouping5_column                = 'Grouping5'
_NOCODEASSIGNED                 = '_NOCODEASSIGNED'

ClassKind_chapter   = 'chapter'
ClassKind_block     = 'block'
ClassKind_category  = 'category'

titleIndentRegExp = re.compile('^((- )*)(.*)$')

def get_raw_title(cells):
    return cells[Title_column]


def get_title_level(row):
    match = titleIndentRegExp.match(row[Title_column])
    dashes_and_spaces = match.group(1)
    return len(dashes_and_spaces) // 2


def get_title_without_indent(row):
    return unindent_title(row[Title_column])


def unindent_title(title):
    match = titleIndentRegExp.match(title)
    return match.group(3)


def get_code(row):
    code_cell_value = row[Code_column]
    if code_cell_value != '': return code_cell_value

    ClassKind = row[ClassKind_column]
    Title_underscored = get_title_without_indent(row).replace(' ', '_')

    if ClassKind == ClassKind_chapter:
        ChapterNo = row[ChapterNo_column]
        if ChapterNo == '':
            return 'chapter_' + Title_underscored
        return 'chapter_' + ChapterNo

    if ClassKind == ClassKind_block:
        BlockId = row[BlockId_column]
        if BlockId == '':
            return 'block_' + Title_underscored
        return 'block_' + BlockId

    raise ValueError('Cannot get code: ' + ClassKind + ' ' + row[Title_column])


def row_to_record(row):
    return {
        'Code':         get_code(row),
        'title':        get_title_without_indent(row),
        'ClassKind':    row[ClassKind_column],
        'IsResidual':   string_to_bool(row[IsResidual_column]),
    }


def string_to_bool(s):
    if s == 'True': return True
    if s == 'False': return False
    raise ValueError('Invalid string boolean value: ' + s)


def is_row_valid(row):
    Code = get_code(row)
    if Code == _NOCODEASSIGNED: return False

    ClassKind = row[ClassKind_column]

    if ClassKind == ClassKind_category: return True
    if ClassKind == ClassKind_chapter: return True

    if ClassKind == ClassKind_block:
        BlockId = row[BlockId_column]
        return BlockId != ''

    raise ValueError('Unknown ClassKind: ' + ClassKind + ' ' + row[Title_column])


def all_true(list_):
    for value in list_:
        if not value: return False
    return True


def get_title_word_count(row):
    Title = get_title_without_indent(row)
    return len(Title.split(' '))


def is_category(row):
    return row[ClassKind_column] == ClassKind_category


parser = argparse.ArgumentParser(description='Converts World Health Organization\'s linearized classifications to JSON')
parser.add_argument('--tsv', metavar='FILE', type=str, help='Path to a linearization file.')
parser.add_argument('--skip_residual', action='store_true')
parser.add_argument('--skip_duplicates', action='store_true')
parser.add_argument('--index_word_limit', metavar='N', type=int, help='Only index categories no longer than this number of words.')
parser.add_argument('--limit', metavar='N', type=int, help='Only use first N lines.')
parser.add_argument('--batch_tag', metavar='TAG', type=str, help='A string that will identify this import among others.')

args = parser.parse_args()

skip_residual       = args.skip_residual
skip_duplicates     = args.skip_duplicates
index_word_limit    = args.index_word_limit
limit               = args.limit
batch_tag           = args.batch_tag

dict = {}

dict['root'] = {
}

parent_id = 'root'
last_id_chain = [parent_id]
last_validity_chain = [True]

with open(args.tsv, encoding='utf-8-sig') as f:
    reader = csv.DictReader(f, delimiter='\t', quotechar='"')

    for row in reader:
        if limit == 0: break

        id = get_code(row)
        self_valid = is_row_valid(row)
        index = is_category(row)

        record = row_to_record(row)
        level = get_title_level(row) + 1
        level_diff = level - len(last_id_chain) + 1

        if level_diff == 1:
            ancestor_ids = last_id_chain
            ancestor_validities = last_validity_chain
        else:
            ancestor_ids = last_id_chain[:-1 + level_diff]
            ancestor_validities = last_validity_chain[:-1 + level_diff]

        record['ancestorIds'] = ancestor_ids
        record['parentId'] = ancestor_ids[-1]

        if index_word_limit != None:
            title_word_count = get_title_word_count(row)
            index = index and (title_word_count <= index_word_limit)

        record['index'] = index

        if batch_tag != None:
            record['batchTag'] = batch_tag

        last_id_chain = ancestor_ids + [id]
        last_validity_chain = ancestor_validities + [self_valid]

        if not all_true(last_validity_chain): continue
        if skip_residual and record['IsResidual']: continue

        if id in dict and not skip_duplicates:
            raise ValueError('Duplicate ID: ' + id + ' for ' + row[Title_column])

        dict[id] = record

        if limit != None:
            limit -= 1

print(json.dumps(dict))
