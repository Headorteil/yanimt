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
* `--display / -D, --no-display`: Display things that are not logs nor live like tables  [default: display]
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

* `clear-db`: Clear the database
* `gather`: Gather required data from AD to a local file

## `yanimt clear-db`

Clear the database

**Usage**:

```console
$ yanimt clear-db [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

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
* `--auth-proto [kerberos|ntlm|auto]`: Use Kerberos or NTLM authentication. If auto, it try with NTLM then with kerberos  [default: auto]
* `-a, --aes-key TEXT`: AES key to use for Kerberos Authentication (128 or 256 bits)
* `-c, --ccache-path PATH`: Path of the ccache. If ommited and no other authentification method is supplied, it checks KRB5CCNAME env var
* `-d, --domain TEXT`: Domain to query. If ommited, it checks --dc-ip, --dh-host or resolv.conf
* `-i, --dc-ip TEXT`: IP address of the domain controller. If ommited it checks the --dc-host, --domain
* `--dc-host TEXT`: Hostname of the domain controller. If ommited it checks the --dc-ip or --domain
* `-l, --ldap-scheme [ldap|ldaps|auto]`: Ldap scheme. If auto, it try ldap then ldaps  [default: auto]
* `-D, --dns-ip TEXT`: DNS IP. If ommited, it try with DC IP
* `--dns-proto [tcp|udp|auto]`: DNS protocol. If auto, it try UDP tne TCP  [default: auto]
* `--help`: Show this message and exit.

**Commands**:

* `all`: Gather all required data from AD
* `computers`: Gather computers
* `domain-sid`: Gather the domain sid
* `groups`: Gather groups
* `ous`: Gather organisational units
* `secrets`: Gather secrets
* `users`: Gather users

### `yanimt gather all`

Gather all required data from AD

**Usage**:

```console
$ yanimt gather all [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

### `yanimt gather computers`

Gather computers

**Usage**:

```console
$ yanimt gather computers [OPTIONS]
```

**Options**:

* `-r, --resolve / -R, --no-resolve`: Resolve the DNS name of the machines  [default: resolve]
* `--help`: Show this message and exit.

### `yanimt gather domain-sid`

Gather the domain sid

**Usage**:

```console
$ yanimt gather domain-sid [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

### `yanimt gather groups`

Gather groups

**Usage**:

```console
$ yanimt gather groups [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

### `yanimt gather ous`

Gather organisational units

**Usage**:

```console
$ yanimt gather ous [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

### `yanimt gather secrets`

Gather secrets

**Usage**:

```console
$ yanimt gather secrets [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

### `yanimt gather users`

Gather users

**Usage**:

```console
$ yanimt gather users [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.
