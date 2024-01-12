# SEQDAT

**Seq**uencing **Dat**a Manager

## Usage

See [docs](docs/usage.md) for more info. Also view available commands with `--help`.

```bash
seqdat --help
```


## Standalone Binary

Using `pyoxidizer` and the included config file you can easily generate a
standalone binary to handle python and associated dependencies.

Run the below command to generate the binary:

```bash
pyoxidizer build --release
```

This will fetch the necessary `rust`/`python` components necessary to compile everything.

Then you can find your final binary in `./build/x86_64-unknown-linux-gnu/release/install/seqdat/`.
