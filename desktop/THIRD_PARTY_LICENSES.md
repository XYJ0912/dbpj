# Third-party runtime notices

## Electron

The desktop shell uses Electron.

- Project: https://www.electronjs.org/
- License: MIT

## MySQL Community Server

The Windows desktop package expects a portable MySQL Community Server runtime in:

```text
desktop/runtime/mysql/
```

This project does not commit the MySQL binary runtime. Before building the desktop package,
download the Windows x64 ZIP archive from Oracle's MySQL Community Server distribution and
copy the extracted server contents so these files exist:

```text
desktop/runtime/mysql/bin/mysqld.exe
desktop/runtime/mysql/bin/mysql.exe
```

When distributing a desktop build that includes MySQL, keep Oracle's MySQL license files from
the downloaded ZIP in the packaged runtime directory.
