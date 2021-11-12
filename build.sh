#!/usr/bin/env bash

# build seqdat executable

pyinstaller \
	--onefile \
	--clean \
	--name seqdat \
	seqdat/cli.py
