# who-int-to-json

This script converts Wolrd Health Organization's classifications from their 'simplified linearizations' TSV files to JSON.

It was tested with two classifications:
- ICD-11 for Mortality and Morbidity Statistics
https://icd.who.int/browse11/l-m/en
- International Classification of Health Interventions (ICHI)
https://icd.who.int/dev11/l-ichi/en

The classifiers are represented as browseable trees at those links. Their linearized TSV files can be downloaded here:
https://icd.who.int/dev11/downloads/

```
usage: who-int-to-json.py [-h] [--tsv FILE] [--skip_residual] [--skip_duplicates] [--index_word_limit N] [--limit N] [--batch_tag TAG]

Converts World Health Organization's linearized classifications to JSON

optional arguments:
  --tsv FILE            Path to a linearization file.
  --skip_residual
  --skip_duplicates
  --index_word_limit N  Only index categories no longer than this number of words.
  --limit N             Only use first N lines.
  --batch_tag TAG       A string that will identify this import among others.
```

These classifiers all have 3 levels of entities:
- Chapters are top level entities. They can contain only blocks.
- Blocks are broad grouping entities that should not be selected as end-values by those classifying diseases or interventions. They can contain nested blocks or categories.
- Categories are the payload. These are diseases and interventions that are meant to be selected by end-users classifying something. They can contain only other nested categories or just be leafs.

This script only yields valid lines determined by the following:
- All chapters are valid.
- A block is only valid if it contains non-empty `BlockId`. Empty `BlockId` is used in ICHI for sub-dictionaries of targets, actions, and means of interventions and are useless when selecting categories by end-users.
- A category is only valid if all of its ancestor blocks are valid.

Some lines are marked as residuals. While they are useful to professionals, their suggesting to non-professionals is discouraging. So these can be skipped using `--skip_residual` flag.

Some lines contain duplicate codes. While we hope WHO will fix these, we cannot afford duplicates when mapping entities by their codes. Duplicate codes throw an error by default but can be skipped using `--skip_duplicates` flag.

Some lines are of little use for patients finding doctors, such as "Non-economic incentives to encourage improvements in relation to other health-related behaviours, not elsewhere classified". While you should manually sort what you show to your users, many lines can be filter out by limiting the number of words. Such a limit can produce false negatives but it simplifies sorting by a lot. Use `--index_word_limit` option to set `index` JSON field to `true` or `false` based on word count.

Example for ICD-11:
```bash
python3 who-int-to-json.py --tsv=LinearizationMiniOutput-MMS-en.txt --skip_residual --skip_duplicates --index_word_limit=4 --batch_tag="2021-10-15 07:15" --limit=20 > icd-11_4w_20.json
```

Example for ICHI-11:
```bash
python3 who-int-to-json.py --tsv=LinearizationMiniOutput-ICHI-en.txt --skip_residual --skip_duplicates --index_word_limit=4 --batch_tag="2021-10-15 07:15" --limit=20 > ichi-11_4w_20.json
```

## Firebase Import
In case you want to import this JSON to Firebase, use this:

```bash
npm install -g node-firestore-import-export
firestore-import --accountCredentials credentials.json --backupFile icd-11.json --nodePath conditions
```

where `credentials.json` is a file you export from Firebase console as per this tutorial: https://www.youtube.com/watch?v=gPzs6t3tQak
