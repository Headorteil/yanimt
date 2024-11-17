# Yanimt

Yet ANother IMpacket Tool

Gather infos from active directory and visualize it from your terminal

# Installation


```
# System wide
pipx install yanimt

# In a venv
pip install yanimt

# Directly from source
pipx install git+https://github.com/Headorteil/yanimt
```

# Doc
Check the [cli doc](https://github.com/Headorteil/yanimt/blob/main/docs/cli.md)

![TUI 1](https://raw.githubusercontent.com/Headorteil/yanimt/refs/heads/main/images/TUI-1.png)

![TUI 2](https://raw.githubusercontent.com/Headorteil/yanimt/refs/heads/main/images/TUI-2.png)

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
