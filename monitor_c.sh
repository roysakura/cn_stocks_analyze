#!/bin/sh
dir1=/workspace/projects/cn_stocks_analyze/data/concepts/
while inotifywait -qqre modify "$dir1"; do
	cd /workspace/projects/cn_stocks_analyze/ && /workspace/projects/cn_stocks_analyze/venv/bin/python concept_updates.py 
done