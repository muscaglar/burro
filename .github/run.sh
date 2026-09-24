#!/bin/sh
# Runs one command of ci.yml. If it fails, says again what it printed, where anyone can read it.
#
# Anyone can read the annotations of a run, and only a person who is signed in can read
# its log. So when the command fails, two things are said as annotations: the lines that
# name a failure, and the last lines that were printed. The step then fails with the
# command's own code. A command that passes is run and nothing more.
#
#     sh .github/run.sh COMMAND [WORD ...]
#
# It is for ci.yml alone, whose jobs run on made-up data and are given no secret. A
# workflow that reads a key or a real file says nothing this way: see docs/data-builds.md.

# How many of the last lines are said, how many lines that name a failure are said from
# each end, and how long a line may be.
LAST=60
EACH_END=20
WIDTH=400
# What a line that names a failure holds, in the words of the tools these jobs run.
NAMES='[Ee]rror:|error TS[0-9]+|^E  |^(FAILED|ERROR|FAIL) |Found [0-9]+ errors?'
NAMES="$NAMES"'|^ +[0-9]+:[0-9]+ +error |●|✖|✕|Exceeded timeout|^not ok|is out of date'
NAMES="$NAMES"'|\*\* [A-Z ]*FAILED \*\*|^make(\[[0-9]+\])?: \*\*\*|^npm (error|ERR!)'
NAMES="$NAMES"'|(^|[^0-9A-Za-z])[0-9]+ failed'

kept=$(mktemp "${RUNNER_TEMP:-${TMPDIR:-/tmp}}/printed.XXXXXX") || exit 1
trap 'rm -f "$kept" "$kept.code"' EXIT

# The code of the command, and not of `tee`, is the one that counts.
{
    "$@" 2>&1
    echo "$?" > "$kept.code"
} | tee "$kept"
code=$(cat "$kept.code" 2>/dev/null || echo 1)
[ "$code" -eq 0 ] && exit 0

# A comma and a colon end a title, so each is written as the runner asks.
title=$(printf '%s' "$*" | LC_ALL=C sed -e 's/%/%25/g' -e 's/:/%3A/g' -e 's/,/%2C/g')

if [ ! -s "$kept" ]; then
    echo "::error title=$title::It failed, and printed nothing."
    exit "$code"
fi

# The runner reads an annotation only where it starts a line, and a command may end what
# it prints with no end of line.
if [ "$(tail -c 1 "$kept" | wc -l)" -eq 0 ]; then
    echo
fi

escape=$(printf '\033')

# What was printed, as bytes and not as text in any language, so that a byte that is no
# letter stops nothing. Colour is taken out and a long line is cut.
plain() {
    LC_ALL=C sed -e "s/$escape\[[0-9;]*[A-Za-z]//g" "$kept" | LC_ALL=C cut -c "1-$WIDTH"
}

# Lines as one line: the runner reads `%0A` as the end of a line, and a line of its own
# that starts `::` as a command.
as_one() {
    LC_ALL=C awk '
        { gsub(/%/, "%25"); gsub(/\r/, "%0D"); printf "%s%s", (NR > 1 ? "%0A" : ""), $0 }
        END { printf "\n" }
    '
}

named=$(plain | LC_ALL=C grep -E -c "$NAMES")
if [ "$named" -gt 0 ]; then
    printf '::error title=%s%%3A the lines that name a failure::' "$title"
    plain | LC_ALL=C grep -E "$NAMES" |
        LC_ALL=C awk -v each="$EACH_END" -v all="$named" '
            all <= 2 * each || NR <= each || NR > all - each { print; next }
            NR == each + 1 { printf "and %d lines more, of which the last are:\n", all - 2 * each }
        ' | as_one
fi

printf '::error title=%s%%3A the last lines it printed::' "$title"
plain | tail -n "$LAST" | as_one
exit "$code"
