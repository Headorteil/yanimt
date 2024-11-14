#! /bin/bash

poetry up --latest --no-install

pre-commit autoupdate

pyright --createstub impacket

typer yanimt.cli utils docs --name yanimt --output docs/cli.md
