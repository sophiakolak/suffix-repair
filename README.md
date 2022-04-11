# Suffix-Repair

## build_db

Files for extracting data from `BugsInPy` that will eventually be added to a database. For now, it just writes to various json files (described below)

`setup.sh`

adds BugsInPy shell scripts to PATH environment variable (this is specific to my project configuration)

`project_parser.py` 
    called by : `bug_parser.py` 

gets all relevant meta-data on projects used to accurately parse the diffs (i.e., #bugs, bug/patch commit, tests relevant to each bug, the location of those tests)

`bug_parser.py`
    requires: `project_parser.py` 
    writes to: `data/all_data`

to checkout the buggy versions of each project, and determine the exact lines changed with the diff+reconstruct the block. This info is written to "data/all_data", where a file is created for each project which includes all the information necessary to reproduce the bug/extract context 

`sort_patches.py` 
    reads from: `data/all_data` 
    writes to: `data/add`, `data/del`, `data/rep`, `data/other`

goes through the data created by `bug_parser.py`, and determines which "type" of patch was required for each bug. This is relevant for how we extract context. Currently, there are two major types (gap and no-gap) and three sub-types (1:1 replace, add only, delete only), as well as the category of "other" for when the bug is a combination of different types of changes. Writes these changes to the file  

    1. NO-GAP
    This means that all the changes come sequentially, i.e., there are no original lines of code between changes. These are simpler to handle. For example: 

        ```
                     if True:
                         do x
        -            if False:
        +            else:
                         do y           
        ```

    2. GAP
        This means that there are breaks between the changes, where the original code is still present. For example: 

        ```
                     if True:
                         do x
        -            if False:
        +            else:
                         do y 
        +                do z
        ```
    
    * 1:1 replacement
      * When lines deleted=lines added
    * delete only 
      * When the patch removed lines, but did not add any. 
    * add only 
      * When the patch added lines, but did not delete any. 

    Each of 1-1-replacement, delete-only, and add-only can be either "gap" or "no gap". When the change does not fall into any of these categories, it was marked as other (for the time being) 

`context_parser.py`
    reads from: `data/add`, `data/del`, `data/rep`, `data/other`
    writes to: `data/rep/no_gap_context`

    Uses the data created by `sort_patches.py` to extract prefix/suffix context for the type of patches specified. Currently only doing this for the 1-1-replacements with no gap (as these are the simplest types of patches). This generates a dictionary for each bug (of this type) of the form: 

    ```
    {
        prefix: 40 lines before the change
        suffix: 40 lines after the change
        long_prefix: 80 lines before the change
    }
    ```

    When prompting with prefix and suffix context, the model gets the short prefix. When prompting with only prefix, it recieves the long prefix. In both cases, it gets 80 lines total. 

## patch-gen

Generates 20 prefix only patches and 20 prefix+suffix patches (40 patches total) per bug and calculates their bleu score. 

`prefix-only.py` 
    reads from: `data/rep/no_gap_context`
    writes to: `patch-data/prefix-only/rep/no_gap`

    generates 20 ranked candidate patches (per bug) using the long prefix context created by `context_parser.py` 

`prefix-suffix.py` 
    reads from: `data/rep/no_gap_context`
    writes to: `patch-data/prefix-suffix/rep/no_gap`

    generates 20 ranked candidate patches (per bug) using the prefix and suffix context created by `context_parser.py`

`BLEU-score.py` 
    reads from: `patch-data/prefix-only/rep/no_gap`, `patch-data/prefix-suffix/rep/no_gap` 
    writes to: `data/rep/no_gap_bleu_score/p`, `data/rep/no_gap_bleu_score/ps`

    calculates bleu score for each candidate generated (with and without suffix context). Writes the bleu score, trimmed version of code, and rank to the files listed above (p=prefix only), (ps=prefix+suffix)

## BugsInPy

The underlying BugsInPy framework. Using the `BugsInPy/projects` directory to extract bug and project meta-data in the `build_db` files. Not currently relying on the scripts in `BugsInPy/framework` 

