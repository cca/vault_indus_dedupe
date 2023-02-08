# Dedupe Industrial Design Items in VAULT

In March, 2019 we moved the Industrial Design Program collection to a custom filestore location outside the main filestore. openEQUELLA saves INDUS items to this location with one additional intermediary directory, named after the collection's UUID, in the attachments path:

- main filestore: {{ ROOT }}/Institutions/cca2012/Attachments/{{ 7-bit hash of item UUID }}/{{ item UUID }}/{{ item version }}
- custom filestore: {{ ROOT }}/Institutions/cca2012/Attachments/{{ collection UUID }}/{{ 7-bit hash of item UUID }}/{{ item UUID }}/{{ item version }}

However, openEQUELLA did not _move_ INDUS item attachments to the new location, it _copied_ them. Thus every INDUS item contributed before March, 2019 is duplicated at a corresponding path in the main filestore. I discovered this when trying to confirm that our retention procedures were actually purging items—I kept running across supposedly purged items with their attachments still present, then noticed they were all INDUS items.

## Outline

- identify relevant INDUS items
- remove the main filestore directory if
    1. the attachments dir exists in the INDUS filestore
    2. both attachments dirs have the same set of files
- handle exceptions that the script runs across

To collect a JSON array of INDUS items, we can iterate over `eq search` commands:

```sh
# how many items are there?
> eq search --collections 5b07c041-2353-4712-92d0-a71eed9201da --showall | jq .available
# ≈680 items, max search length is 50, iterate 14 times until we have all items
> for i in (seq 0 13); eq search --collections 5b07c041-2353-4712-92d0-a71eed9201da --showall --info detail --length 50 --start (math 50 x $i) --modifiedBefore 2019-03-31 | jq '.results[]' >> items.txt; end
# items.txt is invalid JSON because there are no commas in between array members
# gsed is gnu sed (from homebrew), edits add commas & fix first & last lines
# could also do this in a text editor
cat items.txt | gsed -e 's/^}$/},/' -e '1c[{' -e '$c}]' > items.json
```

Once we have the items JSON, just sync this data to the file server and run the script with enough permissions to operate on the files in the filestore.

```sh
> ./sync.sh
> ssh v2
> cd indus-dedupe
# test first to make sure script works & output makes sense
> sudo python3 app.py --dry-run items.json
> sudo python3 app.py items.json
```

Included is a test.json file of example items that demonstrate different scenarios, meant to be processed with the `--dry-run` flag. It should show that one item exists only in the INDUS filestore, one in the main, and one in both with no differences in the file list.
