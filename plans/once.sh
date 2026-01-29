#!/bin/bash

issues=$(gh issue list --state open --json number,title,body,comments)

opencode --agent plan --prompt "$issues @plans/progress.txt @plans/prompt.md"