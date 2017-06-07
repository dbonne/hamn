# hamn
Fork of the oficial PostgreSQL Planet

# Sources

Hamn's sources are available at https://github.com/dbonne/hamn.git, via Git.

``` bash
$ cd prj
$ git clone https://github.com/dbonne/hamn.git
```

# Requirements

Hamn is currently developed for Python 3.4 and Django 1.11

We recommend installing `pyenv` on a developer's system, in order
to be able to install several Python versions without interfering
with the system one.

Installing `pyenv` is very easy:

``` bash
~$ curl -L https://raw.githubusercontent.com/yyuu/\
pyenv-installer/master/bin/pyenv-installer | bash
```

To complete the installation of `pyenv`, you need to append this lines
to your `.bashrc`:

``` bash
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
```

Pyenv install Python from sources, so you need to have a complete C development
environment in your workstation. You will also need the Bzip2 development
files.

Then, list all the available Python versions with:

``` bash
pyenv install --list
```

Make sure you pick the latest available version for 3.4.
Suppose it is 3.4.6. You can install it with:

``` bash
pyenv install 3.4.6
```

Finally, enter the main Hamn directory and type:

``` bash
pyenv local 3.4.6
```
