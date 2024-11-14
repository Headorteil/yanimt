# `yanimt`

Yanimt by Headorteil 😎

**Usage**:

```console
$ yanimt [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `-V, --version`: Print the tool version
* `-c, --config PATH`: Config path  [default: /home/headorteil/.yanimt/config.yml]
* `-v, --verbosity-level INTEGER RANGE`: Change the logs verbosity  [default: 2; 0<=x<=3]
* `--display / --no-display`: Display things that are not logs nor live like tables  [default: display]
* `-p, --pager / -P, --no-pager`: Display things that are not logs nor live like tables in less  [default: no-pager]
* `-l, --live / -L, --no-live`: Display live objects like progress bars  [default: live]
* `-d, --debug`: Use max verbosity and print file infos with logs
* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

Examples :



- Get tool version

yanimt -V

- Access the terminal user interface

yanimt

- Gather all infos from the domain

yanimt gather -u <username> -p <password> -i <dc ip> all

**Commands**:

* `gather`: Gather required data from AD to a local file

## `yanimt gather`

Gather required data from AD to a local file

**Usage**:

```console
$ yanimt gather [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `-u, --username TEXT`: Username to connect with
* `-p, --password TEXT`: Password to connect with
* `-P, --ask-password`: Ask for a password
* `-H, --hashes TEXT`: NTLM hashes, format is LMHASH:NTHASH
* `-k, --kerberos / -K, --no-kerberos`: Use kerberos authentication. If ommited, it try with NTLM then with kerberos
* `-a, --aes-key TEXT`: AES key to use for Kerberos Authentication (128 or 256 bits)
* `-c, --ccache-path PATH`: Path of the ccache. If ommited and no other authentification method is supplied, it checks KRB5CCNAME env var
* `-d, --domain TEXT`: Domain to query. If ommited, it checks --dc-ip, --dh-host or resolv.conf
* `-i, --dc-ip TEXT`: IP address of the domain controller. If ommited it checks the --dc-host, --domain
* `--dc-host TEXT`: Hostname of the domain controller. If ommited it checks the --dc-ip or --domain
* `-l, --ldap-scheme [ldap|ldaps]`: Ldap scheme. If ommited, it try ldap then ldaps
* `-D, --dns-ip TEXT`: DNS IP. If ommited, it try with DC IP
* `--dns-proto [tcp|udp]`: DNS protocol. If ommited, it try UDP tne TCP
* `--help`: Show this message and exit.

**Commands**:

* `all`: Gather all required data from AD

### `yanimt gather all`

Gather all required data from AD

**Usage**:

```console
$ yanimt gather all [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.
