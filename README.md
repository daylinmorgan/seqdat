# SEQDAT

**Seq**uencing **Dat**a Manager

## Usage

```bash
seqdat --help
```

## Development

To make changes to seqdat generate a new conda enviroment and install dependencies with poetry.

```bash
git clone git@github.com:daylinmorgan/seqdat.git
cd seqdat
mamba create -n seqdatdev python=3.7 poetry
poetry install
```

After making some changes you can build a local executable using `pyinstaller`.

```bash
./build.sh
```

If pyinstaller completes successfully the executable will be in `dist/`
