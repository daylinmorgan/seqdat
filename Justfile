build:
  shiv -c seqdat -o ~/bin/seqdat .
lint:
  pre-commit run --all
  mypy seqdat
