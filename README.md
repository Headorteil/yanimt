# Yanimt

Yet ANother IMpacket Tool

Gather infos from active directory and visualize it from your terminal

# Installation
`pipx install git+https://github.com/Headorteil/yanimt`

# Doc
Check the [cli doc](docs/cli.md)

![TUI 1](images/TUI-1.png)

![TUI 2](images/TUI-2.png)

> NOTE : You can select text from the tui by pressing the shift key in most terminals

# DEV
## Set up env

Install poetry and poetry-up

```bash
poetry shell
poetry install
pre-commit install
```

## Debug

In 2 terms :

`textual console`

`textual run --dev -c yanimt`

# TODO

- Follow these issues :
    - https://github.com/fastapi/typer/issues/951
    - https://github.com/fastapi/typer/issues/347
- Write a proper doc
- Remove all the `# noqa:` and `# pyright: ignore` ? (maybe one day)
- Do things
