# SEQDAT

**Seq**uencing **Dat**a Manager

## Usage

See [docs](docs/usage.md) for more info. Also view available commands with `--help`.

```bash
seqdat --help
```

## Development

To make changes to seqdat generate a new conda enviroment and install dependencies with poetry.

```bash
git clone git@github.com:daylinmorgan/seqdat.git
cd seqdat
mamba create -p ./env python poetry
mamba activate ./env
poetry install
```

`Black`, `isort` and `flake8` are applied via `pre-commit`, additionally type checking should be enforced with `mypy seqdat`.

After making a patch or preparing new minor release use `bumpver` to update version and generate `git` tag and commit.

## Standalone Binary

Using `pyoxidizer` and the included config file you can easily generate a standalone binary to handle python and associated dependencies.

Run the below command to generate the binary:
```bash
pyoxidizer build
```

This will fetch the necessary `rust`/`python` components necessary to compile everything.

Then you can find your final binary in `./build/x86_64-unknown-linux-gnu/debug/install/seqdat/`.

*Note*: If you have `just` and `pyoxidizer` installed you can run `just build install-bin` to build the binary and copy it to `~/bin`.
