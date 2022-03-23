lint:
  pre-commit run --all
  mypy seqdat
install-bin: build
  cp build/x86_64-unknown-linux-gnu/debug/install/seqdat/seqdat ~/bin/seqdat
build:
  pyoxidizer build --path .
