lint:
	pre-commit run --all
	mypy seqdat

install:
	cp ./build/x86_64-unknown-linux-gnu/release/install/seqdat/seqdat ~/bin/seqdat

build:
	pyoxidizer build --release

.PHONY: build install lint
